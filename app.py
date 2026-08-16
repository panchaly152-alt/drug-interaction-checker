import streamlit as st
import requests
import re


# =========================================================
# MEDCHECK AI V3
# Evidence-Based Drug Interaction Analyzer
# U.S. FDA openFDA + Rule-Based Pharmacy Intelligence
# No paid AI API required
# =========================================================


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="MedCheck AI",
    page_icon="💊",
    layout="centered"
)


FDA_URL = "https://api.fda.gov/drug/label.json"


# =========================================================
# DRUG ALIASES
# =========================================================

ALIASES = {
    "paracetamol": "acetaminophen",
    "tylenol": "acetaminophen",
    "advil": "ibuprofen",
    "motrin": "ibuprofen",
    "brufen": "ibuprofen",
    "aleve": "naproxen",
    "coumadin": "warfarin",
    "plavix": "clopidogrel",
    "lipitor": "atorvastatin",
    "zocor": "simvastatin",
    "crestor": "rosuvastatin",
    "glucophage": "metformin",
    "lasix": "furosemide",
    "norvasc": "amlodipine",
    "lopressor": "metoprolol",
    "toprol": "metoprolol",
    "protonix": "pantoprazole",
    "prilosec": "omeprazole",
    "xanax": "alprazolam",
    "valium": "diazepam",
    "prozac": "fluoxetine",
    "zoloft": "sertraline",
    "ventolin": "albuterol"
}


# =========================================================
# DRUG CLASS DATABASE
# =========================================================

DRUG_CLASSES = {

    "warfarin": "Anticoagulant",
    "heparin": "Anticoagulant",
    "enoxaparin": "Anticoagulant",
    "rivaroxaban": "Direct oral anticoagulant",
    "apixaban": "Direct oral anticoagulant",
    "dabigatran": "Direct oral anticoagulant",

    "aspirin": "Antiplatelet / NSAID",
    "clopidogrel": "Antiplatelet",
    "cilostazol": "Antiplatelet",

    "ibuprofen": "NSAID",
    "naproxen": "NSAID",
    "diclofenac": "NSAID",
    "ketorolac": "NSAID",
    "indomethacin": "NSAID",
    "meloxicam": "NSAID",
    "celecoxib": "NSAID",

    "metformin": "Biguanide antidiabetic",
    "glipizide": "Sulfonylurea",
    "glyburide": "Sulfonylurea",
    "pioglitazone": "Thiazolidinedione",
    "sitagliptin": "DPP-4 inhibitor",
    "dapagliflozin": "SGLT2 inhibitor",
    "empagliflozin": "SGLT2 inhibitor",
    "semaglutide": "GLP-1 receptor agonist",
    "liraglutide": "GLP-1 receptor agonist",
    "insulin": "Insulin",

    "atorvastatin": "Statin",
    "simvastatin": "Statin",
    "rosuvastatin": "Statin",
    "pravastatin": "Statin",
    "lovastatin": "Statin",

    "lisinopril": "ACE inhibitor",
    "enalapril": "ACE inhibitor",
    "captopril": "ACE inhibitor",

    "losartan": "ARB",
    "valsartan": "ARB",
    "irbesartan": "ARB",

    "amlodipine": "Calcium-channel blocker",
    "nifedipine": "Calcium-channel blocker",

    "metoprolol": "Beta blocker",
    "atenolol": "Beta blocker",
    "propranolol": "Beta blocker",
    "carvedilol": "Beta blocker",

    "omeprazole": "Proton-pump inhibitor",
    "esomeprazole": "Proton-pump inhibitor",
    "pantoprazole": "Proton-pump inhibitor",

    "sertraline": "SSRI",
    "fluoxetine": "SSRI",
    "escitalopram": "SSRI",
    "paroxetine": "SSRI",

    "alprazolam": "Benzodiazepine",
    "lorazepam": "Benzodiazepine",
    "clonazepam": "Benzodiazepine",
    "diazepam": "Benzodiazepine",

    "phenytoin": "Antiepileptic",
    "carbamazepine": "Antiepileptic",
    "valproic acid": "Antiepileptic",
    "lamotrigine": "Antiepileptic",
    "levetiracetam": "Antiepileptic",
    "topiramate": "Antiepileptic",
    "gabapentin": "Antiepileptic",
    "pregabalin": "Antiepileptic",

    "rifampin": "Rifamycin antibiotic",
    "azithromycin": "Macrolide antibiotic",
    "erythromycin": "Macrolide antibiotic",
    "clarithromycin": "Macrolide antibiotic",
    "ciprofloxacin": "Fluoroquinolone antibiotic",
    "amoxicillin": "Penicillin antibiotic",

    "fluconazole": "Azole antifungal",
    "ketoconazole": "Azole antifungal",
    "itraconazole": "Azole antifungal",

    "amiodarone": "Antiarrhythmic",
    "sotalol": "Antiarrhythmic",

    "digoxin": "Cardiac glycoside",
    "nitroglycerin": "Nitrate",
    "sildenafil": "PDE-5 inhibitor",
    "tadalafil": "PDE-5 inhibitor",

    "tramadol": "Opioid analgesic",
    "codeine": "Opioid analgesic",
    "morphine": "Opioid analgesic",
    "oxycodone": "Opioid analgesic",
    "fentanyl": "Opioid analgesic",

    "ondansetron": "5-HT3 antagonist",
    "metoclopramide": "Prokinetic / antiemetic",
    "haloperidol": "Antipsychotic",

    "prednisone": "Corticosteroid",
    "dexamethasone": "Corticosteroid",

    "furosemide": "Loop diuretic",
    "hydrochlorothiazide": "Thiazide diuretic",
    "spironolactone": "Potassium-sparing diuretic",

    "levothyroxine": "Thyroid hormone",
    "methotrexate": "Antimetabolite / immunosuppressant",

    "tacrolimus": "Calcineurin inhibitor",
    "cyclosporine": "Calcineurin inhibitor",

    "colchicine": "Anti-gout agent",
    "allopurinol": "Xanthine oxidase inhibitor"
}


# =========================================================
# COMMON DRUGS
# =========================================================

KNOWN_DRUGS = set(DRUG_CLASSES.keys())

KNOWN_DRUGS.update({

    "acetaminophen",
    "insulin",
    "lansoprazole",
    "rabeprazole",
    "famotidine",
    "diphenhydramine",
    "loratadine",
    "cetirizine",
    "montelukast",
    "albuterol",
    "salbutamol",
    "fluticasone",
    "budesonide",
    "tiotropium",
    "infliximab",
    "adalimumab",
    "tofacitinib",
    "cyclophosphamide",
    "sucralfate",
    "repaglinide",
    "canagliflozin",
    "ezetimibe",
    "gemfibrozil",
    "caffeine",
    "theophylline",
    "sumatriptan",
    "ranolazine",
    "loperamide",
    "mesalamine",
    "aprepitant",
    "granisetron"
})


# =========================================================
# DRUG SUFFIX HEURISTICS
# =========================================================

DRUG_SUFFIXES = (
    "nib",
    "mab",
    "zumab",
    "tinib",
    "ciclib",
    "parib",
    "vastatin",
    "sartan",
    "pril",
    "olol",
    "olide",
    "azide",
    "mycin",
    "cycline",
    "floxacin",
    "micin",
    "sone",
    "nide",
    "mide",
    "zide",
    "pam",
    "lam",
    "dipine",
    "pramine",
    "triptyline",
    "prazole",
    "tidine",
    "xetine",
    "pram",
    "done",
    "zodone",
    "tide",
    "formin",
    "cillin",
    "bactam",
    "cef",
    "penem",
    "vir",
    "navir",
    "previr"
)


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_drug(name):

    name = name.strip().lower()

    return ALIASES.get(
        name,
        name
    )


# =========================================================
# DRUG CLASS
# =========================================================

def get_drug_class(name):

    normalized = normalize_drug(name)

    if normalized in DRUG_CLASSES:
        return DRUG_CLASSES[normalized]

    return "Drug class not mapped"


# =========================================================
# FDA LABEL FETCH
# =========================================================

@st.cache_data(ttl=3600)
def fetch_label(
    drug_name,
    search_type="generic"
):

    drug_name = normalize_drug(
        drug_name
    )

    if search_type == "brand":

        field = "openfda.brand_name"

    else:

        field = "openfda.generic_name"

    search_name = drug_name.upper()

    queries = [
        f'{field}:"{search_name}"',
        f"{field}:{search_name}"
    ]

    for query in queries:

        try:

            response = requests.get(
                FDA_URL,
                params={
                    "search": query,
                    "limit": 1
                },
                timeout=15
            )

            if response.status_code == 200:

                results = response.json().get(
                    "results",
                    []
                )

                if results:

                    return results[0]

        except (
            requests.RequestException,
            ValueError
        ):

            continue

    return None


# =========================================================
# INTERACTION SECTION
# =========================================================

def get_interaction_text(label):

    if not label:
        return ""

    interaction = label.get(
        "drug_interactions"
    )

    if isinstance(
        interaction,
        list
    ):

        return " ".join(
            interaction
        )

    if isinstance(
        interaction,
        str
    ):

        return interaction

    for key, value in label.items():

        if "drug_interaction" in key.lower():

            if isinstance(
                value,
                list
            ):

                return " ".join(
                    value
                )

            if isinstance(
                value,
                str
            ):

                return value

    return ""


# =========================================================
# EVIDENCE CATEGORY ENGINE
# =========================================================

def classify_evidence(text):

    text_lower = text.lower()

    categories = []

    rules = [

        (
            [
                "bleeding",
                "hemorrhage",
                "hemorrhagic"
            ],
            "🩸 Bleeding / Hemorrhage"
        ),

        (
            [
                "qt prolongation",
                "qt interval",
                "torsade",
                "torsades"
            ],
            "❤️ QT / Cardiac Rhythm"
        ),

        (
            [
                "serotonin syndrome",
                "serotonergic"
            ],
            "🧠 Serotonergic Effect"
        ),

        (
            [
                "hypoglycemia",
                "blood glucose"
            ],
            "🩸 Glucose Effect"
        ),

        (
            [
                "hypotension",
                "blood pressure"
            ],
            "📉 Blood Pressure"
        ),

        (
            [
                "sedation",
                "central nervous system depression",
                "cns depression"
            ],
            "😴 CNS Depression / Sedation"
        ),

        (
            [
                "cyp3a4",
                "cyp2c9",
                "cyp2c19",
                "cyp2d6"
            ],
            "🧬 CYP Enzyme Interaction"
        ),

        (
            [
                "renal impairment",
                "renal function",
                "kidney"
            ],
            "🫘 Renal Function"
        ),

        (
            [
                "hepatic impairment",
                "hepatic function",
                "liver"
            ],
            "🫀 Hepatic Function"
        ),

        (
            [
                "seizure",
                "convulsion"
            ],
            "⚡ Seizure Risk"
        ),

        (
            [
                "arrhythmia",
                "cardiac"
            ],
            "❤️ Cardiac Effect"
        )
    ]

    for keywords, category in rules:

        if any(
            keyword in text_lower
            for keyword in keywords
        ):

            categories.append(
                category
            )

    if not categories:

        categories.append(
            "📄 FDA Interaction Evidence"
        )

    return categories


# =========================================================
# EVIDENCE STRENGTH
# =========================================================

def get_evidence_strength(
    direct_match
):

    if direct_match:

        return (
            "🟢 Direct FDA label evidence",
            "The checked FDA drug-label "
            "interaction section directly "
            "mentions the other medicine."
        )

    return (
        "⚪ No direct mention found",
        "No direct mention was found in "
        "the checked FDA interaction section."
    )


# =========================================================
# EXTRACT DRUG MENTIONS
# =========================================================

def extract_drug_mentions(
    text,
    label
):

    if not text:

        return []

    text_lower = text.lower()

    known = set(
        KNOWN_DRUGS
    )

    openfda = label.get(
        "openfda",
        {}
    )

    for field in [
        "brand_name",
        "generic_name",
        "substance_name"
    ]:

        values = openfda.get(
            field,
            []
        )

        if isinstance(
            values,
            str
        ):

            values = [values]

        for value in values:

            if isinstance(
                value,
                str
            ):

                known.add(
                    value.lower().strip()
                )

    found = []

    seen = set()

    for drug in known:

        if len(drug) < 3:

            continue

        pattern = (
            r"\b"
            + re.escape(drug)
            + r"\b"
        )

        match = re.search(
            pattern,
            text_lower
        )

        if match:

            if drug in seen:

                continue

            start = max(
                0,
                match.start() - 100
            )

            end = min(
                len(text),
                match.end() + 120
            )

            found.append(
                {
                    "drug": drug.title(),
                    "context": text[
                        start:end
                    ],
                    "method": "dictionary"
                }
            )

            seen.add(
                drug
            )

    return found


# =========================================================
# CHECK TWO DRUGS
# =========================================================

def check_two_drugs(
    drug_a,
    drug_b
):

    normalized_a = normalize_drug(
        drug_a
    )

    normalized_b = normalize_drug(
        drug_b
    )

    label_a = fetch_label(
        normalized_a,
        "generic"
    )

    label_b = fetch_label(
        normalized_b,
        "generic"
    )

    if not label_a and not label_b:

        return {
            "found": False,
            "status": "error",
            "reason": (
                "No FDA label was found "
                "for either medicine."
            )
        }

    evidence = []

    # -----------------------------------------------------
    # DRUG A LABEL
    # -----------------------------------------------------

    if label_a:

        text_a = get_interaction_text(
            label_a
        )

        if text_a:

            aliases_b = {
                normalized_b,
                drug_b.lower()
            }

            for alias, canonical in ALIASES.items():

                if canonical == normalized_b:

                    aliases_b.add(
                        alias
                    )

            for name in aliases_b:

                pattern = (
                    r"\b"
                    + re.escape(name)
                    + r"\b"
                )

                match = re.search(
                    pattern,
                    text_a.lower()
                )

                if match:

                    start = max(
                        0,
                        match.start() - 180
                    )

                    end = min(
                        len(text_a),
                        match.end() + 300
                    )

                    evidence.append(
                        {
                            "source": drug_a,
                            "context": text_a[
                                start:end
                            ]
                        }
                    )

                    break

    # -----------------------------------------------------
    # DRUG B LABEL
    # -----------------------------------------------------

    if label_b:

        text_b = get_interaction_text(
            label_b
        )

        if text_b:

            aliases_a = {
                normalized_a,
                drug_a.lower()
            }

            for alias, canonical in ALIASES.items():

                if canonical == normalized_a:

                    aliases_a.add(
                        alias
                    )

            for name in aliases_a:

                pattern = (
                    r"\b"
                    + re.escape(name)
                    + r"\b"
                )

                match = re.search(
                    pattern,
                    text_b.lower()
                )

                if match:

                    start = max(
                        0,
                        match.start() - 180
                    )

                    end = min(
                        len(text_b),
                        match.end() + 300
                    )

                    evidence.append(
                        {
                            "source": drug_b,
                            "context": text_b[
                                start:end
                            ]
                        }
                    )

                    break

    if evidence:

        return {
            "found": True,
            "status": "evidence",
            "evidence": evidence
        }

    return {
        "found": False,
        "status": "no_match",
        "reason": (
            "No direct mention of the other "
            "medicine was found in the "
            "checked FDA interaction sections."
        )
    }


# =========================================================
# SINGLE DRUG PROFILE
# =========================================================

def get_drug_profile(
    drug_name,
    search_type="generic"
):

    label = fetch_label(
        drug_name,
        search_type
    )

    if not label:

        return {
            "ok": False,
            "error": (
                f"No FDA label found for "
                f"'{drug_name}'."
            )
        }

    openfda = label.get(
        "openfda",
        {}
    )

    brand = openfda.get(
        "brand_name",
        []
    )

    generic = openfda.get(
        "generic_name",
        []
    )

    manufacturer_list = openfda.get(
        "manufacturer_name",
        []
    )

    manufacturer = (
        manufacturer_list[0]
        if manufacturer_list
        else "Unknown"
    )

    text = get_interaction_text(
        label
    )

    mentions = extract_drug_mentions(
        text,
        label
    )

    return {
        "ok": True,
        "drug": drug_name,
        "brand": brand,
        "generic": generic,
        "manufacturer": manufacturer,
        "interaction_text": text,
        "interactions": mentions
    }


# =========================================================
# CLINICAL INTERPRETATION
# =========================================================

def build_interpretation(
    drug_a,
    drug_b,
    context
):

    class_a = get_drug_class(
        drug_a
    )

    class_b = get_drug_class(
        drug_b
    )

    categories = classify_evidence(
        context
    )

    category_text = "\n".join(
        f"- {category}"
        for category in categories
    )

    return f"""
### 🔎 Interaction Summary

**{drug_a}**  
`{class_a}`

**{drug_b}**  
`{class_b}`

### 🎯 Evidence Category

{category_text}

### 📊 Evidence Level

🟢 **Direct FDA label evidence**

The retrieved FDA interaction section
contains a direct mention of the other
medicine.

### 🧠 Pharmacy Interpretation

The tool has identified clinically
relevant terms and interaction signals
from the retrieved FDA label text.
This is an educational prototype.

"""
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "MedCheck AI V3 | U.S. FDA openFDA data | "
    "Evidence-Based Educational Prototype | "
    "Not Medical Advice"
)