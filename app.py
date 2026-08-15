import streamlit as st
import requests
import re
from typing import List, Dict, Optional

st.set_page_config(
    page_title="MedCheck AI",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===================== CUSTOM CSS =====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        min-height: 100vh;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    .title-container {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00d4ff, #7b2cbf, #ff006e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .subtitle {
        color: #a0a0c0;
        font-size: 1.1rem;
        font-weight: 300;
        margin-top: -10px;
    }
    
    .badge {
        display: inline-block;
        background: rgba(0, 212, 255, 0.15);
        border: 1px solid rgba(0, 212, 255, 0.3);
        color: #00d4ff;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-top: 8px;
    }
    
    .card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .input-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .result-danger {
        background: linear-gradient(135deg, rgba(255, 0, 110, 0.15), rgba(255, 0, 110, 0.05));
        border: 1px solid rgba(255, 0, 110, 0.4);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        animation: pulse-danger 2s infinite;
    }
    
    .result-safe {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.15), rgba(0, 255, 136, 0.05));
        border: 1px solid rgba(0, 255, 136, 0.4);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    @keyframes pulse-danger {
        0%, 100% { box-shadow: 0 0 0 0 rgba(255, 0, 110, 0.2); }
        50% { box-shadow: 0 0 20px 5px rgba(255, 0, 110, 0.1); }
    }
    
    .drug-tag {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 6px 16px;
        border-radius: 25px;
        font-weight: 600;
        font-size: 0.9rem;
        margin: 2px;
    }
    
    .context-box {
        background: rgba(0, 0, 0, 0.3);
        border-left: 3px solid #00d4ff;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-top: 10px;
        color: #c0c0e0;
        font-style: italic;
        font-size: 0.9rem;
    }
    
    .stat-box {
        text-align: center;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #00d4ff;
    }
    
    .stat-label {
        font-size: 0.8rem;
        color: #8888aa;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .footer {
        text-align: center;
        color: #555577;
        font-size: 0.75rem;
        margin-top: 3rem;
        padding-bottom: 2rem;
    }
    
    div[data-testid="stTabs"] button {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px 8px 0 0 !important;
        border: none !important;
        color: #8888aa !important;
        font-weight: 500 !important;
    }
    
    div[data-testid="stTabs"] button[aria-selected="true"] {
        background: rgba(0, 212, 255, 0.15) !important;
        color: #00d4ff !important;
        border-bottom: 2px solid #00d4ff !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 32px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: white;
        padding: 14px;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00d4ff;
        box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
    }
    
    .stRadio > div {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        padding: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ===================== API CONFIG =====================
BASE_URL = "https://api.fda.gov/drug/label.json"

KNOWN_DRUGS = {
    "warfarin", "aspirin", "ibuprofen", "naproxen", "acetaminophen", "paracetamol",
    "amoxicillin", "azithromycin", "ciprofloxacin", "metformin", "insulin",
    "atorvastatin", "simvastatin", "rosuvastatin", "pravastatin", "fluvastatin",
    "lovastatin", "pitavastatin",
    "lisinopril", "enalapril", "captopril", "ramipril", "perindopril",
    "amlodipine", "nifedipine", "felodipine", "nicardipine", "isradipine",
    "metoprolol", "atenolol", "propranolol", "carvedilol", "labetalol",
    "bisoprolol", "nebivolol", "sotalol",
    "losartan", "valsartan", "irbesartan", "candesartan", "telmisartan",
    "omeprazole", "esomeprazole", "lansoprazole", "pantoprazole", "rabeprazole",
    "ranitidine", "famotidine", "cimetidine", "nizatidine",
    "sertraline", "fluoxetine", "escitalopram", "paroxetine", "citalopram",
    "fluvoxamine", "venlafaxine", "duloxetine", "milnacipran",
    "alprazolam", "lorazepam", "clonazepam", "diazepam", "temazepam",
    "midazolam", "triazolam", "oxazepam", "chlordiazepoxide",
    "phenytoin", "carbamazepine", "valproic acid", "divalproex", "lamotrigine",
    "levetiracetam", "topiramate", "gabapentin", "pregabalin",
    "levothyroxine", "methimazole", "propylthiouracil",
    "prednisone", "prednisolone", "methylprednisolone", "dexamethasone",
    "hydrocortisone", "betamethasone", "triamcinolone",
    "furosemide", "bumetanide", "torsemide",
    "hydrochlorothiazide", "chlorthalidone", "indapamide", "metolazone",
    "spironolactone", "eplerenone", "amiloride", "triamterene",
    "digoxin", "clopidogrel", "prasugrel", "ticagrelor",
    "heparin", "enoxaparin", "dalteparin", "fondaparinux",
    "rivaroxaban", "apixaban", "dabigatran", "edoxaban",
    "phenobarbital", "primidone",
    "rifampin", "rifampicin", "isoniazid", "pyrazinamide", "ethambutol",
    "ketoconazole", "fluconazole", "itraconazole", "voriconazole", "posaconazole",
    "erythromycin", "clarithromycin", "telithromycin",
    "grapefruit", "alcohol", "ethanol", "caffeine", "nicotine",
    "theophylline", "aminophylline",
    "codeine", "morphine", "tramadol", "oxycodone", "hydrocodone",
    "fentanyl", "methadone", "buprenorphine", "naloxone",
    "ondansetron", "granisetron", "promethazine", "prochlorperazine",
    "diphenhydramine", "loratadine", "cetirizine", "fexofenadine",
    "montelukast", "zafirlukast", "zileuton",
    "salbutamol", "albuterol", "salmeterol", "formoterol", "indacaterol",
    "fluticasone", "budesonide", "beclomethasone", "mometasone",
    "tiotropium", "ipratropium", "umeclidinium", "aclidinium",
    "methotrexate", "cyclosporine", "tacrolimus", "sirolimus", "everolimus",
    "mycophenolate", "azathioprine", "leflunomide",
    "allopurinol", "colchicine", "febuxostat", "probenecid",
    "sildenafil", "tadalafil", "vardenafil", "avanafil",
    "finasteride", "dutasteride", "tamsulosin", "alfuzosin", "silodosin",
    "donepezil", "memantine", "rivastigmine", "galantamine",
    "levodopa", "carbidopa", "ropinirole", "pramipexole", "rotigotine",
    "sumatriptan", "rizatriptan", "zolmitriptan", "naratriptan",
    "bromocriptine", "cabergoline", "quinagolide",
    "isosorbide mononitrate", "isosorbide dinitrate", "nitroglycerin",
    "ranolazine", "ivabradine",
    "hydralazine", "minoxidil", "doxazosin", "prazosin", "terazosin",
    "clonidine", "methyldopa", "reserpine",
    "amiodarone", "sotalol", "dofetilide", "ibutilide",
    "flecainide", "propafenone", "mexiletine", "disopyramide",
    "adenosine",
    "alteplase", "reteplase", "tenecteplase", "streptokinase",
    "cilostazol", "dipyridamole",
    "tranexamic acid", "aminocaproic acid", "protamine",
    "epoetin alfa", "darbepoetin alfa",
    "filgrastim", "pegfilgrastim", "sargramostim",
    "romiplostim", "eltrombopag", "avatrombopag",
    "deferoxamine", "deferasirox", "deferiprone",
    "hydroxyurea", "anagrelide",
    "eculizumab", "ravulizumab",
    "omalizumab", "mepolizumab", "benralizumab", "dupilumab",
    "epinephrine", "norepinephrine", "dopamine", "dobutamine",
    "phenylephrine", "pseudoephedrine",
    "milrinone",
    "sacubitril", "valsartan",
    "acetazolamide", "topiramate", "zonisamide",
    "oxcarbazepine", "eslicarbazepine",
    "fosphenytoin",
    "ethosuximide", "methsuximide",
    "lacosamide", "perampanel", "cenobamate",
    "rufinamide", "stiripentol", "cannabidiol",
    "clobazam", "nitrazepam", "oxazepam",
    "dihydroergotamine", "ergotamine", "methysergide",
    "propranolol", "timolol", "nadolol",
    "amitriptyline", "nortriptyline", "imipramine", "desipramine",
    "clomipramine", "doxepin",
    "onabotulinumtoxina", "erenumab", "fremanezumab", "galcanezumab",
    "flunarizine", "cinnarizine", "pizotifen",
    "diclofenac", "ketorolac", "indomethacin", "sulindac", "etodolac",
    "meloxicam", "piroxicam", "celecoxib",
    "metoclopramide", "promethazine", "prochlorperazine",
    "chlorpromazine", "haloperidol", "droperidol",
    "granisetron", "dolasetron", "palonosetron",
    "aprepitant", "fosaprepitant",
    "scopolamine", "dimenhydrinate", "meclizine",
    "domperidone", "itopride",
    "sennosides", "bisacodyl", "lactulose", "polyethylene glycol",
    "loperamide", "diphenoxylate",
    "bismuth subsalicylate",
    "rifaximin", "neomycin",
    "mesalamine", "sulfasalazine", "balsalazide",
    "infliximab", "adalimumab", "golimumab", "certolizumab",
    "vedolizumab", "natalizumab", "ustekinumab",
    "tofacitinib", "upadacitinib",
    "chlorambucil", "cyclophosphamide", "ifosfamide",
    "sucralfate", "misoprostol",
    "aluminum hydroxide", "magnesium hydroxide", "calcium carbonate",
    "megestrol", "cyproheptadine", "mirtazapine",
    "glipizide", "glyburide", "glimepiride",
    "repaglinide", "nateglinide",
    "pioglitazone", "rosiglitazone",
    "sitagliptin", "saxagliptin", "linagliptin", "alogliptin",
    "canagliflozin", "dapagliflozin", "empagliflozin", "ertugliflozin",
    "liraglutide", "exenatide", "dulaglutide", "semaglutide",
    "insulin lispro", "insulin aspart", "insulin glulisine",
    "insulin regular", "insulin nph",
    "insulin detemir", "insulin glargine", "insulin degludec",
    "pramlintide",
    "ezetimibe", "fenofibrate", "gemfibrozil", "niacin",
    "evolocumab", "alirocumab",
}

DRUG_SUFFIXES = (
    'nib', 'mab', 'zumab', 'ximab', 'tinib', 'ciclib', 'parib', 'vastatin',
    'sartan', 'pril', 'olol', 'olide', 'azide', 'mycin', 'cycline', 'floxacin',
    'micin', 'sone', 'nide', 'mide', 'zide', 'pam', 'lam', 'dipine', 'pramine',
    'triptyline', 'prazole', 'tidine', 'xetine', 'pram', 'done', 'zodone',
    'lone', 'zone', 'tide', 'glitazone', 'formin', 'glipizide', 'glyburide',
    'sulfa', 'cillin', 'icillin', 'bactam', 'ceph', 'cef', 'penem', 'vir',
    'navir', 'previr', 'tegravir', 'vudine', 'citabine', 'arabine'
)

SKIP_WORDS = {
    "the", "and", "for", "with", "may", "use", "see", "fda", "patients", "clinical",
    "studies", "table", "figure", "section", "drug", "drugs", "medicine", "product",
    "administration", "treatment", "therapy", "dose", "patient", "subject", "study",
    "effect", "effects", "adverse", "reaction", "monitor", "increase", "decrease",
    "concomitant", "coadministration", "pharmacokinetics", "metabolism", "absorption",
    "distribution", "elimination", "plasma", "serum", "blood", "liver", "kidney",
    "renal", "hepatic", "cardiac", "gastrointestinal", "central", "nervous", "system",
    "respiratory", "oral", "intravenous", "subcutaneous", "intramuscular", "topical",
    "inhibitor", "inducer", "substrate", "receptor", "agonist", "antagonist", "blocker",
    "channel", "enzyme", "cyp", "food", "grapefruit", "juice", "alcohol", "smoking",
    "pregnancy", "pediatric", "geriatric", "male", "female", "children", "adults",
    "mild", "moderate", "severe", "significant", "clinically", "recommended", "avoid",
    "caution", "contraindicated", "approximately", "result", "found", "observed",
    "reported", "shown", "compared", "versus", "placebo", "control", "single",
    "multiple", "daily", "week", "month", "year", "high", "low", "normal", "abnormal",
    "increased", "decreased", "greater", "less", "before", "after", "during", "following",
    "due", "because", "however", "therefore", "thus", "addition", "including", "example",
    "manufacturer", "company", "brand", "generic", "formulation", "tablet", "capsule",
    "injection", "solution", "cream", "ointment", "gel", "patch", "inhaler", "spray",
    "drop", "package", "insert", "label", "prescribing", "information", "warning",
    "precaution", "overdosage", "description", "indications", "contraindications",
    "dosage", "supplied", "storage", "handling", "counseling", "revised", "date",
    "copyright", "trademark", "all", "rights", "reserved", "disclaimer", "contact",
    "phone", "email", "website", "address", "usa", "united", "states", "america",
    "europe", "international", "global", "inc", "llc", "ltd", "corp", "corporation",
    "division", "subsidiary", "group", "organization", "institution", "university",
    "hospital", "clinic", "center", "department", "laboratory", "research", "physician",
    "doctor", "pharmacist", "nurse", "practitioner", "specialist", "consultant",
    "committee", "panel", "board", "society", "association", "foundation", "council",
    "academy", "college", "school", "institute",
}


class OpenFDAInteractionFinder:
    def __init__(self, api_key: None):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Pharmacy-Project/1.0)'
        })

    def _make_request(self, params: Dict) -> Optional[Dict]:
        if self.api_key:
            params['api_key'] = self.api_key
        try:
            response = self.session.get(BASE_URL, params=params, timeout=15)
            if response.status_code == 404:
                return None
            if response.status_code == 429:
                st.warning("Rate limit exceeded. Get free API key at open.fda.gov")
                return None
            if response.status_code != 200:
                return None
            return response.json()
        except Exception:
            return None

    def search_drug(self, drug_name: str, search_type: str = "brand") -> Optional[Dict]:
        drug_name = drug_name.strip().upper()
        if search_type == "brand":
            search_query = 'openfda.brand_name:"' + drug_name + '"'
        else:
            search_query = 'openfda.generic_name:"' + drug_name + '"'
        params = {"search": search_query, "limit": 1}
        data = self._make_request(params)
        if not data or not data.get("results"):
            if search_type == "brand":
                search_query = 'openfda.brand_name:' + drug_name
            else:
                search_query = 'openfda.generic_name:' + drug_name
            params["search"] = search_query
            data = self._make_request(params)
        if data and data.get("results"):
            return data["results"][0]
        return None

    def extract_interaction_text(self, label: Dict) -> Optional[str]:
        if not label:
            return None
        interactions = label.get("drug_interactions")
        if interactions and isinstance(interactions, list) and interactions:
            return interactions[0]
        for key, val in label.items():
            if "drug_interaction" in key.lower():
                if isinstance(val, list) and val:
                    return val[0]
                elif isinstance(val, str):
                    return val
        return None

    def _get_label_drugs(self, label: Dict) -> set:
        drugs = set()
        openfda = label.get("openfda", {})
        for field in ["brand_name", "generic_name", "substance_name"]:
            values = openfda.get(field, [])
            if isinstance(values, str):
                values = [values]
            for v in values:
                drugs.add(v.lower().strip())
        return drugs

    def extract_drugs_from_text(self, text: str, label: Dict) -> List[Dict]:
        if not text:
            return []
        known_drugs = KNOWN_DRUGS | self._get_label_drugs(label)
        found = []
        text_lower = text.lower()
        seen = set()

        for drug in known_drugs:
            if len(drug) < 3:
                continue
            pattern = r'\b' + re.escape(drug) + r'\b'
            for match in re.finditer(pattern, text_lower):
                if drug not in seen:
                    start = max(0, match.start() - 60)
                    end = min(len(text), match.end() + 60)
                    snippet = text[start:end].strip()
                    found.append({
                        "drug": drug.title(),
                        "context": "..." + snippet + "...",
                        "method": "dictionary"
                    })
                    seen.add(drug)
                    break

        cap_pattern = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\b'
        for match in re.finditer(cap_pattern, text):
            candidate = match.group(1)
            cand_lower = candidate.lower()
            if cand_lower in SKIP_WORDS or len(cand_lower) < 3:
                continue
            if cand_lower in seen:
                continue
            looks_drug = any(cand_lower.endswith(s) for s in DRUG_SUFFIXES)
            if not looks_drug:
                for w in cand_lower.split():
                    if w in known_drugs and len(w) > 3:
                        looks_drug = True
                        break
            if looks_drug:
                start = max(0, match.start() - 60)
                end = min(len(text), match.end() + 60)
                snippet = text[start:end].strip()
                found.append({
                    "drug": candidate,
                    "context": "..." + snippet + "...",
                    "method": "heuristic"
                })
                seen.add(cand_lower)

        found.sort(key=lambda x: text_lower.find(x["drug"].lower())
                   if text_lower.find(x["drug"].lower()) != -1 else 99999)
        return found

    def get_interactions(self, drug_name: str, search_type: str = "brand") -> Dict:
        label = self.search_drug(drug_name, search_type)
        if not label:
            return {
                "success": False,
                "drug": drug_name,
             