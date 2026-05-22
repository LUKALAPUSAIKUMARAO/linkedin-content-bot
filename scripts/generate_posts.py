import os
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

# ─────────────────────────────────────────────
# YOUR PERSONA — edit this
# ─────────────────────────────────────────────
YOUR_PERSONA = """
- 4 years hands-on DevOps and Cloud Infrastructure engineering
- Current role: DevOps Engineer at a mid-sized SaaS product company
- Daily stack: Kubernetes (EKS), Terraform, GitHub Actions, AWS, Python, Helm, ArgoCD
- Built and maintained CI/CD pipelines handling 50+ deployments per day
- Reduced infra costs by 40% through right-sizing and spot instance strategies
- Debugged production Kubernetes outages at 2am — have the battle scars
- Strong opinions on GitOps, platform engineering, and eliminating toil
- Based in Hyderabad, India — writing for a global DevOps audience
"""

# ─────────────────────────────────────────────
# TOPIC POOL — 49 unique topics, one per week
# Never repeats within a run
# ─────────────────────────────────────────────
TOPIC_POOL = [
    # Kubernetes
    "How Kubernetes pod scheduling actually works under the hood",
    "Kubernetes resource requests vs limits — most teams get this wrong",
    "Debugging CrashLoopBackOff: my exact step-by-step process",
    "Why I switched from Ingress to Gateway API in Kubernetes",
    "Kubernetes RBAC done right — least privilege in practice",
    "HPA vs KEDA — when autoscaling gets serious",
    # Terraform
    "Terraform state file — the thing that will bite you if ignored",
    "Why terraform destroy once deleted our production database",
    "Terraform modules I wish I had built from day one",
    "Managing multiple AWS accounts with Terraform workspaces",
    "Terragrunt vs Terraform — honest comparison after using both",
    # CI/CD
    "GitHub Actions: 5 patterns that cut our pipeline time by 60%",
    "Why our monorepo CI was slow and how we fixed it with path filters",
    "Self-hosted GitHub Actions runners on EKS — full setup walkthrough",
    "The hidden cost of flaky tests in CI pipelines",
    "Secrets management in CI/CD — what not to do",
    # AWS
    "AWS IAM: the permissions model that took me 6 months to truly understand",
    "How I reduced our AWS bill by $3000/month with one config change",
    "EKS vs self-managed Kubernetes — real production comparison",
    "AWS SQS + Lambda for async workloads — architecture that scales",
    "VPC design mistakes that cause production incidents",
    # Observability
    "The difference between monitoring and observability — it actually matters",
    "How I set up alerting that pages me only when it matters",
    "Distributed tracing with OpenTelemetry — getting started the right way",
    "Why your dashboards are lying to you",
    "Log aggregation at scale: what we learned after 3 failed attempts",
    # Platform Engineering
    "Why we built an Internal Developer Platform and what we got wrong first",
    "Golden paths: how platform teams reduce cognitive load",
    "Developer self-service without losing control — the balance",
    "Backstage.io after 6 months — honest review",
    # SRE
    "SLOs vs SLAs — the distinction that changed how our team operates",
    "Error budgets in practice — not just a concept",
    "Postmortem culture: how we turned a 4-hour outage into a team win",
    "Toil: how I calculated it and got headcount approved to fix it",
    # Linux & Shell
    "Linux performance debugging commands I use in every incident",
    "Shell scripting patterns I stopped using after learning Python",
    "Understanding Linux cgroups — the foundation of containers",
    # Docker
    "Docker image size went from 1.2GB to 180MB — here is exactly how",
    "Multi-stage Docker builds: the pattern that should be default",
    "Why we stopped using Docker Compose in production",
    # Security
    "Container security scanning in CI — tools and what they actually catch",
    "Least privilege in AWS: how to audit what your services really need",
    "Secrets sprawl: how we cleaned up 200+ hardcoded credentials",
    # Career
    "How I prepared for senior DevOps interviews — what actually worked",
    "The DevOps skills no one talks about but every team needs",
    "From sysadmin to DevOps engineer — the mindset shift that mattered",
    "How to demonstrate DevOps impact without being the loudest in the room",
    "Building a home lab for DevOps practice — what I actually use",
    "Technical debt in infrastructure — how to make the business case",
]

# ─────────────────────────────────────────────
# LOAD TRENDS
# ─────────────────────────────────────────────
try:
    trends_raw   = json.loads(Path("outputs/trends.json").read_text())
    trend_titles = trends_raw.get("trends", [])[:8]
except Exception:
    trend_titles = []

# ─────────────────────────────────────────────
# PICK 7 UNIQUE TOPICS FOR THIS WEEK
# Rotate based on week number so it never repeats
# ─────────────────────────────────────────────
UTC = timezone.utc
today        = datetime.now(UTC)
week_number  = today.isocalendar()[1]
start_index  = (week_number * 7) % len(TOPIC_POOL)
chosen_topics = []
for i in range(7):
    chosen_topics.append(TOPIC_POOL[(start_index + i) % len(TOPIC_POOL)])

# ─────────────────────────────────────────────
# BUILD NEXT WEEK DATES MON–SUN
# ─────────────────────────────────────────────
days_to_monday = (7 - today.weekday()) % 7 or 7
next_monday    = today + timedelta(days=days_to_monday)
week_days      = [
    (next_monday + timedelta(days=i)).strftime("%A %d %b")
    for i in range(7)
]

POST_FORMATS = [
    "Numbered list: 5-7 specific, technical, numbered insights. Each point is 2-3 sentences with real detail.",
    "What nobody tells you: reveal 4 non-obvious truths about this topic that practitioners learn the hard way.",
    "Before vs After: show the exact transformation — what the old way looked like, what changed, and the measurable result.",
    "Myth vs Reality: bust 3-4 specific misconceptions. Each myth gets a crisp reality check with the reason why.",
    "5 specific tools or commands: real names, real use cases, one concrete example or command per tool.",
    "Incident story: set the scene, describe what broke, walk through the debug steps, share what you learned. Be specific.",
    "Career insight: one concrete, opinionated piece of advice with a real example. Not generic motivation."
]

# ─────────────────────────────────────────────
# MASTER PROMPT
# ─────────────────────────────────────────────
PROMPT = f"""
You are a senior DevOps engineer with deep hands-on experience writing LinkedIn posts.
You write for a technical audience: DevOps engineers, SREs, platform engineers, and hiring managers.

YOUR BACKGROUND:
{YOUR_PERSONA}

═══════════════════════════════════════════
STRICT POST REQUIREMENTS — follow every rule
═══════════════════════════════════════════

LENGTH: Every post body must be 180–280 words. No exceptions. Count carefully.

STRUCTURE — every post must follow this exact format:

Line 1: HOOK — one punchy, specific sentence. No fluff. Examples of good hooks:
  "I spent 6 hours debugging a Kubernetes OOMKilled pod. The fix was one line."
  "Your Terraform state file is a single point of failure. Most teams ignore this."
  "We cut our CI pipeline from 22 minutes to 4 minutes. Here's the exact change."

[blank line]

Line 2-3: CONTEXT — 1-2 sentences setting up why this matters or what the problem was.

[blank line]

BODY — the actual technical content. Format depends on the post type assigned.
Use real tool names, real commands, real numbers where possible.
Never use vague phrases like "ensure efficiency" or "best practices".
Every point needs a specific detail, not a label.

[blank line]

CLOSING LINE: One genuine question that a practitioner would actually want to answer.
Not "What do you think?" — something specific like:
  "What's your go-to tool for Kubernetes network debugging?"
  "How does your team handle Terraform state in multi-account setups?"

[blank line]

HASHTAGS: Exactly 3-5 hashtags on the final line. Always include #DevOps.

═══════════════════════════════════════════
WRITING RULES
═══════════════════════════════════════════
- Write in first person — "I", "we", "our team"
- Short sentences. One idea per sentence.
- No buzzwords: "game-changer" "leverage" "delve" "unlock" "journey" "synergy" "revolutionize"
- No corporate language: "excited to share" "thrilled" "humbled"
- Line breaks between every paragraph — LinkedIn collapses walls of text
- Sound like a practitioner writing a Slack message to smart colleagues, not a blog post

═══════════════════════════════════════════
IMAGE PROMPT RULES
═══════════════════════════════════════════
Each image_prompt must describe a TECHNICAL VISUAL — not a person, not a stock photo.
Must specify:
1. The type of visual (terminal, architecture diagram, dashboard, code snippet, infographic)
2. Dark background (#0d1117 or similar)
3. Accent colors (green #00ff88, cyan #00d4ff, or amber #ffb300)
4. Specific technical elements to show (e.g. "kubectl get pods output with STATUS column")
5. Style: clean, minimal, professional, no clutter

Good examples:
  "Dark terminal window showing 'kubectl top nodes' output with CPU and memory bars in green, monospace font, subtle grid, no background noise"
  "AWS architecture diagram on dark background showing VPC with public/private subnets, EKS cluster, RDS, and ALB connected with cyan arrows, minimal icons"
  "Terraform plan output on dark background showing green + added resources and red - destroyed resources in diff format, clean monospace"

Bad examples (never use these):
  "A photo of a person" — NO
  "A messy room vs clean room" — NO
  "Someone looking at a computer" — NO

═══════════════════════════════════════════
THIS WEEK'S TOPICS AND FORMATS
═══════════════════════════════════════════
{chr(10).join(f"Day {i+1} ({week_days[i]}): Topic = [{chosen_topics[i]}] | Format = {POST_FORMATS[i]}" for i in range(7))}

TRENDING THIS WEEK (reference if relevant, do not copy):
{chr(10).join(f"- {t}" for t in trend_titles) if trend_titles else "- General DevOps and cloud infrastructure topics"}

═══════════════════════════════════════════
JSON OUTPUT RULES
═══════════════════════════════════════════
Return ONLY raw JSON. No markdown. No ```json. No explanation before or after.
Escape all special characters properly. No tabs inside strings. No control characters.

{{
  "week_start": "{week_days[0]}",
  "posts": [
    {{
      "day": "{week_days[0]}",
      "topic": "exact topic label",
      "hook": "the first line only",
      "body": "complete post — hook through hashtags — 180-280 words — use \\n for line breaks",
      "hashtags": "#Tag1 #Tag2 #DevOps",
      "image_prompt": "detailed technical visual description following image prompt rules above",
      "word_count": 0
    }}
  ]
}}
"""

# ─────────────────────────────────────────────
# GENERATE
# ─────────────────────────────────────────────

def clean_json(raw: str) -> str:
    raw = raw.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in response")
    cleaned = match.group(0)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)
    return cleaned


def generate():
    print("Calling Groq API...")
    print(f"Topics this week:")
    for i, t in enumerate(chosen_topics, 1):
        print(f"  Day {i}: {t}")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": PROMPT}],
        temperature=0.75,
        max_tokens=8000,
    )

    raw = response.choices[0].message.content

    print("\n=== RAW RESPONSE (first 500 chars) ===")
    print(raw[:500])
    print("======================================\n")

    try:
        data = json.loads(clean_json(raw))
    except Exception as e:
        print(f"JSON parse failed: {e}")
        Path("outputs/debug_raw.txt").write_text(raw)
        raise

    for post in data.get("posts", []):
        post["word_count"]   = len(post.get("body", "").split())
        post["status"]       = "Draft"
        post["generated_at"] = datetime.now(timezone.utc).isoformat()

    Path("outputs/posts.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False)
    )

    print(f"Generated {len(data['posts'])} posts:\n")
    for p in data["posts"]:
        print(f"  {p['day']} | {p['topic']} | {p['word_count']} words")


if __name__ == "__main__":
    generate()
