import os
import time
import json
import argparse
import requests

def main():
    parser = argparse.ArgumentParser(description="Stream mock email data to the ingestion API.")
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Speed multiplier. Delay between emails is calculated as 1.0 / speed seconds (default: 1.0)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000/api/ingest",
        help="API URL to post payloads to (default: http://localhost:8000/api/ingest)"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to JSON file containing email data (default: searches in data/email-data-advanced.json)"
    )
    args = parser.parse_args()

    # Determine data file path
    data_file = args.file
    if not data_file:
        # Resolve path relative to script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(script_dir, "..", "data", "email-data-advanced.json")

    # Ensure files exists
    if not os.path.exists(data_file):
        print(f"Error: Email data file not found at '{os.path.abspath(data_file)}'")
        return

    # Load emails data
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            emails = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return

    print(f"Successfully loaded {len(emails)} emails from {data_file}")
    print(f"Starting simulation at speed multiplier {args.speed} (delay = {1.0 / args.speed:.3f} seconds per email)...")
    print("-" * 80)

    success_count = 0
    fail_count = 0

    for idx, email in enumerate(emails):
        message_id = email.get("message_id", "unknown")
        
        # Prepare post headers and payload
        try:
            response = requests.post(
                args.url,
                json=email,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                res_data = response.json()
                ingest_status = res_data.get("status", "unknown")
                priority = res_data.get("priority_score", 0)
                print(f"[{idx+1}/{len(emails)}] Sent message_id: {message_id} | Ingestion Status: {ingest_status} | Priority: {priority}")
                success_count += 1
            else:
                print(f"[{idx+1}/{len(emails)}] Failed to ingest message_id: {message_id} | HTTP {response.status_code}")
                try:
                    err_payload = response.json()
                    print(f"  Error: {err_payload.get('error_code')} - {err_payload.get('message')}")
                    if err_payload.get("details"):
                        print(f"  Details: {err_payload.get('details')}")
                except Exception:
                    print(f"  Raw Body: {response.text}")
                fail_count += 1
        except requests.exceptions.RequestException as req_err:
            print(f"[{idx+1}/{len(emails)}] Network Error while sending message_id: {message_id}")
            print(f"  Exception Details: {req_err}")
            fail_count += 1

        # Control streaming speed
        if idx < len(emails) - 1:
            time.sleep(1.0 / args.speed)

    print("-" * 80)
    print(f"Simulation completed. Total: {len(emails)} | Success: {success_count} | Failures: {fail_count}")

if __name__ == "__main__":
    main()
