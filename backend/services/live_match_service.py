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
    "Turkey": "土耳其", "Czech Republic": "捷克", "Czechia": "捷克",
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

    def get_scoreboard(self) -> Dict:
        """Get all matches from ESPN fifa.world scoreboard (live + recent + upcoming)."""
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

    def get_today_matches(self) -> List[Dict]:
        """Return today's matches (all statuses) for the schedule page."""
        sb = self.get_scoreboard()
        return [self._simplify_match(ev) for ev in sb.get("events", [])]

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
        """Find an ESPN match_id by matching home/away team names. Returns match_id or None."""
        sb = self.get_scoreboard()
        h_norm = self._normalize_team(home_team)
        a_norm = self._normalize_team(away_team)
        for ev in sb.get("events", []):
            comps = ev.get("competitions", [])
            teams = {}
            for comp in comps:
                for team in comp.get("competitors", []):
                    side = team.get("homeAway", "unknown")
                    t = team.get("team", {})
                    teams[side] = t.get("displayName", t.get("abbreviation", ""))
            h = self._normalize_team(teams.get("home", ""))
            a = self._normalize_team(teams.get("away", ""))
            ev_date = ev.get("date", "")[:10]
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
                return str(ev.get("id", ""))
        return None

    def get_team_roster(self, team_id: str) -> Optional[Dict]:
        """Get full roster for a national team."""
        key = f"roster_{team_id}"
        return self._cached(key, ROSTER_TTL, lambda: self._fetch_roster(team_id))

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

    # ── ESPN fetchers ─────────────────────────────────────────

    def _fetch_scoreboard(self) -> Dict:
        url = f"{ESPN_BASE}/scoreboard"
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

        for comp in comps:
            for team in comp.get("competitors", []):
                side = team.get("homeAway", "unknown")
                t = team.get("team", {})
                teams[side] = t.get("displayName", t.get("abbreviation", "?"))
                scores[side] = int(team.get("score", 0) or 0)

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

        home_name = teams.get("home", "")
        away_name = teams.get("away", "")

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
        for comp in comps:
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

        return {
            "match_id": match_id,
            "status": status_info,
            "home": teams_info.get("home", {}),
            "away": teams_info.get("away", {}),
            "events": events,
            "statistics": stats,
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
