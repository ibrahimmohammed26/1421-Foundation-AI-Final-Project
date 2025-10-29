# AncientWave AI: AI-Powered Historical Maritime Knowledge Base

## Project Overview
This system transforms 20 years of unstructured research on pre-Columbian maritime exploration into a queryable AI knowledge base with an interactive exploration map. Built for The 1421 Foundation.

## Technology Stack
- **Backend:** Python, FastAPI, PostgreSQL with PostGIS, LangChain
- **Frontend:** React.js, Leaflet.js, Mapbox
- **AI/ML:** OpenAI GPT-4 API / Llama 3, RAG implementation
- **Data Processing:** PyPDF2, pdfplumber, python-email

## Setup Instructions
1. Clone repository: `git clone [repository-url]`
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables (see `.env.example`)
4. Run database migrations: `alembic upgrade head`
5. Start backend: `uvicorn src.backend.main:app --reload`
6. Start frontend: `cd src/frontend && npm start`

## Project Status
- [x] Project Planning & PDD
- [ ] Data Processing Pipeline
- [ ] Backend API Development
- [ ] LLM Integration
- [ ] Frontend & Mapping Interface
- [ ] Testing & Deployment

## University Project
This is a final year BSc Computer Science project at City, University of London (IN3007). Supervisor: [Consultant Name], Client: Ian Hudson, The 1421 Foundation.
