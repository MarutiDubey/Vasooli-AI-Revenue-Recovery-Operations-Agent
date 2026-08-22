import hmac
import hashlib
import sqlite3
import os
import json
import logging
from fastapi import FastAPI, Request, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.state_mapper import process_webhook_event
from app.dashboard_api import router as dashboard_router

load_dotenv()

app = FastAPI(title="Vasooli - AI Revenue Recovery")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(dashboard_router)

RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "test_secret_123")
DB_PATH = "vasooli.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
def startup():
    from app.database import init_db
    init_db()
    logger.info("Database initialized successfully.")

@app.post("/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None, alias="x-razorpay-signature"),
    x_razorpay_event_id: str = Header(None, alias="x-razorpay-event-id"),
    x_vasooli_source: str = Header("RAZORPAY", alias="x-vasooli-source"),
    background_tasks: BackgroundTasks = None
):
    # Log incoming request
    logger.info(f"Received webhook event_id: {x_razorpay_event_id}")

    if not x_razorpay_signature:
        logger.error("Missing x-razorpay-signature header")
        raise HTTPException(status_code=400, detail="Missing signature")
        
    payload = await request.body()
    
    # 1. HMAC-SHA256 signature verification using raw payload
    expected_signature = hmac.new(
        key=RAZORPAY_WEBHOOK_SECRET.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected_signature, x_razorpay_signature):
        logger.error("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 2. Parse JSON
    try:
        data = json.loads(payload.decode('utf-8'))
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = data.get('event')
    
    # Fallback to get event_id from payload if header is missing
    event_id = x_razorpay_event_id or data.get('account_id', 'unknown') + "_" + event_type
    
    # Extract IDs safely
    payload_dict = data.get('payload', {})
    subscription_id = payload_dict.get('subscription', {}).get('entity', {}).get('id')
    payment_id = payload_dict.get('payment', {}).get('entity', {}).get('id')

    # Hash the payload to store it
    payload_hash = hashlib.sha256(payload).hexdigest()
    
    # 3. Store verified events with deduplication
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO webhook_events (event_id, event_type, subscription_id, payment_id, payload_hash, event_source)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (event_id, event_type, subscription_id, payment_id, payload_hash, x_vasooli_source))
        conn.commit()
        logger.info(f"Successfully stored new event {event_id} (Source: {x_vasooli_source})")
        if background_tasks:
            background_tasks.add_task(process_webhook_event, event_id, event_type, payload_dict)
    except sqlite3.IntegrityError:
        # Duplicate event_id, idempotent response (Requirement: return 200 within 5 seconds)
        logger.info(f"Duplicate event ignored: {event_id}")
        return {"status": "ok", "message": "Duplicate event ignored"}
    finally:
        conn.close()
        
    return {"status": "ok"}
