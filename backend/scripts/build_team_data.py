"""
Build team data: 48 teams info + extract recent 20yr matches from results.csv
"""
import json
import os
import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "teams"
ARCHIVE_DIR = Path(__file__).parent.parent.parent / "archive"

# 48 teams of 2026 World Cup with confederation, group, FIFA ranking (approximate)
TEAMS_2026 = [
    # UEFA (16)
    {"team_en": "England", "team_cn": "英格兰", "confederation": "UEFA", "group": "L"},
    {"team_en": "France", "team_cn": "法国", "confederation": "UEFA", "group": "I"},
    {"team_en": "Croatia", "team_cn": "克罗地亚", "confederation": "UEFA", "group": "L"},
    {"team_en": "Norway", "team_cn": "挪威", "confederation": "UEFA", "group": "I"},
    {"team_en": "Portugal", "team_cn": "葡萄牙", "confederation": "UEFA", "group": "K"},
    {"team_en": "Germany", "team_cn": "德国", "confederation": "UEFA", "group": "E"},
    {"team_en": "Netherlands", "team_cn": "荷兰", "confederation": "UEFA", "group": "F"},
    {"team_en": "Switzerland", "team_cn": "瑞士", "confederation": "UEFA", "group": "B"},
    {"team_en": "Scotland", "team_cn": "苏格兰", "confederation": "UEFA", "group": "C"},
    {"team_en": "Spain", "team_cn": "西班牙", "confederation": "UEFA", "group": "H"},
    {"team_en": "Austria", "team_cn": "奥地利", "confederation": "UEFA", "group": "J"},
    {"team_en": "Belgium", "team_cn": "比利时", "confederation": "UEFA", "group": "G"},
    {"team_en": "Bosnia and Herzegovina", "team_cn": "波黑", "confederation": "UEFA", "group": "B"},
    {"team_en": "Sweden", "team_cn": "瑞典", "confederation": "UEFA", "group": "F"},
    {"team_en": "Turkey", "team_cn": "土耳其", "confederation": "UEFA", "group": "D"},
    {"team_en": "Czechia", "team_cn": "捷克", "confederation": "UEFA", "group": "A"},

    # CONMEBOL (6)
    {"team_en": "Argentina", "team_cn": "阿根廷", "confederation": "CONMEBOL", "group": "J"},
    {"team_en": "Brazil", "team_cn": "巴西", "confederation": "CONMEBOL", "group": "C"},
    {"team_en": "Colombia", "team_cn": "哥伦比亚", "confederation": "CONMEBOL", "group": "K"},
    {"team_en": "Ecuador", "team_cn": "厄瓜多尔", "confederation": "CONMEBOL", "group": "E"},
    {"team_en": "Paraguay", "team_cn": "巴拉圭", "confederation": "CONMEBOL", "group": "D"},
    {"team_en": "Uruguay", "team_cn": "乌拉圭", "confederation": "CONMEBOL", "group": "H"},

    # AFC (9)
    {"team_en": "Australia", "team_cn": "澳大利亚", "confederation": "AFC", "group": "D"},
    {"team_en": "Iran", "team_cn": "伊朗", "confederation": "AFC", "group": "G"},
    {"team_en": "Japan", "team_cn": "日本", "confederation": "AFC", "group": "F"},
    {"team_en": "Jordan", "team_cn": "约旦", "confederation": "AFC", "group": "J"},
    {"team_en": "Uzbekistan", "team_cn": "乌兹别克斯坦", "confederation": "AFC", "group": "K"},
    {"team_en": "Qatar", "team_cn": "卡塔尔", "confederation": "AFC", "group": "B"},
    {"team_en": "Saudi Arabia", "team_cn": "沙特阿拉伯", "confederation": "AFC", "group": "H"},
    {"team_en": "South Korea", "team_cn": "韩国", "confederation": "AFC", "group": "A"},
    {"team_en": "Iraq", "team_cn": "伊拉克", "confederation": "AFC", "group": "I"},

    # CAF (10)
    {"team_en": "Algeria", "team_cn": "阿尔及利亚", "confederation": "CAF", "group": "J"},
    {"team_en": "Cape Verde", "team_cn": "佛得角", "confederation": "CAF", "group": "H"},
    {"team_en": "DR Congo", "team_cn": "刚果民主共和国", "confederation": "CAF", "group": "K"},
    {"team_en": "Egypt", "team_cn": "埃及", "confederation": "CAF", "group": "G"},
    {"team_en": "Ghana", "team_cn": "加纳", "confederation": "CAF", "group": "L"},
    {"team_en": "Ivory Coast", "team_cn": "科特迪瓦", "confederation": "CAF", "group": "E"},
    {"team_en": "Morocco", "team_cn": "摩洛哥", "confederation": "CAF", "group": "C"},
    {"team_en": "Senegal", "team_cn": "塞内加尔", "confederation": "CAF", "group": "I"},
    {"team_en": "South Africa", "team_cn": "南非", "confederation": "CAF", "group": "A"},
    {"team_en": "Tunisia", "team_cn": "突尼斯", "confederation": "CAF", "group": "F"},

    # CONCACAF (6)
    {"team_en": "United States", "team_cn": "美国", "confederation": "CONCACAF", "group": "D"},
    {"team_en": "Mexico", "team_cn": "墨西哥", "confederation": "CONCACAF", "group": "A"},
    {"team_en": "Canada", "team_cn": "加拿大", "confederation": "CONCACAF", "group": "B"},
    {"team_en": "Panama", "team_cn": "巴拿马", "confederation": "CONCACAF", "group": "L"},
    {"team_en": "Haiti", "team_cn": "海地", "confederation": "CONCACAF", "group": "C"},
    {"team_en": "Curaçao", "team_cn": "库拉索", "confederation": "CONCACAF", "group": "E"},

    # OFC (1)
    {"team_en": "New Zealand", "team_cn": "新西兰", "confederation": "OFC", "group": "G"},
]

# Team name mapping for results.csv (historical names)
NAME_ALIASES = {
    "United States": ["USA", "United States"],
    "South Korea": ["Korea Republic", "South Korea"],
    "Czechia": ["Czech Republic", "Czechia"],
    "Bosnia and Herzegovina": ["Bosnia", "Bosnia and Herzegovina"],
    "Curaçao": ["Curaçao"],
    "Cape Verde": ["Cape Verde"],
    "DR Congo": ["DR Congo", "Congo DR", "Zaire"],
    "Ivory Coast": ["Ivory Coast", "Côte d'Ivoire"],
    "Turkey": ["Turkey", "Türkiye"],
    "Iran": ["Iran"],
    "Iraq": ["Iraq"],
    "Netherlands": ["Netherlands"],
}

KNOWN_NAMES = set()
for t in TEAMS_2026:
    KNOWN_NAMES.add(t["team_en"])
    if t["team_en"] in NAME_ALIASES:
        for alias in NAME_ALIASES[t["team_en"]]:
            KNOWN_NAMES.add(alias)


def extract_recent_matches():
    """Extract last 20 years of matches from results.csv for each team."""
    results_path = ARCHIVE_DIR / "results.csv"
    cutoff_year = 2006  # Last 20 years from 2026

    team_matches = defaultdict(list)
    all_matches_count = 0

    with open(results_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row.get("date", "")
            if not date_str:
                continue
            try:
                year = int(date_str[:4])
            except ValueError:
                continue

            if year < cutoff_year:
                continue

            home = row["home_team"].strip()
            away = row["away_team"].strip()
            tournament = row.get("tournament", "").strip()

            match = {
                "date": date_str,
                "home_team": home,
                "away_team": away,
                "home_score": row["home_score"],
                "away_score": row["away_score"],
                "tournament": tournament,
                "city": row.get("city", ""),
                "country": row.get("country", ""),
                "neutral": row.get("neutral", "FALSE"),
            }

            added_home = False
            added_away = False
            for team_name in KNOWN_NAMES:
                if home == team_name or home in NAME_ALIASES.get(team_name, []):
                    if not added_home:
                        team_matches[team_name].append(match)
                        added_home = True
                if away == team_name or away in NAME_ALIASES.get(team_name, []):
                    if not added_away:
                        team_matches[team_name].append(match)
                        added_away = True

            all_matches_count += 1

    print(f"Total matches (2006-2026): {all_matches_count}")
    print(f"Teams with match data: {len(team_matches)}")

    for team_name, matches in sorted(team_matches.items(), key=lambda x: -len(x[1])):
        print(f"  {team_name}: {len(matches)} matches")

    return team_matches


def build_team_stats(team_info, matches):
    """Build stats from match history."""
    if not matches:
        return {"total_matches": 0, "wins": 0, "draws": 0, "losses": 0,
                "goals_for": 0, "goals_against": 0}

    stats = {"total_matches": 0, "wins": 0, "draws": 0, "losses": 0,
             "goals_for": 0, "goals_against": 0}

    for m in matches:
        home = m["home_team"]
        away = m["away_team"]
        is_home = home == team_info["team_en"] or home in NAME_ALIASES.get(team_info["team_en"], [])

        try:
            hs = int(m["home_score"])
            as_ = int(m["away_score"])
        except (ValueError, TypeError):
            continue

        stats["total_matches"] += 1

        if is_home:
            stats["goals_for"] += hs
            stats["goals_against"] += as_
            if hs > as_:
                stats["wins"] += 1
            elif hs == as_:
                stats["draws"] += 1
            else:
                stats["losses"] += 1
        else:
            stats["goals_for"] += as_
            stats["goals_against"] += hs
            if as_ > hs:
                stats["wins"] += 1
            elif as_ == hs:
                stats["draws"] += 1
            else:
                stats["losses"] += 1

    return stats


def main():
    print("Extracting recent 20-year matches from results.csv...")
    team_matches = extract_recent_matches()

    # Map matches back to our team keys
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for team in TEAMS_2026:
        team_name = team["team_en"]
        team_dir = DATA_DIR / team_name
        team_dir.mkdir(parents=True, exist_ok=True)

        # Find matches for this team
        matches = team_matches.get(team_name, [])
        # Also check aliases
        if not matches and team_name in NAME_ALIASES:
            for alias in NAME_ALIASES[team_name]:
                matches.extend(team_matches.get(alias, []))

        stats = build_team_stats(team, matches)

        # Sort matches by date (newest first)
        matches_sorted = sorted(matches, key=lambda m: m["date"], reverse=True)

        # Recent 10 matches
        recent_10 = matches_sorted[:10]

        # Recent matches by year
        matches_by_year = defaultdict(list)
        for m in matches_sorted:
            matches_by_year[m["date"][:4]].append(m)

        # Tournament breakdown
        tournament_counts = defaultdict(int)
        for m in matches_sorted:
            tournament_counts[m["tournament"]] += 1

        team_data = {
            **team,
            "stats": stats,
            "recent_matches": recent_10,
            "matches_by_year": {y: len(ms) for y, ms in sorted(matches_by_year.items(), reverse=True)},
            "tournament_breakdown": dict(sorted(tournament_counts.items(), key=lambda x: -x[1])),
            "total_matches_20y": len(matches_sorted),
            # Full match history saved separately
        }

        # Save team data
        team_json_path = team_dir / "team_info.json"
        with open(team_json_path, "w", encoding="utf-8") as f:
            json.dump(team_data, f, ensure_ascii=False, indent=2)

        # Save full match history separately
        matches_json_path = team_dir / "match_history.json"
        with open(matches_json_path, "w", encoding="utf-8") as f:
            json.dump(matches_sorted, f, ensure_ascii=False, indent=2)

        print(f"Saved {team_name}: {stats['total_matches']} matches analyzed, "
              f"W{stats['wins']}-D{stats['draws']}-L{stats['losses']}")

    # Save all teams index
    all_teams = []
    for team in TEAMS_2026:
        team_dir = DATA_DIR / team["team_en"]
        info_path = team_dir / "team_info.json"
        if info_path.exists():
            with open(info_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            all_teams.append({
                "team_en": data["team_en"],
                "team_cn": data["team_cn"],
                "confederation": data["confederation"],
                "group": data["group"],
                "stats": data.get("stats", {}),
                "total_matches_20y": data.get("total_matches_20y", 0),
            })

    with open(DATA_DIR / "all_teams.json", "w", encoding="utf-8") as f:
        json.dump(all_teams, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(all_teams)} teams saved to {DATA_DIR}")


if __name__ == "__main__":
    main()
