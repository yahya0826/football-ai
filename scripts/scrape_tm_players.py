#!/usr/bin/env python3
"""
World Cup 2026 Player Stats - Transfermarkt Extractor
Extracts profile and basic stats from Transfermarkt using Selenium
"""

import json
import time
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

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

    service = Service(executable_path=CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)

def extract_player_data(driver, player_id=None, search_name=None):
    """Extract player data from Transfermarkt"""
    result = {
        "profile": {},
        "stats": {},
        "market_value": None,
        "url": None
    }

    try:
        # Try direct player URL first
        if player_id:
            url = f"https://www.transfermarkt.com/-/profil/spieler/{player_id}"
            driver.get(url)
            time.sleep(4)

            if "/profil/spieler/" in driver.current_url:
                result["url"] = driver.current_url

                # Get body text
                body_text = driver.find_element(By.TAG_NAME, "body").text

                # Extract key info from text
                lines = body_text.split("\n")
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line.startswith("Date of birth"):
                        result["profile"]["date_of_birth"] = line.split(":")[-1].strip() if ":" in line else ""
                    elif line.startswith("Place of birth"):
                        result["profile"]["birth_place"] = line.split(":")[-1].strip() if ":" in line else ""
                    elif line.startswith("Height"):
                        result["profile"]["height"] = line.split(":")[-1].strip() if ":" in line else ""
                    elif line.startswith("Citizenship"):
                        result["profile"]["citizenship"] = line.split(":")[-1].strip() if ":" in line else ""
                    elif line.startswith("Position"):
                        result["profile"]["position"] = line.split(":")[-1].strip() if ":" in line else ""
                    elif line.startswith("Foot"):
                        result["profile"]["foot"] = line.split(":")[-1].strip() if ":" in line else ""
                    elif line.startswith("Current club"):
                        result["profile"]["current_club"] = line.split(":")[-1].strip() if ":" in line else ""
                    elif "Caps/Goals:" in line:
                        result["profile"]["caps_goals"] = line.split("Caps/Goals:")[-1].strip()

                # Look for market value
                mv_match = re.search(r"([\d.]+)m", body_text)
                if mv_match:
                    result["market_value"] = f"{mv_match.group(1)}m"

                # Try to get stats section
                driver.get(driver.current_url + "/statistik")
                time.sleep(4)

                # Parse stats page
                body_text = driver.find_element(By.TAG_NAME, "body").text

                # Extract season stats
                stats_patterns = {
                    "appearances": r"Appearances[\s:]*(\d+)",
                    "goals": r"Goals[\s:]*(\d+)",
                    "assists": r"Assists[\s:]*(\d+)",
                    "yellow_cards": r"Yellow cards[\s:]*(\d+)",
                    "red_cards": r"Red cards[\s:]*(\d+)",
                    "minutes": r"(\d+)[\s]*Minutes",
                }

                for stat, pattern in stats_patterns.items():
                    match = re.search(pattern, body_text)
                    if match:
                        result["stats"][stat] = match.group(1)

        # If no direct URL, search
        elif search_name:
            search_url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?W_String={search_name.replace(' ', '+')}"
            driver.get(search_url)
            time.sleep(3)

            # Find player link
            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/profil/spieler/']")
            if links:
                href = links[0].get_attribute("href")
                result["url"] = href

                # Extract player ID from URL
                id_match = re.search(r"/profil/spieler/(\d+)", href)
                if id_match:
                    player_id = id_match.group(1)
                    return extract_player_data(driver, player_id=player_id)

    except Exception as e:
        result["error"] = str(e)

    return result

def build_player_url_map():
    """Known Transfermarkt player IDs for key players"""
    # Map of known player URLs
    player_urls = {
        "Son Heung-min": "https://www.transfermarkt.com/heung-min-son/profil/spieler/91845",
        "Kim Min-jae": "https://www.transfermarkt.com/kim-min-jae/profil/spieler/446466",
        "Lee Kang-in": "https://www.transfermarkt.com/lee-kang-in/profil/spieler/654552",
        "Hwang Hee-chan": "https://www.transfermarkt.com/hwang-hee-chan/profil/spieler/196948",
        "Bruno Guimarães": "https://www.transfermarkt.com/bruno-guimaraes/profil/spieler/383487",
        "Casemiro": "https://www.transfermarkt.com/casemiro/profil/spieler/125700",
        "Alisson": "https://www.transfermarkt.com/alisson/profil/spieler/92157",
        "Neymar Jr": "https://www.transfermarkt.com/neymar/profil/spieler/68290",
        "Vinícius Júnior": "https://www.transfermarkt.com/vinicius-junior/profil/spieler/643712",
        "Marquinhos": "https://www.transfermarkt.com/marquinhos/profil/spieler/181365",
        "Gabriel Magalhães": "https://www.transfermarkt.com/gabriel-magalhaes/profil/spieler/368193",
        "Kylian Mbappé": "https://www.transfermarkt.com/kylian-mbappe/profil/spieler/278987",
        "Antoine Griezmann": "https://www.transfermarkt.com/antoine-griezmann/profil/spieler/98212",
        "Ousmane Dembélé": "https://www.transfermarkt.com/ousmane-dembele/profil/spieler/414765",
        "Randal Kolo Muani": "https://www.transfermarkt.com/randal-kolo-muani/profil/spieler/625712",
        "Jamal Musiala": "https://www.transfermarkt.com/jamal-musiala/profil/spieler/356317",
        "Florian Wirtz": "https://www.transfermarkt.com/florian-wirtz/profil/spieler/514103",
        "Leroy Sané": "https://www.transfermarkt.com/leroy-sane/profil/spieler/205012",
        "Bukayo Saka": "https://www.transfermarkt.com/bukayo-saka/profil/spieler/433177",
        "Phil Foden": "https://www.transfermarkt.com/phil-foden/profil/spieler/335759",
        "Declan Rice": "https://www.transfermarkt.com/declan-rice/profil/spieler/197228",
        "Harry Kane": "https://www.transfermarkt.com/harry-kane/profil/spieler/118098",
        "Bernardo Silva": "https://www.transfermarkt.com/bernardo-silva/profil/spieler/321233",
        "Bruno Fernandes": "https://www.transfermarkt.com/bruno-fernandes/profil/spieler/240671",
        "Rúben Dias": "https://www.transfermarkt.com/ruben-dias/profil/spieler/388270",
        "Luka Modrić": "https://www.transfermarkt.com/luka-modric/profil/spieler/27904",
        "Ivan Perišić": "https://www.transfermarkt.com/ivan-perisic/profil/spieler/47816",
    }
    return player_urls

def scrape_team_players(team_data, player_url_map):
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

        print(f"  {name_en} ({position})")

        player_result = {
            "name_en": name_en,
            "name_cn": name_cn,
            "position": position,
            "club": club,
            "transfermarkt": {}
        }

        # Check if we have a known URL
        if name_en in player_url_map:
            player_result["transfermarkt"]["url"] = player_url_map[name_en]

            # Extract player ID
            id_match = re.search(r"/profil/spieler/(\d+)", player_url_map[name_en])
            if id_match:
                player_id = id_match.group(1)
                player_result["transfermarkt"] = extract_player_data(driver, player_id=player_id)
        else:
            # Try search
            player_result["transfermarkt"] = extract_player_data(driver, search_name=name_en)

        # Add to team results
        team_results["players"].append(player_result)

        # Rate limiting
        time.sleep(1.5)

    driver.quit()
    return team_results

def main():
    # Load squads
    with open(SQUAD_FILE, "r", encoding="utf-8") as f:
        squads = json.load(f)

    print(f"Loaded {len(squads)} teams with confirmed squads")

    # Build player URL map
    player_url_map = build_player_url_map()
    print(f"Known player URLs: {len(player_url_map)}")

    # Scrape each team
    for team in squads:
        output_file = os.path.join(OUTPUT_DIR, f"{team['fifa_code']}_players.json")

        # Check if already scraped
        if os.path.exists(output_file):
            print(f"\nSkipping {team['team_en']} - already exists")
            continue

        print(f"\n{'='*60}")
        print(f"Processing: {team['team_en']} ({team['fifa_code']})")
        print(f"{'='*60}")

        team_result = scrape_team_players(team, player_url_map)

        # Save team results
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(team_result, f, ensure_ascii=False, indent=2)

        print(f"Saved to {output_file}")

    # Save combined data
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
    print(f"Combined file: {combined_file}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()