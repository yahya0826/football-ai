"""
Match Analysis Service - Generates concise Chinese halftime/fulltime analysis
from ESPN match data using professional football knowledge.

Rule-based analysis: no AI calls, instant generation, consistent quality.
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


def _parse_minute(min_str: str) -> float:
    """Parse '45'+3' or '90'+1' to float minutes."""
    s = str(min_str).replace("'", "").strip()
    if "+" in s:
        parts = s.split("+")
        return float(parts[0]) + float(parts[1])
    try:
        return float(s)
    except ValueError:
        return 0.0


def _safe_num(val, default=0):
    """Parse numeric value from string."""
    if val is None:
        return default
    try:
        return float(str(val).replace("%", "").replace(",", "."))
    except (ValueError, TypeError):
        return default


def analyze_match(match_detail: Dict) -> Dict:
    """
    Generate halftime or fulltime analysis.

    Returns:
        {
            "type": "halftime" | "fulltime" | "live",
            "summary": str,           # 1-2 sentence overview
            "analysis": str,          # Main analysis text (2-3 paragraphs)
            "key_stats": List[str],   # 3-5 key stat highlights
            "momentum": str,          # Current momentum assessment
            "star_performers": List[str],  # Key players mentioned in events
        }
    """
    status = match_detail.get("status", {})
    state = status.get("state", "")
    events = match_detail.get("events", [])
    stats = match_detail.get("statistics", {})
    home = match_detail.get("home", {})
    away = match_detail.get("away", {})

    home_name = home.get("name_cn", home.get("name", "主队"))
    away_name = away.get("name_cn", away.get("name", "客队"))
    home_score = home.get("score", 0)
    away_score = away.get("score", 0)

    if state == "halftime":
        return _halftime_analysis(events, stats, home_name, away_name, home_score, away_score)
    elif state == "finished":
        return _fulltime_analysis(events, stats, home_name, away_name, home_score, away_score)
    elif state == "live":
        return _live_analysis(events, stats, home_name, away_name, home_score, away_score)
    else:
        return {
            "type": "scheduled",
            "summary": "比赛尚未开始",
            "analysis": "",
            "key_stats": [],
            "momentum": "",
            "star_performers": [],
        }


def _get_event_summary(events: List[Dict], max_minute: float = 200) -> Dict:
    """Extract key events up to a certain minute."""
    goals = []
    yellows = []
    reds = []
    subs = []

    for ev in events:
        m = _parse_minute(ev.get("minute", "0"))
        if m > max_minute:
            continue

        etype = ev.get("type", "")
        desc_cn = ev.get("description_cn", ev.get("text", ""))
        team = ev.get("team_cn", ev.get("team", ""))
        player = ev.get("player", "")

        if etype == "goal":
            goals.append({"minute": m, "team": team, "player": player, "desc": desc_cn})
        elif etype == "yellow_card":
            yellows.append({"minute": m, "team": team, "player": player, "desc": desc_cn})
        elif etype == "red_card":
            reds.append({"minute": m, "team": team, "player": player, "desc": desc_cn})
        elif etype == "substitution":
            subs.append({"minute": m, "team": team, "desc": desc_cn})

    return {"goals": goals, "yellows": yellows, "reds": reds, "subs": subs}


def _get_stat(stats: Dict, side: str, key: str) -> float:
    """Get a numeric stat value for a side."""
    s = stats.get(side, {}).get("stats", {}).get(key, {})
    val = s.get("value", 0) if isinstance(s, dict) else 0
    return _safe_num(val)


def _get_stat_text(stats: Dict, side: str, key: str) -> str:
    """Get stat display value."""
    s = stats.get(side, {}).get("stats", {}).get(key, {})
    return s.get("value", "0") if isinstance(s, dict) else "0"


def _halftime_analysis(events, stats, home_name, away_name, home_score, away_score) -> Dict:
    """Generate halftime analysis."""
    first_half = _get_event_summary(events, max_minute=60)  # include stoppage time
    all_events = _get_event_summary(events)

    # Compute first-half stats approximation (halftime stats = current stats)
    h_poss = _get_stat(stats, "home", "possessionPct")
    a_poss = _get_stat(stats, "away", "possessionPct")
    h_shots = _get_stat(stats, "home", "totalShots")
    a_shots = _get_stat(stats, "away", "totalShots")
    h_sot = _get_stat(stats, "home", "shotsOnTarget")
    a_sot = _get_stat(stats, "away", "shotsOnTarget")
    h_corners = _get_stat(stats, "home", "wonCorners")
    a_corners = _get_stat(stats, "away", "wonCorners")
    h_fouls = _get_stat(stats, "home", "foulsCommitted")
    a_fouls = _get_stat(stats, "away", "foulsCommitted")
    h_yellow = _get_stat(stats, "home", "yellowCards")
    a_yellow = _get_stat(stats, "away", "yellowCards")
    h_red = _get_stat(stats, "home", "redCards")
    a_red = _get_stat(stats, "away", "redCards")

    # Key stats
    key_stats = []
    if h_poss > 0 or a_poss > 0:
        key_stats.append(f"控球率：{home_name} {h_poss:.0f}% - {a_poss:.0f}% {away_name}")
    if h_shots > 0 or a_shots > 0:
        key_stats.append(f"射门：{home_name} {int(h_shots)}次（{int(h_sot)}次射正） - {away_name} {int(a_shots)}次（{int(a_sot)}次射正）")
    if h_corners > 0 or a_corners > 0:
        key_stats.append(f"角球：{home_name} {int(h_corners)} - {int(a_corners)} {away_name}")

    # --- Generate analysis ---
    parts = []

    # 1. Score overview
    goal_text = ""
    if first_half["goals"]:
        goal_parts = []
        for g in first_half["goals"]:
            goal_parts.append(f"第{g['minute']:.0f}分钟{g['player']}为{g['team']}破门")
        goal_text = "，".join(goal_parts)
    else:
        goal_text = "双方上半场均未能破门"

    if home_score > away_score:
        parts.append(f"上半场结束，{home_name} {home_score}-{away_score} 领先{away_name}。{goal_text}。")
    elif away_score > home_score:
        parts.append(f"上半场结束，{away_name} {away_score}-{home_score} 领先{home_name}。{goal_text}。")
    else:
        parts.append(f"上半场结束，双方 {home_score}-{away_score} 战平。{goal_text}。")

    # 2. Possession & control analysis
    if h_poss > 0 and a_poss > 0:
        diff = h_poss - a_poss
        if abs(diff) < 5:
            parts.append(f"控球方面双方势均力敌（{home_name} {h_poss:.0f}% vs {away_name} {a_poss:.0f}%），中场争夺激烈。")
        elif diff > 0:
            parts.append(f"{home_name}掌控了更多球权（控球率 {h_poss:.0f}%），{away_name}更多依靠反击寻找机会。")
        else:
            parts.append(f"{away_name}控球占优（控球率 {a_poss:.0f}%），{home_name}在无球状态下保持紧凑阵型。")

    # 3. Attack threat assessment
    h_threat = h_shots + h_corners
    a_threat = a_shots + a_corners
    if h_threat > 0 or a_threat > 0:
        if h_threat > a_threat * 1.5:
            parts.append(f"进攻端{home_name}明显更具威胁，创造{int(h_shots)}次射门和{int(h_corners)}个角球，持续施压{away_name}防线。")
        elif a_threat > h_threat * 1.5:
            parts.append(f"进攻端{away_name}威胁更大，{int(a_shots)}次射门和{int(a_corners)}个角球说明其进攻组织更具效率。")
        else:
            parts.append(f"双方在进攻端均有建树，{home_name}{int(h_shots)}次射门对{away_name}{int(a_shots)}次射门，场面较为开放。")

    # 4. Discipline note
    if h_yellow > 0 or a_yellow > 0 or h_red > 0 or a_red > 0:
        card_parts = []
        if h_yellow > 0:
            card_parts.append(f"{home_name} {int(h_yellow)}张黄牌")
        if a_yellow > 0:
            card_parts.append(f"{away_name} {int(a_yellow)}张黄牌")
        if h_red > 0:
            card_parts.append(f"{home_name} 1张红牌")
        if a_red > 0:
            card_parts.append(f"{away_name} 1张红牌")
        parts.append(f"纪律方面，{'，'.join(card_parts)}，下半场需注意情绪控制。")

    # 5. Second-half outlook
    if home_score > away_score:
        parts.append(f"下半场{away_name}需要加强进攻，{home_name}或将稳固防守寻求反击。")
    elif away_score > home_score:
        parts.append(f"下半场{home_name}必须调整进攻策略，{away_name}有望继续掌控节奏。")
    else:
        parts.append(f"下半场双方都有机会打破僵局，谁能率先破门将占据心理优势。")

    # Star performers
    star_performers = []
    for g in first_half["goals"]:
        star_performers.append(g["player"])

    return {
        "type": "halftime",
        "summary": f"{home_name} {home_score}-{away_score} {away_name}，上半场{'战平' if home_score == away_score else home_name + '领先' if home_score > away_score else away_name + '领先'}",
        "analysis": "\n\n".join(parts),
        "key_stats": key_stats,
        "momentum": _momentum_label(home_score, away_score, h_shots, a_shots, h_poss, a_poss),
        "star_performers": star_performers,
    }


def _fulltime_analysis(events, stats, home_name, away_name, home_score, away_score) -> Dict:
    """Generate fulltime analysis."""
    match_events = _get_event_summary(events)

    # Stats
    h_poss = _get_stat(stats, "home", "possessionPct")
    a_poss = _get_stat(stats, "away", "possessionPct")
    h_shots = _get_stat(stats, "home", "totalShots")
    a_shots = _get_stat(stats, "away", "totalShots")
    h_sot = _get_stat(stats, "home", "shotsOnTarget")
    a_sot = _get_stat(stats, "away", "shotsOnTarget")
    h_corners = _get_stat(stats, "home", "wonCorners")
    a_corners = _get_stat(stats, "away", "wonCorners")
    h_passes = _get_stat(stats, "home", "totalPasses")
    a_passes = _get_stat(stats, "away", "totalPasses")
    h_pass_pct = _get_stat(stats, "home", "passingPct") or _get_stat(stats, "home", "passPct")
    a_pass_pct = _get_stat(stats, "away", "passingPct") or _get_stat(stats, "away", "passPct")
    h_fouls = _get_stat(stats, "home", "foulsCommitted")
    a_fouls = _get_stat(stats, "away", "foulsCommitted")

    # Key stats
    key_stats = []
    if h_poss > 0 or a_poss > 0:
        key_stats.append(f"控球率：{home_name} {h_poss:.0f}% - {a_poss:.0f}% {away_name}")
    key_stats.append(f"射门：{home_name} {int(h_shots)}次（{int(h_sot)}次射正） - {away_name} {int(a_shots)}次（{int(a_sot)}次射正）")
    if h_corners > 0 or a_corners > 0:
        key_stats.append(f"角球：{home_name} {int(h_corners)} - {int(a_corners)} {away_name}")
    key_stats.append(f"比分：{home_name} {home_score} - {away_score} {away_name}")

    # --- Generate analysis ---
    parts = []

    # 1. Result overview
    if home_score > away_score:
        parts.append(f"全场比赛结束，{home_name} {home_score}-{away_score} 战胜{away_name}。")
    elif away_score > home_score:
        parts.append(f"全场比赛结束，{away_name} {away_score}-{home_score} 战胜{home_name}。")
    else:
        parts.append(f"全场比赛结束，{home_name} {home_score}-{away_score} 与{away_name}握手言和。")

    # 2. Goal summary
    if match_events["goals"]:
        goal_parts = []
        for g in match_events["goals"]:
            goal_parts.append(f"第{g['minute']:.0f}分钟{g['player']}为{g['team']}进球")
        parts.append("进球回顾：" + "；".join(goal_parts) + "。")

    # 3. Stats analysis - who deserved to win
    h_xg_like = h_shots * 0.3 + h_sot * 0.7 + h_corners * 0.1
    a_xg_like = a_shots * 0.3 + a_sot * 0.7 + a_corners * 0.1
    deserved = ""
    if abs(h_xg_like - a_xg_like) < 1.0:
        deserved = "从数据来看，双方表现旗鼓相当"
    elif h_xg_like > a_xg_like:
        deserved = f"{home_name}在进攻端创造了更多威胁"
    else:
        deserved = f"{away_name}在进攻端表现更为出色"

    if home_score > away_score:
        parts.append(f"{deserved}，{'结果与场面相符' if h_xg_like >= a_xg_like - 0.5 else '但结果略有运气成分'}。")
    elif away_score > home_score:
        parts.append(f"{deserved}，{'结果与场面相符' if a_xg_like >= h_xg_like - 0.5 else '但结果略有运气成分'}。")
    else:
        parts.append(f"{deserved}，平局是合理的结果。")

    # 4. Tactical observations
    if h_poss > 0 and a_poss > 0:
        if abs(h_poss - a_poss) < 5:
            parts.append("控球率接近，中场争夺贯穿全场。")
        elif h_poss > a_poss:
            vs = h_poss / max(a_poss, 1)
            parts.append(f"{home_name}控球率 {h_poss:.0f}%，{_poss_desc(vs, '控球优势')}。")
        else:
            vs = a_poss / max(h_poss, 1)
            parts.append(f"{away_name}控球率 {a_poss:.0f}%，{_poss_desc(vs, '控球优势')}。")

    # 5. Key turning points
    if match_events["reds"]:
        for r in match_events["reds"]:
            parts.append(f"转折点：第{r['minute']:.0f}分钟{r['player']}被罚下，彻底改变了比赛走势。")
    elif match_events["goals"]:
        # Highlight goals that changed the lead
        score_goals = [g for g in match_events["goals"] if g["minute"] > 45]
        if score_goals:
            key_goal = score_goals[0]
            parts.append(f"下半场第{key_goal['minute']:.0f}分钟{key_goal['player']}的进球成为比赛关键转折。")

    # Star performers
    star_performers = []
    for g in match_events["goals"]:
        star_performers.append(g["player"])
    # Add players who got cards (involved in key moments)
    for y in match_events["yellows"]:
        if y["player"] not in star_performers:
            star_performers.append(y["player"])
    star_performers = star_performers[:5]

    return {
        "type": "fulltime",
        "summary": f"{home_name} {home_score}-{away_score} {away_name}",
        "analysis": "\n\n".join(parts),
        "key_stats": key_stats,
        "momentum": _momentum_label(home_score, away_score, h_shots, a_shots, h_poss, a_poss),
        "star_performers": star_performers,
    }


def _live_analysis(events, stats, home_name, away_name, home_score, away_score) -> Dict:
    """Generate brief in-game analysis."""
    all_events = _get_event_summary(events)

    # Recent events (last 5)
    recent = []
    for g in all_events["goals"][-3:]:
        recent.append(f"⚽ {g['minute']:.0f}' {g['player']} 进球")
    for y in all_events["yellows"][-2:]:
        recent.append(f"🟨 {y['minute']:.0f}' {y['player']} 黄牌")
    for r in all_events["reds"][-2:]:
        recent.append(f"🟥 {r['minute']:.0f}' {r['player']} 红牌")

    h_shots = _get_stat(stats, "home", "totalShots")
    a_shots = _get_stat(stats, "away", "totalShots")
    h_poss = _get_stat(stats, "home", "possessionPct")
    a_poss = _get_stat(stats, "away", "possessionPct")

    parts = []
    if recent:
        parts.append("近期事件：" + " | ".join(recent))
    if h_poss > 0 or a_poss > 0:
        parts.append(f"当前控球：{home_name} {h_poss:.0f}% - {a_poss:.0f}% {away_name}，射门 {int(h_shots)}-{int(a_shots)}")

    key_stats = []
    if h_poss > 0 or a_poss > 0:
        key_stats.append(f"控球率：{home_name} {h_poss:.0f}% - {a_poss:.0f}% {away_name}")
    if h_shots > 0 or a_shots > 0:
        h_sot = _get_stat(stats, "home", "shotsOnTarget")
        a_sot = _get_stat(stats, "away", "shotsOnTarget")
        key_stats.append(f"射门：{home_name} {int(h_shots)}（{int(h_sot)}正） - {away_name} {int(a_shots)}（{int(a_sot)}正）")

    return {
        "type": "live",
        "summary": f"比赛进行中：{home_name} {home_score}-{away_score} {away_name}",
        "analysis": "\n".join(parts) if parts else "比赛正在进行中，暂无关键事件。",
        "key_stats": key_stats,
        "momentum": _momentum_label(home_score, away_score, h_shots, a_shots, h_poss, a_poss),
        "star_performers": [],
    }


def _momentum_label(h_score, a_score, h_shots, a_shots, h_poss, a_poss) -> str:
    """Generate a short momentum label."""
    total_shots = h_shots + a_shots
    if total_shots == 0:
        return "均势"
    h_pct = h_shots / total_shots
    diff = h_score - a_score

    if diff > 1 and h_pct > 0.55:
        return f"主队完全掌控"
    elif diff > 0 and h_pct > 0.5:
        return f"主队稍占上风"
    elif diff < -1 and h_pct < 0.45:
        return f"客队完全掌控"
    elif diff < 0 and h_pct < 0.5:
        return f"客队稍占上风"
    elif abs(h_poss - a_poss) > 10:
        return "场面一边倒"
    else:
        return "势均力敌"


def _poss_desc(ratio: float, base: str) -> str:
    """Describe possession dominance."""
    if ratio > 2.5:
        return f"形成压倒性{base}"
    elif ratio > 1.8:
        return f"拥有明显{base}"
    elif ratio > 1.3:
        return f"占据一定{base}"
    else:
        return f"略有{base}"
