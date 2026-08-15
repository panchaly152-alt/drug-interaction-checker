import streamlit as st
import requests
import re
from typing import List, Dict, Optional

st.set_page_config(page_title="MedCheck AI", page_icon="💊", layout="centered")

BASE_URL = "https://api.fda.gov/drug/label.json"

KNOWN_DRUGS = {
    "warfarin", "aspirin", "ibuprofen", "naproxen", "acetaminophen", "paracetamol",
    "amoxicillin", "azithromycin", "ciprofloxacin", "metformin", "insulin",
    "atorvastatin", "simvastatin", "rosuvastatin", "pravastatin", "fluvastatin",
    "lovastatin", "pitavastatin", "lisinopril", "enalapril", "captopril",
    "amlodipine", "nifedipine", "felodipine", "metoprolol", "atenolol",
    "propranolol", "carvedilol", "bisoprolol", "losartan", "valsartan",
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


class OpenFDAInteractionFinder:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Pharmacy-Project/1.0)"})

    def _make_request(self, params):
        if self.api_key:
            params["api_key"] = self.api_key
        try:
            resp = self.session.get(BASE_URL, params=params, timeout=15)
            if resp.status_code == 404:
                return None
            if resp.status_code == 429:
                st.warning("Rate limit hit. Get API key at open.fda.gov")
                return None
            if resp.status_code != 200:
                return None
            return resp.json()
        except Exception:
            return None

    def search_drug(self, drug_name, search_type="brand"):
        drug_name = drug_name.strip().upper()
        if search_type == "brand":
            q = 'openfda.brand_name:"' + drug_name + '"'
        else:
            q = 'openfda.generic_name:"' + drug_name + '"'
        data = self._make_request({"search": q, "limit": 1})
        if not data or not data.get("results"):
            if search_type == "brand":
                q = 'openfda.brand_name:' + drug_name
            else:
                q = 'openfda.generic_name:' + drug_name
            data = self._make_request({"search": q, "limit": 1})
        if data and data.get("results"):
            return data["results"][0]
        return None

    def extract_interaction_text(self, label):
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

    def _get_label_drugs(self, label):
        drugs = set()
        openfda = label.get("openfda", {})
        for field in ["brand_name", "generic_name", "substance_name"]:
            values = openfda.get(field, [])
            if isinstance(values, str):
                values = [values]
            for v in values:
                drugs.add(v.lower().strip())
        return drugs

    def extract_drugs_from_text(self, text, label):
        if not text:
            return []
        known_drugs = KNOWN_DRUGS | self._get_label_drugs(label)
        found = []
        text_lower = text.lower()
        seen = set()
        for drug in known_drugs:
            if len(drug) < 3:
                continue
            pattern = r"\b" + re.escape(drug) + r"\b"
            for match in re.finditer(pattern, text_lower):
                if drug not in seen:
                    start = max(0, match.start() - 60)
                    end = min(len(text), match.end() + 60)
                    snippet = text[start:end].strip()
                    found.append({"drug": drug.title(), "context": "..." + snippet + "...", "method": "dictionary"})
                    seen.add(drug)
                    break
        cap_pattern = r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\b"
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
                found.append({"drug": candidate, "context": "..." + snippet + "...", "method": "heuristic"})
                seen.add(cand_lower)
        found.sort(key=lambda x: text_lower.find(x["drug"].lower()) if text_lower.find(x["drug"].lower()) != -1 else 99999)
        return found

    def get_interactions(self, drug_name, search_type="brand"):
        label = self.search_drug(drug_name, search_type)
        if not label:
            return {"success": False, "drug": drug_name, "error": "No FDA label found for '" + drug_name + "'", "interacting_drugs": []}
        openfda = label.get("openfda", {})
        brand_names = openfda.get("brand_name", [])
        generic_names = openfda.get("generic_name", [])
        manufacturer = openfda.get("manufacturer_name", ["Unknown"])
        if isinstance(manufacturer, list):
            manufacturer = manufacturer[0]
        interaction_text = self.extract_interaction_text(label)
        if not interaction_text:
            return {"success": True, "drug": drug_name, "brand_names": brand_names, "generic_names": generic_names, "manufacturer": manufacturer, "interacting_drugs": [], "note": "No interactions section"}
        interacting_drugs = self.extract_drugs_from_text(interaction_text, label)
        return {"success": True, "drug": drug_name, "brand_names": brand_names, "generic_names": generic_names, "manufacturer": manufacturer, "interacting_drugs": interacting_drugs, "interaction_count": len(interacting_drugs)}


def check_interaction_between_two(drug_a, drug_b):
    finder = OpenFDAInteractionFinder()
    result = finder.get_interactions(drug_a, "generic")
    if not result["success"]:
        return {"found": False, "reason": result.get("error", "Unknown")}
    interacting = result.get("interacting_drugs", [])
    drug_b_lower = drug_b.lower()
    for item in interacting:
        if item["drug"].lower() == drug_b_lower or drug_b_lower in item["drug"].lower():
            return {"found": True, "context": item["context"], "method": item["method"]}
    return {"found": False, "reason": "No interaction found in FDA label"}


st.title("💊 MedCheck AI")
st.caption("Intelligent Drug Interaction Analysis | Powered by openFDA")
st.markdown("---")

tab1, tab2 = st.tabs(["🔍 Two-Drug Check", "📋 Single Drug Profile"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        drug1 = st.text_input("Drug 1", placeholder="e.g. Warfarin")
    with c2:
        drug2 = st.text_input("Drug 2", placeholder="e.g. Aspirin")
    if st.button("Analyze Interaction", use_container_width=True):
        if not drug1 or not drug2:
            st.error("Enter both drug names")
        else:
            with st.spinner("Checking FDA labels..."):
                result = check_interaction_between_two(drug1, drug2)
            if result["found"]:
                st.error("⚠️ INTERACTION DETECTED")
                st.markdown("**" + drug1 + "** may interact with **" + drug2 + "**")
                st.info(result["context"])
                st.caption("Source: FDA Drug Label | Detection: " + result["method"].title())
            else:
                st.success("✅ No interaction found in FDA label")
                with st.expander("See details"):
                    st.write(result["reason"])

with tab2:
    drug_input = st.text_input("Enter drug name", placeholder="e.g. Metformin", key="d3")
    search_type = st.radio("Search by", ["generic", "brand"], horizontal=True)
    if st.button("Find Interactions", key="btn2", use_container_width=True):
        if not drug_input:
            st.error("Enter a drug name")
        else:
            with st.spinner("Scanning FDA database..."):
                finder = OpenFDAInteractionFinder()
                result = finder.get_interactions(drug_input, search_type)
            if not result["success"]:
                st.error(result["error"])
            else:
                c1, c2 = st.columns(2)
                c1.metric("Interactions", len(result.get("interacting_drugs", [])))
                c2.metric("Manufacturer", result.get("manufacturer", "N/A")[:20])
                st.write("**Brand:**", ", ".join(result.get("brand_names", [])) or "N/A")
                st.write("**Generic:**", ", ".join(result.get("generic_names", [])) or "N/A")
                st.divider()
                drugs = result.get("interacting_drugs", [])
                if not drugs:
                    st.warning("No interacting drugs found")
                else:
                    for item in drugs:
                        icon = "📖" if item["method"] == "dictionary" else "🔎"
                        with st.expander(icon + " " + item["drug"]):
                            st.write(item["context"])
                            st.caption("Detected via " + item["method"] + " matching")

st.markdown("---")
st.caption("MedCheck AI | Data: U.S. FDA openFDA | Not medical advice")

  