import streamlit as st
import requests
import re

st.set_page_config(page_title="MedCheck AI", page_icon="💊", layout="centered")

BASE_URL = "https://api.fda.gov/drug/label.json"

KNOWN_DRUGS = {
    "warfarin", "aspirin", "ibuprofen", "naproxen", "acetaminophen", "paracetamol",
    "amoxicillin", "azithromycin", "ciprofloxacin", "metformin", "insulin",
    "atorvastatin", "simvastatin", "rosuvastatin", "pravastatin", "fluvastatin",
    "lovastatin", "lisinopril", "enalapril", "captopril", "amlodipine",
    "nifedipine", "felodipine", "metoprolol", "atenolol", "propranolol",
    "carvedilol", "bisoprolol", "losartan", "valsartan", "irbesartan",
    "omeprazole", "esomeprazole", "lansoprazole", "pantoprazole", "rabeprazole",
    "ranitidine", "famotidine", "sertraline", "fluoxetine", "escitalopram",
    "paroxetine", "alprazolam", "lorazepam", "clonazepam", "diazepam",
    "phenytoin", "carbamazepine", "valproic acid", "lamotrigine",
    "levetiracetam", "topiramate", "gabapentin", "pregabalin",
    "levothyroxine", "methimazole", "prednisone", "dexamethasone",
    "furosemide", "hydrochlorothiazide", "spironolactone", "digoxin",
    "clopidogrel", "heparin", "enoxaparin", "rivaroxaban", "apixaban",
    "dabigatran", "phenobarbital", "rifampin", "ketoconazole", "fluconazole",
    "itraconazole", "erythromycin", "clarithromycin", "grapefruit",
    "alcohol", "caffeine", "theophylline", "codeine", "morphine",
    "tramadol", "oxycodone", "fentanyl", "ondansetron", "promethazine",
    "diphenhydramine", "loratadine", "cetirizine", "montelukast",
    "salbutamol", "albuterol", "fluticasone", "budesonide", "tiotropium",
    "methotrexate", "cyclosporine", "tacrolimus", "allopurinol",
    "colchicine", "sildenafil", "tadalafil", "finasteride", "tamsulosin",
    "donepezil", "memantine", "levodopa", "carbidopa", "sumatriptan",
    "nitroglycerin", "ranolazine", "amiodarone", "sotalol", "adenosine",
    "streptokinase", "cilostazol", "epoetin alfa", "filgrastim",
    "deferoxamine", "hydroxyurea", "omalizumab", "epinephrine",
    "dopamine", "milrinone", "sacubitril", "acetazolamide", "lacosamide",
    "rufinamide", "cannabidiol", "clobazam", "amitriptyline",
    "diclofenac", "ketorolac", "indomethacin", "meloxicam", "celecoxib",
    "metoclopramide", "haloperidol", "granisetron", "aprepitant",
    "scopolamine", "lactulose", "loperamide", "mesalamine",
    "infliximab", "adalimumab", "tofacitinib", "cyclophosphamide",
    "sucralfate", "glipizide", "glyburide", "repaglinide",
    "pioglitazone", "sitagliptin", "canagliflozin", "dapagliflozin",
    "empagliflozin", "liraglutide", "semaglutide", "insulin regular",
    "insulin glargine", "pramlintide", "ezetimibe", "gemfibrozil",
}

DRUG_SUFFIXES = (
    'nib','mab','zumab','tinib','ciclib','parib','vastatin','sartan','pril',
    'olol','olide','azide','mycin','cycline','floxacin','micin','sone','nide',
    'mide','zide','pam','lam','dipine','pramine','triptyline','prazole',
    'tidine','xetine','pram','done','zodone','lone','zone','tide','glitazone',
    'formin','glipizide','glyburide','sulfa','cillin','bactam','cef','penem',
    'vir','navir','previr','tegravir','vudine','citabine','arabine'
)

SKIP_WORDS = {
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
    "academy","college","school","institute",
}


def fetch_label(drug_name, search_type="generic"):
    """Look up an FDA label by generic or brand name: try an exact phrase
    match first, then a looser unquoted match as a fallback."""
    field = "openfda.brand_name" if search_type == "brand" else "openfda.generic_name"
    name = drug_name.strip().upper()
    for q in (f'{field}:"{name}"', f"{field}:{name}"):
        try:
            r = requests.get(BASE_URL, params={"search": q, "limit": 1}, timeout=15)
            if r.status_code == 200:
                results = r.json().get("results")
                if results:
                    return results[0]
        except (requests.RequestException, ValueError):
            continue
    return None


def get_interaction_text(label):
    """Pull the drug interactions section text from a label. Joins every
    paragraph in the field, not just the first, so nothing is missed."""
    if not label:
        return None
    interactions = label.get("drug_interactions")
    if isinstance(interactions, list) and interactions:
        return " ".join(interactions)
    for key, val in label.items():
        if "drug_interaction" in key.lower():
            if isinstance(val, list) and val:
                return " ".join(val)
            if isinstance(val, str):
                return val
    return None


def extract_drugs(text, label):
    """Scan interaction text for known drug names (dictionary match) and
    capitalized words with drug-like suffixes (heuristic match)."""
    if not text:
        return []
    known = set(KNOWN_DRUGS)
    openfda = label.get("openfda", {}) if isinstance(label, dict) else {}
    for field in ["brand_name", "generic_name", "substance_name"]:
        vals = openfda.get(field, [])
        if isinstance(vals, str):
            vals = [vals]
        for v in vals:
            known.add(v.lower().strip())

    found = []
    text_lower = text.lower()
    seen = set()

    for drug in known:
        if len(drug) < 3:
            continue
        pat = r"\b" + re.escape(drug) + r"\b"
        if re.search(pat, text_lower) and drug not in seen:
            idx = text_lower.find(drug)
            start = max(0, idx - 60)
            end = min(len(text), idx + len(drug) + 60)
            found.append({"drug": drug.title(), "context": text[start:end], "method": "dictionary"})
            seen.add(drug)

    cap_pat = r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\b"
    for m in re.finditer(cap_pat, text):
        cand = m.group(1)
        cl = cand.lower()
        if cl in SKIP_WORDS or len(cl) < 3 or cl in seen:
            continue
        looks = any(cl.endswith(s) for s in DRUG_SUFFIXES)
        if not looks:
            for w in cl.split():
                if w in known and len(w) > 3:
                    looks = True
                    break
        if looks:
            idx = text_lower.find(cl)
            start = max(0, idx - 60)
            end = min(len(text), idx + len(cl) + 60)
            found.append({"drug": cand, "context": text[start:end], "me