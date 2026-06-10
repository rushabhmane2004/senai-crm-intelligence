import os
import sys
import json
import requests

# Add backend directory to Python path to import modules cleanly
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(script_dir)
backend_path = os.path.join(workspace_root, "backend")
os.chdir(backend_path)
sys.path.insert(0, backend_path)

try:
    from app.database import SessionLocal
    from app.models.email import Email
    from app.models.action import Action
except ImportError as e:
    print(f"Failed to import database modules: {e}")
    sys.exit(1)

def clean_database(test_ids):
    print("Cleaning up database for test emails...")
    db = SessionLocal()
    try:
        for msg_id in test_ids:
            email = db.query(Email).filter(Email.message_id == msg_id).first()
            if email:
                # Delete corresponding actions
                db.query(Action).filter(Action.email_id == email.id).delete()
                # Delete email
                db.delete(email)
        db.commit()
        print("Database cleaned up successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error during database clean up: {e}")
        sys.exit(1)
    finally:
        db.close()

def main():
    test_ids = ["msg_038", "msg_052", "msg_041", "msg_006", "msg_002", "msg_020"]
    
    # 1. Clean up database
    clean_database(test_ids)

    # 2. Load dataset
    json_path = os.path.join(workspace_root, "data", "email-data-advanced.json")
    if not os.path.exists(json_path):
        print(f"[FAIL] Missing dataset file at {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        emails = json.load(f)

    emails_by_id = {email["message_id"]: email for email in emails}

    ingest_url = "http://127.0.0.1:8000/api/ingest"
    for msg_id in test_ids:
        if msg_id not in emails_by_id:
            print(f"[FAIL] Test message {msg_id} not found in dataset")
            sys.exit(1)
        print(f"Ingesting {msg_id}...")
        resp = requests.post(ingest_url, json=emails_by_id[msg_id], timeout=60)
        if resp.status_code != 200:
            print(f"[FAIL] Ingestion failed for {msg_id}: {resp.status_code} - {resp.text}")
            sys.exit(1)
        print(f"Ingestion response for {msg_id}: {resp.json()}")

    print("\nStarting scenario validations...")
    print("=" * 50)
    failed = False

    # Scenario 1: msg_038
    try:
        resp = requests.get("http://127.0.0.1:8000/api/classification/msg_038")
        assert resp.status_code == 200, f"Status code {resp.status_code}"
        data = resp.json()
        assert data["heuristic_result"]["category"] == "Security", f"Expected Security, got {data['heuristic_result']['category']}"
        assert data["heuristic_result"]["urgency"] == "Critical", f"Expected Critical, got {data['heuristic_result']['urgency']}"
        assert "confidence" in data["llm_classification"], "Confidence missing"
        assert data["llm_classification"]["sentiment_score"] <= -0.9, f"Expected <= -0.9, got {data['llm_classification']['sentiment_score']}"
        
        # Verify action
        act_resp = requests.get("http://127.0.0.1:8000/api/actions/msg_038")
        assert act_resp.status_code == 200
        act_data = act_resp.json()
        assert act_data["agent_action"]["auto_reply_allowed"] is False
        assert act_data["agent_action"]["requires_human_approval"] is True
        print("[PASS] Scenario 1 (msg_038: Security/Ransomware safety overrides)")
    except Exception as e:
        print(f"[FAIL] Scenario 1 (msg_038): {e}")
        failed = True

    # Scenario 2: msg_052
    try:
        resp = requests.get("http://127.0.0.1:8000/api/classification/msg_052")
        assert resp.status_code == 200
        data = resp.json()
        assert data["heuristic_result"]["category"] == "Compliance", f"Expected Compliance, got {data['heuristic_result']['category']}"
        assert data["heuristic_result"]["category"] != "Inquiry"
        deadlines = data["llm_classification"]["detected_entities"]["deadlines"]
        assert any("30-day" in d.lower() for d in deadlines), f"Expected 30-day in deadlines, got {deadlines}"
        assert "confidence" in data["llm_classification"], "Confidence missing"
        print("[PASS] Scenario 2 (msg_052: Compliance GDPR 30-day window)")
    except Exception as e:
        print(f"[FAIL] Scenario 2 (msg_052): {e}")
        failed = True

    # Scenario 3: msg_041
    try:
        resp = requests.get("http://127.0.0.1:8000/api/classification/msg_041")
        assert resp.status_code == 200
        data = resp.json()
        assert data["heuristic_result"]["category"] == "Billing", f"Expected Billing, got {data['heuristic_result']['category']}"
        assert "confidence" in data["llm_classification"], "Confidence missing"
        
        body = emails_by_id["msg_041"]["body"].lower()
        has_pro_rata = "pro-rata" in body
        products = data["llm_classification"]["detected_entities"]["products_mentioned"]
        has_standard_plan = any("standard" in p.lower() for p in products)
        assert has_pro_rata or has_standard_plan, f"Context standard plan or pro-rata not found. Products: {products}, Body: {body}"
        print("[PASS] Scenario 3 (msg_041: Billing pro-rata context)")
    except Exception as e:
        print(f"[FAIL] Scenario 3 (msg_041): {e}")
        failed = True

    # Scenario 4: msg_006
    try:
        resp = requests.get("http://127.0.0.1:8000/api/classification/msg_006")
        assert resp.status_code == 200
        data = resp.json()
        assert data["heuristic_result"]["category"] == "Complaint", f"Expected Complaint, got {data['heuristic_result']['category']}"
        assert data["llm_classification"]["sentiment_score"] < 0, f"Expected negative sentiment_score, got {data['llm_classification']['sentiment_score']}"
        print("[PASS] Scenario 4 (msg_006: Angry Complaint negative sentiment)")
    except Exception as e:
        print(f"[FAIL] Scenario 4 (msg_006): {e}")
        failed = True

    # Scenario 5: msg_002
    try:
        resp = requests.get("http://127.0.0.1:8000/api/classification/msg_002")
        assert resp.status_code == 200
        data = resp.json()
        monetary = data["llm_classification"]["detected_entities"]["monetary_amounts"]
        assert any("10,000" in m for m in monetary), f"Expected $10,000/minute in monetary amounts, got {monetary}"
        print("[PASS] Scenario 5 (msg_002: Monetary entity extraction)")
    except Exception as e:
        print(f"[FAIL] Scenario 5 (msg_002): {e}")
        failed = True

    # Scenario 6: msg_020
    try:
        resp = requests.get("http://127.0.0.1:8000/api/classification/msg_020")
        assert resp.status_code == 200
        data = resp.json()
        assert data["heuristic_result"]["category"] == "Legal", f"Expected Legal, got {data['heuristic_result']['category']}"
        
        act_resp = requests.get("http://127.0.0.1:8000/api/actions/msg_020")
        assert act_resp.status_code == 200
        act_data = act_resp.json()
        assert act_data["agent_action"]["auto_reply_allowed"] is False
        assert act_data["agent_action"]["requires_human_approval"] is True
        print("[PASS] Scenario 6 (msg_020: Legal threat safety overrides)")
    except Exception as e:
        print(f"[FAIL] Scenario 6 (msg_020): {e}")
        failed = True

    print("=" * 50)
    if failed:
        print("[FAIL] Some scenario checks failed.")
        sys.exit(1)
    else:
        print("[SUCCESS] All scenario checks passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
