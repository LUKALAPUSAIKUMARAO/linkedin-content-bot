import os
import json
import time
import requests
from pathlib import Path

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
POSTS_FILE = OUTPUT_DIR / "posts.json"

IMAGE_DIR = OUTPUT_DIR / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────
# HUGGING FACE MODELS
# ─────────────────────────────────────────

HF_MODELS = [
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
            "text": text[:4096]
        },
        timeout=30
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
            },
            timeout=120
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
        f"{prompt}, "
        f"dark background, "
        f"professional DevOps illustration, "
        f"cloud infrastructure, "
        f"cinematic lighting, "
        f"high quality, "
        f"modern UI dashboard, "
        f"cyberpunk style"
    )

    for model in HF_MODELS:

        print(f"\nTrying model: {model}")

        try:

            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=HF_HEADERS,
                json={
                    "inputs": enhanced_prompt,
                    "options": {
                        "wait_for_model": True
                    }
                },
                timeout=300
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

                    print("HF returned non-image response")

                    try:
                        print(response.json())
                    except:
                        print(response.text[:500])

            else:

                print("HF error response:")

                try:
                    print(response.json())
                except:
                    print(response.text[:500])

        except Exception as e:

            print("HF Error:", e)

        time.sleep(5)

    return None

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main():

    print("STARTING TELEGRAM + IMAGE WORKFLOW")

    if not POSTS_FILE.exists():
        raise Exception("outputs/posts.json not found")

    data = json.loads(POSTS_FILE.read_text())

    posts = data.get("posts", [])

    print(f"Loaded {len(posts)} posts")

    tg_send_message(
        f"🚀 Telegram image workflow started\n\n"
        f"Posts loaded: {len(posts)}"
    )

    for i, post in enumerate(posts, start=1):

        topic = post.get("topic", "DevOps")

        body = post.get("body", "")

        hashtags = post.get("hashtags", "#DevOps")

        prompt = post.get(
            "image_prompt",
            f"DevOps cloud illustration about {topic}"
        )

        print(f"\nProcessing post {i}: {topic}")

        filename = f"post_{i}.png"

        img_path = generate_image(prompt, filename)

        caption = (
            f"{topic}\n\n"
            f"{hashtags}"
        )

        if img_path and img_path.exists():

            print("Sending image to Telegram...")

            tg_send_photo(img_path, caption)

        else:

            print("Image generation failed")

            tg_send_message(
                f"⚠️ Failed image generation:\n{topic}"
            )

        time.sleep(2)

        print("Sending post text...")

        tg_send_message(body[:3500])

        time.sleep(2)

    tg_send_message("✅ Workflow completed successfully")

    print("DONE")

# ─────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────

if __name__ == "__main__":
    main()
