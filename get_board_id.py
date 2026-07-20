from playwright.sync_api import sync_playwright
import re

BOARD_URL = "https://in.pinterest.com/upsceducationalwebsite/upsc-polity-practice/"

print(f"Scraping ID directly from: {BOARD_URL}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(BOARD_URL, wait_until="domcontentloaded")
    
    html_content = page.content()
    
    match = re.search(r'"board_id":"(\d+)"', html_content)
    
    if match:
        print("\n✅ SUCCESS!")
        print(f"🔑 Board ID: {match.group(1)}\n")
    else:
        print("\n❌ Could not find the Board ID. Make sure the board is public and the URL is correct.")
        
    browser.close()
