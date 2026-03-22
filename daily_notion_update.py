# Add the date header in a Notion page


import requests
from datetime import datetime

NOTION_TOKEN = 'abc'
PAGE_ID = 'xyz'

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def append_block(block_data):
    url = f"https://api.notion.com/v1/blocks/{PAGE_ID}/children"
    res = requests.patch(url, headers=headers, json={"children": block_data})
    if res.status_code != 200:
        print("Error:", res.text)
    else:
        print("Block added.")

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    block_data = [
        {
            "object": "block",
            "type": "divider",
            "divider": {}
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": today
                    }
                }]
            }
        }
    ]
    append_block(block_data)

if __name__ == "__main__":
    main()
