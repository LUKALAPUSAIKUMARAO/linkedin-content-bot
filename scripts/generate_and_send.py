import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────
# ENV VARIABLES
# ─────────────────────────────────────────

HF_API_KEY         = os.environ["HF_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]
TELEGRAM_API       = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# ─────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────

OUTPUT_DIR = Path("outputs")
POSTS_FILE = OUTPUT_DIR / "posts.json"
IMAGE_DIR  = OUTPUT_DIR / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────
# HF MODELS — ordered best to fallback
# All confirmed working on free HF Inference API
# ─────────────────────────────────────────

HF_MODELS = [
    "black-forest-labs/FLUX.1-schnell",
    "stabilityai/stable-diffusion-xl-base-1.0",
    "stabilityai/stable-diffusion-2-1",
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
        print(f"  TG message: {r.status_code}")
        if r.status_code != 200:
            print(f"  TG error: {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"  TG message exception: {e}")
        return False


def tg_send_photo(image_path, caption):
    try:
        with open(image_path, "rb") as f:
            r = requests.post(
                f"{TELEGRAM_API}/sendPhoto",
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": caption[:1024],
                    "parse_mode": "HTML"
                },
                files={"photo": ("image.png", f, "image/png")},
                timeout=60
            )
        print(f"  TG photo: {r.status_code}")
        if r.status_code != 200:
            print(f"  TG photo error: {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"  TG photo exception: {e}")
        return False

# ─────────────────────────────────────────
# IMAGE GENERATION
# ─────────────────────────────────────────

def generate_image(prompt, filename):
    save_path = IMAGE_DIR / filename

    enhanced = (
        f"{prompt}, "
        "dark background, professional tech illustration, "
        "DevOps cloud infrastructure, clean modern UI, "
        "high resolution, cinematic lighting, no text, no watermark"
    )

    for model in HF_MODELS:
        short = model.split("/")[-1]
        print(f"  Trying: {short}")

        try:
            r = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=HF_HEADERS,
                json={
                    "inputs": enhanced,
                    "parameters": {
                        "num_inference_steps": 20,
                        "guidance_scale": 7.5
                    },
                    "options": {"wait_for_model": True}
                },
                timeout=120
            )

            print(f"  HF status: {r.status_code}")
            print(f"  Content-Type: {r.headers.get('content-type', 'unknown')}")

            # ── Success: got image bytes ──
            if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
                save_path.write_bytes(r.content)
                print(f"  ✓ Saved {filename} ({len(r.content)//1024} KB)")
                return save_path

            # ── Got JSON back instead of image ──
            if r.status_code == 200:
                try:
                    body = r.json()
                    print(f"  HF returned JSON (not image): {body}")
                except Exception:
                    print(f"  HF returned non-image, non-JSON: {r.text[:200]}")
                time.sleep(5)
                continue

            # ── Model still loading ──
            if r.status_code == 503:
                try:
                    wait = r.json().get("estimated_time", 20)
                except Exception:
                    wait = 20
                print(f"  Model loading — waiting {wait}s")
                time.sleep(min(wait, 30))
                # Retry same model once
                print(f"  Retrying {short} after wait...")
                r2 = requests.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers=HF_HEADERS,
                    json={
                        "inputs": enhanced,
                        "parameters": {"num_inference_steps": 20},
                        "options": {"wait_for_model": True}
                    },
                    timeout=120
                )
                if r2.status_code == 200 and "image" in r2.headers.get("content-type", ""):
                    save_path.write_bytes(r2.content)
                    print(f"  ✓ Saved on retry: {filename}")
                    return save_path
                print(f"  Retry failed ({r2.status_code}) — trying next model")
                continue

            # ── Rate limited ──
            if r.status_code == 429:
                print("  Rate limited — waiting 20s")
                time.sleep(20)
                continue

            # ── Model gated / not found ──
            if r.status_code in (401, 403, 404):
                print(f"  Model unavailable ({r.status_code}) — skipping")
                continue

            print(f"  Unexpected status {r.status_code} — trying next model")

        except requests.exceptions.Timeout:
            print(f"  Timeout on {short} — trying next model")
        except Exception as e:
            print(f"  Exception on {short}: {e}")

        time.sleep(3)

    print(f"  ✗ All models failed for {filename}")
    return None

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main():
    print(f"\n{'='*50}")
    print("LinkedIn content bot — image gen + Telegram")
    print(f"{'='*50}\n")

    if not POSTS_FILE.exists():
        tg_send_message("❌ posts.json not found. Check GitHub Actions logs.")
        raise FileNotFoundError("outputs/posts.json not found")

    data  = json.loads(POSTS_FILE.read_text())
    posts = data.get("posts", [])
    week  = data.get("week_start", datetime.utcnow().strftime("%d %b %Y"))

    print(f"Loaded {len(posts)} posts for week of {week}")

    tg_send_message(
        f"🚀 <b>LinkedIn Content — Week of {week}</b>\n\n"
        f"📝 {len(posts)} posts generated\n"
        f"🎨 Generating images via Hugging Face\n\n"
        f"Posts incoming 👇"
    )
    time.sleep(1)

    failed = []

    for i, post in enumerate(posts, 1):
        topic    = post.get("topic", "DevOps")
        body     = post.get("body", "")
        hashtags = post.get("hashtags", "#DevOps")
        hook     = post.get("hook", "")
        day      = post.get("day", f"Day {i}")
        prompt   = post.get("image_prompt", f"DevOps cloud infrastructure illustration, {topic}")
        words    = post.get("word_count", 0)

        print(f"\n[{i}/7] {day} — {topic}")

        # ── Generate image ──
        safe  = topic.lower().replace(" ", "_").replace("/", "_")[:25]
        fname = f"day{i}_{safe}.png"
        img   = generate_image(prompt, fname)

        if not img:
            failed.append(f"Day {i} — {topic}")

        # ── Caption under image ──
        caption = (
            f"<b>Day {i} — {day}</b>\n"
            f"<b>{topic}</b>\n\n"
            f"{hook}\n\n"
            f"{hashtags}\n"
            f"📝 {words} words"
        )

        # ── Send image + caption ──
        if img and img.exists():
            if not tg_send_photo(img, caption):
                tg_send_message(f"⚠️ Photo upload failed\n\n{caption}")
        else:
            tg_send_message(f"⚠️ <b>Image failed — Day {i}</b>\n\n{caption}")

        time.sleep(1)

        # ── Full post text — copy-paste ready ──
        tg_send_message(
            f"📋 <b>Day {i} — Copy to LinkedIn:</b>\n\n{body}"
        )

        time.sleep(2)

    # ── Footer ──
    lines = [f"✅ <b>All {len(posts)} posts sent!</b>\n"]
    lines += [
        "Your checklist:",
        "1️⃣ Read posts above — edit if needed",
        "2️⃣ Save images from this chat",
        "3️⃣ Schedule all 7 on LinkedIn\n"
    ]
    if failed:
        lines.append("⚠️ <b>These images failed — generate on ideogram.ai:</b>")
        lines += [f"  • {f}" for f in failed]

    tg_send_message("\n".join(lines))
    print("\n✅ Done — check Telegram.")


if __name__ == "__main__":
    main()
