"""
AI-powered player live performance analysis using DeepSeek.
Fetches per-player stats from ESPN Core API and generates
Chinese-language analysis at 4 match intervals (25', HT, 65', FT).
"""
import os
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

import requests
from openai import OpenAI

logger = logging.getLogger(__name__)

ESPN_CORE_BASE = "https://sports.core.api.espn.com/v2/sports/soccer/leagues/fifa.world"

BASE_DIR = Path(__file__).parent.parent
CACHE_DIR = BASE_DIR / "data" / "player_analysis"

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
    minute = _parse_clock(clock_str)
    if minute <= INTERVALS["p1"]["max_minute"]:
        return "p1"
    elif minute <= INTERVALS["p2"]["max_minute"]:
        return "p2"
    elif minute <= INTERVALS["p3"]["max_minute"]:
        return "p3"
    else:
        return "p4"


class PlayerLiveAnalysisService:
    """Fetch per-player stats from ESPN Core API and generate AI analysis."""

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        self.client = OpenAI(api_key=api_key) if api_key else None
        if self.client:
            self.client.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("AI_MODEL", "deepseek-chat")
        self._memory_cache: Dict[str, dict] = {}
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

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
            if i <= current_idx:
                analyses[iv] = self._get_or_generate_interval(
                    match_id, player_id, iv, player_name, position, clock, match_state, stats
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
        player_id: str,
        interval: str,
        player_name: str,
        position: str,
        clock: str,
        match_state: str,
        stats: Optional[Dict],
    ) -> Dict:
        """Get cached analysis or generate new one for a time interval."""
        # Check memory cache
        cache_key = f"{match_id}_{player_id}_{interval}"
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # Check file cache
        cached = self._load_cached(cache_key)
        if cached:
            self._memory_cache[cache_key] = cached
            return cached

        # Generate new analysis
        analysis_text = self._generate_analysis(player_name, position, interval, clock, stats)

        result = {
            "interval_key": interval,
            "interval_label": INTERVALS[interval]["label"],
            "generated": bool(analysis_text),
            "analysis": analysis_text or "",
        }

        # Cache it
        self._memory_cache[cache_key] = result
        self._save_cached(cache_key, result)

        return result

    def _generate_analysis(
        self,
        player_name: str,
        position: str,
        interval: str,
        clock: str,
        stats: Optional[Dict],
    ) -> str:
        """Generate AI analysis via DeepSeek or fallback to rule-based."""
        interval_label = INTERVALS[interval]["label"]

        if not stats or len(stats) == 0:
            return f"{interval_label}暂无个人统计数据"

        # Build stats summary for prompt
        stats_lines = []
        for key, info in stats.items():
            if isinstance(info, dict):
                stats_lines.append(f"{info['label']}: {info['value']}")

        if not stats_lines:
            return f"{interval_label}暂无有效数据"

        stats_summary = "，".join(stats_lines)

        # Try AI generation
        if self.client:
            try:
                prompt = f"""你是世界杯比赛分析师。请根据以下球员的实时比赛数据，用2-3句话简要评价该球员截至当前的表现（中文，100-150字）。

球员：{player_name}，位置：{position}
分析时段：{interval_label}（比赛时钟 {clock}）
实时数据：{stats_summary}

要求：简明扼要，突出亮点或问题，不提建议，纯分析。按球员位置侧重评价（如后卫侧重防守数据，前锋侧重进攻数据，中场侧重组织和传球）。"""

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
        return self._fallback_analysis(player_name, position, interval_label, stats)

    def _fallback_analysis(
        self, player_name: str, position: str, interval_label: str, stats: Dict
    ) -> str:
        """Generate simple stat summary as fallback."""
        parts = []

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
