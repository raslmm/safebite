"""Offline behavior checks for the deterministic allergen checker."""

import pytest

from safebite_agent.allergen_checker import check_label
from safebite_agent.schemas import AllergenId, AllergenProfile, LabelExtraction


def make_label(
    ingredients: str,
    *,
    language: str = "en",
    contains: str | None = None,
    may_contain: str | None = None,
    complete: bool = True,
    uncertain: list[str] | None = None,
    uncertain_terms: list[str] | None = None,
    reviewed: bool = False,
) -> LabelExtraction:
    return LabelExtraction(
        language=language,
        ingredients_text=ingredients,
        contains_text=contains,
        may_contain_text=may_contain,
        is_complete=complete,
        uncertain_fields=uncertain or [],
        uncertain_terms=uncertain_terms or [],
        human_reviewed=reviewed,
    )


def profile(*allergens: AllergenId) -> AllergenProfile:
    return AllergenProfile(selected_allergens=list(allergens))


def test_direct_ingredient_match_has_quote_and_source() -> None:
    result = check_label(profile(AllergenId.EGGS), make_label("Sugar, egg powder, salt"))

    assert result.state == "risk_found"
    assert result.evidence[0].quote.lower() == "egg"
    assert result.evidence[0].source_id == "eu-regulation-1169-2011-annex-ii"


def test_contains_statement_is_a_direct_match() -> None:
    result = check_label(
        profile(AllergenId.PEANUTS),
        make_label("Sugar, cocoa", contains="Contains peanuts"),
    )

    assert result.state == "risk_found"
    assert result.evidence[0].location == "contains"


def test_may_contain_statement_is_possible_risk() -> None:
    result = check_label(
        profile(AllergenId.PEANUTS),
        make_label("Sugar, cocoa", may_contain="May contain peanuts"),
    )

    assert result.state == "possible_risk"
    assert result.evidence[0].evidence_type == "possible_match"


def test_whole_word_matching_does_not_match_oatmeal_as_oat() -> None:
    result = check_label(profile(AllergenId.CEREALS_WITH_GLUTEN), make_label("Oatmeal flavor"))

    assert result.state == "no_match_found_in_readable_text"


@pytest.mark.parametrize(
    ("text", "expected_state", "expected_evidence"),
    [
        ("Sulphites 12 mg/kg as SO2", "risk_found", "direct_match"),
        ("Sulphites 10 mg/kg as SO2", "no_match_found_in_readable_text", "below_threshold"),
        ("Sulphites in the ingredients", "possible_risk", "threshold_unknown"),
        ("Sulphites 12 mg/kg", "possible_risk", "threshold_unknown"),
    ],
)
def test_sulphite_threshold_is_applied_conservatively(
    text: str, expected_state: str, expected_evidence: str
) -> None:
    result = check_label(profile(AllergenId.SULPHITES), make_label(text))

    assert result.state == expected_state
    assert result.evidence[0].evidence_type == expected_evidence


def test_known_soy_exception_is_flagged_for_review_not_confirmed() -> None:
    result = check_label(profile(AllergenId.SOYBEANS), make_label("Fully refined soybean oil"))

    assert result.state == "possible_risk"
    assert result.evidence[0].evidence_type == "legal_exception_review"


def test_cereal_exception_is_flagged_for_review_not_confirmed() -> None:
    result = check_label(
        profile(AllergenId.CEREALS_WITH_GLUTEN),
        make_label("Wheat based glucose syrups including dextrose"),
    )

    assert result.state == "possible_risk"
    assert result.evidence[0].evidence_type == "legal_exception_review"


def test_unrelated_direct_match_still_found_alongside_exception() -> None:
    result = check_label(
        profile(AllergenId.SOYBEANS),
        make_label("Fully refined soybean oil, soy protein"),
    )

    assert result.state == "risk_found"
    assert {item.evidence_type for item in result.evidence} == {
        "legal_exception_review",
        "direct_match",
    }


@pytest.mark.parametrize(
    "label",
    [
        make_label("Sugar", language="unsupported"),
        make_label("Sugar", language="unknown"),
        make_label("Sugar", complete=False),
        make_label("", complete=True),
        make_label("Sugar", uncertain=["ingredients_text"]),
        make_label("Sugar, hydrolyzed ingredient", uncertain_terms=["hydrolyzed ingredient"]),
    ],
)
def test_inadequate_or_unreviewed_input_cannot_be_assessed(label: LabelExtraction) -> None:
    result = check_label(profile(AllergenId.MILK), label)

    assert result.state == "cannot_assess"


def test_empty_profile_cannot_be_assessed() -> None:
    result = check_label(profile(), make_label("Sugar"))

    assert result.state == "cannot_assess"


def test_reviewed_remaining_uncertainty_is_possible_risk() -> None:
    result = check_label(
        profile(AllergenId.MILK),
        make_label("Sugar, unclear ingredient", uncertain=["ingredients_text"], reviewed=True),
    )

    assert result.state == "possible_risk"


def test_reviewed_unknown_ingredient_stays_possible_risk() -> None:
    result = check_label(
        profile(AllergenId.MILK),
        make_label(
            "Sugar, hydrolyzed ingredient",
            uncertain_terms=["hydrolyzed ingredient"],
            reviewed=True,
        ),
    )

    assert result.state == "possible_risk"


def test_portuguese_match_uses_portuguese_evidence() -> None:
    result = check_label(
        profile(AllergenId.NUTS),
        make_label("Farinha, amêndoa", language="pt"),
    )

    assert result.state == "risk_found"
    assert result.evidence[0].quote == "amêndoa"


def test_complete_readable_nonmatch_has_required_caveat() -> None:
    result = check_label(profile(AllergenId.MILK), make_label("Sugar, cocoa"))

    assert result.state == "no_match_found_in_readable_text"
    assert "not a safety guarantee" in result.explanation
