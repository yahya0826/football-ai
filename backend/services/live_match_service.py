"""
Live Match Service - ESPN public API integration for real-time match data.

Provides:
  - Live scoreboard (all matches in progress / today)
  - Per-match detail: score, events timeline (goals, cards, substitutions),
    team statistics (possession, shots, corners, fouls, etc.)
  - In-memory caching with configurable TTL
  - Chinese translation layer for events, stats, status
  - JSON file persistence for historical match data

Source: site.api.espn.com/apis/site/v2/sports/soccer/fifa.world
- No API key, no auth, no rate limits observed.
- Cached to avoid redundant requests from multiple frontend users.
"""

import json
import re
import time
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import requests

logger = logging.getLogger(__name__)

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world"
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "live_matches"

# Map ESPN detailed position codes to G/D/M/F groups
_POSITION_GROUP: Dict[str, str] = {
    # Goalkeeper
    "G": "G", "GK": "G",
    # Defender
    "D": "D", "DF": "D", "CD": "D", "CB": "D", "RB": "D", "LB": "D",
    "RWB": "D", "LWB": "D", "SW": "D",
    # Midfielder
    "M": "M", "MF": "M", "CM": "M", "CDM": "M", "CAM": "M",
    "DM": "M", "AM": "M", "RM": "M", "LM": "M",
    # Forward
    "F": "F", "FW": "F", "CF": "F", "ST": "F", "LW": "F", "RW": "F",
    "RF": "F", "LF": "F",
}


def _normalize_position(abbr: str) -> str:
    """Normalize ESPN position abbreviation to G/D/M/F group."""
    if not abbr:
        return "U"
    base = abbr.split("-")[0]  # "CF-L" → "CF"
    return _POSITION_GROUP.get(base, "U")

# Cache TTLs in seconds
SCOREBOARD_TTL = 15
MATCH_DETAIL_TTL = 30
ROSTER_TTL = 300

# ── Event type mapping for ESPN type IDs ──────────────────────
EVENT_TYPE_MAP: Dict[str, str] = {
    "29": "goal",
    "77": "goal",
    "94": "yellow_card",
    "95": "yellow_card",
    "96": "red_card",
    "97": "red_card",
    "76": "substitution",
    "80": "kickoff",
    "81": "halftime",
    "82": "fulltime",
}

# ── Chinese translation maps ──────────────────────────────────

STAT_LABELS_CN: Dict[str, str] = {
    "possessionPct": "控球率",
    "totalShots": "总射门",
    "shotsOnTarget": "射正",
    "shotPct": "射正率",
    "wonCorners": "角球",
    "foulsCommitted": "犯规",
    "yellowCards": "黄牌",
    "redCards": "红牌",
    "offsides": "越位",
    "saves": "扑救",
    "totalPasses": "传球",
    "accuratePasses": "精准传球",
    "passingPct": "传球成功率",
    "passPct": "传球成功率",
    "totalCrosses": "传中",
    "accurateCrosses": "精准传中",
    "crossPct": "传中成功率",
    "totalLongBalls": "长传",
    "accurateLongBalls": "精准长传",
    "longballPct": "长传成功率",
    "blockedShots": "封堵射门",
    "totalTackles": "抢断",
    "effectiveTackles": "有效抢断",
    "tacklePct": "抢断成功率",
    "interceptions": "拦截",
    "effectiveClearance": "有效解围",
    "totalClearance": "解围",
    "penaltyKickGoals": "点球进球",
    "penaltyKickShots": "点球次数",
}

EVENT_TYPE_CN: Dict[str, str] = {
    "goal": "进球",
    "yellow_card": "黄牌",
    "red_card": "红牌",
    "substitution": "换人",
    "kickoff": "开球",
    "halftime": "中场休息",
    "fulltime": "全场结束",
}

STATUS_CN: Dict[str, str] = {
    "live": "进行中",
    "halftime": "中场休息",
    "finished": "已结束",
    "scheduled": "未开始",
}

# Team name EN → CN mapping (from schedule data)
TEAM_NAMES_CN: Dict[str, str] = {
    "England": "英格兰", "France": "法国", "Croatia": "克罗地亚", "Norway": "挪威",
    "Portugal": "葡萄牙", "Germany": "德国", "Netherlands": "荷兰", "Switzerland": "瑞士",
    "Scotland": "苏格兰", "Spain": "西班牙", "Austria": "奥地利", "Belgium": "比利时",
    "Bosnia and Herzegovina": "波黑", "Bosnia-Herzegovina": "波黑", "Sweden": "瑞典",
    "Turkey": "土耳其", "Türkiye": "土耳其", "Czech Republic": "捷克", "Czechia": "捷克",
    "Argentina": "阿根廷", "Brazil": "巴西", "Colombia": "哥伦比亚", "Ecuador": "厄瓜多尔",
    "Paraguay": "巴拉圭", "Uruguay": "乌拉圭",
    "Australia": "澳大利亚", "Iran": "伊朗", "Japan": "日本", "Jordan": "约旦",
    "Uzbekistan": "乌兹别克斯坦", "Qatar": "卡塔尔", "Saudi Arabia": "沙特阿拉伯",
    "South Korea": "韩国", "Iraq": "伊拉克",
    "Algeria": "阿尔及利亚", "Cape Verde": "佛得角", "DR Congo": "刚果民主共和国",
    "Egypt": "埃及", "Ghana": "加纳", "Ivory Coast": "科特迪瓦", "Morocco": "摩洛哥",
    "Senegal": "塞内加尔", "South Africa": "南非", "Tunisia": "突尼斯",
    "United States": "美国", "Mexico": "墨西哥", "Canada": "加拿大",
    "Panama": "巴拿马", "Haiti": "海地", "Curaçao": "库拉索", "New Zealand": "新西兰",
}

# ESPN display name -> schedule name overrides
ESPN_NAME_OVERRIDE: Dict[str, str] = {
    "Türkiye": "Turkey",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Czechia": "Czech Republic",
}


@dataclass
class CacheEntry:
    data: Dict
    ts: float = field(default_factory=time.time)

    def expired(self, ttl: float) -> bool:
        return time.time() - self.ts > ttl


class LiveMatchService:
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ── public API ────────────────────────────────────────────

    def get_scoreboard(self, date: str = None) -> Dict:
        """Get matches from ESPN fifa.world scoreboard.
        When date is provided (YYYY-MM-DD), fetch matches for that date.
        Otherwise fetch live + recent + upcoming."""
        if date:
            # Convert to YYYYMMDD format for ESPN API
            date_str = date.replace("-", "")
            return self._cached(f"scoreboard_{date_str}", 3600, lambda: self._fetch_scoreboard(date_str))
        return self._cached("scoreboard", SCOREBOARD_TTL, self._fetch_scoreboard)

    def get_live_matches(self) -> List[Dict]:
        """Return only in-progress / halftime matches, enriched for the ticker."""
        sb = self.get_scoreboard()
        live = []
        for ev in sb.get("events", []):
            status = ev.get("status", {}).get("type", {})
            name = status.get("name", "STATUS_SCHEDULED")
            if name in ("STATUS_IN_PROGRESS", "STATUS_HALFTIME", "STATUS_END_OF_PERIOD"):
                live.append(self._simplify_match(ev))
        return live

    def get_today_matches(self, date: str = None) -> List[Dict]:
        """Return matches for a given date (all statuses). Merges ESPN scoreboard with local persisted data.
        When date is None, returns today's matches from default scoreboard."""
        sb = self.get_scoreboard(date)
        espn_ids = set()
        results = []
        for ev in sb.get("events", []):
            m = self._simplify_match(ev)
            espn_ids.add(m["match_id"])
            results.append(m)

        # Supplement with locally persisted matches not in ESPN scoreboard
        if not date:
            for local in self._scan_local_matches():
                if local["match_id"] not in espn_ids:
                    results.append(local)

        return results

    def get_match_detail(self, match_id: str) -> Optional[Dict]:
        """Get full match detail with Chinese labels. Checks local persistence first."""
        # Try local persistence first (for finished matches)
        local = self._load_local(match_id)
        if local and local.get("status", {}).get("state") == "finished":
            return local

        # Fetch from ESPN
        key = f"match_{match_id}"
        detail = self._cached(key, MATCH_DETAIL_TTL, lambda: self._fetch_match_detail(match_id))
        if detail:
            detail = self._add_chinese_labels(detail)
            # Persist to local file
            self._save_local(match_id, detail)
        elif local:
            # Fallback to stale local data if ESPN fetch fails
            return local
        return detail

    def _normalize_team(self, name: str) -> str:
        """Normalize team name for fuzzy matching."""
        n = name.lower()
        n = re.sub(r'\band\b', '', n)
        n = n.replace('&', '').replace('-', ' ').replace('.', '')
        return re.sub(r'\s+', ' ', n).strip()

    def find_match_by_teams(self, home_team: str, away_team: str, date: str = None) -> Optional[str]:
        """Find an ESPN match_id by matching home/away team names. Returns match_id or None.
        Searches ESPN scoreboard first (with date filter if provided), then falls back to locally persisted match files."""
        # Determine ESPN UTC date from schedule date (Beijing time = UTC+8, so -1 day)
        espn_date = None
        if date:
            from datetime import datetime, timedelta
            try:
                dt = datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)
                espn_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # Search ESPN scoreboard with date filter if available
        sb = self.get_scoreboard(espn_date)
        sb_simplified = [self._simplify_match(ev) for ev in sb.get("events", [])]
        result = self._search_events_by_teams(sb_simplified, home_team, away_team, date)
        if result:
            return result

        # Fallback: search local persisted match files
        local_matches = self._scan_local_matches()
        return self._search_events_by_teams(local_matches, home_team, away_team, date)

    def _search_events_by_teams(self, events: List[Dict], home_team: str, away_team: str, date: str = None) -> Optional[str]:
        """Search a list of simplified match events for matching team names."""
        h_norm = self._normalize_team(home_team)
        a_norm = self._normalize_team(away_team)
        for ev in events:
            h = self._normalize_team(ev.get("home_team", ""))
            a = self._normalize_team(ev.get("away_team", ""))
            # Skip events with empty team names (not yet populated)
            if not h or not a:
                continue
            ev_date = (ev.get("date", "") or "")[:10]
            if (h == h_norm or h_norm in h or h in h_norm) and (a == a_norm or a_norm in a or a in a_norm):
                if date and ev_date:
                    try:
                        d1 = datetime.strptime(date, "%Y-%m-%d")
                        d2 = datetime.strptime(ev_date, "%Y-%m-%d")
                        if abs((d1 - d2).days) > 1:
                            continue
                    except ValueError:
                        if ev_date != date:
                            continue
                return str(ev.get("match_id", ev.get("id", "")))
        return None

    def get_team_roster(self, team_id: str) -> Optional[Dict]:
        """Get full roster for a national team, with Chinese labels and position grouping.
        Uses local disk persistence as primary source, fetches from ESPN when stale."""
        # Try local persistence first
        local = self._load_roster(team_id)
        if local and not self._roster_stale(team_id):
            return local

        # Fetch from ESPN
        key = f"roster_{team_id}"
        raw = self._cached(key, ROSTER_TTL, lambda: self._fetch_roster(team_id))
        if raw:
            formatted = self._format_roster(raw)
            self._save_roster(team_id, formatted)
            return formatted

        # Fallback to stale local data
        if local:
            return local
        return None

    def _roster_stale(self, team_id: str) -> bool:
        path = DATA_DIR / f"roster_{team_id}.json"
        if not path.exists():
            return True
        age = time.time() - path.stat().st_mtime
        return age > ROSTER_TTL

    def _load_roster(self, team_id: str) -> Optional[Dict]:
        path = DATA_DIR / f"roster_{team_id}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to load local roster {team_id}: {e}")
            return None

    def _save_roster(self, team_id: str, data: Dict):
        path = DATA_DIR / f"roster_{team_id}.json"
        try:
            data["_saved_at"] = datetime.now().isoformat()
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save roster {team_id}: {e}")

    def _format_roster(self, raw: Dict) -> Dict:
        """Format raw ESPN roster into structured data with Chinese labels."""
        athletes = raw.get("athletes", [])

        # Group by position category
        position_groups = {"G": "门将", "D": "后卫", "M": "中场", "F": "前锋", "U": "未知"}
        grouped = {"G": [], "D": [], "M": [], "F": [], "U": []}

        for a in athletes:
            pos = a.get("position", {})
            abbr = pos.get("abbreviation", "")
            cat = _normalize_position(abbr)
            player = {
                "id": str(a.get("id", "")),
                "name": a.get("displayName", a.get("fullName", "")),
                "short_name": a.get("shortName", ""),
                "jersey": str(a.get("jersey", "")) if a.get("jersey") else "",
                "position": abbr,
                "position_name": pos.get("displayName", pos.get("name", "")),
                "headshot": a.get("headshot", {}).get("href", "") if isinstance(a.get("headshot"), dict) else "",
                "height": a.get("displayHeight", ""),
                "weight": a.get("displayWeight", ""),
                "age": a.get("age", 0),
            }
            grouped[cat].append(player)

        # Sort each group by jersey number
        for cat in grouped:
            grouped[cat].sort(key=lambda p: int(p["jersey"]) if p["jersey"].isdigit() else 999)

        # Coach
        coach_raw = raw.get("coach", [])
        coach_name = ""
        if isinstance(coach_raw, list) and len(coach_raw) > 0:
            c = coach_raw[0]
            coach_name = c.get("displayName", c.get("fullName", ""))

        # Team name
        team_info = raw.get("team", {})
        team_name = team_info.get("displayName", "")
        team_name_cn = self._team_cn(team_name)

        return {
            "team_id": team_info.get("id", ""),
            "team_name": team_name,
            "team_name_cn": team_name_cn,
            "coach": coach_name or f"{team_name_cn}主教练",
            "players": grouped,
            "total_players": len(athletes),
            "position_labels": position_groups,
        }

    # ── cache layer ───────────────────────────────────────────

    def _cached(self, key: str, ttl: float, fetcher):
        entry = self._cache.get(key)
        if entry and not entry.expired(ttl):
            return entry.data
        try:
            data = fetcher()
            if data:
                self._cache[key] = CacheEntry(data=data)
            return data
        except Exception as e:
            logger.warning(f"Live match fetch failed ({key}): {e}")
            if entry:
                return entry.data
            return None

    # ── local persistence ─────────────────────────────────────

    def _load_local(self, match_id: str) -> Optional[Dict]:
        path = DATA_DIR / f"{match_id}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to load local match {match_id}: {e}")
            return None

    def _save_local(self, match_id: str, data: Dict):
        path = DATA_DIR / f"{match_id}.json"
        try:
            data["_saved_at"] = datetime.now().isoformat()
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save local match {match_id}: {e}")

    # ── local match scanning ────────────────────────────────────

    def _scan_local_matches(self) -> List[Dict]:
        """Scan all persisted match files and return simplified summaries."""
        matches = []
        for path in sorted(DATA_DIR.glob("*.json")):
            name = path.stem
            if name.startswith("roster_"):
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                simplified = self._local_to_simplified(data)
                if simplified:
                    matches.append(simplified)
            except Exception as e:
                logger.warning(f"Failed to scan local match {name}: {e}")
        return matches

    def _local_to_simplified(self, local: Dict) -> Optional[Dict]:
        """Convert a locally persisted match detail into simplified scoreboard format."""
        status = local.get("status", {})
        home = local.get("home", {})
        away = local.get("away", {})
        state = status.get("state", "scheduled")

        home_name = ESPN_NAME_OVERRIDE.get(home.get("name", ""), home.get("name", ""))
        away_name = ESPN_NAME_OVERRIDE.get(away.get("name", ""), away.get("name", ""))

        return {
            "match_id": str(local.get("match_id", "")),
            "name": f"{home_name} vs {away_name}",
            "date": local.get("date", ""),
            "state": state,
            "state_cn": STATUS_CN.get(state, state),
            "status_detail": status.get("detail", ""),
            "period": status.get("period", 0),
            "clock": status.get("clock", ""),
            "home_team": home_name,
            "away_team": away_name,
            "home_team_cn": self._team_cn(home_name),
            "away_team_cn": self._team_cn(away_name),
            "home_team_id": home.get("team_id", ""),
            "away_team_id": away.get("team_id", ""),
            "home_score": int(home.get("score", 0) or 0),
            "away_score": int(away.get("score", 0) or 0),
            "venue": local.get("venue", ""),
            "broadcast": local.get("broadcast", ""),
        }

    # ── ESPN fetchers ─────────────────────────────────────────

    def _fetch_scoreboard(self, date_str: str = None) -> Dict:
        url = f"{ESPN_BASE}/scoreboard"
        if date_str:
            url += f"?dates={date_str}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()

    def _fetch_match_detail(self, match_id: str) -> Optional[Dict]:
        url = f"{ESPN_BASE}/summary?event={match_id}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        raw = r.json()
        return self._parse_match_detail(raw, match_id)

    def _fetch_roster(self, team_id: str) -> Optional[Dict]:
        url = f"{ESPN_BASE}/teams/{team_id}/roster"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()

    # ── Chinese translation layer ─────────────────────────────

    def _team_cn(self, name: str) -> str:
        return TEAM_NAMES_CN.get(name, name)

    def _add_chinese_labels(self, detail: Dict) -> Dict:
        """Add Chinese labels to all match detail fields."""
        # Status
        state = detail.get("status", {}).get("state", "")
        detail["status"]["state_cn"] = STATUS_CN.get(state, state)

        # Team names
        detail["home"]["name_cn"] = self._team_cn(detail["home"].get("name", ""))
        detail["away"]["name_cn"] = self._team_cn(detail["away"].get("name", ""))

        # Events - generate Chinese descriptions
        scores = {"home": 0, "away": 0}
        for ev in detail.get("events", []):
            ev["type_cn"] = EVENT_TYPE_CN.get(ev.get("type", ""), ev.get("type", ""))
            ev["team_cn"] = self._team_cn(ev.get("team", ""))
            ev["description_cn"] = self._generate_event_cn(ev, scores)

        # Statistics - add Chinese labels
        for side in ("home", "away"):
            stats = detail.get("statistics", {}).get(side, {}).get("stats", {})
            team_name = detail.get("statistics", {}).get(side, {}).get("team_name", "")
            detail["statistics"][side]["team_name_cn"] = self._team_cn(team_name)
            for key, val in stats.items():
                val["label_cn"] = STAT_LABELS_CN.get(key, val.get("label", key))

        return detail

    def _generate_event_cn(self, ev: Dict, scores: Dict[str, int]) -> str:
        """Generate Chinese description for a match event using structured data."""
        etype = ev.get("type", "")
        minute = ev.get("minute", "")
        team = ev.get("team_cn", ev.get("team", ""))
        player = ev.get("player", "")
        player_in = ev.get("player_in", "")
        player_out = ev.get("player_out", "")
        assist = ev.get("assist", "")

        if etype == "goal":
            # Track score
            side = "home" if team == ev.get("team_cn") else "away"
            # Find which side scored
            desc = f"{minute}' {player}"
            if assist:
                desc += f"，助攻 {assist}"
            desc += f" 为{team}进球！"
            return desc

        elif etype == "yellow_card":
            return f"{minute}' {player}（{team}）吃到黄牌 🟨"

        elif etype == "red_card":
            return f"{minute}' {player}（{team}）被红牌罚下 🟥"

        elif etype == "substitution":
            if player_in and player_out:
                return f"{minute}' {player_in} ↑ 替补登场，{player_out} ↓ 被换下"
            return f"{minute}' {team} 换人调整"

        elif etype == "halftime":
            return "中场休息 ⏸️"

        elif etype == "fulltime":
            return "全场比赛结束 🏁"

        elif etype == "kickoff":
            return "比赛开始！"

        # Fallback: return original text
        return ev.get("text", "")

    # ── parsing ───────────────────────────────────────────────

    def _simplify_match(self, event: Dict) -> Dict:
        """Extract minimal match info for scoreboard / ticker."""
        status = event.get("status", {}).get("type", {})
        comps = event.get("competitions", [])
        teams = {}
        scores = {}

        team_ids = {}
        for comp in comps:
            for team in comp.get("competitors", []):
                side = team.get("homeAway", "unknown")
                t = team.get("team", {})
                teams[side] = t.get("displayName", t.get("abbreviation", "?"))
                scores[side] = int(team.get("score", 0) or 0)
                team_ids[side] = str(t.get("id", ""))

        detail = status.get("detail", "")
        status_name = status.get("name", "STATUS_SCHEDULED")
        state = "scheduled"
        if status_name == "STATUS_IN_PROGRESS":
            state = "live"
        elif status_name == "STATUS_HALFTIME":
            state = "halftime"
        elif status_name == "STATUS_FULL_TIME":
            state = "finished"
        elif status_name == "STATUS_END_OF_PERIOD":
            state = "live"

        home_name = ESPN_NAME_OVERRIDE.get(teams.get("home", ""), teams.get("home", ""))
        away_name = ESPN_NAME_OVERRIDE.get(teams.get("away", ""), teams.get("away", ""))

        return {
            "match_id": str(event.get("id", "")),
            "name": event.get("name", ""),
            "date": event.get("date", ""),
            "state": state,
            "state_cn": STATUS_CN.get(state, state),
            "status_detail": detail,
            "period": status.get("period", 0),
            "clock": status.get("displayClock", detail),
            "home_team": home_name,
            "away_team": away_name,
            "home_team_cn": self._team_cn(home_name),
            "away_team_cn": self._team_cn(away_name),
            "home_team_id": team_ids.get("home", ""),
            "away_team_id": team_ids.get("away", ""),
            "home_score": scores.get("home", 0),
            "away_score": scores.get("away", 0),
            "venue": event.get("venue", {}).get("fullName", ""),
            "broadcast": comps[0].get("broadcasts", [{}])[0].get("names", [""])[0] if comps else "",
        }

    def _parse_match_detail(self, raw: Dict, match_id: str) -> Optional[Dict]:
        """Parse ESPN summary into clean events + stats structure."""
        header = raw.get("header", {})
        comps = header.get("competitions", [])

        teams_info = {}
        status_info = {}
        competition_id = ""
        for comp in comps:
            if not competition_id:
                competition_id = str(comp.get("id", ""))
            for team in comp.get("competitors", []):
                side = team.get("homeAway", "unknown")
                t = team.get("team", {})
                teams_info[side] = {
                    "name": t.get("displayName", t.get("abbreviation", "?")),
                    "abbrev": t.get("abbreviation", ""),
                    "logo": t.get("logo", ""),
                    "score": int(team.get("score", 0) or 0),
                    "team_id": str(t.get("id", "")),
                }
            status = comp.get("status", {}).get("type", {})
            status_info = {
                "state": self._state_name(status.get("name", "")),
                "detail": status.get("detail", ""),
                "period": status.get("period", 0),
                "clock": status.get("displayClock", ""),
                "completed": status.get("completed", False),
            }

        events = []
        for ev in raw.get("keyEvents", []):
            parsed = self._parse_event(ev)
            if parsed:
                events.append(parsed)

        stats = self._parse_stats(raw.get("boxscore", {}))

        # Parse starting lineups from rosters
        lineups = self._parse_rosters(raw.get("rosters", []))

        # Extract match date from header
        date = ""
        for comp in header.get("competitions", []):
            d = comp.get("date", "")
            if d:
                date = d[:10] if "T" in d else d[:10]
                break

        return {
            "match_id": match_id,
            "date": date,
            "status": status_info,
            "home": teams_info.get("home", {}),
            "away": teams_info.get("away", {}),
            "events": events,
            "statistics": stats,
            "lineups": lineups,
            "competition_id": competition_id,
        }

    def _state_name(self, name: str) -> str:
        m = {
            "STATUS_SCHEDULED": "scheduled",
            "STATUS_IN_PROGRESS": "live",
            "STATUS_HALFTIME": "halftime",
            "STATUS_END_OF_PERIOD": "live",
            "STATUS_FULL_TIME": "finished",
            "STATUS_FINAL": "finished",
        }
        return m.get(name, "scheduled")

    def _parse_event(self, ev: Dict) -> Optional[Dict]:
        """Parse one keyEvent into normalized format."""
        etype = ev.get("type", {})
        type_id = str(etype.get("id", ""))
        event_type = EVENT_TYPE_MAP.get(type_id)
        if not event_type and etype.get("text", "") not in (
            "Goal", "Goal - Header", "Penalty Goal", "Own Goal",
            "Yellow Card", "Red Card", "Substitution", "Kickoff",
            "Halftime", "End Regular Time",
        ):
            return None

        text = etype.get("text", "")
        if not event_type:
            if "Goal" in text:
                event_type = "goal"
            elif "Yellow" in text:
                event_type = "yellow_card"
            elif "Red" in text:
                event_type = "red_card"
            elif "Sub" in text:
                event_type = "substitution"
            else:
                event_type = type_id

        clock = ev.get("clock", {}).get("displayValue", "")
        team_name = ev.get("team", {}).get("displayName", "")
        ev_text = ev.get("text", "")
        short_text = ev.get("shortText", "")

        player_name = ""
        assist_name = ""
        player_in = ""
        player_out = ""

        athletes = ev.get("athletesInvolved", [])
        participants = ev.get("participants", [])

        if event_type == "substitution" and participants:
            if len(participants) >= 1:
                player_in = participants[0].get("athlete", {}).get("displayName", "")
            if len(participants) >= 2:
                player_out = participants[1].get("athlete", {}).get("displayName", "")
        elif athletes:
            player_name = athletes[0].get("displayName", "")
            if len(athletes) >= 2:
                assist_name = athletes[1].get("displayName", "")

        return {
            "type": event_type,
            "minute": clock,
            "team": team_name,
            "player": player_name or short_text,
            "player_in": player_in,
            "player_out": player_out,
            "assist": assist_name,
            "text": ev_text,
        }

    def _parse_rosters(self, rosters_raw: List[Dict]) -> Dict[str, Dict]:
        """Parse ESPN rosters data into structured lineups with formation and starters."""
        result: Dict[str, Dict] = {}
        if not rosters_raw:
            return result

        for team_roster in rosters_raw:
            side = team_roster.get("homeAway", "")
            if side not in ("home", "away"):
                continue

            formation = team_roster.get("formation", "")
            players = []
            for entry in team_roster.get("roster", []):
                athlete = entry.get("athlete", {})
                pos = entry.get("position", {})
                player = {
                    "id": str(athlete.get("id", "")),
                    "name": athlete.get("displayName", athlete.get("fullName", "")),
                    "short_name": athlete.get("shortName", ""),
                    "jersey": str(entry.get("jersey", "")) if entry.get("jersey") else "",
                    "position": _normalize_position(pos.get("abbreviation", "")),
                    "position_name": pos.get("displayName", pos.get("name", "")),
                    "starter": entry.get("starter", False),
                    "formation_place": entry.get("formationPlace", 0),
                    "active": entry.get("active", False),
                }
                players.append(player)

            starters = sorted(
                [p for p in players if p["starter"]],
                key=lambda p: p.get("formation_place", 99) or 99,
            )
            substitutes = [p for p in players if not p["starter"] and p["active"]]

            result[side] = {
                "formation": formation,
                "starters": starters,
                "substitutes": substitutes,
            }

        return result

    def _parse_stats(self, boxscore: Dict) -> Dict[str, Dict[str, Any]]:
        """Parse boxscore statistics into home/away dicts."""
        result: Dict[str, Dict[str, Any]] = {}
        for team in boxscore.get("teams", []):
            t = team.get("team", {})
            side = "home" if team.get("homeAway") == "home" else "away"
            stats_dict = {}
            for s in team.get("statistics", []):
                name = s.get("name", "")
                label = s.get("label", "")
                value = s.get("displayValue", "")
                stats_dict[name] = {"label": label, "value": value}
            result[side] = {
                "team_name": t.get("displayName", ""),
                "stats": stats_dict,
            }
        return result


# Singleton
live_match_service = LiveMatchService()
