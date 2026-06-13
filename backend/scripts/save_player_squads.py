"""
Save player squad data to team directories.
Squads are from provisional/final announcements as of mid-May 2026.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "teams"

# Argentina full provisional squad (55-man, released May 11)
ARGENTINA_SQUAD = {
    "announced": "2026-05-11",
    "type": "provisional_55",
    "coach": "Lionel Scaloni",
    "goalkeepers": [
        {"name": "Emiliano Martínez", "club": "Aston Villa", "caps": 45},
        {"name": "Gerónimo Rulli", "club": "Marseille", "caps": 6},
        {"name": "Juan Musso", "club": "Atlético Madrid", "caps": 2},
        {"name": "Walter Benítez", "club": "Crystal Palace", "caps": 0},
    ],
    "defenders": [
        {"name": "Cristian Romero", "club": "Tottenham", "caps": 38},
        {"name": "Lisandro Martínez", "club": "Manchester United", "caps": 24},
        {"name": "Nicolás Otamendi", "club": "Benfica", "caps": 115},
        {"name": "Nahuel Molina", "club": "Atlético Madrid", "caps": 40},
        {"name": "Gonzalo Montiel", "club": "River Plate", "caps": 28},
        {"name": "Nicolás Tagliafico", "club": "Lyon", "caps": 55},
        {"name": "Marcos Acuña", "club": "River Plate", "caps": 55},
    ],
    "midfielders": [
        {"name": "Enzo Fernández", "club": "Chelsea", "caps": 28},
        {"name": "Alexis Mac Allister", "club": "Liverpool", "caps": 30},
        {"name": "Rodrigo De Paul", "club": "Inter Miami", "caps": 65},
        {"name": "Exequiel Palacios", "club": "Bayer Leverkusen", "caps": 28},
        {"name": "Leandro Paredes", "club": "Boca Juniors", "caps": 60},
        {"name": "Giovani Lo Celso", "club": "Real Betis", "caps": 52},
    ],
    "forwards": [
        {"name": "Lionel Messi", "club": "Inter Miami", "caps": 180},
        {"name": "Lautaro Martínez", "club": "Inter Milan", "caps": 58},
        {"name": "Julián Álvarez", "club": "Atlético Madrid", "caps": 35},
        {"name": "Alejandro Garnacho", "club": "Chelsea", "caps": 12},
        {"name": "Nicolás González", "club": "Atlético Madrid", "caps": 38},
        {"name": "Thiago Almada", "club": "Atlético Madrid", "caps": 8},
        {"name": "Nico Paz", "club": "Como", "caps": 2},
        {"name": "Claudio Echeverri", "club": "Girona", "caps": 0},
    ],
    "notable_omissions": ["Paulo Dybala"],
}

# Brazil provisional squad
BRAZIL_SQUAD = {
    "announced": "2026-05-11",
    "type": "provisional_55",
    "coach": "Carlo Ancelotti",
    "goalkeepers": [
        {"name": "Alisson", "club": "Liverpool", "caps": 65},
        {"name": "Bento", "club": "Al Nassr", "caps": 12},
        {"name": "Ederson", "club": "Fenerbahçe", "caps": 25},
    ],
    "defenders": [
        {"name": "Marquinhos", "club": "PSG", "caps": 87},
        {"name": "Gabriel Magalhães", "club": "Arsenal", "caps": 20},
        {"name": "Bremer", "club": "Juventus", "caps": 15},
        {"name": "Thiago Silva", "club": "Porto", "caps": 113},
    ],
    "midfielders": [
        {"name": "Bruno Guimarães", "club": "Newcastle", "caps": 30},
        {"name": "Casemiro", "club": "Manchester United", "caps": 75},
        {"name": "Andrey Santos", "club": "Chelsea", "caps": 5},
        {"name": "João Gomes", "club": "Wolves", "caps": 12},
        {"name": "Lucas Paquetá", "club": "Flamengo", "caps": 48},
    ],
    "forwards": [
        {"name": "Vinicius Jr", "club": "Real Madrid", "caps": 30},
        {"name": "Raphinha", "club": "Barcelona", "caps": 28},
        {"name": "Neymar", "club": "Santos", "caps": 124},
        {"name": "Gabriel Martinelli", "club": "Arsenal", "caps": 15},
        {"name": "Endrick", "club": "Lyon", "caps": 8},
        {"name": "Matheus Cunha", "club": "Manchester United", "caps": 20},
    ],
    "notable_omissions": ["Rodrygo (injured)", "Éder Militão (injured)"],
}

# France final squad (leaked, officially announced May 14)
FRANCE_SQUAD = {
    "announced": "2026-05-14",
    "type": "final_26",
    "coach": "Didier Deschamps",
    "goalkeepers": [
        {"name": "Mike Maignan", "club": "AC Milan", "caps": 28},
        {"name": "Brice Samba", "club": "Rennes", "caps": 5},
        {"name": "Robin Risser", "club": "Lens", "caps": 0},
    ],
    "defenders": [
        {"name": "Jules Koundé", "club": "Barcelona", "caps": 35},
        {"name": "Malo Gusto", "club": "Chelsea", "caps": 8},
        {"name": "Dayot Upamecano", "club": "Bayern Munich", "caps": 25},
        {"name": "William Saliba", "club": "Arsenal", "caps": 22},
        {"name": "Ibrahima Konaté", "club": "Liverpool", "caps": 18},
        {"name": "Lucas Hernandez", "club": "PSG", "caps": 40},
        {"name": "Theo Hernandez", "club": "Al-Hilal", "caps": 30},
        {"name": "Lucas Digne", "club": "Aston Villa", "caps": 48},
    ],
    "midfielders": [
        {"name": "Aurélien Tchouaméni", "club": "Real Madrid", "caps": 35},
        {"name": "Eduardo Camavinga", "club": "Real Madrid", "caps": 22},
        {"name": "N'Golo Kanté", "club": "Al-Ittihad", "caps": 55},
        {"name": "Adrien Rabiot", "club": "AC Milan", "caps": 48},
        {"name": "Manu Koné", "club": "Roma", "caps": 8},
        {"name": "Warren Zaïre-Emery", "club": "PSG", "caps": 5},
    ],
    "forwards": [
        {"name": "Kylian Mbappé", "club": "Real Madrid", "caps": 80},
        {"name": "Ousmane Dembélé", "club": "PSG", "caps": 50},
        {"name": "Michael Olise", "club": "Bayern Munich", "caps": 12},
        {"name": "Marcus Thuram", "club": "Inter Milan", "caps": 25},
        {"name": "Bradley Barcola", "club": "PSG", "caps": 15},
        {"name": "Désiré Doué", "club": "PSG", "caps": 5},
        {"name": "Rayan Cherki", "club": "Manchester City", "caps": 8},
        {"name": "Maghnes Akliouche", "club": "Monaco", "caps": 3},
        {"name": "Randal Kolo Muani", "club": "Tottenham", "caps": 30},
    ],
    "notable_omissions": ["Lucas Chevalier", "Benjamin Pavard", "Hugo Ekitike (injured)"],
}

# Spain preliminary squad (partial, leaked)
SPAIN_SQUAD = {
    "announced": "2026-05-11",
    "type": "preliminary_55",
    "coach": "Luis de la Fuente",
    "goalkeepers": [
        {"name": "Unai Simón", "club": "Athletic Bilbao", "caps": 40},
        {"name": "David Raya", "club": "Arsenal", "caps": 12},
        {"name": "Joan García", "club": "Espanyol", "caps": 0},
    ],
    "defenders": [
        {"name": "Pedro Porro", "club": "Tottenham", "caps": 8},
        {"name": "Marc Cucurella", "club": "Chelsea", "caps": 10},
        {"name": "Alejandro Grimaldo", "club": "Bayer Leverkusen", "caps": 15},
        {"name": "Pau Cubarsí", "club": "Barcelona", "caps": 5},
        {"name": "Aymeric Laporte", "club": "Al Nassr", "caps": 40},
        {"name": "Dean Huijsen", "club": "Real Madrid", "caps": 2},
        {"name": "Pau Torres", "club": "Aston Villa", "caps": 28},
        {"name": "Robin Le Normand", "club": "Atlético Madrid", "caps": 18},
    ],
    "midfielders": [
        {"name": "Rodri", "club": "Manchester City", "caps": 55},
        {"name": "Pedri", "club": "Barcelona", "caps": 25},
        {"name": "Gavi", "club": "Barcelona", "caps": 22},
        {"name": "Dani Olmo", "club": "Barcelona", "caps": 35},
        {"name": "Fabián Ruiz", "club": "PSG", "caps": 30},
        {"name": "Martín Zubimendi", "club": "Real Sociedad", "caps": 12},
        {"name": "Mikel Merino", "club": "Arsenal", "caps": 28},
    ],
    "forwards": [
        {"name": "Lamine Yamal", "club": "Barcelona", "caps": 15},
        {"name": "Nico Williams", "club": "Athletic Bilbao", "caps": 22},
        {"name": "Ferran Torres", "club": "Barcelona", "caps": 45},
        {"name": "Mikel Oyarzabal", "club": "Real Sociedad", "caps": 35},
        {"name": "Álex Baena", "club": "Villarreal", "caps": 8},
        {"name": "Yeremy Pino", "club": "Villarreal", "caps": 12},
    ],
    "notable_omissions": ["Dani Carvajal", "Álvaro Morata", "Alejandro Balde"],
}

# England provisional squad (confidential, media reports)
ENGLAND_SQUAD = {
    "announced": "2026-05-11",
    "type": "provisional_55",
    "coach": "Thomas Tuchel",
    "goalkeepers": [
        {"name": "Jordan Pickford", "club": "Everton", "caps": 68},
    ],
    "defenders": [
        {"name": "John Stones", "club": "Manchester City", "caps": 72},
        {"name": "Marc Guéhi", "club": "Crystal Palace", "caps": 20},
        {"name": "Reece James", "club": "Chelsea", "caps": 18},
        {"name": "Ben White", "club": "Arsenal", "caps": 12},
        {"name": "Myles Lewis-Skelly", "club": "Arsenal", "caps": 2},
        {"name": "Trent Alexander-Arnold", "club": "Real Madrid", "caps": 30},
        {"name": "Luke Shaw", "club": "Manchester United", "caps": 32},
        {"name": "Jarrad Branthwaite", "club": "Everton", "caps": 2},
    ],
    "midfielders": [
        {"name": "Jude Bellingham", "club": "Real Madrid", "caps": 40},
        {"name": "Declan Rice", "club": "Arsenal", "caps": 58},
        {"name": "Phil Foden", "club": "Manchester City", "caps": 38},
        {"name": "Cole Palmer", "club": "Chelsea", "caps": 12},
        {"name": "Kobbie Mainoo", "club": "Manchester United", "caps": 10},
        {"name": "Conor Gallagher", "club": "Atlético Madrid", "caps": 20},
        {"name": "Morgan Rogers", "club": "Aston Villa", "caps": 5},
        {"name": "Eberechi Eze", "club": "Arsenal", "caps": 12},
    ],
    "forwards": [
        {"name": "Harry Kane", "club": "Bayern Munich", "caps": 98},
        {"name": "Bukayo Saka", "club": "Arsenal", "caps": 42},
        {"name": "Marcus Rashford", "club": "Barcelona", "caps": 60},
        {"name": "Anthony Gordon", "club": "Newcastle", "caps": 8},
        {"name": "Ollie Watkins", "club": "Aston Villa", "caps": 15},
        {"name": "Danny Welbeck", "club": "Brighton", "caps": 42},
        {"name": "Alex Scott", "club": "Bournemouth", "caps": 2},
    ],
    "notable_omissions": ["Dominic Solanke (injured)"],
}

# Germany provisional (confidential, media reports)
GERMANY_SQUAD = {
    "announced": "2026-05-11",
    "type": "provisional_55",
    "coach": "Julian Nagelsmann",
    "goalkeepers": [
        {"name": "Oliver Baumann", "club": "Hoffenheim", "caps": 10},
        {"name": "Alexander Nübel", "club": "Stuttgart", "caps": 5},
        {"name": "Manuel Neuer", "club": "Bayern Munich", "caps": 124},
    ],
    "defenders": [
        {"name": "Nico Schlotterbeck", "club": "Borussia Dortmund", "caps": 18},
        {"name": "Waldemar Anton", "club": "Borussia Dortmund", "caps": 8},
    ],
    "midfielders": [
        {"name": "Jamal Musiala", "club": "Bayern Munich", "caps": 30},
        {"name": "Florian Wirtz", "club": "Bayer Leverkusen", "caps": 25},
        {"name": "Felix Nmecha", "club": "Borussia Dortmund", "caps": 5},
        {"name": "Leroy Sané", "club": "Galatasaray", "caps": 65},
    ],
    "forwards": [
        {"name": "Maximilian Beier", "club": "Borussia Dortmund", "caps": 5},
        {"name": "Karim Adeyemi", "club": "Borussia Dortmund", "caps": 8},
    ],
    "notable_omissions": ["Serge Gnabry (injured)"],
}

# Map of available squads
SQUAD_DATA = {
    "Argentina": ARGENTINA_SQUAD,
    "Brazil": BRAZIL_SQUAD,
    "France": FRANCE_SQUAD,
    "Spain": SPAIN_SQUAD,
    "England": ENGLAND_SQUAD,
    "Germany": GERMANY_SQUAD,
}


def main():
    for team_name, squad in SQUAD_DATA.items():
        team_dir = DATA_DIR / team_name
        team_dir.mkdir(parents=True, exist_ok=True)

        squad_path = team_dir / "player_squad.json"
        with open(squad_path, "w", encoding="utf-8") as f:
            json.dump(squad, f, ensure_ascii=False, indent=2)

        total_players = (
            len(squad.get("goalkeepers", []))
            + len(squad.get("defenders", []))
            + len(squad.get("midfielders", []))
            + len(squad.get("forwards", []))
        )
        print(f"  {team_name}: {total_players} players saved ({squad['type']})")

    # Create placeholder for teams we don't have squad data yet
    all_teams_path = DATA_DIR / "all_teams.json"
    if all_teams_path.exists():
        with open(all_teams_path, "r", encoding="utf-8") as f:
            all_teams = json.load(f)

        for team in all_teams:
            if team["team_en"] not in SQUAD_DATA:
                team_dir = DATA_DIR / team["team_en"]
                placeholder_path = team_dir / "player_squad.json"
                if not placeholder_path.exists():
                    placeholder = {
                        "announced": None,
                        "type": "pending",
                        "coach": None,
                        "goalkeepers": [],
                        "defenders": [],
                        "midfielders": [],
                        "forwards": [],
                        "note": "球员名单待官方公布后更新 (2026年6月1日前)",
                    }
                    with open(placeholder_path, "w", encoding="utf-8") as f:
                        json.dump(placeholder, f, ensure_ascii=False, indent=2)
                    print(f"  {team['team_en']}: placeholder created")

    print("\nDone! Squad data saved.")


if __name__ == "__main__":
    main()
