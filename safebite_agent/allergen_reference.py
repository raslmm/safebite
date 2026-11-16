"""Portuguese/English starter reference for EU Annex II allergen groups.

Terms include canonical group names, direct singular/plural variants, and
examples named in Annex II. This is not a complete ingredient dictionary. A
missing term remains uncertain, never evidence of no risk. Exception phrases
are review flags, not a full legal interpretation of a product.
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
                "oat",
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
            exception_terms_en=(
                "wheat based glucose syrups including dextrose",
                "wheat based maltodextrins",
                "glucose syrups based on barley",
                "cereals used for making alcoholic distillates including ethyl alcohol of agricultural origin",
            ),
            exception_terms_pt=(
                "xaropes de glucose à base de trigo, incluindo dextrose",
                "maltodextrinas à base de trigo",
                "xaropes de glucose à base de cevada",
                "cereais utilizados no fabrico de destilados alcoólicos, incluindo álcool etílico de origem agrícola",
            ),
        ),
        AllergenReference(
            allergen_id=AllergenId.CRUSTACEANS,
            name_en="Crustaceans",
            name_pt="Crustáceos",
            match_terms_en=("Crustaceans", "Crustacean"),
            match_terms_pt=("Crustáceos", "Crustáceo"),
        ),
        AllergenReference(
            allergen_id=AllergenId.EGGS,
            name_en="Eggs",
            name_pt="Ovos",
            match_terms_en=("Eggs", "Egg"),
            match_terms_pt=("Ovos", "Ovo"),
        ),
        AllergenReference(
            allergen_id=AllergenId.FISH,
            name_en="Fish",
            name_pt="Peixes",
            match_terms_en=("Fish",),
            match_terms_pt=("Peixes", "Peixe"),
            legal_note_en=(
                "Annex II contains specific exceptions for certain fish-derived products; "
                "review them before classifying a derivative."
            ),
            legal_note_pt=(
                "O anexo II prevê exceções específicas para certos produtos derivados de peixe; "
                "confirme-as antes de classificar um derivado."
            ),
            exception_terms_en=(
                "fish gelatine used as carrier for vitamin or carotenoid preparations",
                "fish gelatine or isinglass used as fining agent in beer and wine",
            ),
            exception_terms_pt=(
                "gelatina de peixe utilizada como suporte de preparados de vitaminas ou carotenoides",
                "gelatina de peixe ou ictiocola utilizada como clarificante na cerveja e no vinho",
            ),
        ),
        AllergenReference(
            allergen_id=AllergenId.PEANUTS,
            name_en="Peanuts",
            name_pt="Amendoins",
            match_terms_en=("Peanuts", "Peanut"),
            match_terms_pt=("Amendoins", "Amendoim"),
        ),
        AllergenReference(
            allergen_id=AllergenId.SOYBEANS,
            name_en="Soybeans",
            name_pt="Soja",
            match_terms_en=("Soybeans", "Soybean", "Soy"),
            match_terms_pt=("Soja",),
            exception_terms_en=(
                "fully refined soybean oil",
                "fully refined soybean fat",
                "natural mixed tocopherols e306 from soybean sources",
                "natural d-alpha tocopherol from soybean sources",
                "natural d-alpha tocopherol acetate from soybean sources",
                "natural d-alpha tocopherol succinate from soybean sources",
                "phytosterols and phytosterol esters from soybean sources",
                "plant stanol ester produced from vegetable oil sterols from soybean sources",
            ),
            exception_terms_pt=(
                "óleo de soja totalmente refinado",
                "gordura de soja totalmente refinada",
                "tocoferóis mistos naturais e306 derivados de soja",
                "d-alfa-tocoferol natural derivado de soja",
                "acetato de d-alfa-tocoferol natural derivado de soja",
                "succinato de d-alfa-tocoferol natural derivado de soja",
                "fitoesteróis e ésteres de fitoesterol derivados de soja",
                "éster de estanol vegetal produzido a partir de esteróis de óleo vegetal de soja",
            ),
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
            exception_terms_en=(
                "whey used for making alcoholic distillates including ethyl alcohol of agricultural origin",
                "lactitol",
            ),
            exception_terms_pt=(
                "lactossoro utilizado no fabrico de destilados alcoólicos, incluindo álcool etílico de origem agrícola",
                "lactitol",
            ),
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
                "almond",
                "hazelnut",
                "walnut",
                "cashew",
                "pecan nut",
                "Brazil nut",
                "pistachio nut",
                "macadamia nut",
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
                "amêndoa",
                "avelã",
                "castanha de caju",
                "noz pecã",
                "castanha do Brasil",
                "pistácio",
                "noz de macadâmia",
                "noz do Queensland",
            ),
            legal_note_en=(
                "Annex II names eight nut types and provides an exception for nuts used in "
                "alcoholic distillates. Do not expand this group to other nuts without review."
            ),
            legal_note_pt=(
                "O anexo II enumera oito tipos de frutos de casca rija e prevê uma exceção para "
                "os usados em destilados alcoólicos. Não alargue o grupo sem revisão."
            ),
            exception_terms_en=(
                "nuts used for making alcoholic distillates including ethyl alcohol of agricultural origin",
            ),
            exception_terms_pt=(
                "frutos de casca rija utilizados na confeção de destilados alcoólicos, incluindo álcool etílico de origem agrícola",
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
            match_terms_en=("Sesame seeds", "sesame seed", "sesame"),
            match_terms_pt=("Sementes de sésamo", "semente de sésamo", "sésamo"),
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
            match_terms_en=("Lupin", "Lupins"),
            match_terms_pt=("Tremoço", "Tremoços"),
        ),
        AllergenReference(
            allergen_id=AllergenId.MOLLUSCS,
            name_en="Molluscs",
            name_pt="Moluscos",
            match_terms_en=("Molluscs", "Mollusc", "Mollusks", "Mollusk"),
            match_terms_pt=("Moluscos", "Molusco"),
        ),
    ),
)
