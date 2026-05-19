import os
import json
import re
from datetime import datetime, timedelta, UTC
from pathlib import Path
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

# ─────────────────────────────────────────────
# FILL THIS IN — the only thing you edit here
# ─────────────────────────────────────────────
YOUR_PERSONA = """
- 4 years of experience in DevOps and Cloud Infrastructure
- Working as a DevOps Engineer at a mid-sized product company
- Primary stack: Kubernetes (EKS), Terraform, GitHub Actions, AWS, Python, Helm
- Have worked with cross-functional teams of 10-30 engineers
- Strong opinions on GitOps, infrastructure as code, and platform engineering
- Passionate about SRE practices and reducing toil
- Based in Hyderabad, India
"""
# ─────────────────────────────────────────────

# Load trends
try:
    trends_raw = json.loads(Path("outputs/trends.json").read_text())
    trend_titles = trends_raw.get("trends", [])[:10]
except Exception:
    trend_titles = []

# Build next week's dates (Mon–Sun)
today = datetime.now(UTC)
days_until_monday = (7 - today.weekday()) % 7 or 7
next_monday = today + timedelta(days=days_until_monday)

week_days = [
    (next_monday + timedelta(days=i)).strftime("%A %d %b")
    for i in range(7)
]

POST_FORMATS = [
    "Numbered list of insights (5-7 points)",
    "What nobody tells you about X",
    "Before vs after — show a transformation",
    "Myth vs Reality (bust 3-4 common misconceptions)",
    "5 tools/commands that changed how I work",
    "Story: what happened, what I learned (incident or project)",
    "Career advice for DevOps engineers"
]

PROMPT = f"""
You are a senior DevOps engineer writing LinkedIn posts from personal experience.

YOUR BACKGROUND:
{YOUR_PERSONA}

YOUR WRITING RULES (follow strictly):
- First line is the hook — make it bold, specific, or counterintuitive
- Write like a practitioner, not a content creator
- Use real commands, tools, tradeoffs, failures
- Never use:
  "game-changer"
  "leverage"
  "delve"
  "unlock"
  "journey"
  "excited to share"
  "thrilled"

- Keep sentences short
- Use line breaks generously
- Always end with a genuine discussion question
- 3-5 hashtags only
- Always include #DevOps
- Hashtags at the very end
- Target length: 150-280 words

VERY IMPORTANT JSON RULES:
- Return ONLY VALID JSON
- No markdown
- No ```json
- No explanations
- Escape all quotes properly
- No tabs
- No control characters
- Output must work directly with Python json.loads()

TRENDING THIS WEEK:
{chr(10).join(f"- {t}" for t in trend_titles) if trend_titles else "- General DevOps topics"}

POSTING SCHEDULE:
{chr(10).join(f"Day {i+1} ({d}): {POST_FORMATS[i]}" for i, d in enumerate(week_days))}

Generate 7 LinkedIn posts.

JSON FORMAT:

{{
  "week_start": "{week_days[0]}",
  "posts": [
    {{
      "day": "Monday 23 Jun",
      "topic": "Kubernetes networking",
      "hook": "Hook line",
      "body": "Complete post text",
      "hashtags": "#DevOps #Kubernetes",
      "image_prompt": "Detailed AI image prompt",
      "word_count": 0
    }}
  ]
}}
"""

def clean_json_response(raw: str) -> str:
    """
    Cleans Groq response and extracts valid JSON.
    """

    raw = raw.strip()

    # Remove markdown fences
    raw = raw.replace("```json", "")
    raw = raw.replace("```", "")
    raw = raw.strip()

    # Extract JSON object
    match = re.search(r"\{.*\}", raw, re.DOTALL)

    if not match:
        raise ValueError("No valid JSON object found in response")

    cleaned = match.group(0)

    # Remove invalid control chars
    cleaned = re.sub(r"[\x00-\x1F\x7F]", "", cleaned)

    return cleaned


def generate():
    print("Calling Groq API...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": PROMPT
            }
        ],
        temperature=0.8,
        max_tokens=7000,
    )

    raw = response.choices[0].message.content

    print("\n========== RAW RESPONSE ==========\n")
    print(raw[:3000])
    print("\n==================================\n")

    try:
        cleaned_json = clean_json_response(raw)

        data = json.loads(cleaned_json)

    except Exception as e:
        print("FAILED TO PARSE JSON")
        print(e)

        Path("outputs/debug_raw_response.txt").write_text(raw)

        raise

    # Enhance metadata
    for post in data.get("posts", []):

        post["word_count"] = len(post["body"].split())

        post["status"] = "Draft"

        post["generated_at"] = datetime.now(UTC).isoformat()

    # Save final output
    Path("outputs/posts.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False)
    )

    print(f"\nGenerated {len(data['posts'])} posts\n")

    for p in data["posts"]:
        print(
            f"  {p['day']} | {p['topic']} | {p['word_count']} words"
        )


if __name__ == "__main__":
    generate()