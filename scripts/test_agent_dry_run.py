import os
import sys
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
    print("Starting Autonomous Agent Dry-Run Verification")
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

    # Scenario 1: msg_060 (Bob Jones SLA / Legal Escalation)
    print("\nScenario: msg_060 (Bob Jones SLA / Legal Escalation)")
    try:
        url = "http://127.0.0.1:8000/agent/dry-run/msg_060"
        resp = requests.post(url, timeout=30)
        if resp.status_code != 200:
            print(f"  --> FAIL (HTTP Status: {resp.status_code})")
            print(f"      Response: {resp.text}")
            all_passed = False
        else:
            data = resp.json()
            
            # Assertions:
            # - dry_run true
            # - tool_trace length > 0
            # - tool_call_count <= 6
            # - auto_reply_allowed false
            # - escalation_team includes legal
            # - human_escalation_brief contains SLA or RCA or renewal
            # - account_status contains Enterprise or renewal on hold
            assert data.get("dry_run") is True, f"dry_run should be True, got {data.get('dry_run')}"
            assert len(data.get("tool_trace", [])) > 0, "tool_trace should be non-empty"
            assert data.get("tool_call_count", 0) <= 6, f"tool_call_count should be <= 6, got {data.get('tool_call_count')}"
            assert data.get("auto_reply_allowed") is False, "auto_reply_allowed should be False"
            
            esc_team = (data.get("escalation_team") or "").lower()
            assert "legal" in esc_team, f"escalation_team should contain legal, got {esc_team}"
            
            brief = (data.get("human_escalation_brief") or "").lower()
            assert any(x in brief for x in ["sla", "rca", "renewal"]), f"human_escalation_brief should contain SLA, RCA, or renewal, got {brief}"
            
            status = data.get("account_status") or {}
            status_str = str(status).lower()
            assert any(x in status_str for x in ["enterprise", "renewal on hold"]), f"account_status should contain Enterprise or renewal on hold, got {status_str}"
            
            # Additional trace audits
            trace_actions = [step["action"] for step in data.get("tool_trace", [])]
            assert "get_thread_history" in trace_actions, "get_thread_history tool should be in trace"
            assert "search_knowledge_base" in trace_actions, "search_knowledge_base tool should be in trace"
            assert "check_account_status" in trace_actions, "check_account_status tool should be in trace"
            assert "flag_for_legal" in trace_actions, "flag_for_legal tool should be in trace"
            assert "create_internal_ticket" in trace_actions, "create_internal_ticket tool should be in trace"
            
            print("  --> PASS")
    except Exception as e:
        print(f"  --> FAIL (Exception: {e})")
        all_passed = False

    # Scenario 2: msg_038 (Ransomware)
    print("\nScenario: msg_038 (Ransomware)")
    try:
        url = "http://127.0.0.1:8000/agent/dry-run/msg_038"
        resp = requests.post(url, timeout=30)
        if resp.status_code != 200:
            print(f"  --> FAIL (HTTP Status: {resp.status_code})")
            print(f"      Response: {resp.text}")
            all_passed = False
        else:
            data = resp.json()
            
            # Assertions:
            # - auto_reply_allowed false
            # - escalation_team security
            # - safety blocked/restricted
            assert data.get("auto_reply_allowed") is False, "auto_reply_allowed should be False"
            assert (data.get("escalation_team") or "").lower() == "security", f"escalation_team should be security, got {data.get('escalation_team')}"
            assert data.get("safety_level") in ["blocked", "restricted"], f"safety_level should be blocked/restricted, got {data.get('safety_level')}"
            
            print("  --> PASS")
    except Exception as e:
        print(f"  --> FAIL (Exception: {e})")
        all_passed = False

    # Scenario 3: msg_052 (GDPR / Compliance)
    print("\nScenario: msg_052 (GDPR / Compliance)")
    try:
        url = "http://127.0.0.1:8000/agent/dry-run/msg_052"
        resp = requests.post(url, timeout=30)
        if resp.status_code != 200:
            print(f"  --> FAIL (HTTP Status: {resp.status_code})")
            print(f"      Response: {resp.text}")
            all_passed = False
        else:
            data = resp.json()
            
            # Assertions:
            # - category/compliance indication or escalation_team compliance/legal
            # - 30-day window present somewhere in response OR policy_sources include compliance_faq.md
            # - auto_reply_allowed false or requires_human_approval true
            esc_team = (data.get("escalation_team") or "").lower()
            decision = (data.get("decision") or "").lower()
            assert "compliance" in esc_team or "legal" in esc_team or "compliance" in decision, f"Should be compliance/legal escalated, got esc_team={esc_team}, decision={decision}"
            
            body_or_brief = str(data).lower()
            policy_sources = [p.lower() for p in data.get("policy_sources_used", [])]
            assert "30-day" in body_or_brief or "compliance_faq.md" in policy_sources, f"Should contain 30-day window or compliance_faq.md"
            
            assert data.get("auto_reply_allowed") is False or data.get("requires_human_approval") is True, "auto_reply_allowed should be False OR requires_human_approval True"
            
            print("  --> PASS")
    except Exception as e:
        print(f"  --> FAIL (Exception: {e})")
        all_passed = False

    # Scenario 4: msg_041 (Billing Query)
    print("\nScenario: msg_041 (Billing Query)")
    try:
        url = "http://127.0.0.1:8000/agent/dry-run/msg_041"
        resp = requests.post(url, timeout=30)
        if resp.status_code != 200:
            print(f"  --> FAIL (HTTP Status: {resp.status_code})")
            print(f"      Response: {resp.text}")
            all_passed = False
        else:
            data = resp.json()
            
            # Assertions:
            # - category Billing or decision billing
            # - draft_reply not null or auto_reply_allowed true
            # - policy_sources include pricing_policy.md if available
            decision = (data.get("decision") or "").lower()
            esc_team = (data.get("escalation_team") or "").lower()
            assert "billing" in decision or "billing" in esc_team, f"Should be billing decision, got decision={decision}, esc_team={esc_team}"
            
            assert data.get("draft_reply") is not None or data.get("auto_reply_allowed") is True, "draft_reply should not be null OR auto_reply_allowed True"
            
            policy_sources = [p.lower() for p in data.get("policy_sources_used", [])]
            assert "pricing_policy.md" in policy_sources, f"policy_sources should contain pricing_policy.md, got {policy_sources}"
            
            print("  --> PASS")
    except Exception as e:
        print(f"  --> FAIL (Exception: {e})")
        all_passed = False

    print("\n==================================================")
    print("Autonomous Agent Dry-Run Verification Summary")
    print("==================================================")
    if all_passed:
        print("[SUCCESS] All autonomous agent dry-run validation checks passed!")
        cleanup_and_exit(0)
    else:
        print("[FAIL] One or more dry-run validation checks failed.")
        cleanup_and_exit(1)

if __name__ == "__main__":
    main()
