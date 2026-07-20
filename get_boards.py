import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("PINTEREST_ACCESS_TOKEN")
url = "https://api.pinterest.com/v5/boards"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("Fetching boards from Pinterest...")
response = requests.get(url, headers=headers)

if response.status_code == 200:
    boards = response.json().get("items", [])
    if not boards:
        print("No boards found! Make sure you have created at least one board on your Pinterest account.")
    else:
        print("\n--- YOUR PINTEREST BOARDS ---")
        for b in boards:
            print(f"📌 Board Name: {b['name']}")
            print(f"🔑 Board ID:   {b['id']}\n")
else:
    print(f"API Error ({response.status_code}): {response.text}")
