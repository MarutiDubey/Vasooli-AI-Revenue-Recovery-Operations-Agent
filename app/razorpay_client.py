import os
import requests
import logging

logger = logging.getLogger(__name__)

def create_payment_link(amount: int, customer_name: str, customer_email: str, customer_contact: str, description: str):
    """
    Creates a Razorpay Payment Link using standard API.
    If keys are missing, simulates the API call.
    """
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    
    if not key_id or not key_secret:
        logger.warning("Razorpay API Keys missing. Simulating Payment Link Creation.")
        return {
            "id": "plink_sim_000000001",
            "short_url": "https://rzp.io/i/sim_plink",
            "status": "created"
        }
        
    url = "https://api.razorpay.com/v1/payment_links"
    payload = {
        "amount": amount,
        "currency": "INR",
        "accept_partial": False,
        "description": description,
        "customer": {
            "name": customer_name,
            "email": customer_email,
            "contact": customer_contact
        },
        "notify": {
            "sms": True,
            "email": True
        },
        "reminder_enable": True
    }
    
    try:
        response = requests.post(url, json=payload, auth=(key_id, key_secret), timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Failed to create Razorpay Payment Link: {e} | Response: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Failed to create Razorpay Payment Link: {e}")
        return None
