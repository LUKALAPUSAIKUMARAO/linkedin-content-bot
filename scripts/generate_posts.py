import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

TELEGRAM_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
HF_API_KEY      = os.environ["HF_API_KEY"]
TELEGRAM_API    = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

IMAGE_DIR = Path("outputs/images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────
# Hugging Face models — tried in order, first success wins
# All are free on the HF Inference API
# ─────────────────────────────────────────────────────────
HF_MODELS = [
    "black-forest-labs/FLUX.1-schnell",       # Best quality, fast
    "stabilityai/stable-diffusion-xl-base-1.0",  # Reliable fallback
    "runwayml/stable-diffusion-v1-5",            # Last resort fallback
]

HF_HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json",
    "x-wait-for-model": "true"   # wait instead of 503 if model is loading
}

# ─────────────────────────────────────────────────────────
# IMAGE GENERATION
# ─────────────────────────────────────────────────────────

def build_devops_prompt(raw_prompt: str, topic: str) -> str:
    """
    Strengthen the raw AI-generated prompt with DevOps visual style instructions.
    Hugging Face models respond better to detailed style descriptors.
    """
    style_suffix = (
        "dark background, professional tech aesthetic, "
        "high resolution, clean layout, modern UI design, "
        "no text overlays, no watermarks, ultra detailed"
    )
    return f"{raw_prompt}. {style_suffix}"


def generate_image_hf(prompt: str, filename: str) -> Path | None:
    """Try each HF model in order. Return saved path on first success."""
    enhanced_prompt = build_devops_prompt(prompt, filename)
    save_path = IMAGE_DIR / filename

    for model in HF_MODELS:
        api_url = f"https://api-inference.huggingface.co/models/{model}"
        print(f"  Trying model: {model.split('/')[-1]}")
        try:
            response = requests.post(
                api_url,
                headers=HF_HEADERS,
                json={
                    "inputs": enhanced_prompt,
                    "parameters": {
                        "width": 1200,
                        "height": 628,       # LinkedIn ideal ratio 1.91:1
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
                    size_kb = len(response.content) // 1024
                    print(f"  ✓ Image saved: {filename} ({size_kb} KB)")
                    return save_path
                else:
                    # Model returned JSON error instead of image
                    try:
                        err = response.json()
                        print(f"  ✗ Model error: {err.get('error', 'unknown')}")
                    except Exception:
                        print(f"  ✗ Unexpected response (not an image)")

            elif response.status_code == 503:
                print(f"  ✗ Model loading (503) — trying next model")

            elif response.status_code == 429:
                print(f"  ✗ Rate limited — waiting 15s then trying next model")
                time.sleep(15)

            else:
                print(f"  ✗ HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"  ✗ Timeout after 90s — trying next model")
        except Exception as e:
            print(f"  ✗ Exception: {e}")

        time.sleep(3)  # brief pause between model attempts

    print(f"  ✗ All models failed for {filename}")
    return None


# ─────────────────────────────────────────────────────────
# TELEGRAM HELPERS
# ─────────────────────────────────────────────────────────

def tg_send_message(text: str) -> bool:
    """Send plain HTML text message."""
    try:
        r = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text[:4096],
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            },
            timeout=15
        )
        ok = r.status_code == 200
        if not ok:
            print(f"  Telegram msg error: {r.text[:200]}")
        return ok
    except Exception as e:
        print(f"  Telegram msg exception: {e}")
        return False


def tg_send_photo(image_path: Path, caption: str) -> bool:
    """Send image with caption. Caption max 1024 chars."""
    try:
        with open(image_path, "rb") as f:
            r = requests.post(
                f"{TELEGRAM_API}/sendPhoto",
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": caption[:1024],
                    "parse_mode": "HTML"
                },
                files={"photo": ("image.jpg", f, "image/jpeg")},
                timeout=30
            )
        ok = r.status_code == 200
        if not ok:
            print(f"  Telegram photo error: {r.text[:200]}")
        return ok
    except Exception as e:
        print(f"  Telegram photo exception: {e}")
        return False


# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────

def main():
    posts_path = Path("outputs/posts.json")
    if not posts_path.exists():
        tg_send_message("❌ <b>Error:</b> posts.json not found. Check GitHub Actions logs.")
        return

    data   = json.loads(posts_path.read_text())
    posts  = data.get("posts", [])
    week   = data.get("week_start", datetime.utcnow().strftime("%d %b %Y"))

    print(f"\n{'='*52}")
    print(f"  LinkedIn bot — week of {week}")
    print(f"  {len(posts)} posts to process")
    print(f"{'='*52}\n")

    # ── Header message ──
    tg_send_message(
        f"🚀 <b>LinkedIn Content Ready — Week of {week}</b>\n\n"
        f"✍️ {len(posts)} posts generated\n"
        f"🎨 Generating images via Hugging Face (FLUX.1)\n"
        f"📋 All posts saved to Google Sheets\n\n"
        f"Posts coming up below 👇"
    )
    time.sleep(1)

    failed_images = []

    for i, post in enumerate(posts, 1):
        day      = post.get("day", f"Day {i}")
        topic    = post.get("topic", "DevOps")
        hook     = post.get("hook", "")
        body     = post.get("body", "")
        hashtags = post.get("hashtags", "#DevOps")
        prompt   = post.get("image_prompt", f"Professional DevOps dark theme illustration, {topic}")
        words    = post.get("word_count", 0)

        print(f"\n[{i}/7] {day} — {topic}")

        # ── Generate image ──
        safe_name = topic.lower().replace(" ", "_").replace("/", "_")[:28]
        filename  = f"day{i}_{safe_name}.png"
        img_path  = generate_image_hf(prompt, filename)

        if not img_path:
            failed_images.append(f"Day {i} — {topic}")

        # ── Telegram caption (shown under the image) ──
        caption = (
            f"<b>📅 Day {i} — {day}</b>\n"
            f"<b>📌 {topic}</b>\n\n"
            f"<b>Hook:</b> {hook}\n\n"
            f"<b>Tags:</b> {hashtags}\n"
            f"<b>Words:</b> {words}"
        )

        # ── Send image + caption ──
        if img_path and img_path.exists():
            sent = tg_send_photo(img_path, caption)
            if not sent:
                # image send failed — send text instead
                tg_send_message(f"⚠️ Image upload failed\n\n{caption}")
        else:
            tg_send_message(f"⚠️ <b>No image for Day {i}</b>\n\n{caption}")

        time.sleep(1.5)

        # ── Full post text (separate message — easy to copy-paste into LinkedIn) ──
        full_text = (
            f"📋 <b>Day {i} — Full post (copy to LinkedIn):</b>\n\n"
            f"{body}"
        )
        tg_send_message(full_text)

        time.sleep(2)  # respect Telegram rate limit (30 msgs/sec, but be safe)

    # ── Footer summary ──
    footer_lines = [
        f"✅ <b>All {len(posts)} posts delivered!</b>\n",
        "Your Sunday checklist:",
        "1️⃣ Read each post above — edit if needed",
        "2️⃣ Save images from this chat",
        "3️⃣ Open Google Sheets to approve",
        "4️⃣ Open LinkedIn → schedule all 7 posts\n",
    ]

    if failed_images:
        footer_lines.append("⚠️ <b>Image gen failed for:</b>")
        for f in failed_images:
            footer_lines.append(f"  • {f} — generate manually on ideogram.ai")

    tg_send_message("\n".join(footer_lines))
    print("\n✅ Complete — check Telegram.")


if __name__ == "__main__":
    main()
