import os
import requests

HF_API_KEY = os.environ["HF_API_KEY"]

MODELS = [
    "black-forest-labs/FLUX.1-schnell",
    "stabilityai/stable-diffusion-xl-base-1.0",
    "stabilityai/stable-diffusion-2-1",
]

headers = {
    "Authorization": f"Bearer {HF_API_KEY}",
}

prompt = "dark terminal screen showing kubernetes pod status, green text, professional devops illustration"

for model in MODELS:
    print(f"\n{'='*50}")
    print(f"Testing: {model}")
    try:
        r = requests.post(
            f"https://router.huggingface.co/hf-inference/models/{model}",  # NEW URL
            headers=headers,
            json={"inputs": prompt},
            timeout=60
        )
        print(f"Status      : {r.status_code}")
        print(f"Content-Type: {r.headers.get('content-type', 'none')}")
        print(f"Body size   : {len(r.content)} bytes")
        if "image" in r.headers.get("content-type", ""):
            print(f"RESULT      : ✅ IMAGE WORKS!")
        else:
            try:
                print(f"RESULT      : ❌ {r.json()}")
            except Exception:
                print(f"RESULT      : ❌ {r.text[:300]}")
    except Exception as e:
        print(f"RESULT      : ❌ Exception: {e}")
