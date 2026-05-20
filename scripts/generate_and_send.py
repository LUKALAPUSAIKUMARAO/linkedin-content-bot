import os
import json
import time
import requests
from pathlib import Path

# ─────────────────────────────────────────
# ENV
# ─────────────────────────────────────────

HF_API_KEY = os.environ["HF_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# ─────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────

OUTPUT_DIR = Path("outputs")
POSTS_FILE = OUTPUT_DIR / "posts.json"

IMAGE_DIR = OUTPUT_DIR / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────
# HF MODELS
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
# TELEGRAM
# ─────────────────────────────────────────

def tg_send_message(text):

    response = requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text[:4096]
        }
    )

    print("Telegram message:", response.status_code)

    if response.status_code != 200:
        print(response.text)

    return response.status_code == 200


def tg_send_photo(image_path, caption):

    with open(image_path, "rb") as f:

        response = requests.post(
            f"{TELEGRAM_API}/sendPhoto",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption[:1024]
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

def generate_image(prompt, filename):

    save_path = IMAGE_DIR / filename

    enhanced_prompt = (
        f"{prompt}, dark background, "
        f"DevOps illustration, cinematic lighting, "
        f"cloud infrastructure, modern UI"
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

            print("HF status:", response.status_code)

            if response.status_code == 200:

                content_type = response.headers.get(
                    "content-type",
                    ""
                )

                print("Content-Type:", content_type)

                if "image" in content_type:

                    save_path.write_bytes(response.content)

                    print(f"Saved image: {save_path}")

                    return save_path

                else:
                    print("HF did not return image")
                    print(response.text[:500])

            else:
                print(response.text[:500])

        except Exception as e:
            print("HF Error:", e)

        time.sleep(3)

    return None

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main():

    print("STARTING TELEGRAM TEST")

    if not POSTS_FILE.exists():
        raise Exception("outputs/posts.json not found")

    data = json.loads(POSTS_FILE.read_text())

    posts = data.get("posts", [])

    print(f"Loaded {len(posts)} posts")

    tg_send_message(
        f"🚀 Telegram image workflow started\nPosts: {len(posts)}"
    )

    for i, post in enumerate(posts, start=1):

        topic = post.get("topic", "DevOps")

        body = post.get("body", "")

        hashtags = post.get("hashtags", "#DevOps")

        prompt = post.get(
            "image_prompt",
            f"DevOps cloud illustration about {topic}"
        )

        print(f"\nProcessing: {topic}")

        filename = f"post_{i}.png"

        img_path = generate_image(prompt, filename)

        caption = f"{topic}\n\n{hashtags}"

        if img_path and img_path.exists():

            print("Sending image...")

            tg_send_photo(img_path, caption)

        else:

            tg_send_message(
                f"⚠️ Image generation failed:\n{topic}"
            )

        time.sleep(2)

        tg_send_message(body[:3500])

        time.sleep(2)

    tg_send_message("✅ Workflow completed")

    print("DONE")


if __name__ == "__main__":
    main()
