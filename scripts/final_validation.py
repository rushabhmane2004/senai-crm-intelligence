"""
Final Validation Script -- SenAI CRM Intelligence Platform
===========================================================
Produces a clean, evaluator-ready demo state:

  1. Resets demo tables (actions, audit_log, emails, threads, contacts)
  2. Ensures KB is seeded (runs seed_kb.py if knowledge_chunks is empty)
  3. Ingests exactly 60 emails from data/email-data-advanced.json
  4. Validates 10 critical scenarios via live API calls
  5. Prints a clear PASS/FAIL per check and a final summary

Usage (from project root, with backend server already running):
    python scripts/final_validation.py

Exit code 0 only if ALL checks pass.
"""
import os
import sys
import json
import time
import subprocess
import requests

# ── Path setup ─────────────────────────────────────────────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(script_dir)
backend_path = os.path.join(workspace_root, "backend")

sys.path.insert(0, backend_path)
os.chdir(backend_path)

BASE_URL = "http://127.0.0.1:8000"
DATASET_PATH = os.path.join(workspace_root, "data", "email-data-advanced.json")

server_process = None
all_passed = True


# ── Helpers ────────────────────────────────────────────────────────────────────

def _pass(msg: str):
    print(f"  [PASS] {msg}")


def _fail(msg: str, detail: str = ""):
    global all_passed
    all_passed = False
    print(f"  [FAIL] {msg}" + (f"\n         Detail: {detail}" if detail else ""))


def _check(condition: bool, msg: str, detail: str = ""):
    if condition:
        _pass(msg)
    else:
        _fail(msg, detail)


def cleanup_and_exit(code: int):
    global server_process
    if server_process:
        print("\nTerminating started backend server...")
        server_process.terminate()
        server_process.wait()
    sys.exit(code)


def ensure_server():
    global server_process
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
        print("Backend server found running on port 8000.")
        return
    except requests.exceptions.RequestException:
        pass

    print("Starting backend server...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
        cwd=backend_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(15):
        try:
            requests.get(f"{BASE_URL}/health", timeout=1)
            print("Backend server started.")
            return
        except requests.exceptions.RequestException:
            time.sleep(1)
    print("[FAIL] Could not start backend server.")
    cleanup_and_exit(1)


# ── Step 1: Reset demo tables ──────────────────────────────────────────────────

def step_reset():
    print("\n--------------------------------------------------")
    print("STEP 1: Reset Demo Tables")
    print("--------------------------------------------------")
    reset_script = os.path.join(workspace_root, "scripts", "reset_demo_data.py")
    result = subprocess.run(
        [sys.executable, reset_script],
        capture_output=True,
        text=True,
        cwd=workspace_root,
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        print(f"[FAIL] reset_demo_data.py failed:\n{result.stderr[:400]}")
        cleanup_and_exit(1)


# ── Step 2: Ensure KB is seeded ────────────────────────────────────────────────

def step_seed_kb():
    print("\n--------------------------------------------------")
    print("STEP 2: Knowledge Base Seeding Check")
    print("--------------------------------------------------")
    from app.database import SessionLocal
    from app.models.knowledge_chunk import KnowledgeChunk

    db = SessionLocal()
    chunk_count = db.query(KnowledgeChunk).count()
    db.close()

    if chunk_count > 0:
        print(f"  KB already seeded: {chunk_count} chunks found. Skipping seed_kb.py.")
        return

    print("  KB empty -- running seed_kb.py...")
    seed_script = os.path.join(workspace_root, "scripts", "seed_kb.py")
    result = subprocess.run(
        [sys.executable, seed_script],
        capture_output=True,
        text=True,
        cwd=workspace_root,
    )
    if result.returncode != 0:
        print(f"[FAIL] seed_kb.py failed:\n{result.stderr[:400]}")
        cleanup_and_exit(1)
    print(result.stdout.strip())
    print("  KB seeded successfully.")


# ── Step 3: Ingest 60 emails ──────────────────────────────────────────────────

def step_ingest():
    print("\n--------------------------------------------------")
    print("STEP 3: Ingesting 60 Emails")
    print("--------------------------------------------------")

    if not os.path.exists(DATASET_PATH):
        print(f"[FAIL] Dataset not found: {DATASET_PATH}")
        cleanup_and_exit(1)

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        emails = json.load(f)

    print(f"  Dataset loaded: {len(emails)} emails found.")
    ingested = skipped = errors = 0

    for i, email in enumerate(emails, 1):
        try:
            resp = requests.post(f"{BASE_URL}/api/ingest", json=email, timeout=60)
            data = resp.json()
            status = data.get("status", "?")
            if status == "duplicate_ignored":
                skipped += 1
            else:
                ingested += 1
            if i % 10 == 0 or i == len(emails):
                print(f"  Progress: {i}/{len(emails)} | ingested={ingested} skipped={skipped} errors={errors}")
        except Exception as e:
            errors += 1
            print(f"  [WARN] Email {i} ({email.get('message_id','?')}): {e}")

    print(f"\n  Ingestion complete: {ingested} new, {skipped} duplicate, {errors} errors.")
    if errors > 0:
        print("[WARN] Some emails failed to ingest.")


# ── Step 4: Validate all 10 critical checks ────────────────────────────────────

def step_validate():
    global all_passed
    print("\n--------------------------------------------------")
    print("STEP 4: Final Scenario Validations")
    print("--------------------------------------------------")

    # ── Check 1: Dashboard stats ──────────────────────────────────────────────
    print("\n[Check 1] GET /dashboard/stats -- 60 emails, critical/escalated/spam > 0")
    try:
        r = requests.get(f"{BASE_URL}/dashboard/stats", timeout=10)
        d = r.json()
        total = d.get("total_emails", 0)
        _check(total == 60, f"total_emails == 60 (got {total})")
        _check(d.get("critical_emails", 0) > 0,
               f"critical_emails > 0 (got {d.get('critical_emails')})")
        _check(d.get("escalated_emails", 0) > 0,
               f"escalated_emails > 0 (got {d.get('escalated_emails')})")
        _check(d.get("spam_emails", 0) > 0,
               f"spam_emails > 0 (got {d.get('spam_emails')})")
        print(f"  Stats: {d}")
    except Exception as e:
        _fail("Dashboard stats request failed", str(e))

    # ── Check 2: msg_038 Security/Ransomware ─────────────────────────────────
    print("\n[Check 2] GET /api/status/msg_038 -- Security ransomware, auto_reply blocked")
    try:
        r = requests.get(f"{BASE_URL}/api/status/msg_038", timeout=10)
        d = r.json()
        raw = d.get("raw_entities") or {}
        _check(d.get("category") == "Security",
               f"category == Security (got {d.get('category')})")
        _check(d.get("urgency") == "Critical",
               f"urgency == Critical (got {d.get('urgency')})")
        _check(d.get("status") == "Escalated",
               f"status == Escalated (got {d.get('status')})")
        _check(d.get("priority_score") == 100,
               f"priority_score == 100 (got {d.get('priority_score')})")
        auto_reply = d.get("auto_reply_allowed") or raw.get("auto_reply_allowed")
        _check(auto_reply is False,
               f"auto_reply_allowed == False (got {auto_reply!r})")
    except Exception as e:
        _fail("msg_038 status request failed", str(e))

    # ── Check 3: msg_052 GDPR compliance ─────────────────────────────────────
    print("\n[Check 3] GET /api/status/msg_052 -- GDPR Compliance, escalated")
    try:
        r = requests.get(f"{BASE_URL}/api/status/msg_052", timeout=10)
        d = r.json()
        raw = d.get("raw_entities") or {}
        _check(d.get("category") == "Compliance",
               f"category == Compliance (got {d.get('category')})")
        _check(d.get("urgency") == "Critical",
               f"urgency == Critical (got {d.get('urgency')})")
        _check(d.get("status") == "Escalated",
               f"status == Escalated (got {d.get('status')})")
        # GDPR evidence in body, classification, or raw entities
        combined_text = json.dumps(raw).lower() + (d.get("body") or "").lower()
        gdpr_present = any(kw in combined_text for kw in ["gdpr", "article 20", "30-day", "data portability"])
        _check(gdpr_present, "GDPR/Article 20 evidence present in raw_entities or body")
    except Exception as e:
        _fail("msg_052 status request failed", str(e))

    # ── Check 4: msg_033 Karen reputation / web intelligence ─────────────────
    print("\n[Check 4] GET /api/status/msg_033 -- Complaint, web_intelligence_used=True")
    try:
        r = requests.get(f"{BASE_URL}/api/status/msg_033", timeout=10)
        d = r.json()
        raw = d.get("raw_entities") or {}
        _check(d.get("category") == "Complaint",
               f"category == Complaint (got {d.get('category')})")
        _check(d.get("status") == "Escalated",
               f"status == Escalated (got {d.get('status')})")
        wi_used = raw.get("web_intelligence_used")
        _check(wi_used is True,
               f"raw_entities.web_intelligence_used == True (got {wi_used!r})")
        wi = raw.get("web_intelligence") or {}
        pss = wi.get("public_sentiment_summary") or {}
        _check(bool(pss) or bool(raw.get("market_intelligence_block")),
               "web intelligence summary present")
    except Exception as e:
        _fail("msg_033 status request failed", str(e))

    # ── Check 5: msg_041 Alice billing / RAG ──────────────────────────────────
    print("\n[Check 5] GET /api/status/msg_041 -- Billing, safe path, RAG grounding")
    try:
        r = requests.get(f"{BASE_URL}/api/status/msg_041", timeout=10)
        d = r.json()
        raw = d.get("raw_entities") or {}
        _check(d.get("category") == "Billing",
               f"category == Billing (got {d.get('category')})")
        safe_statuses = ("Processing", "Received", "Replied")
        _check(d.get("status") in safe_statuses,
               f"status in {safe_statuses} (got {d.get('status')})")
        rag_context = raw.get("rag_context") or []
        rag_text = json.dumps(rag_context).lower()
        rag_ok = "pricing_policy" in rag_text or bool(rag_context)
        _check(rag_ok, f"RAG context populated (rag_context items: {len(rag_context)})")
    except Exception as e:
        _fail("msg_041 status request failed", str(e))

    # ── Check 6: msg_060 Bob agent dry-run ───────────────────────────────────
    print("\n[Check 6] POST /agent/dry-run/msg_060 -- dry-run, legal escalation, Enterprise")
    try:
        r = requests.post(f"{BASE_URL}/agent/dry-run/msg_060", timeout=30)
        d = r.json()
        _check(d.get("dry_run") is True, "dry_run == True")
        _check(d.get("auto_reply_allowed") is False,
               f"auto_reply_allowed == False (got {d.get('auto_reply_allowed')!r})")
        esc_team = d.get("escalation_team") or ""
        _check("legal" in esc_team.lower() or "support" in esc_team.lower(),
               f"escalation_team contains legal/support (got '{esc_team}')")
        acct_status = json.dumps(d.get("account_status") or {}).lower()
        acct_ok = any(kw in acct_status for kw in ["enterprise", "renewal", "on hold"])
        _check(acct_ok, f"account_status mentions Enterprise/renewal/on hold")
        tc = d.get("tool_call_count", 0)
        _check(tc <= 6, f"tool_call_count <= 6 (got {tc})")
    except Exception as e:
        _fail("msg_060 dry-run request failed", str(e))

    # ── Check 7: msg_031 spam safety ─────────────────────────────────────────
    print("\n[Check 7] GET /api/status/msg_031 -- Spam category and status")
    try:
        r = requests.get(f"{BASE_URL}/api/status/msg_031", timeout=10)
        d = r.json()
        raw = d.get("raw_entities") or {}
        _check(d.get("category") == "Spam",
               f"category == Spam (got {d.get('category')})")
        _check(d.get("status") == "Spam",
               f"status == Spam (got {d.get('status')})")
        auto_reply = d.get("auto_reply_allowed") or raw.get("auto_reply_allowed")
        _check(auto_reply is False or auto_reply is None,
               f"auto_reply_allowed is False/None (got {auto_reply!r})")
    except Exception as e:
        _fail("msg_031 status request failed", str(e))

    # ── Check 8: Karen sentiment trend deterioration ──────────────────────────
    print("\n[Check 8] GET /analytics/sentiment-trend?sender=karen.w@retail-co.com -- deterioration")
    try:
        r = requests.get(
            f"{BASE_URL}/analytics/sentiment-trend",
            params={"sender": "karen.w@retail-co.com", "days": 30},
            timeout=10,
        )
        d = r.json()
        det = d.get("deterioration_detected") or d.get("deterioration", {}).get("detected")
        _check(det is True, f"deterioration_detected == True (got {det!r})")
        pts = d.get("total_points") or len(d.get("trend_points") or d.get("data_points") or [])
        _check(pts >= 3, f"trend points >= 3 (got {pts})")
    except Exception as e:
        _fail("sentiment-trend request failed", str(e))

    # -- Check 9: Web intelligence reputation ---------------------------------
    print("\n[Check 9] GET /intelligence/reputation?company=retail-co.com -- offline mock")
    try:
        r = requests.get(
            f"{BASE_URL}/intelligence/reputation",
            params={"company": "retail-co.com"},
            timeout=10,
        )
        d = r.json()
        _check(d.get("scraping_mode") == "offline_mock",
               f"scraping_mode == offline_mock (got {d.get('scraping_mode')})")
        _check(d.get("robots_checked") is True,
               f"robots_checked == True (got {d.get('robots_checked')!r})")
        pss = d.get("public_sentiment_summary") or {}
        _check("g2_rating" in pss,
               f"g2_rating present in public_sentiment_summary (keys: {list(pss.keys())})")
    except Exception as e:
        _fail("reputation intelligence request failed", str(e))

    # -- Check 10: RAG GDPR retrieval -----------------------------------------
    print("\n[Check 10] GET /rag/search?q=GDPR Article 20 -- compliance_faq.md or escalation_matrix.md")
    try:
        r = requests.get(
            f"{BASE_URL}/rag/search",
            params={"q": "GDPR Article 20 data portability 30-day statutory window"},
            timeout=15,
        )
        d = r.json()
        results = d.get("results") or []
        source_docs = [res.get("source_doc", "") for res in results]
        expected = {"compliance_faq.md", "escalation_matrix.md"}
        found = expected.intersection(set(source_docs))
        _check(bool(found),
               f"Top docs contain compliance_faq.md or escalation_matrix.md (got {source_docs})")
    except Exception as e:
        _fail("RAG search request failed", str(e))


# -- Main -----------------------------------------------------------------------

def main():
    print("====================================================")
    print("  SenAI CRM Intelligence -- Final Validation Script ")
    print("====================================================")

    ensure_server()
    step_reset()
    step_seed_kb()
    step_ingest()
    step_validate()

    print("\n========================================================")
    if all_passed:
        print("  FINAL VALIDATION PASSED -- Clean 60-email demo ready!")
        print("========================================================")
        cleanup_and_exit(0)
    else:
        print("  FINAL VALIDATION FAILED -- See FAIL entries above.")
        print("========================================================")
        cleanup_and_exit(1)


if __name__ == "__main__":
    main()
