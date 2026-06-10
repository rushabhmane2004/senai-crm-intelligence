import os
import sys
import time
import urllib.parse
import requests
import subprocess

# Set paths
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(script_dir)
backend_path = os.path.join(workspace_root, "backend")

server_process = None

SCENARIOS = [
    {
        "name": "1. Karen Refund + Public Review Escalation",
        "query": "refund public review escalation retention playbook G2 Trustpilot",
        "expected": ["refund_policy.md", "escalation_matrix.md"]
    },
    {
        "name": "2. GDPR Article 20 Compliance Escalation",
        "query": "GDPR Article 20 data portability 30-day statutory window compliance escalation",
        "expected": ["compliance_faq.md", "escalation_matrix.md"]
    },
    {
        "name": "3. Bob SLA Legal Escalation",
        "query": "SLA breach RCA 24 hours downtime credit legal review renewal on hold",
        "expected": ["sla_policy.md", "escalation_matrix.md"]
    },
    {
        "name": "4. Alice Pro-rata Billing",
        "query": "nonprofit discount Standard plan pro-rata billing mid-cycle seat additions",
        "expected": ["pricing_policy.md"]
    },
    {
        "name": "5. API v2 / 403 / X-Workspace-ID",
        "query": "API v2 403 X-Workspace-ID header permission scope rate limit",
        "expected": ["api_docs.md"]
    },
    {
        "name": "6. Chatbot Misinformation Refund",
        "query": "chatbot misinformation prorated refund cancellation policy legal liability",
        "expected": ["refund_policy.md", "escalation_matrix.md"]
    }
]

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
    print("Starting RAG Quality Validation Benchmarks")
    print("==================================================")

    # Try connecting to port 8000. If not running, spin it up.
    try:
        requests.get("http://127.0.0.1:8000/health", timeout=1)
        print("Found existing backend server running on port 8000.")
    except requests.exceptions.RequestException:
        print("Starting backend server locally...")
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

    all_passed = True

    for scenario in SCENARIOS:
        name = scenario["name"]
        query = scenario["query"]
        expected = scenario["expected"]

        print(f"\nScenario: {name}")
        print(f"  Query:    \"{query}\"")
        print(f"  Expected: {expected}")

        try:
            url = f"http://127.0.0.1:8000/rag/search?q={urllib.parse.quote(query)}&top_k=3"
            resp = requests.get(url, timeout=30)
            if resp.status_code != 200:
                print(f"  --> FAIL (HTTP Status: {resp.status_code})")
                print(f"      Response: {resp.text}")
                all_passed = False
                continue

            data = resp.json()
            results = data.get("results", [])
            retrieved_docs = [r["source_doc"] for r in results]

            print("  Retrieved Top-3 Chunks:")
            for idx, r in enumerate(results):
                print(f"    [{idx+1}] Doc: {r['source_doc']} (Similarity: {r.get('similarity_score', 0.0)}) - {r.get('policy_ref')}")

            # Verify presence of expected docs in retrieved_docs
            scenario_passed = True
            missing_docs = []
            for exp_doc in expected:
                if exp_doc not in retrieved_docs:
                    scenario_passed = False
                    missing_docs.append(exp_doc)

            if scenario_passed:
                print("  --> PASS")
            else:
                print(f"  --> FAIL (Missing expected documents: {missing_docs})")
                all_passed = False

        except Exception as e:
            print(f"  --> FAIL (Exception: {e})")
            all_passed = False

    print("\n==================================================")
    print("RAG Quality Validation Summary")
    print("==================================================")
    if all_passed:
        print("[SUCCESS] All RAG quality scenarios passed successfully!")
        cleanup_and_exit(0)
    else:
        print("[FAIL] One or more RAG quality validation checks failed.")
        cleanup_and_exit(1)

if __name__ == "__main__":
    main()
