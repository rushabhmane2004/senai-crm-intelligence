import os
import sys
import json
import time

# Add backend directory to Python path to import modules cleanly
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(script_dir)
backend_path = os.path.join(workspace_root, "backend")
sys.path.insert(0, backend_path)

try:
    from app.services.heuristic_classifier import classify_email_heuristically
except ImportError as e:
    print(f"Failed to import heuristic classifier: {e}")
    sys.exit(1)

# Scenario expectations based on requirements
SCENARIO_EXPECTATIONS = {
    "msg_038": {
        "category": "Security",
        "urgency": "Critical",
        "status": "Escalated",
        "priority_score": 100,
        "requires_human": True,
        "security_flag": True
    },
    "msg_052": {
        "category": "Compliance",
        "urgency": "Critical",
        "status": "Escalated",
        "requires_human": True,
        "routing_queue": "compliance"
    },
    "msg_020": {
        "category": "Legal",
        "urgency": "Critical",
        "status": "Escalated",
        "requires_human": True,
        "legal_flag": True
    },
    "msg_031": {
        "category": "Spam",
        "urgency": "Low",
        "status": "Spam",
        "priority_score": 5,
        "requires_human": False,
        "is_spam": True
    },
    "msg_017": {
        "category": "Internal",
        "urgency": "Low",
        "status": "Ignored",
        "requires_human": False,
        "is_internal": True
    },
    "msg_033": {
        "category": "Complaint",
        "urgency": "High",
        "status": "Escalated",
        "requires_human": True
    },
    "msg_041": {
        "category": "Billing",
        "urgency": "Medium",
        "status": "Processing"
    },
    "msg_060": {
        "category": "Legal",
        "urgency": "Critical",
        "status": "Escalated",
        "requires_human": True,
        "legal_flag": True
    }
}

def main():
    print("==================================================")
    print("Starting Heuristic Classifier Benchmark & Tests")
    print("==================================================")

    # 1. Load advanced email data
    json_path = os.path.join(workspace_root, "data", "email-data-advanced.json")
    if not os.path.exists(json_path):
        print(f"[FAIL] Missing dataset file at {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        emails = json.load(f)

    print(f"Loaded {len(emails)} emails from dataset.")

    # 2. Benchmark execution time
    times_ms = []
    classification_results = {}

    for email in emails:
        message_id = email["message_id"]
        sender = email["sender"]
        subject = email["subject"]
        body = email["body"]

        # Time block
        start = time.perf_counter()
        res = classify_email_heuristically(sender, subject, body)
        end = time.perf_counter()

        elapsed_ms = (end - start) * 1000
        times_ms.append(elapsed_ms)
        classification_results[message_id] = res

    # 3. Print validation for scenario expectations
    passed_tests = 0
    failed_tests = 0

    print("\n--- Validating Scenario Expectations ---")
    for message_id, expected in SCENARIO_EXPECTATIONS.items():
        actual = classification_results.get(message_id)
        if not actual:
            print(f"[{message_id}] FAIL: Email not found in dataset results")
            failed_tests += 1
            continue

        errors = []
        for key, expected_val in expected.items():
            actual_val = actual.get(key)
            if actual_val != expected_val:
                errors.append(f"Field '{key}': expected {expected_val}, got {actual_val}")

        if not errors:
            print(f"[{message_id}] PASS")
            passed_tests += 1
        else:
            print(f"[{message_id}] FAIL:")
            for err in errors:
                print(f"  - {err}")
            failed_tests += 1

    # 4. Print benchmark stats
    total_emails = len(emails)
    total_elapsed_ms = sum(times_ms)
    avg_ms = total_elapsed_ms / total_emails
    max_ms = max(times_ms)
    is_under_10ms = avg_ms < 10.0

    print("\n--- Speed Performance Benchmark ---")
    print(f"Total Emails Benchmarked: {total_emails}")
    print(f"Total Elapsed Time:       {total_elapsed_ms:.3f} ms")
    print(f"Average Time Per Email:   {avg_ms:.3f} ms")
    print(f"Max Classification Time:  {max_ms:.3f} ms")
    print(f"Avg Time Under 10ms?:     {'YES' if is_under_10ms else 'NO'}")
    print("==================================================")

    # 5. Determine overall exit status
    if failed_tests > 0:
        print("[FAIL] One or more scenario expectation checks failed.")
        sys.exit(1)
    if not is_under_10ms:
        print("[FAIL] Average classification time exceeded the 10ms threshold.")
        sys.exit(1)

    print("[SUCCESS] All scenario validation checks and speed benchmarks passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
