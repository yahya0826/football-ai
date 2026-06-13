#!/usr/bin/env python3
"""
World Cup 2026 - Player Stats Extraction from Transfermarkt
Extracts profile, stats, and market values using Selenium
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

def extract_stats(driver, url):
    """Extract player stats from stats page"""
    driver.get(url)
    time.sleep(5)

    result = {
        "profile_url": url,
        "basic_info": {},
        "current_season": {},
        "market_value": None
    }

    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text

        # Encode to ASCII to avoid encoding issues
        body_text = body_text.encode('ascii', 'replace').decode('ascii')

        lines = [l.strip() for l in body_text.split('\n') if l.strip()]

        # Extract basic info from profile section
        info_patterns = {
            "date_of_birth": r"Date of birth/Age:\s*([\d/]+)",
            "place_of_birth": r"Place of birth:\s*([\w\s,]+)",
            "height": r"Height:\s*([\d,\.]+\s*m)",
            "citizenship": r"Citizenship:\s*([\w,\s]+)",
            "position": r"Position:\s*([\w\s-]+)",
            "foot": r"Foot:\s*(\w+)",
            "caps_goals": r"Caps/Goals:\s*([\d\s/]+)",
        }

        for key, pattern in info_patterns.items():
            match = re.search(pattern, body_text)
            if match:
                result["basic_info"][key] = match.group(1).strip()

        # Extract market value
        mv_match = re.search(r"([\d.]+)\.m", body_text)
        if mv_match:
            result["market_value"] = f"{mv_match.group(1)}m"

        # Extract current season stats
        season_patterns = {
            "appearances": r"Appearances\s*(\d+)",
            "goals": r"Goals\s*(\d+)",
            "assists": r"Assists\s*(\d+)",
            "yellow_cards": r"Yellow cards\s*(\d+)",
            "second_yellows": r"Second yellows\s*(\d+)",
            "red_cards": r"Red cards\s*(\d+)",
            "minutes_percent": r"Minutes\s*(\d+)",
            "starting_eleven_percent": r"Starting eleven\s*(\d+)",
        }

        for key, pattern in season_patterns.items():
            match = re.search(pattern, body_text)
            if match:
                result["current_season"][key] = match.group(1).strip()

        # Get league info
        league_match = re.search(r"(\w+\s*\d{4})\s*\n\s*(\d+)\s*\n\s*Appearences", body_text, re.DOTALL)
        if league_match:
            result["current_season"]["league"] = league_match.group(1).strip()

    except Exception as e:
        result["error"] = str(e)

    return result

def scrape_player(player_name, player_url, driver):
    """Scrape a single player's data"""
    try:
        # Try profile page first
        profile_url = player_url.replace("/statistik", "")
        stats_url = profile_url + "/statistik"

        data = extract_stats(driver, stats_url)
        data["name_en"] = player_name
        data["profile_url"] = profile_url

        return data

    except Exception as e:
        return {"name_en": player_name, "error": str(e)}

def main():
    # Load squads
    with open(SQUAD_FILE, "r", encoding="utf-8") as f:
        squads = json.load(f)

    # Known Transfermarkt URLs (key players)
    KNOWN_URLS = {
        # South Korea
        "Son Heung-min": "https://www.transfermarkt.com/heung-min-son/profil/spieler/91845",
        "Kim Min-jae": "https://www.transfermarkt.com/kim-min-jae/profil/spieler/446466",
        "Lee Kang-in": "https://www.transfermarkt.com/lee-kang-in/profil/spieler/654552",
        "Hwang Hee-chan": "https://www.transfermarkt.com/hwang-hee-chan/profil/spieler/196948",
        "Kim Seong-gyu": "https://www.transfermarkt.com/kim-seong-gyu/profil/spieler/124948",
        "Park Jin-seop": "https://www.transfermarkt.com/park-jin-seop/profil/spieler/391259",
        "Seol Young-woo": "https://www.transfermarkt.com/seol-young-woo/profil/spieler/877237",
        "Yang Hyun-jun": "https://www.transfermarkt.com/yang-hyun-jun/profil/spieler/866983",
        "Bae Jun-ho": "https://www.transfermarkt.com/bae-jun-ho/profil/spieler/1067549",
        # Japan
        "Takehiro Tomiyasu": "https://www.transfermarkt.com/takehiro-tomiyasu/profil/spieler/394359",
        "Daichi Kamada": "https://www.transfermarkt.com/daichi-kamada/profil/spieler/274601",
        "Wataru Endo": "https://www.transfermarkt.com/wataru-endo/profil/spieler/122665",
        "Kubo Takefusa": "https://www.transfermarkt.com/kubo-takefusa/profil/spieler/418658",
        "Ritsu Doan": "https://www.transfermarkt.com/ritsu-doan/profil/spieler/414351",
        "Junya Ito": "https://www.transfermarkt.com/junya-ito/profil/spieler/337441",
        "Koki Ueda": "https://www.transfermarkt.com/koki-ueda/profil/spieler/396412",
        # Brazil
        "Alisson": "https://www.transfermarkt.com/alisson/profil/spieler/92157",
        "Ederson": "https://www.transfermarkt.com/ederson/profil/spieler/238451",
        "Gabriel Magalhães": "https://www.transfermarkt.com/gabriel-magalhaes/profil/spieler/368193",
        "Marquinhos": "https://www.transfermarkt.com/marquinhos/profil/spieler/181365",
        "Bruno Guimarães": "https://www.transfermarkt.com/bruno-guimaraes/profil/spieler/383487",
        "Casemiro": "https://www.transfermarkt.com/casemiro/profil/spieler/125700",
        "Neymar Jr": "https://www.transfermarkt.com/neymar/profil/spieler/68290",
        "Vinícius Júnior": "https://www.transfermarkt.com/vinicius-junior/profil/spieler/643712",
        "Rodri": "https://www.transfermarkt.com/rodri/profil/spieler/367539",
        "Raphinha": "https://www.transfermarkt.com/raphinha/profil/spieler/402629",
        # France
        "Kylian Mbappé": "https://www.transfermarkt.com/kylian-mbappe/profil/spieler/278987",
        "Antoine Griezmann": "https://www.transfermarkt.com/antoine-griezmann/profil/spieler/98212",
        "Ousmane Dembélé": "https://www.transfermarkt.com/ousmane-dembele/profil/spieler/414765",
        "William Saliba": "https://www.transfermarkt.com/william-saliba/profil/spieler/405228",
        "Aurélien Tchouaméni": "https://www.transfermarkt.com/aurelien-tchouameni/profil/spieler/444063",
        "Eduardo Camavinga": "https://www.transfermarkt.com/eduardo-camavinga/profil/spieler/625695",
        # Germany
        "Jamal Musiala": "https://www.transfermarkt.com/jamal-musiala/profil/spieler/356317",
        "Florian Wirtz": "https://www.transfermarkt.com/florian-wirtz/profil/spieler/514103",
        "Leroy Sané": "https://www.transfermarkt.com/leroy-sane/profil/spieler/205012",
        "Kai Havertz": "https://www.transfermarkt.com/kai-havertz/profil/spieler/236537",
        "Joshua Kimmich": "https://www.transfermarkt.com/joshua-kimmich/profil/spieler/182452",
        "Toni Kroos": "https://www.transfermarkt.com/toni-kroos/profil/spieler/56499",
        # England
        "Bukayo Saka": "https://www.transfermarkt.com/bukayo-saka/profil/spieler/433177",
        "Phil Foden": "https://www.transfermarkt.com/phil-foden/profil/spieler/335759",
        "Declan Rice": "https://www.transfermarkt.com/declan-rice/profil/spieler/197228",
        "Harry Kane": "https://www.transfermarkt.com/harry-kane/profil/spieler/118098",
        "Jude Bellingham": "https://www.transfermarkt.com/jude-bellingham/profil/spieler/581678",
        "Cole Palmer": "https://www.transfermarkt.com/cole-palmer/profil/spieler/629589",
        # Portugal
        "Bernardo Silva": "https://www.transfermarkt.com/bernardo-silva/profil/spieler/321233",
        "Bruno Fernandes": "https://www.transfermarkt.com/bruno-fernandes/profil/spieler/240671",
        "Rúben Dias": "https://www.transfermarkt.com/ruben-dias/profil/spieler/388270",
        "Rafael Leão": "https://www.transfermarkt.com/rafael-leao/profil/spieler/472046",
        "Vitinha": "https://www.transfermarkt.com/vitinha/profil/spieler/600118",
        "Diogo Jota": "https://www.transfermarkt.com/diogo-jota/profil/spieler/379782",
        # Croatia
        "Luka Modrić": "https://www.transfermarkt.com/luka-modric/profil/spieler/27904",
        "Ivan Perišić": "https://www.transfermarkt.com/ivan-perisic/profil/spieler/47816",
        "Marcelo Brozović": "https://www.transfermarkt.com/marcelo-brozovic/profil/spieler/108037",
        "Mateo Kovačić": "https://www.transfermarkt.com/mateo-kovacic/profil/spieler/178296",
        "Andrej Kramarić": "https://www.transfermarkt.com/andrej-kramaric/profil/spieler/94271",
        "Lovro Majer": "https://www.transfermarkt.com/lovro-majer/profil/spieler/504466",
    }

    # Initialize driver
    driver = init_driver()
    print("Driver initialized")
    print(f"Processing {len(squads)} teams...")

    all_results = []

    for team in squads:
        print(f"\n{'='*60}")
        print(f"Team: {team['team_en']} ({team['fifa_code']})")
        print(f"{'='*60}")

        team_result = {
            "team_en": team["team_en"],
            "team_cn": team["team_cn"],
            "fifa_code": team["fifa_code"],
            "coach": team["coach"],
            "group": team["group"],
            "players": []
        }

        for player in team["squad"]:
            name_en = player["name_en"]
            name_cn = player.get("name_cn", "")
            position = player.get("position", "")
            club = player.get("club", "")

            name_en_clean = name_en.encode('ascii', 'replace').decode('ascii')
            print(f"  {name_en_clean} ({position})", end="", flush=True)

            player_data = {
                "name_en": name_en,
                "name_cn": name_cn.encode('ascii', 'replace').decode('ascii') if name_cn else "",
                "position": position,
                "club": club.encode('ascii', 'replace').decode('ascii') if club else "",
                "age": player.get("age"),
                "club_country": player.get("club_country", ""),
            }

            # Check if we have a known URL
            if name_en in KNOWN_URLS:
                url = KNOWN_URLS[name_en]
                player_data["transfermarkt_url"] = url

                # Scrape data
                stats_data = extract_stats(driver, url + "/statistik")
                player_data.update(stats_data)

                print(f" -> MV: {stats_data.get('market_value', 'N/A')}")
            else:
                print(f" -> No URL known")

            team_result["players"].append(player_data)

        all_results.append(team_result)

        # Save team file
        team_file = os.path.join(OUTPUT_DIR, f"{team['fifa_code']}_players.json")
        with open(team_file, "w", encoding="utf-8") as f:
            json.dump(team_result, f, ensure_ascii=False, indent=2)

        print(f"Saved to {team_file}")

        # Rate limit between teams
        time.sleep(2)

    # Save combined file
    combined_file = os.path.join(OUTPUT_DIR, "all_players.json")
    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    driver.quit()

    print(f"\n{'='*60}")
    print(f"Complete! Data saved to {OUTPUT_DIR}")
    print(f"Total players scraped: {sum(len(t['players']) for t in all_results)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()