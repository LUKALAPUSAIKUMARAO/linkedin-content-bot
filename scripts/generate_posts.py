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
    "How Kubernetes pod scheduling actually works under the hood",
    "Kubernetes resource requests vs limits — most teams get this wrong",
    "Debugging CrashLoopBackOff: my exact step-by-step process",
    "Why I switched from Ingress to Gateway API in Kubernetes",
    "Kubernetes RBAC done right — least privilege in practice",
    "HPA vs KEDA — when autoscaling gets serious",
    "Kubernetes network policies — zero trust between pods",
    "Helm chart best practices I learned after 3 broken deployments",
    "ArgoCD vs Flux — GitOps tool comparison after using both in production",
    "Kubernetes persistent volumes — what nobody explains clearly",
    "Blue-green vs canary deployments — when to use which",
    "Kubernetes upgrade strategy — how we do zero-downtime version bumps",
    "Service mesh with Istio — what we gained and what it cost us",
    "Kubernetes liveness vs readiness vs startup probes — real differences",
    "How I debugged a Kubernetes memory leak at 2am",
    "Kubernetes namespaces — how we structure them in production",
    "Pod disruption budgets — the setting that saved our deployments",
    "Kubernetes init containers — underrated and misunderstood",
    "Kubernetes config maps vs secrets — when to use which",
    "How we reduced Kubernetes cluster costs by 35% without downtime",
    "Kubernetes admission controllers — the gatekeeper most teams ignore",
    "Debugging Kubernetes networking with tcpdump and ephemeral containers",
    "Kubernetes cluster autoscaler vs Karpenter — honest comparison",
    "How Kubernetes etcd works and why it matters for production",
    "OPA Gatekeeper for Kubernetes policy enforcement — real setup",
    "Kubernetes jobs and cronjobs — patterns I use in production",
    "Multi-tenancy in Kubernetes — 3 approaches and their tradeoffs",
    "Kubernetes taints and tolerations — practical production use cases",
    "How we migrated from self-managed k8s to EKS without downtime",
    "Kubernetes DNS debugging — the commands I use every time",

    # ── Terraform / IaC ─────────────────────────────────────
    "Terraform state file — the thing that will bite you if ignored",
    "Why terraform destroy once deleted our production database",
    "Terraform modules I wish I had built from day one",
    "Managing multiple AWS accounts with Terraform workspaces",
    "Terragrunt vs Terraform — honest comparison after using both",
    "Terraform state locking — why it matters and how we broke it",
    "How I structure Terraform repos for large teams",
    "Terraform import — rescuing manually created infrastructure",
    "Drift detection in Terraform — our workflow for catching it early",
    "Terraform testing with Terratest — setup that actually works",
    "How we refactored 10000 lines of Terraform without breaking prod",
    "Terraform provider version pinning — lessons from a bad upgrade",
    "Remote state in Terraform — S3 backend setup done right",
    "Terraform for Kubernetes — managing EKS with infrastructure as code",
    "Pulumi vs Terraform — after trying both for 6 months",
    "Terraform plan in CI — how we review infrastructure changes safely",
    "Managing secrets in Terraform without storing them in state",
    "Terraform Cloud vs self-hosted — our decision and why",
    "How we onboard new engineers to a 50000 line Terraform codebase",
    "Terraform null resources — when to use them and when not to",
    "OpenTofu — the Terraform fork and whether it is worth switching",
    "Crossplane vs Terraform — infrastructure from Kubernetes",
    "Ansible vs Terraform — right tool for right job",
    "Terraform moved blocks — refactoring without destroying resources",
    "Data sources in Terraform — patterns I use every week",

    # ── CI/CD ────────────────────────────────────────────────
    "GitHub Actions: 5 patterns that cut our pipeline time by 60%",
    "Why our monorepo CI was slow and how we fixed it with path filters",
    "Self-hosted GitHub Actions runners on EKS — full setup walkthrough",
    "The hidden cost of flaky tests in CI pipelines",
    "Secrets management in CI/CD — what not to do",
    "GitHub Actions vs Jenkins — honest migration experience",
    "Blue-green deployments in CI/CD — our exact pipeline",
    "Database migrations in CI/CD — how to do them without downtime",
    "Feature flags in production — our setup and lessons learned",
    "Reusable GitHub Actions workflows — patterns that save hours",
    "How we cut Docker build time from 18 minutes to 3",
    "Pipeline as code — why we moved everything to YAML",
    "How we handle rollbacks in our deployment pipeline",
    "Canary deployments with GitHub Actions and Argo Rollouts",
    "Matrix builds in GitHub Actions — parallel testing at scale",
    "CircleCI vs GitHub Actions — migration experience after 2 years",
    "How we test infrastructure changes before applying them",
    "Deployment frequency — how we went from weekly to 20 times a day",
    "GitHub Actions OIDC — no more long-lived AWS credentials in CI",
    "How we built a zero-downtime deployment pipeline from scratch",
    "Artifact management in CI — what we use and why",
    "Jenkins to GitHub Actions migration — lessons from 200 pipelines",
    "GitLab CI vs GitHub Actions — side by side comparison",
    "How we enforce code quality gates in our CI pipeline",
    "Tekton pipelines on Kubernetes — real production experience",

    # ── AWS ──────────────────────────────────────────────────
    "AWS IAM: the permissions model that took me 6 months to truly understand",
    "How I reduced our AWS bill by $3000 per month with one config change",
    "EKS vs self-managed Kubernetes — real production comparison",
    "AWS SQS + Lambda for async workloads — architecture that scales",
    "VPC design mistakes that cause production incidents",
    "AWS Cost Explorer: the 5 filters I check every Monday morning",
    "AWS Lambda cold starts — what causes them and how we reduced ours by 80%",
    "Multi-region AWS architecture — what breaks that single-region hides",
    "AWS ECS vs EKS — when containers don't need Kubernetes",
    "AWS IAM roles vs users — why we eliminated all IAM users",
    "S3 bucket policies that caused a security incident — lessons learned",
    "AWS RDS vs Aurora — decision framework after using both",
    "How we use AWS Organizations for multi-account governance",
    "AWS CloudWatch vs Datadog — cost and capability tradeoffs",
    "Spot instances in production — our strategy for 60% cost savings",
    "AWS security hub — setting it up and making it actionable",
    "How we handle AWS region failover for our critical services",
    "AWS CDK vs Terraform — choosing the right IaC tool for AWS",
    "Reserved instances vs savings plans — our actual cost analysis",
    "AWS Transit Gateway — simplifying multi-VPC networking",
    "AWS WAF setup that actually blocks attacks",
    "How we audit AWS permissions across 15 accounts",
    "AWS Fargate vs EC2 — when serverless containers make sense",
    "EBS vs EFS vs S3 — storage decision guide from real use cases",
    "How we use AWS Config to enforce compliance automatically",

    # ── Azure ────────────────────────────────────────────────
    "Azure DevOps vs GitHub Actions — enterprise perspective",
    "AKS vs EKS — Kubernetes on Azure vs AWS comparison",
    "Azure managed identities — eliminating service account passwords",
    "Azure Policy for governance at scale — our setup",
    "How we reduced Azure costs by 40% in one quarter",
    "Azure Monitor vs Datadog — observability stack decision",
    "Azure Blob Storage patterns for high-throughput workloads",
    "Azure AD vs AWS IAM — identity differences that matter",
    "How we use Azure Bicep instead of ARM templates",
    "Azure landing zones — what they are and why they matter",

    # ── Linux & Shell ────────────────────────────────────────
    "Linux performance debugging commands I use in every incident",
    "Shell scripting patterns I stopped using after learning Python",
    "Understanding Linux cgroups — the foundation of containers",
    "Linux signals — what every DevOps engineer needs to know",
    "How I use tmux for managing production incident sessions",
    "Linux file descriptor limits — the bug that took us 4 hours to find",
    "strace and lsof — underused tools for debugging production issues",
    "Linux memory management — what OOMKilled actually means",
    "How I use awk and sed in real infrastructure automation",
    "Linux networking commands that saved me in production incidents",
    "systemd — service management patterns I use every week",
    "Bash vs Python for automation — my honest decision framework",
    "Linux disk I/O debugging — tools and techniques from real incidents",
    "How we harden Linux servers in production — checklist and reasoning",
    "Understanding Linux load average — what the numbers actually mean",
    "SSH hardening — every setting we changed and why",
    "Linux swap — when it helps and when it destroys performance",
    "How I use jq for JSON processing in shell scripts",
    "Linux process management — beyond kill and ps",
    "Understanding /proc filesystem — what it tells you about your system",

    # ── Docker / Containers ──────────────────────────────────
    "Docker image size went from 1.2GB to 180MB — here is exactly how",
    "Multi-stage Docker builds: the pattern that should be default",
    "Why we stopped using Docker Compose in production",
    "Docker layer caching — how it works and how we exploit it in CI",
    "Container security scanning in CI — tools and what they actually catch",
    "Distroless containers — what they are and when to use them",
    "Docker BuildKit — features that change how you build images",
    "How we manage base images across 40 microservices",
    "Container runtime comparison — Docker vs containerd vs CRI-O",
    "How we debug running containers without SSH",
    "Docker network modes — bridge vs host vs overlay explained",
    "Building minimal Python containers — from 900MB to 80MB",
    "How we sign and verify container images in our pipeline",
    "Podman vs Docker — practical differences after switching",
    "How we enforce container image policies in Kubernetes",

    # ── Observability & Monitoring ───────────────────────────
    "The difference between monitoring and observability — it actually matters",
    "How I set up alerting that pages me only when it matters",
    "Distributed tracing with OpenTelemetry — getting started the right way",
    "Why your dashboards are lying to you",
    "Log aggregation at scale: what we learned after 3 failed attempts",
    "Prometheus alerting rules that actually reduce alert fatigue",
    "Grafana dashboard design — what engineers actually look at during incidents",
    "OpenTelemetry vs vendor agents — the case for open standards",
    "How we reduced MTTR from 45 minutes to 8 minutes",
    "Structured logging — why we switched and what changed",
    "How we use synthetic monitoring to catch issues before users do",
    "Building a runbook that engineers actually use during incidents",
    "Metrics vs logs vs traces — when to use which for debugging",
    "How we instrument Python services with OpenTelemetry",
    "ELK stack vs Loki — log aggregation comparison from production",
    "Datadog vs Grafana Cloud — honest cost and feature comparison",
    "How we catch performance regressions before they reach production",
    "SLO-based alerting — moving from threshold alerts to error budgets",
    "How we built a real-time cost dashboard for engineering teams",
    "On-call alert quality — how we reduced noise by 70%",

    # ── Platform Engineering ─────────────────────────────────
    "Why we built an Internal Developer Platform and what we got wrong first",
    "Golden paths: how platform teams reduce cognitive load for developers",
    "Developer self-service without losing control — the balance",
    "Backstage.io after 6 months in production — honest review",
    "Platform engineering vs DevOps — the difference that matters",
    "How we measure platform team success — metrics that matter",
    "Developer experience — how we measure and improve it",
    "How we built a self-service database provisioning system",
    "Internal platforms: build vs buy — our decision framework",
    "How we reduced onboarding time from 2 weeks to 2 days",
    "Platform team toil — how we identified and eliminated it",
    "How we communicate platform changes without breaking teams",
    "Port vs Backstage vs OpsLevel — internal developer portal comparison",
    "How we handle platform versioning and deprecation",
    "The hardest part of platform engineering is not technical",

    # ── SRE ──────────────────────────────────────────────────
    "SLOs vs SLAs — the distinction that changed how our team operates",
    "Error budgets in practice — not just a concept",
    "Postmortem culture: how we turned a 4-hour outage into a team win",
    "Toil: how I calculated it and got headcount approved to fix it",
    "Incident command structure — how we run outages without chaos",
    "On-call rotation design — what works and what burns people out",
    "How we define SLOs for services we don't own",
    "Chaos engineering — how we started small and built confidence",
    "Game days — how we practice incidents before they happen",
    "How we write postmortems that actually prevent recurrence",
    "Production readiness reviews — our checklist and process",
    "How we reduced on-call burden by 50% in 6 months",
    "Reliability vs velocity — the tradeoff no one talks about honestly",
    "How we prioritize reliability work against feature requests",
    "SRE team structure — embedded vs centralized — our experience",
    "Blameless culture — what it actually means in practice",
    "How we handle cascading failures in microservices",
    "Capacity planning — how we forecast infrastructure needs",
    "How we track and reduce error budget burn rate",
    "Mean time to detect vs mean time to resolve — both matter equally",

    # ── Security & DevSecOps ─────────────────────────────────
    "Least privilege in AWS: how to audit what your services really need",
    "Secrets sprawl: how we cleaned up 200 hardcoded credentials",
    "How we shift security left without slowing down developers",
    "SAST vs DAST — security scanning in our CI pipeline",
    "How we handle CVEs in our container base images",
    "HashiCorp Vault for secrets management — our production setup",
    "How we audit IAM permissions across 15 AWS accounts",
    "Supply chain security — how we verify our dependencies",
    "Network segmentation in production — zero trust in practice",
    "How we do threat modeling for infrastructure changes",
    "SBOM — software bill of materials and why it matters now",
    "How we handle security incidents — runbook and lessons learned",
    "Falco for runtime security in Kubernetes — real setup",
    "How we use AWS GuardDuty and what it actually catches",
    "Security as code — encoding policies in version control",
    "How we do secrets rotation without downtime",
    "Container image signing with Cosign — our pipeline setup",
    "How we passed SOC2 audit without slowing engineering",
    "Zero trust networking — what it means in a cloud-native setup",
    "How we handle third-party vendor security assessments",

    # ── Networking ───────────────────────────────────────────
    "How DNS actually works — deeper than most DevOps engineers go",
    "TCP vs UDP — when it actually matters for infrastructure decisions",
    "How we debug intermittent network timeouts in microservices",
    "Load balancer algorithms — round robin is rarely the right choice",
    "How we use eBPF for network visibility in Kubernetes",
    "Service discovery in microservices — patterns and pitfalls",
    "How we handle certificate rotation without downtime",
    "mTLS in practice — securing service-to-service communication",
    "CDN configuration mistakes that caused production incidents",
    "How we troubleshoot packet loss in production",
    "BGP basics every cloud engineer should understand",
    "How we handle IPv6 in our cloud infrastructure",
    "API gateway patterns — what we use and why",
    "How we use Envoy proxy beyond just Istio",
    "Network performance testing — tools we use before launching",

    # ── Databases & Storage ──────────────────────────────────
    "How we do zero-downtime PostgreSQL schema migrations",
    "Database connection pooling — the tuning that fixed our timeouts",
    "How we handle database failover in production",
    "Redis in production — patterns we use and mistakes we made",
    "How we back up databases and actually test the restores",
    "Database sharding — when we needed it and how we did it",
    "How we monitor database performance in production",
    "MongoDB vs PostgreSQL — choosing the right database",
    "How we handle data migrations across microservices",
    "Read replicas in production — setup and gotchas",
    "How we use database proxies to improve resilience",
    "TimescaleDB for metrics storage — our experience",
    "How we archive data without breaking application queries",
    "Database index optimization that cut query time by 90%",
    "How we test database disaster recovery quarterly",

    # ── Career & Growth ──────────────────────────────────────
    "How I prepared for senior DevOps interviews — what actually worked",
    "The DevOps skills no one talks about but every team needs",
    "From sysadmin to DevOps engineer — the mindset shift that mattered",
    "How to demonstrate DevOps impact without being the loudest in the room",
    "Building a home lab for DevOps practice — what I actually use",
    "Technical debt in infrastructure — how to make the business case",
    "How I learn new DevOps tools without tutorial paralysis",
    "DevOps certifications — which ones actually helped my career",
    "How to negotiate a DevOps salary — what worked for me",
    "The books that changed how I think about systems and reliability",
    "How I got my first DevOps job without a traditional CS degree",
    "Senior vs staff DevOps engineer — the real difference",
    "How to build credibility as a DevOps engineer in a new team",
    "The soft skills that separate good DevOps engineers from great ones",
    "How I structure my learning as a DevOps engineer in 2025",
    "How to run a productive blameless postmortem",
    "DevOps burnout — how I recognized it and what I changed",
    "How I built a reputation as the go-to infrastructure person",
    "What hiring managers actually look for in DevOps candidates",
    "How to present infrastructure work to non-technical stakeholders",
    "Open source contributions as a DevOps engineer — getting started",
    "How I use documentation as a force multiplier on my team",
    "The career advice I wish someone gave me 3 years ago",
    "How to handle being on-call without it ruining your life",
    "DevOps engineer to engineering manager — things to consider first",

    # ── AI & Automation ──────────────────────────────────────
    "How I use AI coding assistants in my DevOps workflow",
    "AI for log analysis — what works and what does not yet",
    "How we use LLMs to improve our runbooks",
    "AI-assisted code review for infrastructure changes",
    "How we automate toil with Python and AI APIs",
    "ChatOps — how we run infrastructure operations from Slack",
    "How we use AI for anomaly detection in metrics",
    "Automating incident triage with machine learning — our experiment",
    "How I built an internal Slack bot for infrastructure queries",
    "AI for capacity planning — promising but not there yet",
    "How we use GitHub Copilot for writing Terraform",
    "Automating cloud cost optimization with Python scripts",
    "How we built an auto-remediation system for common alerts",
    "AI pair programming for DevOps — honest experience after 6 months",
    "How we use natural language to query our observability stack",

    # ── GitOps & Workflows ───────────────────────────────────
    "What nobody tells you about GitOps",
    "How we structure Git branches for infrastructure repos",
    "GitOps with ArgoCD — our production setup and lessons",
    "How we handle environment promotion in a GitOps workflow",
    "Git hooks for infrastructure validation — our setup",
    "How we review infrastructure pull requests effectively",
    "Monorepo vs polyrepo for microservices — our decision",
    "How we handle hotfixes in a GitOps workflow",
    "Pre-commit hooks that save us from broken infrastructure",
    "How we version and release internal platform tooling",

    # ── Cost Engineering ─────────────────────────────────────
    "FinOps in practice — how we built a cloud cost culture",
    "How we allocate cloud costs to product teams",
    "Kubernetes cost optimization — rightsizing workloads in production",
    "How we cut data transfer costs by 60% without code changes",
    "Spot instance interruption handling — our production strategy",
    "How we use cloud cost anomaly detection",
    "Building a cloud cost dashboard engineers actually use",
    "How we reduced data storage costs through lifecycle policies",
    "FinOps team setup — how platform and finance work together",
    "How we forecast cloud spend for annual budgeting",

    # ── Microservices & Architecture ─────────────────────────
    "How we decompose a monolith — lessons from a real migration",
    "Service mesh vs sidecar — when the complexity is worth it",
    "How we handle distributed transactions across microservices",
    "API versioning strategy — what works in a microservices world",
    "Event-driven architecture — patterns we use in production",
    "How we handle backward compatibility across 30 microservices",
    "gRPC vs REST — when we switched and what changed",
    "How we manage service dependencies and avoid tight coupling",
    "Circuit breaker pattern in production — setup and tuning",
    "How we do contract testing between microservices",
    "Saga pattern for distributed transactions — real implementation",
    "How we handle configuration management across environments",
    "Service catalog — how we document and discover internal services",
    "How we handle versioning of async events in Kafka",
    "Strangler fig pattern — gradually replacing legacy systems",

    # ── Kafka & Messaging ────────────────────────────────────
    "Kafka in production — setup mistakes we made and fixed",
    "Kafka consumer group rebalancing — debugging the lag spike",
    "How we size Kafka partitions for throughput",
    "Dead letter queues — our strategy for handling failed messages",
    "Kafka vs RabbitMQ vs SQS — choosing the right queue",
    "How we monitor Kafka consumer lag in production",
    "Schema registry — enforcing message contracts across teams",
    "How we handle Kafka topic replication for disaster recovery",
    "Exactly-once semantics in Kafka — when it matters",
    "How we migrated from RabbitMQ to Kafka without downtime",

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

    # Find outermost JSON object
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in response")
    raw = raw[start:end]

    # State machine: fix control characters inside strings only
    result    = []
    in_string = False
    escaped   = False

    for ch in raw:
        if escaped:
            result.append(ch)
            escaped = False
            continue

        if ch == "\\" and in_string:
            result.append(ch)
            escaped = True
            continue

        if ch == '"':
            in_string = not in_string
            result.append(ch)
            continue

        if in_string:
            if ch == "\n":
                result.append("\\n")
            elif ch == "\r":
                result.append("\\r")
            elif ch == "\t":
                result.append("\\t")
            elif ord(ch) < 32:
                pass  # skip other control chars
            else:
                result.append(ch)
        else:
            result.append(ch)

    return "".join(result)


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

    batches = [
        (list(range(0, 4)), "Batch 1 — Days 1 to 4"),
        (list(range(4, 7)), "Batch 2 — Days 5 to 7"),
    ]

    for batch_indices, batch_label in batches:
        print(f"\n--- {batch_label} ---")

        batch_topics  = [chosen_topics[i] for i in batch_indices]
        batch_days    = [week_days[i]     for i in batch_indices]
        batch_formats = [POST_FORMATS[i]  for i in batch_indices]

        batch_prompt = f"""
You are a senior DevOps engineer writing LinkedIn posts from real hands-on experience.
You write for: DevOps engineers, SREs, platform engineers, hiring managers.

YOUR BACKGROUND:
{YOUR_PERSONA}

POST REQUIREMENTS:
- LENGTH: 180 to 280 words per post body. No exceptions.
- STRUCTURE:
  Line 1: HOOK — one punchy specific sentence
  blank line
  CONTEXT — 1-2 sentences
  blank line
  BODY — technical content in assigned format, real tool names, real commands, real numbers
  blank line
  CLOSING QUESTION — specific, practitioner-level
  blank line
  HASHTAGS — 3 to 5, always include #DevOps

WRITING RULES:
- First person: I, we, our team
- Short sentences
- Banned: game-changer, leverage, delve, unlock, journey, synergy, excited to share, thrilled
- No vague phrases like "best practices" or "improve efficiency"

IMAGE PROMPT RULES:
- TECHNICAL VISUAL only — no people, no stock photos
- Dark background #0d1117
- Accent: green #00ff88 or cyan #00d4ff
- Specify: visual type, technical elements, style
- Clean, minimal, professional, no watermark

POSTS TO GENERATE:
{chr(10).join(f"Post {i+1} ({batch_days[i]}): TOPIC=[{batch_topics[i]}] FORMAT=[{batch_formats[i]}]" for i in range(len(batch_indices)))}

OUTPUT RULES:
- Return ONLY raw JSON — no markdown, no backticks, no explanation
- CRITICAL: newlines inside string values MUST be \\n — never real line breaks inside JSON strings

{{
  "posts": [
    {{
      "day": "{batch_days[0]}",
      "topic": "exact topic",
      "hook": "first line only, no newlines",
      "body": "complete post using \\n for paragraph breaks — 180 to 280 words",
      "hashtags": "#Tag1 #Tag2 #DevOps",
      "image_prompt": "technical visual — no people",
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

                data  = json.loads(clean_json(raw))
                posts = data.get("posts", [])

                if len(posts) < len(batch_indices):
                    print(f"  Got {len(posts)} posts, expected {len(batch_indices)} — retrying")
                    continue

                for j, post in enumerate(posts[:len(batch_indices)]):
                    post["day"]          = batch_days[j]
                    post["topic"]        = post.get("topic", batch_topics[j])
                    post["word_count"]   = len(post.get("body", "").split())
                    post["status"]       = "Draft"
                    post["generated_at"] = datetime.now(UTC).isoformat()

                all_posts.extend(posts[:len(batch_indices)])
                print(f"  ✅ {len(batch_indices)} posts OK")
                break

            except json.JSONDecodeError as e:
                print(f"  JSON parse failed attempt {attempt+1}: {e}")
                Path("outputs/debug_raw.txt").write_text(raw)
                if attempt == 2:
                    raise
            except Exception as e:
                print(f"  Error attempt {attempt+1}: {e}")
                if attempt == 2:
                    raise

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


if __name__ == "__main__":
    generate()
