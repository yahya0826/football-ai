"""
多源球员数据汇聚服务 v2.0
- datafc (Sofascore): 19 个联赛, 2025-26 赛季, 30 个统计字段 (主力)
- FPL API: 英超积分数据 (辅助)
- 统一输出: UnifiedPlayerStats → players.json
"""
import re
import json
import math
import httpx
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

try:
    from datafc import league_player_stats_data
    from datafc.exceptions import DataNotAvailableError
    HAS_DATFC = True
except ImportError:
    HAS_DATFC = False

from .unified_schema import (
    UnifiedPlayerStats, UnifiedSchemaEngine, engine,
    DataSource, Confidence,
)

FPL_API = "https://fantasy.premierleague.com/api/bootstrap-static/"

# 2025-26 赛季联赛配置: (sofascore_tournament_id, season_id, label)
SOFASCORE_LEAGUES = [
    (17, 76986, "Premier League"),
    (8, 77559, "La Liga"),
    (35, 77333, "Bundesliga"),
    (23, 76457, "Serie A"),
    (34, 77356, "Ligue 1"),
    (37, 77012, "Eredivisie"),
    (238, 77806, "Primeira Liga"),
    (955, 80443, "Saudi Pro League"),
    (52, 77805, "Super Lig"),
    (38, 77040, "Belgian Pro League"),
    (36, 77128, "Scottish Premiership"),
    (242, 86668, "MLS"),
    (325, 87678, "Brasileirao"),
    (196, 87931, "J1 League"),
    (825, 77227, "Qatar Stars League"),
    (44, 77354, "2. Bundesliga"),
    (182, 77357, "Ligue 2"),
    (53, 79502, "Serie B"),
    (11620, 87699, "Liga MX"),
    # (45, 77382, "Austrian Bundesliga"),  # optional
]


class PlayerDataService:
    """多源球员数据服务 v2.0"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.fpl_index: Dict[str, dict] = {}
        self.sofascore_index: Dict[str, list] = {}  # name -> list of entries

    # ═══════════════════════════════════════════════════════
    # DATA FETCHING
    # ═══════════════════════════════════════════════════════

    def fetch_all_sofascore(self) -> Dict[str, dict]:
        """从 Sofascore 拉取所有配置联赛的球员数据，返回标准化名索引"""
        if not HAS_DATFC:
            print("  datafc not installed, skipping Sofascore")
            return {}

        index = defaultdict(list)
        total = 0
        league_counts = {}

        for tid, sid, name in SOFASCORE_LEAGUES:
            league_total = 0
            seen_ids = set()

            # Fetch by position group to get full coverage (datafc limits 100 per call)
            for pos_code in ['G', 'D', 'M', 'F']:
                try:
                    df = league_player_stats_data(
                        tournament_id=tid, season_id=sid,
                        max_players=999, position=pos_code,
                        order="-appearances",
                    )
                    for _, row in df.iterrows():
                        raw = row.to_dict()
                        pid = raw.get("player_id")
                        if pid in seen_ids:
                            continue
                        seen_ids.add(pid)

                        norm = self._normalize_name(raw.get("player_name", ""))
                        if not norm or len(norm) < 2:
                            continue
                        raw["league"] = name
                        team = self._normalize_name(str(raw.get("team_name", "")))
                        raw["team_norm"] = team

                        existing = index[norm]
                        dup = [e for e in existing if e.get("team_norm") == team]
                        if dup:
                            if dup[0].get("rating", 0) >= raw.get("rating", 0):
                                continue
                            existing.remove(dup[0])
                        index[norm].append(raw)
                        league_total += 1
                except DataNotAvailableError:
                    pass
                except Exception as e:
                    print(f"  [WARN] {name}/{pos_code}: {e}")

            league_counts[name] = league_total
            total += league_total

        self.sofascore_index = dict(index)
        top5 = sorted(league_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"  Sofascore: {total} entries ({len(index)} unique names) from {len(SOFASCORE_LEAGUES)} leagues")
        print(f"  Top 5: {', '.join(f'{n}({c})' for n, c in top5)}")

        # Flatten: keep only the best entry per name+team combo
        self.sofascore_index = dict(index)
        print(f"  Sofascore: {total} entries ({len(index)} unique names) from {len(SOFASCORE_LEAGUES)} leagues")
        return self.sofascore_index

    def fetch_fpl_data(self) -> Dict[str, dict]:
        """从 FPL API 获取英超球员数据，返回标准化名索引"""
        try:
            resp = httpx.get(FPL_API, timeout=30)
            if resp.status_code != 200:
                print(f"  FPL API returned {resp.status_code}")
                return {}
            data = resp.json()
        except Exception as e:
            print(f"  FPL API error: {e}")
            return {}

        teams = {t["id"]: t["name"] for t in data.get("teams", [])}
        pos_map = {1: "GK", 2: "CB", 3: "CM", 4: "ST"}
        index = {}

        for p in data.get("elements", []):
            full_name = f"{p['first_name']} {p['second_name']}".strip()
            norm = self._normalize_name(full_name)
            if not norm:
                continue
            index[norm] = {
                "full_name": full_name,
                "club": teams.get(p.get("team", 0), ""),
                "position": pos_map.get(p.get("element_type", 0), "CM"),
                "starts": p.get("starts", 0),
                "minutes": p.get("minutes", 0),
                "goals_scored": p.get("goals_scored", 0),
                "assists": p.get("assists", 0),
                "expected_goals": float(p.get("expected_goals", 0)),
                "expected_assists": float(p.get("expected_assists", 0)),
                "yellow_cards": p.get("yellow_cards", 0),
                "red_cards": p.get("red_cards", 0),
                "total_points": p.get("total_points", 0),
                "form": p.get("form", 0),
                "saves": p.get("saves", 0),
                "bonus": p.get("bonus", 0),
                "bps": p.get("bps", 0),
                "ict_index": p.get("ict_index", 0),
                "expected_goals_per_90": float(p.get("expected_goals_per_90", 0)) if "expected_goals_per_90" in p else 0,
                "league": "Premier League",
            }

        self.fpl_index = index
        print(f"  FPL: {len(index)} players indexed")
        return index

    # ═══════════════════════════════════════════════════════
    # MATCHING & ENRICHING
    # ═══════════════════════════════════════════════════════

    def match_and_enrich(self, squads: Dict[str, List[dict]]) -> Dict[str, List[dict]]:
        """主流程：匹配并增强所有球队的球员数据"""
        print("Fetching Sofascore data (19 leagues)...")
        self.fetch_all_sofascore()

        print("Fetching FPL data...")
        self.fetch_fpl_data()

        enriched = {}
        total_with_data = 0
        total_players = 0
        sources_breakdown = defaultdict(int)

        for country, players in squads.items():
            enriched_players = []
            for p in players:
                total_players += 1
                stats, source_label = self._match_player(p)
                if stats:
                    total_with_data += 1
                    sources_breakdown[source_label] += 1

                enriched_players.append({
                    **p,
                    "stats": stats,
                })
            enriched[country] = enriched_players

        print(f"\n  Matched: {total_with_data}/{total_players} players ({total_with_data/total_players*100:.1f}%)")
        for src, count in sorted(sources_breakdown.items()):
            print(f"    {src}: {count}")
        return enriched

    def _match_player(self, player: dict) -> tuple:
        """匹配单个球员到最佳数据源，返回 (api_dict, source_label)"""
        name = self._normalize_name(player.get("name", ""))
        club = player.get("club", "").strip()
        position = player.get("position", "CM")

        sofascore_raw = None
        fpl_raw = None

        # Sofascore match (multi-entry index)
        s_entries = self.sofascore_index.get(name, [])
        if s_entries:
            sofascore_raw = self._pick_best_entry(s_entries, name, club)
        if not sofascore_raw:
            sofascore_raw = self._fuzzy_match_multi(name, self.sofascore_index, club)

        # FPL match (single-entry index)
        if name in self.fpl_index:
            fpl_raw = self.fpl_index[name]
        else:
            fpl_raw = self._fuzzy_match(name, self.fpl_index, club)

        # 转换 + 合并
        sofascore_stats = None
        fpl_stats = None

        if sofascore_raw:
            sofascore_stats = engine.convert_from_sofascore(sofascore_raw, position, club)
        if fpl_raw:
            fpl_stats = engine.convert_from_fpl(fpl_raw, position, club)

        if sofascore_stats and fpl_stats:
            # 双源合并
            sources = {}
            if sofascore_stats.confidence != Confidence.NONE:
                sources[DataSource.SOFASCORE] = sofascore_stats
            if fpl_stats.confidence != Confidence.NONE:
                sources[DataSource.FPL] = fpl_stats
            if sources:
                merged = engine.merge(sources, position)
                return engine.to_api_dict(merged), "Sofascore+FPL"
            return None, "none"

        if sofascore_stats and sofascore_stats.confidence != Confidence.NONE:
            return engine.to_api_dict(sofascore_stats), "Sofascore"

        if fpl_stats and fpl_stats.confidence != Confidence.NONE:
            return engine.to_api_dict(fpl_stats), "FPL"

        return None, "none"

    # ═══════════════════════════════════════════════════════
    # NAME MATCHING UTILITIES
    # ═══════════════════════════════════════════════════════

    def _pick_best_entry(self, entries: List[dict], name: str, club: str) -> Optional[dict]:
        """从多个同名条目中选出最佳匹配"""
        if len(entries) == 1:
            e = entries[0]
            # 如果用俱乐部匹配，确认一致
            if club and not self._club_match(club, str(e.get("team_name", ""))):
                return None
            return e

        # 优先俱乐部匹配
        if club:
            club_matches = [e for e in entries if self._club_match(club, str(e.get("team_name", "")))]
            if len(club_matches) == 1:
                return club_matches[0]
            if club_matches:
                return max(club_matches, key=lambda e: e.get("rating", 0))

        # 否则取评分最高的
        return max(entries, key=lambda e: e.get("rating", 0))

    def _fuzzy_match_multi(self, name: str, index: Dict[str, list], club: str) -> Optional[dict]:
        """对多条目索引的模糊匹配"""
        parts = name.split()
        if len(parts) < 2:
            return None

        last = parts[-1]
        first3 = parts[0][:3] if parts[0] else ""

        candidates = []
        for idx_name, entries in index.items():
            idx_parts = idx_name.split()
            if not idx_parts:
                continue
            if idx_parts[-1] == last and idx_parts[0][:3] == first3:
                candidates.extend(entries)

        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]

        # 俱乐部二次过滤
        if club:
            filtered = [c for c in candidates if self._club_match(club, str(c.get("team_name", "")))]
            if len(filtered) == 1:
                return filtered[0]
            if filtered:
                return max(filtered, key=lambda e: e.get("rating", 0))

        return max(candidates, key=lambda e: e.get("rating", 0))

    def _fuzzy_match(self, name: str, index: Dict[str, dict], club: str) -> Optional[dict]:
        """两级模糊匹配：姓氏 + 名首字符"""
        parts = name.split()
        if len(parts) < 2:
            return None

        last = parts[-1]
        first3 = parts[0][:3] if parts[0] else ""

        candidates = []
        for idx_name, data in index.items():
            idx_parts = idx_name.split()
            if not idx_parts:
                continue
            if idx_parts[-1] == last:
                if first3 and idx_parts[0][:3] == first3:
                    candidates.append(data)

        if len(candidates) == 1:
            return candidates[0]

        # 用俱乐部二次过滤
        if club and len(candidates) > 1:
            club_filtered = [c for c in candidates if self._club_match(club, c.get("club", ""))]
            if len(club_filtered) == 1:
                return club_filtered[0]

        return None

    @staticmethod
    def _club_match(club1: str, club2: str) -> bool:
        if not club1 or not club2:
            return False
        c1 = club1.lower().strip()
        c2 = (club2.get("club", str(club2)) if isinstance(club2, dict) else str(club2)).lower().strip()
        if not c2:
            return False
        if c1 == c2:
            return True
        if c1 in c2 or c2 in c1:
            return True
        aliases = {
            "man city": "manchester city", "man utd": "manchester united",
            "psg": "paris saint-germain", "bayern": "bayern munich",
            "leverkusen": "bayer leverkusen", "dortmund": "borussia dortmund",
            "inter": "inter milan", "milan": "ac milan",
            "atletico madrid": "atlético madrid", "besiktas": "beşiktaş",
            "fenerbahce": "fenerbahçe",
        }
        for alias, full in aliases.items():
            if alias in c1 or alias in c2:
                if full in c1 or full in c2:
                    return True
        return False

    @staticmethod
    def _normalize_name(name: str) -> str:
        name = name.lower().strip()
        name = re.sub(r'[^a-z\s]', '', name)
        name = re.sub(r'\s+', ' ', name)
        return name.strip()

    # ═══════════════════════════════════════════════════════
    # SAVE
    # ═══════════════════════════════════════════════════════

    def save_all(self, enriched: Dict[str, List[dict]], teams_dir: Path):
        for country, players in enriched.items():
            team_dir = teams_dir / country
            team_dir.mkdir(parents=True, exist_ok=True)

            matched = sum(1 for p in players if p.get("stats"))
            filepath = team_dir / "players.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "team": country,
                    "total_players": len(players),
                    "matched_count": matched,
                    "players": players,
                }, f, ensure_ascii=False, indent=2)


player_data_service = PlayerDataService()
