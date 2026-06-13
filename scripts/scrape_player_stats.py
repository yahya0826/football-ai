#!/usr/bin/env python3
"""
World Cup 2026 Player Stats Scraper
Uses Selenium + Chrome to scrape player data from Transfermarkt
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
from selenium.webdriver.common.action_chains import ActionChains

# Paths
CHROME_BINARY = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROMEDRIVER_PATH = r"C:\Users\ASUS\football-ai\backend\venv\Lib\site-packages\seleniumbase\drivers\chromedriver.exe"
SQUAD_FILE = r"C:\Users\ASUS\football-ai\data\worldcup2026\squads\squad_data.json"
OUTPUT_DIR = r"C:\Users\ASUS\football-ai\data\worldcup2026\player_stats"

def init_driver():
    """Initialize Chrome with options"""
    options = Options()
    options.binary_location = CHROME_BINARY
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    # Anti-detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        """
    })

    return driver

def get_player_url(player_name_en, club, position):
    """Search for player on Transfermarkt"""
    # Map positions for Transfermarkt
    pos_map = {"GK": "Tor", "DF": "Abwehr", "MF": "Mittelfeld", "FW": "Sturm"}
    pos_suffix = pos_map.get(position, "")

    return f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?W_String={player_name_en.replace(' ', '+')}"

def parse_transfermarkt_stats(driver, url, player_name):
    """Parse player stats from Transfermarkt"""
    driver.get(url)
    time.sleep(3)

    try:
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Look for player link in results
        results = driver.find_elements(By.CSS_SELECTOR, ".responsive-table a")
        for result in results:
            href = result.get_attribute("href")
            if href and "/profil/spieler/" in href:
                # Visit player page
                result.click()
                time.sleep(3)
                return extract_player_page_data(driver, player_name)

        return None

    except Exception as e:
        print(f"  Error parsing {player_name}: {e}")
        return None

def extract_player_page_data(driver, player_name):
    """Extract detailed stats from player page"""
    data = {
        "player_name": player_name,
        "market_value": None,
        "stats": {}
    }

    try:
        # Get market value
        try:
            value_elem = driver.find_element(By.CSS_SELECTOR, ".tm-player-market-value__value")
            data["market_value"] = value_elem.text.strip()
        except:
            pass

        # Get stats from various categories
        stat_categories = {
            "current_season": {},
            "career_stats": {},
            "detailed_stats": {}
        }

        # Try to get current season stats
        tables = driver.find_elements(By.CSS_SELECTOR, ".tm-player-statistical-data")
        for table in tables:
            try:
                category = table.find_element(By.CSS_SELECTOR, ".tm-player-statistical-data__category")
                rows = table.find_elements(By.CSS_SELECTOR, ".tm-player-statistical-data__row")

                category_text = category.text.strip()
                category_data = {}

                for row in rows:
                    cols = row.find_elements(By.CSS_SELECTOR, "td")
                    if len(cols) >= 2:
                        stat_name = cols[0].text.strip()
                        stat_value = cols[1].text.strip()
                        category_data[stat_name] = stat_value

                if category_data:
                    stat_categories[category_text] = category_data
            except:
                continue

        data["stats"] = stat_categories

    except Exception as e:
        print(f"  Error extracting page data for {player_name}: {e}")

    return data

def scrape_all_players():
    """Main scraping function"""
    # Load squad data
    with open(SQUAD_FILE, "r", encoding="utf-8") as f:
        squads = json.load(f)

    # Initialize driver
    driver = init_driver()
    print("Chrome driver initialized")

    all_player_data = {}

    # Process each team
    for team in squads:
        team_name = team["team_en"]
        print(f"\n{'='*60}")
        print(f"Processing {team_name} ({len(team['squad'])} players)")
        print(f"{'='*60}")

        team_players = []

        for i, player in enumerate(team["squad"]):
            player_name_en = player["name_en"]
            position = player.get("position", "")
            club = player.get("club", "")

            print(f"[{i+1}/{len(team['squad'])}] {player_name_en} ({position}) - {club}")

            # Get player URL
            url = get_player_url(player_name_en, club, position)

            # Scrape data
            player_data = parse_transfermarkt_stats(driver, url, player_name_en)

            if player_data:
                print(f"  -> Found data for {player_name_en}")
                team_players.append(player_data)
            else:
                print(f"  -> No data found for {player_name_en}")

            time.sleep(2)  # Rate limiting

        all_player_data[team_name] = {
            "team_cn": team["team_cn"],
            "fifa_code": team["fifa_code"],
            "players": team_players
        }

        # Save intermediate results
        output_file = os.path.join(OUTPUT_DIR, f"{team['fifa_code']}_players.json")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "team_cn": team["team_cn"],
                "team_en": team_name,
                "fifa_code": team["fifa_code"],
                "players": team_players
            }, f, ensure_ascii=False, indent=2)
        print(f"  Saved to {output_file}")

    driver.quit()

    # Save combined data
    combined_file = os.path.join(OUTPUT_DIR, "all_players_combined.json")
    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(all_player_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"Scraping complete! Combined data saved to {combined_file}")
    print(f"{'='*60}")

if __name__ == "__main__":
    scrape_all_players()