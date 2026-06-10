# Agentic CRM Intelligence Platform & Real-Time Email Operations System

An AI-powered CRM operations platform that ingests customer emails, classifies risk, retrieves internal policy context with RAG, and produces auditable safe action plans.

---

## 1. Project Overview & Key Features

This platform is a production-grade operations system designed to ingest high-throughput support tickets, legal disputes, billing inquiries, and security incidents. It combines rule-based heuristics with retrieval-augmented generation (RAG) and an LLM-based safe action planner to execute decisions safely and transparently.

### Key Features
* **Real-time Email Ingestion Simulation**: Streams customer payloads with metadata (message IDs, custom threads, timestamps).
* **PostgreSQL Persistence**: Stores normalized profiles, thread histories, email states, and audit trails.
* **`message_id` Deduplication**: Prevents double-processing of identical message IDs (`duplicate_ignored`).
* **Thread Linking & Contact History**: Groups related messages into threads, automatically updating customer profile metrics (churn risk, account valuation).
* **Heuristic Classification**: Performs immediate tagging of categorizations, SLA urgencies, priority scoring, and initial routing.
* **Policy-Grounded RAG**: Automatically queries a local vector store containing company knowledge base guidelines to ground responses.
* **Knowledge Base Documents**: Pre-loaded system policies regarding SLA commitments, security matrix, billing, and GDPR compliance.
* **Triage Agent Reasoning Trace**: Generates step-by-step reasoning logs detailing findings, policies applied, and final decisions.
* **Safe Auto-Reply Decisioning**: Restricts auto-replies or auto-execution based on safety classifications (safe, restricted, blocked).
* **Frontend Dashboard**: A professional dark React dashboard featuring interactive stats, critical escalation queue, email inspector, trace loggers, and timeline.
* **Critical Escalation Queue**: Auto-flags high-priority/escalated tickets for human inspection and team hand-offs.

---

## 2. Architecture & Data Flow

```
email-data-advanced.json
        ↓
stream_emails.py
        ↓
FastAPI /api/ingest
        ↓
PostgreSQL persistence + deduplication
        ↓
Heuristic classifier
        ↓
Conditional RAG retrieval
        ↓
Triage agent + safe action planner
        ↓
Actions table + audit trace
        ↓
React dashboard
```

---

## 3. Technical Stack

### Backend
* **FastAPI**: Main web services frameworks, routers, and CORS middleware.
* **SQLAlchemy**: ORM database schema representation.
* **PostgreSQL / SQLite**: Data storage and thread relationship tracking.
* **Pydantic**: Consistent response validation and strict schemas.
* **ChromaDB**: Native Vector Store hosting company documents.
* **sentence-transformers (`all-MiniLM-L6-v2`)**: Dense embedding generations.

### Frontend
* **React**: Core UI components.
* **Vite**: Rapid hot-reloading development and assets compilation.
* **CSS**: Clean custom-styled dark theme variables, responsive grids, and interactive badges.

### AI & RAG
* **ChromaDB vector store**: Local DB instances.
* **Embeddings**: Sentence Transformer embeddings mapping.
* **Markdown Policy Knowledge Base**: Documents for grounding.

---

## 4. Knowledge Base Policies
The platform grounds CRM actions against the following company markdown policies stored in `kb/`:
1. **[kb/pricing_policy.md](file:///c:/Users/Rushabh/Desktop/senai-crm-intelligence/kb/pricing_policy.md)**: Product pricing rules, multi-user tier structures, and retention discounts.
2. **[kb/sla_policy.md](file:///c:/Users/Rushabh/Desktop/senai-crm-intelligence/kb/sla_policy.md)**: Support tier response deadlines, SLA breaches, and service credits.
3. **[kb/refund_policy.md](file:///c:/Users/Rushabh/Desktop/senai-crm-intelligence/kb/refund_policy.md)**: Refund eligibility limits, 14-day money-back guarantee, and billing adjustments.
4. **[kb/api_docs.md](file:///c:/Users/Rushabh/Desktop/senai-crm-intelligence/kb/api_docs.md)**: Technical integration guidelines, developer token parameters, and routing paths.
5. **[kb/compliance_faq.md](file:///c:/Users/Rushabh/Desktop/senai-crm-intelligence/kb/compliance_faq.md)**: Privacy compliance guidelines, GDPR inquiries, and data deletion rights.
6. **[kb/escalation_matrix.md](file:///c:/Users/Rushabh/Desktop/senai-crm-intelligence/kb/escalation_matrix.md)**: Escalation team routing policies and strict auto-messaging safety rules.

---

## 5. Safety Rules & Auto-Reply Decisions

The platform enforces strict safe-action rules to mitigate legal, security, and privacy risks:
* **No Auto-Reply for Ransomware / Security Extortion**: Restricts messaging to prevent interacting with bad actors.
* **No Auto-Reply for Legal Threats**: Escalates immediately to the Legal team, freezing automated threads.
* **No Generic Auto-Reply for GDPR / Article 20 requests**: Compliance cases are blocked from auto-replies, requiring manual verification of data exports.
* **Spam is Ignored**: Automatically identified junk mail skips RAG grounding pipelines and is flagged for archiving.
* **Safe Billing / Pricing inquiries**: Permitted to automatically draft response templates using retrieved KB constraints.

---

## 6. Critical Scenario Validation

The following validation states are processed dynamically:

| Message ID | Category | Urgency | Status | Safety Decision | Escalation Queue |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **msg_038** | Security | Critical | Escalated | Auto-reply blocked | security |
| **msg_052** | Compliance | Critical | Escalated | Auto-reply blocked | compliance |
| **msg_020** | Legal | Critical | Escalated | Auto-reply blocked | legal |
| **msg_060** | Support | Critical | Escalated | Auto-reply blocked | legal |
| **msg_041** | Billing | Medium | Processing | Auto-reply allowed | billing |
| **msg_031** | Spam | Low | Spam | Auto-reply blocked | none |

---

## 7. Setup & Run Instructions

### 1. Backend Setup
1. **Navigate and Create Environment**:
   ```bash
   cd backend
   python -m venv venv
   ```
2. **Activate Environment**:
   * **Windows**: `venv\Scripts\activate`
   * **macOS/Linux**: `source venv/bin/activate`
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Environment variables**:
   Create a `.env` file in the root backend directory:
   ```env
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/senai_crm
   BACKEND_PORT=8000
   ```
   *(Note: If no PostgreSQL configuration is supplied, the server falls back to SQLite `sqlite:///./senai_crm.db` automatically for ease of local testing).*
5. **Start backend application**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### 2. Seed Vector Database (RAG)
To load markdown files into the ChromaDB vector database:
```bash
python scripts/seed_kb.py
```

### 3. Running the Streaming Simulator
To stream advanced emails simulating real-time operations:
```bash
python scripts/stream_emails.py --speed 10
```

### 4. Frontend Setup
1. **Navigate and Install**:
   ```bash
   cd frontend
   npm install
   ```
2. **Configure Settings**:
   Create `frontend/.env` file:
   ```env
   VITE_API_BASE_URL=http://127.0.0.1:8000
   ```
3. **Run Dev server**:
   ```bash
   npm run dev
   ```
   * Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 8. API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/health` | Core system status health check |
| **POST** | `/api/ingest` | Normalizes and ingests email payloads |
| **GET** | `/api/status/{message_id}` | Returns classification metrics for an email |
| **GET** | `/api/actions/{message_id}` | Returns action plan, trace, and policy grounding details |
| **GET** | `/dashboard/stats` | Aggregates operational KPIs for the stats cards |
| **GET** | `/threads/{contact_email}` | Returns historical threads and contact profile metrics |
| **GET** | `/rag/search?q=...` | Executes semantic search query against KB policies |
| **POST** | `/rag/seed` | Seeds KB policies into ChromaDB database |

---

## 9. Demo walkthrough

Follow this workflow to test the end-to-end functionality:
1. **Start Backend Server**: Confirm uvicorn is running on port `8000`.
2. **Seed KB**: Run `python scripts/seed_kb.py` to index markdown policies.
3. **Stream Emails**: Execute `python scripts/stream_emails.py --speed 10`. This ingests over 60 simulated emails into the database.
4. **Launch Dashboard**: Launch and open the React dashboard at [http://localhost:5173](http://localhost:5173).
5. **Evaluate Crucial Scenarios**:
   * Select **`msg_038`**: Note that the urgency is `Critical`, category is `Security`, and the Auto-reply is blocked (`Escalation Target: security`) because of a ransomware/extortion alert. Observe the step-by-step audit reasoning trace.
   * Select **`msg_052`**: GDPR Article 20 inquiry. Observe that it gets escalated to `compliance`, auto-reply is blocked, and RAG grounded policies on data deletion and exports are previewed.
   * Select **`msg_041`**: Standard billing question. Notice that auto-reply is **allowed** and the agent drafts a response containing pro-rata refund calculations using the RAG grounded refund policy.
   * Select **`msg_031`**: Inheritance scam spam email. Categorized as spam, auto-reply blocked, and RAG grounding is skipped.
6. **Deduplication Check**: Run the streaming simulator script again. Observe that it responds with `duplicate_ignored` status for already processed email IDs, preserving transactional consistency.

---

## 10. Evaluation Highlights

* **Resilience**: Gracefully handles malformed/duplicate payloads without interrupting streaming pipelines.
* **Efficiency**: Triggers costly vector search RAG queries conditionally, avoiding execution overhead for low-risk/spam tickets.
* **Explainability**: Persists comprehensive step-by-step agent reasoning logs and policy citation indices in database tables, keeping actions fully auditable.
* **Safety first**: Prevents hallucinated or inappropriate replies to sensitive items (such as legal threats, compliance, or security extortion).
* **Deep Context**: Merges individual emails into thread objects, mapping customer lifecycles and historical communications in real-time.
