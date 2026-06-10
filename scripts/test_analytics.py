import os
import sys
import json
import time
import requests
import subprocess

# Set paths
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(script_dir)
backend_path = os.path.join(workspace_root, "backend")

server_process = None

def cleanup_and_exit(code):
    global server_process
    if server_process:
        print("Terminating started backend server...")
        server_process.terminate()
        server_process.wait()
    sys.exit(code)

def main():
    global server_process
    print("==================================================")
    print("Starting Analytics Endpoints & Safety Tests")
    print("==================================================")

    # Try connecting to port 8000. If not running, spin it up.
    try:
        requests.get("http://127.0.0.1:8000/health", timeout=1)
        print("Found existing backend server running on port 8000.")
    except requests.exceptions.RequestException:
        print("Starting backend server locally...")
        # Start server with python -m uvicorn app.main:app
        server_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
            cwd=backend_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Wait for server to start
        for _ in range(10):
            try:
                requests.get("http://127.0.0.1:8000/health", timeout=1)
                print("Backend server started successfully.")
                break
            except requests.exceptions.RequestException:
                time.sleep(1)
        else:
            print("[FAIL] Failed to start backend server.")
            cleanup_and_exit(1)

    # 1. Ensure Karen's three messages are ingested: msg_006, msg_018, msg_033
    json_path = os.path.join(workspace_root, "data", "email-data-advanced.json")
    if not os.path.exists(json_path):
        print(f"[FAIL] Missing dataset file at {json_path}")
        cleanup_and_exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        emails = json.load(f)

    emails_by_id = {e["message_id"]: e for e in emails}
    karen_msg_ids = ["msg_006", "msg_018", "msg_033"]

    print("\n--- Verifying Ingestion of Karen's Emails ---")
    for msg_id in karen_msg_ids:
        resp = requests.get(f"http://127.0.0.1:8000/api/status/{msg_id}")
        if resp.status_code == 404:
            print(f"Message {msg_id} is missing. Ingesting...")
            if msg_id not in emails_by_id:
                print(f"[FAIL] {msg_id} not found in advanced dataset.")
                cleanup_and_exit(1)
            
            # Post ingestion
            ingest_resp = requests.post(
                "http://127.0.0.1:8000/api/ingest",
                json=emails_by_id[msg_id],
                timeout=30
            )
            if ingest_resp.status_code != 200:
                print(f"[FAIL] Ingesting {msg_id} failed: {ingest_resp.text}")
                cleanup_and_exit(1)
            print(f"Successfully ingested {msg_id}.")
        else:
            print(f"Message {msg_id} is already in the database.")

    # 2. Test /analytics/category-breakdown
    print("\n--- Testing /analytics/category-breakdown ---")
    resp = requests.get("http://127.0.0.1:8000/analytics/category-breakdown")
    if resp.status_code != 200:
        print(f"[FAIL] Category breakdown status code is {resp.status_code}")
        cleanup_and_exit(1)

    data = resp.json()
    # verify total > 0
    total = data.get("total", 0)
    print(f"Total emails: {total}")
    if total <= 0:
        print(f"[FAIL] Expected total > 0, got {total}")
        cleanup_and_exit(1)

    # verify categories list not empty
    categories = data.get("categories", [])
    if not isinstance(categories, list) or len(categories) == 0:
        print("[FAIL] Expected categories to be a non-empty list")
        cleanup_and_exit(1)

    # verify fields in category breakdown
    for item in categories:
        if "category" not in item or "count" not in item or "percentage" not in item:
            print(f"[FAIL] Category breakdown item missing required fields: {item}")
            cleanup_and_exit(1)
    print(f"Validated {len(categories)} categories.")
    print("[PASS] Category breakdown verified successfully.")

    # 3. Test /analytics/sentiment-trend?sender=karen.w@retail-co.com&days=30
    print("\n--- Testing /analytics/sentiment-trend?sender=karen.w@retail-co.com&days=30 ---")
    resp = requests.get("http://127.0.0.1:8000/analytics/sentiment-trend?sender=karen.w@retail-co.com&days=30")
    if resp.status_code != 200:
        print(f"[FAIL] Sentiment trend status code is {resp.status_code}")
        cleanup_and_exit(1)

    data = resp.json()
    points = data.get("points", [])
    total_points = data.get("total_points", 0)
    det_detected = data.get("deterioration_detected")
    
    print(f"Trend Points Count: {total_points}")
    print(f"Deterioration Detected: {det_detected}")

    if total_points < 3:
        print(f"[FAIL] Expected total_points >= 3, got {total_points}")
        cleanup_and_exit(1)

    if det_detected is not True:
        print("[FAIL] Expected deterioration_detected to be True for Karen's sequence")
        cleanup_and_exit(1)

    # Verify at least one moving_average field is present
    has_ma = any("moving_average" in p for p in points)
    if not has_ma:
        print("[FAIL] Expected moving_average field to be present in the trend points")
        cleanup_and_exit(1)

    print("[PASS] Sentiment trend verified successfully.")

    # 4. Test /analytics/risk-summary
    print("\n--- Testing /analytics/risk-summary ---")
    resp = requests.get("http://127.0.0.1:8000/analytics/risk-summary")
    if resp.status_code != 200:
        print(f"[FAIL] Risk summary status code is {resp.status_code}")
        cleanup_and_exit(1)

    data = resp.json()
    total_emails = data.get("total_emails", 0)
    top_senders = data.get("top_at_risk_senders", [])

    print(f"Total Emails in Risk Summary: {total_emails}")
    print(f"Number of At-Risk Senders: {len(top_senders)}")

    if total_emails <= 0:
        print(f"[FAIL] Expected total_emails > 0, got {total_emails}")
        cleanup_and_exit(1)

    # Verify Karen is in top_at_risk_senders
    karen_present = any(s.get("sender") == "karen.w@retail-co.com" for s in top_senders)
    if not karen_present:
        print("[FAIL] Expected karen.w@retail-co.com to be present in top_at_risk_senders")
        cleanup_and_exit(1)

    # Verify keys of the at risk senders
    for sender in top_senders:
        required_keys = ["sender", "message_count", "latest_sentiment_score", "deterioration_detected", "highest_urgency"]
        for key in required_keys:
            if key not in sender:
                print(f"[FAIL] Missing key '{key}' in risk sender profile: {sender}")
                cleanup_and_exit(1)

    print("[PASS] Risk summary verified successfully.")

    # 5. Regression Safety Check on msg_038
    print("\n--- Testing Regression Safety ---")
    resp_class = requests.get("http://127.0.0.1:8000/api/classification/msg_038")
    if resp_class.status_code == 200:
        print("[PASS] /api/classification/msg_038 is accessible.")
        c_data = resp_class.json()
        assert "heuristic_result" in c_data, "Missing heuristic_result"
        assert "llm_classification" in c_data, "Missing llm_classification"
    elif resp_class.status_code == 404:
        print("[NOTE] msg_038 is not in database, skipping classification check.")
    else:
        print(f"[FAIL] /api/classification/msg_038 returned status {resp_class.status_code}")
        cleanup_and_exit(1)

    resp_status = requests.get("http://127.0.0.1:8000/api/status/msg_038")
    if resp_status.status_code == 200:
        print("[PASS] /api/status/msg_038 is accessible.")
        s_data = resp_status.json()
        assert "status" in s_data, "Missing status"
        assert "category" in s_data, "Missing category"
        assert "urgency" in s_data, "Missing urgency"
    elif resp_status.status_code == 404:
        print("[NOTE] msg_038 is not in database, skipping status check.")
    else:
        print(f"[FAIL] /api/status/msg_038 returned status {resp_status.status_code}")
        cleanup_and_exit(1)

    print("[SUCCESS] All regression safety checks passed.")
    print("\n==================================================")
    print("[SUCCESS] All analytics endpoint checks completed successfully!")
    print("==================================================")
    cleanup_and_exit(0)

if __name__ == "__main__":
    main()
