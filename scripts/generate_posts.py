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
# TOPIC POOL — 49 unique topics, rotates weekly
# ─────────────────────────────────────────────
TOPIC_POOL = [
    "How Kubernetes pod scheduling actually works under the hood",
    "Kubernetes resource requests vs limits — most teams get this wrong",
    "Debugging CrashLoopBackOff: my exact step-by-step process",
    "Why I switched from Ingress to Gateway API in Kubernetes",
    "Kubernetes RBAC done right — least privilege in practice",
    "HPA vs KEDA — when autoscaling gets serious",
    "Terraform state file — the thing that will bite you if ignored",
    "Why terraform destroy once deleted our production database",
    "Terraform modules I wish I had built from day one",
    "Managing multiple AWS accounts with Terraform workspaces",
    "Terragrunt vs Terraform — honest comparison after using both",
    "GitHub Actions: 5 patterns that cut our pipeline time by 60%",
    "Why our monorepo CI was slow and how we fixed it with path filters",
    "Self-hosted GitHub Actions runners on EKS — full setup walkthrough",
    "The hidden cost of flaky tests in CI pipelines",
    "Secrets management in CI/CD — what not to do",
    "AWS IAM: the permissions model that took me 6 months to truly understand",
    "How I reduced our AWS bill by $3000/month with one config change",
    "EKS vs self-managed Kubernetes — real production comparison",
    "AWS SQS + Lambda for async workloads — architecture that scales",
    "VPC design mistakes that cause production incidents",
    "The difference between monitoring and observability — it actually matters",
    "How I set up alerting that pages me only when it matters",
    "Distributed tracing with OpenTelemetry — getting started the right way",
    "Why your dashboards are lying to you",
    "Log aggregation at scale: what we learned after 3 failed attempts",
    "Why we built an Internal Developer Platform and what we got wrong first",
    "Golden paths: how platform teams reduce cognitive load for developers",
    "Developer self-service without losing control — the balance",
    "Backstage.io after 6 months in production — honest review",
    "SLOs vs SLAs — the distinction that changed how our team operates",
    "Error budgets in practice — not just a concept",
    "Postmortem culture: how we turned a 4-hour outage into a team win",
    "Toil: how I calculated it and got headcount approved to fix it",
    "Linux performance debugging commands I use in every incident",
    "Shell scripting patterns I stopped using after learning Python",
    "Understanding Linux cgroups — the foundation of containers",
    "Docker image size went from 1.2GB to 180MB — here is exactly how",
    "Multi-stage Docker builds: the pattern that should be default",
    "Why we stopped using Docker Compose in production",
    "Container security scanning in CI — tools and what they actually catch",
    "Least privilege in AWS: how to audit what your services really need",
    "Secrets sprawl: how we cleaned up 200 hardcoded credentials",
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
# PICK 7 UNIQUE TOPICS — rotate by week number
# ─────────────────────────────────────────────
UTC          = timezone.utc
today        = datetime.now(UTC)
week_number  = today.isocalendar()[1]
start_index  = (week_number * 7) % len(TOPIC_POOL)
chosen_topics = [
    TOPIC_POOL[(start_index + i) % len(TOPIC_POOL)]
    for i in range(7)
]

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
    "Before vs After: show the exact transformation — what the old way looked like, what changed, measurable result.",
    "Myth vs Reality: bust 3-4 specific misconceptions. Each myth gets a crisp reality check with the reason why.",
    "5 specific tools or commands: real names, real use cases, one concrete example or command per tool.",
    "Incident story: set the scene, describe what broke, walk through the debug steps, share what you learned.",
    "Career insight: one concrete, opinionated piece of advice with a real example. Not generic motivation.",
]

# ─────────────────────────────────────────────
# MASTER PROMPT
# ─────────────────────────────────────────────
PROMPT = f"""
You are a senior DevOps engineer writing LinkedIn posts from real hands-on experience.
You write for technical professionals: DevOps engineers, SREs, platform engineers, hiring managers.

YOUR BACKGROUND:
{YOUR_PERSONA}

═══════════════════════════════════════════
POST REQUIREMENTS — follow every rule strictly
═══════════════════════════════════════════

LENGTH: Every post body must be 180 to 280 words. Count carefully. No exceptions.

STRUCTURE — every post must follow this exact layout:

[HOOK] One punchy, specific sentence on its own line. Examples:
"I spent 6 hours debugging a Kubernetes pod that wouldn't schedule. The fix was one misconfigured affinity rule."
"Your Terraform state file is a single point of failure. Most teams treat it as an afterthought."
"We cut CI pipeline time from 22 minutes to 4. Here is exactly what we changed."

[blank line]

[CONTEXT] 1-2 sentences: why this matters or what situation triggered this post.

[blank line]

[BODY] The technical content in the format assigned for that day.
Use real tool names. Use real commands. Use real numbers.
Never write vague phrases like "ensure best practices" or "improve efficiency".
Every point must have a specific detail, not just a label.

[blank line]

[CLOSING QUESTION] One specific question a practitioner would genuinely want to answer.
Bad: "What do you think?"
Good: "What's your go-to tool for Kubernetes network debugging?"
Good: "How does your team handle Terraform state in a multi-account setup?"

[blank line]

[HASHTAGS] Exactly 3 to 5 hashtags on the final line. Always include #DevOps.

═══════════════════════════════════════════
WRITING RULES
═══════════════════════════════════════════
- First person: use I, we, our team
- Short sentences. One idea per sentence.
- Banned words: game-changer, leverage, delve, unlock, journey, synergy, revolutionize, excited to share, thrilled, humbled
- Line breaks between every paragraph — LinkedIn collapses walls of text
- Sound like a practitioner writing to smart colleagues, not a corporate blog

═══════════════════════════════════════════
IMAGE PROMPT RULES
═══════════════════════════════════════════
Each image_prompt must describe a TECHNICAL VISUAL only. Never describe a person or stock photo.
Must specify ALL of these:
1. Visual type: terminal screenshot, architecture diagram, dashboard UI, code diff, infographic
2. Dark background: #0d1117 or similar dark tone
3. Accent color: green #00ff88, cyan #00d4ff, or amber #ffb300
4. Specific technical elements: exact command output, service names, diagram components
5. Style: clean, minimal, professional, no clutter, no watermark, no text overlays

Good image prompt examples:
"Dark terminal showing kubectl top nodes output with CPU and memory percentage bars in green, monospace font Fira Code, subtle dark grid background, clean minimal layout, no watermark"
"AWS architecture diagram on #0d1117 background: VPC box containing public and private subnets, EKS cluster icon, RDS instance, ALB at top, all connected with cyan #00d4ff arrows, minimal flat icons, professional infographic style"
"Terraform plan diff output on dark background: green plus signs for added resources, red minus signs for destroyed, monospace font, syntax highlighted, clean developer tool aesthetic"

═══════════════════════════════════════════
THIS WEEK TOPICS AND FORMATS
═══════════════════════════════════════════
{chr(10).join(f"Day {i+1} ({week_days[i]}): TOPIC=[{chosen_topics[i]}] FORMAT=[{POST_FORMATS[i]}]" for i in range(7))}

TRENDING THIS WEEK for context:
{chr(10).join(f"- {t}" for t in trend_titles) if trend_titles else "- General DevOps and cloud infrastructure topics"}

═══════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════
Return ONLY a raw JSON object. No markdown. No backticks. No explanation.
CRITICAL: All newlines inside string values MUST be written as the two characters backslash-n. Never use a real line break inside a JSON string value.

{{
  "week_start": "{week_days[0]}",
  "posts": [
    {{
      "day": "{week_days[0]}",
      "topic": "exact topic label",
      "hook": "the first line only, no newlines",
      "body": "complete post from hook to hashtags — use \\n for line breaks between paragraphs",
      "hashtags": "#Tag1 #Tag2 #DevOps",
      "image_prompt": "detailed technical visual — no people, no stock photos",
      "word_count": 0
    }}
  ]
}}
"""

# ─────────────────────────────────────────────
# JSON CLEANER
# ─────────────────────────────────────────────
def clean_json(raw: str) -> str:
    raw = raw.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in response")
    cleaned = match.group(0)

    # Fix literal newlines inside JSON string values
    def fix_newlines_in_strings(m):
        inner = m.group(0)
        # Replace real newlines inside the string with escaped \n
        inner = inner.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
        return inner

    cleaned = re.sub(
        r'"(?:[^"\\]|\\.)*"',
        fix_newlines_in_strings,
        cleaned,
        flags=re.DOTALL
    )

    # Remove remaining control characters
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

    return cleaned


# ─────────────────────────────────────────────
# GENERATE
# ─────────────────────────────────────────────
def generate():
    print("Calling Groq API...")
    print("Topics this week:")
    for i, t in enumerate(chosen_topics, 1):
        print(f"  Day {i}: {t}")

    Path("outputs").mkdir(exist_ok=True)

    all_posts = []

    # Split into two batches: days 1-4 and days 5-7
    batches = [
        (list(range(0, 4)), "Batch 1 — Days 1 to 4"),
        (list(range(4, 7)), "Batch 2 — Days 5 to 7"),
    ]

    for batch_indices, batch_label in batches:
        print(f"\n--- {batch_label} ---")

        batch_topics = [chosen_topics[i] for i in batch_indices]
        batch_days   = [week_days[i]     for i in batch_indices]
        batch_formats= [POST_FORMATS[i]  for i in batch_indices]

        batch_prompt = f"""
You are a senior DevOps engineer writing LinkedIn posts from real hands-on experience.
You write for technical professionals: DevOps engineers, SREs, platform engineers, hiring managers.

YOUR BACKGROUND:
{YOUR_PERSONA}

═══════════════════════════════════════════
POST REQUIREMENTS — follow every rule strictly
═══════════════════════════════════════════

LENGTH: Every post body must be 180 to 280 words. Count carefully. No exceptions.

STRUCTURE — every post must follow this exact layout:

[HOOK] One punchy specific sentence on its own line.
[blank line]
[CONTEXT] 1-2 sentences: why this matters or what triggered this.
[blank line]
[BODY] Technical content in the assigned format. Real tool names. Real commands. Real numbers. No vague phrases.
[blank line]
[CLOSING QUESTION] One specific question a practitioner would genuinely answer.
[blank line]
[HASHTAGS] 3 to 5 hashtags. Always include #DevOps.

WRITING RULES:
- First person: I, we, our team
- Short sentences. One idea per sentence.
- Banned: game-changer, leverage, delve, unlock, journey, synergy, excited to share, thrilled
- Use \\n between paragraphs — never a real line break inside a JSON string

IMAGE PROMPT RULES — each image_prompt must be a TECHNICAL VISUAL:
- Visual type: terminal, architecture diagram, dashboard, code diff, infographic
- Dark background #0d1117
- Accent color: green #00ff88 or cyan #00d4ff
- Specific technical elements (exact commands, service names, diagram parts)
- Style: clean, minimal, no people, no watermark

═══════════════════════════════════════════
POSTS TO GENERATE FOR THIS BATCH
═══════════════════════════════════════════
{chr(10).join(f"Post {i+1} ({batch_days[i]}): TOPIC=[{batch_topics[i]}] FORMAT=[{batch_formats[i]}]" for i in range(len(batch_indices)))}

═══════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════
Return ONLY a raw JSON object. No markdown. No backticks. No explanation before or after.
CRITICAL: All newlines inside string values MUST be written as \\n — never use real line breaks inside JSON strings.

{{
  "posts": [
    {{
      "day": "{batch_days[0]}",
      "topic": "exact topic",
      "hook": "first line only, no newlines",
      "body": "complete post using \\n for paragraph breaks",
      "hashtags": "#Tag1 #Tag2 #DevOps",
      "image_prompt": "technical visual description — no people, no stock photos",
      "word_count": 0
    }}
  ]
}}
"""

        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": batch_prompt}],
                    temperature=0.75,
                    max_tokens=8000,
                )

                raw = response.choices[0].message.content
                print(f"  Raw length: {len(raw)} chars")

                data = json.loads(clean_json(raw))
                posts = data.get("posts", [])

                if len(posts) < len(batch_indices):
                    print(f"  Got {len(posts)} posts, expected {len(batch_indices)} — retrying")
                    continue

                # Stamp each post with correct day from our schedule
                for j, post in enumerate(posts[:len(batch_indices)]):
                    post["day"]          = batch_days[j]
                    post["topic"]        = post.get("topic", batch_topics[j])
                    post["word_count"]   = len(post.get("body", "").split())
                    post["status"]       = "Draft"
                    post["generated_at"] = datetime.now(UTC).isoformat()

                all_posts.extend(posts[:len(batch_indices)])
                print(f"  Got {len(posts[:len(batch_indices)])} posts OK")
                break

            except json.JSONDecodeError as e:
                print(f"  JSON parse failed attempt {attempt+1}: {e}")
                if attempt == 2:
                    raise
                continue

            except Exception as e:
                print(f"  Error attempt {attempt+1}: {e}")
                if attempt == 2:
                    raise
                continue

    if len(all_posts) != 7:
        print(f"WARNING: Expected 7 posts, got {len(all_posts)}")

    output = {
        "week_start": week_days[0],
        "posts": all_posts
    }

    Path("outputs/posts.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=False)
    )

    print(f"\nGenerated {len(all_posts)} posts:\n")
    for p in all_posts:
        print(f"  {p['day']} | {p['topic']} | {p['word_count']} words")
