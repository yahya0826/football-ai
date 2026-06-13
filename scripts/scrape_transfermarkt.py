#!/usr/bin/env python3
"""
World Cup 2026 Player Stats Scraper - Transfermarkt
Uses Selenium to extract player data with JavaScript rendering
"""

import json
import time
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CHROME_BINARY = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROMEDRIVER_PATH = r"C:\Users\ASUS\football-ai\backend\venv\Lib\site-packages\seleniumbase\drivers\chromedriver.exe"
SQUAD_FILE = r"C:\Users\ASUS\football-ai\data\worldcup2026\squads\squad_data.json"
OUTPUT_DIR = r"C:\Users\ASUS\football-ai\data\worldcup2026\player_stats"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def init_driver():
    options = Options()
    options.binary_location = CHROME_BINARY
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    service = Service(executable_path=CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)

def extract_player_data(driver):
    """Extract all available data from current player page"""
    data = {
        "profile": {},
        "market_value": None,
        "stats": {},
        "career": []
    }

    try:
        # Get page source after JS rendering
        html = driver.page_source

        # Extract player profile info
        try:
            name_elem = driver.find_element(By.CSS_SELECTOR, "h1[data-testid='profile-name'], h1[class*='player']")
            data["profile"]["name"] = name_elem.text.strip()
        except:
            try:
                name_elem = driver.find_element(By.CSS_SELECTOR, ".dataHeader .info-box .playerName")
                data["profile"]["name"] = name_elem.text.strip()
            except:
                pass

        # Try to find stats using data attributes
        # Transfermarkt uses data-box containers
        boxes = driver.find_elements(By.CSS_SELECTOR, "[data-box]")
        for box in boxes:
            try:
                label = box.get_attribute("data-box")
                value = box.text.strip()
                data["profile"][label] = value
            except:
                continue

        # Try multiple selectors for market value
        market_value = None
        selectors = [
            ".tm-player-market-value__value",
            "[data-market-value]",
            ".market-value",
            "span[class*='value']"
        ]
        for sel in selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, sel)
                market_value = elem.text.strip()
                break
            except:
                continue

        if market_value:
            data["market_value"] = market_value

        # Try to find stats table
        stat_tables = driver.find_elements(By.CSS_SELECTOR, "table[class*='stats']")
        for table in stat_tables[:5]:
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                table_data = {}
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 2:
                        stat = cols[0].text.strip()
                        val = cols[1].text.strip()
                        if stat and val:
                            table_data[stat] = val
                if table_data:
                    data["stats"][f"table_{len(data['stats'])}"] = table_data
            except:
                continue

        # Try to extract from page source for JSON data
        source = html
        # Look for Vue/React state data
        state_matches = re.findall(r'window\.__STATE__\s*=\s*(\{.*?\});', source, re.DOTALL)
        if state_matches:
            try:
                import ast
                state = ast.literal_eval(state_matches[0])
                data["raw_state"] = "found"
            except:
                pass

    except Exception as e:
        data["error"] = str(e)

    return data

def try_player_url(driver, name_en, player_id=None):
    """Try to access player page directly"""
    # Create Transfermarkt-style URL
    name_slug = name_en.lower().replace(" ", "-").replace(".", "").replace(",", "")

    # Try direct player ID if known
    if player_id:
        url = f"https://www.transfermarkt.com/-/profil/spieler/{player_id}"
        driver.get(url)
        time.sleep(2)
        if "profil/spieler" in driver.current_url:
            return driver.current_url

    # Try search
    search_url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?W_String={name_en.replace(' ', '+')}"
    driver.get(search_url)
    time.sleep(3)

    # Find first player link
    links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/profil/spieler/']")
    if links:
        return links[0].get_attribute("href")

    return None

def scrape_team(team_data):
    """Scrape all players for a team"""
    driver = init_driver()
    team_results = {
        "team_en": team_data["team_en"],
        "team_cn": team_data["team_cn"],
        "fifa_code": team_data["fifa_code"],
        "players": []
    }

    for player in team_data["squad"]:
        name_en = player["name_en"]
        name_cn = player.get("name_cn", "")
        position = player.get("position", "")
        club = player.get("club", "")

        print(f"  {name_en} ({position}) - {club}")

        player_result = {
            "name_en": name_en,
            "name_cn": name_cn,
            "position": position,
            "club": club,
            "transfermarkt_url": None,
            "data": {}
        }

        # Try to find player URL
        url = try_player_url(driver, name_en)
        if url:
            player_result["transfermarkt_url"] = url

            # Extract data from page
            player_result["data"] = extract_player_data(driver)
            print(f"    -> Data extracted")
        else:
            print(f"    -> No URL found")

        team_results["players"].append(player_result)
        time.sleep(1)

    driver.quit()
    return team_results

def main():
    # Load squads
    with open(SQUAD_FILE, "r", encoding="utf-8") as f:
        squads = json.load(f)

    print(f"Loaded {len(squads)} teams with confirmed squads")
    print(f"Output directory: {OUTPUT_DIR}")

    # Scrape each team
    for team in squads:
        print(f"\n{'='*60}")
        print(f"Processing: {team['team_en']} ({team['fifa_code']})")
        print(f"{'='*60}")

        team_result = scrape_team(team)

        # Save team results
        output_file = os.path.join(OUTPUT_DIR, f"{team['fifa_code']}_players.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(team_result, f, ensure_ascii=False, indent=2)
        print(f"Saved to {output_file}")

    # Save combined
    all_data = []
    for team in squads:
        team_file = os.path.join(OUTPUT_DIR, f"{team['fifa_code']}_players.json")
        if os.path.exists(team_file):
            with open(team_file, "r", encoding="utf-8") as f:
                all_data.append(json.load(f))

    combined_file = os.path.join(OUTPUT_DIR, "all_players.json")
    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"Complete! Data saved to {OUTPUT_DIR}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()