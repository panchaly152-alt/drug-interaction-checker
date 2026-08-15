💊 MedCheck AI

Intelligent Drug Interaction Analysis | Powered by U.S. FDA openFDA

MedCheck AI is a pharmacy-focused healthcare technology project built with Python and Streamlit. It retrieves publicly available drug-label information from the U.S. FDA openFDA API and analyzes interaction-related information to identify potential drug–drug interactions.

The project explores the intersection of Pharmaceutical Sciences, Clinical Information, Data, and Artificial Intelligence.

---

🚀 Key Features

- 🔍 Two-Drug Interaction Checker
- 📋 Single Drug Interaction Profile
- 💊 Generic & Brand Drug Search
- 📚 FDA Drug-Label Evidence
- 🧠 Drug-Interaction Text Analysis
- 🔎 Dictionary & Heuristic Drug Detection
- 🌐 Interactive Streamlit Web Application

---

🧠 How It Works

User enters two medicines
          ↓
     FDA openFDA API
          ↓
     Retrieve drug label
          ↓
 Extract interaction section
          ↓
   Analyze drug mentions
          ↓
Potential interaction identified
          ↓
 Display supporting FDA evidence

The application checks the interaction information from both drug labels, helping reduce the chance of missing information documented in only one direction.

---

🛠️ Technology Stack

- Python — Core application logic
- Streamlit — Web application interface
- Requests — API communication
- Regular Expressions — Text and pattern analysis
- U.S. FDA openFDA API — Drug-label data source

---

📊 Data Source

MedCheck AI uses publicly available information from the U.S. Food and Drug Administration's openFDA drug-label API.

The application retrieves the drug-interaction sections of FDA labels and uses them as the evidence layer for its analysis.

---

🔬 Technical Approach

The current prototype combines:

- Known-drug dictionary matching
- FDA drug-label metadata
- Drug-name pattern recognition
- Drug-like suffix heuristics
- Bidirectional interaction checking
- Context extraction from FDA labeling

The goal is to transform complex regulatory drug-label information into a simpler, accessible interface.

---

🧪 Example

Input

Drug 1: Warfarin
Drug 2: Aspirin

Output

⚠️ Potential Interaction Identified

The application retrieves relevant interaction information from FDA drug labeling and displays the supporting evidence.

Source: U.S. FDA Drug Label via openFDA

---

🔐 Safety & Responsible Use

«⚠️ Educational / research prototype only.»

MedCheck AI is not a medical device, diagnostic system, or substitute for professional medical advice.

A "no interaction found" result does not guarantee that a medication combination is safe. Medication decisions should always be evaluated and confirmed by an appropriately qualified healthcare professional.

---

🗺️ Development Roadmap

✅ V1 — Core Interaction Engine

- FDA openFDA integration
- Two-drug interaction checking
- Single-drug interaction profile
- Interaction text extraction
- Dictionary and heuristic detection
- Streamlit deployment

🚧 V2 — Evidence-Grounded AI

- AI-assisted explanation of retrieved evidence
- Structured interaction summaries
- Clear explanation of clinical significance
- Improved evidence presentation
- Stronger drug-name normalization

🔮 V3 — Advanced Analysis

- Multi-drug interaction checking
- Expanded evaluation dataset
- Automated testing
- Improved evidence retrieval
- Robust interaction classification
- Enhanced clinical-information interface

---

🎯 Project Vision

MedCheck AI aims to explore how pharmaceutical knowledge and modern technology can be combined to create transparent and accessible healthcare information tools.

Future development will focus on improving evidence grounding, transparency, testing, and usability, while maintaining clear boundaries between educational software and professional clinical decision-making.

---

👨‍💻 About the Project

MedCheck AI is a personal B.Pharm + Technology project exploring:

Pharmaceutical Sciences × Clinical Information × Data × AI × Software Development

---

📌 Project Status

Current Version: V1 — Functional Prototype

🚀 Actively under development

---

⚠️ Disclaimer

This project is intended solely for educational and research purposes.

It should not be used to diagnose, treat, prevent, or make medication decisions without consultation with a qualified healthcare professional.

Always verify medication information using authoritative sources.