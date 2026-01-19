# ClientOps AI (Demo)

A practical **AI-for-business** demo: RAG chatbot + lead/support triage + CRM-style records + automation + admin dashboard.

## What runs today (Day 1 scaffold)
- FastAPI API service (health + placeholder routes)
- Streamlit UI service (placeholder pages)
- Postgres database
- Redis + RQ worker (background jobs scaffold)
- Sample SME docs to ingest later

## Quickstart (Docker)
1) Copy `.env.example` to `.env` and set values.
2) Run:
```bash
docker compose up --build
```

### URLs
- API: http://localhost:8000/docs
- UI:  http://localhost:8501

## Local dev (without Docker)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn apps.api.main:app --reload
streamlit run apps/ui/app.py
rq worker -c apps.worker.rq_settings
```

## Roadmap
See `docs/PLAN.md`.
