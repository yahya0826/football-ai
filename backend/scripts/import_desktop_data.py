"""
Import desktop player data (stats + avatars) into the backend platform.

Reads stats.txt and .jpg avatars from Desktop/WorldCup2026,
matches them to backend players by normalized name comparison,
and produces updated players.json files + copies avatars.
"""

import json
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path
from typing import Dict, Optional, Tuple

DESKTOP_ROOT = Path(os.environ.get("DESKTOP_ROOT", "C:/Users/ASUS/Desktop/WorldCup2026"))
BACKEND_TEAMS = Path(os.environ.get("BACKEND_TEAMS", "C:/Users/ASUS/football-ai/backend/data/teams"))
AVATARS_OUT = Path(os.environ.get("AVATARS_OUT", "C:/Users/ASUS/football-ai/frontend/public/headshots"))

NAME_MAP: Dict[str, str] = {
    "Bosnia and Herzegovina": "Bosnia and Herzegovina",
    "Bosnia": "Bosnia and Herzegovina",
    "Cape Verde": "Cape Verde",
    "Curacao": "Curaçao",
    "Curaçao": "Curaçao",
    "DR Congo": "DR Congo",
    "Ivory Coast": "Ivory Coast",
    "New Zealand": "New Zealand",
    "Saudi Arabia": "Saudi Arabia",
    "South Africa": "South Africa",
    "South Korea": "South Korea",
    "United States": "United States",
    "USA": "United States",
    "Czechia": "Czech Republic",
    "Czech Republic": "Czech Republic",
}


def name_key(name: str) -> str:
    """Normalize name for comparison: lower, strip diacritics, remove separators."""
    clean = name.lower()
    # Strip _C, _VC suffixes
    if clean.endswith("_c"):
        clean = clean[:-2]
    elif clean.endswith("_vc"):
        clean = clean[:-3]
    clean = clean.replace("_", "").replace(" ", "").replace("-", "").replace(".", "")
    return unicodedata.normalize("NFKD", clean).encode("ascii", "ignore").decode()


def extract_team_en(folder_name: str) -> str:
    """Extract English team name from 'South_Africa_南非'."""
    parts = folder_name.split("_")
    eng_parts = []
    for p in parts:
        if not p:
            continue
        # Check if first char is CJK
        if "一" <= p[0] <= "鿿":
            break
        eng_parts.append(p)
    return " ".join(eng_parts)


def normalize_team(desktop_en: str) -> str:
    """Map desktop team name to API team name."""
    if desktop_en in NAME_MAP:
        return NAME_MAP[desktop_en]
    return desktop_en


def parse_stats_file(filepath: str) -> Optional[dict]:
    """Parse a single stats.txt and return aggregated stats dict.

    Handles two formats:
    - Field player:  ...Start|Pos|Min|Gls|Ast|PK|PKatt|Sh|SoT|CrdY|CrdR|Fls|Fld|Off|Crs|TklW|Int|OG|PKwon|PKcon
    - Goalkeeper:    ...Start|Pos|Min|SoTA|GA|Saves|Save%|CS|PKatt|PKA|PKsv|PKm
    """
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return None

    if len(lines) < 2:
        return None

    apps = starts = mins = 0
    wins = draws = losses = 0
    # Field columns
    gls = ast = pk_scored = pk_attempted = 0
    shots = sot = yellows = reds = fls = fld = offs = crosses = 0
    tkl = inter = og = pk_won = pk_conceded = 0
    # GK columns
    saves = goals_conceded = clean_sheets = pk_against = pk_saved = 0

    header_found = False
    is_gk = False
    parsed_rows = 0

    for raw in lines:
        line = raw.rstrip("\n").rstrip("\r")
        if not line.strip():
            continue
        if line.strip().startswith("Includes") or line.strip().startswith("Stats include"):
            continue

        fields = line.split("\t")

        # Check for summary row (W-D-L pattern like "25-13-11")
        if fields and fields[0].strip():
            first = fields[0].strip()
            if re.match(r"^\d+-\d+-\d+$", first) and not re.match(r"^\d{4}-\d{2}-\d{2}$", first):
                if parsed_rows > 0:
                    continue
                wdl = first.split("-")
                if len(wdl) == 3:
                    wins = int(wdl[0]) if wdl[0].isdigit() else 0
                    draws = int(wdl[1]) if wdl[1].isdigit() else 0
                    losses = int(wdl[2]) if wdl[2].isdigit() else 0
                if len(fields) >= 6:
                    try:
                        mins = int(fields[5].replace(",", "")) if fields[5].strip() else 0
                    except ValueError:
                        pass
                continue

        # Detect header row and determine format
        if not header_found and "Performance" in raw:
            header_found = True
            is_gk = "SoTA" in raw or "GA" in raw
            # Also check next line (column header) if current line doesn't have format info
            continue

        if header_found and not parsed_rows and not is_gk:
            # First line after "Performance" is the column header — re-check format
            is_gk = "SoTA" in raw or "GA" in raw

        if not header_found:
            continue

        # Data row: date must be YYYY-MM-DD
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", fields[0].strip() if fields and fields[0] else ""):
            continue

        parsed_rows += 1

        def sf(i: int) -> str:
            return fields[i].strip() if i < len(fields) else ""

        def si(i: int) -> int:
            v = sf(i)
            return int(v) if v and v.isdigit() else 0

        # Start at index 8 for both formats
        start_val = sf(8)
        if start_val == "Y" or (start_val and start_val.startswith("Y")):
            starts += 1
            apps += 1
        elif start_val == "N":
            apps += 1

        # Min at index 10 for both formats (index 9 is Pos)
        mins += si(10)

        if is_gk:
            saves += si(13)
            goals_conceded += si(12)
            clean_sheets += si(15)
            pk_against += si(16)
            pk_saved += si(18)
        else:
            gls += si(11)
            ast += si(12)
            pk_scored += si(13)
            pk_attempted += si(14)
            shots += si(15)
            sot += si(16)
            yellows += si(17)
            reds += si(18)
            fls += si(19)
            fld += si(20)
            offs += si(21)
            crosses += si(22)
            tkl += si(23)
            inter += si(24)
            og += si(25)
            pk_won += si(26)
            pk_conceded += si(27)

        # Result at index 5 for both
        res = sf(5)
        if res.startswith("W"):
            wins += 1
        elif res.startswith("D"):
            draws += 1
        elif res.startswith("L"):
            losses += 1

    if apps == 0:
        return None

    safe_mins = max(mins, 1)

    if is_gk:
        return {
            "appearances": apps,
            "starts": starts,
            "minutes": mins,
            "goals": 0,
            "assists": 0,
            "pk_scored": 0,
            "pk_attempted": 0,
            "shots": 0,
            "shots_on_target": 0,
            "yellow_cards": yellows,
            "red_cards": reds,
            "fouls": fls,
            "fouled": fld,
            "offsides": 0,
            "crosses": 0,
            "tackles_won": 0,
            "interceptions": 0,
            "own_goals": 0,
            "pk_won": 0,
            "pk_conceded": 0,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_p90": 0,
            "assists_p90": 0,
            "shots_p90": 0,
            "tackles_p90": 0,
            "shot_conversion": 0,
            "shot_accuracy": 0,
            "start_rate": round(starts / max(apps, 1) * 100, 1),
            "saves": saves,
            "goals_conceded": goals_conceded,
            "clean_sheets": clean_sheets,
            "pk_against": pk_against,
            "pk_saved": pk_saved,
            "data_source": "desktop",
            "has_real_data": True,
        }

    safe_apps = max(apps, 1)
    return {
        "appearances": apps,
        "starts": starts,
        "minutes": mins,
        "goals": gls,
        "assists": ast,
        "pk_scored": pk_scored,
        "pk_attempted": pk_attempted,
        "shots": shots,
        "shots_on_target": sot,
        "yellow_cards": yellows,
        "red_cards": reds,
        "fouls": fls,
        "fouled": fld,
        "offsides": offs,
        "crosses": crosses,
        "tackles_won": tkl,
        "interceptions": inter,
        "own_goals": og,
        "pk_won": pk_won,
        "pk_conceded": pk_conceded,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_p90": round(gls / safe_mins * 90, 2),
        "assists_p90": round(ast / safe_mins * 90, 2),
        "shots_p90": round(shots / safe_mins * 90, 2),
        "tackles_p90": round(tkl / safe_mins * 90, 2),
        "shot_conversion": round(gls / max(shots, 1) * 100, 1),
        "shot_accuracy": round(sot / max(shots, 1) * 100, 1),
        "start_rate": round(starts / safe_apps * 100, 1),
        "data_source": "desktop",
        "has_real_data": True,
    }


def find_player_in_team(team_dir: Path, player_key: str) -> Optional[Path]:
    """Find a player folder in a team directory by name key."""
    for pdir in sorted(team_dir.iterdir()):
        if not pdir.is_dir():
            continue
        pk = name_key(pdir.name)
        if pk == player_key:
            return pdir
    return None


def import_all():
    """Main import function."""
    AVATARS_OUT.mkdir(parents=True, exist_ok=True)

    # Build desktop player index
    print("=== Building desktop player index ===")
    desktop_index: Dict[str, Dict[str, Tuple[Path, dict]]] = {}  # {team_api: {player_key: (folder, stats)}}

    total_desktop_players = 0
    total_desktop_stats = 0
    total_desktop_avatars = 0

    for group_dir in sorted(DESKTOP_ROOT.iterdir()):
        if not group_dir.is_dir() or not group_dir.name.startswith("Group_"):
            continue
        for team_dir in sorted(group_dir.iterdir()):
            if not team_dir.is_dir():
                continue
            team_en = extract_team_en(team_dir.name)
            team_api = normalize_team(team_en)

            if team_api not in desktop_index:
                desktop_index[team_api] = {}

            for player_dir in sorted(team_dir.iterdir()):
                if not player_dir.is_dir():
                    continue
                total_desktop_players += 1
                pk = name_key(player_dir.name)
                stats_file = player_dir / "stats.txt"
                stats = parse_stats_file(str(stats_file))
                if stats:
                    total_desktop_stats += 1

                # Check for avatar
                avatar_file = None
                for f in player_dir.iterdir():
                    if f.suffix.lower() == ".jpg":
                        avatar_file = f
                        total_desktop_avatars += 1
                        break

                desktop_index[team_api][pk] = (player_dir, stats, avatar_file)

    print(f"Desktop: {total_desktop_players} players, {total_desktop_stats} stats, {total_desktop_avatars} avatars")
    print(f"Teams: {len(desktop_index)}")

    # Process each backend team
    print("\n=== Importing data ===")
    total_merged = 0
    total_avatar_copied = 0
    total_missing_match = 0
    updated_teams = 0

    for team_dir in sorted(BACKEND_TEAMS.iterdir()):
        if not team_dir.is_dir():
            continue
        team_name = team_dir.name

        # Skip non-team directories
        if team_name in ("Coach representation by country", "_index.json", "all_teams.json"):
            continue

        pfile = team_dir / "players.json"
        if not pfile.exists():
            print(f"  SKIP {team_name}: no players.json")
            continue

        with open(pfile, encoding="utf-8") as f:
            data = json.load(f)

        desktop_players = desktop_index.get(team_name, {})
        if not desktop_players:
            # Try fuzzy match with desktop team names
            for dt_name, d_players in desktop_index.items():
                if dt_name.lower() == team_name.lower():
                    desktop_players = d_players
                    break
                # Try normalized comparison
                if name_key(dt_name) == name_key(team_name):
                    desktop_players = d_players
                    break

        if not desktop_players:
            print(f"  NO DESKTOP: {team_name} (no matching desktop data)")
            continue

        team_updated = False
        team_merged = 0
        team_avatars = 0

        for player in data.get("players", []):
            player_name = player.get("name", "")
            pk = name_key(player_name)

            # Try exact match first
            match = desktop_players.get(pk)
            if not match:
                # Try without middle name
                name_parts = player_name.split()
                if len(name_parts) >= 3:
                    short_key = name_key(f"{name_parts[0]}_{name_parts[-1]}")
                    match = desktop_players.get(short_key)
                # Try first name + last initial
                if not match and len(name_parts) >= 2:
                    alt_key = name_key(f"{name_parts[0]}_{name_parts[-1]}")
                    if alt_key != pk:
                        match = desktop_players.get(alt_key)

            if not match:
                total_missing_match += 1
                continue

            player_folder, desktop_stats, avatar_file = match

            existing_stats = player.get("stats") or {}

            if desktop_stats:
                # Merge: desktop as base + Sofascore advanced metrics
                merged = dict(desktop_stats)
                merged["data_source"] = "desktop"
                merged["has_real_data"] = True
                # Preserve Sofascore advanced fields
                for sof_key in ("rating", "xg", "xa", "pass_accuracy", "key_passes",
                                "progressive_passes", "dribble_success_rate",
                                "match_confidence", "_attributes", "touches",
                                "xg_p90", "xa_p90", "interceptions_p90",
                                "key_passes_p90", "progressive_passes"):
                    if sof_key in existing_stats and existing_stats[sof_key] is not None:
                        merged[sof_key] = existing_stats[sof_key]
                player["stats"] = merged
                team_merged += 1
                total_merged += 1

            # Copy avatar
            if avatar_file:
                ext = avatar_file.suffix.lower()
                avatar_out = AVATARS_OUT / f"{player['id']}{ext}"
                try:
                    if not avatar_out.exists():
                        shutil.copy2(str(avatar_file), str(avatar_out))
                    player["avatar"] = f"/headshots/{player['id']}{ext}"
                    team_avatars += 1
                    total_avatar_copied += 1
                except Exception as e:
                    print(f"    Avatar copy failed for {player_name}: {e}")

        if team_merged > 0:
            data["matched_count"] = team_merged
            with open(pfile, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            updated_teams += 1

        print(f"  {team_name}: merged {team_merged} stats, {team_avatars} avatars")

    print(f"\n=== Summary ===")
    print(f"Teams updated: {updated_teams}")
    print(f"Players merged: {total_merged}")
    print(f"Avatars copied: {total_avatar_copied}")
    print(f"Unmatched players: {total_missing_match}")


if __name__ == "__main__":
    import_all()
