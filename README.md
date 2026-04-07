# 1421 Foundation AncientWave AI Project

**Student:** Ibrahim Mohammed  
**Project Supervisor:** Martin Walter  
**Client:** Ian Hudson, The 1421 Research, Education and Exploration Foundation  
**Degree:** BSc Computer Science (Hons), City St George's, University of London

## Live Demo

🌐 **Frontend (Vercel):** https://1421-foundation-ai-final-project.vercel.app

---

## GitHub Repository Structure
1421-Foundation-AI-Final-Project/
├── .gitignore
├── .python-version
├── LICENSE
├── Procfile
├── README.md
├── package.json
├── package-lock.json
├── requirements.txt
├── backend/
│ ├── main.py
│ ├── requirements.txt
│ └── .env.example
├── data/
│ └── vector_databases/
│ └── main_index/
│ └── faiss_index.bin
├── frontend/
│ ├── src/
│ │ ├── App.tsx
│ │ ├── pages/
│ │ │ ├── Chat.tsx
│ │ │ ├── DataMap.tsx
│ │ │ └── Feedback.tsx
│ │ └── lib/
│ │ └── api.ts
│ ├── index.html
│ ├── package.json
│ ├── package-lock.json
│ ├── vite.config.js
│ ├── postcss.config.js
│ ├── tailwind.config.js
│ └── .env.example
├── raw_csvs/ (source data files)
├── scraping_scripts/ (scripts used to collect data)
├── streamlit/ (prototyping dashboard)
└── test/ (test scripts including OpenAI key verification)

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Frontend | React, TypeScript, Tailwind CSS, Leaflet.js, Vite |
| Backend | FastAPI (Python), LangChain |
| Database | PostgreSQL with PostGIS |
| LLM | OpenAI GPT-4 (via API) |
| Deployment | Vercel (frontend), Koyeb (backend) |
| Version Control | Git + GitHub |

---

## Installation & Testing Instructions

### Prerequisites
- Node.js (v18+)
- Python (3.10+)
- OpenAI API key

### Run Locally

**1. Backend**

cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env
uvicorn main:app --reload
Backend runs at http://localhost:8000 | API docs: http://localhost:8000/docs

2. Frontend

cd frontend
npm install
cp .env.example .env
# Set VITE_API_URL=http://localhost:8000
npm run dev
Frontend runs at http://localhost:5173

Run Tests

cd test
python test_openai_connection.py   # Verifies API key works
Deployment
Service	Platform	Status
Frontend	Vercel	✅ Live
Backend	Koyeb	✅ Deployed

Reuse Summary (Appendix B)
Component	Written by me?	Notes
backend/main.py	✅ Yes	All original code
frontend/src/pages/Chat.tsx	✅ Yes	Original
frontend/src/pages/DataMap.tsx	✅ Yes	Original
frontend/src/lib/api.ts	✅ Yes	Original
scraping_scripts/	✅ Yes	Original scraping code
test/	✅ Yes	Original test scripts
data/vector_databases/	❌ No	Generated FAISS index (processed data)
raw_csvs/	❌ No	Client-provided source data
node_modules/, venv/	❌ No	Excluded via .gitignore
AI Tools Used: None. All code written by Ibrahim Mohammed.

Confidentiality & Access
Repository access: Public 

Live site: Publicly accessible (no sensitive data exposed)

Client data: Raw CSV files and FAISS index stored securely; not all data is public

Notes for Markers

.gitignore excludes node_modules/, venv/, __pycache__/, .env files

.env.example files are provided as templates

The streamlit/ folder contains an optional prototyping dashboard (not required for core functionality)

The raw_csvs/ folder contains client-provided source data

Contact
Ibrahim Mohammed: Ibrahim.mohammed.4@city.ac.uk




