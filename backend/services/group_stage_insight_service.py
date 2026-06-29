"""
Group-stage live data aggregation and concise AI match insight.

The service only uses locally persisted ESPN live-match data. AI output is
cached by data signature so users do not trigger a new generation on each open.
"""
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

BASE_DIR = Path(__file__).parent.parent
LIVE_MATCH_DIR = BASE_DIR / "data" / "live_matches"
INSIGHT_CACHE_DIR = BASE_DIR / "data" / "group_stage_insights"
PROMPT_VERSION = "v1"

TEAM_ALIASES = {
    "czechia": "czech republic",
    "czech republic": "czech republic",
    "bosnia-herzegovina": "bosnia and herzegovina",
    "bosnia and herzegovina": "bosnia and herzegovina",
    "türkiye": "turkey",
    "turkiye": "turkey",
    "turkey": "turkey",
    "congo dr": "dr congo",
    "dr congo": "dr congo",
    "korea republic": "south korea",
    "south korea": "south korea",
    "usa": "united states",
    "united states": "united states",
}


def _team_key(name: str) -> str:
    clean = str(name or "").strip().lower()
    clean = clean.replace("  ", " ").replace("_", " ")
    return TEAM_ALIASES.get(clean, clean)


def _num(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("%", "").strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _pct(value: float) -> float:
    # ESPN often stores passPct/shotPct as 0.9 instead of 90.
    return round(value * 100, 1) if 0 < value <= 1 else round(value, 1)


def _stat(stats: Dict[str, Any], key: str) -> float:
    raw = (stats or {}).get(key, {})
    if isinstance(raw, dict):
        return _num(raw.get("value"))
    return _num(raw)


def _clean_goal_player(name: str) -> str:
    text = str(name or "").strip()
    text = re.sub(r"\s+Goal.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+Penalty.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+Own Goal.*$", "", text, flags=re.IGNORECASE)
    return text or "未知球员"


def _empty_team(team: str, team_cn: str = "") -> Dict[str, Any]:
    return {
        "team": team,
        "team_cn": team_cn or team,
        "matches": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0,
        "goal_difference": 0,
        "shots": 0,
        "shots_on_target": 0,
        "shot_accuracy": 0,
        "avg_possession": 0,
        "pass_accuracy": 0,
        "corners": 0,
        "fouls": 0,
        "yellow_cards": 0,
        "red_cards": 0,
        "key_players": [],
        "form": [],
    }


class GroupStageInsightService:
    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        self.client = OpenAI(api_key=api_key) if api_key else None
        if self.client:
            self.client.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("AI_MODEL", "deepseek-chat")
        INSIGHT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def get_match_insight(
        self,
        match_id: int,
        home_team: str,
        away_team: str,
        home_team_cn: str = "",
        away_team_cn: str = "",
    ) -> Optional[Dict[str, Any]]:
        summaries = self._aggregate_group_stage()
        home_key = _team_key(home_team)
        away_key = _team_key(away_team)

        home = summaries.get(home_key) or _empty_team(home_team, home_team_cn)
        away = summaries.get(away_key) or _empty_team(away_team, away_team_cn)
        if home_team_cn:
            home["team_cn"] = home_team_cn
        if away_team_cn:
            away["team_cn"] = away_team_cn

        if home["matches"] == 0 and away["matches"] == 0:
            return None

        payload = {
            "home": home,
            "away": away,
            "comparison": self._comparison_points(home, away),
        }
        signature = hashlib.sha1(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

        cached = self._load_cache(match_id)
        if cached and cached.get("signature") == signature:
            return cached

        analysis, generated_by_ai = self._generate_analysis(home, away, payload["comparison"])
        result = {
            "available": True,
            "source": "ESPN小组赛实时数据聚合",
            "prompt_version": PROMPT_VERSION,
            "signature": signature,
            "generated_by_ai": generated_by_ai,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "home": home,
            "away": away,
            "comparison": payload["comparison"],
            "analysis": analysis,
        }
        self._save_cache(match_id, result)
        return result

    def _aggregate_group_stage(self) -> Dict[str, Dict[str, Any]]:
        teams: Dict[str, Dict[str, Any]] = {}
        goal_players: Dict[str, Dict[str, int]] = {}
        possession_sum: Dict[str, float] = {}
        accurate_passes: Dict[str, float] = {}
        total_passes: Dict[str, float] = {}

        for path in sorted(LIVE_MATCH_DIR.glob("*.json")):
            if path.name.endswith("_analysis.json") or path.name.startswith(("roster_", "players_")):
                continue
            try:
                detail = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            state = detail.get("status", {}).get("state", "")
            if state == "scheduled":
                continue

            home = detail.get("home", {})
            away = detail.get("away", {})
            for side, opponent_side in (("home", "away"), ("away", "home")):
                team = detail.get(side, {})
                opponent = detail.get(opponent_side, {})
                team_name = team.get("name", "")
                key = _team_key(team_name)
                if not key:
                    continue

                summary = teams.setdefault(key, _empty_team(team_name, team.get("name_cn", "")))
                stats = detail.get("statistics", {}).get(side, {}).get("stats", {})
                gf = int(_num(team.get("score")))
                ga = int(_num(opponent.get("score")))

                summary["matches"] += 1
                summary["goals_for"] += gf
                summary["goals_against"] += ga
                if gf > ga:
                    summary["wins"] += 1
                    result = "胜"
                elif gf == ga:
                    summary["draws"] += 1
                    result = "平"
                else:
                    summary["losses"] += 1
                    result = "负"

                summary["shots"] += int(_stat(stats, "totalShots"))
                summary["shots_on_target"] += int(_stat(stats, "shotsOnTarget"))
                summary["corners"] += int(_stat(stats, "wonCorners"))
                summary["fouls"] += int(_stat(stats, "foulsCommitted"))
                summary["yellow_cards"] += int(_stat(stats, "yellowCards"))
                summary["red_cards"] += int(_stat(stats, "redCards"))
                possession_sum[key] = possession_sum.get(key, 0.0) + _stat(stats, "possessionPct")
                accurate_passes[key] = accurate_passes.get(key, 0.0) + _stat(stats, "accuratePasses")
                total_passes[key] = total_passes.get(key, 0.0) + _stat(stats, "totalPasses")
                summary["form"].append({
                    "match_id": detail.get("match_id", path.stem),
                    "opponent": opponent.get("name", ""),
                    "opponent_cn": opponent.get("name_cn", opponent.get("name", "")),
                    "score": f"{gf}-{ga}",
                    "result": result,
                    "state": state,
                })

            for event in detail.get("events", []):
                if event.get("type") != "goal":
                    continue
                scorer_team = _team_key(event.get("team", ""))
                if not scorer_team:
                    continue
                player = _clean_goal_player(event.get("player", ""))
                goal_players.setdefault(scorer_team, {})
                goal_players[scorer_team][player] = goal_players[scorer_team].get(player, 0) + 1

        for key, summary in teams.items():
            summary["goal_difference"] = summary["goals_for"] - summary["goals_against"]
            summary["shot_accuracy"] = round(summary["shots_on_target"] / summary["shots"] * 100, 1) if summary["shots"] else 0
            summary["avg_possession"] = round(possession_sum.get(key, 0) / summary["matches"], 1) if summary["matches"] else 0
            summary["pass_accuracy"] = round(accurate_passes.get(key, 0) / total_passes.get(key, 1) * 100, 1) if total_passes.get(key) else 0
            players = sorted(goal_players.get(key, {}).items(), key=lambda item: (-item[1], item[0]))
            summary["key_players"] = [{"name": name, "goals": goals} for name, goals in players[:3]]

        return teams

    def _comparison_points(self, home: Dict[str, Any], away: Dict[str, Any]) -> List[str]:
        points = []
        if home["goals_for"] != away["goals_for"]:
            better = home if home["goals_for"] > away["goals_for"] else away
            points.append(f"{better['team_cn']}小组赛进球更多，累计{better['goals_for']}球。")
        if home["avg_possession"] and away["avg_possession"]:
            controller = home if home["avg_possession"] >= away["avg_possession"] else away
            points.append(f"{controller['team_cn']}控球更稳定，平均控球率{controller['avg_possession']}%。")
        if home["goals_against"] != away["goals_against"]:
            tighter = home if home["goals_against"] < away["goals_against"] else away
            points.append(f"{tighter['team_cn']}防守数据更稳，累计失球{tighter['goals_against']}个。")
        if home["shots_on_target"] != away["shots_on_target"]:
            sharper = home if home["shots_on_target"] > away["shots_on_target"] else away
            points.append(f"{sharper['team_cn']}射正产出更高，累计{sharper['shots_on_target']}次射正。")
        return points[:3]

    def _generate_analysis(self, home: Dict[str, Any], away: Dict[str, Any], comparison: List[str]) -> tuple[str, bool]:
        fallback = self._fallback_analysis(home, away, comparison)
        if not self.client:
            return fallback, False

        prompt = f"""你是世界杯战术分析师。只基于以下小组赛实时数据做简短分析，不要编造没有给出的事实，不预测具体比分。

主队：{self._team_context(home)}
客队：{self._team_context(away)}
对比点：{"；".join(comparison) if comparison else "双方已获取数据较少"}

请用中文输出3段，每段1-2句：
1. {home['team_cn']}目前情况
2. {away['team_cn']}目前情况
3. 双方对战分析
总字数控制在180-260字，专业、凝练。"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是严谨的足球数据分析师，结论必须由数据支撑，语言简洁。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.25,
                max_tokens=500,
            )
            text = (response.choices[0].message.content or "").strip()
            return text or fallback, bool(text)
        except Exception as exc:
            print(f"[GroupStageInsight] AI generation failed: {exc}")
            return fallback, False

    def _team_context(self, team: Dict[str, Any]) -> str:
        players = "、".join(f"{p['name']} {p['goals']}球" for p in team.get("key_players", [])) or "暂无进球球员数据"
        return (
            f"{team['team_cn']}，{team['matches']}场{team['wins']}胜{team['draws']}平{team['losses']}负，"
            f"进{team['goals_for']}球失{team['goals_against']}球，"
            f"射门{team['shots']}次/射正{team['shots_on_target']}次，"
            f"平均控球{team['avg_possession']}%，传球成功率{team['pass_accuracy']}%，"
            f"关键球员：{players}"
        )

    def _fallback_analysis(self, home: Dict[str, Any], away: Dict[str, Any], comparison: List[str]) -> str:
        def team_line(team: Dict[str, Any]) -> str:
            players = "、".join(f"{p['name']}({p['goals']}球)" for p in team.get("key_players", [])) or "暂无突出进球点"
            if team["matches"] == 0:
                return f"{team['team_cn']}暂无已获取的小组赛实时数据。"
            return (
                f"{team['team_cn']}小组赛已获取{team['matches']}场数据，"
                f"{team['wins']}胜{team['draws']}平{team['losses']}负，进{team['goals_for']}球失{team['goals_against']}球。"
                f"球队射正率{team['shot_accuracy']}%，平均控球{team['avg_possession']}%，关键球员为{players}。"
            )

        matchup = " ".join(comparison) if comparison else "双方样本有限，本场更需要关注临场阵容和转换效率。"
        return f"{team_line(home)}\n\n{team_line(away)}\n\n对战分析：{matchup}"

    def _cache_path(self, match_id: int) -> Path:
        return INSIGHT_CACHE_DIR / f"{match_id}.json"

    def _load_cache(self, match_id: int) -> Optional[Dict[str, Any]]:
        path = self._cache_path(match_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _save_cache(self, match_id: int, data: Dict[str, Any]):
        try:
            self._cache_path(match_id).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"[GroupStageInsight] Cache save failed: {exc}")


group_stage_insight_service = GroupStageInsightService()
