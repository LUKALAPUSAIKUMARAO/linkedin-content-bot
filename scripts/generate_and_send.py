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
# HF — correct URL confirmed working
# ─────────────────────────────────────────

HF_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

HF_HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json",
}

# ─────────────────────────────────────────
# TELEGRAM
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
        print(f"  TG exception: {e}")
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
                files={"photo": ("image.jpg", f, "image/jpeg")},
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
        "high resolution, no text, no watermark"
    )

    print(f"  Generating: {filename}")

    for attempt in range(3):
        try:
            r = requests.post(
                HF_URL,
                headers=HF_HEADERS,
                json={"inputs": enhanced},
                timeout=120
            )

            print(f"  Attempt {attempt+1} — status: {r.status_code}, "
                  f"type: {r.headers.get('content-type','?')}, "
                  f"size: {len(r.content)} bytes")

            if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
                save_path.write_bytes(r.content)
                print(f"  ✅ Saved {filename} ({len(r.content)//1024} KB)")
                return save_path

            if r.status_code == 503:
                try:
                    wait = int(r.json().get("estimated_time", 15))
                except Exception:
                    wait = 15
                wait = min(wait, 30)
                print(f"  Model loading — waiting {wait}s")
                time.sleep(wait)
                continue

            if r.status_code == 429:
                print("  Rate limited — waiting 20s")
                time.sleep(20)
                continue

            try:
                print(f"  Error: {r.json()}")
            except Exception:
                print(f"  Error: {r.text[:200]}")
            time.sleep(5)

        except requests.exceptions.Timeout:
            print(f"  Timeout on attempt {attempt+1}")
            time.sleep(5)
        except Exception as e:
            print(f"  Exception: {e}")
            time.sleep(5)

    print(f"  ✗ Failed after 3 attempts: {filename}")
    return None

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main():
    print(f"\n{'='*50}")
    print("LinkedIn bot — FLUX image gen + Telegram")
    print(f"{'='*50}\n")

    if not POSTS_FILE.exists():
        tg_send_message("❌ posts.json not found.")
        raise FileNotFoundError("outputs/posts.json not found")

    data  = json.loads(POSTS_FILE.read_text())
    posts = data.get("posts", [])
    from datetime import timezone
    week  = data.get("week_start", datetime.now(timezone.utc).strftime("%d %b %Y"))

    print(f"Loaded {len(posts)} posts — week of {week}")

    tg_send_message(
        f"🚀 <b>LinkedIn Content — Week of {week}</b>\n\n"
        f"📝 {len(posts)} posts generated\n"
        f"🎨 Generating images via FLUX.1-schnell\n\n"
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
        prompt   = post.get("image_prompt", f"DevOps cloud infrastructure, {topic}")
        words    = post.get("word_count", 0)

        print(f"\n[{i}/7] {day} — {topic}")

        safe  = topic.lower().replace(" ", "_").replace("/", "_")[:25]
        fname = f"day{i}_{safe}.png"
        img   = generate_image(prompt, fname)

        if not img:
            failed.append(f"Day {i} — {topic}")

        caption = (
            f"<b>Day {i} — {day}</b>\n"
            f"<b>{topic}</b>\n\n"
            f"{hook}\n\n"
            f"{hashtags}\n"
            f"📝 {words} words"
        )

        if img and img.exists():
            if not tg_send_photo(img, caption):
                tg_send_message(f"⚠️ Photo upload failed\n\n{caption}")
        else:
            tg_send_message(f"⚠️ <b>Image failed — Day {i}</b>\n\n{caption}")

        time.sleep(1)

        tg_send_message(f"📋 <b>Day {i} — Copy to LinkedIn:</b>\n\n{body}")

        time.sleep(2)

    lines = [f"✅ <b>All {len(posts)} posts sent!</b>\n"]
    lines += [
        "Your checklist:",
        "1️⃣ Read posts above — edit in Google Sheets if needed",
        "2️⃣ Save images from this chat",
        "3️⃣ Schedule all 7 on LinkedIn\n"
    ]
    if failed:
        lines.append("⚠️ <b>Images that failed — generate on ideogram.ai:</b>")
        lines += [f"  • {f}" for f in failed]

    tg_send_message("\n".join(lines))
    print("\n✅ Done.")


if __name__ == "__main__":
    main()
