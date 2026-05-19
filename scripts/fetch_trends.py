import json
import requests
from datetime import datetime
from pathlib import Path

Path("outputs").mkdir(exist_ok=True)

DEVOPS_KEYWORDS = [
    "kubernetes", "docker", "terraform", "devops", "platform",
    "sre", "observability", "helm", "gitops", "ci/cd", "aws",
    "azure", "linux", "github actions", "infrastructure", "monitoring"
]

def fetch_hackernews():
    topics = []
    try:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10
        ).json()[:150]
        for story_id in ids[:60]:
            story = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                timeout=5
            ).json()
            title = story.get("title", "").lower()
            if any(kw in title for kw in DEVOPS_KEYWORDS):
                topics.append(story.get("title"))
            if len(topics) >= 5:
                break
    except Exception as e:
        print(f"HN error: {e}")
    return topics

def fetch_devto():
    topics = []
    for tag in ["devops", "kubernetes", "terraform", "sre", "platform-engineering"]:
        try:
            articles = requests.get(
                f"https://dev.to/api/articles?tag={tag}&top=7&per_page=2",
                timeout=10
            ).json()
            for a in articles:
                topics.append(a.get("title", ""))
        except Exception as e:
            print(f"Dev.to error for {tag}: {e}")
    return [t for t in topics if t][:8]

if __name__ == "__main__":
    trends = fetch_hackernews() + fetch_devto()
    output = {
        "fetched_at": datetime.utcnow().isoformat(),
        "trends": [t for t in trends if t]
    }
    Path("outputs/trends.json").write_text(json.dumps(output, indent=2))
    print(f"Saved {len(output['trends'])} trends")