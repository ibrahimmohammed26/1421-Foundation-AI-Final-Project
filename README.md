```markdown
# 1421 Foundation AncientWave AI Project

**Student:** Ibrahim Mohammed  
**Project Supervisor:** Martin Walter  
**Client:** Ian Hudson, The 1421 Research, Education and Exploration Foundation  
**Degree:** BSc Computer Science (Hons), City St George's, University of London

## Live Demo

🌐 **Frontend (Vercel):** https://1421-foundation-ai-final-project.vercel.app

## Repository Structure

```

1421-Foundation-AI-Final-Project/
├── backend/
│   ├── main.py              # FastAPI app + LangChain chat
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Layout + routing
│   │   ├── pages/
│   │   │   ├── Chat.tsx     # AI chat interface
│   │   │   ├── DataMap.tsx  # Leaflet interactive map
│   │   │   └── Feedback.tsx
│   │   └── lib/
│   │       └── api.ts       # API client
│   ├── package.json
│   └── .env.example
├── data/
│   └── vector_databases/
│       └── main_index/
│           └── faiss_index.bin
├── Procfile
├── requirements.txt          # Root-level dependencies
├── .python-version
└── README.md

```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Frontend | React, TypeScript, Tailwind CSS, Leaflet.js |
| Backend | FastAPI (Python), LangChain |
| Database | PostgreSQL with PostGIS |
| LLM | OpenAI GPT-4 (via API) |
| Deployment | Vercel (frontend), Koyeb (backend) |
| Version Control | Git + GitHub |

## Installation & Testing Instructions

### Prerequisites
- Node.js (v18+)
- Python (3.10+)
- OpenAI API key

### Run Locally

**1. Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env
uvicorn main:app --reload
```

Backend runs at http://localhost:8000 | API docs: http://localhost:8000/docs

2. Frontend

```bash
cd frontend
npm install
cp .env.example .env
# Set VITE_API_URL=http://localhost:8000
npm run dev
```

Frontend runs at http://localhost:5173

Test the System

1. Open chat interface → ask: "What evidence suggests Chinese contact with Panama?"
2. Open map → verify voyage routes and location markers appear
3. Test all 3 client UAT tasks (per PDD)

Deployment

Service Platform Status
Frontend Vercel ✅ Live
Backend Koyeb ✅ Deployed

Reuse Summary (Appendix B requirement)

Component Source Lines (approx) Written by me
Chat.tsx Original 320 ✅ Yes
DataMap.tsx Original 280 ✅ Yes
API client (api.ts) Original 150 ✅ Yes
FastAPI main.py Original with LangChain reference 420 ✅ Yes (LangChain used as library)
Tailwind config Generated via npm create vite 15 ❌ No (template)
Leaflet CSS CDN library N/A ❌ No (external library)

AI Tools Used: None. All code written by Ibrahim Mohammed.

Confidentiality & Access

· Repository access: Private (share with markers: @city.ac.uk email required)
· Live site: Publicly accessible (no sensitive data exposed)
· Client data: Stored in password-protected OneDrive; not included in public repo

Markers' Instructions

1. View live demo: https://1421-foundation-ai-final-project.vercel.app
2. Access source code: Grant @city.ac.uk read access to this GitHub repo
3. Test backend API: (deployed on Koyeb) contact student for URL
4. Contact for issues: Ibrahim.mohammed.4@city.ac.uk

Related Documents

· Project Definition Document (Appendix A of final report)
· Minutes of supervisory meetings (Appendix C)
· Client Information Sheet (Appendix B of PDD)
