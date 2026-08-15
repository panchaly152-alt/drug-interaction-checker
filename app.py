"""
Drug Interaction Checker
-------------------------
A Streamlit app that checks known interactions between two medicines
using the National Library of Medicine's RxNav API (RxNorm + DrugBank data).

Author: Yash Panchal
Data source: https://rxnav.nlm.nih.gov (NLM, free public API, no key required)

IMPORTANT: This is an educational/demo tool. It is not a substitute for
advice from a licensed pharmacist or physician.
"""

import streamlit as st
import requests

st.set_page_config(page_title="Drug Interaction Checker", page_icon="💊", layout="centered")

RXNAV_BASE = "https://rxnav.nlm.nih.gov/REST"


def get_rxcui(drug_name: str):
    """Look up the RxCUI (RxNorm Concept Unique Identifier) for a drug name."""
    try:
        resp = requests.get(f"{RXNAV_BASE}/rxcui.json", params={"name": drug_name}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        ids = data.get("idGroup", {}).get("rxnormId")
        return ids[0] if ids else None
    except requests.RequestException:
        return None


def get_interactions(rxcui_list):
    """Query RxNav's interaction list API for a list of RxCUIs."""
    try:
        rxcuis_param = "+".join(rxcui_list)
        resp = requests.get(
            f"{RXNAV_BASE}/interaction/list.json",
            params={"rxcuis": rxcuis_param},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


def parse_interactions(data):
    """Extract readable interaction descriptions from the RxNav response."""
    results = []
    if not data:
        return results
    for group in data.get("fullInteractionTypeGroup", []):
        source = group.get("sourceName", "Unknown source")
        for itype in group.get("fullInteractionType", []):
            for pair in itype.get("interactionPair", []):
                results.append({
                    "source": source,
                    "description": pair.get("description", "No description available."),
                    "severity": pair.get("severity", "N/A"),
                })
    return results


# ---------------- UI ----------------

st.title("💊 Drug Interaction Checker")
st.caption("Data from NLM RxNav (RxNorm / DrugBank) · Educational demo")

st.warning(
    "⚠️ Educational tool only — not a substitute for advice from a licensed "
    "pharmacist or physician. Always confirm with a healthcare professional "
    "before making medication decisions."
)

col1, col2 = st.columns(2)
with col1:
    drug1 = st.text_input("First medicine", placeholder="e.g. Warfarin")
with col2:
    drug2 = st.text_input("Second medicine", placeholder="e.g. Aspirin")

if st.button("Check Interaction", type="primary", use_container_width=True):
    if not drug1 or not drug2:
        st.error("Please enter both medicine names.")
    else:
        with st.spinner("Looking up drugs..."):
            rxcui1 = get_rxcui(drug1.strip())
            rxcui2 = get_rxcui(drug2.strip())

        if not rxcui1:
            st.error(f"Couldn't find '{drug1}' in RxNorm. Try the generic name or check spelling.")
        elif not rxcui2:
            st.error(f"Couldn't find '{drug2}' in RxNorm. Try the generic name or check spelling.")
        else:
            with st.spinner("Checking known interactions..."):
                data = get_interactions([rxcui1, rxcui2])
                interactions = parse_interactions(data)

            if interactions:
                st.subheader(f"Found {len(interactions)} known interaction record(s)")
                for i, inter in enumerate(interactions, 1):
                    sev = (inter["severity"] or "n/a").lower()
                    box = st.error if "high" in sev or "major" in sev else (
                        st.warning if "moderate" in sev else st.info
                    )
                    box(
                        f"**{i}. Severity: {inter['severity']}**\n\n"
                        f"{inter['description']}\n\n"
                        f"*Source: {inter['source']}*"
                    )
            else:
                st.success("No known interaction found in the RxNav database for this pair.")
                st.caption(
                    "Note: no listed interaction doesn't guarantee safety — "
                    "always confirm with a pharmacist."
                )

st.divider()
st.caption("Built by Yash Panchal · Data: NLM RxNav API (rxnav.nlm.nih.gov)")
