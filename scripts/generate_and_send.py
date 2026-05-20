import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────
# ENV VARIABLES
# ─────────────────────────────────────────

HF_API_KEY = os.environ["HF_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# ─────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────

OUTPUT_DIR = Path("outputs")
IMAGE_DIR = OUTPUT_DIR / "images"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)

POSTS_FILE = OUTPUT_DIR / "posts.json"

# ─────────────────────────────────────────
# HUGGING FACE
# ─────────────────────────────────────────

HF_MODELS = [
    "black-forest-labs/FLUX.1-schnell",
    "stabilityai/stable-diffusion-xl-base-1.0",
    "runwayml/stable-diffusion-v1-5"
]

HF_HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json",
    "x-wait-for-model": "true"
}

# ─────────────────────────────────────────
# TELEGRAM HELPERS
# ─────────────────────────────────────────

def tg_send_message(text):

    response = requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text[:4096],
            "parse_mode": "HTML"
        }
    )

    print("Telegram message:", response.status_code)

    return response.status_code == 200


def tg_send_photo(image_path, caption):

    with open(image_path, "rb") as f:

        response = requests.post(
            f"{TELEGRAM_API}/sendPhoto",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption[:1024],
                "parse_mode": "HTML"
            },
            files={
                "photo": f
            }
        )

    print("Telegram photo:", response.status_code)

    if response.status_code != 200:
        print(response.text)

    return response.status_code == 200

# ─────────────────────────────────────────
# IMAGE GENERATION
# ─────────────────────────────────────────

def generate_image_hf(prompt, filename):

    save_path = IMAGE_DIR / filename

    enhanced_prompt = (
        f"{prompt}, dark background, "
        f"professional DevOps style, "
        f"high quality, cinematic lighting, "
        f"modern cloud infrastructure aesthetic"
    )

    for model in HF_MODELS:

        print(f"Trying model: {model}")

        try:

            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=HF_HEADERS,
                json={
                    "inputs": enhanced_prompt
                },
                timeout=120
            )

            print("HF Status:", response.status_code)

            if response.status_code == 200:

                save_path.write_bytes(response.content)

                print(f"Saved image: {save_path}")

                return save_path

            else:
                print(response.text)

        except Exception as e:
            print("HF Error:", e)

        time.sleep(3)

    return None

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def generate():

    if not POSTS_FILE.exists():
        raise Exception("outputs/posts.json not found")

    data = json.loads(POSTS_FILE.read_text())

    posts = data.get("posts", [])

    print(f"Loaded {len(posts)} posts")

    tg_send_message(
        f"🚀 Testing Telegram + AI Images\n\n"
        f"Posts loaded: {len(posts)}"
    )

    for i, post in enumerate(posts, start=1):

        topic = post.get("topic", "DevOps")

        body = post.get("body", "")

        hashtags = post.get("hashtags", "#DevOps")

        prompt = post.get(
            "image_prompt",
            f"DevOps cloud infrastructure about {topic}"
        )

        print(f"\nGenerating image for: {topic}")

        filename = f"post_{i}.png"

        img_path = generate_image_hf(prompt, filename)

        caption = (
            f"<b>{topic}</b>\n\n"
            f"{hashtags}"
        )

        if img_path and img_path.exists():

            print("Sending image to Telegram...")

            tg_send_photo(img_path, caption)

        else:

            tg_send_message(
                f"⚠️ Failed image generation for:\n{topic}"
            )

        time.sleep(2)

        tg_send_message(body)

        time.sleep(2)

    tg_send_message("✅ Telegram image test completed")


if __name__ == "__main__":
    generate()
