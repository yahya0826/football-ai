"""
Import England player data from desktop folders.
Parses match-by-match stats.txt files, extracts aggregate data,
merges with existing players.json, and copies headshots.

Column formats:
  Field players: Date Day Comp Round Venue Result Squad Opponent Start Pos Min Gls Ast PK PKatt Sh SoT CrdY CrdR Fls Fld Off Crs TklW Int OG PKwon PKcon
  Goalkeepers:   Date Day Comp Round Venue Result Squad Opponent Start Pos Min SoTA GA Saves Save% CS PKatt PKA PKsv PKm
"""
import json
import os
import re
import shutil
from pathlib import Path

DESKTOP_DIR = Path(r"C:\Users\ASUS\Desktop\WorldCup2026\Group_L\England_英格兰")
BACKEND_TEAM_DIR = Path(r"C:\Users\ASUS\football-ai\backend\data\teams\England")
FRONTEND_PUBLIC = Path(r"C:\Users\ASUS\football-ai\frontend\public\headshots")

POSITION_MAP = {
    'GK': 'GK', 'CB': 'CB', 'LB': 'LB', 'RB': 'RB', 'DF': 'CB',
    'CM': 'CM', 'CDM': 'CDM', 'CAM': 'CAM', 'MF': 'CM',
    'LM': 'LM', 'RM': 'RM', 'LW': 'LW', 'RW': 'RW',
    'ST': 'ST', 'FW': 'ST',
}


def parse_squad_list(path: Path) -> list[dict]:
    """Parse squad_list.txt to get player info with jersey numbers."""
    players = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('===') or line.startswith('主教练'):
                continue
            match = re.match(
                r'([A-Z]+)\s+(\d+)\s+(.+?)\s{2,}(.+?)\s{2,}(.+)', line
            )
            if match:
                pos_abbr, number, name_en, name_cn, club = match.groups()
                name_en = name_en.replace(' (C)', '').strip()
                name_cn = name_cn.replace('(队长)', '').strip()
                club = club.strip()
                players.append({
                    'position': pos_abbr,
                    'number': int(number),
                    'name': name_en,
                    'name_cn': name_cn,
                    'club': club,
                })
    return players


def find_player_folder(player_name: str) -> Path | None:
    """Find the folder for a player by matching their name."""
    name_norm = player_name.lower().replace(' ', '_').replace('-', '_')

    for folder in DESKTOP_DIR.iterdir():
        if not folder.is_dir():
            continue
        folder_name = folder.name.lower()
        if folder_name == name_norm:
            return folder
        if name_norm in folder_name or folder_name.replace('_c', '') == name_norm:
            return folder
    return None


def parse_stats_file(stats_path: Path, is_gk: bool) -> dict | None:
    """Parse match-by-match stats.txt and compute aggregate totals.
    Some files have no header (data starts immediately), others have a header
    preceded by some data rows, and others have a proper header at the top.
    """
    with open(stats_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Parse ALL lines that look like match data (start with YYYY-MM-DD date)
    matches = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) < 13:
            continue
        if not re.match(r'\d{4}-\d{2}-\d{2}', parts[0]):
            continue
        matches.append(parts)

    if not matches:
        return None

    if is_gk:
        return _aggregate_gk(matches)
    else:
        return _aggregate_field(matches)


def _aggregate_field(rows: list[list[str]]) -> dict:
    """Aggregate field player match data.
    Columns: Date(0) Day(1) Comp(2) Round(3) Venue(4) Result(5) Squad(6) Opponent(7)
             Start(8) Pos(9) Min(10) Gls(11) Ast(12) PK(13) PKatt(14) Sh(15) SoT(16)
             CrdY(17) CrdR(18) Fls(19) Fld(20) Off(21) Crs(22) TklW(23) Int(24)
             OG(25) PKwon(26) PKcon(27)
    """
    total_minutes = 0
    total_goals = 0
    total_assists = 0
    total_pk = 0
    total_pk_att = 0
    total_shots = 0
    total_sot = 0
    total_yellow = 0
    total_red = 0
    total_fouls = 0
    total_fouls_drawn = 0
    total_offsides = 0
    total_crosses = 0
    total_tackles = 0
    total_interceptions = 0
    total_own_goals = 0
    starts = 0
    appearances = 0
    ratings = []

    for row in rows:
        try:
            minutes = _safe_int(row, 10)
            total_minutes += minutes

            if row[8].strip() in ('Y', 'Y*'):
                starts += 1

            goals = _safe_int(row, 11)
            assists = _safe_int(row, 12)
            total_goals += goals
            total_assists += assists
            total_pk += _safe_int(row, 13)
            total_pk_att += _safe_int(row, 14)
            total_shots += _safe_int(row, 15)
            total_sot += _safe_int(row, 16)
            total_yellow += _safe_int(row, 17)
            total_red += _safe_int(row, 18)
            total_fouls += _safe_int(row, 19)
            total_fouls_drawn += _safe_int(row, 20)
            total_offsides += _safe_int(row, 21)
            total_crosses += _safe_int(row, 22)
            total_tackles += _safe_int(row, 23)
            total_interceptions += _safe_int(row, 24)
            if len(row) > 25:
                total_own_goals += _safe_int(row, 25)

            # Rough rating per game: 6.0 base + goals/assists contribution
            game_rating = 6.0 + (goals * 0.8 + assists * 0.5) * (90 / max(minutes, 1))
            # Bonus for tackles and interceptions (defensive work)
            tackles = _safe_int(row, 23)
            interceptions = _safe_int(row, 24)
            game_rating += min((tackles + interceptions) * 0.05, 0.8)
            # Penalty for yellow cards
            game_rating -= _safe_int(row, 17) * 0.3
            # Penalty for red cards
            game_rating -= _safe_int(row, 18) * 1.5
            ratings.append(max(min(game_rating, 10), 4.5))
        except (IndexError, ValueError):
            continue

    appearances = len(rows)
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 6.5

    return {
        'appearances': appearances,
        'starts': starts,
        'minutes': total_minutes,
        'goals': total_goals,
        'assists': total_assists,
        'pk': total_pk,
        'pk_att': total_pk_att,
        'shots_total': total_shots,
        'shots_on_target': total_sot,
        'yellow_cards': total_yellow,
        'red_cards': total_red,
        'fouls': total_fouls,
        'fouls_drawn': total_fouls_drawn,
        'offsides': total_offsides,
        'crosses': total_crosses,
        'tackles_won': total_tackles,
        'interceptions': total_interceptions,
        'own_goals': total_own_goals,
        'rating': avg_rating,
    }


def _aggregate_gk(rows: list[list[str]]) -> dict:
    """Aggregate goalkeeper match data.
    Columns: Date(0) Day(1) Comp(2) Round(3) Venue(4) Result(5) Squad(6) Opponent(7)
             Start(8) Pos(9) Min(10) SoTA(11) GA(12) Saves(13) Save%(14) CS(15)
             PKatt(16) PKA(17) PKsv(18) PKm(19)
    """
    total_minutes = 0
    total_sota = 0
    total_ga = 0
    total_saves = 0
    total_cs = 0
    total_pk_att = 0
    total_pka = 0
    total_pk_sv = 0
    starts = 0
    appearances = 0
    total_yellow = 0
    total_red = 0

    for row in rows:
        try:
            minutes = _safe_int(row, 10)
            total_minutes += minutes

            if row[8].strip() in ('Y', 'Y*'):
                starts += 1

            total_sota += _safe_int(row, 11)
            total_ga += _safe_int(row, 12)
            total_saves += _safe_int(row, 13)
            cs = row[15].strip()
            if cs == '1':
                total_cs += 1
            if len(row) > 16:
                total_pk_att += _safe_int(row, 16)
            if len(row) > 17:
                total_pka += _safe_int(row, 17)
            if len(row) > 18:
                total_pk_sv += _safe_int(row, 18)
            # Yellows/reds for GK - not in these columns but sometimes available
        except (IndexError, ValueError):
            continue

    appearances = len(rows)
    save_pct = round(total_saves / max(total_sota, 1) * 100, 1) if total_sota > 0 else 0
    # GK rating based on save percentage and clean sheets
    rating = 6.0 + (save_pct / 100 * 2.0) + (total_cs / max(appearances, 1) * 2.0)
    rating = round(max(min(rating, 9.5), 5.0), 1)

    return {
        'appearances': appearances,
        'starts': starts,
        'minutes': total_minutes,
        'goals': 0,
        'assists': 0,
        'shots_total': 0,
        'shots_on_target': 0,
        'yellow_cards': total_yellow,
        'red_cards': total_red,
        # GK-specific
        'goals_conceded': total_ga,
        'saves': total_saves,
        'save_pct': save_pct,
        'clean_sheets': total_cs,
        'penalties_faced': total_pk_att,
        'penalties_conceded': total_pka,
        'penalties_saved': total_pk_sv,
        'rating': rating,
    }


def _safe_int(row: list[str], idx: int) -> int:
    """Safely parse an integer from a row column."""
    try:
        val = row[idx].strip()
        if not val:
            return 0
        return int(val.replace(',', ''))
    except (IndexError, ValueError):
        return 0


def derive_attributes(stats: dict, position: str) -> dict:
    """Derive player attribute scores (0-100) from stats."""
    apps = max(stats.get('appearances', 1), 1)
    minutes = stats.get('minutes', 0)
    goals = stats.get('goals', 0)
    assists = stats.get('assists', 0)
    shots = stats.get('shots_total', 0)
    tackles = stats.get('tackles_won', 0)
    interceptions = stats.get('interceptions', 0)
    crosses = stats.get('crosses', 0)

    goal_rate = min(goals / apps * 5, 1)
    shooting = round(50 + goal_rate * 45)

    assist_rate = min(assists / apps * 8, 1)
    passing = round(55 + assist_rate * 35)

    if position in ('LB', 'RB', 'LW', 'RW', 'LWB', 'RWB'):
        speed_base = 70
    else:
        speed_base = 55
    speed = round(speed_base + min(crosses / apps * 10, 1) * 25)

    dribbling = round(55 + min((goals + assists) / apps * 5, 1) * 35)

    def_rate = (tackles + interceptions) / apps
    defending = round(40 + min(def_rate / 3, 1) * 50)

    mins_per_app = minutes / apps
    physical = round(60 + min(mins_per_app / 90, 1) * 30)

    return {
        'speed': max(min(speed, 99), 30),
        'shooting': max(min(shooting, 99), 30),
        'passing': max(min(passing, 99), 30),
        'dribbling': max(min(dribbling, 99), 30),
        'defending': max(min(defending, 99), 30),
        'physical': max(min(physical, 99), 30),
    }


def generate_id(name: str) -> str:
    return name.lower().replace(' ', '-').replace("'", '').replace('é', 'e').replace('è', 'e')


def main():
    squad_path = DESKTOP_DIR / 'squad_list.txt'
    if not squad_path.exists():
        print(f"ERROR: squad_list.txt not found at {squad_path}")
        return

    squad_players = parse_squad_list(squad_path)
    print(f"Found {len(squad_players)} players in squad list")

    # Read existing players.json
    existing_path = BACKEND_TEAM_DIR / 'players.json'
    if existing_path.exists():
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        existing_players = {p['id']: p for p in existing_data.get('players', [])}
        print(f"Loaded {len(existing_players)} existing players")
    else:
        existing_data = {'team': 'England', 'total_players': 0, 'matched_count': 0, 'players': []}
        existing_players = {}

    FRONTEND_PUBLIC.mkdir(parents=True, exist_ok=True)

    updated_players = []
    stats_found = 0
    headshots_copied = 0

    for sp in squad_players:
        player_id = generate_id(sp['name'])
        folder = find_player_folder(sp['name'])
        is_gk = sp['position'] == 'GK'

        stats = None
        attributes = None
        avatar = None

        if folder:
            stats_path = folder / 'stats.txt'
            if stats_path.exists():
                raw_stats = parse_stats_file(stats_path, is_gk)
                if raw_stats:
                    stats = raw_stats
                    attributes = derive_attributes(raw_stats, sp['position'])
                    stats_found += 1

            jpg_files = list(folder.glob('*.jpg'))
            if jpg_files:
                src = jpg_files[0]
                dst_name = f"{player_id}.jpg"
                dst = FRONTEND_PUBLIC / dst_name
                shutil.copy2(src, dst)
                avatar = f"/headshots/{dst_name}"
                headshots_copied += 1

        existing = existing_players.get(player_id)

        player_entry = {
            'id': player_id,
            'name': sp['name'],
            'position': sp['position'],
            'position_display': POSITION_MAP.get(sp['position'], sp['position']),
            'number': sp['number'],
            'club': sp['club'],
            'age': existing.get('age', 0) if existing else 0,
            'national_caps': existing.get('national_caps', 0) if existing else 0,
            'national_goals': existing.get('national_goals', 0) if existing else 0,
            'stats': None,
        }

        if avatar:
            player_entry['avatar'] = avatar
        elif existing and existing.get('avatar'):
            player_entry['avatar'] = existing['avatar']

        if stats:
            existing_stats = existing.get('stats') if existing else None

            rating_value = stats.get('rating', 6.5)
            if existing_stats and existing_stats.get('match_confidence') == 'high':
                rating_value = existing_stats.get('rating', rating_value)

            merged_stats = {
                'appearances': stats.get('appearances', 0),
                'starts': stats.get('starts', 0),
                'minutes': stats.get('minutes', 0),
                'goals': stats.get('goals', 0),
                'assists': stats.get('assists', 0),
                'rating': rating_value,
                'yellow_cards': stats.get('yellow_cards', 0),
                'red_cards': stats.get('red_cards', 0),
                'xg': existing_stats.get('xg') if existing_stats else None,
                'shots_total': stats.get('shots_total', 0),
                'shots_on_target': stats.get('shots_on_target', 0),
                'shot_accuracy': None,
                'pass_accuracy': existing_stats.get('pass_accuracy') if existing_stats else None,
                'key_passes': existing_stats.get('key_passes') if existing_stats else None,
                'progressive_passes': existing_stats.get('progressive_passes') if existing_stats else None,
                'tackles': stats.get('tackles_won', 0),
                'interceptions': stats.get('interceptions', 0),
                'clearances': existing_stats.get('clearances') if existing_stats else None,
                'dribble_success_rate': existing_stats.get('dribble_success_rate') if existing_stats else None,
                'goals_p90': round(stats.get('goals', 0) / max(stats.get('minutes', 1) / 90, 0.01), 2),
                'assists_p90': round(stats.get('assists', 0) / max(stats.get('minutes', 1) / 90, 0.01), 2),
                'xg_p90': existing_stats.get('xg_p90') if existing_stats else None,
                'xa_p90': existing_stats.get('xa_p90') if existing_stats else None,
                'shots_p90': round(stats.get('shots_total', 0) / max(stats.get('minutes', 1) / 90, 0.01), 2),
                'key_passes_p90': existing_stats.get('key_passes_p90') if existing_stats else None,
                'tackles_p90': round(stats.get('tackles_won', 0) / max(stats.get('minutes', 1) / 90, 0.01), 2),
                'match_confidence': 'high',
                'data_source': 'FBref 2025-26',
                '_attributes': attributes or {
                    'speed': 60, 'shooting': 60, 'passing': 60,
                    'dribbling': 60, 'defending': 60, 'physical': 60,
                },
            }

            # Add GK-specific fields
            if is_gk:
                merged_stats['goals_conceded'] = stats.get('goals_conceded', 0)
                merged_stats['saves'] = stats.get('saves', 0)
                merged_stats['save_pct'] = stats.get('save_pct', 0)
                merged_stats['clean_sheets'] = stats.get('clean_sheets', 0)
                merged_stats['penalties_saved'] = stats.get('penalties_saved', 0)

            player_entry['stats'] = merged_stats
        elif existing and existing.get('stats'):
            player_entry['stats'] = existing['stats']

        updated_players.append(player_entry)

    matched = sum(1 for p in updated_players if p['stats'] and p['stats'].get('match_confidence') == 'high')
    output = {
        'team': 'England',
        'total_players': len(updated_players),
        'matched_count': matched,
        'players': updated_players,
    }

    with open(existing_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== Results ===")
    print(f"Total players: {len(updated_players)}")
    print(f"With detailed stats: {stats_found}")
    print(f"Headshots copied: {headshots_copied}")
    print(f"Saved to: {existing_path}")

    # Print sample
    print("\n=== Sample (Harry Kane) ===")
    for p in updated_players:
        if 'kane' in p['id']:
            s = p.get('stats', {})
            print(f"  Goals: {s.get('goals')}, Assists: {s.get('assists')}, Shots: {s.get('shots_total')}")
            print(f"  Apps: {s.get('appearances')}, Starts: {s.get('starts')}, Mins: {s.get('minutes')}")
            print(f"  Rating: {s.get('rating')}, YC: {s.get('yellow_cards')}, RC: {s.get('red_cards')}")
            break

    print("\n=== Sample (Pickford - GK) ===")
    for p in updated_players:
        if 'pickford' in p['id']:
            s = p.get('stats', {})
            print(f"  Apps: {s.get('appearances')}, Mins: {s.get('minutes')}")
            print(f"  GA: {s.get('goals_conceded')}, Saves: {s.get('saves')}")
            print(f"  CS: {s.get('clean_sheets')}, Save%: {s.get('save_pct')}")
            break


if __name__ == '__main__':
    main()
