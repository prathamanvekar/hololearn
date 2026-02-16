# HoloLearn

HoloLearn is an AI-powered learning assistant that combines:

- conversational tutoring (chat + voice),
- document-grounded answers (RAG),
- bilingual responses (English/Hindi-first flow),
- quiz generation + grading,
- progress analytics dashboard,
- and a 3D holographic avatar UI.

The project is split into:

- `backend/` → FastAPI + SQLite + AI modules
- `frontend/` → React + Vite + Three.js interface

## Core Features

- Chat-based learning with context from uploaded documents
- Voice input transcription endpoint
- Document upload and processing for knowledge-base retrieval
- Bilingual response support (currently optimized for English/Hindi)
- Quiz generation, submission, review, and history
- Dashboard analytics (streak, performance trend, strengths/weaknesses)
- Exportable PDF summaries (Dashboard + Quiz results)
- 3D holographic avatar (`frontend/public/models/avatar.glb`)

## Tech Stack

- Frontend: React, Vite, Three.js (`@react-three/fiber`, `@react-three/drei`), Tailwind CSS
- Backend: FastAPI, SQLAlchemy, Uvicorn
- Database: SQLite
- AI/ML: HuggingFace models + Groq LLM integration
- Retrieval: Chroma-based vector storage

## Project Structure

```text
code/
├─ backend/
│  ├─ main.py
│  ├─ requirements.txt
│  ├─ routes/
│  ├─ modules/
│  └─ database/
├─ frontend/
│  ├─ package.json
│  ├─ src/
│  └─ public/models/avatar.glb
└─ README.md
```

## Prerequisites

- Python 3.10+ (3.11 recommended)
- Node.js 18+ (Node 20 recommended)
- npm 9+

## 1) Backend Setup (FastAPI)

From project root:

### Windows (PowerShell)

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS/Linux

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env` inside `backend/` (or set environment variables) for required keys, for example:

```env
GROQ_API_KEY=your_groq_api_key
```

Run backend:

```bash
uvicorn main:app --reload --port 8000
```

Backend URL: `http://127.0.0.1:8000`

## 2) Frontend Setup (React + Vite)

Open a second terminal, from project root:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

If needed, set API base URL in `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

## 3) Production Build

```bash
cd frontend
npm run build
npm run preview
```

## Notes for GitHub Push

- Root `.gitignore` is configured to exclude caches, virtual envs, build outputs, temp data, and local artifacts.
- `avatar.glb` is explicitly preserved and will remain tracked:
  - `frontend/public/models/avatar.glb`

## API Surface (High-Level)

- Chat: `/chat/send`
- Documents: `/documents/upload`, `/documents/list/{student_id}`
- Speech: `/speech/transcribe`
- Profile: `/profile/*`
- Quiz: `/quiz/generate`, `/quiz/submit`, `/quiz/history/{student_id}`
- Dashboard: `/dashboard/{student_id}`, `/dashboard/{student_id}/performance-chart`

## Troubleshooting

- If dashboard fails, ensure backend is running and student exists in DB.
- If CORS/API errors appear, verify `VITE_API_URL` points to backend.
- If model/API calls fail, check `GROQ_API_KEY` and backend logs.
