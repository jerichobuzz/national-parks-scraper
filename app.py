import math
import time
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import subprocess
import os

# Force install chromium if not already
if not os.path.exists("/opt/render/.cache/ms-playwright"):
    subprocess.run(["python", "-m", "playwright", "install", "chromium"])

app = Flask(__name__)


@app.route("/scrape-alltrails", methods=["POST"])
def scrape_alltrails():
    data = request.get_json()
    url = data.get("url")
    print("🔍 Scraping URL:", url)

    if not url:
        print("❌ Missing 'url' in request")
        return jsonify({"error": "Missing 'url' in request body"}), 400

    initial_results = 10
    results_per_click = 10
    links = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            "--disable-blink-features=AutomationControlled"
        ])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/New_York",
            geolocation={"latitude": 40.7128, "longitude": -74.0060},
            permissions=["geolocation"],
        )

        page = context.new_page()
        try:
            page.goto(url, timeout=60000)
            time.sleep(5)

            # Get total number of results
            max_results = 0
            showing_div = page.query_selector("div.TopResults_showing__mNXH8")
            if showing_div:
                text_parts = showing_div.inner_text().split()
                for part in text_parts:
                    if part.isdigit():
                        max_results = int(part)
                        break
            print("📊 Max results detected:", max_results)

            if max_results > 0 and max_results > initial_results:
                max_clicks = math.ceil((max_results - initial_results) / results_per_click)
            else:
                max_clicks = 0
            print("🔁 Clicks needed:", max_clicks)

            clicks = 0
            while clicks < max_clicks:
                btn = page.query_selector("div.TopResults_showMoreSection__FLSrW button.styles_button__KagQX.styles_md__2wnXO.styles_primary___7R_x")
                if btn:
                    print(f"🖱 Clicking Show More ({clicks + 1}/{max_clicks})")
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    clicks += 1
                    time.sleep(10)
                else:
                    print("⚠️ Show More button not found")
                    break

            # Extract links
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            result_divs = soup.find_all("div", class_=lambda x: x and x.startswith("TopResults_resultCardContent"))
            print(f"🔎 Found {len(result_divs)} result cards")

            for div in result_divs:
                a_tag = div.find("a", href=True)
                if a_tag:
                    links.append(a_tag["href"])

            print(f"✅ Total links extracted: {len(links)}")

        except Exception as e:
            print("💥 Error during scraping:", str(e))
            return jsonify({"error": str(e)}), 500
        finally:
            browser.close()

    return jsonify({
        "links": links,
        "debug": {
            "max_results": max_results,
            "show_more_clicks": clicks,
            "trail_divs_found": len(result_divs),
            "url": url
        }
    })






if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
