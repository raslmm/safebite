"""Deterministic, evidence-producing checks against the reviewed Annex II list."""

import re
from dataclasses import dataclass

from safebite_agent.allergen_reference import (
    EU_ALLERGEN_CATALOG,
    EU_ANNEX_II_SOURCE_ID,
    EU_ANNEX_II_VERSION,
)
from safebite_agent.schemas import (
    AllergenEvidence,
    AllergenId,
    AllergenProfile,
    EvidenceLocation,
    EvidenceType,
    LabelExtraction,
    RiskAssessment,
    RiskState,
)

_CONCENTRATION_RE = re.compile(
    r"(?P<value>\d+(?:[.,]\d+)?)\s*mg\s*/\s*(?:kg|l|litre|liter)\b", re.IGNORECASE
)
_SO2_RE = re.compile(
    r"\bSO\s*2\b|SO₂|sulphur dioxide|sulfur dioxide|dióxido de enxofre", re.IGNORECASE
)


@dataclass(frozen=True)
class _TextField:
    location: EvidenceLocation
    text: str


def _pattern(term: str) -> re.Pattern[str]:
    body = re.escape(term).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<!\w){body}(?!\w)", re.IGNORECASE)


def _matches(text: str, terms: tuple[str, ...]) -> list[tuple[int, int, str]]:
    """Return non-overlapping term matches, keeping the longest matching phrase."""
    ranges: list[tuple[int, int, str]] = []
    for term in sorted(set(terms), key=len, reverse=True):
        for match in _pattern(term).finditer(text):
            candidate = (match.start(), match.end(), match.group())
            if any(candidate[0] < end and start < candidate[1] for start, end, _ in ranges):
                continue
            ranges.append(candidate)
    return sorted(ranges)


def _sulphite_threshold(text: str, start: int, end: int) -> str:
    """Classify a nearby sulphite quantity only when it is expressed as SO2."""
    context_start = max(0, start - 48)
    context_end = min(len(text), end + 88)
    context = text[context_start:context_end]
    if not _SO2_RE.search(context):
        return "unknown"

    quantities = list(_CONCENTRATION_RE.finditer(context))
    if not quantities:
        return "unknown"

    term_center = (start + end) / 2 - context_start
    quantity = min(
        quantities,
        key=lambda item: abs((item.start() + item.end()) / 2 - term_center),
    )
    value = float(quantity.group("value").replace(",", "."))
    return "above" if value > 10 else "at_or_below"


def _localized(label: LabelExtraction, english: str, portuguese: str) -> str:
    return portuguese if label.language == "pt" else english


def _evidence(
    allergen_id: AllergenId,
    location: EvidenceLocation,
    evidence_type: EvidenceType,
    quote: str,
) -> AllergenEvidence:
    return AllergenEvidence(
        allergen_id=allergen_id,
        location=location,
        evidence_type=evidence_type,
        quote=quote,
        source_id=EU_ANNEX_II_SOURCE_ID,
        source_version=EU_ANNEX_II_VERSION,
    )


def check_label(profile: AllergenProfile, label: LabelExtraction) -> RiskAssessment:
    """Assess reviewed ingredient text; the model never chooses the risk state.

    The checker uses whole terms from the deliberately small reference list. It
    does not infer aliases, ingredient derivatives, or allergen absence from
    unlisted terms. Statutory exceptions are surfaced for review, not silently
    applied as legal conclusions.
    """
    if not profile.selected_allergens:
        return RiskAssessment(
            state="cannot_assess",
            explanation=_localized(
                label,
                "Select at least one allergen before checking a label.",
                "Selecione pelo menos um alergénio antes de analisar o rótulo.",
            ),
        )

    if label.language not in ("pt", "en"):
        return RiskAssessment(
            state="cannot_assess",
            explanation=(
                "This label language is not supported."
                if label.language == "unsupported"
                else "The label language could not be identified."
            ),
        )

    if not label.is_complete or not (label.ingredients_text or "").strip():
        return RiskAssessment(
            state="cannot_assess",
            explanation=_localized(
                label,
                "The ingredient text is missing or incomplete; the label cannot be assessed.",
                "O texto dos ingredientes está em falta ou incompleto; não é possível avaliar o rótulo.",
            ),
        )

    if (label.uncertain_fields or label.uncertain_terms) and not label.human_reviewed:
        return RiskAssessment(
            state="cannot_assess",
            explanation=_localized(
                label,
                "Review the uncertain extracted text before checking the label.",
                "Reveja o texto extraído assinalado como incerto antes de analisar o rótulo.",
            ),
        )

    fields = [
        _TextField("ingredients", label.ingredients_text or ""),
        _TextField("contains", label.contains_text or ""),
        _TextField("may_contain", label.may_contain_text or ""),
    ]
    reference_by_id = {
        reference.allergen_id: reference for reference in EU_ALLERGEN_CATALOG.allergens
    }
    evidence: list[AllergenEvidence] = []
    has_direct_match = False
    has_possible_match = bool(label.uncertain_fields or label.uncertain_terms)

    for allergen_id in profile.selected_allergens:
        reference = reference_by_id[allergen_id]
        terms = (*reference.match_terms_en, *reference.match_terms_pt)
        exceptions = (*reference.exception_terms_en, *reference.exception_terms_pt)

        for field in fields:
            if not field.text.strip():
                continue

            exception_matches = _matches(field.text, exceptions)
            for _, _, quote in exception_matches:
                evidence.append(
                    _evidence(
                        allergen_id,
                        field.location,
                        "legal_exception_review",
                        quote,
                    )
                )
                has_possible_match = True

            for start, end, quote in _matches(field.text, terms):
                if any(
                    start < exception_end and exception_start < end
                    for exception_start, exception_end, _ in exception_matches
                ):
                    continue

                evidence_type: EvidenceType = "direct_match"
                if field.location == "may_contain":
                    evidence_type = "possible_match"
                    has_possible_match = True
                elif allergen_id == AllergenId.SULPHITES:
                    threshold = _sulphite_threshold(field.text, start, end)
                    if threshold == "unknown":
                        evidence_type = "threshold_unknown"
                        has_possible_match = True
                    elif threshold == "at_or_below":
                        evidence_type = "below_threshold"
                    else:
                        has_direct_match = True
                else:
                    has_direct_match = True

                evidence.append(_evidence(allergen_id, field.location, evidence_type, quote))

    if not label.human_reviewed and (label.uncertain_fields or label.uncertain_terms):
        state: RiskState = "cannot_assess"
        explanation = _localized(
            label,
            "Review the uncertain extracted text before relying on this assessment.",
            "Reveja o texto extraído assinalado como incerto antes de utilizar esta avaliação.",
        )
    elif not label.is_complete:
        state = "cannot_assess"
        explanation = _localized(
            label,
            "The label text is incomplete, so the whole label cannot be assessed.",
            "O texto do rótulo está incompleto, por isso não é possível avaliar o rótulo completo.",
        )
    elif has_direct_match:
        state = "risk_found"
        explanation = _localized(
            label,
            "A selected allergen matched readable ingredient or contains text. Review the evidence and any listed exceptions.",
            "Foi encontrado um alergénio selecionado nos ingredientes ou na declaração «contém». Reveja a evidência e as exceções indicadas.",
        )
    elif has_possible_match:
        state = "possible_risk"
        explanation = _localized(
            label,
            "A possible allergen match or unresolved condition needs your attention.",
            "Existe uma possível correspondência ou condição por esclarecer que requer atenção.",
        )
    else:
        state = "no_match_found_in_readable_text"
        explanation = _localized(
            label,
            "No selected allergen matched the readable text. This is not a safety guarantee.",
            "Não foi encontrado um alergénio selecionado no texto legível. Isto não garante que o produto seja seguro.",
        )

    return RiskAssessment(state=state, evidence=evidence, explanation=explanation)
