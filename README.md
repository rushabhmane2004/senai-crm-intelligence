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

## 5.5. LLM Classification Provider
The system features a pluggable LLM structured classification layer that operates directly during email ingestion:
* **LLM_PROVIDER**: Set to `mock` by default in config settings.
* **Deterministic Fallback**: Falls back automatically to offline `mock` mode if `OPENAI_API_KEY` is not found, enabling offline execution and reproducible evaluation.
* **Structured Output Schema**: Extracts key parameters including category, sentiment, sentiment score, urgency, requires human flag, model provider, prompt snapshot and regex-extracted entities (order IDs, ticket IDs, monetary amounts, deadlines, and products mentioned).
* **Low Confidence Safety Valve**: If classification confidence drops below `0.70`, the system forces `requires_human=True` and disables auto-replies to prevent inappropriate automated emails.
* **Safety Overrides**: The classifier output strictly respects pre-filter heuristics. Security threats, legal disputes, spam, internal emails, and regulatory compliance actions are never downgraded, and their auto-reply protections are strictly preserved.

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
    LLM_PROVIDER=mock
    OPENAI_API_KEY=
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
*(Note: The KB policies are intentionally concise, so each document may generate only one or a few chunks. Retrieval is validated by source-document correctness).*

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
| **GET** | `/api/classification/{message_id}` | Returns structured LLM classification, entities, and prompt snapshots |
| **GET** | `/dashboard/stats` | Aggregates operational KPIs for the stats cards |
| **GET** | `/threads/{contact_email}` | Returns historical threads and contact profile metrics |
| **GET** | `/rag/search?q=...` | Executes semantic search query against KB policies |
| **POST** | `/rag/seed` | Seeds KB policies into ChromaDB database |
| **GET** | `/analytics/sentiment-trend` | Returns chronological sentiment trend, moving average, and deterioration flags |
| **GET** | `/analytics/category-breakdown` | Returns total email count and category breakdown statistics |
| **GET** | `/analytics/risk-summary` | Returns critical/escalated/spam counts and top at-risk customer senders |
| **GET** | `/intelligence/reputation?company=...` | Returns offline mock public reputation intelligence (G2, Trustpilot, Capterra) with 6-hour DB cache semantics |
| **POST** | `/agent/dry-run/{message_id}` | Runs a planning-only dry-run simulation of the triage agent without side effects, returning a ReAct tool trace |

---

## 9. Demo walkthrough

Follow this workflow to test the end-to-end functionality:
1. **Start Backend Server**: Confirm uvicorn is running on port `8000`.
2. **Seed KB**: Run `python scripts/seed_kb.py` to index markdown policies.
3. **Stream Emails**: Execute `python scripts/stream_emails.py --speed 10`. This ingests over 60 simulated emails into the database.
4. **Validate LLM Classification**: Execute `python scripts/test_llm_classification.py` to verify structured outputs, entity extraction, and safety overrides.
5. **Validate Sentiment Trend & Analytics**: Run `python scripts/test_analytics.py` to verify categories, trends, risk, and regression safety.
6. **Validate RAG Quality**: Run `python scripts/test_rag_quality.py` to verify RAG semantic retrieval accuracy on all 6 evaluation scenarios.
7. **Validate Web Intelligence**: Run `python scripts/test_web_intelligence.py` to verify offline reputation intelligence, cache hit semantics, and msg_033 raw_entities enrichment.
8. **Validate Autonomous Agent Dry-Run**: Run `python scripts/test_agent_dry_run.py` to verify the planning-only endpoint runs without side effects and produces ReAct-style traces.
9. **Launch Dashboard**: Launch and open the React dashboard at [http://localhost:5173](http://localhost:5173).
10. **Evaluate Crucial Scenarios**:
   * Select **`msg_038`**: Note that the urgency is `Critical`, category is `Security`, and the Auto-reply is blocked (`Escalation Target: security`) because of a ransomware/extortion alert. Observe the step-by-step audit reasoning trace.
   * Select **`msg_052`**: GDPR Article 20 inquiry. Observe that it gets escalated to `compliance`, auto-reply is blocked, and RAG grounded policies on data deletion and exports are previewed.
   * Select **`msg_041`**: Standard billing question. Notice that auto-reply is **allowed** and the agent drafts a response containing pro-rata refund calculations using the RAG grounded refund policy.
   * Select **`msg_031`**: Inheritance scam spam email. Categorized as spam, auto-reply blocked, and RAG grounding is skipped.
10. **Deduplication Check**: Run the streaming simulator script again. Observe that it responds with `duplicate_ignored` status for already processed email IDs, preserving transactional consistency.

---

## 10. Evaluation Highlights

* **Resilience**: Gracefully handles malformed/duplicate payloads without interrupting streaming pipelines.
* **Efficiency**: Triggers costly vector search RAG queries conditionally, avoiding execution overhead for low-risk/spam tickets.
* **Explainability**: Persists comprehensive step-by-step agent reasoning logs and policy citation indices in database tables, keeping actions fully auditable.
* **Safety first**: Prevents hallucinated or inappropriate replies to sensitive items (such as legal threats, compliance, or security extortion).
* **Deep Context**: Merges individual emails into thread objects, mapping customer lifecycles and historical communications in real-time.

---

## 11. Known Limitations

The following items represent design boundaries established to comply with offline sandbox constraints and API key restrictions:
1. **Rule-Based Triage Planner**: The triage engine uses a deterministic regex parser and policy lookup rather than an external LLM API (such as OpenAI/Anthropic). This eliminates token cost overhead, connectivity errors, and API credential issues.
2. **Heuristic Sentiment Trend**: The `/analytics/sentiment-trend` endpoint evaluates email customer sentiment timelines using category/urgency mappings rather than a live machine learning model.
3. **Web Intelligence Offline Mode**: Web intelligence runs in offline mock mode by default for safe reproducible evaluation. The architecture includes full cache semantics (`web_intelligence_cache` DB table, 6-hour TTL, `robots_checked=true`) and trigger logic. Live scraping can be enabled later behind the same service interface without changing the API contract.
4. **Mock Reputation Intelligence**: The `/intelligence/reputation` endpoint provides realistic mock ratings and threat reports. It does not perform active scraping on real websites to bypass sandboxed firewall blocks.
5. **Scope Exclusions**: SMTP mail triggers and database level event triggers are not implemented. Action executions are stored as status logs.

---

## 12. Final Assessment Audit Report

For a complete checklist of requirement coverage, scenario validations, and automatic disqualifier checks, refer to the [FINAL_AUDIT.md](file:///c:/Users/Rushabh/Desktop/senai-crm-intelligence/FINAL_AUDIT.md) document in the workspace.

