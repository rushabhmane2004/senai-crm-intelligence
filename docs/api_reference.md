# API Reference — Agentic CRM Intelligence Platform

This document provides a concise reference for all public API endpoints exposed by the SenAI CRM Intelligence backend.

**Base URL**: `http://127.0.0.1:8000` (local development)  
**OpenAPI Interactive Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
**OpenAPI JSON**: [`docs/openapi.json`](./openapi.json) (generated via `python scripts/export_openapi.py`)

---

## 1. Core / System

### `GET /health`
**Purpose**: Lightweight liveness check. Returns immediately with no DB interaction.

**Response:**
```json
{ "status": "healthy", "service": "senai-crm-backend" }
```

---

### `POST /api/ingest`
**Purpose**: Ingest a customer email. Runs the full pipeline: deduplication → thread linking → contact upsert → heuristic classification → RAG grounding → LLM classification → web intelligence → triage agent → action plan → DB persist.

**Request body** (JSON):
| Field | Type | Required | Description |
|---|---|---|---|
| `message_id` | string | Yes | Unique email identifier — enforces deduplication |
| `sender` | string | Yes | Sender email address |
| `subject` | string | No | Email subject |
| `body` | string | No | Email body (truncated to 10,000 chars for AI) |
| `timestamp` | ISO 8601 datetime | Yes | Email send time |
| `thread_id` | string | No | Thread identifier for grouping related emails |

**Response:**
```json
{
  "email_id": 42,
  "message_id": "msg_038",
  "thread_id": "thread_security_002",
  "status": "Escalated",
  "priority_score": 100
}
```
Returns `"status": "duplicate_ignored"` if `message_id` already exists.

**Safety notes**: Auto-reply is blocked for Security, Legal, Compliance, and Spam categories regardless of other factors.

---

### `GET /api/status/{message_id}`
**Purpose**: Return the current classification state and full `raw_entities` enrichment blob for a processed email.

**Path param**: `message_id` — the original ingestion identifier.

**Response fields**: `message_id`, `status`, `category`, `urgency`, `priority_score`, `requires_human`, `confidence`, `sender`, `subject`, `body`, `raw_entities`, `agent_decision`, `auto_reply_allowed`, `requires_human_approval`, `escalation_team`, `safety_level`.

---

### `GET /api/actions/{message_id}`
**Purpose**: Return the full triage agent action plan for an email including reasoning trace, draft reply, policy citations, and safety classification.

**Response** includes `agent_action` sub-object with:
- `action_type`, `recommended_action`, `auto_reply_allowed`, `requires_human_approval`
- `escalation_team`, `safety_level`, `policy_sources`
- `agent_reasoning_log` (step-by-step trace array)
- `proposed_content` (draft reply template)

---

### `GET /threads/{contact_email}`
**Purpose**: Retrieve all threads and email history for a contact.

**Query param**: `contact_email` — sender email address.

**Response**: Array of thread objects with embedded email timelines and contact profile metrics (churn risk, account value).

---

### `GET /dashboard/stats`
**Purpose**: Return aggregated operational KPIs for the frontend dashboard stats cards.

**Response includes**: total emails, emails by status, emails by category, emails by urgency, escalation counts, spam counts, at-risk sender counts.

---

## 2. Classification & Analytics

### `GET /api/classification/{message_id}`
**Purpose**: Return the structured LLM classification output, detected entities, and prompt snapshot for a specific email.

**Response** includes `heuristic_result` and `llm_classification` sub-objects:
- `category`, `urgency`, `sentiment_score`, `confidence`
- `detected_entities`: `order_ids`, `ticket_ids`, `monetary_amounts`, `deadlines`, `products_mentioned`
- `prompt_snapshot` — exact prompt sent to the classifier

---

### `GET /analytics/sentiment-trend`
**Purpose**: Return chronological sentiment trend data for a sender or globally.

**Query params**:
| Param | Type | Default | Description |
|---|---|---|---|
| `sender` | string | None | Filter to a specific sender email. Omit for global trend. |
| `days` | integer | 30 | Lookback window in days |

**Response includes**: trend points (timestamp + score + moving average), deterioration flag, deterioration details if 3+ consecutive negative emails detected.

**Safety note**: `sentiment_score` uses LLM output when available; falls back to heuristic category/urgency mapping.

---

### `GET /analytics/category-breakdown`
**Purpose**: Return total email count and per-category distribution statistics.

**Response**: `{ "total_emails": 131, "categories": { "Complaint": 12, "Billing": 8, ... } }`

---

### `GET /analytics/risk-summary`
**Purpose**: Return high-level risk counts and a list of at-risk sender profiles.

**Response includes**: critical count, escalated count, spam count, total at-risk senders, top at-risk sender list with churn risk scores.

---

## 3. RAG / Knowledge Base

### `GET /rag/search`
**Purpose**: Execute a semantic similarity search against the ChromaDB vector store containing company policy documents.

**Query params**:
| Param | Type | Default | Description |
|---|---|---|---|
| `q` | string | Required | Natural language search query |
| `top_k` | integer | 3 | Number of top chunks to return |

**Response**: `{ "results": [ { "source_doc": "sla_policy.md", "policy_ref": "...", "similarity_score": 0.61, "chunk_text": "..." } ] }`

**Knowledge base documents**: `sla_policy.md`, `pricing_policy.md`, `refund_policy.md`, `compliance_faq.md`, `escalation_matrix.md`, `api_docs.md`

---

### `POST /rag/seed`
**Purpose**: (Re-)seed all markdown policy documents from `kb/` into ChromaDB.

**Response**: `{ "seeded": 6, "skipped": 0, "chunks_total": 12 }`

---

## 4. Autonomous Agent

### `POST /agent/dry-run/{message_id}`
**Purpose**: Execute a **planning-only** triage agent simulation for an email. No database writes occur. Returns a full ReAct-style tool trace for audit and inspection.

**Path param**: `message_id`

**Response schema**:
```json
{
  "dry_run": true,
  "message_id": "msg_060",
  "agent_version": "triage-agent-v1",
  "max_tool_calls": 6,
  "tool_call_count": 6,
  "tool_trace": [
    {
      "step": 1,
      "thought": "...",
      "action": "get_thread_history",
      "observation": "...",
      "next": "..."
    }
  ],
  "decision": "Escalate SLA breach and legal review",
  "recommended_action": "Route to Legal and Support Leadership",
  "auto_reply_allowed": false,
  "requires_human_approval": true,
  "escalation_team": "legal",
  "safety_level": "blocked",
  "reasoning_trace": ["..."],
  "policy_sources_used": ["sla_policy.md", "escalation_matrix.md"],
  "draft_reply": "...",
  "internal_ticket_preview": {...},
  "human_escalation_brief": "...",
  "contact_profile": {...},
  "account_status": {...}
}
```

**Available mock tools**: `get_thread_history`, `get_contact_profile`, `check_account_status`, `search_knowledge_base`, `flag_for_legal`, `create_internal_ticket`, `draft_reply_tool`

**Safety notes**: `auto_reply_allowed` is always `false` for Security, Legal, and Compliance scenarios.

---

## 5. Web Intelligence

### `GET /intelligence/reputation`
**Purpose**: Return cached offline public reputation intelligence for a company or domain. Fires automatically during ingestion when reputation-related keywords or complaint signals are detected.

**Query params**:
| Param | Type | Required | Description |
|---|---|---|---|
| `company` | string | Yes | Company name or domain (e.g. `retail-co.com`) |

**Response schema**:
```json
{
  "target_entity": "retail-co.com",
  "source": "offline_mock_reputation_intelligence",
  "cache_status": "hit",
  "robots_checked": true,
  "scraping_mode": "offline_mock",
  "public_sentiment_summary": {
    "g2_rating": 4.4,
    "trustpilot_rating": 3.8,
    "capterra_rating": 4.1,
    "recent_review_count": 3,
    "common_complaints": ["slow support response", "refund delays", "dashboard performance"],
    "competitor_rating": { "CompetitorX": 4.6 },
    "summary": "Recent public sentiment shows support responsiveness concerns and potential churn risk."
  },
  "scraped_at": "2026-06-10T18:00:00",
  "expires_at": "2026-06-11T00:00:00"
}
```

**`cache_status` values**:
- `"hit"` — served from unexpired DB cache
- `"miss"` — first fetch, new record created and committed
- `"fallback"` — error occurred, graceful fallback returned

**Safety notes**: `scraping_mode` is always `"offline_mock"` by default. `robots_checked: true` signals robots.txt compliance intent. Live scraping can be enabled behind the same interface later.

---

## 6. Error Envelope

All error responses follow a consistent envelope schema:
```json
{
  "error_code": "NOT_FOUND",
  "message": "Email with message_id 'msg_999' not found",
  "details": {}
}
```

Common error codes: `NOT_FOUND`, `VALIDATION_ERROR`, `INTERNAL_SERVER_ERROR`, `UNAUTHORIZED`, `FORBIDDEN`
