# 1421 Foundation Research System

**Frontend:** React + Leaflet + Tailwind  
**Backend:** FastAPI + LangChain  
**Database:** PostgreSQL (PostGIS-ready)  
**Deploy:** Vercel (frontend) + Render (backend)

---

## Quick Start (Local)

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # Add your OPENAI_API_KEY
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend runs at `http://localhost:5173`.

---

## Deploy

### Backend → Render

1. Push to GitHub
2. On [render.com](https://render.com), create a **Web Service** pointing to your repo
3. Set build command: `pip install -r backend/requirements.txt`
4. Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add env vars: `OPENAI_API_KEY`, `DATABASE_URL` (Render Postgres), `FRONTEND_URL`

Or use the included `render.yaml` blueprint.

### Frontend → Vercel

1. On [vercel.com](https://vercel.com), import repo
2. Set root directory to `frontend`
3. Add env var: `VITE_API_URL=https://your-render-service.onrender.com`
4. Deploy

---

## Project Structure

```
├── backend/
│   ├── main.py              # FastAPI app + LangChain chat
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── render.yaml           # Render blueprint
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Layout + routing
│   │   ├── pages/Chat.tsx    # AI chat with streaming
│   │   ├── pages/VoyageMap.tsx # Leaflet interactive map
│   │   ├── pages/Feedback.tsx
│   │   └── lib/api.ts        # API client
│   ├── package.json
│   └── .env.example
└── README.md
```
