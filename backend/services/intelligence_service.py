"""
情报编排服务 — 协调所有情报子服务
统一提供结构化情报数据
"""
from typing import Dict, List, Optional
from datetime import datetime

from .intelligence_data_service import intelligence_data_service
from .sentiment_service import sentiment_service
from .tactics_service import tactics_service
from .knowledge_service import knowledge_service


class IntelligenceService:
    """哨前情报编排中心"""

    def __init__(self):
        self.data = intelligence_data_service
        self.sentiment = sentiment_service

    def build_daily_report(self, date: Optional[str] = None) -> Dict:
        """构建完整的哨前日报"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        matches = self.data.get_today_matches(date)

        # 识别重点比赛
        key_match = matches[0] if matches else None
        key_match_focus = ""
        if key_match:
            key_match_focus = f"{key_match['home_team']} vs {key_match['away_team']}"

        sections = [
            {
                "title": "今日赛程纵览",
                "type": "schedule",
                "content": self._build_schedule_section(matches),
                "priority": "high"
            },
            {
                "title": "重点比赛深度分析",
                "type": "key_match",
                "content": self._build_key_match_section(key_match),
                "priority": "high"
            },
            {
                "title": "关键变量追踪",
                "type": "variables",
                "content": self._build_variables_section(),
                "priority": "medium"
            },
            {
                "title": "舆情热度一览",
                "type": "sentiment",
                "content": self._build_sentiment_section(),
                "priority": "medium"
            },
            {
                "title": "临场提醒",
                "type": "alerts",
                "content": "首发名单公布前请关注临哨快讯，我们将第一时间推送阵容变化信息。",
                "priority": "low"
            }
        ]

        return {
            "date": date,
            "generated_at": datetime.now().isoformat(),
            "total_matches": len(matches),
            "key_match_focus": key_match_focus,
            "sections": sections,
            "summary": f"今日共{len(matches)}场比赛。哨前情报站为您提前解读关键变量，帮助看懂比赛走向。",
            "disclaimer": "本内容仅提供赛事分析参考，不构成任何投注建议"
        }

    def _build_schedule_section(self, matches: List[Dict]) -> str:
        if not matches:
            return "今日暂无比赛安排"
        lines = []
        for m in matches[:6]:
            lines.append(
                f"• {m['home_team']} vs {m['away_team']} | {m.get('venue', '待定')}"
            )
        return "\n".join(lines)

    def _build_key_match_section(self, key_match: Optional[Dict]) -> str:
        if not key_match:
            return "暂无重点比赛"
        return (
            f"本场焦点战: {key_match['home_team']} 对阵 {key_match['away_team']} "
            f"({key_match.get('venue', '')})。\n"
            f"关键看点: {key_match.get('intel_summary', '数据分析中')}"
        )

    def _build_variables_section(self) -> str:
        return (
            "• 阵容完整性: 各队伤病情况更新中\n"
            "• 战术适应性: 基于近期比赛模式的战术预测\n"
            "• 体能储备: 赛程密集期的轮换策略\n"
            "• 天气因素: 比赛日天气预报及影响评估"
        )

    def _build_sentiment_section(self) -> str:
        tournament = self.sentiment.get_tournament_sentiment()
        top = tournament["team_sentiments"][:3]
        lines = [f"关注度最高的三支球队:"]
        for t in top:
            lines.append(
                f"  {t['team']} - 关注度{t['attention_score']}/100 ({t['trend']})"
            )
        return "\n".join(lines)

    def build_intel_card(self, home_team: str, away_team: str,
                         home_elo: float = 1500, away_elo: float = 1500) -> Dict:
        """构建单场比赛的哨前情报卡"""
        home_injuries = self.data.get_injuries(home_team)
        away_injuries = self.data.get_injuries(away_team)
        home_lineup = self.data.predict_lineup(home_team)
        away_lineup = self.data.predict_lineup(away_team)
        press_conf = self.data.get_press_conference(home_team)
        sentiment = self.sentiment.get_match_sentiment(
            home_team=home_team, away_team=away_team
        )

        # ── 真实战术分析 ──────────────────────────
        home_form = home_lineup.get("formation", "4-3-3")
        away_form = away_lineup.get("formation", "4-4-2")

        formation_matchup = tactics_service.analyze_formation_matchup(home_form, away_form)

        # 查找球队战术档案
        home_tactical_profile = self._get_team_tactical_profile(home_team)
        away_tactical_profile = self._get_team_tactical_profile(away_team)

        # 风格对位分析
        style_matchup = None
        if home_tactical_profile and away_tactical_profile:
            home_style = home_tactical_profile.get("primary_style", "")
            away_style = away_tactical_profile.get("primary_style", "")
            if home_style and away_style:
                style_matchup = tactics_service.analyze_style_matchup(home_style, away_style)

        # 构建战术笔记
        tactical_note_home = self._build_tactical_note(
            home_team, home_form, home_tactical_profile, formation_matchup.get("home_advantage_score", 0)
        )
        tactical_note_away = self._build_tactical_note(
            away_team, away_form, away_tactical_profile, -formation_matchup.get("home_advantage_score", 0)
        )

        return {
            "home_team": {
                "name": home_team,
                "elo": home_elo,
                "recent_form": self._assess_form(home_elo),
                "injuries": home_injuries,
                "predicted_lineup": home_lineup,
                "tactical_note": tactical_note_home,
                "tactical_profile": home_tactical_profile,
                "key_player": self._identify_key_player(home_team),
            },
            "away_team": {
                "name": away_team,
                "elo": away_elo,
                "recent_form": self._assess_form(away_elo),
                "injuries": away_injuries,
                "predicted_lineup": away_lineup,
                "tactical_note": tactical_note_away,
                "tactical_profile": away_tactical_profile,
                "key_player": self._identify_key_player(away_team),
            },
            "match_context": {
                "elo_gap": f"{abs(home_elo - away_elo):.0f}",
                "favorite": home_team if home_elo > away_elo else away_team,
                "press_conference_summary": press_conf.get("key_quotes", [])[:1],
            },
            "tactical_matchup": {
                "formation_matchup": {
                    "home_formation": home_form,
                    "away_formation": away_form,
                    "home_advantage_score": formation_matchup.get("home_advantage_score", 0),
                    "key_battle_zones": formation_matchup.get("key_battle_zones", []),
                    "tactical_note": formation_matchup.get("tactical_note", ""),
                    "home_strengths": formation_matchup.get("home_strengths", []),
                    "away_strengths": formation_matchup.get("away_strengths", []),
                    "home_weaknesses": formation_matchup.get("home_weaknesses", []),
                    "away_weaknesses": formation_matchup.get("away_weaknesses", []),
                },
                "style_matchup": style_matchup,
                "interpretation": tactics_service._interpret_advantage(
                    formation_matchup.get("home_advantage_score", 0)
                ),
            },
            "key_variables": self._build_key_variables(home_injuries, away_injuries),
            "sentiment": {
                "attention": sentiment["attention_description"],
                "home_expectation": sentiment["home_expectation"],
                "away_expectation": sentiment["away_expectation"],
            },
            "disclaimer": "本情报卡提供赛前信息汇总，不构成投注建议"
        }

    def _get_team_tactical_profile(self, team: str) -> Optional[Dict]:
        """从球队档案获取战术配置"""
        profile = knowledge_service.get_team_profile(team)
        if profile:
            return profile.get("tactical_profile")
        return None

    def _build_tactical_note(self, team: str, formation: str,
                             tactical_profile: Optional[Dict],
                             advantage_score: float) -> str:
        """构建有实质内容的战术笔记"""
        parts = []

        if tactical_profile:
            style = tactical_profile.get("primary_style", "")
            style_name_map = {
                "tiki_taka": "Tiki-Taka传控", "gegenpressing": "高位压迫",
                "counter_attack": "防守反击", "direct_play": "直接足球",
                "possession_based": "控球型", "wing_play": "边路进攻",
                "low_block": "低位防守", "fluid_attack": "全攻全守",
            }
            style_cn = style_name_map.get(style, style)
            parts.append(f"主打{style_cn}，{formation}阵型")
            parts.append(f"压迫强度{tactical_profile.get('pressing_intensity', '中等')}")
            patterns = tactical_profile.get("key_tactical_patterns", [])
            if patterns:
                parts.append(f"关键战术：{patterns[0]}")
        else:
            parts.append(f"预计采用{formation}阵型")

        if advantage_score > 0.10:
            parts.append("阵型对位有优势")
        elif advantage_score < -0.10:
            parts.append("阵型对位处于劣势")

        return "。".join(parts)

    def _assess_form(self, elo: float) -> str:
        if elo > 1800:
            return "顶级状态，近期表现强势"
        elif elo > 1650:
            return "状态良好，近期战绩稳定"
        elif elo > 1500:
            return "状态中等，有起伏"
        else:
            return "状态待提升，需关注反弹可能性"

    def _identify_key_player(self, team: str) -> str:
        """识别关键球员（模拟）"""
        return f"{team}核心球员 — 本场比赛的关键发挥将直接影响走向"

    def _build_key_variables(self, home_injuries: List, away_injuries: List) -> List[Dict]:
        """构建关键变量清单"""
        variables = [
            {
                "name": "阵容完整性",
                "status": "uncertain" if (home_injuries or away_injuries) else "confirmed",
                "impact": "high",
                "description": "伤病/停赛对两队阵容的影响",
                "home_status": f"{len(home_injuries)}人受影响" if home_injuries else "阵容齐整",
                "away_status": f"{len(away_injuries)}人受影响" if away_injuries else "阵容齐整",
                "trend": "stable"
            },
            {
                "name": "战术适应性",
                "status": "confirmed",
                "impact": "medium",
                "description": "基于历史表现评估两队战术执行力",
                "trend": "stable"
            },
            {
                "name": "体能储备",
                "status": "uncertain",
                "impact": "medium",
                "description": "赛程密度影响球员体能分布",
                "trend": "stable"
            },
            {
                "name": "天气影响",
                "status": "confirmed",
                "impact": "low",
                "description": "比赛日天气条件评估",
                "trend": "stable"
            },
        ]
        return variables

    def build_review(self, match_id: int, home_team: str, away_team: str,
                     home_score: int, away_score: int,
                     pre_match_prediction: Optional[Dict] = None) -> Dict:
        """构建哨后复盘"""
        # 判定预测准确度
        if pre_match_prediction:
            pred_home = pre_match_prediction.get("home_win", 0.33)
            pred_away = pre_match_prediction.get("away_win", 0.33)
            if home_score > away_score:
                prediction_correct = pred_home > pred_away
            elif away_score > home_score:
                prediction_correct = pred_away > pred_home
            else:
                prediction_correct = abs(pred_home - pred_away) < 0.1
        else:
            prediction_correct = None

        return {
            "match_id": match_id,
            "home_team": home_team,
            "away_team": away_team,
            "final_score": f"{home_score} - {away_score}",
            "pre_match_expectation": (
                f"赛前预测{'正确' if prediction_correct else '有偏差'}"
                if prediction_correct is not None else "赛前预测数据缺失"
            ),
            "variable_verification": [
                {
                    "variable": "阵容完整性",
                    "pre_match_assessment": "赛前评估",
                    "actual_impact": "实际影响分析",
                    "verified": True,
                    "analysis": "阵容变化对比赛的影响需要在赛后详细评估"
                }
            ],
            "key_turning_points": [
                "比赛关键转折点分析",
                "战术调整的关键时刻"
            ],
            "model_accuracy_note": (
                "模型预测方向正确" if prediction_correct
                else "模型预测需要进一步优化" if prediction_correct is not None
                else "等待模型评估"
            ),
            "summary": "哨后复盘通过对比赛前变量与比赛实际进程，验证赛前情报的有效性。",
            "disclaimer": "复盘分析仅用于模型优化参考，不构成任何投注建议"
        }


# 全局实例
intelligence_service = IntelligenceService()
