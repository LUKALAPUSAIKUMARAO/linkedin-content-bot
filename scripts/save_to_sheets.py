import os
import json
from pathlib import Path
from datetime import datetime, UTC

import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound


# ─────────────────────────────────────────────
# ENV VARIABLES
# ─────────────────────────────────────────────

SHEET_ID = os.getenv("GOOGLE_SHEETS_ID")
CREDS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

if not SHEET_ID:
    raise ValueError("GOOGLE_SHEETS_ID environment variable missing")

if not CREDS_JSON:
    raise ValueError("GOOGLE_CREDENTIALS_JSON environment variable missing")


# ─────────────────────────────────────────────
# GOOGLE API SCOPES
# ─────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


# ─────────────────────────────────────────────
# SHEET HEADERS
# ─────────────────────────────────────────────

HEADERS = [
    "Day",
    "Topic",
    "Hook",
    "Full Post",
    "Hashtags",
    "Image Prompt",
    "Word Count",
    "Status",
    "Your Notes",
]


# ─────────────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────────────

def get_gspread_client():

    try:
        creds_dict = json.loads(CREDS_JSON)

        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=SCOPES
        )

        client = gspread.authorize(creds)

        return client

    except Exception as e:
        print("Failed to authenticate with Google")
        print(e)
        raise


# ─────────────────────────────────────────────
# GET OR CREATE WEEK TAB
# ─────────────────────────────────────────────

def get_or_create_sheet(spreadsheet):

    week_label = "Week of " + datetime.now(UTC).strftime("%Y-%m-%d")

    try:
        ws = spreadsheet.worksheet(week_label)

        print(f"Using existing worksheet: {week_label}")

        return ws

    except WorksheetNotFound:

        print(f"Creating worksheet: {week_label}")

        ws = spreadsheet.add_worksheet(
            title=week_label,
            rows=100,
            cols=20
        )

        ws.append_row(HEADERS)

        # Format header row
        ws.format(
            "A1:I1",
            {
                "textFormat": {
                    "bold": True
                }
            }
        )

        return ws


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():

    posts_path = Path("outputs/posts.json")

    if not posts_path.exists():
        print("posts.json not found")
        return

    print("Loading posts.json...")

    data = json.loads(posts_path.read_text(encoding="utf-8"))

    print("Authenticating Google Sheets...")

    gc = get_gspread_client()

    try:
        spreadsheet = gc.open_by_key(SHEET_ID)

    except Exception as e:

        print("\nFAILED TO OPEN GOOGLE SHEET\n")

        print("Possible reasons:")
        print("1. Wrong GOOGLE_SHEETS_ID")
        print("2. Service account not shared to sheet")
        print("3. Google APIs not enabled")

        print("\nError:")
        print(e)

        raise

    ws = get_or_create_sheet(spreadsheet)

    rows = []

    for post in data.get("posts", []):

        rows.append([
            post.get("day", ""),
            post.get("topic", ""),
            post.get("hook", ""),
            post.get("body", ""),
            post.get("hashtags", ""),
            post.get("image_prompt", ""),
            post.get("word_count", 0),
            post.get("status", "Draft"),
            ""
        ])

    if not rows:
        print("No posts found")
        return

    print(f"Uploading {len(rows)} rows...")

    ws.append_rows(
        rows,
        value_input_option="USER_ENTERED"
    )

    print(f"\nSUCCESS")
    print(f"Saved {len(rows)} posts to worksheet: {ws.title}")


if __name__ == "__main__":
    main()