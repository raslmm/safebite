"""Typed data contracts shared by the SafeBite application and agent."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class Contract(BaseModel):
    """Base contract: reject undeclared fields and preserve source text exactly."""

    model_config = ConfigDict(extra="forbid")


class AllergenId(StrEnum):
    CEREALS_WITH_GLUTEN = "cereals_with_gluten"
    CRUSTACEANS = "crustaceans"
    EGGS = "eggs"
    FISH = "fish"
    PEANUTS = "peanuts"
    SOYBEANS = "soybeans"
    MILK = "milk"
    NUTS = "nuts"
    CELERY = "celery"
    MUSTARD = "mustard"
    SESAME = "sesame"
    SULPHITES = "sulphites"
    LUPIN = "lupin"
    MOLLUSCS = "molluscs"


class AllergenProfile(Contract):
    """Allergens selected by the user for the active session."""

    selected_allergens: list[AllergenId]

    @field_validator("selected_allergens")
    @classmethod
    def selected_allergens_are_unique(cls, values: list[AllergenId]) -> list[AllergenId]:
        if len(values) != len(set(values)):
            raise ValueError("An allergen may only be selected once.")
        return values


LabelLanguage = Literal["pt", "en", "unsupported", "unknown"]
LabelField = Literal["language", "ingredients_text", "contains_text", "may_contain_text"]


class LabelExtraction(Contract):
    """Extracted label fields; text values retain their original spelling and punctuation."""

    language: LabelLanguage
    ingredients_text: str | None = None
    contains_text: str | None = None
    may_contain_text: str | None = None
    uncertain_fields: list[LabelField] = []
    uncertain_terms: list[str] = []
    is_complete: bool
    human_reviewed: bool = False


EvidenceLocation = Literal["ingredients", "contains", "may_contain"]
EvidenceType = Literal[
    "direct_match",
    "possible_match",
    "legal_exception_review",
    "threshold_unknown",
    "below_threshold",
    "unresolved_extraction",
]


class AllergenEvidence(Contract):
    """A quoted label passage associated with a reviewed allergen reference."""

    allergen_id: AllergenId
    location: EvidenceLocation
    evidence_type: EvidenceType
    quote: str
    source_id: str
    source_version: str


class SourceReference(Contract):
    source_id: str
    title: str
    url: str
    jurisdiction: str
    version: str


class AllergenReference(Contract):
    allergen_id: AllergenId
    name_en: str
    name_pt: str
    match_terms_en: tuple[str, ...]
    match_terms_pt: tuple[str, ...]
    exception_terms_en: tuple[str, ...] = ()
    exception_terms_pt: tuple[str, ...] = ()
    legal_note_en: str | None = None
    legal_note_pt: str | None = None

    @model_validator(mode="after")
    def names_are_in_match_terms(self) -> "AllergenReference":
        if self.name_en.casefold() not in {term.casefold() for term in self.match_terms_en}:
            raise ValueError("The English canonical name must be included in its match terms.")
        if self.name_pt.casefold() not in {term.casefold() for term in self.match_terms_pt}:
            raise ValueError("The Portuguese canonical name must be included in its match terms.")
        return self


class AllergenCatalog(Contract):
    source: SourceReference
    allergens: tuple[AllergenReference, ...]

    @model_validator(mode="after")
    def contains_each_eu_allergen_once(self) -> "AllergenCatalog":
        ids = [allergen.allergen_id for allergen in self.allergens]
        if len(ids) != len(AllergenId) or set(ids) != set(AllergenId):
            raise ValueError("The EU catalog must contain each of the 14 allergen groups once.")
        return self


RiskState = Literal[
    "risk_found",
    "possible_risk",
    "no_match_found_in_readable_text",
    "cannot_assess",
]


class RiskAssessment(Contract):
    """Assessment created by deterministic application code, with supporting evidence."""

    state: RiskState
    evidence: list[AllergenEvidence] = []
    explanation: str


ToolOutcome = Literal["ok", "needs_input", "error"]


class ToolResult(Contract):
    outcome: ToolOutcome
    message: str
    assessment: RiskAssessment | None = None
