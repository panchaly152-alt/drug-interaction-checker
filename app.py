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
    drug_name = drug_name.strip().upper()
    if search_type == "brand":
        q = 'openfda.brand_name:"' + drug_name + '"'
    else:
        q = 'openfda.generic_name:"' + drug_name + '"'
    try:
        r = requests.get(BASE_URL, params={"search": q, "limit": 1}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("results"):
                return data["results"][0]
        # fallback partial
        if search_type == "brand":
            q = 'openfda.brand_name:' + drug_name
        else:
            q = 'openfda.generic_name:' + drug_name
        r = requests.get(BASE_URL, params={"search": q, "limit": 1}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("results"):
                return data["results"][0]
    except Exception as e:
        return {"error": str(e)}
    return None


def get_interaction_text(label):
    if not label or isinstance(label, dict) and "error" in label:
        return None
    interactions = label.get("drug_interactions")
    if interactions and isinstance(interactions, list) and len(interactions) > 0:
        return interactions[0]
    # fallback
    for key, val in label.items():
        if "drug_interaction" in key.lower():
            if isinstance(val, list) and val:
                return val[0]
            elif isinstance(val, str):
                return val
    return None


def extract_drugs(text, label):
    if not text:
        return []
    # Build known set from label + hardcoded
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
    
    # Dictionary match
    for drug in known:
        if len(drug) < 3:
            continue
        pat = r"\b" + re.escape(drug) + r"\b"
        if re.search(pat, text_lower):
            if drug not in seen:
                idx = text_lower.find(drug)
                start = max(0, idx - 60)
                end = min(len(text), idx + len(drug) + 60)
                found.append({"drug": drug.title(), "context": text[start:end], "method": "dictionary"})
                seen.add(drug)
    
    # Heuristic match
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
            found.append({"drug": cand, "context": text[start:end], "method": "heuristic"})
            seen.add(cl)
    
    found.sort(key=lambda x: text_lower.find(x["drug"].lower()) if text_lower.find(x["drug"].lower()) != -1 else 99999)
    return found


def get_all_interactions(drug_name, search_type="generic"):
    label = fetch_label(drug_name, search_type)
    if label is None:
        return {"ok": False, "error": "No FDA label found for '" + drug_name + "'"}
    if isinstance(label, dict) and "error" in label:
        return {"ok": False, "error": "API error: " + label["error"]}
    
    openfda = label.get("openfda", {})
    brand = openfda.get("brand_name", [])
    generic = openfda.get("generic_name", [])
    mfr = openfda.get("manufacturer_name", ["Unknown"])
    if isinstance(mfr, list):
        mfr = mfr[0]
    
    text = get_interaction_text(label)
    if not text:
        return {
            "ok": True, "drug": drug_name, "brand": brand, "generic": generic,
            "manufacturer": mfr, "interactions": [], "raw_len": 0,
            "note": "No drug_interactions section in label"
        }
    
    drugs = extract_drugs(text, label)
    return {
        "ok": True, "drug": drug_name, "brand": brand, "generic": generic,
        "manufacturer": mfr, "interactions": drugs, "raw_len": len(text),
        "raw_preview": text[:500]
    }


def check_two(drug_a, drug_b):
    data = get_all_interactions(drug_a, "generic")
    if not data["ok"]:
        return {"found": False, "reason": data["error"], "debug": data}
    
    interactions = data.get("interactions", [])
    b_lower = drug_b.lower()
    
    for item in interactions:
        item_lower = item["drug"].lower()
        if item_lower == b_lower or b_lower in item_lower or item_lower in b_lower:
            return {"found": True, "context": item["context"], "method": item["method"], "debug": data}
    
    return {"found": False, "reason": "Drug '" + drug_b + "' not in extracted interaction list", "debug": data}


# ===================== UI =====================
st.title("💊 MedCheck AI")
st.caption("Powered by openFDA | FDA Official Drug Labels")
st.markdown("---")

tab1, tab2 = st.tabs(["🔍 Two-Drug Check", "📋 Single Drug Profile"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        d1 = st.text_input("Drug 1", placeholder="e.g. Warfarin")
    with c2:
        d2 = st.text_input("Drug 2", placeholder="e.g. Aspirin")
    
    if st.button("Analyze Interaction", use_container_width=True):
        if not d1 or not d2:
            st.error("Enter both drugs")
        else:
            with st.spinner("Fetching from openFDA..."):
                result = check_two(d1, d2)
            
            if result["found"]:
                st.error("⚠️ INTERACTION DETECTED")
                st.write("**" + d1 + "** + **" + d2 + "**")
                st.info(result["context"])
                st.caption("Detected via: " + result["method"])
            else:
                st.success("✅ No interaction found")
                st.caption("Source: FDA Drug Label (openFDA)")
            
            # DEBUG expander
            with st.expander("Debug: See what FDA label contains"):
                debug = result.get("debug", {})
                st.write("Label found:", debug.get("ok", False))
                st.write("Brand names:", debug.get("brand", []))
                st.write("Generic names:", debug.get("generic", []))
                st.write("Interaction text length:", debug.get("raw_len", 0))
                st.write("Extracted drugs count:", len(debug.get("interactions", [])))
                st.write("Extracted drugs:", [i["drug"] for i in debug.get("interactions", [])])
                if debug.get("raw_preview"):
                    st.text_area("Raw text preview", debug["raw_preview"], height=100)

with tab2:
    drug_input = st.text_input("Drug name", placeholder="e.g. Metformin", key="d3")
    stype = st.radio("Search by", ["generic", "brand"], horizontal=True)
    
    if st.button("Find Interactions", key="btn2", use_container_width=True):
        if not drug_input:
            st.error("Enter a drug name")
        else:
            with st.spinner("Scanning..."):
                data = get_all_interactions(drug_input, stype)
            
            if not data["ok"]:
                st.error(data["error"])
            else:
                c1, c2 = st.columns(2)
                c1.metric("Interactions", len(data["interactions"]))
                c2.metric("Mfr", data["manufacturer"][:20])
                st.write("Brand:", ", ".join(data["brand"]) or "N/A")
                st.write("Generic:", ", ".join(data["generic"]) or "N/A")
                st.divider()
                
                if not data["interactions"]:
                    st.warning("No interactions extracted")
                    if data.get("note"):
                        st.write(data["note"])
                else:
                    for item in data["interactions"]:
                        icon = "📖" if item["method"] == "dictionary" else "🔎"
                        with st.expander(icon + " " + item["drug"]):
                            st.write(item["context"])
                            st.caption(item["method"])

st.markdown("---")
st.caption("MedCheck AI | Data: U.S. FDA openFDA | Not medical advice")
