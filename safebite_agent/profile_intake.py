"""Conservative phrase-based detection for user-confirmed allergy additions."""

import re

from safebite_agent.allergen_reference import EU_ALLERGEN_CATALOG
from safebite_agent.schemas import AllergenId

_POSITIVE_ALLERGY_STATEMENT = re.compile(
    r"\b(?:"
    r"i(?:'m| am)\s+allergic\s+to|"
    r"i\s+have\s+(?:a\s+|an\s+)?(?:food\s+)?allerg(?:y|ies)\s+(?:to|for|of)|"
    r"i\s+have\s+(?!no\b|not\b)(?:\w+\s+){0,3}allerg(?:y|ies)|"
    r"my\s+allerg(?:y|ies)(?:\s+(?:is|are))?|"
    r"tenho\s+alergia\s+a|"
    r"sou\s+al[eé]rgic[oa]\s+a"
    r")\b",
    re.IGNORECASE,
)


def explicit_allergy_additions(message: str, current: list[AllergenId]) -> list[AllergenId]:
    """Find known allergen groups in a clear first-person positive allergy statement.

    This only proposes additions. The caller must get explicit confirmation before changing
    the active profile, and persistence still requires the app's profile-storage consent.
    """
    if not _POSITIVE_ALLERGY_STATEMENT.search(message):
        return []

    additions: list[AllergenId] = []
    for reference in EU_ALLERGEN_CATALOG.allergens:
        terms = (*reference.match_terms_en, *reference.match_terms_pt)
        for term in sorted(set(terms), key=len, reverse=True):
            term_pattern = r"\s+".join(re.escape(word) for word in term.split())
            if re.search(rf"(?<!\w){term_pattern}(?!\w)", message, re.IGNORECASE):
                if reference.allergen_id not in current and reference.allergen_id not in additions:
                    additions.append(reference.allergen_id)
                break
    return additions
