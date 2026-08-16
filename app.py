import streamlit as st
import requests, re
from itertools import combinations

st.set_page_config(page_title="MedCheck AI V4", page_icon="💊", layout="wide")
st.markdown("""<style>
.main-header{font-size:2.5rem;font-weight:800;background:linear-gradient(90deg,#1e88e5,#43a047);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.risk-major{background:linear-gradient(135deg,#ffebee,#ffcdd2);padding:12px;border-radius:10px;border-left:5px solid #d32f2f;margin:6px 0;}
.risk-moderate{background:linear-gradient(135deg,#fff8e1,#ffecb3);padding:12px;border-radius:10px;border-left:5px solid #f57c00;margin:6px 0;}
.risk-minor{background:linear-gradient(135deg,#e8f5e9,#c8e6c9);padding:12px;border-radius:10px;border-left:5px solid #388e3c;margin:6px 0;}
.drug-chip{display:inline-block;background:#e3f2fd;color:#1565c0;padding:5px 12px;border-radius:20px;margin:3px;font-weight:600;font-size:0.85rem;}
.metric-card{text-align:center;padding:14px;background:#fff;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,0.08);}
</style>""", unsafe_allow_html=True)

FDA_URL="https://api.fda.gov/drug/label.json"

ALIASES={"paracetamol":"acetaminophen","tylenol":"acetaminophen","advil":"ibuprofen","motrin":"ibuprofen","aleve":"naproxen","coumadin":"war
