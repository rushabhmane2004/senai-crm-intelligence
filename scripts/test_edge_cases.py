import sys
import json
import requests
import time
import random

BASE_URL = "http://127.0.0.1:8000/api/ingest"

# Generate a unique run ID for re-running the test script safely
run_id = f"{int(time.time())}_{random.randint(1000, 9999)}"

# Base valid payload to use as template
VALID_TEMPLATE = {
    "message_id": "edge_msg_001",
    "sender": "customer@edge-test.com",
    "subject": "Edge Testing",
    "body": "Normal standard body query content.",
    "timestamp": "2026-06-10T12:00:00Z",
    "thread_id": "thread_edge_test_001"
}

def make_payload(**kwargs):
    payload = VALID_TEMPLATE.copy()
    # Add unique run_id suffix to make test runs independent
    if "message_id" in payload:
        payload["message_id"] = f"{payload['message_id']}_{run_id}"
    for k, v in kwargs.items():
        if v is None:
            payload.pop(k, None)
        else:
            if k == "message_id":
                payload[k] = f"{v}_{run_id}"
            else:
                payload[k] = v
    return payload

def main():
    print("==================================================")
    print("Starting Ingestion Edge Case Hardening Validation")
    print("==================================================")

    test_cases = [
        # 1. Missing message_id
        {
            "name": "1. Missing message_id",
            "payload": make_payload(message_id=None),
            "expected_status": 422,
            "validate": lambda r: "message_id" in r.text or "VALIDATION_ERROR" in r.text
        },
        # 2. Missing sender
        {
            "name": "2. Missing sender",
            "payload": make_payload(sender=None),
            "expected_status": 422,
            "validate": lambda r: "sender" in r.text or "VALIDATION_ERROR" in r.text
        },
        # 3. Missing timestamp
        {
            "name": "3. Missing timestamp",
            "payload": make_payload(timestamp=None),
            "expected_status": 422,
            "validate": lambda r: "timestamp" in r.text or "VALIDATION_ERROR" in r.text
        },
        # 4. Invalid timestamp format
        {
            "name": "4. Invalid timestamp format",
            "payload": make_payload(timestamp="invalid-timestamp-format-1234"),
            "expected_status": 422,
            "validate": lambda r: "timestamp" in r.text or "VALIDATION_ERROR" in r.text
        },
        # 5. Empty subject (None/null)
        {
            "name": "5. Empty subject (None)",
            "payload": make_payload(message_id="edge_msg_005", subject=None),
            "expected_status": 200,
            "validate": lambda r: r.json().get("status") in ["Received", "Processing", "Escalated", "Spam", "Ignored"]
        },
        # 6. Empty body (None/null)
        {
            "name": "6. Empty body (None)",
            "payload": make_payload(message_id="edge_msg_006", body=None),
            "expected_status": 200,
            "validate": lambda r: r.json().get("status") in ["Received", "Processing", "Escalated", "Spam", "Ignored"]
        },
        # 7. Body with only whitespace
        {
            "name": "7. Body with only whitespace",
            "payload": make_payload(message_id="edge_msg_007", body="    \n   \t  "),
            "expected_status": 200,
            "validate": lambda r: r.json().get("status") in ["Received", "Processing", "Escalated", "Spam", "Ignored"]
        },
        # 8. Body with only HTML entities
        {
            "name": "8. Body with only HTML entities",
            "payload": make_payload(message_id="edge_msg_008", body="&amp;&nbsp;&lt;&gt;"),
            "expected_status": 200,
            "validate": lambda r: r.json().get("status") in ["Received", "Processing", "Escalated", "Spam", "Ignored"]
        },
        # 9. Extremely long body > 10,000 characters
        {
            "name": "9. Long body (>10k chars)",
            "payload": make_payload(message_id="edge_msg_009", body="A" * 12000),
            "expected_status": 200,
            "validate": lambda r: r.json().get("status") in ["Received", "Processing", "Escalated", "Spam", "Ignored"]
        },
        # 10. Duplicate message_id
        {
            "name": "10. Duplicate message_id",
            "payload": make_payload(message_id="edge_msg_009"),  # Already ingested in step 9
            "expected_status": 200,
            "validate": lambda r: r.json().get("status") == "duplicate_ignored"
        },
        # 11. Out-of-order timestamp within an existing thread
        {
            "name": "11. Out-of-order timestamp in thread",
            "payload": make_payload(
                message_id="edge_msg_011",
                timestamp="2020-01-01T00:00:00Z",  # Way older than 2026
                thread_id="thread_edge_test_001"  # Existing thread
            ),
            "expected_status": 200,
            "validate": lambda r: r.json().get("status") in ["Received", "Processing", "Escalated", "Spam", "Ignored"]
        },
        # 12. Unknown extra fields
        {
            "name": "12. Unknown extra fields",
            "payload": {
                **make_payload(message_id="edge_msg_012"),
                "unsupported_extra_field_abc": "ignored_value",
                "nested_extra": {"key": 123}
            },
            "expected_status": 200,
            "validate": lambda r: r.json().get("status") in ["Received", "Processing", "Escalated", "Spam", "Ignored"]
        }
    ]

    passed = 0
    failed = 0

    for tc in test_cases:
        name = tc["name"]
        payload = tc["payload"]
        expected_status = tc["expected_status"]
        validate_fn = tc["validate"]

        print(f"\nRunning: {name}")
        try:
            res = requests.post(BASE_URL, json=payload, timeout=5)
            status_ok = (res.status_code == expected_status)
            custom_ok = False
            if status_ok:
                try:
                    custom_ok = validate_fn(res)
                except Exception as ex:
                    print(f"  [ERROR] Validation function threw exception: {ex}")
            
            if status_ok and custom_ok:
                print(f"  --> PASS (Status: {res.status_code})")
                passed += 1
            else:
                print(f"  --> FAIL (Expected status {expected_status}, got {res.status_code})")
                print(f"  Response content: {res.text[:200]}")
                failed += 1
        except Exception as err:
            print(f"  --> FAIL (Connection error: {err})")
            failed += 1

    total = passed + failed
    print("\n==================================================")
    print("Final Edge-Case Hardening Summary")
    print("==================================================")
    print(f"Total Tests Run: {total}")
    print(f"Passed:         {passed}")
    print(f"Failed:         {failed}")
    print("==================================================")

    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
