import os
import json
from datetime import datetime, timedelta
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
today = datetime.utcnow()
days_until_monday = (7 - today.weekday()) % 7 or 7
next_monday = today + timedelta(days=days_until_monday)
week_days = [(next_monday + timedelta(days=i)).strftime("%A %d %b") for i in range(7)]

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
- First line is the hook — make it bold, specific, or counterintuitive. No "I'm excited to share".
- Write like a practitioner, not a content creator. Real commands, real tools, real tradeoffs.
- Never use: "game-changer", "leverage", "delve", "unlock", "journey", "excited to share", "thrilled"
- Keep sentences short. Use line breaks generously for readability.
- Always end with a genuine question that invites discussion.
- 3-5 hashtags only. Always include #DevOps. Keep hashtags at the very end.
- Target length: 150-280 words per post.

TRENDING THIS WEEK (use as inspiration for relevance, don't copy directly):
{chr(10).join(f"- {t}" for t in trend_titles) if trend_titles else "- General DevOps topics"}

POSTING SCHEDULE AND FORMATS:
{chr(10).join(f"Day {i+1} ({d}): {POST_FORMATS[i]}" for i, d in enumerate(week_days))}

Generate 7 LinkedIn posts, one per day. Cover different topics across:
Kubernetes, CI/CD pipelines, Terraform/IaC, AWS/Cloud, Linux, Monitoring,
Platform Engineering, SRE, GitHub Actions, career growth.

Return ONLY raw JSON — no markdown, no code fences, no explanation. Just the JSON object.

{{
  "week_start": "{week_days[0]}",
  "posts": [
    {{
      "day": "Monday 23 Jun",
      "topic": "short topic label e.g. Kubernetes networking",
      "hook": "just the first line of the post",
      "body": "the complete post text including hook, all content, CTA question, and hashtags",
      "hashtags": "#Tag1 #Tag2 #DevOps",
      "image_prompt": "Detailed prompt for AI image generator. Dark background. Specify: style (terminal/dashboard/architecture diagram/observability UI), colors (dark bg with green or cyan text), specific elements to include. Example: A dark terminal window showing kubectl get pods output with colorized status columns, green SUCCESS labels, subtle grid lines, clean monospace font, professional DevOps aesthetic.",
      "word_count": 0
    }}
  ]
}}
"""

def generate():
    print("Calling Groq API...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": PROMPT}],
        temperature=0.82,
        max_tokens=7000,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if model adds them
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                raw = part
                break

    data = json.loads(raw)

    for post in data["posts"]:
        post["word_count"] = len(post["body"].split())
        post["status"] = "Draft"
        post["generated_at"] = datetime.utcnow().isoformat()

    Path("outputs/posts.json").write_text(json.dumps(data, indent=2))
    print(f"Generated {len(data['posts'])} posts")
    for p in data["posts"]:
        print(f"  {p['day']}: {p['topic']} ({p['word_count']} words)")

if __name__ == "__main__":
    generate()