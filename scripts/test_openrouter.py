import requests

import os

API_KEY = os.getenv("TOKENIN_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://tokenin.my.id/v1"

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

# Only test working models - get actual response content
working_models = [
    'myt/gemini-3.5-flash-free',
    'myt/kimi-k3-free',
    'myt/mimo-v2.5-free',
    'myt/gpt-5.6-sol-free',
]

print("Detail test of working models...\n")

prompt = """You are a payment failure analyst. A customer's subscription payment failed.
Failure reason: insufficient_funds - bank declined due to insufficient balance.
Customer history: 8 successful payments, 1 failure, tenure 180 days.
Analyze this and recommend ONE action: MONITOR, ONE_TIME_RECOVERY, ESCALATE, or STOP.
Keep response under 50 words."""

for model in working_models:
    data = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 100
    }
    try:
        resp = requests.post(
            f'{BASE_URL}/chat/completions',
            headers=headers, json=data, timeout=30
        )
        if resp.status_code == 200:
            j = resp.json()
            content = j.get('choices', [{}])[0].get('message', {}).get('content', '')
            tokens = j.get('usage', {})
            print(f"[OK] {model}")
            print(f"     Reply: {content.strip()[:150]}")
            print(f"     Tokens: {tokens}")
        else:
            print(f"[FAIL] {model}: {resp.text[:100]}")
    except Exception as e:
        print(f"[ERR] {model}: {e}")
    print()
