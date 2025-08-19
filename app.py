import time
import math
import random
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync


def human_delay(a=3, b=7):
    time.sleep(random.uniform(a, b))


url = "https://www.alltrails.com/parks/us/arizona/petrified-forest-national-park"
initial_results = 10
results_per_click = 10

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=[
        "--disable-blink-features=AutomationControlled",
        "--start-maximized"
    ])

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36"
    ]

    context = browser.new_context(
        user_agent=random.choice(user_agents),
        viewport={"width": 1280, "height": 800},
        locale="en-US",
        timezone_id="America/New_York",
        geolocation={"latitude": 40.7128, "longitude": -74.0060},
        permissions=["geolocation"],
    )

    page = context.new_page()
    stealth_sync(page)

    print(f"[*] Opening: {url}")
    page.goto("https://www.alltrails.com", timeout=60000)
    human_delay(2, 4)
    page.goto(url, timeout=60000)
    human_delay(4, 7)

    # Get total number of results
    max_results = 0
    try:
        showing_div = page.query_selector("div.TopResults_showing__mNXH8")
        if showing_div:
            text_parts = showing_div.inner_text().split()
            for part in text_parts:
                if part.isdigit():
                    max_results = int(part)
        print(f"[+] Total results: {max_results}")
    except Exception as e:
        print(f"[!] Failed to extract max results: {e}")

    # Calculate how many times to click
    if max_results > 0 and max_results > initial_results:
        max_clicks = math.ceil((max_results - initial_results) / results_per_click)
    else:
        max_clicks = 0

    print(f"[+] Will attempt {max_clicks} Show More clicks")

    # Click the Show More button if needed
    clicks = 0
    while clicks < max_clicks:
        try:
            btn = page.query_selector("div.TopResults_showMoreSection__FLSrW button.styles_button__KagQX.styles_md__2wnXO.styles_primary___7R_x")
            if btn:
                btn.scroll_into_view_if_needed()
                btn.click()
                clicks += 1
                print(f"[+] Clicked 'Show more' ({clicks}/{max_clicks})")
                human_delay(8, 12)
            else:
                print("[!] Show more button not found.")
                break
        except Exception as e:
            print(f"[!] Error clicking button: {e}")
            break

    # Extract links from loaded page
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")
    result_divs = soup.find_all("div", class_=lambda x: x and x.startswith("TopResults_resultCardContent"))

    links = []
    for div in result_divs:
        a_tag = div.find("a", href=True)
        if a_tag:
            links.append(a_tag["href"])

    print("\n=== Extracted Trail Links ===")
    for link in links:
        print(link)

    browser.close()
