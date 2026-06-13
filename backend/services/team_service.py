"""
Team data service - read from local data files with caching.
"""
import json
from pathlib import Path
from typing import Optional, List, Dict
from functools import lru_cache

DATA_DIR = Path(__file__).parent.parent / "data" / "teams"


class TeamService:
    def __init__(self):
        self._teams_cache: Optional[List[Dict]] = None

    def _load_all_teams(self) -> List[Dict]:
        if self._teams_cache is None:
            path = DATA_DIR / "all_teams.json"
            with open(path, "r", encoding="utf-8") as f:
                self._teams_cache = json.load(f)
        return self._teams_cache

    def get_all_teams(
        self,
        confederation: Optional[str] = None,
        group: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[Dict]:
        teams = self._load_all_teams()

        if confederation:
            teams = [t for t in teams if t["confederation"] == confederation.upper()]

        if group:
            teams = [t for t in teams if t["group"] == group.upper()]

        if search:
            q = search.lower()
            teams = [
                t for t in teams
                if q in t["team_en"].lower() or q in t["team_cn"].lower()
            ]

        if sort_by == "win_rate" and any("stats" in t and t["stats"]["total_matches"] > 0 for t in teams):
            teams = sorted(teams, key=lambda t: t["stats"]["wins"] / max(t["stats"]["total_matches"], 1), reverse=True)
        elif sort_by == "matches":
            teams = sorted(teams, key=lambda t: t.get("total_matches_20y", 0), reverse=True)
        elif sort_by == "name":
            teams = sorted(teams, key=lambda t: t["team_cn"])

        return teams

    def get_team_detail(self, team_name: str) -> Optional[Dict]:
        team_dir = DATA_DIR / team_name
        info_path = team_dir / "team_info.json"
        if not info_path.exists():
            return None
        with open(info_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Load player squad if available
        squad_path = team_dir / "player_squad.json"
        if squad_path.exists():
            with open(squad_path, "r", encoding="utf-8") as f:
                data["player_squad"] = json.load(f)
        else:
            data["player_squad"] = None

        return data

    def get_team_matches(
        self,
        team_name: str,
        limit: int = 50,
        tournament: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[Dict]:
        team_dir = DATA_DIR / team_name
        matches_path = team_dir / "match_history.json"
        if not matches_path.exists():
            return []

        with open(matches_path, "r", encoding="utf-8") as f:
            matches = json.load(f)

        if tournament:
            matches = [m for m in matches if m["tournament"] == tournament]

        if year_from:
            matches = [m for m in matches if int(m["date"][:4]) >= year_from]

        if year_to:
            matches = [m for m in matches if int(m["date"][:4]) <= year_to]

        return matches[:limit]

    def get_confederations(self) -> List[Dict]:
        teams = self._load_all_teams()
        confs = {}
        for t in teams:
            c = t["confederation"]
            if c not in confs:
                confs[c] = {"name": c, "count": 0}
            confs[c]["count"] += 1
        return list(confs.values())

    def get_groups(self) -> List[str]:
        teams = self._load_all_teams()
        groups = sorted(set(t["group"] for t in teams))
        return groups

    def get_team_players(self, team_name: str) -> Optional[Dict]:
        """获取球队球员列表（含赛季统计数据）— 桌面数据优先 + Sofascore补充"""
        players_data = None

        # 1. 加载 players.json（Sofascore/FPL 赛季数据）
        players_path = DATA_DIR / team_name / "players.json"
        if players_path.exists():
            with open(players_path, "r", encoding="utf-8") as f:
                players_data = json.load(f)

        # 2. 回退到 squad.json / player_squad.json
        if players_data is None:
            squad_wiki_path = DATA_DIR / team_name / "squad.json"
            if squad_wiki_path.exists():
                with open(squad_wiki_path, "r", encoding="utf-8") as f:
                    players_data = json.load(f)
                # Ensure players_data has a "players" key
                if "players" not in players_data and "squad" in players_data:
                    players_data = {"team": team_name, "total_players": len(players_data["squad"]), "players": players_data["squad"]}

        if players_data is None:
            squad_path = DATA_DIR / team_name / "player_squad.json"
            if squad_path.exists():
                with open(squad_path, "r", encoding="utf-8") as f:
                    squad_data = json.load(f)
                players = []
                for pos_group in ["goalkeepers", "defenders", "midfielders", "forwards"]:
                    for p in squad_data.get(pos_group, []):
                        players.append({
                            "id": p.get("name", "").lower().replace(" ", "-"),
                            "name": p["name"],
                            "club": p.get("club", ""),
                            "position": pos_group,
                            "national_caps": p.get("caps", 0),
                            "stats": None,
                        })
                players_data = {"team": team_name, "total_players": len(players), "players": players}

        if players_data is None:
            return None

        # 3. 加载桌面数据并合并（跳过已导入的，import_desktop_data.py 已合并过）
        try:
            from .desktop_stats_service import desktop_stats_service
            desktop_stats_loaded = False
            desktop_stats = {}

            for player in players_data.get("players", []):
                existing_stats = player.get("stats")

                # 已从桌面导入过，跳过运行时合并
                if existing_stats and existing_stats.get("data_source") == "desktop" and existing_stats.get("has_real_data"):
                    continue

                if not desktop_stats_loaded:
                    desktop_stats = desktop_stats_service.get_team_players_stats(team_name) or {}
                    desktop_stats_loaded = True

                player_name = player.get("name", "")
                desktop_stat = self._match_desktop_player(player_name, desktop_stats)

                if desktop_stat:
                    # Desktop data as base
                    merged = dict(desktop_stat)
                    merged["data_source"] = "desktop"
                    merged["has_real_data"] = True

                    # Supplement with Sofascore advanced metrics
                    if existing_stats:
                        merged["rating"] = existing_stats.get("rating")
                        merged["xg"] = existing_stats.get("xg")
                        merged["pass_accuracy"] = existing_stats.get("pass_accuracy")
                        merged["key_passes"] = existing_stats.get("key_passes")
                        merged["progressive_passes"] = existing_stats.get("progressive_passes")
                        merged["dribble_success_rate"] = existing_stats.get("dribble_success_rate")
                        merged["match_confidence"] = existing_stats.get("match_confidence")
                        merged["_attributes"] = existing_stats.get("_attributes")
                    else:
                        merged["rating"] = None
                        merged["match_confidence"] = "high"

                    player["stats"] = merged
                elif existing_stats:
                    # No desktop data, use Sofascore
                    existing_stats["data_source"] = existing_stats.get("data_source", "sofascore")
                    existing_stats["has_real_data"] = existing_stats.get("match_confidence") in ("medium", "high")
                else:
                    # No data at all
                    player["stats"] = {
                        "data_source": "none",
                        "has_real_data": False,
                    }
        except ImportError:
            pass  # Desktop data not available, use existing data as-is

        return players_data

    def _match_desktop_player(self, player_name: str, desktop_stats: dict) -> dict:
        """Match a player by name to desktop stats using fuzzy matching."""
        if not desktop_stats:
            return None
        # Direct match
        if player_name in desktop_stats:
            return desktop_stats[player_name]
        # Case-insensitive
        for dname, dstats in desktop_stats.items():
            if dname.lower() == player_name.lower():
                return dstats
        # Diacritic-insensitive
        import unicodedata
        def strip_diacritics(s):
            return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
        pkey = strip_diacritics(player_name)
        for dname, dstats in desktop_stats.items():
            if strip_diacritics(dname) == pkey:
                return dstats
        # Contains match (for short names)
        for dname, dstats in desktop_stats.items():
            dkey = strip_diacritics(dname).replace(" ", "")
            if len(dkey) >= 8 and dkey in pkey.replace(" ", ""):
                return dstats
        return None

    def get_player_detail(self, team_name: str, player_name: str) -> Optional[Dict]:
        """获取单个球员详细信息"""
        team_players = self.get_team_players(team_name)
        if not team_players:
            return None

        for p in team_players.get("players", []):
            if p["name"].lower() == player_name.lower():
                return {
                    "player": p,
                    "team": team_name,
                }
        return None

    def get_all_teams_index(self) -> Dict:
        """获取所有球队的球员数据索引"""
        index_path = DATA_DIR / "_index.json"
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"teams": {}, "total_teams": 0}


team_service = TeamService()
