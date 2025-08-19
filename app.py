from flask import Flask, request, jsonify
import time
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

@app.route("/scrape-alltrails", methods=["POST"])
def scrape_alltrails():
    data = request.get_json(force=True, silent=True) or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    # Install matching ChromeDriver
    chromedriver_autoinstaller.install()

    # Setup Chrome in headless mode
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Launch the driver
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        time.sleep(5)

        max_clicks = 10
        clicks = 0

        while clicks < max_clicks:
            try:
                show_more_btn = driver.find_element(
                    By.CSS_SELECTOR,
                    "div.TopResults_showMoreSection__FLSrW button.styles_button__KagQX.styles_md__2wnXO.styles_primary___7R_x"
                )
                driver.execute_script("arguments[0].scrollIntoView();", show_more_btn)
                driver.execute_script("arguments[0].click();", show_more_btn)
                clicks += 1
                time.sleep(10)
            except Exception:
                break

        soup = BeautifulSoup(driver.page_source, "html.parser")
        result_divs = soup.find_all("div", class_=lambda x: x and x.startswith("TopResults_resultCardContent"))

        links = []
        for div in result_divs:
            a_tag = div.find("a", href=True)
            if a_tag:
                links.append(a_tag["href"])

        return jsonify([{"links": links}])

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        driver.quit()

# Support dynamic port for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
