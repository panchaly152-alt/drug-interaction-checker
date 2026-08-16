import streamlit as st
import requests
import re


# =========================================================
# MEDCHECK AI — FREE V2
# FDA EVIDENCE + RULE-BASED PHARMACY ANALYSIS
# No paid AI API required
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
    "zoloft": "sertraline"
}


# =========================================================
# COMMON DRUG DATABASE
# =========================================================

KNOWN_DRUGS = {
    "warfarin",
    "aspirin",
    "ibuprofen",
    "naproxen",
    "acetaminophen",
    "amoxicillin",
    "azithromycin",
    "ciprofloxacin",
    "metformin",
    "insulin",
    "atorvastatin",
    "simvastatin",
    "rosuvastatin",
    "pravastatin",
    "lovastatin",
    "lisinopril",
    "enalapril",
    "captopril",
    "amlodipine",
    "nifedipine",
    "felodipine",
    "metoprolol",
    "atenolol",
    "propranolol",
    "carvedilol",
    "bisoprolol",
    "losartan",
    "valsartan",
    "irbesartan",
    "omeprazole",
    "esomeprazole",
    "lansoprazole",
    "pantoprazole",
    "rabeprazole",
    "famotidine",
    "sertraline",
    "fluoxetine",
    "escitalopram",
    "paroxetine",
    "alprazolam",
    "lorazepam",
    "clonazepam",
    "diazepam",
    "phenytoin",
    "carbamazepine",
    "valproic acid",
    "lamotrigine",
    "levetiracetam",
    "topiramate",
    "gabapentin",
    "pregabalin",
    "levothyroxine",
    "prednisone",
    "dexamethasone",
    "furosemide",
    "hydrochlorothiazide",
    "spironolactone",
    "digoxin",
    "clopidogrel",
    "heparin",
    "enoxaparin",
    "rivaroxaban",
    "apixaban",
    "dabigatran",
    "phenobarbital",
    "rifampin",
    "ketoconazole",
    "fluconazole",
    "itraconazole",
    "erythromycin",
    "clarithromycin",
    "codeine",
    "morphine",
    "tramadol",
    "oxycodone",
    "fentanyl",
    "ondansetron",
    "promethazine",
    "diphenhydramine",
    "loratadine",
    "cetirizine",
    "montelukast",
    "salbutamol",
    "albuterol",
    "fluticasone",
    "budesonide",
    "tiotropium",
    "methotrexate",
    "cyclosporine",
    "tacrolimus",
    "allopurinol",
    "colchicine",
    "sildenafil",
    "tadalafil",
    "finasteride",
    "tamsulosin",
    "donepezil",
    "memantine",
    "levodopa",
    "carbidopa",
    "sumatriptan",
    "nitroglycerin",
    "ranolazine",
    "amiodarone",
    "sotalol",
    "cilostazol",
    "amitriptyline",
    "diclofenac",
    "ketorolac",
    "indomethacin",
    "meloxicam",
    "celecoxib",
    "metoclopramide",
    "haloperidol",
    "granisetron",
    "aprepitant",
    "loperamide",
    "mesalamine",
    "infliximab",
    "adalimumab",
    "tofacitinib",
    "cyclophosphamide",
    "sucralfate",
    "glipizide",
    "glyburide",
    "repaglinide",
    "pioglitazone",
    "sitagliptin",
    "canagliflozin",
    "dapagliflozin",
    "empagliflozin",
    "liraglutide",
    "semaglutide",
    "ezetimibe",
    "gemfibrozil",
    "caffeine",
    "theophylline"
}


# =========================================================
# DRUG-LIKE SUFFIXES
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
    "previr",
    "tegravir",
    "vudine",
    "citabine"
)


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_drug(name):
    name = name.strip().lower()

    if name in ALIASES:
        return ALIASES[name]

    return name


# =========================================================
# FDA LABEL FETCH
# =========================================================

@st.cache_data(ttl=3600)
def fetch_label(drug_name, search_type="generic"):

    drug_name = normalize_drug(drug_name)

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
# INTERACTION TEXT
# =========================================================

def get_interaction_text(label):

    if not label:
        return ""

    interactions = label.get(
        "drug_interactions"
    )

    if isinstance(
        interactions,
        list
    ):

        return " ".join(
            interactions
        )

    if isinstance(
        interactions,
        str
    ):

        return interactions

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
# FIND DRUG MENTIONS
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

    # -----------------------------------------------------
    # Dictionary matching
    # -----------------------------------------------------

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
                match.end() + 100
            )

            found.append(
                {
                    "drug": drug.title(),
                    "context": text[start:end],
                    "method": "dictionary"
                }
            )

            seen.add(drug)

    # -----------------------------------------------------
    # Heuristic matching
    # -----------------------------------------------------

    pattern = (
        r"\b("
        r"[A-Z][a-zA-Z]+"
        r"(?:\s+[A-Z][a-zA-Z]+){0,2}"
        r")\b"
    )

    for match in re.finditer(
        pattern,
        text
    ):

        candidate = match.group(1)
        candidate_lower = candidate.lower()

        if candidate_lower in seen:
            continue

        looks_like_drug = any(
            candidate_lower.endswith(
                suffix
            )
            for suffix in DRUG_SUFFIXES
        )

        if not looks_like_drug:
            continue

        start = max(
            0,
            match.start() - 100
        )

        end = min(
            len(text),
            match.end() + 100
        )

        found.append(
            {
                "drug": candidate,
                "context": text[start:end],
                "method": "heuristic"
            }
        )

        seen.add(
            candidate_lower
        )

    return found


# =========================================================
# DRUG PROFILE
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

    interaction_text = (
        get_interaction_text(
            label
        )
    )

    mentions = extract_drug_mentions(
        interaction_text,
        label
    )

    return {
        "ok": True,
        "drug": drug_name,
        "brand": brand,
        "generic": generic,
        "manufacturer": manufacturer,
        "interaction_text": interaction_text,
        "interactions": mentions
    }


# =========================================================
# TWO DRUG ANALYSIS
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
    # Check Drug A label
    # -----------------------------------------------------

    if label_a:

        text_a = get_interaction_text(
            label_a
        )

        if text_a:

            text_lower = text_a.lower()

            aliases_b = {
                normalized_b,
                drug_b.lower()
            }

            for alias, canonical in ALIASES.items():

                if canonical == normalized_b:
                    aliases_b.add(alias)

            for name in aliases_b:

                pattern = (
                    r"\b"
                    + re.escape(name)
                    + r"\b"
                )

                if re.search(
                    pattern,
                    text_lower
                ):

                    match = re.search(
                        pattern,
                        text_lower
                    )

                    start = max(
                        0,
                        match.start() - 160
                    )

                    end = min(
                        len(text_a),
                        match.end() + 260
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
    # Check Drug B label
    # -----------------------------------------------------

    if label_b:

        text_b = get_interaction_text(
            label_b
        )

        if text_b:

            text_lower = text_b.lower()

            aliases_a = {
                normalized_a,
                drug_a.lower()
            }

            for alias, canonical in ALIASES.items():

                if canonical == normalized_a:
                    aliases_a.add(alias)

            for name in aliases_a:

                pattern = (
                    r"\b"
                    + re.escape(name)
                    + r"\b"
                )

                if re.search(
                    pattern,
                    text_lower
                ):

                    match = re.search(
                        pattern,
                        text_lower
                    )

                    start = max(
                        0,
                        match.start() - 160
                    )

                    end = min(
                        len(text_b),
                        match.end() + 260
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
# EVIDENCE SIGNAL ENGINE
# =========================================================

def evidence_signals(text):

    text_lower = text.lower()

    signals = []

    rules = [
        (
            [
                "bleeding",
                "hemorrhage",
                "hemorrhagic"
            ],
            "🩸 Bleeding-related signal"
        ),
        (
            [
                "qt prolong",
                "torsade",
                "arrhythmia"
            ],
            "❤️ Cardiac rhythm/QT signal"
        ),
        (
            [
                "hypoglycemia",
                "blood glucose"
            ],
            "🩸 Glucose-related signal"
        ),
        (
            [
                "serotonin syndrome",
                "serotonergic"
            ],
            "🧠 Serotonergic signal"
        ),
        (
            [
                "cyp3a4",
                "cyp2c9",
                "cyp2c19",
                "cyp2d6"
            ],
            "🧬 CYP enzyme interaction signal"
        ),
        (
            [
                "renal",
                "kidney",
                "creatinine"
            ],
            "🫘 Renal-function signal"
        ),
        (
            [
                "hepatic",
                "liver"
            ],
            "🫀 Hepatic-function signal"
        ),
        (
            [
                "hypotension",
                "blood pressure"
            ],
            "📉 Blood-pressure signal"
        ),
        (
            [
                "sedation",
                "central nervous system depression"
            ],
            "😴 CNS-depression signal"
        ),
        (
            [
                "seizure",
                "convulsion"
            ],
            "⚡ Seizure-related signal"
        )
    ]

    for keywords, label in rules:

        if any(
            keyword in text_lower
            for keyword in keywords
        ):

            signals.append(
                label
            )

    return signals


# =========================================================
# EVIDENCE SUMMARY
# =========================================================

def build_evidence_summary(
    drug_a,
    drug_b,
    context
):

    signals = evidence_signals(
        context
    )

    if signals:

        signal_text = "\n".join(
            f"- {signal}"
            for signal in signals
        )

    else:

        signal_text = (
            "- No predefined clinical "
            "signal detected from this "
            "text excerpt."
        )

    return f"""
### 🔎 Evidence Summary

**Medicines:** {drug_a} + {drug_b}

The FDA label evidence contains a
direct mention of the other medicine.

### 📌 Detected Evidence Signals

{signal_text}

### 🧪 Source Evidence

> {context}

### ⚠️ Interpretation

This tool identifies and summarizes
signals present in the retrieved FDA
label text. It does not assign a
clinical severity grade and does not
replace professional interaction
checking.

### 🎓 Pharmacy Learning Point

Always interpret a drug-interaction
signal using the mechanism, dose,
patient factors, formulation, and
current clinical guidance.
"""


# =========================================================
# UI HEADER
# =========================================================

st.title(
    "💊 MedCheck AI"
)

st.caption(
    "Evidence-Based Drug Interaction "
    "Analysis | Powered by U.S. FDA openFDA"
)

st.info(
    "🆓 Free version — no paid AI API required."
)

st.warning(
    "⚠️ Educational tool only. "
    "It is not a substitute for a licensed "
    "pharmacist or physician. "
    "A 'no interaction found' result does "
    "not guarantee safety."
)

st.markdown("---")


# =========================================================
# TABS
# =========================================================

tab1, tab2 = st.tabs(
    [
        "🔍 Two-Drug Check",
        "📋 Single Drug Profile"
    ]
)


# =========================================================
# TWO DRUG CHECK
# =========================================================

with tab1:

    col1, col2 = st.columns(2)

    with col1:

        drug1 = st.text_input(
            "Drug 1",
            placeholder="e.g. Warfarin"
        ).strip()

    with col2:

        drug2 = st.text_input(
            "Drug 2",
            placeholder="e.g. Aspirin"
        ).strip()

    analyze_button = st.button(
        "Analyze Interaction",
        use_container_width=True
    )

    if analyze_button:

        if not drug1 or not drug2:

            st.error(
                "Enter both drug names."
            )

        elif (
            normalize_drug(drug1)
            == normalize_drug(drug2)
        ):

                                  st.warning(
                    "Please enter two different medicines."
                )

        else:

            with st.spinner(
                "Searching FDA drug-label data..."
            ):

                result = check_two_drugs(
                    drug1,
                    drug2
                )

            if result["found"]:

                st.error(
                    "⚠️ POTENTIAL INTERACTION EVIDENCE FOUND"
                )

                st.write(
                    f"**{drug1}** + **{drug2}**"
                )

                for item in result["evidence"]:

                    st.info(
                        item["context"]
                    )

                    st.caption(
                        "Evidence source: "
                        f"{item['source']}'s FDA Drug Label"
                    )

                st.markdown("---")

                st.subheader(
                    "🧠 Evidence-Based Analysis"
                )

                combined_context = "\n\n".join(
                    item["context"]
                    for item in result["evidence"]
                )

                st.markdown(
                    build_evidence_summary(
                        drug1,
                        drug2,
                        combined_context
                    )
                )

            elif result["status"] == "error":

                st.error(
                    result["reason"]
                )

            else:

                st.success(
                    "✅ No direct interaction mention found "
                    "in the checked FDA labels"
                )

                st.caption(
                    "No direct mention was found in the "
                    "retrieved interaction sections. "
                    "This does NOT prove the combination is safe."
                )

                with st.expander(
                    "See analysis details"
                ):

                    st.write(
                        result["reason"]
                    )


# =========================================================
# SINGLE DRUG PROFILE
# =========================================================

with tab2:

    drug_input = st.text_input(
        "Drug name",
        placeholder="e.g. Metformin",
        key="single_drug"
    ).strip()

    search_type = st.radio(
        "Search by",
        ["generic", "brand"],
        horizontal=True
    )

    profile_button = st.button(
        "Find Interactions",
        key="profile_button",
        use_container_width=True
    )

    if profile_button:

        if not drug_input:

            st.error(
                "Enter a drug name."
            )

        else:

            with st.spinner(
                "Scanning FDA label..."
            ):

                profile = get_drug_profile(
                    drug_input,
                    search_type
                )

            if not profile["ok"]:

                st.error(
                    profile["error"]
                )

            else:

                col1, col2 = st.columns(2)

                col1.metric(
                    "Detected Mentions",
                    len(profile["interactions"])
                )

                col2.metric(
                    "Manufacturer",
                    profile["manufacturer"][:25]
                )

                st.write(
                    "**Brand:**",
                    ", ".join(profile["brand"])
                    if profile["brand"]
                    else "N/A"
                )
   