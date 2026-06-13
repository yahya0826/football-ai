"""
同步球员赛季数据 v2.0
- datafc (Sofascore): 19 联赛, 2025-26 赛季
- FPL API: 英超辅助
- 输出: data/teams/{国家队}/players.json (Unified Stats)
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.squad_service import squad_service
from services.player_data_service import player_data_service


def main():
    parser = argparse.ArgumentParser(description="同步球员赛季数据")
    parser.add_argument("--sofascore-only", action="store_true", help="仅使用 Sofascore")
    parser.add_argument("--fpl-only", action="store_true", help="仅使用 FPL")
    args = parser.parse_args()

    print("=" * 50)
    print("  STEP 1: Load squad data (Wikipedia)")
    print("=" * 50)
    squads = squad_service.load_squads()
    if not squads:
        print("No squad data found. Run squad_service.fetch_all_squads() first.")
        return
    print(f"  {len(squads)} teams loaded\n")

    print("=" * 50)
    print("  STEP 2: Fetch & match (Sofascore + FPL)")
    print("=" * 50)
    enriched = player_data_service.match_and_enrich(squads)

    print("\n" + "=" * 50)
    print("  STEP 3: Save players.json for all teams")
    print("=" * 50)
    player_data_service.save_all(enriched, squad_service.teams_dir)

    # Update index
    index_data = {}
    index_path = squad_service.teams_dir / "_index.json"
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            index_data = json.load(f)

    for country in enriched:
        players_path = squad_service.teams_dir / country / "players.json"
        if players_path.exists():
            with open(players_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            index_data[country] = {
                "total": data["total_players"],
                "matched": data.get("matched_count", 0),
            }

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump({
            "teams": index_data,
            "total_teams": len(index_data),
        }, f, ensure_ascii=False, indent=2)

    # Summary
    total = sum(len(p) for p in enriched.values())
    matched = sum(
        sum(1 for p in players if p.get("stats"))
        for players in enriched.values()
    )
    print(f"\nDone: {matched}/{total} players matched ({matched/total*100:.1f}%)")
    print(f"  Missing: {total - matched}")


if __name__ == "__main__":
    main()
