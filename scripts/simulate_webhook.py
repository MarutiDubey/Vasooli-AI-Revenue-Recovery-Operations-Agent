import argparse
import json
import os
import time
import uuid
import hmac
import hashlib
import requests
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "vasooli_test_secret_2026")
WEBHOOK_URL = "http://localhost:8000/webhook/razorpay"

def main():
    parser = argparse.ArgumentParser(description="Simulate Razorpay Webhooks")
    parser.add_argument("event_type", choices=[
        "subscription.pending", 
        "subscription.halted", 
        "subscription.charged", 
        "payment.failed"
    ], help="Type of webhook event to simulate")
    
    args = parser.parse_args()
    
    fixture_path = os.path.join(os.path.dirname(__file__), f"fixtures/{args.event_type}.json")
    
    if not os.path.exists(fixture_path):
        print(f"Error: Fixture for {args.event_type} not found at {fixture_path}")
        return

    with open(fixture_path, 'r') as f:
        payload = json.load(f)

    # Make it unique and current
    current_time = int(time.time())
    payload["created_at"] = current_time
    
    if "subscription" in payload.get("payload", {}):
        payload["payload"]["subscription"]["entity"]["charge_at"] = current_time

    raw_body = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    
    signature = hmac.new(
        key=RAZORPAY_WEBHOOK_SECRET.encode('utf-8'),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    event_id = f"evt_sim_{uuid.uuid4().hex[:16]}"
    
    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": signature,
        "X-Razorpay-Event-Id": event_id,
        "X-Vasooli-Source": "SIMULATOR"
    }

    print(f"Sending {args.event_type} (Event ID: {event_id}) to {WEBHOOK_URL}...")
    
    try:
        response = requests.post(WEBHOOK_URL, data=raw_body, headers=headers)
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {WEBHOOK_URL}. Is the FastAPI server running?")

if __name__ == "__main__":
    main()
