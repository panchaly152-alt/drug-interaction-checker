import streamlit as st
import requests
import re
from openai import OpenAI

# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="MedCheck AI",
    page_icon="💊",
    layout="centered"
)

BASE_URL = "https://api.fda.gov/drug/label.json"

# OpenAI API key is stored securely in Streamlit Secrets
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    client = None


# =========================================================
# DRUG KNOWLEDGE
# =========================================================

KNOWN_DRUGS = {
    "warfarin", "aspirin", "ibuprofen", "naproxen", "acetaminophen",
    "paracetamol", "amoxicillin", "azithromycin", "ciprofloxacin",
    "metformin", "insulin", "atorvastatin", "simvastatin",
    "rosuvastatin", "pravastatin", "fluvastatin", "lovastatin",
    "lisinopril", "enalapril", "captopril", "amlodipine",
    "nifedipine", "felodipine", "metoprolol", "atenolol",
    "propranolol", "carvedilol", "bisoprolol", "losartan",
    "valsartan", "irbesartan", "omeprazole", "esomeprazole",
    "lansoprazole", "pantoprazole", "rabeprazole", "ranitidine",
    "famotidine", "sertraline", "fluoxetine", "escitalopram",
    "paroxetine", "alprazolam", "lorazepam", "clonazepam",
    "diazepam", "phenytoin", "carbamazepine", "valproic acid",
    "lamotrigine", "levetiracetam", "topiramate", "gabapentin",
    "pregabalin", "levothyroxine", "methimazole", "prednisone",
    "dexamethasone", "furosemide", "hydrochlorothiazide",
    "spironolactone", "digoxin", "clopidogrel", "heparin",
    "enoxaparin", "rivaroxaban", "apixaban", "dabigatran",
    "phenobarbital", "rifampin", "ketoconazole", "fluconazole",
    "itraconazole", "erythromycin", "clarithromycin", "grapefruit",
    "alcohol", "caffeine", "theophylline", "codeine", "morphine",
    "tramadol", "oxycodone", "fentanyl", "ondansetron",
    "promethazine", "diphenhydramine", "loratadine", "cetirizine",
    "montelukast", "salbutamol", "albuterol", "fluticasone",
    "budesonide", "tiotropium", "methotrexate", "cyclosporine",
    "tacrolimus", "allopurinol", "colchicine", "sildenafil",
    "tadalafil", "finasteride", "tamsulosin", "donepezil",
    "memantine", "levodopa", "carbidopa", "sumatriptan",
    "nitroglycerin", "ranolazine", "amiodarone", "sotalol",
    "adenosine", "streptokinase", "cilostazol", "epoetin alfa",
    "filgrastim", "deferoxamine", "hydroxyurea", "omalizumab",
    "epinephrine", "dopamine", "milrinone", "sacubitril",
    "acetazolamide", "lacosamide", "rufinamide", "cannabidiol",
    "clobazam", "amitriptyline", "diclofenac", "ketorolac",
    "indomethacin", "meloxicam", "celecoxib", "metoclopramide",
    "haloperidol", "granisetron", "aprepitant", "scopolamine",
    "lactulose", "loperamide", "mesalamine", "infliximab",
    "adalimumab", "tofacitinib", "cyclophosphamide", "sucralfate",
    "glipizide", "glyburide", "repaglinide", "pioglitazone",
    "sitagliptin", "canagliflozin", "dapagliflozin", "empagliflozin",
    "liraglutide", "semaglutide", "insulin regular",
    "insulin glargine", "pramlintide", "ezetimibe", "gemfibrozil"
}

DRUG_SUFFIXES = (
    "nib", "mab", "zumab", "tinib", "ciclib", "parib", "vastatin",
    "sartan", "pril", "olol", "olide", "azide", "mycin", "cycline",
    "floxacin", "micin", "sone", "nide", "mide", "zide", "pam",
    "lam", "dipine", "pramine", "triptyline", "prazole", "tidine",
    "xetine", "pram", "done", "zodone", "lone", "zone", "tide",
    "glitazone", "formin", "glipizide", "glyburide", "sulfa",
    "cillin", "bactam", "cef", "penem", "vir", "navir", "previr",
    "tegravir", "vudine", "citabine", "arabine"
)

SKIP_WORDS = {
    "the", "and", "for", "with", "may", "use", "see", "fda",
    "patients", "clinical", "studies", "table", "figure", "section",
    "drug", "drugs", "medicine", "product", "administration",
    "treatment", "therapy", "dose", "patient", "subject", "study",
    "effect", "effects", "adverse", "reaction", "monitor", "increase",
    "decrease", "concomitant", "coadministration", "pharmacokinetics",
    "metabolism", "absorption", "distribution", "elimination",
    "plasma", "serum", "blood", "liver", "kidney", "renal", "hepatic",
    "cardiac", "gastrointestinal", "central", "nervous", "system",
    "respiratory", "oral", "intravenous", "subcutaneous",
    "intramuscular", "topical", "inhibitor", "inducer", "substrate",
    "receptor", "agonist", "antagonist", "blocker", "channel",
    "enzyme", "cyp", "food", "grapefruit", "juice", "alcohol",
    "smoking", "pregnancy", "pediatric", "geriatric", "male",
    "female", "children", "adults", "mild", "moderate", "severe",
    "significant", "clinically", "recommended", "avoid", "caution",
    "contraindicated", "approximately", "result", "found", "observed",
    "reported", "shown", "compared", "versus", "placebo", "control",
    "single", "multiple", "daily", "week", "month", "year", "high",
    "low", "normal", "abnormal", "increased", "decreased", "greater",
    "less", "before", "after", "during", "following", "due", "because",
    "however", "therefore", "thus", "addition", "including", "example",
    "manufacturer", "company", "brand", "generic", "formulation",
    "tablet", "capsule", "injection", "solution", "cream", "ointment",
    "gel", "patch", "inhaler", "spray", "drop", "package", "insert",
    "label", "prescribing", "information", "warning", "precaution",
    "overdosage", "description", "indications", "contraindications",
    "dosage", "supplied", "storage", "handling", "counseling",
    "revised", "date", "copyright", "trademark", "all", "rights",
    "reserved", "disclaimer", "contact", "phone", "email", "website",
    "address", "usa", "united", "states", "america", "europe",
    "international", "global", "inc", "llc", "ltd", "corp",
    "corporation", "division", "subsidiary", "group", "organization",
    "institution", "university", "hospital", "clinic", "center",
    "department", "laboratory", "research", "physician", "doctor",
    "pharmacist", "nurse", "practitioner", "specialist", "consultant",
    "committee", "panel", "board", "society", "association",
    "foundation", "council", "academy", "college", "school", "institute"
}


# =========================================================
# FDA DATA FUNCTIONS
# =========================================================

def fetch_label(drug_name, search_type="generic"):
    """Fetch an FDA drug label by generic or brand name."""

    field = (
        "openfda.brand_name"
        if search_type == "brand"
        else "openfda.generic_name"
    )

    name = drug_name.strip().upper()

    for query in (
        f'{field}:"{name}"',
        f"{field}:{name}"
    ):
        try:
            response = requests.get(
                BASE_URL,
                params={"search": query, "limit": 1},
                timeout=15
            )

            if response.status_code == 200:
                results = response.json().get("results")

                if results:
                    return results[0]

        except (requests.RequestException, ValueError):
            continue

    return None


def get_interaction_text(label):
    """Extract the complete drug-interactions section."""

    if not label:
        return None

    interactions = label.get("drug_interactions")

    if isinstance(interactions, list) and interactions:
        return " ".join(interactions)

    for key, value in label.items():

        if "drug_interaction" in key.lower():

            if isinstance(value, list) and value:
                return " ".join(value)

            if isinstance(value, str):
                return value

    return None


def extract_drugs(text, label):
    """Identify drug mentions using dictionary and heuristic matching."""

    if not text:
        return []

    known = set(KNOWN_DRUGS)

    openfda = label.get("openfda", {}) if isinstance(label, dict) else {}

    for field in ["brand_name", "generic_name", "substance_name"]:

        values = openfda.get(field, [])

        if isinstance(values, str):
            values = [values]

        for value in values:
            known.add(value.lower().strip())

    found = []
    text_lower = text.lower()
    seen = set()

    # Dictionary matching
    for drug in known:

        if len(drug) < 3:
            continue

        pattern = r"\b" + re.escape(drug) + r"\b"

        if re.search(pattern, text_lower) and drug not in seen:

            index = text_lower.find(drug)

            start = max(0, index - 60)
            end = min(len(text), index + len(drug) + 60)

            found.append({
                "drug": drug.title(),
                "context": text[start:end],
                "method": "dictionary"
            })

            seen.add(drug)

    # Heuristic matching
    cap_pattern = (
        r"\b([A-Z][a-zA-Z]+"
        r"(?:\s+[A-Z][a-zA-Z]+){0,2})\b"
    )

    for match in re.finditer(cap_pattern, text):

        candidate = match.group(1)
        candidate_lower = candidate.lower()

        if (
            candidate_lower in SKIP_WORDS
            or len(candidate_lower) < 3
            or candidate_lower in seen
        ):
            continue

        looks_like_drug = any(
            candidate_lower.endswith(suffix)
            for suffix in DRUG_SUFFIXES
        )

        if not looks_like_drug:

            for word in candidate_lower.split():

                if word in known and len(word) > 3:
                    looks_like_drug = True
                    break

        if looks_like_drug:

            index = text_lower.find(candidate_lower)

            start = max(0, index - 60)
            end = min(
                len(text),
                index + len(candidate) + 60
            )

            found.append({
                "drug": candidate,
                "context": text[start:end],
                "method": "heuristic"
            })

            seen.add(candidate_lower)

    found.sort(
        key=lambda x: (
            text_lower.find(x["drug"].lower())
            if text_lower.find(x["drug"].lower()) != -1
            else 99999
        )
    )

    return found


def get_all_interactions(drug_name, search_type="generic"):

    label = fetch_label(drug_name, search_type)

    if label is None:
        return {
            "ok": False,
            "error": f"No FDA label found for '{drug_name}'"
        }

    openfda = label.get("openfda", {})

    brand = openfda.get("brand_name", [])
    generic = openfda.get("generic_name", [])

    manufacturers = openfda.get("manufacturer_name", [])

    manufacturer = (
        manufacturers[0]
        if manufacturers
        else "Unknown"
    )

    interaction_text = get_interaction_text(label)

    if not interaction_text:

        return {
            "ok": True,
            "drug": drug_name,
            "brand": brand,
            "generic": generic,
            "manufacturer": manufacturer,
            "interactions": [],
            "note": "No interactions section found in FDA label."
        }

    drugs = extract_drugs(
        interaction_text,
        label
    )

    return {
        "ok": True,
        "drug": drug_name,
        "brand": brand,
        "generic": generic,
        "manufacturer": manufacturer,
        "interactions": drugs
    }


def check_two(drug_a, drug_b):
    """Check both drug labels for evidence mentioning the other drug."""

    data_a = get_all_interactions(
        drug_a,
        "generic"
    )

    data_b = get_all_interactions(
        drug_b,
        "generic"
    )

    a_lower = drug_a.lower()
    b_lower = drug_b.lower()

    if data_a["ok"]:

        for item in data_a.get("interactions", []):

            interaction_drug = item["drug"].lower()

            if (
                interaction_drug == b_lower
                or b_lower in interaction_drug
                or interaction_drug in b_lower
            ):

                return {
                    "found": True,
                    "context": item["context"],
                    "method": item["method"],
                    "source": drug_a
                }

    if data_b["ok"]:

        for item in data_b.get("interactions", []):

            interaction_drug = item["drug"].lower()

            if (
                interaction_drug == a_lower
                or a_lower in interaction_drug
                or interaction_drug in a_lower
            ):

                return {
                    "found": True,
                    "context": item["context"],
                    "method": item["method"],
                    "source": drug_b
                }

    if not data_a["ok"] and not data_b["ok"]:

        return {
            "found": False,
            "reason": "Could not find an FDA label for either drug."
        }

    reasons = []

    if data_a["ok"]:
        reasons.append(
            f"no mention of {drug_b} in {drug_a}'s label"
        )

    if data_b["ok"]:
        reasons.append(
            f"no mention of {drug_a} in {drug_b}'s label"
        )

    return {
        "found": False,
        "reason": (" and ".join(reasons) + ".").capitalize()
    }


# =========================================================
# AI EVIDENCE EXPLANATION
# =========================================================

def generate_ai_explanation(drug_a, drug_b, evidence):

    if client is None:

        return (
            "AI explanation is unavailable because the OpenAI API key "
            "is not configured in Streamlit Secrets."
        )

    prompt = f"""
You are an educational pharmacy information assistant.

Analyze ONLY the FDA drug-label evidence provided below.

Drug A: {drug_a}
Drug B: {drug_b}

FDA label evidence:
{evidence}

Provide a concise explanation using exactly these sections:

### What the evidence says
Explain what the retrieved FDA label information states.

### Why it may matter
Explain the mechanism or clinical significance ONLY if supported
by the supplied evidence.

### Key point
Give one concise summary.

Strict rules:
- Do not invent medical facts.
- Do not add unsupported interaction information.
- Do not assign Major, Moderate, or Minor severity unless the
  supplied evidence explicitly supports it.
- Do not tell the user to start, stop, or change medication.
- If the evidence is insufficient, clearly state that.
- Keep the language understandable for a pharmacy student.
- This is educational information, not medical advice.
"""

    try:

        response = client.responses.create(
            model="gpt-5.6",
            input=prompt
        )

        return response.output_text

    except Exception as error:

        return (
            "AI explanation could not be generated.\n\n"
            f"Technical message: {error}"
        )


# =========================================================
# USER INTERFACE
# =========================================================

st.title("💊 MedCheck AI")

st.caption(
    "Intelligent Drug Interaction Analysis | "
    "Powered by U.S. FDA openFDA + AI"
)

st.warning(
    "⚠️ Educational tool only — not a substitute for advice "
    "from a licensed pharmacist or physician. A 'no interaction "
    "found' result does not guarantee safety. Always confirm "
    "medication decisions with a healthcare professional."
)

st.markdown("---")

tab1, tab2 = st.tabs(
    ["🔍 Two-Drug Check", "📋 Single Drug Profile"]
)


# =========================================================
# TWO DRUG CHECK
# =========================================================

with tab1:

    column1, column2 = st.columns(2)

    with column1:

        drug_1 = st.text_input(
            "Drug 1",
            placeholder="e.g. Warfarin"
        ).strip()

    with column2:

        drug_2 = st.text_input(
            "Drug 2",
            placeholder="e.g. Aspirin"
        ).strip()

    if st.button(
        "Analyze Interaction",
        use_container_width=True
    ):

        if not drug_1 or not drug_2:

            st.error(
                "Please enter both drug names."
            )

        elif drug_1.lower() == drug_2.lower():

            st.warning(
                "Please enter two different medicines."
            )

        else:

            with st.spinner(
                "Fetching evidence from FDA openFDA..."
            ):

                result = check_two(
                    drug_1,
                    drug_2
                )

            if result["found"]:

                st.error(
                    "⚠️ POTENTIAL INTERACTION IDENTIFIED"
                )

                st.write(
                    f"**{drug_1}** + **{drug_2}**"
                )

                st.info(
                    result["context"]
                )

                st.caption(
                    f"Evidence source: "
                    f"{result['source']}'s FDA Drug Label · "
                    f"Detection: "
                    f"{result['method'].title()}"
                )

                st.markdown("---")

                st.subheader(
                    "🤖 AI Evidence Explanation"
                )

                with st.spinner(
                    "Analyzing retrieved FDA evidence..."
                ):

                    explanation = generate_ai_explanation(
                        drug_1,
                        drug_2,
                        result["context"]
                    )

                st.markdown(
                    explanation
                )

                st.caption(
                    "AI explanation is grounded in retrieved "
                    "FDA label evidence. Educational use only."
                )

            else:

                st.success(
                    "✅ No interaction found in the checked FDA labels"
                )

                st.caption(
                    "Source: U.S. FDA Drug Label via openFDA"
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
        key="d3"
    ).strip()

    search_type = st.radio(
        "Search by",
        ["generic", "brand"],
        horizontal=True
    )

    if st.button(
        "Find Interactions",
        key="btn2",
        use_container_width=True
    ):

        if not drug_input:

            st.error(
                "Please enter a drug name."
            )

        else:

            with st.spinner(
                "Scanning FDA drug-label data..."
            ):

                data = get_all_interactions(
                    drug_input,
                    search_type
                )

            if not data["ok"]:

                st.error(
                    data["error"]
                )

            else:

                column1, column2 = st.columns(2)

                column1.metric(
                    "Detected Drug Mentions",
                    len(data["interactions"])
                )

                column2.metric(
                    "Manufacturer",
                    data["manufacturer"][:20]
                )

                st.write(
                    "Brand:",
                    ", ".join(data["brand"]) or "N/A"
                )

                st.write(
                    "Generic:",
                    ", ".join(data["generic"]) or "N/A"
                )

                st.divider()

                if not data["interactions"]:

                    st.warning(
                        "No interacting drug mentions were detected."
     