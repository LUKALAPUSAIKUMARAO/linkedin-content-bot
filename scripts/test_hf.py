import os
import requests
from pathlib import Path

HF_API_KEY         = os.environ["HF_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]
TELEGRAM_API       = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

HF_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

IMAGE_PATH = Path("outputs/images/test_image.jpg")
IMAGE_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── STEP 1: Generate image ──────────────────────────
print("\n── STEP 1: Generate image via FLUX ──")
r = requests.post(
    HF_URL,
    headers={
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
    },
    json={"inputs": "dark kubernetes dashboard, green terminal text, professional devops illustration"},
    timeout=120
)
print(f"Status      : {r.status_code}")
print(f"Content-Type: {r.headers.get('content-type')}")
print(f"Size        : {len(r.content)} bytes")

if r.status_code != 200 or "image" not in r.headers.get("content-type", ""):
    print("FAILED at image generation — stopping here")
    exit(1)

# ── STEP 2: Save to disk ────────────────────────────
print("\n── STEP 2: Save image to disk ──")
IMAGE_PATH.write_bytes(r.content)
print(f"Saved to    : {IMAGE_PATH}")
print(f"File exists : {IMAGE_PATH.exists()}")
print(f"File size   : {IMAGE_PATH.stat().st_size} bytes")

# ── STEP 3: Send text message to Telegram ──────────
print("\n── STEP 3: Send text message to Telegram ──")
r2 = requests.post(
    f"{TELEGRAM_API}/sendMessage",
    json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "🧪 Test message from LinkedIn bot — if you see this, Telegram is working"
    },
    timeout=15
)
print(f"Status      : {r2.status_code}")
print(f"Response    : {r2.text[:300]}")

# ── STEP 4: Send image as photo ─────────────────────
print("\n── STEP 4: Send image as photo to Telegram ──")
with open(IMAGE_PATH, "rb") as f:
    r3 = requests.post(
        f"{TELEGRAM_API}/sendPhoto",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": "🧪 Test image from FLUX.1-schnell — DevOps bot working!"
        },
        files={"photo": ("test.jpg", f, "image/jpeg")},
        timeout=60
    )
print(f"Status      : {r3.status_code}")
print(f"Response    : {r3.text[:500]}")

if r3.status_code == 200:
    print("\n✅ FULL PIPELINE WORKS — image generated and sent to Telegram")
else:
    print("\n❌ FAILED at Telegram photo send — see response above")
