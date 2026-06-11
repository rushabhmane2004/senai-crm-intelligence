# Agentic CRM Intelligence Platform — Real-Time Email Operations System

> An AI-powered CRM email intelligence system that ingests customer emails, classifies risk, retrieves internal policy context with RAG, and produces auditable safe action plans.

---

## Submission Links

- **GitHub Repository**: https://github.com/rushabhmane2004/senai-crm-intelligence
- **Demo Video**: https://drive.google.com/file/d/1ZUtEcyfN7RQswU-pQlh7Kni7dreOhx4z/view?usp=drive_link

---

## 1. Project Overview

This platform is a production-grade CRM operations system that processes high-throughput support tickets, legal disputes, billing inquiries, and security incidents automatically.

### End-to-End Flow

```
Email Ingestion → Heuristic Filter → LLM Engine with RAG → Triage Agent → Database → UI Dashboard
```

| Stage | What happens |
|---|---|
| **Email Ingestion** | Customer emails are streamed via `stream_emails.py` and POSTed to `/api/ingest` |
| **Heuristic Filter** | Fast, deterministic pre-classification: category, urgency, priority, deduplication |
| **LLM Engine + RAG** | Structured LLM classification with entity extraction; ChromaDB retrieves grounding context from KB policies |
| **Triage Agent** | ReAct-style agent produces a safe action plan with step-by-step reasoning traces |
| **Database** | PostgreSQL stores emails, threads, contacts, actions, audit logs, RAG chunks, and web intelligence cache |
| **UI Dashboard** | React frontend displays stats, escalation queue, email inspector, reasoning traces, and analytics |

### Capabilities

- **RAG Retrieval** — Semantic search across 6 internal KB markdown policies via ChromaDB
- **Reasoning Traces** — Full step-by-step agent audit logs persisted to database for every processed email
- **Web Intelligence** — Offline-mode reputation intelligence (G2, Trustpilot, Capterra) with 6-hour DB cache
- **Email Simulation** — Streams 60+ realistic synthetic emails with deduplication
- **Analytics Dashboard** — Sentiment trend, category breakdown, risk summary, and escalation queue

---

## 2. Quick Start with Docker

Docker is the recommended and easiest way to run this project. No Python or Node.js setup required.

### Clone from GitHub

**macOS / Linux:**
```bash
git clone https://github.com/rushabhmane2004/senai-crm-intelligence.git
cd senai-crm-intelligence
cp .env.example .env
docker compose up --build
```

**Windows PowerShell:**
```powershell
git clone https://github.com/rushabhmane2004/senai-crm-intelligence.git
cd senai-crm-intelligence
copy .env.example .env
docker compose up --build
```

### Run from ZIP (if downloaded from GitHub)

**Windows PowerShell:**
```powershell
cd path\to\senai-crm-intelligence
copy .env.example .env
docker compose up --build
```

**macOS / Linux:**
```bash
cd path/to/senai-crm-intelligence
cp .env.example .env
docker compose up --build
```

---

## 3. Application URLs

Once `docker compose up --build` completes, all three services are available:

| Service | URL |
|---|---|
| **Frontend UI** | http://localhost:5173 |
| **Backend API** | http://localhost:8000 |
| **API Docs (Swagger UI)** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/health |

---

## 4. Environment Variables

A `.env.example` file is provided at the project root.

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/senai_crm
BACKEND_PORT=8000
```

**Steps:**
1. Copy `.env.example` to `.env`:
   - macOS/Linux: `cp .env.example .env`
   - Windows: `copy .env.example .env`
2. Do **not** commit `.env` — it is already listed in `.gitignore`.
3. Real secrets (e.g. `OPENAI_API_KEY`) should never be committed.

### Offline / Mock Mode

The system runs fully **offline by default**:
- `LLM_PROVIDER=mock` — deterministic structured output, no API key needed.
- If `OPENAI_API_KEY` is not set, the backend automatically falls back to `mock` mode.
- Web intelligence runs in `offline_mock` mode with realistic cached data.

You do **not** need an OpenAI key to evaluate the project.

---

## 5. Knowledge Base Seeding

Six internal policy documents are pre-loaded in the `kb/` directory:

| File | Content |
|---|---|
| `kb/pricing_policy.md` | Product pricing rules, multi-user tiers, and retention discounts |
| `kb/sla_policy.md` | Support tier response deadlines, SLA breaches, and service credits |
| `kb/refund_policy.md` | Refund eligibility, 14-day money-back guarantee, billing adjustments |
| `kb/api_docs.md` | Technical integration guidelines and developer token parameters |
| `kb/compliance_faq.md` | GDPR compliance, data deletion rights, and privacy guidelines |
| `kb/escalation_matrix.md` | Escalation routing policies and auto-messaging safety rules |

### Seed the ChromaDB Vector Store

Run this once to index the KB documents for RAG retrieval:

```bash
python scripts/seed_kb.py
```

> The `final_validation.py` script checks `knowledge_chunks` and auto-runs `seed_kb.py` if the collection is empty.

---

## 6. Email Simulation

The project includes a streaming email simulator that POSTs 60+ realistic synthetic emails to the backend:

```bash
python scripts/stream_emails.py --speed 10
```

- Reads from `data/email-data-advanced.json`
- Simulates real-time ingestion with configurable delay
- Demonstrates deduplication: re-running returns `duplicate_ignored` for already-processed IDs

---

## 7. Diagrams and Documentation

| Document | Description |
|---|---|
| [docs/architecture_diagram.png](./docs/architecture_diagram.png) | System Architecture Diagram — end-to-end component flow |
| [docs/er_diagram.png](./docs/er_diagram.png) | ER Diagram — entity relationships across all 7 database tables |
| [docs/database_schema.md](./docs/database_schema.md) | Full table-by-table schema with Mermaid ER diagram, JSON field contents, relationships, and data retention notes |
| [docs/api_reference.md](./docs/api_reference.md) | Comprehensive reference for all 14 API endpoints with request/response details and safety notes |
| [docs/openapi.json](./docs/openapi.json) | Machine-readable OpenAPI 3.x specification (14 paths, 11 components) |

To regenerate `docs/openapi.json` from a live FastAPI instance:
```bash
python scripts/export_openapi.py
```

---

## 8. Architecture Decisions and Trade-offs

- **Heuristic filter** is fast and deterministic but limited for complex contextual edge cases.
- **LLM engine** improves reasoning quality and entity extraction but may add cost and latency in production.
- **RAG** grounds responses using seeded KB documents, reducing hallucination risk; quality depends on chunking and embedding strategy.
- **Web intelligence** helps churn and escalation scenarios with public reputation context, but data is mocked/offline and can be stale or incomplete in a live environment.
- **Reasoning traces** are persisted per-email to improve explainability and simplify debugging; this adds a small storage overhead.
- **Conditional RAG** is only triggered for non-spam, non-internal emails — reducing unnecessary vector search overhead.

---

## 9. Local Development Setup

<details>
<summary>Expand for manual (non-Docker) setup instructions</summary>

### Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Seed KB (after backend starts)

```bash
python scripts/seed_kb.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Create `frontend/.env`:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Open http://localhost:5173 in your browser.

</details>

---

## 10. API Endpoints

| Method | Endpoint | Description |
|:---|:---|:---|
| **GET** | `/health` | Core system status health check |
| **POST** | `/api/ingest` | Normalizes and ingests email payloads |
| **GET** | `/api/status/{message_id}` | Returns classification metrics for an email |
| **GET** | `/api/actions/{message_id}` | Returns action plan, trace, and policy grounding details |
| **GET** | `/api/classification/{message_id}` | Returns structured LLM classification, entities, and prompt snapshots |
| **GET** | `/dashboard/stats` | Aggregates operational KPIs for the stats cards |
| **GET** | `/threads/{contact_email}` | Returns historical threads and contact profile metrics |
| **GET** | `/rag/search?q=...` | Executes semantic search query against KB policies |
| **POST** | `/rag/seed` | Seeds KB policies into ChromaDB database |
| **GET** | `/analytics/sentiment-trend` | Returns chronological sentiment trend, moving average, and deterioration flags |
| **GET** | `/analytics/category-breakdown` | Returns total email count and category breakdown statistics |
| **GET** | `/analytics/risk-summary` | Returns critical/escalated/spam counts and top at-risk customer senders |
| **GET** | `/intelligence/reputation?company=...` | Returns offline mock public reputation intelligence with 6-hour DB cache |
| **POST** | `/agent/dry-run/{message_id}` | Runs a planning-only dry-run simulation of the triage agent without side effects |

Full interactive docs: http://localhost:8000/docs

---

## 11. Safety Rules & Auto-Reply Decisions

The platform enforces strict safe-action rules to mitigate legal, security, and privacy risks:

- **Security / Ransomware**: Auto-reply blocked, escalated to security team.
- **Legal Threats**: Escalated to Legal immediately, automated threads frozen.
- **GDPR / Article 20**: Blocked from auto-reply; requires manual verification.
- **Spam**: Skips RAG pipeline entirely, flagged for archiving.
- **Safe Billing / Pricing**: Auto-reply allowed; response drafted using RAG-grounded KB context.

---

## 12. Critical Scenario Validation

| Message ID | Category | Urgency | Status | Safety Decision | Escalation |
|:---|:---|:---|:---|:---|:---|
| **msg_038** | Security | Critical | Escalated | Auto-reply blocked | security |
| **msg_052** | Compliance | Critical | Escalated | Auto-reply blocked | compliance |
| **msg_020** | Legal | Critical | Escalated | Auto-reply blocked | legal |
| **msg_060** | Support | Critical | Escalated | Auto-reply blocked | legal |
| **msg_041** | Billing | Medium | Processing | Auto-reply allowed | billing |
| **msg_031** | Spam | Low | Spam | Auto-reply blocked | none |

---

## 13. Known Limitations

- **Demo-focused**: Not production-hardened; designed for offline evaluation and reproducible demos.
- **Web intelligence is offline**: Reputation data is mocked; live scraping can be enabled behind the same service interface without changing the API contract.
- **RAG quality**: Depends on KB chunking and embedding quality; concise KB docs may produce only one or two chunks per document.
- **LLM output**: Should be reviewed by a human for high-impact customer-facing decisions.
- **Authentication/authorization**: Simplified for demo purposes; not implemented as production-grade auth.
- **No SMTP**: Email triggers are simulated via script; actual send/receive mail is out of scope.

---

## 14. Demo Walkthrough

Full end-to-end validation workflow:

```bash
# 1. Reset demo tables (preserves KB and intelligence cache)
python scripts/reset_demo_data.py

# 2. Full reset + seed + ingest 60 emails + validate 10 critical scenarios
python scripts/final_validation.py
```

`final_validation.py` automatically:
1. Resets demo tables
2. Seeds KB if empty
3. Ingests all 60 emails
4. Validates 10 critical scenarios and prints `FINAL VALIDATION PASSED` or `FAILED`

> This is the **recommended command before any screen recording or evaluator demo.**

---

## 15. Technical Stack

### Backend
- **FastAPI** — Web framework, routers, and CORS middleware
- **SQLAlchemy** — ORM and database schema
- **PostgreSQL** — Primary data store (SQLite fallback for local dev without Docker)
- **ChromaDB** — Local vector store for RAG
- **sentence-transformers (`all-MiniLM-L6-v2`)** — Dense embeddings for semantic search
- **Pydantic** — Strict response validation schemas

### Frontend
- **React** — Core UI components
- **Vite** — Dev server and asset compilation
- **Vanilla CSS** — Custom dark theme, responsive grid, interactive badges

### AI / RAG
- **ChromaDB vector store** — Local in-process vector DB
- **Sentence Transformer embeddings** — Dense semantic retrieval
- **Markdown Policy KB** — 6 documents ground LLM responses
- **Pluggable LLM provider** — `mock` (default) or `openai`

---

## 16. Final Deliverables Checklist

| Deliverable | Status |
|---|---|
| ✅ GitHub Repository | https://github.com/rushabhmane2004/senai-crm-intelligence |
| ✅ README | This document |
| ✅ Docker Setup | `docker compose up --build` |
| ✅ Architecture Diagram | `docs/architecture_diagram.png` |
| ✅ Knowledge Base Files | `kb/` — 6 markdown policy documents |
| ✅ ER Diagram | `docs/er_diagram.png` |
| ✅ Database Schema | `docs/database_schema.md` |
| ✅ OpenAPI Spec | `docs/openapi.json` (14 paths) |
| ✅ API Reference | `docs/api_reference.md` |
| ✅ Screen Recording | https://drive.google.com/file/d/1ZUtEcyfN7RQswU-pQlh7Kni7dreOhx4z/view?usp=drive_link |
| ✅ Email Simulation | `scripts/stream_emails.py` |
| ✅ RAG Debug View | `/rag/search` endpoint + UI trace panel |
| ✅ Analytics Dashboard | `/analytics/*` endpoints + React dashboard |

---

## 17. Assessment Audit Report

For a complete checklist of requirement coverage, scenario validations, and automatic disqualifier checks, see [FINAL_AUDIT.md](./FINAL_AUDIT.md).
