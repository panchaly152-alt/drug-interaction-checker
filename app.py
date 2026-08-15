"""
openFDA Drug Interaction Fetcher
================================
Drop-in replacement for RxNav. Fetches FDA labels, extracts interactions.

Dependencies: requests (pip install requests)
"""

import requests
import re
from typing import List, Dict, Optional

BASE_URL = "https://api.fda.gov/drug/label.json"

# Common drug names for dictionary matching
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
    """Robust client to fetch drug-drug interactions from openFDA drug labels."""

    def __init__(self, api_key: Optional[str] = None):
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
                print("[WARN] Rate limit exceeded. Get free API key at open.fda.gov")
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

        # Strategy 1: Dictionary matching
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

        # Strategy 2: Heuristic - capitalized sequences
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
                "error": "No FDA label found for '" + drug_name + "'",
                "raw_interactions": None,
                "interacting_drugs": []
            }
        openfda = label.get("openfda", {})
        brand_names = openfda.get("brand_name", [])
        generic_names = openfda.get("generic_name", [])
        manufacturer = openfda.get("manufacturer_name", ["Unknown"])
        if isinstance(manufacturer, list):
            manufacturer = manufacturer[0]
        interaction_text = self.extract_interaction_text(label)
        if not interaction_text:
            return {
                "success": True,
                "drug": drug_name,
                "brand_names": brand_names,
                "generic_names": generic_names,
                "manufacturer": manufacturer,
                "raw_interactions": None,
                "interacting_drugs": [],
                "note": "No drug interactions section in FDA label"
            }
        interacting_drugs = self.extract_drugs_from_text(interaction_text, label)
        return {
            "success": True,
            "drug": drug_name,
            "brand_names": brand_names,
            "generic_names": generic_names,
            "manufacturer": manufacturer,
            "raw_interactions": interaction_text,
            "interacting_drugs": interacting_drugs,
            "interaction_count": len(interacting_drugs)
        }

    def print_report(self, result: Dict):
        if not result["success"]:
            print("\nERROR: " + result["error"])
            return
        sep = "=" * 60
        print("\n" + sep)
        print("INTERACTION REPORT: " + result["drug"].upper())
        print(sep)
        bn = ", ".join(result.get("brand_names", [])) or "N/A"
        gn = ", ".join(result.get("generic_names", [])) or "N/A"
        print("Brand Name(s): " + bn)
        print("Generic Name(s): " + gn)
        print("Manufacturer: " + result.get("manufacturer", "N/A"))
        print(sep)
        drugs = result.get("interacting_drugs", [])
        if not drugs:
            print("\nNo interacting drugs could be extracted.")
            raw = result.get("raw_interactions", "")
            print("\nRaw Text (first 800 chars):\n" + raw[:800] + "...")
            return
        print("\nFound " + str(len(drugs)) + " potentially interacting drug(s):\n")
        for i, drug_info in enumerate(drugs[:30], 1):
            icon = "[D]" if drug_info["method"] == "dictionary" else "[H]"
            print(str(i).rjust(2) + ". " + icon + " " + drug_info["drug"])
            print("    " + drug_info["context"])
            print()
        if len(drugs) > 30:
            print("... and " + str(len(drugs) - 30) + " more (truncated)")
        print("\nFull Raw Interaction Text (first 1500 chars):")
        print("-" * 60)
        raw = result.get("raw_interactions", "")
        if len(raw) > 1500:
            print(raw[:1500] + "\n... [truncated]")
        else:
            print(raw)
        print("-" * 60)


def get_interacting_drugs(drug_name: str, search_type: str = "brand") -> List[str]:
    """Simple drop-in replacement for RxNav."""
    finder = OpenFDAInteractionFinder()
    result = finder.get_interactions(drug_name, search_type)
    if not result["success"]:
        return []
    return [d["drug"].lower() for d in result.get("interacting_drugs", [])]


def get_interactions_with_context(drug_name: str, search_type: str = "brand") -> List[Dict]:
    """Returns interacting drugs with context snippets."""
    finder = OpenFDAInteractionFinder()
    result = finder.get_interactions(drug_name, search_type)
    if not result["success"]:
        return []
    return result.get("interacting_drugs", [])
