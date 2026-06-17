"""
AI-powered player live performance analysis using DeepSeek.
Fetches per-player stats from ESPN Core API and generates
Chinese-language analysis at 4 match intervals (25', HT, 65', FT).
"""
import os
import json
import time
import logging
import re
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

import requests
from openai import OpenAI

logger = logging.getLogger(__name__)

ESPN_CORE_BASE = "https://sports.core.api.espn.com/v2/sports/soccer/leagues/fifa.world"

BASE_DIR = Path(__file__).parent.parent
CACHE_DIR = BASE_DIR / "data" / "player_analysis"
PLAYER_STATS_DIR = BASE_DIR / "data" / "player_live_stats"
CACHE_VERSION = 2

INTERVALS = {
    "p1": {"label": "上半场25分钟", "max_minute": 25},
    "p2": {"label": "中场休息", "max_minute": 52},
    "p3": {"label": "下半场65分钟", "max_minute": 70},
    "p4": {"label": "全场结束", "max_minute": 200},
}

# Key stats to extract from ESPN Core API with Chinese labels
STAT_KEYS: Dict[str, str] = {
    "totalShots": "射门",
    "shotsOnTarget": "射正",
    "goals": "进球",
    "assists": "助攻",
    "totalPasses": "传球",
    "accuratePasses": "精准传球",
    "passingPct": "传球成功率",
    "totalTackles": "抢断",
    "totalInterceptions": "拦截",
    "totalClearances": "解围",
    "totalDribbles": "过人",
    "touches": "触球",
    "aerialDuelsWon": "争顶成功",
    "foulsCommitted": "犯规",
    "wasFouled": "被犯规",
    "offsides": "越位",
    "totalCrosses": "传中",
    "accurateCrosses": "精准传中",
    "totalLongBalls": "长传",
    "blockedShots": "封堵射门",
    "saves": "扑救",
    "goalsConceded": "失球",
    "cleanSheets": "零封",
    "savesTotal": "扑救总数",
    "duelTotal": "对抗总次数",
    "duelWon": "对抗成功",
    "aerialTotal": "争顶总数",
    "dispossessed": "丢失球权",
    "turnovers": "失误",
    "foulsSuffered": "被侵犯",
    "yellowCards": "黄牌",
    "redCards": "红牌",
}


def _parse_clock(clock_str: str) -> float:
    """Parse ESPN clock strings like '23'', '45'+2', '67'', '90'+4' to float minutes."""
    s = str(clock_str).replace("'", "").strip()
    if not s:
        return 0.0
    if "+" in s:
        parts = s.split("+")
        try:
            return float(parts[0]) + float(parts[1])
        except ValueError:
            return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def get_current_interval(clock_str: str, match_state: str) -> str:
    """Determine which analysis interval we're in based on clock and match state."""
    if match_state == "finished":
        return "p4"
    if match_state == "halftime":
        return "p2"
    minute = _parse_clock(clock_str)
    if minute >= 65:
        return "p3"
    if minute >= 45:
        return "p2"
    return "p1"


def _name_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _stats_signature(stats: Optional[Dict]) -> str:
    payload = json.dumps(stats or {}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _interval_available(interval: str, clock: str, match_state: str) -> bool:
    if match_state == "finished":
        return True
    if interval == "p4":
        return False
    minute = _parse_clock(clock)
    if interval == "p1":
        return minute >= 25
    if interval == "p2":
        return match_state == "halftime" or minute >= 45
    if interval == "p3":
        return minute >= 65
    return False


def _event_within_interval(event: Dict[str, Any], interval: str, clock: str, match_state: str) -> bool:
    if interval == "p4" or match_state == "finished":
        return True
    limit = INTERVALS[interval]["max_minute"]
    current_minute = _parse_clock(clock)
    if current_minute > 0:
        limit = min(limit, current_minute)
    return _parse_clock(event.get("minute", "")) <= limit


def _extract_player_events(events: Optional[List[Dict[str, Any]]], player_name: str, interval: str, clock: str, match_state: str) -> List[str]:
    if not events:
        return []
    player_key = _name_key(player_name)
    if not player_key:
        return []

    matched: List[str] = []
    for event in events:
        if not _event_within_interval(event, interval, clock, match_state):
            continue
        text = " ".join(str(event.get(k, "")) for k in ("player", "assist", "player_in", "player_out", "text", "description_cn"))
        if player_key not in _name_key(text):
            continue
        minute = event.get("minute") or ""
        event_type = event.get("type_cn") or event.get("type") or "事件"
        description = event.get("description_cn") or event.get("text") or event.get("player") or ""
        matched.append(f"{minute} {event_type}: {description}".strip())

    return matched[:5]


def _get_player_substitution_context(events: Optional[List[Dict[str, Any]]], player_name: str) -> Dict[str, Any]:
    context: Dict[str, Any] = {
        "subbed_in": False,
        "subbed_in_minute": None,
        "subbed_out": False,
        "subbed_out_minute": None,
    }
    if not events:
        return context

    player_key = _name_key(player_name)
    if not player_key:
        return context

    for event in events:
        if event.get("type") != "substitution":
            continue
        player_in = str(event.get("player_in") or "")
        player_out = str(event.get("player_out") or "")
        minute_raw = event.get("minute", "")
        minute = _parse_clock(minute_raw)

        if player_key and player_key in _name_key(player_in):
            context.update({
                "subbed_in": True,
                "subbed_in_minute": minute,
                "subbed_in_display": minute_raw,
            })
        if player_key and player_key in _name_key(player_out):
            context.update({
                "subbed_out": True,
                "subbed_out_minute": minute,
                "subbed_out_display": minute_raw,
            })

    return context


def _interval_window(interval: str, clock: str, match_state: str) -> tuple[float, float]:
    current_minute = _parse_clock(clock)
    if match_state == "finished":
        current_minute = 200
    windows = {
        "p1": (0, 25),
        "p2": (25, 52),
        "p3": (52, 70),
        "p4": (70, 200),
    }
    start, end = windows.get(interval, (0, current_minute or 200))
    if current_minute > 0:
        end = min(end, current_minute)
    return start, end


def _player_available_for_interval(sub_context: Dict[str, Any], interval: str, clock: str, match_state: str) -> tuple[bool, str]:
    start, end = _interval_window(interval, clock, match_state)
    subbed_in_minute = sub_context.get("subbed_in_minute")
    subbed_out_minute = sub_context.get("subbed_out_minute")

    if sub_context.get("subbed_in") and subbed_in_minute is not None and subbed_in_minute > end:
        return False, "not_yet_subbed_in"
    if sub_context.get("subbed_out") and subbed_out_minute is not None and subbed_out_minute < start:
        return False, "already_subbed_out"
    return True, ""


def _sub_context_text(sub_context: Dict[str, Any]) -> str:
    parts: List[str] = []
    if sub_context.get("subbed_in"):
        parts.append(f"{sub_context.get('subbed_in_display') or sub_context.get('subbed_in_minute')} 替补登场")
    if sub_context.get("subbed_out"):
        parts.append(f"{sub_context.get('subbed_out_display') or sub_context.get('subbed_out_minute')} 被换下")
    return "；".join(parts) if parts else "首发或暂无换人信息"


def _only_substitution_events(player_events: Optional[List[str]]) -> bool:
    if not player_events:
        return False
    substitution_markers = ("substitution", "换人", "替补登场", "被换下")
    return all(any(marker in event for marker in substitution_markers) for event in player_events)


class PlayerLiveAnalysisService:
    """Fetch per-player stats from ESPN Core API and generate AI analysis."""

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        self.client = OpenAI(api_key=api_key) if api_key else None
        if self.client:
            self.client.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("AI_MODEL", "deepseek-chat")
        self._memory_cache: Dict[str, dict] = {}
        self._collection_cache: Dict[str, float] = {}
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        PLAYER_STATS_DIR.mkdir(parents=True, exist_ok=True)

    # ── public API ─────────────────────────────────────────────

    def get_player_analysis(
        self,
        match_id: str,
        competition_id: str,
        team_id: str,
        player_id: str,
        player_name: str,
        position: str,
        clock: str = "",
        match_state: str = "scheduled",
        events: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Get player stats + AI analysis for all available intervals."""
        current_interval = get_current_interval(clock, match_state)

        # Fetch player stats from ESPN Core API
        stats = self._fetch_player_stats(match_id, competition_id, team_id, player_id)
        stats_available = stats is not None and len(stats) > 0

        # Determine which intervals should be generated
        interval_order = ["p1", "p2", "p3", "p4"]
        current_idx = interval_order.index(current_interval)

        analyses: Dict[str, Dict] = {}
        for i, iv in enumerate(interval_order):
            should_generate = i <= current_idx and (_interval_available(iv, clock, match_state) or iv == current_interval)
            if should_generate:
                analyses[iv] = self._get_or_generate_interval(
                    match_id, team_id, player_id, iv, player_name, position, clock, match_state, stats, events
                )
            else:
                analyses[iv] = {
                    "interval_key": iv,
                    "interval_label": INTERVALS[iv]["label"],
                    "generated": False,
                    "analysis": "",
                }

        return {
            "player_id": player_id,
            "player_name": player_name,
            "position": position,
            "stats": stats if stats_available else {},
            "stats_available": stats_available,
            "current_interval": current_interval,
            "clock": clock,
            "match_state": match_state,
            "analyses": analyses,
        }

    def collect_match_player_stats(self, match_detail: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
        """Persist live stats for every player who has appeared in the match."""
        match_id = str(match_detail.get("match_id") or match_detail.get("id") or "")
        if not match_id:
            return {"collected": 0, "reason": "missing_match_id"}

        status = match_detail.get("status", {}) or {}
        match_state = status.get("state", "scheduled")
        clock = status.get("clock", "")
        is_finished = match_state == "finished"
        collection_key = f"{match_id}:{match_state}:{clock}"

        if not force and self._collection_recent(collection_key, is_finished):
            return {"collected": 0, "skipped": True, "reason": "recently_collected"}

        persisted = self._load_match_player_stats(match_id)
        if is_finished and persisted.get("final_collected"):
            return {"collected": 0, "skipped": True, "reason": "final_already_collected"}

        competition_id = str(match_detail.get("competition_id") or "")
        if not competition_id:
            return {"collected": 0, "reason": "missing_competition_id"}

        players = self._extract_appeared_players(match_detail)
        if not players:
            return {"collected": 0, "reason": "no_appeared_players"}

        interval = get_current_interval(clock, match_state)
        interval_ready = _interval_available(interval, clock, match_state) or is_finished
        now = datetime.now().isoformat()

        output = {
            "match_id": match_id,
            "competition_id": competition_id,
            "status": status,
            "last_collected_at": now,
            "final_collected": bool(is_finished),
            "players": persisted.get("players", {}),
        }

        collected = 0
        for player in players:
            team_id = player["team_id"]
            player_id = player["id"]
            stats = self._fetch_player_stats(match_id, competition_id, team_id, player_id)
            key = f"{team_id}_{player_id}"
            existing = output["players"].get(key, {})
            record = {
                **existing,
                "team_id": team_id,
                "team_side": player["team_side"],
                "team_name": player.get("team_name", ""),
                "player_id": player_id,
                "player_name": player.get("name", ""),
                "short_name": player.get("short_name", ""),
                "jersey": player.get("jersey", ""),
                "position": player.get("position", ""),
                "position_name": player.get("position_name", ""),
                "starter": player.get("starter", False),
                "appeared": True,
                "minutes": player.get("minutes", {}),
                "latest_stats": stats or {},
                "latest_stats_available": bool(stats),
                "latest_collected_at": now,
                "interval_snapshots": existing.get("interval_snapshots", {}),
            }
            if interval_ready or is_finished:
                record["interval_snapshots"][interval] = {
                    "interval_key": interval,
                    "interval_label": INTERVALS[interval]["label"],
                    "clock": clock,
                    "match_state": match_state,
                    "stats": stats or {},
                    "stats_available": bool(stats),
                    "collected_at": now,
                }
            if is_finished:
                record["final_stats"] = stats or {}
                record["final_stats_available"] = bool(stats)
                record["final_collected_at"] = now
            output["players"][key] = record
            collected += 1

        self._save_match_player_stats(match_id, output)
        self._collection_cache[collection_key] = time.time()
        return {
            "collected": collected,
            "match_id": match_id,
            "final_collected": output["final_collected"],
            "path": str(self._match_player_stats_path(match_id)),
        }

    def _collection_recent(self, collection_key: str, is_finished: bool) -> bool:
        if is_finished:
            return False
        ts = self._collection_cache.get(collection_key)
        return bool(ts and time.time() - ts < 30)

    def _match_player_stats_path(self, match_id: str) -> Path:
        return PLAYER_STATS_DIR / f"{match_id}.json"

    def _load_match_player_stats(self, match_id: str) -> Dict[str, Any]:
        path = self._match_player_stats_path(match_id)
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to load match player stats {match_id}: {e}")
            return {}

    def _save_match_player_stats(self, match_id: str, data: Dict[str, Any]):
        path = self._match_player_stats_path(match_id)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save match player stats {match_id}: {e}")

    def _extract_appeared_players(self, match_detail: Dict[str, Any]) -> List[Dict[str, Any]]:
        lineups = match_detail.get("lineups", {}) or {}
        events = match_detail.get("events", []) or []
        teams = {
            "home": match_detail.get("home", {}) or {},
            "away": match_detail.get("away", {}) or {},
        }
        appeared: Dict[str, Dict[str, Any]] = {}

        for side in ("home", "away"):
            team = teams[side]
            team_id = str(team.get("team_id") or "")
            team_name = team.get("team_name") or team.get("name") or ""
            lineup = lineups.get(side) or {}
            for player in lineup.get("starters", []) or []:
                record = self._player_record(player, side, team_id, team_name, starter=True)
                if record:
                    record["minutes"] = self._player_minutes_context(events, record["player_name"], starter=True)
                    appeared[f"{team_id}_{record['id']}"] = record

        for event in events:
            if event.get("type") != "substitution":
                continue
            incoming_name = event.get("player_in") or ""
            outgoing_name = event.get("player_out") or ""
            if not incoming_name:
                continue

            for side in ("home", "away"):
                team = teams[side]
                team_id = str(team.get("team_id") or "")
                team_name = team.get("team_name") or team.get("name") or ""
                lineup = lineups.get(side) or {}
                outgoing = self._find_player_by_name(outgoing_name, lineup.get("starters", []) or [])
                incoming = self._find_player_by_name(incoming_name, lineup.get("substitutes", []) or [])
                if not outgoing or not incoming:
                    continue
                record = self._player_record(incoming, side, team_id, team_name, starter=False)
                if record:
                    record["minutes"] = self._player_minutes_context(events, record["player_name"], starter=False)
                    appeared[f"{team_id}_{record['id']}"] = record
                break

        return list(appeared.values())

    def _player_record(self, player: Dict[str, Any], side: str, team_id: str, team_name: str, starter: bool) -> Optional[Dict[str, Any]]:
        player_id = str(player.get("id") or "")
        if not player_id or not team_id:
            return None
        return {
            "id": player_id,
            "team_id": team_id,
            "team_side": side,
            "team_name": team_name,
            "name": player.get("name") or "",
            "player_name": player.get("name") or "",
            "short_name": player.get("short_name") or "",
            "jersey": player.get("jersey") or "",
            "position": player.get("position") or "",
            "position_name": player.get("position_name") or "",
            "starter": starter,
        }

    def _find_player_by_name(self, name: str, players: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        target = _name_key(name)
        if not target:
            return None
        for player in players:
            names = [player.get("name", ""), player.get("short_name", "")]
            if any(target == _name_key(n) or target in _name_key(n) or _name_key(n) in target for n in names if n):
                return player
        return None

    def _player_minutes_context(self, events: List[Dict[str, Any]], player_name: str, starter: bool) -> Dict[str, Any]:
        sub_context = _get_player_substitution_context(events, player_name)
        return {
            "starter": starter,
            "subbed_in": sub_context.get("subbed_in", False),
            "subbed_in_minute": sub_context.get("subbed_in_minute"),
            "subbed_in_display": sub_context.get("subbed_in_display"),
            "subbed_out": sub_context.get("subbed_out", False),
            "subbed_out_minute": sub_context.get("subbed_out_minute"),
            "subbed_out_display": sub_context.get("subbed_out_display"),
        }

    # ── ESPN Core API ──────────────────────────────────────────

    def _fetch_player_stats(
        self, match_id: str, competition_id: str, team_id: str, player_id: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch individual player statistics from ESPN Core API."""
        if not competition_id or not team_id or not player_id:
            return None

        url = (
            f"{ESPN_CORE_BASE}/events/{match_id}"
            f"/competitions/{competition_id}"
            f"/competitors/{team_id}"
            f"/roster/{player_id}/statistics/0"
        )

        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            raw = r.json()
            return self._parse_player_stats(raw)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.debug(f"Player stats not available for {player_id} in match {match_id}")
            else:
                logger.warning(f"ESPN Core API error for player {player_id}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch player stats for {player_id}: {e}")
            return None

    def _parse_player_stats(self, raw: Dict) -> Dict[str, Any]:
        """Parse ESPN Core API player stats into simplified {label: value} dict."""
        result: Dict[str, Any] = {}

        # The API returns stats grouped by category
        categories = raw.get("splits", {}).get("categories", [])
        for cat in categories:
            stats_list = cat.get("stats", [])
            for s in stats_list:
                name = s.get("name", "")
                if name in STAT_KEYS:
                    result[name] = {
                        "label": STAT_KEYS[name],
                        "value": s.get("displayValue", s.get("value", "")),
                    }

        # If the categories structure is different, try alternative paths
        if not result:
            # Try top-level stats array
            for s in raw.get("statistics", raw.get("stats", [])):
                name = s.get("name", "")
                if name in STAT_KEYS:
                    result[name] = {
                        "label": STAT_KEYS[name],
                        "value": s.get("displayValue", s.get("value", "")),
                    }

        return result

    # ── AI analysis generation ──────────────────────────────────

    def _get_or_generate_interval(
        self,
        match_id: str,
        team_id: str,
        player_id: str,
        interval: str,
        player_name: str,
        position: str,
        clock: str,
        match_state: str,
        stats: Optional[Dict],
        events: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict:
        """Get cached analysis or generate new one for a time interval."""
        # Check memory cache
        cache_key = f"{match_id}_{team_id}_{player_id}_{interval}"
        signature = _stats_signature(stats)
        generated_minute = _parse_clock(clock)
        cache_allowed = _interval_available(interval, clock, match_state)
        cache_locked = interval != get_current_interval(clock, match_state) or match_state == "finished"
        if cache_key in self._memory_cache:
            cached = self._memory_cache[cache_key]
            if self._cache_valid(cached, signature, cache_allowed):
                self._lock_cache_if_past(cache_key, cached, interval, clock, match_state)
                return cached

        # Check file cache
        cached = self._load_cached(cache_key)
        if cached and self._cache_valid(cached, signature, cache_allowed):
            self._lock_cache_if_past(cache_key, cached, interval, clock, match_state)
            self._memory_cache[cache_key] = cached
            return cached

        current_interval = get_current_interval(clock, match_state)
        if interval != current_interval:
            return {
                "_cache_version": CACHE_VERSION,
                "team_id": team_id,
                "player_id": player_id,
                "interval_key": interval,
                "interval_label": INTERVALS[interval]["label"],
                "generated": False,
                "analysis": "该时段数据快照未捕获",
            }

        player_events = _extract_player_events(events, player_name, interval, clock, match_state)
        sub_context = _get_player_substitution_context(events, player_name)
        player_available, unavailable_reason = _player_available_for_interval(sub_context, interval, clock, match_state)
        if not player_available:
            if unavailable_reason == "not_yet_subbed_in":
                analysis_text = "未上场"
            else:
                analysis_text = f"{INTERVALS[interval]['label']}该球员已被换下，暂无该时段场上表现分析"
        else:
            analysis_text = self._generate_analysis(player_name, position, interval, clock, stats, player_events, sub_context)

        result = {
            "_cache_version": CACHE_VERSION,
            "_stats_signature": signature,
            "_generated_minute": generated_minute,
            "_cache_locked": cache_locked,
            "interval_key": interval,
            "interval_label": INTERVALS[interval]["label"],
            "generated": bool(analysis_text),
            "analysis": analysis_text or "",
        }

        if cache_allowed:
            self._memory_cache[cache_key] = result
            self._save_cached(cache_key, result)

        return result

    def _cache_valid(self, cached: Dict, signature: str, cache_allowed: bool) -> bool:
        """Reject legacy or early-match cache that may have been generated from stale ESPN stats."""
        if cached.get("_cache_version") != CACHE_VERSION:
            return False
        if not cache_allowed:
            return False
        if cached.get("_stats_signature") != signature and not cached.get("_cache_locked"):
            return False
        return True

    def _lock_cache_if_past(self, cache_key: str, cached: Dict, interval: str, clock: str, match_state: str):
        if cached.get("_cache_locked"):
            return
        if interval == get_current_interval(clock, match_state) and match_state != "finished":
            return
        cached["_cache_locked"] = True
        self._memory_cache[cache_key] = cached
        self._save_cached(cache_key, cached)

    def _generate_analysis(
        self,
        player_name: str,
        position: str,
        interval: str,
        clock: str,
        stats: Optional[Dict],
        player_events: Optional[List[str]] = None,
        sub_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate AI analysis via DeepSeek or fallback to rule-based."""
        interval_label = INTERVALS[interval]["label"]
        event_summary = "；".join(player_events or []) if player_events else "无"
        substitution_summary = _sub_context_text(sub_context or {})

        if (not stats or len(stats) == 0) and not player_events:
            return f"{interval_label}暂无个人统计数据"

        # Build stats summary for prompt
        stats_lines = []
        for key, info in stats.items():
            if isinstance(info, dict):
                stats_lines.append(f"{info['label']}: {info['value']}")

        if not stats_lines and not player_events:
            return f"{interval_label}暂无有效数据"

        stats_summary = "，".join(stats_lines) if stats_lines else "个人统计暂未同步"

        # Try AI generation
        if self.client:
            try:
                prompt = f"""你是世界杯比赛实时分析师。请根据以下球员的实时比赛数据和关键事件，用2-3句话评价该球员截至当前的表现（中文，100-150字）。

球员：{player_name}，位置：{position}
分析时段：{interval_label}（比赛时钟 {clock}）
登场状态：{substitution_summary}
实时数据：{stats_summary}
关键事件：{event_summary}

要求：
1. 关键事件优先级高于普通累计数据；如果球员已有进球、助攻、制造点球、关键扑救等决定性事件，必须正向体现，不能仅因触球少或传球少判断为沉寂。
2. 实时个人统计可能存在 ESPN 同步延迟或缺项；若数据与关键事件冲突，应说明“统计口径仍在同步”，避免下绝对负面结论。
3. 如果球员是替补登场，只评价他登场后的表现；不要把被换下球员或球队此前的数据归到他身上，也不要因为登场时间短就作过重负面判断。
4. 按位置侧重评价：后卫看防守动作和失误，前锋看进球、射门、威胁和牵制，中场看组织、传球、推进和防守覆盖，门将看扑救和失球。
5. 不提建议，不预测未来，只分析当前表现；语气克制，避免“明显低迷/沉寂”等过重判断，除非多项数据和事件都支持。"""

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=300,
                )
                result = response.choices[0].message.content
                if result:
                    logger.info(f"AI analysis generated for {player_name} [{interval}]")
                    return result.strip()
            except Exception as e:
                logger.warning(f"AI analysis generation failed for {player_name}: {e}")

        # Fallback: simple stat-based summary
        return self._fallback_analysis(player_name, position, interval_label, stats or {}, player_events)

    def _fallback_analysis(
        self, player_name: str, position: str, interval_label: str, stats: Dict, player_events: Optional[List[str]] = None
    ) -> str:
        """Generate simple stat summary as fallback."""
        parts = []

        if player_events:
            if _only_substitution_events(player_events):
                return f"{player_name}在{interval_label}已替补登场，个人统计仍在同步或样本较少，暂不把换人事件本身视为表现亮点。"
            return f"{player_name}在{interval_label}已有关键事件参与：{'；'.join(player_events[:2])}。即使部分个人统计仍在同步，也应视为对比赛产生了直接影响。"

        # Shot stats for attacking players
        shots = stats.get("totalShots", {})
        if isinstance(shots, dict) and shots.get("value"):
            parts.append(f"射门{shots['value']}次")
        sot = stats.get("shotsOnTarget", {})
        if isinstance(sot, dict) and sot.get("value"):
            parts.append(f"射正{sot['value']}次")

        # Goals
        goals = stats.get("goals", {})
        if isinstance(goals, dict) and goals.get("value") and goals["value"] != "0":
            parts.append(f"进球{goals['value']}个")

        # Pass accuracy
        passes = stats.get("totalPasses", {})
        pass_pct = stats.get("passingPct", {})
        if isinstance(passes, dict) and passes.get("value"):
            pct_str = f"（成功率{pass_pct['value']}%）" if isinstance(pass_pct, dict) and pass_pct.get("value") else ""
            parts.append(f"传球{passes['value']}次{pct_str}")

        # Defensive
        tackles = stats.get("totalTackles", {})
        if isinstance(tackles, dict) and tackles.get("value"):
            parts.append(f"抢断{tackles['value']}次")

        interceptions = stats.get("totalInterceptions", {})
        if isinstance(interceptions, dict) and interceptions.get("value"):
            parts.append(f"拦截{interceptions['value']}次")

        if not parts:
            return f"{interval_label}暂无显著数据"

        return f"{player_name}在{interval_label}的数据表现：{'，'.join(parts)}。"

    # ── caching layer ──────────────────────────────────────────

    def _cache_path(self, cache_key: str) -> Path:
        return CACHE_DIR / f"{cache_key}.json"

    def _load_cached(self, cache_key: str) -> Optional[Dict]:
        path = self._cache_path(cache_key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to load player analysis cache {cache_key}: {e}")
            return None

    def _save_cached(self, cache_key: str, data: Dict):
        path = self._cache_path(cache_key)
        try:
            data["_cached_at"] = __import__("datetime").datetime.now().isoformat()
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save player analysis cache {cache_key}: {e}")


# Singleton
player_live_analysis_service = PlayerLiveAnalysisService()
