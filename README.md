# CMMC Implementation Statement + Evidence Checklist Generator

MVP Version 1 for generating CMMC Level 2 implementation statements, responsible parties, evidence checklists, assessment notes, gaps, and export-ready artifacts.

## Stack

- Frontend: Next.js, React, Tailwind, shadcn-style UI primitives
- Backend: FastAPI
- Database: PostgreSQL-ready via SQLAlchemy
- AI: OpenAI API, with deterministic fallback when `OPENAI_API_KEY` is absent
- Vector DB: pgvector extension included in Docker/PostgreSQL setup
- Exports: `python-docx` and `reportlab`

## Quick Start

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL="sqlite:///./cmmc_mvp.db"
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

If `python`, `npm`, or `node` are not available on PATH, use the included Windows helper scripts from the project root:

```powershell
.\scripts\start-backend.ps1
.\scripts\start-frontend.ps1
```

The frontend helper includes `NODE_OPTIONS=--openssl-legacy-provider`, which is required for the currently installed Node 24 + Webpack combination.

Restart the FastAPI backend after changes to generator or checklist logic. The API now composes evidence checklists dynamically, so existing local databases do not need to be dropped just to pick up improved checklist wording.

## First Milestone

A user can enter their company profile, select `AC.L2-3.1.1`, and generate an editable implementation statement with responsible parties and evidence artifacts.

## Milestone 2

Policy & Procedure Generation is available from the control workspace:

- Select a CMMC control.
- Generate an editable policy.
- Generate an editable procedure.
- Edit document metadata: version, author, approver, approval date, review date, and status.
- Save each edit as a document version.
- Export policies and procedures to DOCX or PDF.

The backend includes the Milestone 2 tables: `policies`, `procedures`, `policy_templates`, `procedure_templates`, `document_versions`, and `document_approvals`.

## Environment

Backend:

```env
DATABASE_URL=postgresql+psycopg://cmmc:cmmc@localhost:5432/cmmc_mvp
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

Frontend:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Docker PostgreSQL

```powershell
docker compose up -d db
```
