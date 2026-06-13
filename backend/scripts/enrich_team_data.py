"""
Enrich team data with ELO ratings (estimated from match history) and betting odds.
"""
import json
from pathlib import Path
import math

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "teams"

# Betting odds from major platforms (aggregated data as of April 2026)
# Format: team_name -> {decimal_odds, implied_probability_percent, rank}
ODDS_DATA = {
    "Spain": {"decimal_odds": 5.50, "implied_probability": 18.0, "rank": 1, "platforms": {"Bet365": 5.50, "William Hill": 5.50, "DraftKings": 6.00}},
    "England": {"decimal_odds": 6.50, "implied_probability": 14.0, "rank": 2, "platforms": {"Bet365": 6.50, "William Hill": 6.00, "DraftKings": 7.00}},
    "France": {"decimal_odds": 7.00, "implied_probability": 14.0, "rank": 3, "platforms": {"Bet365": 7.00, "William Hill": 7.50, "DraftKings": 6.50}},
    "Brazil": {"decimal_odds": 9.00, "implied_probability": 10.5, "rank": 4, "platforms": {"Bet365": 9.00, "William Hill": 8.50, "DraftKings": 9.50}},
    "Argentina": {"decimal_odds": 9.00, "implied_probability": 10.5, "rank": 5, "platforms": {"Bet365": 9.00, "William Hill": 9.00, "DraftKings": 8.50}},
    "Portugal": {"decimal_odds": 13.00, "implied_probability": 7.7, "rank": 6, "platforms": {"Bet365": 13.00, "William Hill": 12.00, "DraftKings": 13.00}},
    "Germany": {"decimal_odds": 13.00, "implied_probability": 6.7, "rank": 7, "platforms": {"Bet365": 13.00, "William Hill": 15.00, "DraftKings": 13.00}},
    "Netherlands": {"decimal_odds": 21.00, "implied_probability": 4.5, "rank": 8, "platforms": {"Bet365": 21.00, "William Hill": 21.00, "DraftKings": 22.00}},
    "Norway": {"decimal_odds": 26.00, "implied_probability": 3.3, "rank": 9, "platforms": {"Bet365": 26.00, "William Hill": 29.00, "DraftKings": 30.00}},
    "Belgium": {"decimal_odds": 34.00, "implied_probability": 2.8, "rank": 10, "platforms": {"Bet365": 34.00, "William Hill": 34.00, "DraftKings": 35.00}},
    "United States": {"decimal_odds": 41.00, "implied_probability": 2.3, "rank": 11, "platforms": {"Bet365": 41.00, "William Hill": 41.00, "DraftKings": 65.00}},
    "Switzerland": {"decimal_odds": 41.00, "implied_probability": 2.3, "rank": 11, "platforms": {"Bet365": 81.00, "William Hill": 101.00, "DraftKings": 41.00}},
    "Colombia": {"decimal_odds": 51.00, "implied_probability": 1.9, "rank": 13, "platforms": {"Bet365": 51.00, "William Hill": 51.00, "DraftKings": 50.00}},
    "Morocco": {"decimal_odds": 51.00, "implied_probability": 1.9, "rank": 13, "platforms": {"Bet365": 51.00, "William Hill": 67.00, "DraftKings": 51.00}},
    "Japan": {"decimal_odds": 67.00, "implied_probability": 1.4, "rank": 15, "platforms": {"Bet365": 67.00, "William Hill": 67.00, "DraftKings": 75.00}},
    "Mexico": {"decimal_odds": 81.00, "implied_probability": 1.2, "rank": 16, "platforms": {"Bet365": 81.00, "William Hill": 81.00, "DraftKings": 80.00}},
    "Uruguay": {"decimal_odds": 81.00, "implied_probability": 1.2, "rank": 16, "platforms": {"Bet365": 81.00, "William Hill": 67.00, "DraftKings": 80.00}},
    "Canada": {"decimal_odds": 81.00, "implied_probability": 1.2, "rank": 18, "platforms": {"Bet365": 81.00, "William Hill": 201.00, "DraftKings": 200.00}},
    "Ecuador": {"decimal_odds": 101.00, "implied_probability": 1.0, "rank": 19, "platforms": {"Bet365": 101.00, "William Hill": 101.00, "DraftKings": 100.00}},
    "Croatia": {"decimal_odds": 101.00, "implied_probability": 1.0, "rank": 19, "platforms": {"Bet365": 101.00, "William Hill": 101.00, "DraftKings": 100.00}},
    "Senegal": {"decimal_odds": 101.00, "implied_probability": 1.0, "rank": 19, "platforms": {"Bet365": 101.00, "William Hill": 126.00, "DraftKings": 100.00}},
    "Turkey": {"decimal_odds": 101.00, "implied_probability": 1.0, "rank": 19, "platforms": {"Bet365": 101.00, "William Hill": 101.00, "DraftKings": 100.00}},
    "Austria": {"decimal_odds": 151.00, "implied_probability": 0.7, "rank": 23, "platforms": {"Bet365": 151.00, "William Hill": 101.00, "DraftKings": 150.00}},
    "Paraguay": {"decimal_odds": 151.00, "implied_probability": 0.7, "rank": 23, "platforms": {"Bet365": 201.00, "William Hill": 201.00, "DraftKings": 151.00}},
    "Sweden": {"decimal_odds": 151.00, "implied_probability": 0.7, "rank": 23, "platforms": {"Bet365": 151.00, "William Hill": 151.00, "DraftKings": 150.00}},
    "Scotland": {"decimal_odds": 251.00, "implied_probability": 0.4, "rank": 26, "platforms": {"Bet365": 251.00, "William Hill": 251.00, "DraftKings": 200.00}},
    "Bosnia and Herzegovina": {"decimal_odds": 251.00, "implied_probability": 0.4, "rank": 26, "platforms": {"Bet365": 251.00, "William Hill": 251.00, "DraftKings": 250.00}},
    "Ivory Coast": {"decimal_odds": 301.00, "implied_probability": 0.3, "rank": 28, "platforms": {"Bet365": 251.00, "William Hill": 251.00, "DraftKings": 301.00}},
    "Egypt": {"decimal_odds": 301.00, "implied_probability": 0.3, "rank": 28, "platforms": {"Bet365": 301.00, "William Hill": 301.00, "DraftKings": 251.00}},
    "Czechia": {"decimal_odds": 301.00, "implied_probability": 0.3, "rank": 28, "platforms": {"Bet365": 251.00, "William Hill": 151.00, "DraftKings": 301.00}},
    "Ghana": {"decimal_odds": 401.00, "implied_probability": 0.2, "rank": 31, "platforms": {"Bet365": 401.00, "William Hill": 401.00, "DraftKings": 350.00}},
    "Algeria": {"decimal_odds": 401.00, "implied_probability": 0.2, "rank": 31, "platforms": {"Bet365": 401.00, "William Hill": 351.00, "DraftKings": 401.00}},
    "South Korea": {"decimal_odds": 501.00, "implied_probability": 0.2, "rank": 33, "platforms": {"Bet365": 501.00, "William Hill": 501.00, "DraftKings": 350.00}},
    "Tunisia": {"decimal_odds": 501.00, "implied_probability": 0.2, "rank": 33, "platforms": {"Bet365": 501.00, "William Hill": 501.00, "DraftKings": 500.00}},
    "Australia": {"decimal_odds": 501.00, "implied_probability": 0.2, "rank": 33, "platforms": {"Bet365": 501.00, "William Hill": 501.00, "DraftKings": 450.00}},
    "Iran": {"decimal_odds": 501.00, "implied_probability": 0.2, "rank": 33, "platforms": {"Bet365": 501.00, "William Hill": 301.00, "DraftKings": 501.00}},
    "DR Congo": {"decimal_odds": 751.00, "implied_probability": 0.1, "rank": 37, "platforms": {"Bet365": 751.00, "William Hill": 751.00, "DraftKings": 701.00}},
    "South Africa": {"decimal_odds": 1001.00, "implied_probability": 0.1, "rank": 38, "platforms": {"Bet365": 1001.00, "William Hill": 1001.00, "DraftKings": 800.00}},
    "Qatar": {"decimal_odds": 1001.00, "implied_probability": 0.1, "rank": 38, "platforms": {"Bet365": 1001.00, "William Hill": 1001.00, "DraftKings": 1000.00}},
    "Saudi Arabia": {"decimal_odds": 1001.00, "implied_probability": 0.1, "rank": 38, "platforms": {"Bet365": 1001.00, "William Hill": 1001.00, "DraftKings": 1000.00}},
    "Panama": {"decimal_odds": 1501.00, "implied_probability": 0.07, "rank": 41, "platforms": {"Bet365": 1501.00, "William Hill": 1501.00, "DraftKings": 1000.00}},
    "New Zealand": {"decimal_odds": 1501.00, "implied_probability": 0.07, "rank": 41, "platforms": {"Bet365": 1501.00, "William Hill": 2001.00, "DraftKings": 1500.00}},
    "Iraq": {"decimal_odds": 1501.00, "implied_probability": 0.07, "rank": 41, "platforms": {"Bet365": 1501.00, "William Hill": 1501.00, "DraftKings": 1000.00}},
    "Cape Verde": {"decimal_odds": 2001.00, "implied_probability": 0.05, "rank": 44, "platforms": {"Bet365": 2001.00, "William Hill": 2001.00, "DraftKings": 1500.00}},
    "Curaçao": {"decimal_odds": 2001.00, "implied_probability": 0.05, "rank": 44, "platforms": {"Bet365": 2001.00, "William Hill": 2001.00, "DraftKings": 2000.00}},
    "Uzbekistan": {"decimal_odds": 2001.00, "implied_probability": 0.05, "rank": 44, "platforms": {"Bet365": 2001.00, "William Hill": 2001.00, "DraftKings": 2000.00}},
    "Jordan": {"decimal_odds": 2501.00, "implied_probability": 0.04, "rank": 47, "platforms": {"Bet365": 2501.00, "William Hill": 2501.00, "DraftKings": 2000.00}},
    "Haiti": {"decimal_odds": 3001.00, "implied_probability": 0.03, "rank": 48, "platforms": {"Bet365": 3001.00, "William Hill": 3001.00, "DraftKings": 3000.00}},
}


def calculate_elo_from_record(wins, draws, losses, goals_for, goals_against, total_matches):
    """Estimate ELO from match record using simplified model."""
    if total_matches < 5:
        return None

    win_rate = wins / total_matches
    goal_diff_per_match = (goals_for - goals_against) / total_matches

    # Base ELO range: ~1400 (weakest) to ~2200 (strongest)
    # Distribution: win_rate -> ELO_adjustment using normal approximation
    # ELO_diff ~ -400 * log10(1/win_rate - 1)

    if win_rate > 0 and win_rate < 1:
        elo_from_wr = 1500 + 400 * math.log10(win_rate / (1 - win_rate))
    elif win_rate >= 1:
        elo_from_wr = 2200
    else:
        elo_from_wr = 1400

    # Goal difference bonus
    gd_bonus = goal_diff_per_match * 50

    estimated_elo = elo_from_wr + gd_bonus

    # Clamp to realistic range
    return round(max(1300, min(2250, estimated_elo)))


def main():
    print("Enriching team data with ELO estimates and betting odds...")

    for team_dir in sorted(DATA_DIR.iterdir()):
        if not team_dir.is_dir():
            continue

        info_path = team_dir / "team_info.json"
        if not info_path.exists():
            continue

        with open(info_path, "r", encoding="utf-8") as f:
            team_data = json.load(f)

        team_name = team_data["team_en"]

        # Calculate ELO from match record
        stats = team_data.get("stats", {})
        if stats and stats.get("total_matches", 0) > 0:
            elo = calculate_elo_from_record(
                stats["wins"], stats["draws"], stats["losses"],
                stats["goals_for"], stats["goals_against"],
                stats["total_matches"]
            )
            if elo:
                team_data["elo_rating"] = elo

        # Add odds data
        if team_name in ODDS_DATA:
            team_data["odds"] = ODDS_DATA[team_name]

        # Add FIFA ranking estimate based on odds/ELO
        team_data["fifa_ranking"] = team_data.get("fifa_ranking") or None

        # Save back
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(team_data, f, ensure_ascii=False, indent=2)

        print(f"  {team_name}: ELO={team_data.get('elo_rating','N/A')}, "
              f"Odds={ODDS_DATA.get(team_name,{}).get('decimal_odds','N/A')}")

    # Also update all_teams.json with ELO
    all_teams_path = DATA_DIR / "all_teams.json"
    with open(all_teams_path, "r", encoding="utf-8") as f:
        all_teams = json.load(f)

    for team in all_teams:
        info_path = DATA_DIR / team["team_en"] / "team_info.json"
        if info_path.exists():
            with open(info_path, "r", encoding="utf-8") as f:
                detail = json.load(f)
            if "elo_rating" in detail:
                team["elo_rating"] = detail["elo_rating"]
            if "odds" in detail:
                team["odds_rank"] = detail["odds"].get("rank")

    with open(all_teams_path, "w", encoding="utf-8") as f:
        json.dump(all_teams, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(all_teams)} teams enriched.")


if __name__ == "__main__":
    main()
