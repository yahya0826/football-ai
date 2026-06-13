"""
世界杯大名单抓取服务 - 从 Wikipedia 获取48强最新大名单
"""
import re
import json
import httpx
from pathlib import Path
from typing import Dict, List, Optional
from collections import OrderedDict
from bs4 import BeautifulSoup

WIKI_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"

HEADERS = {
    "User-Agent": "FootballAI/1.0 (data-collection; contact@example.com)",
    "Accept": "text/html,application/xhtml+xml",
}

POSITION_MAP = {
    "GK": {"en": "Goalkeeper", "cn": "守门员"},
    "CB": {"en": "Centre-Back", "cn": "中后卫"},
    "LB": {"en": "Left-Back", "cn": "左后卫"},
    "RB": {"en": "Right-Back", "cn": "右后卫"},
    "LWB": {"en": "Left Wing-Back", "cn": "左边翼卫"},
    "RWB": {"en": "Right Wing-Back", "cn": "右边翼卫"},
    "MF": {"en": "Midfielder", "cn": "中场"},
    "CM": {"en": "Central Midfielder", "cn": "中前卫"},
    "CDM": {"en": "Defensive Midfielder", "cn": "后腰"},
    "CAM": {"en": "Attacking Midfielder", "cn": "前腰"},
    "LM": {"en": "Left Midfielder", "cn": "左前卫"},
    "RM": {"en": "Right Midfielder", "cn": "右前卫"},
    "FW": {"en": "Forward", "cn": "前锋"},
    "ST": {"en": "Striker", "cn": "中锋"},
    "LW": {"en": "Left Winger", "cn": "左边锋"},
    "RW": {"en": "Right Winger", "cn": "右边锋"},
}

WIKI_POS_TO_CODE = {
    "GK": "GK", "DF": "CB", "CB": "CB", "LB": "LB", "RB": "RB",
    "LWB": "LWB", "RWB": "RWB", "MF": "CM", "CM": "CM", "CDM": "CDM",
    "CAM": "CAM", "LM": "LM", "RM": "RM", "FW": "ST", "ST": "ST",
    "LW": "LW", "RW": "RW",
}

SKIP = {"Contents", "See also", "References", "External links", "Notes",
        "Overview", "Navigation", "Coach representation by country"}


class SquadService:

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.teams_dir = self.data_dir / "teams"
        self.teams_dir.mkdir(parents=True, exist_ok=True)

    def fetch_all_squads(self) -> Dict[str, List[dict]]:
        """从 Wikipedia 抓取全部48强大名单"""
        resp = httpx.get(WIKI_URL, timeout=30, headers=HEADERS)
        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code}")
            return {}
        html = resp.text

        all_squads = OrderedDict()

        # 找出所有 h3 标签（= 国家队名）及其之后的表格
        h3_matches = list(re.finditer(
            r'<h3[^>]*>\s*<span[^>]*>(.*?)</span>\s*</h3>', html, re.DOTALL
        ))

        if not h3_matches:
            # fallback: 找没有 span 的 h3
            h3_matches = list(re.finditer(
                r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL
            ))

        for i, match in enumerate(h3_matches):
            country = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            if self._should_skip(country):
                continue

            # 找这个 h3 到下一个 h3 (或页面结束) 之间的第一个 table
            start = match.end()
            end = h3_matches[i + 1].start() if i + 1 < len(h3_matches) else len(html)
            section = html[start:end]

            table_match = re.search(r'<table[^>]*class="wikitable[^"]*"[^>]*>(.*?)</table>', section, re.DOTALL)
            if not table_match:
                table_match = re.search(r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>(.*?)</table>', section, re.DOTALL)
            if not table_match:
                continue

            table_html = table_match.group(0)
            players = self._parse_table_html(table_html)
            if players:
                all_squads[country] = players
                print(f"  {country}: {len(players)} players")

        return all_squads

    def _should_skip(self, text: str) -> bool:
        text_lower = text.lower().strip()
        for s in SKIP:
            if s.lower() in text_lower:
                return True
        if text_lower.startswith("group "):
            return True
        return len(text) > 35

    def _parse_table_html(self, table_html: str) -> List[dict]:
        """把一段 wikitable HTML 解析成球员列表"""
        soup = BeautifulSoup(table_html, 'html.parser')

        # 取第一个 table（就是 wikitable 本身）
        if soup.name == 'table':
            table = soup
        else:
            table = soup.find('table')
        if not table:
            return []

        rows = table.find_all('tr')
        if not rows:
            return []

        # 尝试找到数据的第一行（跳过表头）
        header_row = None
        data_start = 0
        for i, row in enumerate(rows):
            th_cells = row.find_all('th')
            td_cells = row.find_all('td')
            if th_cells and len(th_cells) >= 3:
                header_row = row
                data_start = i + 1
                break

        if header_row is None:
            data_start = 0

        # 解析表头
        col_map = self._parse_header_row(header_row)

        # 解析数据行
        players = []
        for i in range(data_start, len(rows)):
            row = rows[i]
            cells = row.find_all(['th', 'td'])
            if len(cells) < 3:
                continue

            player = self._parse_player_row(cells, col_map)
            if player:
                players.append(player)

        return players

    def _parse_header_row(self, header_row) -> Dict[str, int]:
        """确定列索引"""
        col_map = {}
        if header_row is None:
            return {'number': 0, 'position': 1, 'player': 2, 'club': 6}

        cells = header_row.find_all('th')
        if len(cells) < 2:
            # 检查 td
            cells = header_row.find_all('td')

        for idx, cell in enumerate(cells):
            text = cell.get_text(strip=True).lower()
            text = re.sub(r'<[^>]+>', '', text)
            if text in ('no.', '№', '#', 'no'):
                col_map['number'] = idx
            elif 'pos' in text and 'player' not in text:
                col_map['position'] = idx
            elif 'player' in text or 'name' in text:
                col_map['player'] = idx
            elif 'club' in text or 'team' in text:
                col_map['club'] = idx
            elif 'date' in text or 'age' in text or 'born' in text:
                col_map['age'] = idx
            elif 'caps' in text:
                col_map['caps'] = idx
            elif 'goal' in text:
                col_map['goals'] = idx

        return col_map

    def _parse_player_row(self, cells, col_map: Dict[str, int]) -> Optional[dict]:
        """解析单个球员行"""
        def get_cell(n: int) -> str:
            if n >= len(cells) or n is None:
                return ""
            return cells[n].get_text(strip=True)

        # 用默认索引作为后备
        player_idx = col_map.get('player', 2)
        name = get_cell(player_idx)

        if not name or len(name) < 2:
            return None

        # 跳过非球员行
        if name.lower() in ('player', 'name', 'head coach', 'manager', 'coach'):
            return None
        if any(kw in name.lower() for kw in ('total', 'manager', 'coach')):
            return None

        # 清理名字
        clean_name = re.sub(r'\[.*?\]', '', name)
        clean_name = re.sub(r'\s*\(c\)', '', clean_name, flags=re.IGNORECASE).strip()
        clean_name = re.sub(r'\s*\(captain\)', '', clean_name, flags=re.IGNORECASE).strip()
        clean_name = re.sub(r'\s*\(vice-captain\)', '', clean_name, flags=re.IGNORECASE).strip()

        if len(clean_name) < 2:
            return None

        number_str = get_cell(col_map.get('number', 0))
        number = int(number_str) if number_str.isdigit() else 0

        wiki_pos = get_cell(col_map.get('position', 1))
        pos_code = self._normalize_position(wiki_pos)

        club_idx = col_map.get('club', 6)
        if club_idx is None:
            club_idx = -1
        club = get_cell(club_idx)
        club = re.sub(r'\[.*?\]', '', club).strip()

        return {
            "id": self._make_player_id(clean_name),
            "name": clean_name,
            "position": pos_code,
            "position_display": POSITION_MAP.get(pos_code, {}).get("cn", wiki_pos),
            "number": number,
            "club": club,
            "age": 0,
            "national_caps": 0,
            "national_goals": 0,
        }

    def _normalize_position(self, wiki_pos: str) -> str:
        wiki_pos = wiki_pos.upper().strip()
        # 去掉数字前缀 (如 "1GK" → "GK", "4FW" → "FW")
        wiki_pos = re.sub(r'^\d+', '', wiki_pos)
        wiki_pos = wiki_pos.replace("(", "").replace(")", "")
        wiki_pos = wiki_pos.split("/")[0].strip()
        return WIKI_POS_TO_CODE.get(wiki_pos, wiki_pos)

    def _make_player_id(self, name: str) -> str:
        return re.sub(r'[^a-z0-9]', '-', name.lower()).strip('-')

    def save_squads(self, squads: Dict[str, List[dict]]):
        for country, players in squads.items():
            team_dir = self.teams_dir / country
            team_dir.mkdir(parents=True, exist_ok=True)

            filepath = team_dir / "squad.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "team": country,
                    "player_count": len(players),
                    "players": players,
                }, f, ensure_ascii=False, indent=2)

        index = {country: len(players) for country, players in squads.items()}
        index_path = self.teams_dir / "_index.json"
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({"teams": index, "total_teams": len(index)}, f, ensure_ascii=False, indent=2)

    def load_squads(self) -> Dict[str, List[dict]]:
        index_path = self.teams_dir / "_index.json"
        if not index_path.exists():
            return {}
        with open(index_path, "r", encoding="utf-8") as f:
            index_data = json.load(f)
        squads = {}
        for country in index_data.get("teams", {}):
            filepath = self.teams_dir / country / "squad.json"
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    squad_data = json.load(f)
                    squads[country] = squad_data.get("players", [])
        return squads

    def get_team_squad(self, country: str) -> List[dict]:
        filepath = self.teams_dir / country / "squad.json"
        if not filepath.exists():
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f).get("players", [])


squad_service = SquadService()


if __name__ == "__main__":
    print("=== Fetching 2026 World Cup Squads ===")
    service = SquadService()
    squads = service.fetch_all_squads()
    if squads:
        service.save_squads(squads)
        print(f"\nTotal: {len(squads)} teams")
        for country, players in list(squads.items())[:10]:
            print(f"  {country}: {len(players)} players")
