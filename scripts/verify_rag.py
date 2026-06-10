import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_query(q, top_k=3):
    print(f"\n--- Testing Search Query: '{q}' ---")
    url = f"{BASE_URL}/rag/search"
    res = requests.get(url, params={"q": q, "top_k": top_k})
    if res.status_code == 200:
        data = res.json()
        print(f"Query: {data.get('query')}")
        print(f"Top K: {data.get('top_k')}")
        for idx, r in enumerate(data.get("results", [])):
            print(f"  [{idx+1}] Source: {r.get('source_doc')} | Ref: {r.get('policy_ref')} | Score: {r.get('similarity_score')}")
            # print first 100 characters of chunk
            preview = r.get("chunk_text", "").replace("\n", " ")[:120]
            print(f"      Text: {preview}...")
    else:
        print(f"Search failed: {res.status_code} - {res.text}")

def test_ingestion(email_payload):
    print(f"\n--- Ingesting Email: {email_payload['message_id']} ---")
    ingest_url = f"{BASE_URL}/api/ingest"
    res = requests.post(ingest_url, json=email_payload)
    if res.status_code == 200:
        ingest_res = res.json()
        print(f"Ingested successfully: {ingest_res.get('status')}")
    else:
        print(f"Ingestion failed: {res.status_code} - {res.text}")
        return

    # Check status and raw_entities
    status_url = f"{BASE_URL}/api/status/{email_payload['message_id']}"
    status_res = requests.get(status_url)
    if status_res.status_code == 200:
        status_data = status_res.json()
        raw_entities = status_data.get("raw_entities", {})
        print(f"Category: {status_data.get('category')} | Urgency: {status_data.get('urgency')} | Status: {status_data.get('status')}")
        print(f"RAG Used: {raw_entities.get('rag_used')}")
        if raw_entities.get("rag_used"):
            print(f"  RAG Query: '{raw_entities.get('rag_query')}'")
            print("  RAG Context:")
            for ctx in raw_entities.get("rag_context", []):
                print(f"    - Source: {ctx.get('source_doc')} | Ref: {ctx.get('policy_ref')} | Score: {ctx.get('similarity_score')}")
                print(f"      Preview: {ctx.get('chunk_preview')[:100]}...")
        else:
            print(f"  RAG Skip Reason: {raw_entities.get('rag_skip_reason')}")
            if "rag_error" in raw_entities:
                print(f"  RAG Error: {raw_entities.get('rag_error')}")
    else:
        print(f"Status check failed: {status_res.status_code} - {status_res.text}")

def main():
    print("Starting Phase 3 Verification Script against port 8001...")
    
    # 1. Test the search queries requested in the prompt
    test_queries = [
        "refund public review escalation",
        "GDPR Article 20 data portability 30-day statutory window",
        "SLA breach RCA 24 hours downtime credit",
        "API v2 403 X-Workspace-ID",
        "nonprofit discount pro-rata billing",
        "ransomware never auto-reply escalation"
    ]
    for q in test_queries:
        test_query(q)

    # 2. Test email ingestion for GDPR Right to Portability (msg_052_test - should use RAG)
    gdpr_email = {
        "message_id": "msg_052_test",
        "sender": "marcus.del@fintech-startup.co",
        "subject": "Data Export: GDPR Right to Portability Request",
        "body": "Under GDPR Article 20, I am formally requesting a complete export of all personal data your platform holds about me (account: marcus.del@fintech-startup.co). Please provide this within the statutory 30-day window.",
        "timestamp": "2023-10-17T08:00:00Z",
        "thread_id": "thread_gdpr_001_test"
    }
    test_ingestion(gdpr_email)

    # 3. Test email ingestion for Spam cold outreach (msg_003_test - should NOT use RAG)
    spam_email = {
        "message_id": "msg_003_test",
        "sender": "spam.bot@marketing-guru.io",
        "subject": "Boost your SEO by 300%",
        "body": "Dear Sir/Madam, we can get you on the front page of Google in 24 hours for just $99. Limited offer! Click here to claim.",
        "timestamp": "2023-10-01T09:30:00Z",
        "thread_id": "thread_spam_001_test"
    }
    test_ingestion(spam_email)

if __name__ == "__main__":
    main()
