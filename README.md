# Agentic CRM Intelligence Platform

A production-grade Agentic CRM Intelligence Platform and Real-Time Email Operations System designed for automated lead qualification, support routing, security alerts ingestion, and customer analytics.

---

## Phase 1 Overview: Backend Foundation & Ingestion

Phase 1 establishes the core backend architectures, database models, request validations, data normalization pipeline, contact thread linking, and automated priority heuristics. It includes a multi-threaded streaming simulation script mimicking real-time customer and client interactions.

### Completed Features

1. **FastAPI Web Framework**:
   * Clean, modular routes registration for ingestion, dashboards, statuses, and contact history.
   * CORS middleware initialized for cross-origin frontend requests.
   * Global exception interceptors mapping standard Pydantic validation errors and HTTP exceptions into a consistent error response envelope.
   * Root `/health` status endpoint.

2. **Database Schema & Models**:
   * **`contacts`**: Stores profiles, lifecycle status (`VIP`, `Blocked`, `Active`, `Churned`), account valuation, and metadata.
   * **`threads`**: Groups communications. Connects incoming messages logically.
   * **`emails`**: Real-time email ingestion rows. Connects to `threads.id`. Includes priority scores and sentiment parameters.
   * **`actions`**: Captures proposed AI replies, reasons, and approvals.
   * **`audit_log`**: Records audit tracks of internal processing, changes, and database modifications.

3. **Email Ingestion Engine (`POST /api/ingest`)**:
   * Normalizes incoming subject and body whitespace.
   * Gracefully falls back to defaults for empty subjects and bodies.
   * Automates message deduplication using `message_id` hashes to prevent message double-processing (`duplicate_ignored`).
   * Truncates message body payloads to `10,000` characters if they exceed limits, flagging the audit logs.
   * Assigns initial priority scores (`0` to `3`) using keyword heuristics:
     * **Critical (3)**: `ransomware`, `legal`, `cease and desist`, `p0`, `production down`, `breach`, `gdpr`.
     * **High (2)**: `urgent`, `refund`, `outage`, `escalation`, `public review`, `trustpilot`, `g2`.
     * **Medium (1)**: `bug`, `issue`, `deadline`, `failed`, `compliance`, `rfp`.
     * **Low (0)**: Default priority level.
   * Updates contact profiles (`last_contact_at`).

4. **Real-time Streaming Simulator (`scripts/stream_emails.py`)**:
   * Reads high-fidelity JSON files.
   * Submits payloads to the ingestion pipeline.
   * Supports speed configurations via command-line arguments.
   * Gracefully catches and formats operational API errors.

---

## Technical Stack
* **Backend**: Python 3.10+ (FastAPI)
* **Web Server**: Uvicorn
* **Database**: PostgreSQL 15
* **ORM**: SQLAlchemy
* **Validation**: Pydantic v2
* **Containerization**: Docker & Docker Compose

---

## Setup & Running Guide

### 1. Locally (with SQLite fallback)

For quick development iteration, the backend automatically falls back to a SQLite database when no external Postgres connection is provided.

1. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   source .venv/bin/activate    # macOS/Linux
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Configure Settings**:
   Create a local `.env` in the root workspace folder:
   ```env
   DATABASE_URL=sqlite:///./senai_crm.db
   BACKEND_PORT=8000
   ```

4. **Start the FastAPI Backend**:
   ```bash
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   * Swagger documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
   * Health endpoint is available at [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

5. **Run the Streaming Simulator**:
   ```bash
   # Stream at speed multiplier 1 (1 email per second)
   python scripts/stream_emails.py --speed 1
   ```

---

### 2. Using Docker Compose (with PostgreSQL)

To test a production-like environment with persistent PostgreSQL storage:

1. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. **Build and Launch Container Stack**:
   ```bash
   docker-compose up --build -d
   ```
   This spins up:
   * **`crm_postgres`**: Local PostgreSQL database mapped to port `5432` with a persistent volume named `pgdata`.
   * **`crm_backend`**: FastAPI backend mapped to port `8000`. It waits until PostgreSQL is fully healthy.

3. **Stream Emails into the Container Backend**:
   ```bash
   python scripts/stream_emails.py --speed 2
   ```

4. **Stop Container Stack**:
   ```bash
   docker-compose down -v
   ```

---

## API Documentation

### 1. Ingest Email (`POST /api/ingest`)

**Request Payload**:
```json
{
  "message_id": "msg_002",
  "sender": "bob.jones@enterprise.net",
  "subject": "URGENT: Production System Down",
  "body": "Our production server is not responding since 08:50 UTC. We need support immediately. This is a P0 incident.",
  "timestamp": "2023-10-01T09:15:00Z",
  "thread_id": "thread_bob_outage"
}
```

**Response (New Ingest)**:
```json
{
  "email_id": 2,
  "message_id": "msg_002",
  "thread_id": "thread_bob_outage",
  "status": "Received",
  "priority_score": 3
}
```

**Response (Duplicate Ignored)**:
```json
{
  "email_id": 2,
  "message_id": "msg_002",
  "thread_id": "thread_bob_outage",
  "status": "duplicate_ignored",
  "priority_score": 3
}
```

### 2. Contact Threads History (`GET /threads/{contact_email}`)

Returns the user profile, all group communication threads, chronological list of emails, and details of actions proposed or performed on their behalf.

**Response**:
```json
{
  "contact": {
    "id": 1,
    "email": "alice.smith@greenlight-npo.org",
    "name": null,
    "company": null,
    "status": "Active",
    "account_value": 0.0,
    "churn_risk_score": 0.0,
    "created_at": "2026-06-09T14:25:09",
    "last_contact_at": "2026-06-09T14:26:35.628932"
  },
  "threads": [
    {
      "id": 1,
      "thread_id": "thread_alice_pricing",
      "subject": "Question about pricing",
      "sender_email": "alice.smith@greenlight-npo.org",
      "first_seen_at": "2023-10-01T09:00:00",
      "last_updated_at": "2026-06-09T14:26:35.626932",
      "status": "Open",
      "assigned_to": null,
      "emails": [
        {
          "id": 1,
          "thread_id": 1,
          "message_id": "msg_001",
          "sender": "alice.smith@greenlight-npo.org",
          "subject": "Question about pricing",
          "body": "Hi, I was looking at your enterprise plan. Do you offer discounts for non-profits? We are a registered 501(c)(3) and work with underserved communities.",
          "timestamp": "2023-10-01T09:00:00",
          "priority_score": 0,
          "sentiment_score": null,
          "category": null,
          "urgency": null,
          "requires_human": null,
          "confidence": null,
          "raw_entities": null,
          "status": "Received",
          "created_at": "2026-06-09T14:25:09",
          "actions": []
        }
      ]
    }
  ]
}
```

### 3. Dashboard Stats (`GET /dashboard/stats`)

Returns counts of total emails, pending tasks (Received or Processing status), spam items, escalated threads, critical queries, contacts, and active conversations.

**Response**:
```json
{
  "total_emails": 60,
  "pending_emails": 60,
  "spam_emails": 0,
  "escalated_emails": 0,
  "critical_emails": 4,
  "total_contacts": 48,
  "total_threads": 47
}
```

### 4. Consistent Error Envelope

All API errors return a standard envelope schema:

**Example validation error (HTTP 422)**:
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid email payload",
  "details": {
    "body.sender": "value is not a valid email address: An email address must have an @-sign."
  }
}
```

**Example not found error (HTTP 404)**:
```json
{
  "error_code": "NOT_FOUND",
  "message": "Email with message_id 'msg_nonexistent' not found",
  "details": {}
}
```

---

## Phase 2: Heuristic Classification Engine

Phase 2 introduces a rule-based deterministic classifier executing synchronously during ingestion (`POST /api/ingest`). It checks messages for patterns and security/legal risks before any downstream LLM or agent workflows.

### Sequential Evaluation Rules
The classifier scans sender addresses and combined subjects/bodies in a strict priority order:
1. **Security**: Triggers `Security` category, `Critical` urgency, `Escalated` status, `requires_human` = true, and priority score `100`.
2. **Legal**: Triggers `Legal` category, `Critical` urgency, `Escalated` status, `requires_human` = true, and priority score `95`.
3. **GDPR / Compliance legal**: Triggers `Compliance` category, `Critical` urgency, `Escalated` status, `requires_human` = true, and priority score `95`.
4. **Internal**: Triggers `Internal` category, `Low` urgency, `Ignored` status, `requires_human` = false, and priority score `10`.
5. **Spam**: Triggers `Spam` category, `Low` urgency, `Spam` status, `requires_human` = false, and priority score `5`.
6. **P0 Outage**: Triggers `Complaint` category, `Critical` urgency, `Escalated` status, `requires_human` = true, and priority score `90`.
7. **Reputation / Churn**: Triggers `Complaint` category, `High` urgency, `Escalated` status, `requires_human` = true, and priority score `85`.
8. **Refund / Angry Complaint**: Triggers `Complaint` category, `High` urgency, `Escalated` status, `requires_human` = true, and priority score `80`.
9. **Bug Report**: Triggers `Bug Report` category, `Medium` urgency, `Processing` status, `requires_human` = true, and priority score `60`.
10. **Compliance**: Triggers `Compliance` category, `High` urgency, `Escalated` status, `requires_human` = true, and priority score `75`.
11. **Billing**: Triggers `Billing` category, `Medium` urgency, `Processing` status, `requires_human` = false, and priority score `50`.
12. **Pricing / Sales Inquiry**: Triggers `Inquiry` category, `Medium` urgency, `Processing` status, `requires_human` = false, and priority score `45`.
13. **Feature Request**: Triggers `Feature Request` category, `Low` urgency, `Processing` status, `requires_human` = false, and priority score `30`.
14. **Default (Other)**: Triggers `Other` category, `Low` urgency, `Processing` status, `requires_human` = false, and priority score `20`.

### Expected Verification Results

* **`msg_038`** (Ransomware threat) -> Category: `Security`, Urgency: `Critical`, Status: `Escalated`, Priority: `100`, Requires Human: `true`.
* **`msg_052`** (GDPR Article 20 request) -> Category: `Compliance`, Urgency: `Critical`, Status: `Escalated`, Priority: `95`, Requires Human: `true`.
* **`msg_020`** (Cease and desist legal notice) -> Category: `Legal`, Urgency: `Critical`, Status: `Escalated`, Priority: `95`, Requires Human: `true`.
* **`msg_060`** (SLA breach + legal escalation) -> Category: `Legal`, Urgency: `Critical`, Status: `Escalated`, Priority: `95`, Requires Human: `true` (specifically excludes matching the generic Security `breach` rule due to `SLA breach` check).
* **`msg_033`** (Public review / churn threat) -> Category: `Complaint`, Urgency: `High`, Status: `Escalated`, Priority: `85`, Requires Human: `true`.
* **`msg_003`**, **`msg_031`**, **`msg_039`** -> Category: `Spam`, Status: `Spam`, Priority: `5`.
* **`msg_017`**, **`msg_035`** -> Category: `Internal`, Status: `Ignored`, Priority: `10`.

---

## Phase 3: Production-Minded RAG Knowledge Pipeline

Phase 3 implements a local vector storage and semantic lookup pipeline using ChromaDB and local sentence embeddings (`sentence-transformers/all-MiniLM-L6-v2`) to anchor AI decisions and routing recommendations in internal policies.

### Business-Driven Grounding Architecture
> [!IMPORTANT]
> **RAG is used as a policy-grounding layer, not as a universal search step.**
> The system avoids retrieval for spam/internal/low-risk emails to reduce latency, control costs, and avoid adding irrelevant context. Retrieval is triggered only when the action depends on internal policy, compliance rules, contractual obligations, or escalation ownership.

* **Excluded from RAG**:
  * Category is `Spam` or `Internal`.
  * Category is `Other` with `Low` urgency.
* **Eligible for RAG**:
  * Category is `Legal`, `Compliance`, `Security`, `Billing`, `Complaint`, or `Inquiry`.
  * Category is `Bug Report` and text mentions API keywords (`api`, `v2`, `endpoint`, `403`, `rate limit`, `webhook`).
  * Any ticket with status `Escalated` (excluding Spam/Internal).

---

### Seeding and Managing the Knowledge Base

Policy files are stored under `/kb`:
1. `pricing_policy.md` - Subscriptions, seats, pro-rata, non-profit discounts, upgrade policies.
2. `sla_policy.md` - 99.9% uptime commitments, P0 RCA targets (24 hours), credits, escalation paths.
3. `refund_policy.md` - 14-day window, exceptions, reputation crisisCS escalation, chatbot misinformation safety rule.
4. `api_docs.md` - v1 deprecation, v2 endpoints, webhook specs, X-Workspace-ID header requirements.
5. `compliance_faq.md` - SOC 2 Type II, HIPAA BAA availability, GDPR Article 20 exports (30-day window).
6. `escalation_matrix.md` - specialized routing queues (Security, Legal, GDPR, VIP Churn) and safety guidelines (e.g., Never auto-reply to ransomware/extortion).

#### Seeding Command
Ensure dependencies are installed and run the seeding script:
```bash
python scripts/seed_kb.py
```
This script initializes tables, reads all files under `/kb`, splits them into semantic chunks of ~300-500 tokens, calculates embeddings, indexes them under Chroma (`backend/chroma_store`), and updates the database catalog table (`knowledge_chunks`) checking unique hashes to avoid duplicates.

---

### RAG Operations & API Endpoints

1. **Vector Search API (`GET /rag/search`)**:
   Query the knowledge base via the debug endpoint:
   ```bash
   GET /rag/search?q=refund public review escalation&top_k=3
   ```
2. **In-Flight Grounding during Ingestion**:
   When an incoming email qualifies for RAG, a targeted query is constructed and the top 3 policy citations are embedded inside the `raw_entities` column:
   ```json
   "rag_used": true,
   "rag_query": "refund policy exception service failure retention playbook",
   "rag_context": [
     {
       "source_doc": "refund_policy.md",
       "policy_ref": "refund_policy.md#chunk-0",
       "similarity_score": 0.478,
       "chunk_preview": "# Refund and Customer Retention Policy..."
     }
   ]
   ```
   *If the RAG service fails (due to model loading or vector store read issues), the email ingestion does not block; it registers the failure in an `AuditLog` entry, appends `rag_error` in `raw_entities`, and successfully finishes ingestion.*

---

### Verification and Test Queries

Run verification queries using the provided helper:
```bash
python scripts/verify_rag.py
```

Expected search results:
1. **Query**: `refund public review escalation`
   * Returns: `refund_policy.md`, `escalation_matrix.md`
2. **Query**: `GDPR Article 20 data portability 30-day statutory window`
   * Returns: `compliance_faq.md`, `escalation_matrix.md`
3. **Query**: `SLA breach RCA 24 hours downtime credit`
   * Returns: `sla_policy.md`, `escalation_matrix.md` (or top policy chunks)
4. **Query**: `API v2 403 X-Workspace-ID`
   * Returns: `api_docs.md`
5. **Query**: `nonprofit discount pro-rata billing`
   * Returns: `pricing_policy.md`
6. **Query**: `ransomware never auto-reply escalation`
   * Returns: `escalation_matrix.md`

---

## Phase 4: Agent Reasoning Trace + Safe Action Planner

Phase 4 implements an auditable triage agent (`triage-agent-v1`) that evaluates heuristic classifications and policy-grounded RAG context to formulate CRM action plans, reasoning logs, safety levels, and next steps.

### Safety Rules & Decision Logic
1. **Spam & Internal**: Automatically blocked from auto-replies, marked as safe/blocked, and suppressed to save system resources.
2. **Security & Ransomware Extortion**: Safety level: `blocked`. Suppresses all auto-replies and routes immediately to the **Security Incident Response Team** as dictated by the escalation matrix rules. Draft reply is `null`.
3. **Legal Threats (Cease & Desist)**: Safety level: `blocked`. Suppresses auto-replies and routes directly to the **Legal Team**. Draft reply is `null`.
4. **GDPR / Article 20 (Privacy)**: Safety level: `restricted`. Routes directly to the **Compliance and Legal Operations Team** tracking the statutory 30-day response window. Auto-replies are blocked (`null` draft).
5. **SLA Outages & P0 Incidents**: Safety level: `restricted`. Escalates immediately to the **Support Lead and Engineering Manager** to trigger Root Cause Analysis (RCA) within 24 hours. Auto-reply is disallowed for billing/liability statements.
6. **Public Review Threats / Churn Risk**: Safety level: `restricted`. Escalates to the **Customer Success Lead and Account Executive** to deploy the Customer Retention Playbook. Direct refund commitments are disallowed.
7. **Billing & Customer Inquiries**: Safety level: `safe`. Automatically drafts a professional response grounded in the retrieved `pricing_policy.md` or `api_docs.md` context, allowing automated auto-replies.

### API Endpoints
1. **GET Agent Action Plan (`GET /api/actions/{message_id}`)**:
   Fetches the triage decision, recommended action, safety level, audit-friendly reasoning trace, policy sources used, and drafted reply (if applicable).
   ```bash
   GET /api/actions/msg_038
   ```
2. **GET Status (`GET /api/status/{message_id}`)**:
   Includes compact agent fields: `agent_decision`, `auto_reply_allowed`, `requires_human_approval`, `escalation_team`, and `safety_level`.



