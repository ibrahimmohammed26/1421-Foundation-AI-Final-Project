# 1421 Foundation – AncientWave AI Project

**Student:** Ibrahim Mohammed  
**Project Supervisor:** Edward Anstead  
**Client:** Ian Hudson, The 1421 Research, Education and Exploration Foundation  
**Degree:** BSc Computer Science (Hons), City St George’s, University of London  

---

## Live Demo

**Frontend (Vercel):** https://1421-foundation-ai-final-project.vercel.app

---

## Technology Stack

| Component | Technology |
|----------|------------|
| Frontend | React, TypeScript, Tailwind CSS, Leaflet.js, Vite |
| Backend | FastAPI (Python), LangChain |
| Database | PostgreSQL with PostGIS |
| LLM | OpenAI GPT-4 (via API) |
| Deployment | Vercel (frontend), Koyeb (backend) |
| Version Control | Git + GitHub |

---

## Installation and Local Development

### Prerequisites
- Node.js (v18+)  
- Python (3.10+)  
- OpenAI API key  

---

## 1. Backend Setup (FastAPI)

```bash
# Navigate to backend folder
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

Add your OpenAI key to `.env`:

```bash
OPENAI_API_KEY=your_api_key_here
```

Run the server:

```bash
uvicorn main:app --reload
```

Backend runs at:  
http://localhost:8000  
API documentation:  
http://localhost:8000/docs

---

## 2. Frontend Setup (React + Vite)

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env
```

Edit `.env`:

```bash
VITE_API_URL=http://localhost:8000
```

Start the development server:

```bash
npm run dev
```

Frontend runs at:  
http://localhost:5173

---

## Running Tests

```bash
cd test
python test_openai_connection.py
```

This verifies that the OpenAI API key is working.

---

## Deployment Overview

| Service | Platform | Status |
|---------|----------|--------|
| Frontend | Vercel | Live |
| Backend | Koyeb | Deployed |

---

## Reuse Summary (Appendix B)

| Component | Written by me? | Notes |
|-----------|----------------|-------|
| backend/main.py | Yes | Original code |
| frontend/src/pages/Chat.tsx | Yes | Original code |
| frontend/src/pages/DataMap.tsx | Yes | Original code |
| frontend/src/lib/api.ts | Yes | Original code |
| scraping_scripts/ | Yes | Original scraping code |
| test/ | Yes | Original test scripts |
| data/vector_databases/ | Yes | Generated via code |
| raw_csvs/ | No | Client-provided source data |
| node_modules/, venv/ | No | Standard ignored directories |

AI Tools Used: None. All code written by Ibrahim Mohammed.

---

## Confidentiality and Access

- Repository access: Public  
- Live site: Publicly accessible (no sensitive data exposed)  
- Client data: Raw CSV files and FAISS index stored securely 

---

## Notes for Markers

- `.gitignore` excludes `node_modules/`, `venv/`, `__pycache__/`, and `.env`  
- `.env.example` files are included as templates    
- `raw_csvs/` contains client-provided data  

---

## Contact

**Ibrahim Mohammed**  
Email: ibrahim.mohammed.4@city.ac.uk
