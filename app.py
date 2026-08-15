import streamlit as st
import requests
import re
from openai import OpenAI


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="MedCheck AI",
    page_icon="💊",
    layout="centered"
)

FDA_URL = "https://api.fda.gov/drug/label.json"


# =========================================================
# OPENAI CLIENT
# =========================================================

def get_openai_client():
    try:
        api_key = st.secrets["OPENAI_API_KEY"]

        if not api_key:
            return None

        return OpenAI(api_key=api_key)

    except Exception:
        return None


client = get_openai_client()


# =========================================================
# DRUG DATABASE / PATTERNS
# =========================================================

KNOWN_DRUGS = {
    "warfarin",
    "aspirin",
    "ibuprofen",
    "naproxen",
    "acetaminophen",
    "paracetamol",
    "amoxicillin",
    "azithromycin",
    "ciprofloxacin",
    "metformin",
    "insulin",
    "atorvastatin",
    "simvastatin",
    "rosuvastatin",
    "pravastatin",
    "fluvastatin",
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
    "ranitidine",
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
    "methimazole",
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
    "adenosine",
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
    "scopolamine",
    "lactulose",
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
    "grapefruit",
    "alcohol",
    "caffeine",
    "theophylline"
}


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
    "glitazone",
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


SKIP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "may",
    "use",
    "see",
    "fda",
    "patients",
    "clinical",
    "studies",
    "table",
    "figure",
    "section",
    "drug",
    "drugs",
    "medicine",
    "product",
    "administration",
    "treatment",
    "therapy",
    "dose",
    "patient",
    "subject",
    "study",
    "effect",
    "effects",
    "adverse",
    "reaction",
    "monitor",
    "increase",
    "decrease",
    "concomitant",
    "coadministration",
    "pharmacokinetics",
    "metabolism",
    "absorption",
    "distribution",
    "elimination",
    "plasma",
    "serum",
    "blood",
    "liver",
    "kidney",
    "renal",
    "hepatic",
    "cardiac",
    "gastrointestinal",
    "central",
    "nervous",
    "system",
    "respiratory",
    "oral",
    "intravenous",
    "subcutaneous",
    "intramuscular",
    "topical",
    "inhibitor",
    "inducer",
    "substrate",
    "receptor",
    "agonist",
    "antagonist",
    "blocker",
    "channel",
    "enzyme",
    "food",
    "juice",
    "pregnancy",
    "pediatric",
    "geriatric",
    "male",
    "female",
    "children",
    "adults",
    "mild",
    "moderate",
    "severe",
    "significant",
    "clinically",
    "recommended",
    "avoid",
    "caution",
    "contraindicated",
    "approximately",
    "result",
    "found",
    "observed",
    "reported",
    "shown",
    "compared",
    "versus",
    "placebo",
    "control",
    "single",
    "multiple",
    "daily",
    "week",
    "month",
    "year",
    "high",
    "low",
    "normal",
    "abnormal",
    "increased",
    "decreased",
    "greater",
    "less",
    "before",
    "after",
    "during",
    "following",
    "due",
    "because",
    "however",
    "therefore",
    "thus",
    "addition",
    "including",
    "example",
    "manufacturer",
    "company",
    "brand",
    "generic",
    "formulation",
    "tablet",
    "capsule",
    "injection",
    "solution",
    "cream",
    "ointment",
    "gel",
    "patch",
    "inhaler",
    "spray",
    "drop",
    "package",
    "insert",
    "label",
    "prescribing",
    "information",
    "warning",
    "precaution",
    "overdosage",
    "description",
    "indications",
    "contraindications",
    "dosage",
    "supplied",
    "storage",
    "handling",
    "counseling",
    "revised",
    "date",
    "copyright",
    "trademark",
    "rights",
    "reserved",
    "disclaimer",
    "contact",
    "phone",
    "email",
    "website",
    "address",
    "usa",
    "united",
    "states",
    "america",
    "europe",
    "international",
    "global",
    "inc",
    "llc",
    "ltd",
    "corp",
    "corporation",
    "division",
    "subsidiary",
    "group",
    "organization",
    "institution",
    "university",
    "hospital",
    "clinic",
    "center",
    "department",
    "laboratory",
    "research",
    "physician",
    "doctor",
    "pharmacist",
    "nurse",
    "practitioner",
    "specialist",
    "consultant",
    "committee",
    "panel",
    "board",
    "society",
    "association",
    "foundation",
    "council",
    "academy",
    "college",
    "school",
    "institute"
}


# =========================================================
# FDA FUNCTIONS
# =========================================================

def fetch_label(drug_name, search_type="generic"):
    """Fetch one FDA drug label."""

    if search_type == "brand":
        field = "openfda.brand_name"
    else:
        field = "openfda.generic_name"

    name = drug_name.strip().upper()

    queries = [
        f'{field}:"{name}"',
        f"{field}:{name}"
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
                results = response.json().get("results", [])

                if results:
                    return results[0]

        except (requests.RequestException, ValueError):
            pass

    return None


def get_interaction_text(label):
    """Extract interaction-related text from FDA label."""

    if not label:
        return None

    interactions = label.get("drug_interactions")

    if isinstance(interactions, list) and interactions:
        return " ".join(interactions)

    if isinstance(interactions, str):
        return interactions

    for key, value in label.items():

        if "drug_interaction" in key.lower():

            if isinstance(value, list) and value:
                return " ".join(value)

            if isinstance(value, str):
                return value

    return None


def extract_drugs(text, label):
    """Detect drug mentions from interaction text."""

    if not text:
        return []

    known = set(KNOWN_DRUGS)

    openfda = label.get("openfda", {})

    for field in [
        "brand_name",
        "generic_name",
        "substance_name"
    ]:

        values = openfda.get(field, [])

        if isinstance(values, str):
            values = [values]

        for value in values:

            if isinstance(value, str):
                known.add(value.lower().strip())

    text_lower = text.lower()

    found = []
    seen = set()

    # Dictionary matching
    for drug in known:

        if len(drug) < 3:
            continue

        pattern = r"\b" + re.escape(drug) + r"\b"

        match = re.search(
            pattern,
            text_lower
        )

        if match and drug not in seen:

            index = match.start()

            start = max(
                0,
                index - 80
            )

            end = min(
                len(text),
                index + len(drug) + 80
            )

            found.append(
                {
                    "drug": drug.title(),
                    "context": text[start:end],
                    "method": "dictionary"
                }
            )

            seen.add(drug)

    # Heuristic matching
    pattern = (
        r"\b([A-Z][a-zA-Z]+"
        r"(?:\s+[A-Z][a-zA-Z]+){0,2})\b"
    )

    for match in re.finditer(
        pattern,
        text
    ):

        candidate = match.group(1)
        candidate_lower = candidate.lower()

        if candidate_lower in SKIP_WORDS:
            continue

        if len(candidate_lower) < 3:
            continue

        if candidate_lower in seen:
            continue

        looks_like_drug = any(
            candidate_lower.endswith(
                suffix
            )
            for suffix in DRUG_SUFFIXES
        )

        if not looks_like_drug:

            for word in candidate_lower.split():

                if (
                    word in known
                    and len(word) > 3
                ):
                    looks_like_drug = True
                    break

        if looks_like_drug:

            start = max(
                0,
                match.start() - 80
            )

            end = min(
                len(text),
                match.end() + 80
            )

            found.append(
                {
                    "drug": candidate,
                    "context": text[start:end],
                    "method": "heuristic"
                }
            )

            seen.add(candidate_lower)

    return found


def get_all_interactions(
    drug_name,
    search_type="generic"
):
    """Return FDA interaction information for a drug."""

    label = fetch_label(
        drug_name,
        search_type
    )

    if label is None:

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

    manufacturers = openfda.get(
        "manufacturer_name",
        []
    )

    manufacturer = (
        manufacturers[0]
        if manufacturers
        else "Unknown"
    )

    interaction_text = get_interaction_text(
        label
    )

    if not interaction_text:

        return {
            "ok": True,
            "drug": drug_name,
            "brand": brand,
            "generic": generic,
            "manufacturer": manufacturer,
            "interactions": [],
            "note": (
                "No drug-interactions section "
                "was found in this FDA label."
            )
        }

    interactions = extract_drugs(
        interaction_text,
        label
    )

    return {
        "ok": True,
        "drug": drug_name,
        "brand": brand,
        "generic": generic,
        "manufacturer": manufacturer,
        "interactions": interactions
    }


def check_two_drugs(drug_a, drug_b):
    """Check both FDA labels for evidence mentioning the other drug."""

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

    # Check Drug A label
    if data_a["ok"]:

        for item in data_a["interactions"]:

            detected = item["drug"].lower()

            if (
                detected == b_lower
                or b_lower in detected
                or detected in b_lower
            ):

                return {
                    "found": True,
                    "context": item["context"],
                    "method": item["method"],
                    "source": drug_a
                }

    # Check Drug B label
    if data_b["ok"]:

        for item in data_b["interactions"]:

            detected = item["drug"].lower()

            if (
                detected == a_lower
                or a_lower in detected
                or detected in a_lower
            ):

                return {
                    "found": True,
                    "context": item["context"],
                    "method": item["method"],
                    "source": drug_b
                }

    # Neither label found
    if not data_a["ok"] and not data_b["ok"]:

        return {
            "found": False,
            "reason": (
                "Could not find an FDA label "
                "for either drug."
            )
        }

    reasons = []

    if data_a["ok"]:

        reasons.append(
            f"no mention of {drug_b} "
            f"in {drug_a}'s checked interaction label"
        )

    if data_b["ok"]:

        reasons.append(
            f"no mention of {drug_a} "
            f"in {drug_b}'s checked interaction label"
        )

    return {
        "found": False,
        "reason": (
            "No matching interaction mention "
            "was found in the checked FDA labels. "
            + " ".join(reasons)
            + "."
        )
    }


# =========================================================
# AI EXPLANATION
# =========================================================

def generate_ai_explanation(
    drug_a,
    drug_b,
    evidence
):
    """Generate an evidence-grounded explanation."""

    if client is None:

        return (
            "### AI unavailable\n\n"
            "The OpenAI API key is not configured "
            "in Streamlit Secrets."
        )

    prompt = f"""
You are MedCheck AI, an educational pharmacy
information assistant.

Analyze ONLY the FDA label evidence supplied below.

Drug A: {drug_a}
Drug B: {drug_b}

FDA evidence:
{evidence}

Create a concise explanation for a pharmacy student.

Use exactly these sections:

### What the evidence says

Explain what the supplied FDA evidence actually states.

### Why it may matter

Explain the possible pharmacological or clinical
significance ONLY when supported by the supplied
evidence.

### Key point

Give one concise educational takeaway.

Rules:

1. Do not invent interaction facts.
2. Do not use information that is not supported by
   the supplied evidence.
3. Do not assign Major, Moderate, or Minor severity
   unless the evidence explicitly supports it.
4. Do not recommend starting, stopping, increasing,
   or decreasing medication.
5. If the evidence is insufficient, say so clearly.
6. Keep the explanation concise and understandable.
7. This is educational information, not medical advice.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content

    except Exception as error:

        return (
            "### AI explanation unavailable\n\n"
            f"Technical error: {error}"
        )


# =========================================================
# UI
# =========================================================

st.title("💊 MedCheck AI")

st.caption(
    "Intelligent Drug Interaction Analysis | "
    "Powered by U.S. FDA openFDA + AI"
)

st.warning(
    "⚠️ Educational tool only — not a substitute "
    "for advice from a licensed pharmacist or physician. "
    "A 'no interaction found' result does not guarantee "
    "safety. Always confirm medication decisions with "
    "a healthcare professional."
)

st.markdown("---")


tab1, tab2 = st.tabs(
    [
        "🔍 Two-Drug Check",
        "📋 Single Drug Profile"
    ]
)


# =========================================================
# TAB 1 — TWO DRUG CHECK
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

    analyze = st.button(
        "Analyze Interaction",
        use_container_width=True
    )

    if analyze:

        if not drug1 or not drug2:

            st.error(
                "Please enter both drug names."
            )

        elif drug1.lower() == drug2.lower():

            st.warning(
                "Please enter two different medicines."
            )

        else:

            with st.spinner(
                "Fetching FDA drug-label evidence..."
            ):

                result = check_two_drugs(
                    drug1,
                    drug2
                )

            if result["found"]:

                st.error(
                    "⚠️ POTENTIAL INTERACTION IDENTIFIED"
                )

                st.write(
                    f"**{drug1}** + **{drug2}**"
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
                    "Analyzing FDA evidence..."
                ):

                    explanation = generate_ai_explanation(
                        drug1,
                        drug2,
                        result["context"]
                    )

                st.markdown(
                    explanation
                )

                st.caption(
                    "AI explanation is grounded in the "
                    "retrieved FDA label evidence. "
                    "Educationa