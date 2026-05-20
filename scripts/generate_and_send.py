def generate():

    print("Skipping Groq generation for testing...")

    posts_file = OUTPUT_DIR / "posts.json"

    if not posts_file.exists():
        raise Exception("outputs/posts.json not found")

    data = json.loads(posts_file.read_text())

    print(f"Loaded {len(data.get('posts', []))} existing posts")

    for p in data.get("posts", []):
        print(f"  {p['day']}: {p['topic']}")

    return data


    # ─────────────────────────────────────────
    # TEMPORARILY DISABLED GROQ GENERATION
    # ─────────────────────────────────────────

    # print("Calling Groq API...")

    # response = client.chat.completions.create(
    #     model="llama-3.3-70b-versatile",
    #     messages=[{"role": "user", "content": PROMPT}],
    #     temperature=0.82,
    #     max_tokens=7000,
    # )

    # raw = response.choices[0].message.content.strip()

    # if "```" in raw:
    #     parts = raw.split("```")
    #     for part in parts:
    #         part = part.strip()
    #         if part.startswith("json"):
    #             part = part[4:].strip()
    #         if part.startswith("{"):
    #             raw = part
    #             break

    # data = json.loads(raw)

    # for post in data["posts"]:
    #     post["word_count"] = len(post.get("body", "").split())
    #     post["status"] = "Draft"
    #     post["generated_at"] = datetime.utcnow().isoformat()

    # out = OUTPUT_DIR / "posts.json"
    # out.write_text(json.dumps(data, indent=2))

    # print(f"Saved {len(data['posts'])} posts to {out}")
