import os
import json
from pathlib import Path
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = os.environ["GOOGLE_SHEETS_ID"]
CREDS_JSON = os.environ["GOOGLE_CREDENTIALS_JSON"]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

HEADERS = [
    "Day", "Topic", "Hook", "Full Post",
    "Hashtags", "Image Prompt", "Word Count", "Status", "Your Notes"
]

def get_or_create_sheet(spreadsheet):
    week_label = "Week of " + datetime.utcnow().strftime("%Y-%m-%d")
    try:
        ws = spreadsheet.worksheet(week_label)
        print(f"Using existing tab: {week_label}")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=week_label, rows=20, cols=len(HEADERS))
        ws.append_row(HEADERS)
        # Bold the header row
        ws.format("A1:I1", {"textFormat": {"bold": True}})
        print(f"Created new tab: {week_label}")
    return ws

def main():
    posts_path = Path("outputs/posts.json")
    if not posts_path.exists():
        print("No posts.json found — skipping Sheets save")
        return

    data = json.loads(posts_path.read_text())

    creds = Credentials.from_service_account_info(
        json.loads(CREDS_JSON), scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SHEET_ID)
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
            "Draft",
            ""
        ])

    ws.append_rows(rows, value_input_option="USER_ENTERED")
    print(f"Saved {len(rows)} posts to '{ws.title}'")

if __name__ == "__main__":
    main()