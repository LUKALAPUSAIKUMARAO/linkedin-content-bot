import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────────────────
# SAFE ENVIRONMENT VARIABLES
# ─────────────────────────────────────────────────────────

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HF_API_KEY = os.getenv("HF_API_KEY")

missing = []

if not TELEGRAM_TOKEN:
    missing.append("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_CHAT_ID:
    missing.append("TELEGRAM_CHAT_ID")

if not HF_API_KEY:
    missing.append("HF_API_KEY")

if missing:
    raise Exception(
        f"Missing required GitHub secrets: {', '.join(missing)}"
    )

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ─────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────

IMAGE_DIR = Path("outputs/images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────
# HUGGING FACE MODELS
# ─────────────────────────────────────────────────────────

HF_MODELS = [
    "black-forest-labs/FLUX.1-schnell",
    "stabilityai/stable-diffusion-xl-base-1.0",
    "runwayml/stable-diffusion-v1-5",
]

HF_HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json",
    "x-wait-for-model": "true"
}

# ─────────────────────────────────────────────────────────
# IMAGE GENERATION
# ─────────────────────────────────────────────────────────

def build_devops_prompt(raw_prompt: str) -> str:
    style_suffix = (
        "dark background, professional tech aesthetic, "
        "high resolution, cinematic lighting, "
        "modern UI design, ultra detailed, "
        "no watermark, no text overlays"
    )

    return f"{raw_prompt}. {style_suffix}"


def generate_image_hf(prompt: str, filename: str):

    enhanced_prompt = build_devops_prompt(prompt)

    save_path = IMAGE_DIR / filename

    for model in HF_MODELS:

        api_url = f"https://api-inference.huggingface.co/models/{model}"

        print(f"Trying model: {model}")

        try:

            response = requests.post(
                api_url,
                headers=HF_HEADERS,
                json={
                    "inputs": enhanced_prompt,
                    "parameters": {
                        "width": 1200,
                        "height": 628,
                        "num_inference_steps": 20,
                        "guidance_scale": 7.5
                    }
                },
                timeout=90
            )

            if response.status_code == 200:

                content_type = response.headers.get("content-type", "")

                if "image" in content_type or len(response.content) > 5000:

                    save_path.write_bytes(response.content)

                    print(f"✓ Saved image: {filename}")

                    return save_path

                else:
                    print("✗ Response was not image")

            elif response.status_code == 503:
                print("✗ Model loading")

            elif response.status_code == 429:
                print("✗ Rate limited")
                time.sleep(15)

            else:
                print(f"✗ HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            print("✗ Timeout")

        except Exception as e:
            print(f"✗ Exception: {e}")

        time.sleep(3)

    print(f"✗ Failed image generation: {filename}")

    return None

# ─────────────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────────────

def tg_send_message(text: str):

    try:

        response = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text[:4096],
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            },
            timeout=20
        )

        if response.status_code != 200:
            print(f"Telegram message failed: {response.text}")

        return response.status_code == 200

    except Exception as e:
        print(f"Telegram message exception: {e}")
        return False


def tg_send_photo(image_path: Path, caption: str):

    try:

        with open(image_path, "rb") as f:

            response = requests.post(
                f"{TELEGRAM_API}/sendPhoto",
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": caption[:1024],
                    "parse_mode": "HTML"
                },
                files={
                    "photo": ("image.jpg", f, "image/jpeg")
                },
                timeout=60
            )

        if response.status_code != 200:
            print(f"Telegram photo failed: {response.text}")

        return response.status_code == 200

    except Exception as e:
        print(f"Telegram photo exception: {e}")
        return False

# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────

def main():

    posts_path = Path("outputs/posts.json")

    if not posts_path.exists():

        tg_send_message(
            "❌ posts.json not found. Check GitHub Actions logs."
        )

        return

    data = json.loads(posts_path.read_text())

    posts = data.get("posts", [])

    week = data.get(
        "week_start",
        datetime.utcnow().strftime("%d %b %Y")
    )

    print("=" * 60)
    print(f"LinkedIn Bot — Week {week}")
    print(f"Posts to process: {len(posts)}")
    print("=" * 60)

    tg_send_message(
        f"🚀 <b>LinkedIn Content Ready — Week of {week}</b>\n\n"
        f"✍️ {len(posts)} posts generated\n"
        f"🎨 AI images generating\n"
        f"📋 Saved to Google Sheets\n\n"
        f"Posts below 👇"
    )

    failed_images = []

    for i, post in enumerate(posts, start=1):

        day = post.get("day", f"Day {i}")

        topic = post.get("topic", "DevOps")

        hook = post.get("hook", "")

        body = post.get("body", "")

        hashtags = post.get("hashtags", "#DevOps")

        prompt = post.get(
            "image_prompt",
            f"Professional DevOps illustration about {topic}"
        )

        print(f"\n[{i}] Processing: {topic}")

        safe_name = (
            topic.lower()
            .replace(" ", "_")
            .replace("/", "_")
        )[:28]

        filename = f"day{i}_{safe_name}.png"

        img_path = generate_image_hf(prompt, filename)

        if not img_path:
            failed_images.append(topic)

        caption = (
            f"<b>📅 {day}</b>\n"
            f"<b>📌 {topic}</b>\n\n"
            f"<b>Hook:</b> {hook}\n\n"
            f"{hashtags}"
        )

        if img_path and img_path.exists():

            sent = tg_send_photo(img_path, caption)

            if not sent:
                tg_send_message(
                    f"⚠️ Image upload failed\n\n{caption}"
                )

        else:

            tg_send_message(
                f"⚠️ No image generated\n\n{caption}"
            )

        time.sleep(2)

        full_post = (
            f"📋 <b>LinkedIn Post:</b>\n\n"
            f"{body}"
        )

        tg_send_message(full_post)

        time.sleep(2)

    footer = [
        f"✅ Delivered {len(posts)} posts",
        "",
        "Checklist:",
        "1️⃣ Review posts",
        "2️⃣ Save images",
        "3️⃣ Approve in Sheets",
        "4️⃣ Schedule on LinkedIn"
    ]

    if failed_images:

        footer.append("")
        footer.append("⚠️ Failed image generation:")

        for item in failed_images:
            footer.append(f"• {item}")

    tg_send_message("\n".join(footer))

    print("\n✅ Completed successfully")


if __name__ == "__main__":
    main()
