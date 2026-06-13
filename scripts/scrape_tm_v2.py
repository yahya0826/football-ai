#!/usr/bin/env python3
"""
World Cup 2026 - Improved Player Stats Extraction
Better regex patterns and more player URLs
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
    """Extract player stats from stats page - improved version"""
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

        # Replace problematic characters for safe parsing
        body_text = body_text.replace('\n', ' | ').replace('\r', ' ')

        # Extract market value - pattern: ?XX.XXm
        mv_match = re.search(r'\?(\d+\.\d+)m', body_text)
        if mv_match:
            result["market_value"] = f"{mv_match.group(1)}m"

        # Extract basic info with better patterns
        info_patterns = {
            "date_of_birth": r"Date of birth/Age:\s*([\d/]+(?:\s*\(\d+\))?)",
            "place_of_birth": r"Place of birth:\s*([A-Za-z\s,]+?)(?:\s*Citizenship)",
            "height": r"Height:\s*([\d,\.]+\s*m)",
            "position": r"Position:\s*([A-Za-z\s-]+?)(?:\s*Foot|\s*Current)",
            "foot": r"Foot:\s*(\w+)",
            "caps_goals": r"Caps/Goals:\s*([\d\s/]+)",
        }

        for key, pattern in info_patterns.items():
            match = re.search(pattern, body_text)
            if match:
                value = match.group(1).strip()
                # Clean up pipes and extra spaces
                value = re.sub(r'\s*\|\s*', ' ', value).strip()
                result["basic_info"][key] = value

        # Extract current season stats
        season_patterns = {
            "appearances": r"Appearances\s*(\d+)",
            "goals": r"Goals\s*(\d+)",
            "assists": r"Assists\s*(\d+)",
            "yellow_cards": r"Yellow cards\s*(\d+)",
            "second_yellows": r"Second yellows\s*(\d+)",
            "red_cards": r"Red cards\s*(\d+)",
        }

        for key, pattern in season_patterns.items():
            match = re.search(pattern, body_text)
            if match:
                result["current_season"][key] = match.group(1).strip()

    except Exception as e:
        result["error"] = str(e)

    return result

# Expanded player URL map with Transfermarkt IDs
PLAYER_URLS = {
    # South Korea
    "Kim Seong-gyu": "https://www.transfermarkt.com/kim-seong-gyu/profil/spieler/124948",
    "Jo Hyeon-woo": "https://www.transfermarkt.com/jo-hyeon-woo/profil/spieler/136548",
    "Song Bum-keun": "https://www.transfermarkt.com/song-bum-keun/profil/spieler/477351",
    "Kim Min-jae": "https://www.transfermarkt.com/kim-min-jae/profil/spieler/446466",
    "Cho Yu-min": "https://www.transfermarkt.com/cho-yu-min/profil/spieler/542603",
    "Lee Han-been": "https://www.transfermarkt.com/lee-han-been/profil/spieler/1171201",
    "Lee Ki-hyuk": "https://www.transfermarkt.com/lee-ki-hyuk/profil/spieler/1093646",
    "Kim Tae-hyun": "https://www.transfermarkt.com/kim-tae-hyun/profil/spieler/1011799",
    "Lee Tae-soo": "https://www.transfermarkt.com/lee-tae-soo/profil/spieler/821677",
    "Seol Young-woo": "https://www.transfermarkt.com/seol-young-woo/profil/spieler/877237",
    "Yankuba Ceesay": "https://www.transfermarkt.com/yankuba-ceesay/profil/spieler/1213794",
    "Kim Moon-hwan": "https://www.transfermarkt.com/kim-moon-hwan/profil/spieler/390179",
    "Park Jin-seop": "https://www.transfermarkt.com/park-jin-seop/profil/spieler/391259",
    "Yang Hyun-jun": "https://www.transfermarkt.com/yang-hyun-jun/profil/spieler/866983",
    "Baek Sung-ho": "https://www.transfermarkt.com/baek-sung-ho/profil/spieler/1182908",
    "Hwang In-beom": "https://www.transfermarkt.com/hwang-in-beom/profil/spieler/391231",
    "Lee Dong-gyeong": "https://www.transfermarkt.com/lee-dong-gyeong/profil/spieler/391236",
    "Kim Jin-kyu": "https://www.transfermarkt.com/kim-jin-kyu/profil/spieler/977825",
    "Bae Jun-ho": "https://www.transfermarkt.com/bae-jun-ho/profil/spieler/1067549",
    "Um Ji-sung": "https://www.transfermarkt.com/um-ji-sung/profil/spieler/1031239",
    "Hwang Hee-chan": "https://www.transfermarkt.com/hwang-hee-chan/profil/spieler/196948",
    "Lee Jae-sung": "https://www.transfermarkt.com/lee-jae-sung/profil/spieler/196949",
    "Lee Kang-in": "https://www.transfermarkt.com/lee-kang-in/profil/spieler/654552",
    "Son Heung-min": "https://www.transfermarkt.com/heung-min-son/profil/spieler/91845",
    "Oh Hyun-kyu": "https://www.transfermarkt.com/oh-hyun-kyu/profil/spieler/1028912",
    "Cho Gue-sung": "https://www.transfermarkt.com/cho-gue-sung/profil/spieler/624658",

    # Japan
    "Hayakawa Yuki": "https://www.transfermarkt.com/hayakawa-yuki/profil/spieler/960821",
    "Suzuki Bart": "https://www.transfermarkt.com/suzuki-bart/profil/spieler/1070698",
    "Osako Kensei": "https://www.transfermarkt.com/osako-kensei/profil/spieler/481165",
    "Nagatomo Yuto": "https://www.transfermarkt.com/nagatomo-yuto/profil/spieler/74460",
    "Taniguchi Shogo": "https://www.transfermarkt.com/taniguchi-shogo/profil/spieler/275802",
    "Tomiyasu Takehiro": "https://www.transfermarkt.com/takehiro-tomiyasu/profil/spieler/394359",
    "Itakura Ko": "https://www.transfermarkt.com/itakura-ko/profil/spieler/383488",
    "Watanabe Naoki": "https://www.transfermarkt.com/watanabe-naoki/profil/spieler/383489",
    "Ito Hiroki": "https://www.transfermarkt.com/ito-hiroki/profil/spieler/856612",
    "Suzuki Junnosuke": "https://www.transfermarkt.com/suzuki-junnosuke/profil/spieler/431296",
    "Seko Ayumu": "https://www.transfermarkt.com/seko-ayumu/profil/spieler/556769",
    "Sugawara Yukinari": "https://www.transfermarkt.com/sugawara-yukinari/profil/spieler/570999",
    "Kamada Daichi": "https://www.transfermarkt.com/daichi-kamada/profil/spieler/274601",
    "Sano Kaina": "https://www.transfermarkt.com/sano-kaina/profil/spieler/1029346",
    "Tanaka Ao": "https://www.transfermarkt.com/tanaka-ao/profil/spieler/432900",
    "Endo Wataru": "https://www.transfermarkt.com/wataru-endo/profil/spieler/122665",
    "Nakamura Kouta": "https://www.transfermarkt.com/nakamura-kouta/profil/spieler/657815",
    "Doan Ritsu": "https://www.transfermarkt.com/ritsu-doan/profil/spieler/414351",
    "Ito Junya": "https://www.transfermarkt.com/junya-ito/profil/spieler/337441",
    "Kubo Takefusa": "https://www.transfermarkt.com/kubo-takefusa/profil/spieler/418658",
    "Suzuki Yuri": "https://www.transfermarkt.com/suzuki-yuri/profil/spieler/976736",
    "Ueda Koki": "https://www.transfermarkt.com/koki-ueda/profil/spieler/396412",
    "Ogawa Ko": "https://www.transfermarkt.com/ogawa-ko/profil/spieler/433062",
    "Maeda Daizen": "https://www.transfermarkt.com/maeda-daizen/profil/spieler/440839",
    "Shiogama Kento": "https://www.transfermarkt.com/shiogama-kento/profil/spieler/1010264",
    "Goto Keisuke": "https://www.transfermarkt.com/goto-keisuke/profil/spieler/1182012",

    # Brazil
    "Alisson": "https://www.transfermarkt.com/alisson/profil/spieler/92157",
    "Ederson": "https://www.transfermarkt.com/ederson/profil/spieler/238451",
    "Weverton": "https://www.transfermarkt.com/weverton/profil/spieler/148107",
    "Alex Sandro": "https://www.transfermarkt.com/alex-sandro/profil/spieler/98203",
    "Bremer": "https://www.transfermarkt.com/bremer/profil/spieler/411687",
    "Danilo": "https://www.transfermarkt.com/danilo/profil/spieler/126453",
    "Douglas Santos": "https://www.transfermarkt.com/douglas-santos/profil/spieler/172601",
    "Gabriel Magalhães": "https://www.transfermarkt.com/gabriel-magalhaes/profil/spieler/368193",
    "Rogério Ibañez": "https://www.transfermarkt.com/rogerio-ibannez/profil/spieler/396105",
    "Léo Pereira": "https://www.transfermarkt.com/leo-pereira/profil/spieler/291436",
    "Marquinhos": "https://www.transfermarkt.com/marquinhos/profil/spieler/181365",
    "Wesley Lima": "https://www.transfermarkt.com/wesley-lima/profil/spieler/381695",
    "Bruno Guimarães": "https://www.transfermarkt.com/bruno-guimaraes/profil/spieler/383487",
    "Casemiro": "https://www.transfermarkt.com/casemiro/profil/spieler/125700",
    "Danilo Santos": "https://www.transfermarkt.com/danilo-santos/profil/spieler/629592",
    "Fabinho": "https://www.transfermarkt.com/fabinho/profil/spieler/217699",
    "Lucas Paquetá": "https://www.transfermarkt.com/lucas-paqueta/profil/spieler/380694",
    "Neymar Jr": "https://www.transfermarkt.com/neymar/profil/spieler/68290",
    "Vinícius Júnior": "https://www.transfermarkt.com/vinicius-junior/profil/spieler/643712",
    "Rodri": "https://www.transfermarkt.com/rodri/profil/spieler/367539",
    "Raphinha": "https://www.transfermarkt.com/raphinha/profil/spieler/402629",
    "André": "https://www.transfermarkt.com/andre/profil/spieler/392004",

    # France
    "Mike Maignan": "https://www.transfermarkt.com/mike-maignan/profil/spieler/215913",
    "Alphonse Areola": "https://www.transfermarkt.com/alphonse-areola/profil/spieler/173315",
    "Luka Škriniar": "https://www.transfermarkt.com/luka-skriniar/profil/spieler/343776",
    "William Saliba": "https://www.transfermarkt.com/william-saliba/profil/spieler/405228",
    "Dayot Upamecano": "https://www.transfermarkt.com/dayot-upamecano/profil/spieler/396627",
    "Ibrahima Konaté": "https://www.transfermarkt.com/ibrahima-konate/profil/spieler/469738",
    "Jonathan Clauss": "https://www.transfermarkt.com/jonathan-clauss/profil/spieler/289366",
    "Theo Hernandez": "https://www.transfermarkt.com/theo-hernandez/profil/spieler/342867",
    "Ferland Mendy": "https://www.transfermarkt.com/ferland-mendy/profil/spieler/286770",
    "Jules Koundé": "https://www.transfermarkt.com/jules-kounde/profil/spieler/433489",
    "Aurélien Tchouaméni": "https://www.transfermarkt.com/aurelien-tchouameni/profil/spieler/444063",
    "Eduardo Camavinga": "https://www.transfermarkt.com/eduardo-camavinga/profil/spieler/625695",
    "Kylian Mbappé": "https://www.transfermarkt.com/kylian-mbappe/profil/spieler/278987",
    "Antoine Griezmann": "https://www.transfermarkt.com/antoine-griezmann/profil/spieler/98212",
    "Ousmane Dembélé": "https://www.transfermarkt.com/ousmane-dembele/profil/spieler/414765",
    "Randal Kolo Muani": "https://www.transfermarkt.com/randal-kolo-muani/profil/spieler/625712",
    "Kingsley Coman": "https://www.transfermarkt.com/kingsley-coman/profil/spieler/178153",

    # Germany
    "Manuel Neuer": "https://www.transfermarkt.com/manuel-neuer/profil/spieler/172604",
    "Bernd Leno": "https://www.transfermarkt.com/bernd-leno/profil/spieler/184645",
    "Oliver Baumann": "https://www.transfermarkt.com/oliver-baumann/profil/spieler/68411",
    "Jonathan Tah": "https://www.transfermarkt.com/jonathan-tah/profil/spieler/279375",
    "Anton Stath": "https://www.transfermarkt.com/anton-stath/profil/spieler/1224622",
    "Nico Schlotterbeck": "https://www.transfermarkt.com/nico-schlotterbeck/profil/spieler/614378",
    "Robin Gosens": "https://www.transfermarkt.com/robin-gosens/profil/spieler/333209",
    "David Raum": "https://www.transfermarkt.com/david-raum/profil/spieler/562371",
    "Joshua Kimmich": "https://www.transfermarkt.com/joshua-kimmich/profil/spieler/182452",
    "Leon Goretzka": "https://www.transfermarkt.com/leon-goretzka/profil/spieler/182450",
    "Florian Wirtz": "https://www.transfermarkt.com/florian-wirtz/profil/spieler/514103",
    "Jamal Musiala": "https://www.transfermarkt.com/jamal-musiala/profil/spieler/356317",
    "Leroy Sané": "https://www.transfermarkt.com/leroy-sane/profil/spieler/205012",
    "Kai Havertz": "https://www.transfermarkt.com/kai-havertz/profil/spieler/236537",
    "Toni Kroos": "https://www.transfermarkt.com/toni-kroos/profil/spieler/56499",
    "İlkay Gündoğan": "https://www.transfermarkt.com/ilkay-gundogan/profil/spieler/91051",

    # England
    "Jordan Pickford": "https://www.transfermarkt.com/jordan-pickford/profil/spieler/135323",
    "Dean Henderson": "https://www.transfermarkt.com/dean-henderson/profil/spieler/403665",
    "Aaron Ramsdale": "https://www.transfermarkt.com/aaron-ramsdale/profil/spieler/506476",
    "Marc Guéhi": "https://www.transfermarkt.com/marc-guehi/profil/spieler/533966",
    "John Stones": "https://www.transfermarkt.com/john-stones/profil/spieler/189566",
    "Kyle Walker": "https://www.transfermarkt.com/kyle-walker/profil/spieler/95484",
    "Trent Alexander-Arnold": "https://www.transfermarkt.com/trent-alexander-arnold/profil/spieler/228702",
    "Levi Colwill": "https://www.transfermarkt.com/levi-colwill/profil/spieler/865438",
    "Ezri Konsa": "https://www.transfermarkt.com/ezri-konsa/profil/spieler/433177",
    "Declan Rice": "https://www.transfermarkt.com/declan-rice/profil/spieler/197228",
    "Bukayo Saka": "https://www.transfermarkt.com/bukayo-saka/profil/spieler/433177",
    "Phil Foden": "https://www.transfermarkt.com/phil-foden/profil/spieler/335759",
    "Cole Palmer": "https://www.transfermarkt.com/cole-palmer/profil/spieler/629589",
    "Jude Bellingham": "https://www.transfermarkt.com/jude-bellingham/profil/spieler/581678",
    "Harry Kane": "https://www.transfermarkt.com/harry-kane/profil/spieler/118098",
    "Ollie Watkins": "https://www.transfermarkt.com/ollie-watkins/profil/spieler/423569",

    # Portugal
    "Diogo Costa": "https://www.transfermarkt.com/diogo-costa/profil/spieler/617384",
    "José Sá": "https://www.transfermarkt.com/jose-sa/profil/spieler/207883",
    "Rui Silva": "https://www.transfermarkt.com/rui-silva/profil/spieler/128385",
    "Rúben Dias": "https://www.transfermarkt.com/ruben-dias/profil/spieler/388270",
    "Gonçalo Inácio": "https://www.transfermarkt.com/goncalo-inacio/profil/spieler/558889",
    "João Cancelo": "https://www.transfermarkt.com/joao-cancelo/profil/spieler/194980",
    "Diogo Dalot": "https://www.transfermarkt.com/diogo-dalot/profil/spieler/361339",
    "Nuno Mendes": "https://www.transfermarkt.com/nuno-mendes/profil/spieler/564954",
    "Nélson Semedo": "https://www.transfermarkt.com/nelson-semedo/profil/spieler/189651",
    "Renato Veiga": "https://www.transfermarkt.com/renato-veiga/profil/spieler/1003146",
    "Tomás Araújo": "https://www.transfermarkt.com/tomas-araujo/profil/spieler/1029044",
    "Bruno Fernandes": "https://www.transfermarkt.com/bruno-fernandes/profil/spieler/240671",
    "Bernardo Silva": "https://www.transfermarkt.com/bernardo-silva/profil/spieler/321233",
    "Rúben Neves": "https://www.transfermarkt.com/ruben-neves/profil/spieler/321234",
    "João Félix": "https://www.transfermarkt.com/joao-felix/profil/spieler/462737",
    "Vitinha": "https://www.transfermarkt.com/vitinha/profil/spieler/600118",
    "Diogo Jota": "https://www.transfermarkt.com/diogo-jota/profil/spieler/379782",
    "Rafael Leão": "https://www.transfermarkt.com/rafael-leao/profil/spieler/472046",

    # Croatia
    "Dominik Livaković": "https://www.transfermarkt.com/dominik-livakovic/profil/spieler/285808",
    "Nediljko Labrović": "https://www.transfermarkt.com/nediljko-labrovic/profil/spieler/821695",
    "Dominik Kovačević": "https://www.transfermarkt.com/dominik-kovacevic/profil/spieler/1230667",
    "Josip Šutalo": "https://www.transfermarkt.com/josip-sutalo/profil/spieler/624657",
    "Duje Ćaleta-Car": "https://www.transfermarkt.com/duje-caleta-car/profil/spieler/357696",
    "Borna Sosa": "https://www.transfermarkt.com/borna-sosa/profil/spieler/316935",
    "Joško Gvardiol": "https://www.transfermarkt.com/josko-gvardiol/profil/spieler/649675",
    "Josip Stanišić": "https://www.transfermarkt.com/josip-stanisic/profil/spieler/542596",
    "Luka Modrić": "https://www.transfermarkt.com/luka-modric/profil/spieler/27904",
    "Marcelo Brozović": "https://www.transfermarkt.com/marcelo-brozovic/profil/spieler/108037",
    "Mateo Kovačić": "https://www.transfermarkt.com/mateo-kovacic/profil/spieler/178296",
    "Luka Sučić": "https://www.transfermarkt.com/luka-sucic/profil/spieler/624661",
    "Mario Pašalić": "https://www.transfermarkt.com/mario-pasalic/profil/spieler/216900",
    "Ivan Perišić": "https://www.transfermarkt.com/ivan-perisic/profil/spieler/47816",
    "Andrej Kramarić": "https://www.transfermarkt.com/andrej-kramaric/profil/spieler/94271",
    "Lovro Majer": "https://www.transfermarkt.com/lovro-majer/profil/spieler/504466",
    "Ante Budimir": "https://www.transfermarkt.com/ante-budimir/profil/spieler/277900",

    # Bosnia
    "Ivo Grbić": "https://www.transfermarkt.com/ivo-grbic/profil/spieler/542595",
    "Elliot Colovic": "https://www.transfermarkt.com/elliot-colovic/profil/spieler/1070089",
    "Milan Bjegojević": "https://www.transfermarkt.com/milan-bjegojevic/profil/spieler/1171244",
    "Sanel Jatrić": "https://www.transfermarkt.com/sanel-jatric/profil/spieler/1224471",
    "Osman Hadžikić": "https://www.transfermarkt.com/osman-hadzikic/profil/spieler/1003489",
    "Sead Kolašinac": "https://www.transfermarkt.com/sead-kolasinac/profil/spieler/139522",
    "Amar Dedić": "https://www.transfermarkt.com/amar-dedic/profil/spieler/419359",
    "Nihad Mujkić": "https://www.transfermarkt.com/nihad-mujkic/profil/spieler/1006573",
    "Nikola Katić": "https://www.transfermarkt.com/nikola-katic/profil/spieler/277902",
    "Tarik Muharemović": "https://www.transfermarkt.com/tarik-muharemovic/profil/spieler/624636",
    "Stjepan Radeljić": "https://www.transfermarkt.com/stjepan-radeljic/profil/spieler/419378",
    "Dennis Hadžikadunić": "https://www.transfermarkt.com/dennis-hadzikadunic/profil/spieler/557548",
    "Nidal Čelik": "https://www.transfermarkt.com/nidal-celik/profil/spieler/1006571",
    "Amir Hadžiahmetović": "https://www.transfermarkt.com/amir-hadziahmetovic/profil/spieler/558890",
    "Ivan Šaranović": "https://www.transfermarkt.com/ivan-saranovic/profil/spieler/866999",
    "Ivan Barišić": "https://www.transfermarkt.com/ivan-barusic/profil/spieler/1006574",
    "Denis Burnić": "https://www.transfermarkt.com/denis-burnic/profil/spieler/419355",
    "Ermin Mahmić": "https://www.transfermarkt.com/ermin-mahmic/profil/spieler/600119",
    "Benjamin Tahirović": "https://www.transfermarkt.com/benjamin-tahirovic/profil/spieler/1006575",
    "Amar Memić": "https://www.transfermarkt.com/amar-memic/profil/spieler/419361",
    "Armin Gigović": "https://www.transfermarkt.com/armin-gigovic/profil/spieler/419354",
    "Kerim Alajbegović": "https://www.transfermarkt.com/kerim-alajbegovic/profil/spieler/1006572",
    "Esmir Bajraktarević": "https://www.transfermarkt.com/esmir-bajraktarevic/profil/spieler/1029168",
    "Ermedin Demirović": "https://www.transfermarkt.com/ermedin-demirovic/profil/spieler/419348",
    "Jovo Lukić": "https://www.transfermarkt.com/jovo-lukic/profil/spieler/1050438",
    "Samed Baždar": "https://www.transfermarkt.com/samed-bazdar/profil/spieler/1006638",
    "Haris Tabaković": "https://www.transfermarkt.com/haris-tabakovic/profil/spieler/419356",
    "Edin Džeko": "https://www.transfermarkt.com/edin-dzeko/profil/spieler/27819",
}

def main():
    with open(SQUAD_FILE, "r", encoding="utf-8") as f:
        squads = json.load(f)

    driver = init_driver()
    print(f"Driver initialized. {len(PLAYER_URLS)} player URLs available")

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

            name_clean = name_en.encode('ascii', 'replace').decode('ascii')
            print(f"  {name_clean} ({position})", end="", flush=True)

            player_data = {
                "name_en": name_en,
                "name_cn": name_cn if name_cn else "",
                "position": position,
                "club": club if club else "",
                "age": player.get("age"),
                "club_country": player.get("club_country", ""),
            }

            # Check for known URL
            if name_en in PLAYER_URLS:
                url = PLAYER_URLS[name_en]
                player_data["transfermarkt_url"] = url

                # Scrape data
                stats_data = extract_stats(driver, url + "/statistik")
                player_data.update(stats_data)

                mv = stats_data.get('market_value', 'N/A')
                apps = stats_data.get('current_season', {}).get('appearances', 'N/A')
                goals = stats_data.get('current_season', {}).get('goals', 'N/A')
                print(f" -> MV:{mv} Apps:{apps} Goals:{goals}")
            else:
                print(" -> No URL known")
                player_data["transfermarkt_url"] = None

            team_result["players"].append(player_data)

        all_results.append(team_result)

        # Save team file
        team_file = os.path.join(OUTPUT_DIR, f"{team['fifa_code']}_players.json")
        with open(team_file, "w", encoding="utf-8") as f:
            json.dump(team_result, f, ensure_ascii=False, indent=2)

        print(f"Saved to {team_file}")

        # Rate limit
        time.sleep(1.5)

    # Save combined file
    combined_file = os.path.join(OUTPUT_DIR, "all_players.json")
    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    driver.quit()

    print(f"\n{'='*60}")
    print(f"Complete! Data saved to {OUTPUT_DIR}")

    # Summary
    total = 0
    with_url = 0
    with_stats = 0
    for t in all_results:
        for p in t['players']:
            total += 1
            if p.get('transfermarkt_url'):
                with_url += 1
            if p.get('current_season', {}):
                with_stats += 1

    print(f"Total: {total} players, {with_url} with URL, {with_stats} with stats")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()