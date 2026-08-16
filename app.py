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
from datetime import datetime
from itertools import combinations
from collections import defaultdict

st.set_page_config(page_title="MedCheck AI V4", page_icon="💊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header {font-size:2.8rem;font-weight:800;background:linear-gradient(90deg,#1e88e5,#43a047);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
    .sub-header {font-size:1.1rem;color:#666;margin-top:-10px;margin-bottom:20px;}
    .risk-major {background:linear-gradient(135deg,#ffebee,#ffcdd2);padding:14px;border-radius:10px;border-left:6px solid #d32f2f;margin:8px 0;}
    .risk-moderate {background:linear-gradient(135deg,#fff8e1,#ffecb3);padding:14px;border-radius:10px;border-left:6px solid #f57c00;margin:8px 0;}
    .risk-minor {background:linear-gradient(135deg,#e8f5e9,#c8e6c9);padding:14px;border-radius:10px;border-left:6px solid #388e3c;margin:8px 0;}
    .risk-theoretical {background:linear-gradient(135deg,#e3f2fd,#bbdefb);padding:14px;border-radius:10px;border-left:6px solid #1976d2;margin:8px 0;}
    .drug-chip {display:inline-block;background:#e3f2fd;color:#1565c0;padding:6px 14px;border-radius:20px;margin:3px;font-weight:600;font-size:0.9rem;}
    .metric-card {text-align:center;padding:18px;background:white;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);}
    .metric-value {font-size:2rem;font-weight:700;}
    .metric-label {font-size:0.85rem;color:#666;text-transform:uppercase;letter-spacing:0.5px;}
    .evidence-box {background:#fafafa;padding:12px;border-radius:8px;font-family:'Courier New',monospace;font-size:0.85rem;border:1px solid #e0e0e0;}
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
    "immitrex":"sumatriptan","ranexa":"ranolazine","im
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
    (["myopathy","rhabdomyolysis","muscle","ck elevation"], "💪 Myopathy / R
