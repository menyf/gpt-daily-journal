"""
# README
The Notion Markdown Importer is a Python script that automatically imports markdown files from a local folder into a Notion database as pages. Each imported markdown file gets transformed into Notion-friendly blocks and structured according to its content.

## Prerequisites
- Notion API Token: You must have an integration token from Notion. Refer to the official guide on how to create an integration and obtain the token.
- Notion Database ID: The database where you wish to import your markdown files. The ID can be obtained from the database URL. You must grant the connection in your database page.

## Configuration

To set up the script for your environment, there are several global fields in the script that you should be aware of:

- NOTION_TOKEN: The token from your Notion integration. It gives the script permission to interact with your Notion workspace.
- DATABASE_ID: The ID of the Notion database where the markdown files will be imported as pages.
- FOLDER_NAME: The name of the folder containing your markdown files. By default, it's set to "Daily". If your files reside in a different folder, adjust this value accordingly.
- MODIFIED_TIME_THRESHOLD_MINUTES: The script only processes files that were modified within the last X minutes, as defined by this variable. Default is 10 minutes.
- SUMMARY_IDENTIFIER: Identifier for the summary section, the next line will be treated as the summary.

## Usage

1. Place your markdown files in the FOLDER_NAME directory.
2. Update the global fields in the script with your specific values (e.g., NOTION_TOKEN, DATABASE_ID, etc.).
3. Run the script with `python3 notion_uploader`. It will scan the specified folder, filter out markdown files modified within the time threshold, and then import them into your Notion database.
Understanding the Markdown Formatting

The script expects markdown files to have a certain structure to correctly transform them into Notion blocks. The supported blocks are:

- `##`: Transforms into a Heading 2 in Notion.
- `-`: Bullet points in markdown become bulleted list items in Notion.
- ````json...````: Code blocks in markdown with a specified json language become code blocks in Notion.

Additional transformations and functionalities can be seen and understood from the script's functions.

"""


import os
import re
import requests
from datetime import datetime, timezone, timedelta

# Configuration
NOTION_TOKEN = "secret_123Xyz" # 'Integration Token' from Notion
DATABASE_ID = "127" # 32digits database ID
FOLDER_NAME = "Daily"  # The folder containing markdown files
MODIFIED_TIME_THRESHOLD_MINUTES = 10  # Time threshold for considering a file as "recently modified"
SUMMARY_IDENTIFIER = "## Summary" # Identifier for the summary section, the next line will be treated as the summary.

# HTTP headers for Notion API
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def read_markdown_file(file_path):
    """Read and return the content of a markdown file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_summary_from_markdown(markdown_content):
    """Extract the summary content under the {SUMMARY_IDENTIFIER} heading."""
    lines = markdown_content.split('\n')
    for i, line in enumerate(lines):
        if line.strip() == SUMMARY_IDENTIFIER:
            return lines[i+1].strip()
    return "NA"

def markdown_to_notion_blocks(markdown_content):
    """Convert markdown content to Notion-compatible block format."""
    blocks = []
    lines = markdown_content.split('\n')

    skip = False
    for i, line in enumerate(lines):
        if skip:
            if line.startswith("```"):
                skip = False
            continue

        # Heading 2
        if line.startswith("## "):
            blocks.append({
                "type": "heading_2",
                "object": "block",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": line.replace("## ", "")}}]
                }
            })
        # Bullet list
        elif line.startswith("- "):
            blocks.append({
                "type": "bulleted_list_item",
                "object": "block",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": line.replace("- ", "")}}]
                }
            })
        # Code block
        elif line.startswith("```json"):
            json_content = ""
            i += 1
            while not lines[i].startswith("```"):
                json_content += lines[i] + "\n"
                i += 1
            blocks.append({
                "type": "code",
                "object": "block",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": json_content[:-1]}}],
                    "language": "json"
                }
            })
            skip = True
        # Note block (time-based notes)
        elif re.match(r'\[\d+:\d+\]', line):
            blocks.append({
                "type": "paragraph",
                "object": "block",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}]
                }
            })
        # Paragraph
        elif line and not line.startswith("##"):
            blocks.append({
                "type": "paragraph",
                "object": "block",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}]
                }
            })
    return blocks

def is_recently_modified(file_path, minutes=MODIFIED_TIME_THRESHOLD_MINUTES):
    """Check if a file was modified within the last 'minutes'."""
    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    return datetime.now() - mod_time < timedelta(minutes=minutes)

def create_page(data, content_blocks):
    """Send a request to Notion API to create a new page."""
    create_url = "https://api.notion.com/v1/pages"
    payload = {"parent": {"database_id": DATABASE_ID}, "properties": data, "children": content_blocks}
    return requests.post(create_url, headers=headers, json=payload)

def process_markdown_files(directory_path=None):
    """Process markdown files from a directory and upload to Notion."""
    if directory_path is None:
        directory_path = os.path.join(os.getcwd(), FOLDER_NAME)

    # Filter .md files that were recently modified
    md_files = [f for f in os.listdir(directory_path)
                if f.endswith('.md')
                and re.match(r'^\d{4}-\d{2}-\d{2}.md$', f)
                and is_recently_modified(os.path.join(directory_path, f))]

    # Process each markdown file
    for md_file in md_files:
        file_path = os.path.join(directory_path, md_file)

        # Extract content from the markdown file
        markdown_content = read_markdown_file(file_path)

        # Extract title from the filename
        title = os.path.splitext(md_file)[0]

        # Convert UTC to California time (PST/PDT)
        file_date = datetime.strptime(title, '%Y-%m-%d')
        pst = timezone(timedelta(hours=-8))
        file_date_california = file_date.astimezone(pst)

        # Extract the summary from the markdown content
        summary = extract_summary_from_markdown(markdown_content)

        # Prepare data payload
        data = {
            "Title": {"title": [{"text": {"content": title}}]},
            "Summary": {"rich_text": [{"text": {"content": summary}}]},
            "Published": {"date": {"start": file_date_california.isoformat(), "end": None}}
        }

        # Convert markdown to Notion blocks
        notion_blocks = markdown_to_notion_blocks(markdown_content)

        # Sending the request to Notion
        response = create_page(data, notion_blocks)
        if response.status_code == 200:
            print(f"Journal '{title}' uploaded successfully with content!")
        else:
            print(f"Error uploading journal '{title}': {response.text}")

if __name__ == '__main__':
    process_markdown_files()
