"""
================================================================================
MEDCHECK AI V4 — Polypharmacy Intelligence Platform
Evidence-Based Drug Interaction Analyzer
U.S. FDA openFDA + Clinical Rule Engine + Patient Risk Context
================================================================================
"""

import streamlit as st
import requests
import re
import io
import csv
from datetime import datetime
from itertools import combinations
from collections import defaultdict

APP_VERSION = "V4.1"

st.set_page_config(page_title="MedCheck AI V4", page_icon="💊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* ---- Header ---- */
    .main-header {font-size:2.8rem;font-weight:800;background:linear-gradient(90deg,#42a5f5,#66bb6a);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-0.5px;}
    .sub-header {font-size:1.05rem;color:#9aa5b1;margin-top:-8px;margin-bottom:22px;}
    .badge-row {margin-bottom:18px;}
    .badge {display:inline-block;background:rgba(66,165,245,0.12);color:#42a5f5;border:1px solid rgba(66,165,245,0.35);padding:4px 12px;border-radius:20px;margin-right:6px;font-size:0.78rem;font-weight:600;}

    /* ---- Risk cards (theme-safe: subtle tinted bg + colored border, works light or dark) ---- */
    .risk-major {background:rgba(211,47,47,0.10);padding:16px 18px;border-radius:12px;border-left:6px solid #d32f2f;margin:10px 0;}
    .risk-moderate {background:rgba(245,124,0,0.10);padding:16px 18px;border-radius:12px;border-left:6px solid #f57c00;margin:10px 0;}
    .risk-minor {background:rgba(56,142,60,0.10);padding:16px 18px;border-radius:12px;border-left:6px solid #388e3c;margin:10px 0;}
    .risk-theoretical {background:rgba(25,118,210,0.10);padding:16px 18px;border-radius:12px;border-left:6px solid #1976d2;margin:10px 0;}

    /* ---- Chips ---- */
    .drug-chip {display:inline-block;background:rgba(66,165,245,0.15);color:#42a5f5;padding:6px 14px;border-radius:20px;margin:3px;font-weight:600;font-size:0.88rem;border:1px solid rgba(66,165,245,0.25);}

    /* ---- Metric cards (theme-safe) ---- */
    .metric-card {text-align:center;padding:20px 10px;background:rgba(128,128,128,0.08);border-radius:14px;border:1px solid rgba(128,128,128,0.18);}
    .metric-value {font-size:2.1rem;font-weight:800;}
    .metric-label {font-size:0.78rem;color:#9aa5b1;text-transform:uppercase;letter-spacing:0.6px;margin-top:2px;}

    /* ---- Evidence box ---- */
    .evidence-box {background:rgba(128,128,128,0.10);padding:14px;border-radius:10px;font-family:'Courier New',monospace;font-size:0.85rem;border:1px solid rgba(128,128,128,0.2);line-height:1.5;}

    /* ---- Misc ---- */
    .risk-score-wrap {padding:18px;border-radius:14px;background:rgba(128,128,128,0.08);border:1px solid rgba(128,128,128,0.18);text-align:center;}
    div[data-testid="stExpander"] {border-radius:10px;}
</style>
""", unsafe_allow_html=True)

FDA_URL = "https://api.fda.gov/drug/label.json"

# =========================================================
# DRUG ALIASES (Brand → Generic)
# =========================================================
ALIASES = {
    "paracetamol":"acetaminophen","tylenol":"acetaminophen","advil":"ibuprofen",
    "motrin":"ibuprofen","brufen":"ibuprofen","aleve":"naproxen","coumadin":"warfarin",
    "plavix":"clopidogrel","lipitor":"atorvastatin","zocor":"simvastatin",
    "crestor":"rosuvastatin","glucophage":"metformin","lasix":"furosemide",
    "norvasc":"amlodipine","lopressor":"metoprolol","toprol":"metoprolol",
    "protonix":"pantoprazole","prilosec":"omeprazole","nexium":"esomeprazole",
    "xanax":"alprazolam","valium":"diazepam","prozac":"fluoxetine","zoloft":"sertraline",
    "paxil":"paroxetine","lexapro":"escitalopram","ventolin":"albuterol",
    "salbutamol":"albuterol","lantus":"insulin glargine","novolog":"insulin aspart",
    "humalog":"insulin lispro","celebrex":"celecoxib","voltaren":"diclofenac",
    "toradol":"ketorolac","indocin":"indomethacin","mobic":"meloxicam",
    "glucotrol":"glipizide","diabeta":"glyburide","actos":"pioglitazone",
    "januvia":"sitagliptin","farxiga":"dapagliflozin","jardiance":"empagliflozin",
    "ozempic":"semaglutide","victoza":"liraglutide","pravachol":"pravastatin",
    "mevacor":"lovastatin","prinivil":"lisinopril","vasotec":"enalapril",
    "capoten":"captopril","cozaar":"losartan","diovan":"valsartan",
    "avapro":"irbesartan","procardia":"nifedipine","tenormin":"atenolol",
    "inderal":"propranolol","coreg":"carvedilol","prevacid":"lansoprazole",
    "aciphex":"rabeprazole","pepcid":"famotidine","benadryl":"diphenhydramine",
    "claritin":"loratadine","zyrtec":"cetirizine","singulair":"montelukast",
    "spiriva":"tiotropium","remicade":"infliximab","humira":"adalimumab",
    "xeljanz":"tofacitinib","carafate":"sucralfate","prandin":"repaglinide",
    "invokana":"canagliflozin","zetia":"ezetimibe","lopid":"gemfibrozil",
    "immitrex":"sumatriptan","ranexa":"ranolazine","imodium":"loperamide",
    "asacol":"mesalamine","emend":"aprepitant","kytril":"granisetron",
    "zofran":"ondansetron","reglan":"metoclopramide","haldol":"haloperidol",
    "deltasone":"prednisone","decadron":"dexamethasone","aldactone":"spironolactone",
    "microzide":"hydrochlorothiazide","synthroid":"levothyroxine","trexall":"methotrexate",
    "prograf":"tacrolimus","neoral":"cyclosporine","colcrys":"colchicine",
    "zyloprim":"allopurinol","uloric":"febuxostat","cordarone":"amiodarone",
    "betapace":"sotalol","lanoxin":"digoxin","nitrostat":"nitroglycerin",
    "viagra":"sildenafil","cialis":"tadalafil","ultram":"tramadol",
    "ms contin":"morphine","oxycontin":"oxycodone","duragesic":"fentanyl",
    "dilantin":"phenytoin","tegretol":"carbamazepine","depakote":"valproic acid",
    "lamictal":"lamotrigine","keppra":"levetiracetam","topamax":"topiramate",
    "neurontin":"gabapentin","lyrica":"pregabalin","rifadin":"rifampin",
    "zithromax":"azithromycin","biaxin":"clarithromycin","cipro":"ciprofloxacin",
    "diflucan":"fluconazole","nizoral":"ketoconazole","sporanox":"itraconazole",
    "vfend":"voriconazole","lantus":"insulin glargine","lantus solostar":"insulin glargine",
}

# =========================================================
# DRUG CLASS DATABASE
# =========================================================
DRUG_CLASSES = {
    "warfarin":"Anticoagulant (VKA)","heparin":"Anticoagulant","enoxaparin":"Anticoagulant (LMWH)",
    "rivaroxaban":"DOAC (FXa)","apixaban":"DOAC (FXa)","dabigatran":"DOAC (DTC)","edoxaban":"DOAC (FXa)",
    "aspirin":"Antiplatelet / NSAID","clopidogrel":"Antiplatelet (P2Y12)","prasugrel":"Antiplatelet (P2Y12)",
    "ticagrelor":"Antiplatelet (P2Y12)","cilostazol":"Antiplatelet","dipyridamole":"Antiplatelet",
    "ibuprofen":"NSAID","naproxen":"NSAID","diclofenac":"NSAID","ketorolac":"NSAID",
    "indomethacin":"NSAID","meloxicam":"NSAID","celecoxib":"COX-2 NSAID","etoricoxib":"COX-2 NSAID",
    "metformin":"Biguanide","glipizide":"Sulfonylurea","glyburide":"Sulfonylurea","glimepiride":"Sulfonylurea",
    "pioglitazone":"TZD","rosiglitazone":"TZD","sitagliptin":"DPP-4i","saxagliptin":"DPP-4i",
    "linagliptin":"DPP-4i","dapagliflozin":"SGLT2i","empagliflozin":"SGLT2i","canagliflozin":"SGLT2i",
    "semaglutide":"GLP-1 RA","liraglutide":"GLP-1 RA","dulaglutide":"GLP-1 RA","exenatide":"GLP-1 RA",
    "insulin":"Insulin","insulin glargine":"Insulin","insulin aspart":"Insulin","insulin lispro":"Insulin",
    "insulin detemir":"Insulin","insulin nph":"Insulin","repaglinide":"Meglitinide","nateglinide":"Meglitinide",
    "acarbose":"Alpha-glucosidase inhibitor","voglibose":"Alpha-glucosidase inhibitor",
    "atorvastatin":"Statin","simvastatin":"Statin","rosuvastatin":"Statin","pravastatin":"Statin",
    "lovastatin":"Statin","fluvastatin":"Statin","pitavastatin":"Statin",
    "lisinopril":"ACEi","enalapril":"ACEi","captopril":"ACEi","ramipril":"ACEi","perindopril":"ACEi",
    "benazepril":"ACEi","fosinopril":"ACEi","quinapril":"ACEi",
    "losartan":"ARB","valsartan":"ARB","irbesartan":"ARB","telmisartan":"ARB","olmesartan":"ARB",
    "candesartan":"ARB","azilsartan":"ARB",
    "amlodipine":"DHP-CCB","nifedipine":"DHP-CCB","felodipine":"DHP-CCB",
    "verapamil":"Non-DHP CCB","diltiazem":"Non-DHP CCB",
    "metoprolol":"Beta-1 blocker","atenolol":"Beta-1 blocker","bisoprolol":"Beta-1 blocker",
    "propranolol":"Non-selective BB","carvedilol":"Alpha/Beta blocker","labetalol":"Alpha/Beta blocker",
    "nebivolol":"Beta-1 blocker","sotalol":"Class III antiarrhythmic","esmolol":"Ultra-short BB",
    "omeprazole":"PPI","esomeprazole":"PPI","pantoprazole":"PPI","lansoprazole":"PPI",
    "rabeprazole":"PPI","dexlansoprazole":"PPI","famotidine":"H2RA","ranitidine":"H2RA","cimetidine":"H2RA",
    "sucralfate":"Mucosal protectant",
    "sertraline":"SSRI","fluoxetine":"SSRI","escitalopram":"SSRI","paroxetine":"SSRI",
    "citalopram":"SSRI","fluvoxamine":"SSRI","venlafaxine":"SNRI","duloxetine":"SNRI",
    "desvenlafaxine":"SNRI","milnacipran":"SNRI","levomilnacipran":"SNRI",
    "bupropion":"NDRI","mirtazapine":"NaSSA","trazodone":"SARI","amitriptyline":"TCA",
    "nortriptyline":"TCA","imipramine":"TCA","clomipramine":"TCA","doxepin":"TCA",
    "phenelzine":"MAOI","tranylcypromine":"MAOI","isocarboxazid":"MAOI",
    "selegiline":"MAO-Bi","rasagiline":"MAO-Bi","safinamide":"MAO-Bi",
    "alprazolam":"BZD","lorazepam":"BZD","clonazepam":"BZD","diazepam":"BZD","midazolam":"BZD",
    "temazepam":"BZD","triazolam":"BZD","oxazepam":"BZD","chlordiazepoxide":"BZD",
    "phenytoin":"Antiepileptic","carbamazepine":"Antiepileptic","valproic acid":"Antiepileptic",
    "lamotrigine":"Antiepileptic","levetiracetam":"Antiepileptic","topiramate":"Antiepileptic",
    "gabapentin":"Antiepileptic","pregabalin":"Antiepileptic","oxcarbazepine":"Antiepileptic",
    "eslicarbazepine":"Antiepileptic","lacosamide":"Antiepileptic","zonisamide":"Antiepileptic",
    "ethosuximide":"Antiepileptic","clobazam":"BZD antiepileptic","rufinamide":"Antiepileptic",
    "vigabatrin":"Antiepileptic","tiagabine":"Antiepileptic","felbamate":"Antiepileptic",
    "rifampin":"Rifamycin","rifabutin":"Rifamycin","azithromycin":"Macrolide",
    "erythromycin":"Macrolide","clarithromycin":"Macrolide","ciprofloxacin":"Fluoroquinolone",
    "levofloxacin":"Fluoroquinolone","moxifloxacin":"Fluoroquinolone","ofloxacin":"Fluoroquinolone",
    "norfloxacin":"Fluoroquinolone","amoxicillin":"Penicillin","ampicillin":"Penicillin",
    "cloxacillin":"Penicillin","piperacillin":"Penicillin","amoxicillin-clavulanate":"Beta-lactam/BLI",
    "piperacillin-tazobactam":"Beta-lactam/BLI","ceftriaxone":"Cephalosporin","cefotaxime":"Cephalosporin",
    "cefpodoxime":"Cephalosporin","cefuroxime":"Cephalosporin","cefazolin":"Cephalosporin",
    "cefoxitin":"Cephalosporin","cefepime":"Cephalosporin","meropenem":"Carbapenem",
    "imipenem":"Carbapenem","ertapenem":"Carbapenem","vancomycin":"Glycopeptide",
    "teicoplanin":"Glycopeptide","linezolid":"Oxazolidinone","daptomycin":"Lipopeptide",
    "gentamicin":"Aminoglycoside","amikacin":"Aminoglycoside","tobramycin":"Aminoglycoside",
    "streptomycin":"Aminoglycoside","metronidazole":"Nitroimidazole","tinidazole":"Nitroimidazole",
    "doxycycline":"Tetracycline","minocycline":"Tetracycline","tigecycline":"Glycylcycline",
    "chloramphenicol":"Amphenicol","trimethoprim-sulfamethoxazole":"Sulfonamide",
    "nitrofurantoin":"Nitrofuran","fosfomycin":"Phosphonic acid",
    "fluconazole":"Azole antifungal","ketoconazole":"Azole antifungal","itraconazole":"Azole antifungal",
    "voriconazole":"Azole antifungal","posaconazole":"Azole antifungal","isavuconazole":"Azole antifungal",
    "amphotericin b":"Polyene antifungal","caspofungin":"Echinocandin","micafungin":"Echinocandin",
    "anidulafungin":"Echinocandin","terbinafine":"Allylamine antifungal","griseofulvin":"Antifungal",
    "nystatin":"Polyene antifungal",
    "amiodarone":"Class III antiarrhythmic","sotalol":"Class III antiarrhythmic",
    "digoxin":"Cardiac glycoside","digitoxin":"Cardiac glycoside",
    "nitroglycerin":"Nitrate","isosorbide dinitrate":"Nitrate","isosorbide mononitrate":"Nitrate",
    "sildenafil":"PDE5i","tadalafil":"PDE5i","vardenafil":"PDE5i","avanafil":"PDE5i",
    "ivabradine":"Funny channel inhibitor","ranolazine":"Anti-anginal",
    "tramadol":"Opioid","codeine":"Opioid","morphine":"Opioid","oxycodone":"Opioid",
    "fentanyl":"Opioid","hydrocodone":"Opioid","hydromorphone":"Opioid","buprenorphine":"Partial opioid agonist",
    "methadone":"Opioid","tapentadol":"Opioid","meperidine":"Opioid","pentazocine":"Mixed opioid agonist-antagonist",
    "nalbuphine":"Mixed opioid agonist-antagonist","butorphanol":"Mixed opioid agonist-antagonist",
    "ondansetron":"5-HT3 antagonist","granisetron":"5-HT3 antagonist","palonosetron":"5-HT3 antagonist",
    "metoclopramide":"D2 antagonist / Prokinetic","domperidone":"D2 antagonist / Prokinetic",
    "haloperidol":"Typical antipsychotic","prochlorperazine":"Phenothiazine antiemetic",
    "promethazine":"Phenothiazine antiemetic","aprepitant":"NK1 antagonist","fosaprepitant":"NK1 antagonist",
    "dexamethasone":"Corticosteroid","loperamide":"Opioid antidiarrheal",
    "mesalamine":"5-ASA","sulfasalazine":"5-ASA / DMARD","balsalazide":"5-ASA",
    "infliximab":"Anti-TNF","adalimumab":"Anti-TNF","certolizumab":"Anti-TNF","golimumab":"Anti-TNF",
    "vedolizumab":"Anti-integrin","ustekinumab":"Anti-IL-12/23","tofacitinib":"JAK inhibitor",
    "baricitinib":"JAK inhibitor","upadacitinib":"JAK inhibitor","filgotinib":"JAK inhibitor",
    "prednisone":"Corticosteroid","prednisolone":"Corticosteroid","methylprednisolone":"Corticosteroid",
    "betamethasone":"Corticosteroid","hydrocortisone":"Corticosteroid","fludrocortisone":"Mineralocorticoid",
    "beclomethasone":"ICS","budesonide":"ICS","fluticasone":"ICS","mometasone":"ICS","ciclesonide":"ICS",
    "triamcinolone":"Corticosteroid",
    "furosemide":"Loop diuretic","bumetanide":"Loop diuretic","torsemide":"Loop diuretic",
    "hydrochlorothiazide":"Thiazide diuretic","chlorthalidone":"Thiazide-like","indapamide":"Thiazide-like",
    "metolazone":"Thiazide-like","spironolactone":"K-sparing diuretic","eplerenone":"K-sparing diuretic",
    "amiloride":"K-sparing diuretic","triamterene":"K-sparing diuretic",
    "acetazolamide":"Carbonic anhydrase inhibitor","mannitol":"Osmotic diuretic",
    "levothyroxine":"Thyroid hormone","liothyronine":"Thyroid hormone",
    "methimazole":"Antithyroid","propylthiouracil":"Antithyroid","potassium iodide":"Iodine",
    "methotrexate":"Antimetabolite / DMARD","azathioprine":"Purine analog","mycophenolate":"Immunosuppressant",
    "mycophenolate mofetil":"Immunosuppressant","tacrolimus":"Calcineurin inhibitor",
    "cyclosporine":"Calcineurin inhibitor","sirolimus":"mTOR inhibitor","everolimus":"mTOR inhibitor",
    "cyclophosphamide":"Alkylating agent","chlorambucil":"Alkylating agent","leflunomide":"DMARD",
    "hydroxychloroquine":"Antimalarial / DMARD","sulfasalazine":"DMARD","etanercept":"Anti-TNF fusion protein",
    "anakinra":"IL-1 antagonist","abatacept":"T-cell modulator","rituximab":"Anti-CD20",
    "tocilizumab":"Anti-IL-6R","sarilumab":"Anti-IL-6R","belimumab":"Anti-BLyS",
    "colchicine":"Anti-gout","allopurinol":"Xanthine oxidase inhibitor","febuxostat":"Xanthine oxidase inhibitor",
    "probenecid":"Uricosuric","benzbromarone":"Uricosuric","pegloticase":"Uric acid oxidase",
    "rasburicase":"Uric acid oxidase",
    "diphenhydramine":"1st-gen antihistamine","loratadine":"2nd-gen antihistamine",
    "cetirizine":"2nd-gen antihistamine","fexofenadine":"2nd-gen antihistamine",
    "desloratadine":"2nd-gen antihistamine","levocetirizine":"2nd-gen antihistamine",
    "montelukast":"LTRA","zafirlukast":"LTRA","albuterol":"SABA","salbutamol":"SABA",
    "levalbuterol":"SABA","salmeterol":"LABA","formoterol":"LABA","indacaterol":"Ultra-LABA",
    "olodaterol":"Ultra-LABA","tiotropium":"LAMA","ipratropium":"SAMA","umeclidinium":"LAMA",
    "aclidinium":"LAMA","glycopyrrolate":"LAMA","theophylline":"Methylxanthine","roflumilast":"PDE4i",
    "omalizumab":"Anti-IgE","mepolizumab":"Anti-IL-5","reslizumab":"Anti-IL-5","benralizumab":"Anti-IL-5R",
    "dupilumab":"Anti-IL-4R",
    "ezetimibe":"Cholesterol absorption inhibitor","gemfibrozil":"Fibrate","fenofibrate":"Fibrate",
    "bezafibrate":"Fibrate","ciprofibrate":"Fibrate","niacin":"Vitamin B3","omega-3 fatty acids":"Fish oil",
    "icosapent ethyl":"EPA ester","bempedoic acid":"ACL inhibitor","evolocumab":"PCSK9i",
    "alirocumab":"PCSK9i","inclisiran":"siRNA PCSK9i",
    "risperidone":"Atypical antipsychotic","olanzapine":"Atypical antipsychotic",
    "quetiapine":"Atypical antipsychotic","aripiprazole":"Atypical antipsychotic",
    "ziprasidone":"Atypical antipsychotic","paliperidone":"Atypical antipsychotic",
    "lurasidone":"Atypical antipsychotic","brexpiprazole":"Atypical antipsychotic",
    "cariprazine":"Atypical antipsychotic","clozapine":"Atypical antipsychotic",
    "chlorpromazine":"Typical antipsychotic","fluphenazine":"Typical antipsychotic",
    "perphenazine":"Typical antipsychotic","thiothixene":"Typical antipsychotic",
    "loxapine":"Typical antipsychotic","molindone":"Typical antipsychotic","pimavanserin":"5-HT2A inverse agonist",
    "levodopa":"Dopamine precursor","carbidopa":"DDC inhibitor","levodopa-carbidopa":"Dopaminergic combo",
    "levodopa-benserazide":"Dopaminergic combo","ropinirole":"Dopamine agonist","pramipexole":"Dopamine agonist",
    "rotigotine":"Dopamine agonist","bromocriptine":"Dopamine agonist","cabergoline":"Dopamine agonist",
    "entacapone":"COMT inhibitor","tolcapone":"COMT inhibitor","opicapone":"COMT inhibitor",
    "amantadine":"NMDA antagonist","trihexyphenidyl":"Anticholinergic","benztropine":"Anticholinergic",
    "biperiden":"Anticholinergic","donepezil":"AChE inhibitor","rivastigmine":"AChE inhibitor",
    "galantamine":"AChE inhibitor","memantine":"NMDA antagonist",
    "alendronate":"Bisphosphonate","risedronate":"Bisphosphonate","ibandronate":"Bisphosphonate",
    "zoledronic acid":"Bisphosphonate","pamidronate":"Bisphosphonate","denosumab":"Anti-RANKL",
    "teriparatide":"PTH analog","abaloparatide":"PTHrP analog","romosozumab":"Anti-sclerostin",
    "raloxifene":"SERM","bazedoxifene":"SERM","tamoxifen":"SERM","toremifene":"SERM",
    "calcitonin":"Thyroid hormone analog",
    "ethinyl estradiol":"Estrogen","estradiol":"Estrogen","estriol":"Estrogen",
    "conjugated estrogens":"Estrogen","progesterone":"Progestogen","medroxyprogesterone":"Progestogen",
    "norethindrone":"Progestogen","levonorgestrel":"Progestogen","drospirenone":"Progestogen",
    "cyproterone acetate":"Antiandrogen / Progestogen","finasteride":"5-ARI","dutasteride":"5-ARI",
    "testosterone":"Androgen","testosterone cypionate":"Androgen","testosterone enanthate":"Androgen",
    "testosterone gel":"Androgen","danazol":"Weak androgen","clomiphene":"SERM (fertility)",
    "letrozole":"Aromatase inhibitor","anastrozole":"Aromatase inhibitor","exemestane":"Aromatase inhibitor",
    "fulvestrant":"ER antagonist","bicalutamide":"Antiandrogen","enzalutamide":"Antiandrogen",
    "apalutamide":"Antiandrogen","darolutamide":"Antiandrogen","degarelix":"GnRH antagonist",
    "leuprolide":"GnRH agonist","goserelin":"GnRH agonist","triptorelin":"GnRH agonist",
    "cetrorelix":"GnRH antagonist","ganirelix":"GnRH antagonist","elagolix":"GnRH antagonist (oral)",
    "relugolix":"GnRH antagonist (oral)","cabergoline":"Dopamine agonist","bromocriptine":"Dopamine agonist",
    "oxytocin":"Uterotonic","carboprost":"PGF2alpha analog","dinoprostone":"PGE2 analog",
    "misoprostol":"PGE1 analog","mifepristone":"Progesterone antagonist","ulipristal":"SPRM",
    "imatinib":"TKI (BCR-ABL)","dasatinib":"TKI (BCR-ABL)","nilotinib":"TKI (BCR-ABL)",
    "gefitinib":"EGFR TKI","erlotinib":"EGFR TKI","afatinib":"EGFR TKI","osimertinib":"EGFR TKI (3G)",
    "lapatinib":"HER2/EGFR TKI","neratinib":"Pan-HER TKI","tucatinib":"HER2 TKI",
    "trastuzumab":"Anti-HER2","pertuzumab":"Anti-HER2","ado-trastuzumab emtansine":"ADC (HER2)",
    "fam-trastuzumab deruxtecan":"ADC (HER2)","bevacizumab":"Anti-VEGF","ranibizumab":"Anti-VEGF Fab",
    "aflibercept":"VEGF trap","ramucirumab":"Anti-VEGFR2","sunitinib":"Multi-TKI","sorafenib":"Multi-TKI",
    "pazopanib":"Multi-TKI","axitinib":"VEGFR TKI","cabozantinib":"Multi-TKI","lenvatinib":"Multi-TKI",
    "regorafenib":"Multi-TKI","vandetanib":"Multi-TKI","crizotinib":"ALK/MET/ROS1 TKI",
    "ceritinib":"ALK TKI","alectinib":"ALK TKI","brigatinib":"ALK TKI","lorlatinib":"ALK TKI (3G)",
    "entrectinib":"ROS1/TRK TKI","repotrectinib":"ROS1/TRK TKI","dabrafenib":"BRAFi","trametinib":"MEKi",
    "vemurafenib":"BRAFi","encorafenib":"BRAFi","binimetinib":"MEKi","cobimetinib":"MEKi",
    "palbociclib":"CDK4/6i","ribociclib":"CDK4/6i","abemaciclib":"CDK4/6i","temsirolimus":"mTORi",
    "idelalisib":"PI3Kdelta i","copanlisib":"PI3K i","duvelisib":"PI3K i","venetoclax":"BCL-2i",
    "ibrutinib":"BTKi","acalabrutinib":"BTKi","zanubrutinib":"BTKi","belinostat":"HDACi",
    "vorinostat":"HDACi","panobinostat":"HDACi","romidepsin":"HDACi","bortezomib":"Proteasome i",
    "carfilzomib":"Proteasome i","ixazomib":"Proteasome i","lenalidomide":"IMiD","pomalidomide":"IMiD",
    "thalidomide":"IMiD","azacitidine":"Hypomethylating","decitabine":"Hypomethylating",
    "enasidenib":"IDH2i","ivosidenib":"IDH1i","midostaurin":"Multi-TKI","gilteritinib":"FLT3i",
    "quizartinib":"FLT3i","glasdegib":"Hedgehog i","sonidegib":"Hedgehog i","vismodegib":"Hedgehog i",
    "olaparib":"PARPi","rucaparib":"PARPi","niraparib":"PARPi","talazoparib":"PARPi",
    "larotrectinib":"TRK i","selpercatinib":"RET i","pralsetinib":"RET i","capmatinib":"MET i",
    "tepotinib":"MET i","savolitinib":"MET i","pembrolizumab":"Anti-PD-1","nivolumab":"Anti-PD-1",
    "cemiplimab":"Anti-PD-1","dostarlimab":"Anti-PD-1","atezolizumab":"Anti-PD-L1","avelumab":"Anti-PD-L1",
    "durvalumab":"Anti-PD-L1","ipilimumab":"Anti-CTLA-4","tremelimumab":"Anti-CTLA-4",
    "blinatumomab":"BiTE (CD19/CD3)","mosunetuzumab":"BiTE (CD20/CD3)","epcoritamab":"BiTE (CD20/CD3)",
    "glofitamab":"BiTE (CD20/CD3)","tebentafusp":"BiTE (gp100/CD3)","tisagenlecleucel":"CAR-T (CD19)",
    "axicabtagene ciloleucel":"CAR-T (CD19)","brexucabtagene autoleucel":"CAR-T (CD19)",
    "lisocabtagene maraleucel":"CAR-T (CD19)","idecabtagene vicleucel":"CAR-T (BCMA)",
    "ciltacabtagene autoleucel":"CAR-T (BCMA)","tagraxofusp":"CD123 cytotoxin",
    "gemtuzumab ozogamicin":"ADC (CD33)","inotuzumab ozogamicin":"ADC (CD22)",
    "polatuzumab vedotin":"ADC (CD79b)","enfortumab vedotin":"ADC (Nectin-4)",
    "sacituzumab govitecan":"ADC (TROP2)","loncastuximab tesirine":"ADC (CD19)",
    "tisotumab vedotin":"ADC (TF)","mirvetuximab soravtansine":"ADC (FRalpha)",
    "belantamab mafodotin":"ADC (BCMA)","moxetumomab pasudotox":"Anti-CD22 immunotoxin",
    "asparginase":"Asparagine depletor","pegaspargase":"Asparagine depletor","calaspargase pegol":"Asparagine depletor",
    "arsenic trioxide":"Differentiation agent","tretinoin":"Retinoid (APL)","bexarotene":"Retinoid (CTCL)",
    "alitretinoin":"Retinoid","isotretinoin":"Retinoid (acne)","interferon alfa":"Immunomodulatory cytokine",
    "interferon beta":"Immunomodulatory cytokine","peginterferon alfa":"PEG-IFN",
    "aldesleukin":"IL-2","sipuleucel-t":"Cellular immunotherapy","talimogene laherparepvec":"Oncolytic virus",
    "filgrastim":"G-CSF","pegfilgrastim":"PEG-G-CSF","sargramostim":"GM-CSF","epoetin alfa":"EPO",
    "darbepoetin alfa":"EPO","romiplostim":"TPO-RA","eltrombopag":"TPO-RA","avatrombopag":"TPO-RA",
    "lusutrombopag":"TPO-RA","oprelvekin":"IL-11","palifermin":"KGF","amifostine":"Cytoprotective",
    "dexrazoxane":"Cardioprotective","mesna":"Uroprotective","leucovorin":"Folinic acid",
    "glucarpidase":"MTX rescue","caffeine":"Methylxanthine","sumatriptan":"Triptan","rizatriptan":"Triptan",
    "zolmitriptan":"Triptan","eletriptan":"Triptan","almotriptan":"Triptan","frovatriptan":"Triptan",
    "naratriptan":"Triptan","lasmiditan":"5-HT1F agonist","ubrogepant":"Gepant","rimegepant":"Gepant",
    "atogepant":"Gepant","erenumab":"Anti-CGRP R","fremanezumab":"Anti-CGRP","galcanezumab":"Anti-CGRP",
    "eptinezumab":"Anti-CGRP","acetaminophen":"Analgesic","phenazopyridine":"Urinary analgesic",
    "flavoxate":"Urinary antispasmodic","oxybutynin":"Anticholinergic (OAB)","tolterodine":"Anticholinergic (OAB)",
    "solifenacin":"Anticholinergic (OAB)","darifenacin":"Anticholinergic (OAB)","fesoterodine":"Anticholinergic (OAB)",
    "trospium":"Anticholinergic (OAB)","mirabegron":"Beta-3 agonist (OAB)","vibegron":"Beta-3 agonist (OAB)",
    "alprostadil":"PGE1","papaverine":"PDE inhibitor","phentolamine":"Alpha blocker",
    "phenylephrine":"Alpha-1 agonist","pseudoephedrine":"Sympathomimetic","oxymetazoline":"Alpha agonist (topical)",
    "xylometazoline":"Alpha agonist (topical)","naphazoline":"Alpha agonist (topical)",
    "tamsulosin":"Alpha-1A blocker (BPH)","alfuzosin":"Alpha blocker (BPH)","silodosin":"Alpha-1A blocker (BPH)",
    "doxazosin":"Alpha blocker","terazosin":"Alpha blocker","prazosin":"Alpha blocker",
    "phenoxybenzamine":"Irreversible alpha blocker","riociguat":"sGC stimulator","bosentan":"ERA (PAH)",
    "ambrisentan":"ERA (PAH)","macitentan":"ERA (PAH)","selexipag":"Prostacyclin agonist (PAH)",
    "epoprostenol":"Prostacyclin analog (PAH)","treprostinil":"Prostacyclin analog (PAH)",
    "iloprost":"Prostacyclin analog (PAH)","beraprost":"Prostacyclin analog (PAH)",
    "lithium":"Mood stabilizer","lithium carbonate":"Mood stabilizer","lithium citrate":"Mood stabilizer",
    "disulfiram":"ALDH inhibitor","acamprosate":"Alcohol dependence","naltrexone":"Opioid antagonist",
    "naloxone":"Opioid antagonist","nalmefene":"Opioid antagonist","methylnaltrexone":"Peripheral opioid antagonist",
    "naloxegol":"Peripheral opioid antagonist","naldemedine":"Peripheral opioid antagonist","alvimopan":"Peripheral opioid antagonist",
    "varenicline":"Partial nicotinic agonist","bupropion":"NDRI / Smoking cessation","nicotine":"Nicotinic agonist",
    "nicotine patch":"NRT","nicotine gum":"NRT","nicotine lozenge":"NRT","nicotine inhaler":"NRT",
    "nicotine nasal spray":"NRT","cytisine":"Partial nicotinic agonist",
}

KNOWN_DRUGS = set(DRUG_CLASSES.keys()) | set(ALIASES.keys())
KNOWN_DRUGS.update(["acetaminophen","insulin","lansoprazole","rabeprazole","famotidine",
    "diphenhydramine","loratadine","cetirizine","montelukast","albuterol","salbutamol",
    "fluticasone","budesonide","tiotropium","infliximab","adalimumab","tofacitinib",
    "cyclophosphamide","sucralfate","repaglinide","canagliflozin","ezetimibe","gemfibrozil",
    "caffeine","theophylline","sumatriptan","ranolazine","loperamide","mesalamine",
    "aprepitant","granisetron","ondansetron","metoclopramide","haloperidol","prednisone",
    "dexamethasone","furosemide","hydrochlorothiazide","spironolactone","levothyroxine",
    "methotrexate","tacrolimus","cyclosporine","colchicine","allopurinol","febuxostat"])

# =========================================================
# CLINICAL INTERACTION RULES
# =========================================================

CLASS_INTERACTIONS = {
    ("Anticoagulant (VKA)", "Antiplatelet (P2Y12)"): ("Major", "Additive antithrombotic → bleeding", "Avoid unless strong indication. Monitor INR + watch for bleeding."),
    ("Anticoagulant (VKA)", "Antiplatelet / NSAID"): ("Major", "Dual antithrombotic + gastric injury → high bleeding", "Avoid routine combo. Use PPI if absolutely needed."),
    ("Anticoagulant (VKA)", "NSAID"): ("Major", "Additive bleeding + gastric ulceration", "Contraindicated chronic use. Use acetaminophen."),
    ("Anticoagulant (VKA)", "COX-2 NSAID"): ("Moderate", "Reduced but present bleeding risk", "Lowest dose + PPI. Monitor INR."),
    ("DOAC (FXa)", "Antiplatelet (P2Y12)"): ("Major", "Additive antithrombotic → bleeding", "Avoid unless recent PCI. Monitor for bleeding."),
    ("DOAC (FXa)", "NSAID"): ("Major", "Additive bleeding risk", "Avoid chronic NSAIDs. Use acetaminophen."),
    ("DOAC (DTC)", "Antiplatelet (P2Y12)"): ("Major", "Additive antithrombotic", "Avoid unless strong indication."),
    ("DOAC (DTC)", "NSAID"): ("Major", "Additive bleeding", "Avoid chronic NSAIDs."),
    ("Antiplatelet (P2Y12)", "NSAID"): ("Moderate", "Additive bleeding + impaired platelets", "Avoid if possible. Lowest dose + PPI if needed."),
    ("Antiplatelet / NSAID", "NSAID"): ("Major", "Dual NSAID → GI ulceration, bleeding, renal injury", "Absolutely avoid. Use acetaminophen."),
    ("ACEi", "ARB"): ("Moderate", "Dual RAAS blockade → hyperK, AKI, hypotension", "Avoid routine combo. Monitor K+ and creatinine."),
    ("ACEi", "K-sparing diuretic"): ("Major", "Reduced aldosterone → severe hyperK", "Monitor K+ within 1 week. Avoid in CKD/diabetes."),
    ("ACEi", "K-sparing diuretic (aldosterone antagonist)"): ("Major", "Severe hyperK risk", "Monitor K+ closely."),
    ("ARB", "K-sparing diuretic"): ("Major", "Additive hyperK", "Monitor K+ within 1 week."),
    ("ARB", "K-sparing diuretic (aldosterone antagonist)"): ("Major", "Severe hyperK", "Monitor K+ closely."),
    ("Statin", "Fibrate"): ("Moderate", "Additive myotoxicity → rhabdo", "Avoid gemfibrozil. Fenofibrate preferred. Monitor CK."),
    ("Statin", "Azole antifungal"): ("Major", "CYP3A4 inhibition → statin toxicity", "Avoid simvastatin/lovastatin. Use pravastatin/fluvastatin."),
    ("SSRI", "MAOI"): ("Major", "Serotonin syndrome (potentially fatal)", "Contraindicated. Washout 2-5 weeks required."),
    ("SSRI", "MAO-Bi"): ("Moderate", "High-dose MAO-Bi risk serotonin syndrome", "Monitor for serotonin syndrome."),
    ("SSRI", "Opioid"): ("Moderate", "Potential serotonin syndrome (fentanyl, oxycodone)", "Monitor for serotonin syndrome."),
    ("SSRI", "NSAID"): ("Moderate", "Impaired platelet serotonin + gastric injury → GI bleed", "Use PPI prophylaxis. Monitor for bleeding."),
    ("SSRI", "Triptan"): ("Moderate", "Potential serotonin syndrome (rare)", "Monitor. Limit triptan frequency."),
    ("SNRI", "MAOI"): ("Major", "Serotonin syndrome", "Contraindicated. Washout required."),
    ("TCA", "MAOI"): ("Major", "Serotonin syndrome + hypertensive crisis", "Contraindicated."),
    ("Anticoagulant (VKA)", "Azole antifungal"): ("Major", "CYP inhibition → increased warfarin → bleeding", "Monitor INR closely. Dose reduction often needed."),
    ("Anticoagulant (VKA)", "Class III antiarrhythmic"): ("Major", "CYP2C9 inhibition + protein displacement → increased INR", "Reduce warfarin 30-50%. Monitor INR weekly."),
    ("Opioid", "BZD"): ("Major", "Additive CNS depression → respiratory depression, coma, death", "Avoid concurrent use. FDA black box warning."),
    ("PDE5i", "Nitrate"): ("Major", "Synergistic vasodilation → severe hypotension, shock, death", "ABSOLUTE CONTRAINDICATION. Separate 24-48h."),
    ("Cardiac glycoside", "Class III antiarrhythmic"): ("Major", "P-gp inhibition + reduced renal clearance → digoxin toxicity", "Reduce digoxin 50%. Monitor levels."),
    ("Cardiac glycoside", "Loop diuretic"): ("Moderate", "HypoK → increased digoxin toxicity", "Monitor K+ and digoxin levels."),
    ("Cardiac glycoside", "Thiazide diuretic"): ("Moderate", "HypoK → digoxin toxicity", "Monitor K+ and digoxin levels."),
    ("Mood stabilizer", "Loop diuretic"): ("Major", "Reduced lithium clearance → toxicity", "Monitor lithium levels. Dose reduction needed."),
    ("Mood stabilizer", "Thiazide diuretic"): ("Major", "Thiazides > loops for lithium toxicity risk", "Monitor lithium levels closely."),
    ("Antimetabolite / DMARD", "NSAID"): ("Major", "Reduced MTX renal clearance → severe toxicity", "Avoid high-dose MTX with NSAIDs."),
    ("Antimetabolite / DMARD", "Sulfonamide"): ("Major", "Both antifolate → bone marrow suppression", "Contraindicated."),
    ("Calcineurin inhibitor", "Azole antifungal"): ("Major", "CYP3A4 inhibition → nephrotoxicity", "Monitor trough levels. Dose reduction needed."),
    ("Methylxanthine", "Fluoroquinolone"): ("Major", "CYP1A2 inhibition → theophylline toxicity", "Monitor theophylline levels. Cipro > levo > moxi risk."),
    ("Antiplatelet (P2Y12)", "PPI"): ("Major", "CYP2C19 inhibition → reduced clopidogrel activation", "Avoid omeprazole/esomeprazole. Use pantoprazole or H2RA."),
    ("DHP-CCB", "Statin"): ("Moderate", "CYP3A4 inhibition → increased simvastatin/atorvastatin", "Limit simvastatin to 20mg with amlodipine."),
    ("Non-DHP CCB", "Statin"): ("Major", "Strong CYP3A4 inhibition → marked statin increase", "Avoid simvastatin/lovastatin. Use pravastatin."),
    ("Beta-1 blocker", "Non-DHP CCB"): ("Major", "Additive AV block → bradycardia, heart block", "Avoid combo. Monitor ECG if unavoidable."),
    ("Non-selective BB", "Non-DHP CCB"): ("Major", "Additive AV block + negative inotropy → HF, bradycardia", "Avoid combo."),
    ("Alpha/Beta blocker", "Non-DHP CCB"): ("Major", "Additive negative chronotropy/inotropy", "Avoid combo. Monitor closely."),
    ("NSAID", "ACEi"): ("Moderate", "Reduced renal prostaglandins → AKI, reduced BP effect", "Avoid chronic NSAIDs in HF/CKD. Monitor renal function."),
    ("NSAID", "ARB"): ("Moderate", "Reduced renal prostaglandins → AKI", "Avoid chronic NSAIDs in HF/CKD."),
    ("Corticosteroid", "NSAID"): ("Moderate", "Additive GI ulceration/bleeding", "Use PPI prophylaxis. Monitor for GI bleed."),
    ("Oxazolidinone", "SSRI"): ("Major", "Linezolid is weak MAOI → serotonin syndrome", "Avoid concurrent use. Hold SSRI if linezolid essential."),
    ("Oxazolidinone", "SNRI"): ("Major", "Serotonin syndrome", "Avoid concurrent use."),
    ("Oxazolidinone", "MAOI"): ("Major", "Dual MAO inhibition → hypertensive crisis", "Contraindicated."),
    ("Oxazolidinone", "TCA"): ("Major", "Serotonin syndrome", "Avoid concurrent use."),
    ("Rifamycin", "Anticoagulant (VKA)"): ("Major", "CYP induction → reduced warfarin → thrombosis", "Monitor INR frequently. Dose may need doubling."),
    ("Rifamycin", "DOAC (FXa)"): ("Major", "CYP3A4/P-gp induction → reduced DOAC → thrombosis", "Avoid combo. Use warfarin with INR monitoring."),
    ("Rifamycin", "DOAC (DTC)"): ("Major", "P-gp induction → reduced dabigatran", "Avoid combo."),
    ("Rifamycin", "Calcineurin inhibitor"): ("Major", "CYP3A4 induction → rejection", "Avoid rifampin with tacrolimus/cyclosporine."),
    ("Rifamycin", "Antiepileptic"): ("Moderate", "CYP induction → reduced antiepileptic levels", "Monitor antiepileptic levels."),
    ("Macrolide", "Statin"): ("Major", "CYP3A4 inhibition → statin toxicity", "Avoid simvastatin/lovastatin with erythromycin/clarithromycin."),
    ("Macrolide", "Anticoagulant (VKA)"): ("Moderate", "CYP inhibition + gut flora → increased INR", "Monitor INR closely."),
    ("Fluoroquinolone", "Anticoagulant (VKA)"): ("Moderate", "CYP inhibition + gut flora → increased INR", "Monitor INR."),
    ("Aminoglycoside", "Loop diuretic"): ("Major", "Additive ototoxicity + nephrotoxicity", "Avoid if possible. Monitor renal function + hearing."),
    ("Aminoglycoside", "Calcineurin inhibitor"): ("Major", "Additive nephrotoxicity", "Avoid if possible. Monitor renal function."),
    ("Glycopeptide", "Aminoglycoside"): ("Major", "Additive nephrotoxicity + ototoxicity", "Monitor renal function, drug levels, hearing."),
    ("Glycopeptide", "Loop diuretic"): ("Moderate", "Additive nephrotoxicity/ototoxicity", "Monitor renal function and vancomycin levels."),
    ("Nitroimidazole", "Anticoagulant (VKA)"): ("Major", "CYP2C9 inhibition + vit K suppression → marked INR increase", "Monitor INR closely. Dose reduction needed."),
    ("Sulfonamide", "Anticoagulant (VKA)"): ("Moderate", "Protein displacement + CYP inhibition → increased INR", "Monitor INR."),
    ("Sulfonamide", "ACEi"): ("Major", "TMP blocks ENaC + ACEi blocks aldosterone → severe hyperK", "Monitor K+ closely. Avoid in CKD/elderly."),
    ("Sulfonamide", "ARB"): ("Major", "TMP + ARB → severe hyperK", "Monitor K+ closely."),
    ("Non-selective BB", "SABA"): ("Moderate", "Beta-blockade antagonizes beta-2 bronchodilation → bronchospasm", "Avoid in asthma. Use cardioselective BB if needed."),
    ("Non-selective BB", "LABA"): ("Moderate", "Reduced bronchodilator efficacy", "Avoid in asthma. Monitor respiratory symptoms."),
    ("Corticosteroid", "Biguanide"): ("Moderate", "Steroids cause hyperglycemia → antagonize metformin", "Monitor glucose. May need temporary insulin."),
    ("Corticosteroid", "Sulfonylurea"): ("Moderate", "Steroids cause hyperglycemia", "Monitor glucose. May need increased sulfonylurea."),
    ("Corticosteroid", "Insulin"): ("Moderate", "Steroids → increased insulin requirements", "Monitor glucose closely. Increase insulin as needed."),
    ("Corticosteroid", "Cardiac glycoside"): ("Moderate", "HypoK increases digoxin toxicity", "Monitor K+ and digoxin levels."),
    ("Loop diuretic", "ACEi"): ("Minor", "Additive hypotension + first-dose effect", "Start ACEi low. Monitor BP and renal function."),
    ("Thiazide diuretic", "ACEi"): ("Minor", "Additive hypotension", "Monitor BP. Common effective combo."),
    ("Thiazide diuretic", "ARB"): ("Minor", "Additive hypotension", "Monitor BP. Common effective combo."),
    ("Loop diuretic", "Alpha blocker"): ("Moderate", "Additive hypotension (first-dose)", "Start alpha blocker at bedtime. Monitor BP."),
    ("K-sparing diuretic (aldosterone antagonist)", "NSAID"): ("Moderate", "NSAIDs reduce spironolactone efficacy", "Monitor diuretic response."),
    ("Carbonic anhydrase inhibitor", "Antiplatelet / NSAID"): ("Major", "High-dose salicylates + acetazolamide → severe metabolic acidosis", "Avoid high-dose aspirin with acetazolamide."),
    ("Thyroid hormone", "Anticoagulant (VKA)"): ("Moderate", "Increased catabolism of clotting factors → increased warfarin", "Monitor INR closely when adjusting levothyroxine."),
    ("Antithyroid", "Anticoagulant (VKA)"): ("Moderate", "Antithyroid drugs may increase warfarin", "Monitor INR."),
    ("Antiepileptic", "Carbapenem"): ("Major", "Carbapenems reduce valproate levels → breakthrough seizures", "Avoid combo. Use alternative antibiotic or antiepileptic."),
    ("Antiepileptic", "Macrolide"): ("Major", "Macrolides inhibit carbamazepine metabolism → toxicity", "Avoid erythromycin/clarithromycin. Use azithromycin."),
    ("Antiepileptic", "Azole antifungal"): ("Major", "Azoles inhibit carbamazepine metabolism", "Monitor carbamazepine levels. Dose reduction needed."),
    ("Antiepileptic", "Non-DHP CCB"): ("Moderate", "Verapamil/diltiazem increase carbamazepine", "Monitor carbamazepine levels."),
    ("Antiepileptic", "SSRI"): ("Moderate", "Fluoxetine/fluvoxamine increase carbamazepine", "Monitor carbamazepine levels."),
    ("Antiepileptic", "Antiepileptic"): ("Moderate", "Valproate inhibits lamotrigine metabolism → toxicity", "Reduce lamotrigine 50% when adding valproate."),
    ("Antiepileptic", "Antiepileptic (hydantoin)"): ("Moderate", "Valproate displaces phenytoin from protein + inhibits metabolism", "Monitor free phenytoin levels. Reduce phenytoin dose."),
    ("Antiepileptic", "Methylxanthine"): ("Major", "Phenytoin increases theophylline clearance → reduced efficacy", "Monitor theophylline levels."),
    ("Antiepileptic", "Anticoagulant (VKA)"): ("Major", "CYP induction → reduced warfarin", "Monitor INR frequently. Dose may need significant increase."),
    ("Antiepileptic", "DOAC (FXa)"): ("Major", "CYP3A4/P-gp induction → reduced DOAC", "Avoid combo. Use warfarin with INR monitoring."),
    ("Antiepileptic", "Calcineurin inhibitor"): ("Major", "CYP3A4 induction → reduced immunosuppressant → rejection", "Avoid carbamazepine/phenytoin with tacrolimus/cyclosporine."),
    ("Antiepileptic", "Statin"): ("Minor", "CYP induction → reduced statin efficacy", "Monitor lipids."),
    ("Typical antipsychotic", "Typical antipsychotic"): ("Major", "Additive QT prolongation + EPS + anticholinergic", "Avoid combo."),
    ("Typical antipsychotic", "Atypical antipsychotic"): ("Major", "Additive QT prolongation + EPS + metabolic", "Avoid if possible. Monitor ECG + metabolic params."),
    ("Typical antipsychotic", "TCA"): ("Major", "Additive QT prolongation + anticholinergic + sedation", "Avoid combo."),
    ("Typical antipsychotic", "Class III antiarrhythmic"): ("Major", "Additive QT prolongation → Torsades", "Avoid combo."),
    ("Typical antipsychotic", "Macrolide"): ("Major", "Additive QT prolongation", "Avoid erythromycin/clarithromycin."),
    ("Typical antipsychotic", "Fluoroquinolone"): ("Major", "Additive QT prolongation", "Avoid moxifloxacin."),
    ("Typical antipsychotic", "Azole antifungal"): ("Major", "Additive QT prolongation", "Avoid combo."),
    ("Typical antipsychotic", "5-HT3 antagonist"): ("Major", "Additive QT prolongation", "Avoid ondansetron with phenothiazines."),
    ("Atypical antipsychotic", "Atypical antipsychotic"): ("Major", "Additive metabolic + QT + EPS", "Avoid unless switching."),
    ("Atypical antipsychotic", "TCA"): ("Major", "Additive QT + sedation + anticholinergic", "Avoid combo."),
    ("Atypical antipsychotic", "Class III antiarrhythmic"): ("Major", "Additive QT → Torsades", "Avoid combo."),
    ("Atypical antipsychotic", "Macrolide"): ("Major", "Additive QT", "Avoid erythromycin/clarithromycin."),
    ("Atypical antipsychotic", "Fluoroquinolone"): ("Major", "Additive QT", "Avoid moxifloxacin."),
    ("Atypical antipsychotic", "Azole antifungal"): ("Major", "Additive QT", "Avoid combo."),
    ("Atypical antipsychotic", "5-HT3 antagonist"): ("Major", "Additive QT", "Avoid ondansetron with ziprasidone."),
    ("Atypical antipsychotic", "Antiepileptic"): ("Major", "Carbamazepine reduces clozapine; valproate increases clozapine", "Monitor clozapine levels closely."),
    ("Atypical antipsychotic", "SSRI"): ("Major", "Fluvoxamine/fluoxetine/paroxetine inhibit CYP → increased clozapine", "Avoid fluvoxamine with clozapine. Monitor levels with other SSRIs."),
    ("Typical antipsychotic", "Alpha blocker"): ("Major", "Additive hypotension + first-dose", "Monitor BP closely."),
    ("Atypical antipsychotic", "Alpha blocker"): ("Major", "Additive hypotension", "Monitor BP closely."),
    ("Typical antipsychotic", "Dopamine precursor"): ("Major", "Dopamine antagonism → worsening Parkinsonism", "Avoid typical antipsychotics in Parkinson's. Use clozapine/quetiapine."),
    ("Atypical antipsychotic", "Dopamine precursor"): ("Major", "Most atypicals antagonize levodopa", "Use clozapine or quetiapine if needed."),
    ("Typical antipsychotic", "Dopamine agonist"): ("Major", "Dopamine antagonism", "Avoid typicals. Use clozapine/quetiapine."),
    ("Atypical antipsychotic", "Dopamine agonist"): ("Major", "Most atypicals antagonize dopamine agonists", "Use clozapine or quetiapine."),
    ("Typical antipsychotic", "D2 antagonist / Prokinetic"): ("Major", "Additive EPS + hyperprolactinemia", "Avoid combo."),
    ("Atypical antipsychotic", "D2 antagonist / Prokinetic"): ("Major", "Additive EPS", "Avoid combo."),
    ("Typical antipsychotic", "Mood stabilizer"): ("Major", "Additive neurotoxicity + encephalopathy + EPS", "Monitor for neurotoxicity."),
    ("Atypical antipsychotic", "Mood stabilizer"): ("Moderate", "Additive neurotoxicity risk", "Monitor for neurotoxicity."),
    ("Typical antipsychotic", "Anticholinergic"): ("Moderate", "Additive anticholinergic → confusion, constipation, retention, tachycardia", "Avoid in elderly. Monitor anticholinergic toxicity."),
    ("Atypical antipsychotic", "Anticholinergic"): ("Moderate", "Additive anticholinergic", "Monitor for anticholinergic toxicity."),
    ("MAO-Bi", "SSRI"): ("Moderate", "High-dose MAO-Bi risk serotonin syndrome", "Monitor for serotonin syndrome."),
    ("MAO-Bi", "SNRI"): ("Moderate", "Serotonin syndrome risk", "Monitor."),
    ("MAO-Bi", "TCA"): ("Moderate", "Serotonin syndrome risk", "Monitor."),
    ("MAO-Bi", "Opioid"): ("Major", "Serotonin syndrome with tramadol", "Avoid tramadol with MAO-B inhibitors."),
    ("COMT inhibitor", "MAOI"): ("Major", "Additive catecholamine inhibition → hypertensive crisis", "Contraindicated."),
    ("COMT inhibitor", "MAO-Bi"): ("Moderate", "Theoretical hypertensive crisis", "Monitor BP closely."),
    ("Dopamine precursor", "MAOI"): ("Major", "MAO inhibition prevents dopamine breakdown → hypertensive crisis", "Contraindicated. Washout MAOIs before levodopa."),
    ("NMDA antagonist", "Anticholinergic"): ("Moderate", "Additive anticholinergic", "Monitor for confusion, urinary retention."),
    ("NMDA antagonist", "Methylxanthine"): ("Moderate", "Additive CNS effects", "Monitor for confusion."),
    ("AChE inhibitor", "Anticholinergic"): ("Major", "Pharmacodynamic antagonism", "Avoid combo in Alzheimer's."),
    ("AChE inhibitor", "Anticholinergic (OAB)"): ("Major", "Pharmacodynamic antagonism", "Avoid combo."),
    ("AChE inhibitor", "Typical antipsychotic"): ("Major", "Antipsychotics have anticholinergic properties", "Avoid antipsychotics with strong anticholinergic effects in dementia."),
    ("AChE inhibitor", "Atypical antipsychotic"): ("Moderate", "Some atypicals have anticholinergic effects", "Use quetiapine or clozapine (lowest ACB)."),
    ("NMDA antagonist", "NMDA antagonist"): ("Moderate", "Additive NMDA antagonism → confusion, dizziness", "Monitor CNS side effects."),
    ("Bisphosphonate", "NSAID"): ("Moderate", "Additive GI irritation + esophageal injury", "Use PPI. Ensure proper bisphosphonate administration."),
    ("Anti-RANKL", "Calcineurin inhibitor"): ("Moderate", "Additive immunosuppression → infection", "Monitor for infections."),
    ("PTH analog", "Bisphosphonate"): ("Major", "Bisphosphonates antagonize bone formation", "Do not use concurrently. Sequence: bisphosphonate first, then teriparatide."),
    ("Anti-sclerostin", "Bisphosphonate"): ("Major", "No added benefit + potential CV risk", "Do not use concurrently."),
    ("SERM", "Estrogen"): ("Major", "Pharmacodynamic antagonism", "Avoid concurrent use."),
    ("Aromatase inhibitor", "Estrogen"): ("Major", "Pharmacodynamic antagonism", "Avoid concurrent use."),
    ("Androgen", "Anticoagulant (VKA)"): ("Moderate", "Testosterone may increase warfarin", "Monitor INR closely."),
    ("Antiandrogen", "Anticoagulant (VKA)"): ("Major", "Bicalutamide increases warfarin", "Monitor INR. Reduce warfarin dose."),
    ("Antiandrogen", "Antiepileptic"): ("Minor", "Enzalutamide is CYP inducer → reduced antiepileptic", "Monitor antiepileptic levels."),
    ("Antiandrogen", "Calcineurin inhibitor"): ("Major", "Enzalutamide induces CYP3A4 → reduced immunosuppressant", "Avoid or monitor levels closely."),
    ("Antiandrogen", "Azole antifungal"): ("Moderate", "Mutual antagonism", "Monitor levels of both."),
    ("GnRH antagonist (oral)", "Azole antifungal"): ("Major", "CYP3A4 inhibition → increased levels", "Avoid strong CYP3A4 inhibitors."),
    ("GnRH antagonist (oral)", "Macrolide"): ("Major", "CYP3A4 inhibition", "Avoid erythromycin/clarithromycin."),
    ("GnRH antagonist (oral)", "Rifamycin"): ("Major", "CYP3A4 induction → reduced efficacy", "Avoid rifampin."),
    ("Dopamine agonist", "Typical antipsychotic"): ("Major", "Dopamine antagonism reduces efficacy", "Avoid typicals. Use clozapine/quetiapine."),
    ("Dopamine agonist", "Atypical antipsychotic"): ("Major", "Most antipsychotics increase prolactin", "Use quetiapine or clozapine (lowest prolactin)."),
    ("TKI (BCR-ABL)", "Anticoagulant (VKA)"): ("Major", "Imatinib increases warfarin", "Monitor INR. Reduce warfarin dose."),
    ("TKI (BCR-ABL)", "Statin"): ("Moderate", "Imatinib inhibits CYP3A4 → increased simvastatin/atorvastatin", "Use pravastatin or fluvastatin."),
    ("TKI (BCR-ABL)", "Antiepileptic"): ("Major", "Carbamazepine/phenytoin reduce imatinib", "Avoid or monitor imatinib levels."),
    ("TKI (BCR-ABL)", "Azole antifungal"): ("Major", "Additive CYP3A4 inhibition", "Monitor for toxicity."),
    ("EGFR TKI", "PPI"): ("Major", "Reduced gastric acidity → reduced gefitinib/erlotinib/afatinib absorption", "Avoid PPIs. Use H2RA with caution (separate 10-12h)."),
    ("EGFR TKI", "H2RA"): ("Moderate", "Reduced gastric acidity", "Separate doses by 10-12 hours."),
    ("EGFR TKI", "Antiepileptic"): ("Major", "CYP induction reduces EGFR TKI", "Avoid combo."),
    ("EGFR TKI", "Rifamycin"): ("Major", "CYP induction reduces EGFR TKI", "Avoid rifampin."),
    ("Anti-VEGF", "Anticoagulant (VKA)"): ("Major", "Increased bleeding (GI perforation, wound complications)", "Monitor INR. Hold bevacizumab before surgery."),
    ("Anti-VEGF", "DOAC (FXa)"): ("Major", "Increased bleeding", "Monitor for bleeding. Hold before surgery."),
    ("Anti-VEGF", "Antiplatelet (P2Y12)"): ("Major", "Increased bleeding", "Monitor for bleeding."),
    ("Multi-TKI", "Anticoagulant (VKA)"): ("Major", "Increased bleeding + INR fluctuation", "Monitor INR and bleeding."),
    ("Multi-TKI", "Antiplatelet (P2Y12)"): ("Major", "Increased bleeding", "Monitor for bleeding."),
    ("ALK TKI", "Azole antifungal"): ("Major", "CYP3A4 inhibition → increased ALK TKI", "Avoid strong CYP3A4 inhibitors."),
    ("ALK TKI", "Macrolide"): ("Major", "CYP3A4 inhibition", "Avoid erythromycin/clarithromycin."),
    ("ALK TKI", "Antiepileptic"): ("Major", "CYP induction reduces ALK TKI", "Avoid carbamazepine/phenytoin/phenobarbital."),
    ("ALK TKI", "Rifamycin"): ("Major", "CYP induction", "Avoid rifampin."),
    ("ALK TKI", "PPI"): ("Major", "Reduced gastric acidity → reduced alectinib/brigatinib", "Avoid PPIs with alectinib/brigatinib."),
    ("BRAFi", "PPI"): ("Minor", "Reduced gastric acidity → reduced dabrafenib", "Avoid PPIs with dabrafenib."),
    ("CDK4/6i", "Azole antifungal"): ("Major", "CYP3A4 inhibition", "Avoid strong CYP3A4 inhibitors."),
    ("CDK4/6i", "Macrolide"): ("Major", "CYP3A4 inhibition", "Avoid erythromycin/clarithromycin."),
    ("CDK4/6i", "Antiepileptic"): ("Major", "CYP induction reduces CDK4/6i", "Avoid strong CYP inducers."),
    ("CDK4/6i", "Rifamycin"): ("Major", "CYP induction", "Avoid rifampin."),
    ("CDK4/6i", "PPI"): ("Minor", "Reduced gastric acidity", "Avoid PPIs if possible."),
    ("BTKi", "Azole antifungal"): ("Major", "CYP3A4 inhibition", "Avoid strong CYP3A4 inhibitors."),
    ("BTKi", "Antiepileptic"): ("Major", "CYP induction reduces BTKi", "Avoid strong CYP inducers."),
    ("BTKi", "Rifamycin"): ("Major", "CYP induction", "Avoid rifampin."),
    ("BTKi", "PPI"): ("Minor", "Reduced gastric acidity → reduced acalabrutinib", "Avoid PPIs with acalabrutinib."),
    ("BCL-2i", "Azole antifungal"): ("Major", "CYP3A4 inhibition → TLS risk", "Avoid strong CYP3A4 inhibitors during venetoclax ramp-up."),
    ("BCL-2i", "Antiepileptic"): ("Major", "CYP induction reduces venetoclax", "Avoid strong CYP inducers."),
    ("BCL-2i", "Rifamycin"): ("Major", "CYP induction", "Avoid rifampin."),
    ("BCL-2i", "Anticoagulant (VKA)"): ("Major", "Venetoclax increases warfarin", "Monitor INR closely."),
    ("HDACi", "Anticoagulant (VKA)"): ("Major", "Increased bleeding + INR fluctuation", "Monitor INR closely."),
    ("Proteasome i", "Biguanide"): ("Moderate", "Bortezomib/carfilzomib may cause hyperglycemia", "Monitor glucose."),
    ("IMiD", "Anticoagulant (VKA)"): ("Major", "Increased thrombosis + bleeding risk", "Monitor INR. VTE prophylaxis often needed."),
    ("IMiD", "Estrogen"): ("Major", "Additive thrombosis risk", "Avoid combo. High VTE risk."),
    ("Anti-PD-1", "Anti-CTLA-4"): ("Major", "Additive irAEs", "Monitor for irAEs (colitis, hepatitis, pneumonitis, endocrinopathies)."),
    ("Anti-PD-1", "Calcineurin inhibitor"): ("Major", "Immunosuppressants reduce immunotherapy efficacy", "Avoid concurrent use."),
    ("Anti-PD-1", "Corticosteroid"): ("Moderate", "High-dose steroids reduce efficacy", "Use only for severe irAEs."),
    ("Anti-PD-L1", "Anti-CTLA-4"): ("Major", "Additive irAEs", "Monitor for irAEs."),
    ("Anti-PD-L1", "Calcineurin inhibitor"): ("Major", "Reduced immunotherapy efficacy", "Avoid concurrent use."),
    ("CAR-T (CD19)", "Calcineurin inhibitor"): ("Major", "Reduced CAR-T efficacy + infection", "Avoid if possible."),
    ("CAR-T (BCMA)", "Calcineurin inhibitor"): ("Major", "Reduced CAR-T efficacy + infection", "Avoid if possible."),
    ("Triptan", "SSRI"): ("Moderate", "Potential serotonin syndrome", "Monitor. Limit triptan frequency."),
    ("Triptan", "SNRI"): ("Moderate", "Potential serotonin syndrome", "Monitor."),
    ("Triptan", "MAOI"): ("Major", "Serotonin syndrome", "Avoid."),
    ("Gepant", "Azole antifungal"): ("Major", "CYP3A4 inhibition", "Avoid strong CYP3A4 inhibitors with ubrogepant/rimegepant."),
    ("Gepant", "Macrolide"): ("Major", "CYP3A4 inhibition", "Avoid erythromycin/clarithromycin."),
    ("Gepant", "Antiepileptic"): ("Major", "CYP induction reduces gepant", "Avoid strong CYP inducers."),
    ("Gepant", "Protease inhibitor"): ("Major", "CYP3A4 inhibition", "Avoid combo."),
    ("Anticholinergic (OAB)", "Anticholinergic"): ("Major", "Additive anticholinergic → confusion, constipation, retention, tachycardia", "Avoid combo. Monitor ACB toxicity."),
    ("Anticholinergic (OAB)", "Typical antipsychotic"): ("Major", "Additive anticholinergic", "Avoid in elderly."),
    ("Anticholinergic (OAB)", "Atypical antipsychotic"): ("Moderate", "Additive anticholinergic", "Monitor ACB toxicity."),
    ("Anticholinergic (OAB)", "TCA"): ("Major", "Additive anticholinergic", "Avoid combo."),
    ("Anticholinergic (OAB)", "AChE inhibitor"): ("Major", "Pharmacodynamic antagonism", "Avoid in Alzheimer's."),
    ("Alpha-1 agonist", "MAOI"): ("Major", "Hypertensive crisis", "Contraindicated."),
    ("Sympathomimetic", "MAOI"): ("Major", "Hypertensive crisis", "Contraindicated."),
    ("Alpha-1 agonist", "TCA"): ("Moderate", "TCAs potentiate pressor effects", "Monitor BP."),
    ("Sympathomimetic", "TCA"): ("Moderate", "TCAs potentiate pressor effects", "Monitor BP."),
    ("Alpha-1 agonist", "Non-selective BB"): ("Major", "Unopposed alpha → severe hypertension", "Avoid pseudoephedrine/phenylephrine with non-selective BB."),
    ("Sympathomimetic", "Non-selective BB"): ("Major", "Unopposed alpha → severe hypertension", "Avoid combo."),
    ("Alpha agonist (topical)", "MAOI"): ("Major", "Systemic absorption → hypertensive crisis", "Avoid combo."),
    ("Disulfiram", "Nitroimidazole"): ("Major", "Disulfiram-like reaction", "Avoid combo."),
    ("Disulfiram", "Cephalosporin"): ("Major", "Disulfiram-like reaction (MTT-side chain)", "Avoid MTT-side chain cephalosporins."),
    ("Opioid antagonist", "Opioid"): ("Major", "Naltrexone blocks opioid → precipitates withdrawal + blocks analgesia", "Ensure 7-10 day opioid-free before naltrexone."),
    ("Opioid antagonist", "Partial opioid agonist"): ("Major", "Naltrexone blocks buprenorphine → withdrawal", "Ensure opioid-free period."),
    ("Live vaccine", "Calcineurin inhibitor"): ("Major", "Immunosuppression → reduced efficacy + infection", "Contraindicated. Use killed vaccines only."),
    ("Live vaccine", "Anti-TNF"): ("Major", "Immunosuppression", "Contraindicated."),
    ("Live vaccine", "Anti-CD20"): ("Major", "Profound B-cell depletion → no response + infection", "Contraindicated. Wait 6 months post-rituximab."),
    ("Live vaccine", "JAK inhibitor"): ("Major", "Immunosuppression", "Contraindicated."),
    ("Live vaccine", "Corticosteroid"): ("Major", "High-dose steroids → immunosuppression", "Contraindicated during high-dose therapy."),
    ("Live vaccine", "Antimetabolite / DMARD"): ("Major", "Immunosuppression", "Contraindicated."),
    ("Live vaccine", "Purine analog"): ("Major", "Immunosuppression", "Contraindicated."),
    ("Live vaccine", "mTOR inhibitor"): ("Major", "Immunosuppression", "Contraindicated."),
    ("Live vaccine", "CAR-T (CD19)"): ("Major", "Profound immunosuppression", "Contraindicated."),
    ("Live vaccine", "CAR-T (BCMA)"): ("Major", "Profound immunosuppression", "Contraindicated."),
}

# Drug-specific overrides
DRUG_SPECIFIC = {
    ("warfarin", "aspirin"): ("Major", "Dual antithrombotic + gastric injury → very high bleeding", "Avoid routine combo. If needed (mechanical valve), use lowest aspirin (75-81mg) + PPI."),
    ("warfarin", "amiodarone"): ("Major", "CYP2C9 inhibition + displacement → increased INR", "Reduce warfarin 30-50%. Monitor INR weekly."),
    ("warfarin", "acetaminophen"): ("Moderate", "High-dose acetaminophen (>2g/day) may increase INR", "Limit acetaminophen to ≤2g/day. Monitor INR."),
    ("clopidogrel", "omeprazole"): ("Major", "CYP2C19 inhibition → reduced clopidogrel activation", "Avoid omeprazole/esomeprazole. Use pantoprazole or H2RA."),
    ("clopidogrel", "esomeprazole"): ("Major", "CYP2C19 inhibition → reduced clopidogrel activation", "Avoid. Use pantoprazole or H2RA."),
    ("clopidogrel", "fluoxetine"): ("Moderate", "CYP2C19 inhibition → reduced clopidogrel activation", "Avoid fluoxetine/fluvoxamine. Use sertraline/citalopram."),
    ("clopidogrel", "fluconazole"): ("Moderate", "CYP2C19 inhibition → reduced clopidogrel activation", "Monitor antiplatelet effect or use alternative antifungal."),
    ("simvastatin", "amlodipine"): ("Moderate", "CYP3A4 inhibition → increased simvastatin", "Limit simvastatin to 20mg/day with amlodipine."),
    ("simvastatin", "amiodarone"): ("Major", "CYP3A4 inhibition → simvastatin toxicity", "Avoid simvastatin >20mg or lovastatin >40mg with amiodarone."),
    ("metformin", "cimetidine"): ("Minor", "Cimetidine reduces metformin renal clearance", "Monitor for metformin toxicity if long-term cimetidine."),
    ("glyburide", "fluconazole"): ("Major", "CYP2C9 inhibition → severe hypoglycemia", "Monitor glucose closely. Reduce glyburide dose."),
    ("glyburide", "sulfamethoxazole"): ("Major", "Sulfonamides displace glyburide + inhibit metabolism → hypoglycemia", "Monitor glucose. Reduce glyburide."),
    ("repaglinide", "gemfibrozil"): ("Major", "CYP2C8 + OATP1B1 inhibition → markedly increased repaglinide → hypoglycemia", "Avoid gemfibrozil with repaglinide. Use fenofibrate."),
    ("repaglinide", "trimethoprim"): ("Moderate", "CYP2C8 inhibition → increased repaglinide", "Monitor glucose."),
    ("digoxin", "amiodarone"): ("Major", "P-gp inhibition + reduced renal clearance → digoxin toxicity", "Reduce digoxin 50%. Monitor levels."),
    ("digoxin", "verapamil"): ("Major", "Reduced digoxin renal clearance + displacement", "Reduce digoxin 30-50%. Monitor levels."),
    ("digoxin", "diltiazem"): ("Major", "Reduced digoxin renal clearance", "Reduce digoxin dose. Monitor levels."),
    ("digoxin", "spironolactone"): ("Moderate", "Reduced digoxin renal clearance + hyperK reduces binding", "Monitor digoxin levels and K+."),
    ("digoxin", "erythromycin"): ("Moderate", "Reduced gut flora metabolism → increased bioavailability", "Monitor digoxin levels."),
    ("digoxin", "clarithromycin"): ("Moderate", "Reduced gut flora metabolism → increased bioavailability", "Monitor digoxin levels."),
    ("theophylline", "ciprofloxacin"): ("Major", "CYP1A2 inhibition → theophylline toxicity", "Monitor theophylline levels. Cipro > levo > moxi."),
    ("carbamazepine", "erythromycin"): ("Major", "CYP3A4 inhibition → carbamazepine toxicity", "Avoid erythromycin/clarithromycin. Use azithromycin."),
    ("carbamazepine", "clarithromycin"): ("Major", "CYP3A4 inhibition → carbamazepine toxicity", "Avoid. Use azithromycin."),
    ("carbamazepine", "fluconazole"): ("Major", "CYP3A4 inhibition → carbamazepine toxicity", "Monitor carbamazepine levels. Dose reduction needed."),
    ("carbamazepine", "verapamil"): ("Moderate", "Verapamil increases carbamazepine", "Monitor carbamazepine levels."),
    ("carbamazepine", "diltiazem"): ("Moderate", "Diltiazem increases carbamazepine", "Monitor carbamazepine levels."),
    ("phenytoin", "amiodarone"): ("Major", "Complex: phenytoin may increase or decrease warfarin unpredictably", "Monitor INR very closely."),
    ("phenytoin", "cimetidine"): ("Minor", "Cimetidine increases phenytoin", "Avoid cimetidine. Use famotidine or PPI."),
    ("phenytoin", "fluconazole"): ("Major", "CYP2C9 inhibition → increased phenytoin", "Monitor phenytoin levels."),
    ("valproic acid", "aspirin"): ("Minor", "Aspirin displaces valproate from protein → increased free valproate", "Monitor valproate levels."),
    ("valproic acid", "carbapenem"): ("Major", "Carbapenems reduce valproate → breakthrough seizures", "Avoid combo. Use alternative antibiotic."),
    ("valproic acid", "erythromycin"): ("Moderate", "Erythromycin inhibits valproate metabolism", "Monitor valproate levels."),
    ("valproic acid", "lamotrigine"): ("Moderate", "Valproate inhibits lamotrigine metabolism → toxicity", "Reduce lamotrigine 50% when adding valproate."),
    ("lamotrigine", "valproic acid"): ("Moderate", "Valproate inhibits lamotrigine metabolism", "Reduce lamotrigine 50%."),
    ("lamotrigine", "carbamazepine"): ("Moderate", "Carbamazepine induces lamotrigine metabolism → reduced levels", "Monitor lamotrigine levels. Dose increase needed."),
    ("lamotrigine", "oxcarbazepine"): ("Moderate", "Oxcarbazepine induces lamotrigine metabolism", "Monitor lamotrigine levels."),
    ("topiramate", "acetazolamide"): ("Moderate", "Additive metabolic acidosis + kidney stone risk", "Monitor bicarbonate and hydration."),
    ("topiramate", "metformin"): ("Minor", "Topiramate may cause metabolic acidosis + reduce metformin clearance", "Monitor bicarbonate and renal function."),
    ("topiramate", "estrogen"): ("Major", "Topiramate >200mg/day induces estrogen metabolism → reduced contraceptive efficacy", "Use alternative contraception or reduce topiramate."),
    ("tramadol", "fluoxetine"): ("Major", "CYP2D6 inhibition → reduced morphine from codeine → reduced analgesia", "Avoid codeine with fluoxetine/paroxetine. Use morphine/oxycodone."),
    ("tramadol", "paroxetine"): ("Major", "CYP2D6 inhibition → reduced analgesia", "Avoid."),
    ("tramadol", "duloxetine"): ("Moderate", "CYP2D6 inhibition → reduced codeine efficacy", "Monitor pain control."),
    ("tramadol", "carbamazepine"): ("Moderate", "Carbamazepine reduces tramadol levels → reduced analgesia", "Monitor pain control."),
    ("fentanyl", "fluconazole"): ("Major", "CYP3A4 inhibition → increased fentanyl → respiratory depression", "Avoid combo. Monitor closely if unavoidable."),
    ("fentanyl", "verapamil"): ("Moderate", "CYP3A4 inhibition → increased fentanyl", "Monitor for respiratory depression."),
    ("fentanyl", "diltiazem"): ("Moderate", "CYP3A4 inhibition → increased fentanyl", "Monitor for respiratory depression."),
    ("methadone", "fluconazole"): ("Major", "CYP3A4/CYP2B6 inhibition → increased methadone → QT prolongation", "Monitor ECG and sedation."),
    ("methadone", "carbamazepine"): ("Major", "CYP induction reduces methadone → withdrawal", "Monitor for withdrawal. May need dose increase."),
    ("methadone", "phenytoin"): ("Major", "CYP induction reduces methadone", "Monitor for withdrawal."),
    ("buprenorphine", "fluconazole"): ("Moderate", "CYP3A4 inhibition → increased buprenorphine", "Monitor for sedation and respiratory depression."),
    ("buprenorphine", "naltrexone"): ("Major", "Naltrexone blocks buprenorphine → precipitates withdrawal", "Ensure opioid-free period before naltrexone."),
    ("tamoxifen", "fluoxetine"): ("Major", "CYP2D6 inhibition → reduced tamoxifen activation → reduced efficacy", "Avoid fluoxetine/paroxetine. Use citalopram/escitalopram/sertraline."),
    ("tamoxifen", "paroxetine"): ("Major", "CYP2D6 inhibition → reduced tamoxifen activation", "Avoid."),
    ("tamoxifen", "duloxetine"): ("Moderate", "CYP2D6 inhibition → reduced activation", "Monitor for reduced efficacy."),
    ("tamoxifen", "carbamazepine"): ("Major", "CYP2D6 induction → reduced tamoxifen efficacy", "Avoid."),
    ("tamoxifen", "phenytoin"): ("Major", "CYP2D6 induction → reduced efficacy", "Avoid."),
    ("tamoxifen", "rifampin"): ("Major", "CYP2D6 induction → reduced efficacy", "Avoid."),
    ("allopurinol", "azathioprine"): ("Major", "Xanthine oxidase inhibition → increased azathioprine toxicity", "Reduce azathioprine 50-75%. Monitor CBC/LFTs."),
    ("allopurinol", "mercaptopurine"): ("Major", "Xanthine oxidase inhibition → increased 6-MP toxicity", "Reduce 6-MP 50-75%."),
    ("allopurinol", "methotrexate"): ("Major", "Xanthine oxidase inhibition → increased MTX toxicity", "Avoid or reduce MTX significantly."),
    ("febuxostat", "azathioprine"): ("Major", "Same mechanism as allopurinol", "Reduce azathioprine 50-75%."),
    ("colchicine", "erythromycin"): ("Major", "CYP3A4/P-gp inhibition → colchicine toxicity (fatal rhabdo, BM suppression)", "Avoid combo."),
    ("colchicine", "clarithromycin"): ("Major", "CYP3A4/P-gp inhibition → colchicine toxicity", "Avoid combo."),
    ("colchicine", "verapamil"): ("Major", "P-gp/CYP3A4 inhibition → colchicine toxicity", "Avoid combo."),
    ("colchicine", "diltiazem"): ("Major", "P-gp/CYP3A4 inhibition → colchicine toxicity", "Avoid combo."),
    ("colchicine", "simvastatin"): ("Moderate", "Additive myopathy", "Use lowest doses. Monitor muscle pain."),
    ("colchicine", "atorvastatin"): ("Moderate", "Additive myopathy", "Monitor muscle pain."),
    ("methotrexate", "probenecid"): ("Major", "Reduced MTX renal clearance → toxicity", "Avoid or reduce MTX significantly."),
    ("methotrexate", "penicillin"): ("Moderate", "Penicillins may reduce MTX renal clearance", "Monitor MTX levels."),
    ("methotrexate", "trimethoprim"): ("Major", "Both antifolate → bone marrow suppression", "Contraindicated."),
    ("methotrexate", "omeprazole"): ("Minor", "Possible reduced MTX clearance with high-dose MTX", "Monitor MTX levels with high-dose therapy."),
    ("tacrolimus", "diltiazem"): ("Major", "CYP3A4 inhibition → increased tacrolimus → nephrotoxicity", "Monitor trough levels. Dose reduction needed."),
    ("tacrolimus", "verapamil"): ("Major", "CYP3A4 inhibition → increased tacrolimus", "Monitor levels. Dose reduction."),
    ("tacrolimus", "fluconazole"): ("Major", "CYP3A4 inhibition → increased tacrolimus", "Monitor levels. Dose reduction."),
    ("tacrolimus", "erythromycin"): ("Major", "CYP3A4 inhibition → increased tacrolimus", "Avoid erythromycin/clarithromycin."),
    ("tacrolimus", "clarithromycin"): ("Major", "CYP3A4 inhibition → increased tacrolimus", "Avoid."),
    ("tacrolimus", "rifampin"): ("Major", "CYP3A4 induction → reduced tacrolimus → rejection", "Avoid rifampin."),
    ("cyclosporine", "diltiazem"): ("Major", "CYP3A4 inhibition → increased cyclosporine", "Monitor levels. Dose reduction."),
    ("cyclosporine", "verapamil"): ("Major", "CYP3A4 inhibition → increased cyclosporine", "Monitor levels."),
    ("cyclosporine", "fluconazole"): ("Major", "CYP3A4 inhibition → increased cyclosporine", "Monitor levels."),
    ("cyclosporine", "simvastatin"): ("Major", "CYP3A4/P-gp inhibition → markedly increased statin", "Avoid simvastatin/lovastatin. Limit atorvastatin to 10mg."),
    ("cyclosporine", "digoxin"): ("Moderate", "Cyclosporine reduces digoxin clearance", "Monitor digoxin levels. Reduce digoxin."),
    ("cyclosporine", "NSAID"): ("Major", "Additive nephrotoxicity", "Avoid chronic NSAIDs. Monitor renal function."),
    ("sirolimus", "fluconazole"): ("Major", "CYP3A4 inhibition → increased sirolimus", "Monitor levels. Dose reduction."),
    ("sirolimus", "diltiazem"): ("Moderate", "CYP3A4 inhibition → increased sirolimus", "Monitor levels."),
    ("everolimus", "fluconazole"): ("Major", "CYP3A4 inhibition → increased everolimus", "Monitor levels."),
    ("imatinib", "warfarin"): ("Major", "Imatinib increases warfarin", "Monitor INR. Reduce warfarin."),
    ("imatinib", "simvastatin"): ("Moderate", "CYP3A4 inhibition → increased simvastatin", "Use pravastatin or fluvastatin."),
    ("imatinib", "carbamazepine"): ("Major", "Carbamazepine reduces imatinib", "Avoid or monitor imatinib levels."),
    ("imatinib", "phenytoin"): ("Major", "Phenytoin reduces imatinib", "Avoid or monitor."),
    ("imatinib", "rifampin"): ("Major", "Rifampin reduces imatinib", "Avoid."),
    ("gefitinib", "omeprazole"): ("Major", "Reduced gastric acidity → reduced gefitinib", "Avoid PPIs. Use H2RA with caution."),
    ("erlotinib", "omeprazole"): ("Major", "Reduced gastric acidity → reduced erlotinib", "Avoid PPIs."),
    ("afatinib", "omeprazole"): ("Major", "Reduced gastric acidity → reduced afatinib", "Avoid PPIs."),
    ("osimertinib", "omeprazole"): ("Minor", "Less pH-dependent than earlier EGFR TKIs", "Generally acceptable but monitor efficacy."),
    ("bevacizumab", "warfarin"): ("Major", "Increased bleeding (GI perforation, wound complications)", "Monitor INR. Hold before surgery."),
    ("bevacizumab", "rivaroxaban"): ("Major", "Increased bleeding", "Monitor for bleeding. Hold before surgery."),
    ("bevacizumab", "apixaban"): ("Major", "Increased bleeding", "Monitor for bleeding."),
    ("bevacizumab", "clopidogrel"): ("Major", "Increased bleeding", "Monitor for bleeding."),
    ("sunitinib", "warfarin"): ("Major", "Increased bleeding + INR fluctuation", "Monitor INR and bleeding."),
    ("sorafenib", "warfarin"): ("Major", "Increased bleeding", "Monitor INR and bleeding."),
    ("alectinib", "omeprazole"): ("Major", "Reduced gastric acidity → reduced alectinib", "Avoid PPIs."),
    ("brigatinib", "omeprazole"): ("Major", "Reduced gastric acidity → reduced brigatinib", "Avoid PPIs."),
    ("venetoclax", "fluconazole"): ("Major", "CYP3A4 inhibition → TLS risk", "Avoid strong CYP3A4 inhibitors during ramp-up."),
    ("venetoclax", "carbamazepine"): ("Major", "CYP induction reduces venetoclax", "Avoid."),
    ("venetoclax", "rifampin"): ("Major", "CYP induction", "Avoid."),
    ("venetoclax", "warfarin"): ("Major", "Venetoclax increases warfarin", "Monitor INR closely."),
    ("ibrutinib", "fluconazole"): ("Major", "CYP3A4 inhibition", "Avoid strong CYP3A4 inhibitors."),
    ("ibrutinib", "carbamazepine"): ("Major", "CYP induction reduces ibrutinib", "Avoid."),
    ("acalabrutinib", "omeprazole"): ("Minor", "Reduced gastric acidity → reduced acalabrutinib", "Avoid PPIs. Use H2RA with caution."),
    ("palbociclib", "fluconazole"): ("Major", "CYP3A4 inhibition", "Avoid strong CYP3A4 inhibitors."),
    ("ribociclib", "fluconazole"): ("Major", "CYP3A4 inhibition", "Avoid strong CYP3A4 inhibitors."),
    ("abemaciclib", "fluconazole"): ("Major", "CYP3A4 inhibition", "Avoid strong CYP3A4 inhibitors."),
    ("lenalidomide", "warfarin"): ("Major", "Increased thrombosis + bleeding", "Monitor INR. VTE prophylaxis often needed."),
    ("lenalidomide", "estrogen"): ("Major", "Additive thrombosis", "Avoid. High VTE risk."),
    ("thalidomide", "warfarin"): ("Major", "Increased thrombosis + bleeding", "Monitor INR. VTE prophylaxis."),
    ("pembrolizumab", "prednisone"): ("Moderate", "High-dose steroids reduce immunotherapy efficacy", "Use only for severe irAEs."),
    ("nivolumab", "prednisone"): ("Moderate", "High-dose steroids reduce efficacy", "Use only for severe irAEs."),
    ("nivolumab", "ipilimumab"): ("Major", "Additive irAEs", "Monitor for irAEs."),
    ("pembrolizumab", "ipilimumab"): ("Major", "Additive irAEs", "Monitor for irAEs."),
    ("naltrexone", "morphine"): ("Major", "Blocks morphine → precipitates withdrawal", "Ensure 7-10 day opioid-free."),
    ("naltrexone", "oxycodone"): ("Major", "Blocks oxycodone → withdrawal", "Ensure opioid-free period."),
    ("naltrexone", "fentanyl"): ("Major", "Blocks fentanyl → withdrawal", "Ensure opioid-free period."),
    ("naltrexone", "tramadol"): ("Major", "Blocks tramadol + may precipitate withdrawal", "Ensure opioid-free period."),
    ("naltrexone", "buprenorphine"): ("Major", "Blocks buprenorphine → withdrawal", "Ensure opioid-free period."),
    ("naltrexone", "methadone"): ("Major", "Blocks methadone → withdrawal", "Ensure opioid-free period."),
    ("naltrexone", "codeine"): ("Major", "Blocks codeine → withdrawal + no analgesia", "Ensure opioid-free period."),
    ("naltrexone", "hydrocodone"): ("Major", "Blocks hydrocodone → withdrawal", "Ensure opioid-free period."),
    ("naltrexone", "hydromorphone"): ("Major", "Blocks hydromorphone → withdrawal", "Ensure opioid-free period."),
    ("naltrexone", "meperidine"): ("Major", "Blocks meperidine → withdrawal", "Ensure opioid-free period."),
    ("naltrexone", "pentazocine"): ("Major", "Blocks pentazocine → withdrawal", "Ensure opioid-free period."),
    ("naltrexone", "nalbuphine"): ("Major", "Blocks nalbuphine → withdrawal", "Ensure opioid-free period."),
    ("naltrexone", "butorphanol"): ("Major", "Blocks butorphanol → withdrawal", "Ensure opioid-free period."),
}

# =========================================================
# EVIDENCE CATEGORIES
# =========================================================
EVIDENCE_CATEGORIES = [
    (["bleeding","hemorrhage","hemorrhagic"], "🩸 Bleeding / Hemorrhage"),
    (["qt prolongation","qt interval","torsade","torsades"], "❤️ QT / Cardiac Rhythm"),
    (["serotonin syndrome","serotonergic"], "🧠 Serotonergic Effect"),
    (["hypoglycemia","blood glucose","hyperglycemia"], "🩸 Glucose Effect"),
    (["hypotension","blood pressure","hypertension","hypertensive crisis"], "📉 Blood Pressure"),
    (["sedation","cns depression","respiratory depression","coma"], "😴 CNS Depression / Sedation"),
    (["cyp3a4","cyp2c9","cyp2c19","cyp2d6","cyp1a2"], "🧬 CYP Enzyme Interaction"),
    (["renal impairment","renal function","kidney","nephrotoxicity"], "🫘 Renal Function"),
    (["hepatic impairment","hepatic function","liver","hepatotoxicity"], "🫀 Hepatic Function"),
    (["seizure","convulsion","epilepsy"], "⚡ Seizure Risk"),
    (["arrhythmia","cardiac","bradycardia","heart block","av block"], "❤️ Cardiac Effect"),
    (["myopathy","rhabdomyolysis","muscle","ck elevation"], "💪 Myopathy / Rhabdomyolysis"),
    (["bone marrow suppression","neutropenia","thrombocytopenia","anemia"], "🩸 Hematologic Toxicity"),
    (["infection","immunosuppression","pneumonia","sepsis"], "🦠 Infection Risk"),
    (["tumor lysis syndrome","tls","hyperuricemia"], "⚠️ Tumor Lysis Syndrome"),
    (["hyperkalemia","hypokalemia","electrolyte"], "⚡ Electrolyte Disturbance"),
    (["acidosis","alkalosis","ph"], "🧪 Acid-Base Disturbance"),
    (["p-glycoprotein","p-gp","pgp","oatp"], "🚪 Transporter Interaction"),
    (["protein binding","displacement"], "🔗 Protein Binding Interaction"),
]

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def normalize_drug(name):
    name = name.strip().lower()
    return ALIASES.get(name, name)

def get_drug_class(name):
    normalized = normalize_drug(name)
    return DRUG_CLASSES.get(normalized, "Drug class not mapped")

@st.cache_data(ttl=3600)
def fetch_label(drug_name, search_type="generic"):
    drug_name = normalize_drug(drug_name)
    field = "openfda.brand_name" if search_type == "brand" else "openfda.generic_name"
    search_name = drug_name.upper()
    queries = [f'{field}:"{search_name}"', f"{field}:{search_name}"]
    for query in queries:
        try:
            response = requests.get(FDA_URL, params={"search": query, "limit": 1}, timeout=15)
            if response.status_code == 200:
                results = response.json().get("results", [])
                if results:
                    return results[0]
        except (requests.RequestException, ValueError):
            continue
    return None

def get_interaction_text(label):
    if not label:
        return ""
    interaction = label.get("drug_interactions")
    if isinstance(interaction, list):
        return " ".join(interaction)
    if isinstance(interaction, str):
        return interaction
    for key, value in label.items():
        if "drug_interaction" in key.lower():
            if isinstance(value, list):
                return " ".join(value)
            if isinstance(value, str):
                return value
    return ""

def classify_evidence(text):
    text_lower = text.lower()
    categories = []
    for keywords, category in EVIDENCE_CATEGORIES:
        if any(kw in text_lower for kw in keywords):
            categories.append(category)
    if not categories:
        categories.append("📄 FDA Interaction Evidence")
    return categories

def extract_drug_mentions(text, label):
    if not text:
        return []
    text_lower = text.lower()
    known = set(KNOWN_DRUGS)
    openfda = label.get("openfda", {})
    for field in ["brand_name", "generic_name", "substance_name"]:
        values = openfda.get(field, [])
        if isinstance(values, str):
            values = [values]
        for value in values:
            if isinstance(value, str):
                known.add(value.lower().strip())
    found = []
    seen = set()
    for drug in known:
        if len(drug) < 3:
            continue
        pattern = r"\b" + re.escape(drug) + r"\b"
        match = re.search(pattern, text_lower)
        if match and drug not in seen:
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 120)
            found.append({"drug": drug.title(), "context": text[start:end], "method": "dictionary"})
            seen.add(drug)
    return found

def check_two_drugs(drug_a, drug_b):
    norm_a = normalize_drug(drug_a)
    norm_b = normalize_drug(drug_b)
    label_a = fetch_label(norm_a, "generic")
    label_b = fetch_label(norm_b, "generic")
    if not label_a and not label_b:
        return {"found": False, "status": "error", "reason": "No FDA label found for either medicine."}
    evidence = []
    if label_a:
        text_a = get_interaction_text(label_a)
        if text_a:
            aliases_b = {norm_b, drug_b.lower()}
            for alias, canonical in ALIASES.items():
                if canonical == norm_b:
                    aliases_b.add(alias)
            for name in aliases_b:
                pattern = r"\b" + re.escape(name) + r"\b"
                match = re.search(pattern, text_a.lower())
                if match:
                    start = max(0, match.start() - 180)
                    end = min(len(text_a), match.end() + 300)
                    evidence.append({"source": drug_a, "context": text_a[start:end]})
                    break
    if label_b:
        text_b = get_interaction_text(label_b)
        if text_b:
            aliases_a = {norm_a, drug_a.lower()}
            for alias, canonical in ALIASES.items():
                if canonical == norm_a:
                    aliases_a.add(alias)
            for name in aliases_a:
                pattern = r"\b" + re.escape(name) + r"\b"
                match = re.search(pattern, text_b.lower())
                if match:
                    start = max(0, match.start() - 180)
                    end = min(len(text_b), match.end() + 300)
                    evidence.append({"source": drug_b, "context": text_b[start:end]})
                    break
    if evidence:
        return {"found": True, "status": "evidence", "evidence": evidence}
    return {"found": False, "status": "no_match", "reason": "No direct mention found in checked FDA interaction sections."}

def get_drug_profile(drug_name, search_type="generic"):
    label = fetch_label(drug_name, search_type)
    if not label:
        return {"ok": False, "error": f"No FDA label found for '{drug_name}'."}
    openfda = label.get("openfda", {})
    brand = openfda.get("brand_name", [])
    generic = openfda.get("generic_name", [])
    manufacturer_list = openfda.get("manufacturer_name", [])
    manufacturer = manufacturer_list[0] if manufacturer_list else "Unknown"
    text = get_interaction_text(label)
    mentions = extract_drug_mentions(text, label)
    return {
        "ok": True, "drug": drug_name, "brand": brand, "generic": generic,
        "manufacturer": manufacturer, "interaction_text": text, "interactions": mentions
    }

def check_class_interactions(drug_a, drug_b):
    """Check class-to-class and drug-specific interaction rules."""
    norm_a = normalize_drug(drug_a)
    norm_b = normalize_drug(drug_b)
    class_a = get_drug_class(drug_a)
    class_b = get_drug_class(drug_b)

    # Check drug-specific first (overrides class rules)
    key1 = (norm_a, norm_b)
    key2 = (norm_b, norm_a)
    if key1 in DRUG_SPECIFIC:
        sev, mech, rec = DRUG_SPECIFIC[key1]
        return {"found": True, "severity": sev, "mechanism": mech, "recommendation": rec, "type": "drug-specific"}
    if key2 in DRUG_SPECIFIC:
        sev, mech, rec = DRUG_SPECIFIC[key2]
        return {"found": True, "severity": sev, "mechanism": mech, "recommendation": rec, "type": "drug-specific"}

    # Check class-to-class
    class_pairs = [
        (class_a, class_b), (class_b, class_a)
    ]
    for ca, cb in class_pairs:
        key = (ca, cb)
        if key in CLASS_INTERACTIONS:
            sev, mech, rec = CLASS_INTERACTIONS[key]
            return {"found": True, "severity": sev, "mechanism": mech, "recommendation": rec, "type": "class-based"}

    return {"found": False}

def get_severity_color(severity):
    return {"Major": "#d32f2f", "Moderate": "#f57c00", "Minor": "#388e3c", "Theoretical": "#1976d2"}.get(severity, "#757575")

def get_severity_emoji(severity):
    return {"Major": "🔴", "Moderate": "🟠", "Minor": "🟢", "Theoretical": "🔵"}.get(severity, "⚪")

def get_risk_class(severity):
    return {"Major": "risk-major", "Moderate": "risk-moderate", "Minor": "risk-minor", "Theoretical": "risk-theoretical"}.get(severity, "risk-theoretical")

# =========================================================
# STREAMLIT UI
# =========================================================

st.markdown('<div class="main-header">💊 MedCheck AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Polypharmacy Intelligence Platform — FDA openFDA Evidence + Clinical Rule Engine</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="badge-row">'
    f'<span class="badge">🇺🇸 U.S. FDA openFDA</span>'
    f'<span class="badge">🧠 {len(CLASS_INTERACTIONS)}+ Class Rules</span>'
    f'<span class="badge">💊 {len(DRUG_CLASSES)}+ Drugs Mapped</span>'
    f'<span class="badge">{APP_VERSION}</span>'
    f'</div>', unsafe_allow_html=True
)

# Sidebar
with st.sidebar:
    st.header("⚙️ Patient Context")
    st.markdown("*These factors affect interaction risk interpretation*")
    age = st.number_input("Age", min_value=0, max_value=120, value=65)
    has_ckd = st.checkbox("Chronic Kidney Disease (CKD)", value=False)
    has_liver = st.checkbox("Hepatic Impairment", value=False)
    has_hf = st.checkbox("Heart Failure", value=False)
    has_diabetes = st.checkbox("Diabetes Mellitus", value=False)
    is_pregnant = st.checkbox("Pregnancy", value=False)
    is_elderly = age >= 65

    st.divider()
    st.header("📊 About")
    st.markdown("""
    - **Data Source:** U.S. FDA openFDA API
    - **Method:** Direct label search + pharmacy rule engine
    - **Coverage:** 500+ drugs mapped
    - **Cache:** 1 hour
    """)
    st.divider()
    st.markdown("""
    **⚠️ Disclaimer**  
    This tool is for **educational purposes only**.  
    It does not replace professional medical advice. Always consult a qualified healthcare provider.
    """)

# Patient risk modifiers
patient_risk_factors = []
if is_elderly:
    patient_risk_factors.append("👴 Elderly (≥65) — increased sensitivity to CNS depressants, bleeding, and renal toxicity")
if has_ckd:
    patient_risk_factors.append("🫘 CKD — reduced drug clearance, increased toxicity risk (especially metformin, NSAIDs, opioids)")
if has_liver:
    patient_risk_factors.append("🫀 Hepatic impairment — reduced metabolism, increased toxicity (statins, benzodiazepines, antiepileptics)")
if has_hf:
    patient_risk_factors.append("❤️ Heart Failure — avoid NSAIDs, thiazolidinediones; monitor digoxin, diuretics closely")
if has_diabetes:
    patient_risk_factors.append("🩸 Diabetes — monitor glucose with corticosteroids, beta-blockers, fluoroquinolones")
if is_pregnant:
    patient_risk_factors.append("🤰 Pregnancy — avoid ACEi, ARBs, statins, warfarin, retinoids; consult obstetrics")

# Tabs
tab1, tab2, tab3 = st.tabs(["🔍 Pairwise Check", "💊 Polypharmacy Analyzer", "📋 Drug Profile"])

# ---------------------------------------------------------
# TAB 1: PAIRWISE DRUG INTERACTION CHECKER
# ---------------------------------------------------------
with tab1:
    st.subheader("Check Interaction Between Two Medicines")

    col1, col2 = st.columns(2)
    with col1:
        drug_a = st.text_input("Medicine 1", placeholder="e.g. warfarin", key="drug_a")
    with col2:
        drug_b = st.text_input("Medicine 2", placeholder="e.g. aspirin", key="drug_b")

    check_btn = st.button("🔎 Analyze Interaction", use_container_width=True, type="primary")

    if check_btn:
        if not drug_a.strip() or not drug_b.strip():
            st.warning("Please enter both medicines.")
        elif normalize_drug(drug_a) == normalize_drug(drug_b):
            st.info("You entered the same medicine twice.")
        else:
            with st.spinner("Fetching FDA labels and analyzing..."):
                fda_result = check_two_drugs(drug_a, drug_b)
                class_result = check_class_interactions(drug_a, drug_b)

            norm_a = normalize_drug(drug_a)
            norm_b = normalize_drug(drug_b)
            class_a = get_drug_class(drug_a)
            class_b = get_drug_class(drug_b)

            st.markdown("### 🏷️ Medicines Checked")
            st.markdown(f'<span class="drug-chip">{drug_a.title()}</span> <code>{class_a}</code>  ↔  <span class="drug-chip">{drug_b.title()}</span> <code>{class_b}</code>', unsafe_allow_html=True)

            if patient_risk_factors:
                with st.expander("⚠️ Patient Risk Factors (may amplify interaction severity)", expanded=True):
                    for factor in patient_risk_factors:
                        st.markdown(f"- {factor}")

            if fda_result["status"] == "error":
                st.error(f"📡 FDA: {fda_result['reason']}")
            elif fda_result["status"] == "no_match":
                st.info("📡 FDA Label: No direct mention found in interaction sections.")
            elif fda_result["status"] == "evidence":
                st.success("📡 FDA Label: Direct interaction evidence found!")
                for idx, ev in enumerate(fda_result["evidence"], 1):
                    with st.expander(f"Evidence from {ev['source'].title()} ({idx})"):
                        cats = classify_evidence(ev["context"])
                        st.markdown(f"**Categories:** {', '.join(cats)}")
                        st.markdown(f'<div class="evidence-box">{ev["context"]}</div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 🧠 Clinical Rule Engine Analysis")

            if class_result["found"]:
                sev = class_result["severity"]
                color = get_severity_color(sev)
                emoji = get_severity_emoji(sev)
                risk_class = get_risk_class(sev)

                html_block = f'<div class="{risk_class}">'
                html_block += f'<h4 style="margin:0;color:{color}">{emoji} {sev} Severity Interaction</h4>'
                html_block += f'<p style="margin:4px 0 0 0"><strong>Mechanism:</strong> {class_result["mechanism"]}</p>'
                html_block += f'<p style="margin:4px 0 0 0"><strong>💡 Recommendation:</strong> {class_result["recommendation"]}</p>'
                html_block += f'<p style="margin:4px 0 0 0;font-size:0.8rem;color:#666">Source: {class_result["type"].title()}</p>'
                html_block += '</div>'
                st.markdown(html_block, unsafe_allow_html=True)

                if sev == "Major" and (is_elderly or has_ckd or has_liver or has_hf):
                    st.error("🚨 **CRITICAL:** Patient risk factors may significantly amplify this Major interaction. Consider alternative therapy or enhanced monitoring.")
                elif sev == "Moderate" and (is_elderly or has_ckd):
                    st.warning("⚠️ **ELEVATED RISK:** Elderly or CKD patients have reduced drug clearance. Consider dose adjustment or alternative therapy.")
            else:
                st.success("🟢 No known class-to-class or drug-specific interaction detected in the clinical rule engine.")
                st.info("Note: Absence of detected interaction does not guarantee safety. Both drugs may have incomplete mapping. Always verify with a pharmacist.")

            if fda_result["status"] == "evidence" and class_result["found"]:
                st.markdown("🟢 **Confidence: HIGH** — FDA label evidence + clinical rule engine agreement")
            elif fda_result["status"] == "evidence":
                st.markdown("🟡 **Confidence: MEDIUM** — FDA label evidence but no class rule match")
            elif class_result["found"]:
                st.markdown("🟡 **Confidence: MEDIUM** — Clinical rule engine match but no FDA label mention")
            else:
                st.markdown("🔴 **Confidence: LOW** — No FDA evidence or rule engine match found")

# ---------------------------------------------------------
# TAB 2: POLYPHARMACY ANALYZER
# ---------------------------------------------------------
with tab2:
    st.subheader("Analyze Multiple Medicines Simultaneously")
    st.markdown("Enter all medicines the patient is taking (one per line). The system will check every possible pair.")

    drug_list_input = st.text_area(
        "Medicine List",
        placeholder="warfarin\naspirin\nmetformin\natorvastatin",
        height=150,
        key="poly_list"
    )

    analyze_btn = st.button("🔬 Run Polypharmacy Analysis", use_container_width=True, type="primary")

    if analyze_btn:
        raw_drugs = [d.strip() for d in drug_list_input.split("\n") if d.strip()]
        drugs = list(dict.fromkeys([normalize_drug(d) for d in raw_drugs]))

        if len(drugs) < 2:
            st.warning("Please enter at least 2 different medicines.")
        else:
            with st.spinner(f"Analyzing {len(drugs)} medicines ({len(list(combinations(drugs, 2)))} pairs)..."):
                all_interactions = []
                fda_evidence_count = 0
                rule_count = 0
                major_count = 0
                moderate_count = 0
                minor_count = 0

                for d1, d2 in combinations(drugs, 2):
                    fda_res = check_two_drugs(d1, d2)
                    rule_res = check_class_interactions(d1, d2)

                    has_fda = fda_res["status"] == "evidence"
                    has_rule = rule_res["found"]

                    if has_fda:
                        fda_evidence_count += 1
                    if has_rule:
                        rule_count += 1
                        sev = rule_res["severity"]
                        if sev == "Major":
                            major_count += 1
                        elif sev == "Moderate":
                            moderate_count += 1
                        elif sev == "Minor":
                            minor_count += 1

                    if has_fda or has_rule:
                        all_interactions.append({
                            "drug_a": d1, "drug_b": d2,
                            "fda": has_fda, "rule": has_rule,
                            "severity": rule_res.get("severity", "N/A") if has_rule else "N/A",
                            "mechanism": rule_res.get("mechanism", "N/A") if has_rule else "N/A",
                            "recommendation": rule_res.get("recommendation", "N/A") if has_rule else "N/A",
                            "type": rule_res.get("type", "N/A") if has_rule else "N/A"
                        })

                # Overall polypharmacy risk score (weighted: Major=10, Moderate=4, Minor=1)
                raw_score = major_count * 10 + moderate_count * 4 + minor_count * 1
                if major_count >= 1:
                    risk_label, risk_color = ("HIGH RISK", "#d32f2f")
                elif moderate_count >= 2 or raw_score >= 8:
                    risk_label, risk_color = ("ELEVATED RISK", "#f57c00")
                elif rule_count >= 1:
                    risk_label, risk_color = ("LOW-MODERATE RISK", "#fbc02d")
                else:
                    risk_label, risk_color = ("LOW RISK", "#388e3c")

                rcol1, rcol2 = st.columns([1, 2])
                with rcol1:
                    st.markdown(
                        f'<div class="risk-score-wrap">'
                        f'<div style="font-size:0.8rem;color:#9aa5b1;text-transform:uppercase;letter-spacing:0.6px">Overall Polypharmacy Risk</div>'
                        f'<div style="font-size:2.4rem;font-weight:800;color:{risk_color};margin:6px 0">{risk_label}</div>'
                        f'<div style="font-size:0.78rem;color:#9aa5b1">Weighted score: {raw_score} · {len(drugs)} drugs · {len(list(combinations(drugs, 2)))} pairs checked</div>'
                        f'</div>', unsafe_allow_html=True
                    )
                with rcol2:
                    st.markdown("### 📊 Interaction Dashboard")
                    mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
                    with mcol1:
                        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#d32f2f">{major_count}</div><div class="metric-label">Major</div></div>', unsafe_allow_html=True)
                    with mcol2:
                        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#f57c00">{moderate_count}</div><div class="metric-label">Moderate</div></div>', unsafe_allow_html=True)
                    with mcol3:
                        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#388e3c">{minor_count}</div><div class="metric-label">Minor</div></div>', unsafe_allow_html=True)
                    with mcol4:
                        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#1976d2">{fda_evidence_count}</div><div class="metric-label">FDA Evidence</div></div>', unsafe_allow_html=True)
                    with mcol5:
                        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#757575">{len(all_interactions)}</div><div class="metric-label">Total Found</div></div>', unsafe_allow_html=True)

                st.markdown("")

                # Patient risk context
                if patient_risk_factors:
                    with st.expander("⚠️ Patient Risk Factors Applied", expanded=True):
                        for factor in patient_risk_factors:
                            st.markdown(f"- {factor}")

                # Drug list summary
                st.markdown("### 💊 Medicines Analyzed")
                chip_html = " ".join([f'<span class="drug-chip">{d.title()}</span> <code style="font-size:0.75rem">{get_drug_class(d)}</code>' for d in drugs])
                st.markdown(chip_html, unsafe_allow_html=True)

                if not all_interactions:
                    st.success("🎉 No interactions detected across all pairs! This is reassuring but not a guarantee of safety.")
                else:
                    st.markdown("---")
                    st.markdown("### 🚨 Detected Interactions")

                    # Sort by severity: Major first, then Moderate, then Minor
                    severity_order = {"Major": 0, "Moderate": 1, "Minor": 2, "N/A": 3}
                    all_interactions.sort(key=lambda x: severity_order.get(x["severity"], 3))

                    for inter in all_interactions:
                        sev = inter["severity"]
                        color = get_severity_color(sev)
                        emoji = get_severity_emoji(sev)
                        risk_class = get_risk_class(sev)

                        title = f"{emoji} {inter['drug_a'].title()} + {inter['drug_b'].title()}"
                        if sev != "N/A":
                            title += f" — {sev}"

                        with st.expander(title):
                            st.markdown(f'<div class="{risk_class}">', unsafe_allow_html=True)
                            if inter["rule"]:
                                st.markdown(f"**Mechanism:** {inter['mechanism']}")
                                st.markdown(f"**💡 Recommendation:** {inter['recommendation']}")
                                st.markdown(f"<span style='font-size:0.8rem;color:#666'>Source: {inter['type'].title()}</span>", unsafe_allow_html=True)
                            if inter["fda"]:
                                st.markdown("🟢 **FDA Label Evidence:** Direct mention found")
                            else:
                                st.markdown("🔴 **FDA Label Evidence:** No direct mention")
                            st.markdown('</div>', unsafe_allow_html=True)

                            # Patient-context warning
                            if sev == "Major" and (is_elderly or has_ckd or has_liver or has_hf):
                                st.error("🚨 Patient risk factors may significantly amplify this interaction.")
                            elif sev == "Moderate" and (is_elderly or has_ckd):
                                st.warning("⚠️ Elderly/CKD patients have reduced clearance — elevated risk.")

                # Summary report
                st.markdown("---")
                st.markdown("### 📋 Clinical Summary")
                if major_count > 0:
                    st.error(f"**{major_count} Major interaction(s)** detected. Review urgently with prescriber.")
                if moderate_count > 0:
                    st.warning(f"**{moderate_count} Moderate interaction(s)** detected. Monitor closely or consider alternatives.")
                if minor_count > 0:
                    st.info(f"**{minor_count} Minor interaction(s)** detected. Generally manageable with monitoring.")
                if not all_interactions:
                    st.success("No interactions detected. Continue routine monitoring.")

                # Downloadable CSV report
                if all_interactions:
                    csv_buffer = io.StringIO()
                    writer = csv.writer(csv_buffer)
                    writer.writerow(["Drug A", "Drug B", "Severity", "Mechanism", "Recommendation", "Source", "FDA Evidence"])
                    for inter in all_interactions:
                        writer.writerow([
                            inter["drug_a"].title(), inter["drug_b"].title(), inter["severity"],
                            inter["mechanism"], inter["recommendation"], inter["type"],
                            "Yes" if inter["fda"] else "No"
                        ])
                    st.download_button(
                        "⬇️ Download Report (CSV)",
                        data=csv_buffer.getvalue(),
                        file_name=f"medcheck_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

# ---------------------------------------------------------
# TAB 3: SINGLE DRUG PROFILE
# ---------------------------------------------------------
with tab3:
    st.subheader("Look Up a Single Medicine")
    drug_query = st.text_input("Enter medicine name", placeholder="e.g. metformin", key="profile_drug")
    profile_btn = st.button("📋 Get Profile", use_container_width=True, type="primary")

    if profile_btn:
        if not drug_query.strip():
            st.warning("Please enter a medicine name.")
        else:
            with st.spinner("Fetching FDA label..."):
                profile = get_drug_profile(drug_query)

            if not profile["ok"]:
                st.error(profile["error"])
            else:
                st.success(f"Profile: {profile['drug'].title()}")

                meta_col1, meta_col2 = st.columns(2)
                with meta_col1:
                    generic_names = profile['generic']
                    if isinstance(generic_names, list):
                        generic_names = ', '.join(generic_names[:3])
                    st.markdown(f"**Generic Name:** {generic_names}")
                    brand_names = profile['brand']
                    if isinstance(brand_names, list) and brand_names:
                        st.markdown(f"**Brand Name:** {', '.join(brand_names[:3])}")
                    else:
                        st.markdown(f"**Brand Name:** N/A")
                with meta_col2:
                    st.markdown(f"**Manufacturer:** {profile['manufacturer']}")
                    st.markdown(f"**Drug Class:** `{get_drug_class(profile['drug'])}`")

                if profile["interactions"]:
                    st.markdown(f"### ⚠️ Mentions {len(profile['interactions'])} interacting drug(s) in label")
                    for mention in profile["interactions"][:15]:
                        with st.expander(f"🔸 {mention['drug']}"):
                            st.write(mention["context"])
                else:
                    st.info("No specific interacting drugs identified in extracted interaction text.")

                # Show full interaction text if available
                if profile["interaction_text"]:
                    with st.expander("📄 Full FDA Interaction Text"):
                        st.markdown(f'<div class="evidence-box">{profile["interaction_text"][:3000]}</div>', unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption(
    f"💊 MedCheck AI {APP_VERSION}  ·  Data: U.S. FDA openFDA  ·  {len(DRUG_CLASSES)}+ drugs mapped, {len(CLASS_INTERACTIONS)}+ class-interaction rules  ·  "
    f"Evidence-Based Educational Prototype — **Not Medical Advice**  ·  Built for clinical education & research"
)
