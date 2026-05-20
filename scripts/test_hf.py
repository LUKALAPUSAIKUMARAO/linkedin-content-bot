import os
import requests

HF_API_KEY = os.environ["HF_API_KEY"]

MODELS = [
    "black-forest-labs/FLUX.1-schnell",
    "stabilityai/stable-diffusion-xl-base-1.0",
    "stabilityai/stable-diffusion-2-1",
    "stabilityai/sdxl-turbo",
    "nerijs/pixel-art-xl",
]

headers = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "x-wait-for-model": "true"
}

prompt = "dark terminal screen showing kubernetes pod status, green text, professional devops illustration"

for model in MODELS:
    print(f"\n{'='*50}")
    print(f"Testing: {model}")
    print(f"{'='*50}")
    try:
        r = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers={**headers, "Content-Type": "application/json"},
            json={
                "inputs": prompt,
                "options": {"wait_for_model": True}
            },
            timeout=60
        )
        print(f"Status     : {r.status_code}")
        print(f"Content-Type: {r.headers.get('content-type', 'none')}")
        print(f"Body size  : {len(r.content)} bytes")
        if "image" in r.headers.get("content-type", ""):
            print(f"RESULT     : ✅ IMAGE RECEIVED — this model works!")
        else:
            try:
                print(f"RESULT     : ❌ JSON response: {r.json()}")
            except Exception:
                print(f"RESULT     : ❌ Non-image response: {r.text[:300]}")
    except Exception as e:
        print(f"RESULT     : ❌ Exception: {e}")
