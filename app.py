
    """
openFDA Drug Interaction Module — Drop-in replacement for RxNav
===============================================================
Just import these functions and replace your RxNav calls.

Dependencies: requests (pip install requests)
"""

import requests
import re
from typing import List, Dict, Optional

BASE_URL = "https://api.fda.gov/drug/label.json"

# ── 1. FETCH LABEL FROM openFDA ──────────────────────────────────────────────

def fetch_fda_label(drug_name: str, search_type: str = "brand") -> Optional[Dict]:
    """
    Fetch the first matching FDA drug label from openFDA.
    
    Args:
        drug_name: Drug name to search
        search_type: "brand" or "generic"
        
    Returns:
        Label dict or None if not found / error
    """
    drug_name = drug_name.strip().upper()
    
    if search_type == "brand":
        query = f'openfda.brand_name:"{drug_name}"'
    else:
        query = f'openfda.generic_name:"{drug_name}"'
    
    params = {"search": query, "limit": 1}
    
    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        
        if resp.status_code == 404:
            return None
        if resp.status_code == 429:
            print("[WARN] openFDA rate limit hit. Get a free API key at open.fda.gov")
            return None
        if resp.status_code != 200:
            return None
            
        data = resp.json()
        results = data.get("results", [])
        return results[0] if results else None
        
    except Exception:
        return None


# ── 2. EXTRACT INTERACTION TEXT ──────────────────────────────────────────────

def get_interaction_text(label: Dict) -> Optional[str]:
    """
    Pull the raw drug_interactions text out of an FDA label.
    """
    if not label:
        return None
    
    interactions = label.get("drug_interactions")
    if interactions and isinstance(interactions, list) and interactions:
        return interactions[0]
    
    # Fallback: scan for any key containing "drug_interaction"
    for key, val in label.items():
        if "drug_interaction" in key.lower():
            if isinstance(val, list) and val:
                return val[0]
            elif isinstance(val, str):
                return val
    return None


# ── 3. PARSE INTERACTING DRUGS FROM TEXT ─────────────────────────────────────

# Common drug names for dictionary matching (expand as needed)
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


def parse_interacting_drugs(interaction_text: str, label: Dict) -> List[str]:
    """
    Parse the free-text interaction section and return a list of 
    drug names that are mentioned as interacting.
    
    Returns:
        List of unique drug names (lowercased)
    """
    if not interaction_text:
        return []
    
    text_lower = interaction_text.lower()
    found = set()
    
    # ── Strategy A: Dictionary matching ──
    for drug in KNOWN_DRUGS:
        pattern = r'\b' + re.escape(drug) + r'\b'
        if re.search(pattern, text_lower):
            found.add(drug)
    
    # ── Strategy B: Extract drug names from the label's own openfda data ──
    openfda = label.get("openfda", {})
    for field in ["brand_name", "generic_name", "substance_name"]:
        vals = openfda.get(field, [])
        if isinstance(vals, str):
            vals = [vals]
        for v in vals:
            v_clean = v.lower().strip()
            if len(v_clean) > 2:
                pattern = r'\b' + re.escape(v_clean) + r'\b'
                if re.search(pattern, text_lower):
                    found.add(v_clean)
    
    # ── Strategy C: Heuristic — capitalized sequences that look like drugs ──
    cap_pattern = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\b'
    skip = {
        "the","and","for","with","may","use","see","fda","patients","clinical",
        "studies","table","figure","section","drug","drugs","medicine","product",
        "administration","treatment","therapy","dose","patient","subject","study",
        "effect","effects","adverse","reaction","monitor","increase","decrease",
        "concomitant","coadministration","pharmacokinetics","metabolism","absorption",
        "distribution","elimination","plasma","serum","blood","liver","kidney",
        "renal","hepatic","cardiac","gastrointestinal","central","nervous","system",
        "respiratory","oral","intravenous","subcutaneous","intramuscular","topical",
        "inhibitor","inducer","substrate","receptor","agonist","antagonist","blocker",
        "channel","enzyme","cyp","food","grapefruit","juice","alcohol","smoking",
        "pregnancy","pediatric","geriatric","male","female","children","adults",
        "mild","moderate","severe","significant","clinically","recommended","avoid",
        "caution","contraindicated","approximately","result","found","observed",
        "reported","shown","compared","versus","placebo","control","single",
        "multiple","daily","week","month","year","high","low","normal","abnormal",
        "increased","decreased","greater","less","before","after","during","following",
        "due","because","however","therefore","thus","addition","including","example",
        "manufacturer","company","brand","generic","formulation","tablet","capsule",
        "injection","solution","cream","ointment","gel","patch","inhaler","spray",
        "drop","package","insert","label","prescribing","information","warning",
        "precaution","overdosage","description","indications","contraindications",
        "dosage","supplied","storage","handling","counseling","revised","date",
        "copyright","trademark","all","rights","reserved","disclaimer","contact",
        "phone","email","website","address","usa","united","states","america",
        "europe","international","global","inc","llc","ltd","corp","corporation",
        "division","subsidiary","group","organization","institution","university",
        "hospital","clinic","center","department","laboratory","research","physician",
        "doctor","pharmacist","nurse","practitioner","specialist","consultant",
        "committee","panel","board","society","association","foundation","council",
        "academy","college","school","institute","opioid","mu","antagonists",
    }
    
    drug_suffixes = ('nib','mab','zumab','ximab','tinib','ciclib','parib','vastatin',
                     'sartan','pril','olol','olide','azide','mycin','cycline','floxacin',
                     'micin','sone','nide','mide','zide','pam','lam','dipine','pramine',
                     'triptyline','prazole','tidine','xetine','pram','done','zodone',
                     'lone','zone','tide','glitazone','formin','glipizide','glyburide',
                     'sulfa','cillin','icillin','bactam','ceph','cef','penem','vir',
                     'navir','previr','tegravir','vudine','citabine','arabine')
    
    for match in re.finditer(cap_pattern, interaction_text):
        candidate = match.group(1)
        cand_lower = candidate.lower()
        
        if cand_lower in skip or len(cand_lower) < 3:
            continue
        if cand_lower in found:
            continue
        
        looks_drug = any(cand_lower.endswith(s) for s in drug_suffixes)
        
        if not looks_drug:
            for w in cand_lower.split():
                if w in KNOWN_DRUGS and len(w) > 3:
                    looks_drug = True
                    break
        
        if looks_drug:
            found.add(cand_lower)
    
    return sorted(list(found))


# ── 4. MAIN FUNCTION — ONE-LINE REPLACEMENT FOR RxNav ────────────────────────

def get_interacting_drugs(drug_name: str, search_type: str = "brand") -> List[str]:
    """
    DROP-IN REPLACEMENT for your RxNav interaction call.
    
    Usage:
        interacting = get_interacting_drugs("Warfarin", "generic")
        print(interacting)  # ['alcohol', 'amiodarone', 'aspirin', ...]
    
    Returns:
        List of interacting drug names (lowercased, unique, sorted).
        Empty list if no label found or no interactions.
    """
    label = fetch_fda_label(drug_name, search_type)
    if not label:
        return []
    
    text = get_interaction_text(label)
    if not text:
        return []
    
    return parse_interacting_drugs(text, label)


# ── 5. BONUS: Get full details (if you want context/snippets too) ────────────

def get_interactions_with_context(drug_name: str, search_type: str = "brand") -> List[Dict]:
    """
    Like get_interacting_drugs() but returns context snippets too.
    
    Returns:
        [
            {"drug": "warfarin", "context": "...increased INR when given with warfarin..."},
            ...
        ]
    """
    label = fetch_fda_label(drug_name, search_type)
    if not label:
        return []
    
    text = get_interaction_text(label)
    if not text:
        return []
    
    text_lower = text.lower()
    results = []
    seen = set()
    
    for drug in parse_interacting_drugs(text, label):
        if drug in seen:
            continue
        seen.add(drug)
        
        idx = text_lower.find(drug)
        if idx != -1:
            start = max(0, idx - 80)
            end = min(len(text), idx + len(drug) + 80)
            snippet = text[start:end].strip()
            results.append({
                "drug": drug,
                "context": "..." + snippet + "..."
            })
    
    return results

