import os
import json
import re
import time
import requests
from datetime import datetime, timezone
from pathlib import Path
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]
TELEGRAM_API       = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

UTC = timezone.utc

# ─────────────────────────────────────────────
# CHEATSHEET TOPIC POOL — 52 topics, full year
# ─────────────────────────────────────────────
CHEATSHEET_TOPICS = [

    # ── Kubernetes — Basic ───────────────────────────────────
    "kubectl commands every DevOps engineer must know",
    "Kubernetes pod lifecycle and debugging commands",
    "Kubernetes YAML manifest structure — all key fields",
    "Kubernetes namespaces — commands and use cases",
    "Kubernetes services — ClusterIP, NodePort, LoadBalancer reference",
    "Kubernetes ConfigMaps and Secrets — create and consume reference",
    "Kubernetes resource requests and limits — syntax and examples",
    "Kubernetes labels and selectors — patterns and commands",
    "Kubernetes deployments — rollout, rollback, scaling commands",
    "Kubernetes ReplicaSet and DaemonSet reference",

    # ── Kubernetes — Intermediate ────────────────────────────
    "Helm CLI commands cheatsheet — install to uninstall",
    "Helm chart structure and values reference",
    "Kubernetes networking — services, DNS, ingress reference",
    "Kubernetes RBAC — roles, bindings, service accounts reference",
    "Kubernetes liveness, readiness, startup probes reference",
    "Kubernetes resource management — QoS classes explained",
    "Kubernetes jobs and cronjobs — syntax and patterns",
    "Kubernetes persistent volumes and PVCs reference",
    "Kubernetes init containers and sidecar patterns",
    "Kubernetes pod affinity and anti-affinity rules",
    "Kubernetes taints and tolerations reference",
    "Kubernetes horizontal pod autoscaler commands",
    "Kubernetes network policies — syntax and examples",
    "Kubernetes StatefulSet reference — patterns and commands",

    # ── Kubernetes — Advanced ────────────────────────────────
    "ArgoCD CLI and sync strategy cheatsheet",
    "Kubernetes RBAC audit — commands to find permission gaps",
    "Kubernetes admission controllers reference",
    "KEDA autoscaling — scaledObject syntax reference",
    "Kubernetes cluster autoscaler configuration reference",
    "Karpenter node provisioner configuration cheatsheet",
    "Kubernetes Gateway API — HTTPRoute and Gateway syntax",
    "OPA Gatekeeper constraint syntax reference",
    "Kubernetes debugging — ephemeral containers and exec patterns",
    "Kubernetes etcd backup and restore commands",
    "Kubernetes certificate management — kubeadm certs reference",
    "Velero backup and restore commands cheatsheet",
    "Kubernetes multi-cluster management with kubectx and kubens",
    "Cilium network policy syntax reference",
    "Istio service mesh — traffic management commands",
    "Kubernetes pod security standards reference",
    "Kubernetes custom resource definitions — CRD syntax",
    "kubectl plugins — krew and top plugins reference",
    "Kubernetes node troubleshooting commands",
    "Kubernetes audit logging configuration reference",

    # ── Terraform — Basic ────────────────────────────────────
    "Terraform CLI commands — init to destroy",
    "Terraform HCL syntax — variables, outputs, locals",
    "Terraform resource and data source syntax reference",
    "Terraform provider configuration reference",
    "Terraform input variables — types and validation",
    "Terraform output values — syntax and usage",
    "Terraform locals and expressions reference",
    "Terraform built-in functions cheatsheet",
    "Terraform conditionals and loops reference",

    # ── Terraform — Intermediate ─────────────────────────────
    "Terraform modules — structure and calling syntax",
    "Terraform state commands cheatsheet",
    "Terraform workspace commands reference",
    "Terraform backend configuration reference",
    "Terraform import and moved blocks reference",
    "Terraform lifecycle rules — create before destroy reference",
    "Terraform depends on and provisioners reference",
    "Terraform data sources — common patterns",
    "Terraform remote state and outputs reference",

    # ── Terraform — Advanced ─────────────────────────────────
    "Terraform testing — validate, plan, and Terratest reference",
    "Terragrunt commands and config reference",
    "Terraform Cloud CLI and workspace reference",
    "Terraform provider development basics",
    "Terraform drift detection commands and workflow",
    "Terraform secrets management patterns reference",
    "OpenTofu CLI commands cheatsheet",
    "Pulumi CLI commands reference",
    "Crossplane composition reference",
    "Terraform CDK synthesis commands reference",

    # ── GitHub Actions ───────────────────────────────────────
    "GitHub Actions syntax — triggers, jobs, steps reference",
    "GitHub Actions environment variables and secrets reference",
    "GitHub Actions matrix builds and strategy reference",
    "GitHub Actions reusable workflows syntax",
    "GitHub Actions expressions and context reference",
    "GitHub Actions artifact upload and download reference",
    "GitHub Actions caching — actions/cache syntax",
    "GitHub Actions OIDC — AWS and GCP auth reference",
    "GitHub Actions self-hosted runner setup reference",
    "GitHub Actions permissions and security reference",
    "GitHub CLI — gh commands cheatsheet",
    "GitHub Actions debugging and troubleshooting commands",

    # ── Docker — Basic ───────────────────────────────────────
    "Docker CLI commands — build, run, push reference",
    "Dockerfile syntax — all instructions reference",
    "Docker volumes — create, mount, manage commands",
    "Docker networking — bridge, host, overlay reference",
    "Docker Compose syntax reference — services, volumes, networks",
    "Docker image management commands cheatsheet",
    "Docker container lifecycle commands reference",
    "Docker logs and exec commands reference",

    # ── Docker — Advanced ────────────────────────────────────
    "Docker BuildKit advanced syntax reference",
    "Docker multi-stage build patterns reference",
    "Docker Compose override and environment patterns",
    "Docker security scanning commands — Trivy and Grype",
    "Container image signing with Cosign reference",
    "Docker registry commands — push, pull, tag reference",
    "Podman CLI commands cheatsheet",
    "containerd CLI — ctr and nerdctl commands",
    "Docker buildx multi-platform build reference",
    "Docker layer caching optimization patterns",

    # ── AWS — Basic ──────────────────────────────────────────
    "AWS CLI configuration and profile management reference",
    "AWS CLI commands every DevOps engineer uses weekly",
    "AWS S3 CLI commands cheatsheet",
    "AWS EC2 instance management CLI reference",
    "AWS IAM — users, groups, roles, policies CLI reference",
    "AWS VPC — subnets, routing, security groups CLI reference",
    "AWS CloudWatch logs and metrics CLI reference",
    "AWS SSM parameter store commands reference",

    # ── AWS — Intermediate ───────────────────────────────────
    "AWS EKS commands and eksctl cheatsheet",
    "AWS Lambda CLI and deployment cheatsheet",
    "AWS ECS CLI and task definition reference",
    "AWS RDS CLI commands reference",
    "AWS CloudFormation CLI cheatsheet",
    "AWS Secrets Manager CLI commands reference",
    "AWS SQS and SNS CLI commands reference",
    "AWS Route53 CLI commands reference",
    "AWS ALB and target group CLI reference",
    "AWS ACM certificate management CLI reference",
    "AWS ECR commands — push, pull, lifecycle reference",
    "AWS Cost Explorer CLI queries reference",

    # ── AWS — Advanced ───────────────────────────────────────
    "AWS Organizations and SCP management reference",
    "AWS Control Tower commands reference",
    "AWS Service Control Policies syntax reference",
    "AWS CDK CLI commands and synth reference",
    "AWS Security Hub and GuardDuty CLI reference",
    "AWS Config rules and remediation reference",
    "AWS EventBridge rules and targets CLI reference",
    "AWS Step Functions CLI reference",
    "AWS Glue and data pipeline CLI reference",
    "AWS Transit Gateway commands reference",
    "AWS Direct Connect and VPN CLI reference",
    "AWS Backup CLI commands reference",

    # ── Azure ────────────────────────────────────────────────
    "Azure CLI — az commands every DevOps engineer needs",
    "Azure AKS commands reference — az aks cheatsheet",
    "Azure resource group and subscription CLI reference",
    "Azure Active Directory CLI commands reference",
    "Azure DevOps CLI — az devops pipelines reference",
    "Azure Bicep syntax reference",
    "Azure Key Vault CLI commands reference",
    "Azure Monitor and Log Analytics CLI reference",
    "Azure Container Registry CLI reference",
    "Azure Policy CLI commands reference",

    # ── GCP ──────────────────────────────────────────────────
    "GCP gcloud CLI essential commands reference",
    "GCP GKE commands — gcloud container cheatsheet",
    "GCP IAM and service accounts CLI reference",
    "GCP Cloud Run deployment commands reference",
    "GCP Cloud Storage gsutil commands cheatsheet",
    "GCP networking — VPC, firewall rules CLI reference",
    "GCP Cloud Build configuration reference",
    "GCP Artifact Registry commands reference",

    # ── Linux — Basic ────────────────────────────────────────
    "Linux file system navigation commands cheatsheet",
    "Linux file permissions — chmod, chown, umask reference",
    "Linux user and group management commands",
    "Linux package management — apt, yum, dnf reference",
    "Linux process management — ps, kill, jobs reference",
    "Linux disk commands — df, du, lsblk reference",
    "Linux text processing — grep, cat, head, tail reference",
    "Linux file search — find and locate commands reference",
    "Linux archive commands — tar, zip, gzip reference",
    "Linux environment variables and shell config reference",

    # ── Linux — Intermediate ─────────────────────────────────
    "Linux performance commands — top, htop, vmstat, iostat",
    "Linux networking commands — netstat, ss, ip reference",
    "Linux firewall — iptables and ufw reference",
    "Linux log management — journalctl, logrotate reference",
    "systemd — service management commands reference",
    "Linux cron and crontab syntax reference",
    "Linux SSH — config, keys, tunneling reference",
    "Linux disk partitioning — fdisk, parted reference",
    "Linux LVM commands reference",
    "Linux kernel parameters — sysctl reference",

    # ── Linux — Advanced ─────────────────────────────────────
    "Linux performance tuning — tcpdump and strace reference",
    "Linux cgroups and namespaces commands reference",
    "Linux hardening commands and checklist reference",
    "Linux eBPF tools — bpftrace and bcc reference",
    "Linux memory debugging — valgrind and perf reference",
    "Linux network namespaces and veth pairs reference",
    "Linux seccomp profiles reference",
    "Linux audit framework — auditd commands reference",
    "Linux capabilities reference — cap_add and drop",
    "Linux NFS and CIFS mount commands reference",

    # ── Bash Scripting ───────────────────────────────────────
    "Bash scripting syntax — variables, conditionals, loops",
    "Bash functions and error handling reference",
    "Bash string manipulation cheatsheet",
    "Bash arrays and associative arrays reference",
    "Bash file operations and test conditions reference",
    "Bash input and output redirection reference",
    "Bash process substitution and pipes reference",
    "Bash regex and pattern matching reference",
    "Bash script debugging — set -x and trap reference",
    "Bash one-liners for DevOps automation",

    # ── Git ──────────────────────────────────────────────────
    "Git commands cheatsheet — everyday workflow reference",
    "Git branching and merging strategy commands",
    "Git rebase, cherry-pick, and history rewriting reference",
    "Git stash, worktree, and tag commands reference",
    "Git diff and log — advanced filtering reference",
    "Git config — aliases and global settings reference",
    "Git hooks — pre-commit, pre-push setup reference",
    "Git submodules and subtree commands reference",
    "Git bisect and blame commands reference",
    "Git large file storage — git-lfs commands reference",

    # ── Observability ────────────────────────────────────────
    "Prometheus PromQL cheatsheet — queries and functions",
    "Prometheus alerting rules syntax reference",
    "Grafana dashboard variables and panel reference",
    "Grafana alerts and notification channels reference",
    "OpenTelemetry instrumentation cheatsheet",
    "Loki log query language — LogQL reference",
    "Jaeger tracing setup and query reference",
    "kubectl logs and events debugging reference",
    "Datadog CLI and API commands reference",
    "ELK stack — Elasticsearch query syntax reference",
    "cURL for API and health check testing cheatsheet",
    "Prometheus recording rules and federation reference",
    "Grafana Loki label and stream selector reference",
    "OpenTelemetry collector config reference",
    "Alertmanager routing and receiver config reference",

    # ── Security ─────────────────────────────────────────────
    "AWS security audit CLI commands reference",
    "Container security scanning — Trivy commands reference",
    "HashiCorp Vault CLI cheatsheet",
    "Vault secrets engines and auth methods reference",
    "Linux hardening checklist and commands reference",
    "SSL and TLS — openssl commands cheatsheet",
    "GPG commands for signing and encryption reference",
    "Falco rules syntax reference",
    "Cosign image signing commands reference",
    "OWASP top 10 — developer quick reference",
    "AWS IAM policy simulator and audit commands",
    "Kubernetes security context reference",
    "Network security — nmap and netcat commands reference",
    "Secrets scanning — gitleaks and truffleHog reference",
    "SBOM generation — syft commands reference",

    # ── Networking ───────────────────────────────────────────
    "DNS debugging — dig, nslookup, host commands reference",
    "curl commands for API testing and debugging cheatsheet",
    "HTTP status codes complete reference card",
    "TCP/IP networking — essential commands reference",
    "tcpdump commands for traffic analysis cheatsheet",
    "Wireshark display filters reference",
    "iptables rules syntax and examples reference",
    "Nginx configuration — server blocks and proxy reference",
    "HAProxy configuration reference",
    "Network performance testing — iperf and netperf reference",
    "BGP and routing concepts quick reference",
    "IPv6 commands and concepts reference",
    "Envoy proxy configuration reference",
    "Service mesh traffic management patterns reference",
    "Load balancer algorithms and configuration reference",

    # ── Databases ────────────────────────────────────────────
    "PostgreSQL commands cheatsheet — psql reference",
    "PostgreSQL performance queries — slow query analysis",
    "MySQL and MariaDB CLI commands reference",
    "Redis CLI commands cheatsheet",
    "MongoDB shell commands reference",
    "Elasticsearch REST API commands reference",
    "Database backup and restore commands reference",
    "SQL query optimization patterns cheatsheet",
    "PostgreSQL replication setup reference",
    "Database connection pooling configuration reference",

    # ── Python for DevOps ────────────────────────────────────
    "Python one-liners for DevOps automation",
    "Python subprocess and shell command execution reference",
    "Python requests library — HTTP API calls cheatsheet",
    "Python boto3 — AWS SDK common patterns reference",
    "Python file and directory operations cheatsheet",
    "Python JSON and YAML parsing reference",
    "Python argparse — CLI tools syntax reference",
    "Python logging module configuration reference",
    "Python virtualenv and pip commands reference",
    "Python dataclasses and type hints reference",

    # ── Tools and Utilities ──────────────────────────────────
    "jq cheatsheet — JSON processing in the terminal",
    "sed commands cheatsheet — stream editing reference",
    "awk commands cheatsheet — text processing reference",
    "yq commands — YAML processing reference",
    "tmux commands and key bindings cheatsheet",
    "vim commands cheatsheet for DevOps engineers",
    "make and Makefile syntax reference",
    "Ansible ad-hoc commands and playbook reference",
    "Packer build configuration reference",
    "Vagrant commands cheatsheet",
    "Skaffold commands reference for Kubernetes dev",
    "Tilt configuration reference for local Kubernetes",
    "Telepresence commands for Kubernetes debugging",
    "k9s keyboard shortcuts and commands reference",
    "Lens IDE keyboard shortcuts reference",

    # ── SRE and Incident Response ────────────────────────────
    "SRE golden signals reference — latency, traffic, errors, saturation",
    "SLO and error budget calculation reference",
    "Incident response runbook template reference",
    "DevOps incident severity classification reference",
    "Postmortem template and blameless review reference",
    "On-call checklist and escalation reference",
    "Chaos engineering — LitmusChaos commands reference",
    "Load testing — k6 script syntax reference",
    "Load testing — wrk and ab commands reference",
    "Disaster recovery RTO and RPO planning reference",

    # ── FinOps and Cost ──────────────────────────────────────
    "AWS cost optimization CLI commands reference",
    "Kubernetes resource rightsizing commands reference",
    "Cloud cost tagging strategy reference",
    "Spot and preemptible instance configuration reference",
    "AWS Savings Plans and Reserved Instance reference",

    # ── ArgoCD and GitOps ────────────────────────────────────
    "ArgoCD application sync and rollback commands",
    "ArgoCD app of apps pattern reference",
    "Flux CLI commands cheatsheet",
    "GitOps workflow commands and patterns reference",
    "ArgoCD RBAC configuration reference",
]

# ─────────────────────────────────────────────
# TRACK USED TOPICS
# ─────────────────────────────────────────────
USED_FILE = Path("outputs/used_cheatsheet_topics.json")

try:
    used = json.loads(USED_FILE.read_text())
except Exception:
    used = []

remaining = [t for t in CHEATSHEET_TOPICS if t not in used]

if len(remaining) < 1:
    print("All cheatsheet topics used — resetting pool")
    used      = []
    remaining = CHEATSHEET_TOPICS.copy()

topic = remaining[0]
updated_used = used + [topic]
Path("outputs").mkdir(exist_ok=True)
USED_FILE.write_text(json.dumps(updated_used, indent=2))
print(f"Cheatsheet topic this week: {topic}")
print(f"Topics used: {len(updated_used)}/{len(CHEATSHEET_TOPICS)}")

# ─────────────────────────────────────────────
# JSON CLEANER
# ─────────────────────────────────────────────
def clean_json(raw: str) -> str:
    raw = raw.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found")
    raw = raw[start:end]

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
                pass
            else:
                result.append(ch)
        else:
            result.append(ch)

    return "".join(result)

# ─────────────────────────────────────────────
# PROMPT
# ─────────────────────────────────────────────
PROMPT = f"""
You are a senior DevOps engineer creating a professional LinkedIn cheatsheet post.

TOPIC: {topic}

Generate a complete cheatsheet with the following sections.
Every command must be real, accurate, and production-relevant.
No made-up flags. No placeholder examples. Real commands only.

Return ONLY raw JSON. No markdown. No backticks. No explanation.
CRITICAL: All newlines inside string values MUST be \\n — never real line breaks in JSON strings.

{{
  "topic": "{topic}",
  "linkedin_hook": "One punchy sentence to open the LinkedIn post announcing this cheatsheet. Make it specific.",
  "linkedin_intro": "2-3 sentences introducing the cheatsheet. First person. Practical. No buzzwords.",
  "sections": [
    {{
      "section_title": "Section name e.g. Basic Commands",
      "items": [
        {{
          "command": "the exact command or syntax",
          "description": "what it does in plain English — one sentence"
        }}
      ]
    }}
  ],
  "pro_tips": [
    "One specific pro tip practitioners actually use — include real command or config if relevant"
  ],
  "linkedin_cta": "One closing question or CTA that invites engagement from DevOps engineers",
  "hashtags": "#DevOps #relevant1 #relevant2 #relevant3",
  "image_prompt": "Detailed prompt for generating a professional cheatsheet graphic. Must specify: dark background #0d1117, monospace font, the tool or technology name as header in cyan #00d4ff, organized grid layout showing command blocks with green #00ff88 command text and white description text, professional DevOps cheatsheet aesthetic, clean minimal design, no watermark, suitable for LinkedIn carousel first slide"
}}

REQUIREMENTS:
- minimum 5 sections
- minimum 5 items per section
- minimum 4 pro tips
- every command must be real and copy-paste ready
- image_prompt must be detailed enough to generate a professional graphic in Midjourney or Ideogram
"""

# ─────────────────────────────────────────────
# GENERATE
# ─────────────────────────────────────────────
def generate_cheatsheet():
    print("Calling Groq API...")
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": PROMPT}],
                temperature=0.4,
                max_tokens=8000,
            )
            raw  = response.choices[0].message.content
            data = json.loads(clean_json(raw))
            print("✅ Cheatsheet generated successfully")
            return data
        except json.JSONDecodeError as e:
            print(f"JSON parse failed attempt {attempt+1}: {e}")
            if attempt == 2:
                raise
    return None

# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def tg_send(text):
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
        print(f"  TG: {r.status_code}")
        if r.status_code != 200:
            print(f"  TG error: {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"  TG exception: {e}")
        return False

# ─────────────────────────────────────────────
# FORMAT AND SEND
# ─────────────────────────────────────────────
def send_cheatsheet(data):
    topic_title = data.get("topic", topic)
    hook        = data.get("linkedin_hook", "")
    intro       = data.get("linkedin_intro", "")
    sections    = data.get("sections", [])
    tips        = data.get("pro_tips", [])
    cta         = data.get("linkedin_cta", "")
    hashtags    = data.get("hashtags", "#DevOps")
    img_prompt  = data.get("image_prompt", "")
    now         = datetime.now(UTC).strftime("%d %b %Y")

    # ── Message 1: Header ──
    tg_send(
        f"📋 <b>CHEATSHEET — {now}</b>\n\n"
        f"<b>{topic_title}</b>\n\n"
        f"{hook}\n\n"
        f"{intro}\n\n"
        f"<i>Full content coming in next messages 👇</i>"
    )
    time.sleep(1)

    # ── Message 2+: One message per section ──
    for s in sections:
        section_title = s.get("section_title", "")
        items         = s.get("items", [])

        lines = [f"<b>── {section_title} ──</b>\n"]
        for item in items:
            cmd  = item.get("command", "")
            desc = item.get("description", "")
            lines.append(f"<code>{cmd}</code>")
            lines.append(f"  ↳ {desc}\n")

        tg_send("\n".join(lines))
        time.sleep(1)

    # ── Message: Pro tips ──
    tips_lines = ["<b>💡 Pro Tips</b>\n"]
    for i, tip in enumerate(tips, 1):
        tips_lines.append(f"{i}. {tip}\n")
    tg_send("\n".join(tips_lines))
    time.sleep(1)

    # ── Message: LinkedIn post text (copy-paste ready) ──
    post_lines = [f"📝 <b>LinkedIn Post Text (copy-paste ready):</b>\n"]
    post_lines.append(hook)
    post_lines.append(f"\n{intro}\n")

    for s in sections:
        post_lines.append(f"\n<b>{s.get('section_title', '')}</b>")
        for item in s.get("items", [])[:4]:  # top 4 per section for post length
            post_lines.append(f"• {item.get('command','')} — {item.get('description','')}")

    post_lines.append(f"\n💡 Pro tip: {tips[0] if tips else ''}")
    post_lines.append(f"\n{cta}")
    post_lines.append(f"\n{hashtags}")

    full_post = "\n".join(post_lines)
    # Send in chunks if too long
    if len(full_post) > 4096:
        tg_send(full_post[:4096])
        time.sleep(1)
        tg_send(full_post[4096:8192])
    else:
        tg_send(full_post)
    time.sleep(1)

    # ── Message: Image prompt ──
    tg_send(
        f"🎨 <b>Image Prompt — paste into Midjourney / Ideogram / DALL-E:</b>\n\n"
        f"<code>{img_prompt}</code>\n\n"
        f"<i>Tip: Ideogram works best for cheatsheet graphics with text. "
        f"Use 'Design' style and 16:9 ratio for LinkedIn.</i>"
    )
    time.sleep(1)

    # ── Message: Footer ──
    tg_send(
        f"✅ <b>Cheatsheet ready!</b>\n\n"
        f"Your action:\n"
        f"1️⃣ Copy image prompt → paste into Ideogram.ai\n"
        f"2️⃣ Download the cheatsheet graphic\n"
        f"3️⃣ Copy LinkedIn post text above\n"
        f"4️⃣ Post on Wednesday or Thursday for best reach\n\n"
        f"<i>Next cheatsheet arrives next Saturday 🚀</i>"
    )

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"Cheatsheet generator — {topic}")
    print(f"{'='*50}\n")

    data = generate_cheatsheet()
    if data:
        send_cheatsheet(data)
        # Save cheatsheet JSON for reference
        Path("outputs/latest_cheatsheet.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False)
        )
        print("\n✅ Done — check Telegram.")
    else:
        tg_send(f"❌ Cheatsheet generation failed for: {topic}")
