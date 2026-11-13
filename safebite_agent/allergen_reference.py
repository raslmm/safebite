"""Portuguese/English reference for EU Annex II allergen groups.

The terms are limited to canonical group names and the examples expressly named in Annex II. This is not a complete ingredient or synonym dictionary. A missing term must remain uncertain; it must never be treated as evidence of no risk.
Legal notes are review flags, not rules that this module applies to a product.
"""

from safebite_agent.schemas import (
    AllergenCatalog,
    AllergenId,
    AllergenReference,
    SourceReference,
)

EU_ANNEX_II_SOURCE_ID = "eu-regulation-1169-2011-annex-ii"
EU_ANNEX_II_VERSION = "consolidated-2025-04-01"

EU_ALLERGEN_CATALOG = AllergenCatalog(
    source=SourceReference(
        source_id=EU_ANNEX_II_SOURCE_ID,
        title="Regulation (EU) No 1169/2011, consolidated text, Annex II",
        url="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02011R1169-20250401",
        jurisdiction="European Union",
        version=EU_ANNEX_II_VERSION,
    ),
    allergens=(
        AllergenReference(
            allergen_id=AllergenId.CEREALS_WITH_GLUTEN,
            name_en="Cereals containing gluten",
            name_pt="Cereais que contêm glúten",
            match_terms_en=(
                "Cereals containing gluten",
                "wheat",
                "rye",
                "barley",
                "oats",
                "spelt",
                "Khorasan wheat",
            ),
            match_terms_pt=(
                "Cereais que contêm glúten",
                "trigo",
                "centeio",
                "cevada",
                "aveia",
                "espelta",
                "trigo Khorasan",
            ),
            legal_note_en=(
                "Annex II lists specific cereal-derived exemptions; check the exact product "
                "and legal text before treating a derivative as a match."
            ),
            legal_note_pt=(
                "O anexo II prevê exceções específicas para derivados de cereais; confirme o "
                "produto e o texto legal antes de classificar um derivado como correspondência."
            ),
        ),
        AllergenReference(
            allergen_id=AllergenId.CRUSTACEANS,
            name_en="Crustaceans",
            name_pt="Crustáceos",
            match_terms_en=("Crustaceans",),
            match_terms_pt=("Crustáceos",),
        ),
        AllergenReference(
            allergen_id=AllergenId.EGGS,
            name_en="Eggs",
            name_pt="Ovos",
            match_terms_en=("Eggs",),
            match_terms_pt=("Ovos",),
        ),
        AllergenReference(
            allergen_id=AllergenId.FISH,
            name_en="Fish",
            name_pt="Peixes",
            match_terms_en=("Fish",),
            match_terms_pt=("Peixes",),
            legal_note_en=(
                "Annex II contains specific exceptions for certain fish-derived products; "
                "review them before classifying a derivative."
            ),
            legal_note_pt=(
                "O anexo II prevê exceções específicas para certos produtos derivados de peixe; "
                "confirme-as antes de classificar um derivado."
            ),
        ),
        AllergenReference(
            allergen_id=AllergenId.PEANUTS,
            name_en="Peanuts",
            name_pt="Amendoins",
            match_terms_en=("Peanuts",),
            match_terms_pt=("Amendoins",),
        ),
        AllergenReference(
            allergen_id=AllergenId.SOYBEANS,
            name_en="Soybeans",
            name_pt="Soja",
            match_terms_en=("Soybeans",),
            match_terms_pt=("Soja",),
            legal_note_en=(
                "Annex II lists specific soy-derived exemptions, including fully refined oil "
                "and fat; check the exact product and legal text."
            ),
            legal_note_pt=(
                "O anexo II prevê exceções específicas para derivados de soja, incluindo óleo "
                "e gordura totalmente refinados; confirme o produto e o texto legal."
            ),
        ),
        AllergenReference(
            allergen_id=AllergenId.MILK,
            name_en="Milk",
            name_pt="Leite",
            match_terms_en=("Milk", "lactose"),
            match_terms_pt=("Leite", "lactose"),
            legal_note_en=(
                "Annex II lists specific exceptions for whey used in distillates and lactitol."
            ),
            legal_note_pt=(
                "O anexo II prevê exceções específicas para lactossoro usado em destilados e "
                "para o lactitol."
            ),
        ),
        AllergenReference(
            allergen_id=AllergenId.NUTS,
            name_en="Nuts",
            name_pt="Frutos de casca rija",
            match_terms_en=(
                "Nuts",
                "almonds",
                "hazelnuts",
                "walnuts",
                "cashews",
                "pecans",
                "Brazil nuts",
                "pistachios",
                "macadamia nuts",
                "Queensland nuts",
            ),
            match_terms_pt=(
                "Frutos de casca rija",
                "amêndoas",
                "avelãs",
                "nozes",
                "castanhas de caju",
                "nozes pecã",
                "castanhas do Brasil",
                "pistácios",
                "nozes de macadâmia",
                "nozes do Queensland",
            ),
            legal_note_en=(
                "Annex II names eight nut types and provides an exception for nuts used in "
                "alcoholic distillates. Do not expand this group to other nuts without review."
            ),
            legal_note_pt=(
                "O anexo II enumera oito tipos de frutos de casca rija e prevê uma exceção para "
                "os usados em destilados alcoólicos. Não alargue o grupo sem revisão."
            ),
        ),
        AllergenReference(
            allergen_id=AllergenId.CELERY,
            name_en="Celery",
            name_pt="Aipo",
            match_terms_en=("Celery",),
            match_terms_pt=("Aipo",),
        ),
        AllergenReference(
            allergen_id=AllergenId.MUSTARD,
            name_en="Mustard",
            name_pt="Mostarda",
            match_terms_en=("Mustard",),
            match_terms_pt=("Mostarda",),
        ),
        AllergenReference(
            allergen_id=AllergenId.SESAME,
            name_en="Sesame seeds",
            name_pt="Sementes de sésamo",
            match_terms_en=("Sesame seeds",),
            match_terms_pt=("Sementes de sésamo",),
        ),
        AllergenReference(
            allergen_id=AllergenId.SULPHITES,
            name_en="Sulphur dioxide and sulphites",
            name_pt="Dióxido de enxofre e sulfitos",
            match_terms_en=(
                "Sulphur dioxide and sulphites",
                "sulphur dioxide",
                "sulphites",
                "sulfites",
            ),
            match_terms_pt=(
                "Dióxido de enxofre e sulfitos",
                "dióxido de enxofre",
                "sulfitos",
            ),
            legal_note_en=(
                "Annex II covers concentrations above 10 mg/kg or 10 mg/litre, expressed as "
                "total SO₂ in the food as consumed or reconstituted. A name alone does not "
                "establish that threshold."
            ),
            legal_note_pt=(
                "O anexo II abrange concentrações superiores a 10 mg/kg ou 10 mg/litro, "
                "expressas em SO₂ total no alimento pronto a consumir ou reconstituído. O nome "
                "por si só não confirma esse limite."
            ),
        ),
        AllergenReference(
            allergen_id=AllergenId.LUPIN,
            name_en="Lupin",
            name_pt="Tremoço",
            match_terms_en=("Lupin",),
            match_terms_pt=("Tremoço",),
        ),
        AllergenReference(
            allergen_id=AllergenId.MOLLUSCS,
            name_en="Molluscs",
            name_pt="Moluscos",
            match_terms_en=("Molluscs",),
            match_terms_pt=("Moluscos",),
        ),
    ),
)
