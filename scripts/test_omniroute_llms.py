import requests
import time

BASE_URL = "http://localhost:20128/v1"

models_to_test = [
    "auto",
    "oc/big-pickle",
    "felo/auto"
]

prompt = "Hello, this is a test. Are you receiving me? Reply with just 'Yes'."

for model in models_to_test:
    print(f"Testing model: {model} ...")
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 50
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/chat/completions", json=data, timeout=30)
        if resp.status_code == 200:
            j = resp.json()
            content = j.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"[OK] {model}")
            print(f"     Reply: {content.strip()}")
        else:
            print(f"[FAIL] {model}: Status {resp.status_code} - {resp.text[:200]}")
    except Exception as e:
        print(f"[ERROR] {model}: {e}")
    print("-" * 40)
    time.sleep(1)
