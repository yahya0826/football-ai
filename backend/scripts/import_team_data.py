"""
Import player data from desktop folders into the football-ai backend.
Usage: python import_team_data.py "C:\...\Ghana_加纳" Ghana
Parses match-by-match stats.txt files, merges with existing players.json,
and copies headshots to frontend/public/headshots/.
"""
import json
import re
import shutil
import sys
from pathlib import Path

BACKEND_DATA = Path(r"C:\Users\ASUS\football-ai\backend\data\teams")
FRONTEND_PUBLIC = Path(r"C:\Users\ASUS\football-ai\frontend\public\headshots")

POSITION_DISPLAY = {
    'GK': '门将', 'DF': '后卫', 'CB': '中后卫', 'LB': '左后卫', 'RB': '右后卫',
    'LWB': '左边翼卫', 'RWB': '右边翼卫', 'CDM': '后腰', 'CM': '中前卫',
    'CAM': '前腰', 'MF': '中场', 'LM': '左边锋', 'RM': '右边锋',
    'LW': '左边锋', 'RW': '右边锋', 'ST': '中锋', 'FW': '前锋',
}


def parse_squad_list(path: Path) -> list[dict]:
    """Parse squad_list.txt to get player info with jersey numbers.
    Handles two main formats:
    A) With numbers:  'FW  9  Jordan Ayew (C)       乔丹·阿尤(队长)       Leicester City'
    B) Without numbers: 'GK Dominik Livaković     多米尼克·利瓦科维奇   Dinamo Zagreb'
    Also handles:
    - Chinese name glued to English: 'FW 13 Christopher Bonsu Baah克里斯托弗·邦苏·巴   Al Qadsiah'
    - Club with spaces: 'FW  10 Brandon Thomas-Asante 布兰登·托马斯-阿桑特 Coventry City'
    """
    players = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('===') or line.startswith('主教练'):
                continue

            # Try format A: Position + Number + Rest
            m = re.match(r'([A-Z]+)\s+(\d+)\s+(.+)', line)
            if m:
                pos_abbr = m.group(1)
                number = int(m.group(2))
                rest = m.group(3)
            else:
                # Try format B: Position + Name (no number)
                m = re.match(r'([A-Z]+)\s+(.+)', line)
                if not m:
                    continue
                pos_abbr = m.group(1)
                number = 0  # assign later
                rest = m.group(2)

            # Find Chinese character boundaries to split name_en / name_cn / club
            cjk = re.compile(r'[一-鿿　-〿＀-￯·]')
            cjk_positions = [i for i, ch in enumerate(rest) if cjk.match(ch)]

            if cjk_positions:
                cn_start = cjk_positions[0]
                cn_end = cjk_positions[-1] + 1
                name_en = rest[:cn_start].strip()
                name_cn = rest[cn_start:cn_end].strip()
                club = rest[cn_end:].strip()
            else:
                # No Chinese found — assume last field is club
                parts = re.split(r'\s{2,}', rest)
                if len(parts) >= 2:
                    name_en = parts[0].strip()
                    club = parts[-1].strip()
                    name_cn = ''
                else:
                    name_en = rest.strip()
                    name_cn = ''
                    club = ''

            name_en = name_en.replace(' (C)', '').rstrip('_C').strip()
            name_cn = name_cn.replace('(队长)', '').strip()

            players.append({
                'position': pos_abbr,
                'number': number,
                'name': name_en,
                'name_cn': name_cn,
                'club': club,
            })

    # If no numbers found, assign them in order
    if all(p['number'] == 0 for p in players):
        for i, p in enumerate(players):
            p['number'] = i + 1

    return players


def _norm(name: str) -> str:
    """Normalize a name for comparison: lowercase, replace separators with _."""
    return name.lower().replace(' ', '_').replace('-', '_').replace("'", '')


def build_folder_map(desktop_dir: Path, squad_players: list[dict]) -> dict[str, Path]:
    """Build a mapping from normalized player name to folder path.
    Handles folders with Chinese names appended: 'Brandon_Thomas-Asante_布兰登...'
    """
    folders = [f for f in desktop_dir.iterdir() if f.is_dir()]
    mapping = {}

    for sp in squad_players:
        name_key = _norm(sp['name'])
        # Account for special chars like ñ
        name_key_ascii = name_key.replace('ñ', 'n').replace('í', 'i').replace('é', 'e').replace('è', 'e').replace('ü', 'u').replace('ö', 'o').replace('ğ', 'g').replace('ş', 's').replace('İ', 'i').replace('ı', 'i')

        for folder in folders:
            folder_key = _norm(folder.name)
            if folder_key == name_key or folder_key == name_key + '_c':
                mapping[name_key] = folder
                break
            if folder_key.startswith(name_key) or folder_key.startswith(name_key_ascii):
                mapping[name_key] = folder
                break

    return mapping


def parse_stats_file(stats_path: Path, is_gk: bool) -> dict | None:
    """Parse match-by-match stats.txt using header-driven column mapping.
    Determines column indices from the header row for robustness against reordering.
    Falls back to fixed positions if no header is found.
    """
    with open(stats_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find the header row and build column index map
    col_map = {}
    header_seen = False
    for line in lines:
        parts = line.strip().split('\t')
        if len(parts) >= 10 and parts[0].strip() == 'Date':
            for i, col_name in enumerate(parts):
                col_name = col_name.strip()
                col_map[col_name] = i
            header_seen = True
            break

    # Parse match rows (lines starting with YYYY-MM-DD)
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
        return _aggregate_gk(matches, col_map)
    else:
        return _aggregate_field(matches, col_map)


def _col(col_map: dict, *names: str) -> int:
    """Get column index from the header map, or fall back to standard positions."""
    for name in names:
        if name in col_map:
            return col_map[name]

    # Fallback: standard FBref positions for field/GK
    # Field: Min=10, Gls=11, Ast=12, PK=13, PKatt=14, Sh=15, SoT=16,
    #        CrdY=17, CrdR=18, Fls=19, Fld=20, Off=21, Crs=22, TklW=23, Int=24, OG=25
    # GK:    Min=10, SoTA=11, GA=12, Saves=13, Save%=14, CS=15,
    #        PKatt=16, PKA=17, PKsv=18, PKm=19
    fallbacks = {
        'Min': 10, 'Gls': 11, 'Ast': 12, 'PK': 13, 'PKatt': 14,
        'Sh': 15, 'SoT': 16, 'CrdY': 17, 'CrdR': 18,
        'Fls': 19, 'Fld': 20, 'Off': 21, 'Crs': 22,
        'TklW': 23, 'Int': 24, 'OG': 25,
        'SoTA': 11, 'GA': 12, 'Saves': 13, 'Save%': 14, 'CS': 15,
        'PKA': 17, 'PKsv': 18, 'PKm': 19,
    }
    return fallbacks.get(names[0], -1)


def _val(row: list[str], col_map: dict, *names: str) -> int:
    """Extract an integer value by column name(s), using the header map or fallback."""
    idx = _col(col_map, *names)
    if idx < 0:
        return 0
    try:
        val = row[idx].strip()
        return int(val.replace(',', '')) if val else 0
    except (IndexError, ValueError):
        return 0


def _aggregate_field(rows: list[list[str]], col_map: dict) -> dict:
    total_minutes = total_goals = total_assists = total_pk = total_pk_att = 0
    total_shots = total_sot = total_yellow = total_red = 0
    total_fouls = total_fouls_drawn = total_offsides = 0
    total_crosses = total_tackles = total_interceptions = total_own_goals = 0
    starts = 0
    ratings = []

    start_idx = _col(col_map, 'Start')

    for row in rows:
        try:
            minutes = _val(row, col_map, 'Min')
            total_minutes += minutes
            if start_idx >= 0 and row[start_idx].strip() in ('Y', 'Y*'):
                starts += 1
            goals = _val(row, col_map, 'Gls')
            assists = _val(row, col_map, 'Ast')
            total_goals += goals
            total_assists += assists
            total_pk += _val(row, col_map, 'PK')
            total_pk_att += _val(row, col_map, 'PKatt')
            total_shots += _val(row, col_map, 'Sh')
            total_sot += _val(row, col_map, 'SoT')
            total_yellow += _val(row, col_map, 'CrdY')
            total_red += _val(row, col_map, 'CrdR')
            total_fouls += _val(row, col_map, 'Fls')
            total_fouls_drawn += _val(row, col_map, 'Fld')
            total_offsides += _val(row, col_map, 'Off')
            total_crosses += _val(row, col_map, 'Crs')
            total_tackles += _val(row, col_map, 'TklW')
            total_interceptions += _val(row, col_map, 'Int')
            if _col(col_map, 'OG') >= 0:
                total_own_goals += _val(row, col_map, 'OG')

            tkl = _val(row, col_map, 'TklW')
            intercept = _val(row, col_map, 'Int')
            yellow = _val(row, col_map, 'CrdY')
            red = _val(row, col_map, 'CrdR')
            game_rating = 6.0 + (goals * 0.8 + assists * 0.5) * (90 / max(minutes, 1))
            game_rating += min((tkl + intercept) * 0.05, 0.8)
            game_rating -= yellow * 0.3
            game_rating -= red * 1.5
            ratings.append(max(min(game_rating, 10), 4.5))
        except (IndexError, ValueError):
            continue

    appearances = len(rows)
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 6.5

    return {
        'appearances': appearances, 'starts': starts, 'minutes': total_minutes,
        'goals': total_goals, 'assists': total_assists,
        'pk': total_pk, 'pk_att': total_pk_att,
        'shots_total': total_shots, 'shots_on_target': total_sot,
        'yellow_cards': total_yellow, 'red_cards': total_red,
        'fouls': total_fouls, 'fouls_drawn': total_fouls_drawn,
        'offsides': total_offsides, 'crosses': total_crosses,
        'tackles_won': total_tackles, 'interceptions': total_interceptions,
        'own_goals': total_own_goals, 'rating': avg_rating,
    }


def _aggregate_gk(rows: list[list[str]], col_map: dict) -> dict:
    total_minutes = total_sota = total_ga = total_saves = total_cs = 0
    total_pk_att = total_pka = total_pk_sv = 0
    starts = 0
    start_idx = _col(col_map, 'Start')
    cs_idx = _col(col_map, 'CS')

    for row in rows:
        try:
            total_minutes += _val(row, col_map, 'Min')
            if start_idx >= 0 and row[start_idx].strip() in ('Y', 'Y*'):
                starts += 1
            total_sota += _val(row, col_map, 'SoTA')
            total_ga += _val(row, col_map, 'GA')
            total_saves += _val(row, col_map, 'Saves')
            if cs_idx >= 0 and row[cs_idx].strip() == '1':
                total_cs += 1
            if _col(col_map, 'PKatt') >= 0:
                total_pk_att += _val(row, col_map, 'PKatt')
            if _col(col_map, 'PKA') >= 0:
                total_pka += _val(row, col_map, 'PKA')
            if _col(col_map, 'PKsv') >= 0:
                total_pk_sv += _val(row, col_map, 'PKsv')
        except (IndexError, ValueError):
            continue

    appearances = len(rows)
    save_pct = round(total_saves / max(total_sota, 1) * 100, 1) if total_sota > 0 else 0
    rating = 6.0 + (save_pct / 100 * 2.0) + (total_cs / max(appearances, 1) * 2.0)
    rating = round(max(min(rating, 9.5), 5.0), 1)

    return {
        'appearances': appearances, 'starts': starts, 'minutes': total_minutes,
        'goals': 0, 'assists': 0, 'shots_total': 0, 'shots_on_target': 0,
        'yellow_cards': 0, 'red_cards': 0,
        'goals_conceded': total_ga, 'saves': total_saves,
        'save_pct': save_pct, 'clean_sheets': total_cs,
        'penalties_faced': total_pk_att, 'penalties_conceded': total_pka,
        'penalties_saved': total_pk_sv, 'rating': rating,
    }


def derive_attributes(stats: dict, position: str) -> dict:
    apps = max(stats.get('appearances', 1), 1)
    minutes = stats.get('minutes', 0)
    goals = stats.get('goals', 0)
    assists = stats.get('assists', 0)
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
    """Generate a URL-friendly ID from a player name."""
    result = name.lower().replace(' ', '-').replace("'", '')
    replacements = {'é': 'e', 'è': 'e', 'ê': 'e', 'ñ': 'n', 'í': 'i',
                    'ü': 'u', 'ö': 'o', 'ğ': 'g', 'ş': 's', 'İ': 'i',
                    'ı': 'i', 'ł': 'l', 'ć': 'c', 'š': 's', 'đ': 'd'}
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


def main():
    if len(sys.argv) < 3:
        print("Usage: python import_team_data.py <desktop_folder> <team_name>")
        print("Example: python import_team_data.py \"C:\\...\\Ghana_加纳\" Ghana")
        sys.exit(1)

    desktop_dir = Path(sys.argv[1])
    team_name = sys.argv[2]

    squad_path = desktop_dir / 'squad_list.txt'
    if not squad_path.exists():
        print(f"ERROR: squad_list.txt not found at {squad_path}")
        sys.exit(1)

    # Parse squad list
    squad_players = parse_squad_list(squad_path)
    print(f"Found {len(squad_players)} players in squad list for {team_name}")

    # Build folder mapping
    folder_map = build_folder_map(desktop_dir, squad_players)

    # Read existing players.json
    team_dir = BACKEND_DATA / team_name
    existing_path = team_dir / 'players.json'
    if existing_path.exists():
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        existing_players = {p['id']: p for p in existing_data.get('players', [])}
        print(f"Loaded {len(existing_players)} existing players")
    else:
        existing_data = {'team': team_name, 'total_players': 0, 'matched_count': 0, 'players': []}
        existing_players = {}
        print("No existing players.json, will create new")

    FRONTEND_PUBLIC.mkdir(parents=True, exist_ok=True)

    updated_players = []
    stats_found = 0
    headshots_copied = 0

    for sp in squad_players:
        player_id = generate_id(sp['name'])
        name_key = _norm(sp['name'])
        folder = folder_map.get(name_key)
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
        else:
            print(f"  WARNING: No folder found for {sp['name']}")

        existing = existing_players.get(player_id)

        player_entry = {
            'id': player_id,
            'name': sp['name'],
            'position': sp['position'],
            'position_display': POSITION_DISPLAY.get(sp['position'], sp['position']),
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

            mins = max(stats.get('minutes', 1), 1)
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
                'goals_p90': round(stats.get('goals', 0) / max(mins / 90, 0.01), 2),
                'assists_p90': round(stats.get('assists', 0) / max(mins / 90, 0.01), 2),
                'xg_p90': existing_stats.get('xg_p90') if existing_stats else None,
                'xa_p90': existing_stats.get('xa_p90') if existing_stats else None,
                'shots_p90': round(stats.get('shots_total', 0) / max(mins / 90, 0.01), 2),
                'key_passes_p90': existing_stats.get('key_passes_p90') if existing_stats else None,
                'tackles_p90': round(stats.get('tackles_won', 0) / max(mins / 90, 0.01), 2),
                'match_confidence': 'high',
                'data_source': 'FBref 2025-26',
                '_attributes': attributes or {
                    'speed': 60, 'shooting': 60, 'passing': 60,
                    'dribbling': 60, 'defending': 60, 'physical': 60,
                },
            }

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

    # Ensure team directory exists
    team_dir.mkdir(parents=True, exist_ok=True)

    matched = sum(1 for p in updated_players if p['stats'] and p['stats'].get('match_confidence') == 'high')
    output = {
        'team': team_name,
        'total_players': len(updated_players),
        'matched_count': matched,
        'players': updated_players,
    }

    with open(existing_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== Results for {team_name} ===")
    print(f"Total players: {len(updated_players)}")
    print(f"With detailed stats: {stats_found}")
    print(f"Headshots copied: {headshots_copied}")
    print(f"Saved to: {existing_path}")

    # Print summary
    for p in updated_players:
        s = p.get('stats', {})
        av = 'pic' if p.get('avatar') else 'no-pic'
        if s:
            print(f"  {p['name']:30s} #{p['number']:2d} {p['position']:3s} {s.get('appearances',0):3d}apps {s.get('goals',0):3d}G {s.get('assists',0):3d}A  [{av}]")
        else:
            print(f"  {p['name']:30s} #{p['number']:2d} {p['position']:3s} NO STATS  [{av}]")


if __name__ == '__main__':
    main()
