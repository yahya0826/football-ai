"""
哨前情报卡服务 — 单场比赛结构化分析
生成包含阵容、战术、伤病、变量追踪的情报卡
"""
import os
from typing import Dict, List, Optional
from openai import OpenAI

from .intelligence_data_service import intelligence_data_service
from .sentiment_service import sentiment_service
from .tactics_service import tactics_service
from .knowledge_service import knowledge_service


class IntelCardService:
    """哨前情报卡生成器"""

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        self.client = OpenAI(api_key=api_key) if api_key else None
        if self.client:
            self.client.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("AI_MODEL", "deepseek-chat")
        self.data = intelligence_data_service
        self.sentiment = sentiment_service

    def generate(self, home_team: str, away_team: str,
                 home_elo: float = 1500, away_elo: float = 1500) -> Dict:
        """生成完整的哨前情报卡"""
        home_injuries = self.data.get_injuries(home_team)
        away_injuries = self.data.get_injuries(away_team)
        home_lineup = self.data.predict_lineup(home_team)
        away_lineup = self.data.predict_lineup(away_team)
        match_sentiment = self.sentiment.get_match_sentiment(
            home_team=home_team, away_team=away_team
        )
        home_news = self.data.get_team_news(home_team, limit=3)
        away_news = self.data.get_team_news(away_team, limit=3)

        # ── 真实战术分析 ──────────────────────────
        home_form = home_lineup.get("formation", "4-3-3")
        away_form = away_lineup.get("formation", "4-4-2")
        formation_matchup = tactics_service.analyze_formation_matchup(home_form, away_form)

        home_tactical = self._get_tactical_profile(home_team)
        away_tactical = self._get_tactical_profile(away_team)
        home_style = self._infer_style_from_profile(home_tactical, home_form, home_elo)
        away_style = self._infer_style_from_profile(away_tactical, away_form, away_elo)

        # 风格对位
        style_matchup = None
        if home_style.get("style_id") and away_style.get("style_id"):
            style_matchup = tactics_service.analyze_style_matchup(
                home_style["style_id"], away_style["style_id"]
            )

        card = {
            "match": f"{home_team} vs {away_team}",
            "home_team": {
                "name": home_team,
                "elo": home_elo,
                "recent_form": self._assess_form(home_elo),
                "style": home_style,
                "injuries": home_injuries,
                "predicted_lineup": home_lineup,
                "tactical_profile": home_tactical,
                "recent_news": home_news,
                "key_player_assessment": self._identify_key_player(home_team),
            },
            "away_team": {
                "name": away_team,
                "elo": away_elo,
                "recent_form": self._assess_form(away_elo),
                "style": away_style,
                "injuries": away_injuries,
                "predicted_lineup": away_lineup,
                "tactical_profile": away_tactical,
                "recent_news": away_news,
                "key_player_assessment": self._identify_key_player(away_team),
            },
            "match_context": {
                "elo_gap": f"{abs(home_elo - away_elo):.0f}",
                "elo_gap_description": self._describe_elo_gap(home_elo, away_elo),
                "style_clash": f"{home_style.get('style', '未知')} vs {away_style.get('style', '未知')}",
                "favorite": home_team if home_elo > away_elo + 30 else (
                    away_team if away_elo > home_elo + 30 else "实力接近"
                ),
            },
            "tactical_analysis": {
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
                    "interpretation": tactics_service._interpret_advantage(
                        formation_matchup.get("home_advantage_score", 0)
                    ),
                },
                "style_matchup": style_matchup,
            },
            "key_variables": self._build_variables(home_injuries, away_injuries),
            "sentiment": match_sentiment,
            "status": "draft",
            "disclaimer": "哨前情报卡提供赛前信息汇总，不构成任何投注建议"
        }

        return card

    def _get_tactical_profile(self, team: str) -> Optional[Dict]:
        profile = knowledge_service.get_team_profile(team)
        if profile:
            return profile.get("tactical_profile")
        return None

    def _infer_style_from_profile(self, tactical_profile: Optional[Dict],
                                   formation: str, elo: float) -> Dict:
        """基于球队档案+阵型推断战术风格"""
        if tactical_profile:
            style_id = tactical_profile.get("primary_style", "")
            style_name_map = {
                "tiki_taka": "Tiki-Taka传控", "gegenpressing": "高位压迫",
                "counter_attack": "防守反击", "direct_play": "直接足球",
                "possession_based": "控球型", "wing_play": "边路进攻",
                "low_block": "低位防守", "fluid_attack": "全攻全守",
            }
            secondary = tactical_profile.get("secondary_styles", [])
            secondary_cn = [style_name_map.get(s, s) for s in secondary]

            strengths = []
            patterns = tactical_profile.get("key_tactical_patterns", [])
            if patterns:
                strengths = patterns[:2]

            weaknesses = []
            if tactical_profile.get("pressing_intensity") == "high":
                weaknesses.append("高位防线可能被速度反击打穿")
            if len(tactical_profile.get("formation_flexibility", [])) <= 2:
                weaknesses.append("阵型变化选项有限")

            return {
                "formation": formation,
                "style": style_name_map.get(style_id, style_id),
                "style_id": style_id,
                "secondary_styles": secondary_cn,
                "strengths": strengths,
                "weaknesses": weaknesses if weaknesses else ["战术表现需比赛验证"],
                "pressing_intensity": tactical_profile.get("pressing_intensity", "medium"),
                "defensive_line": tactical_profile.get("defensive_line", "medium"),
                "build_up_style": tactical_profile.get("build_up_style", ""),
                "key_patterns": patterns,
            }

        # 回退方案：基于ELO+阵型的粗略推断
        return self._infer_style_fallback(elo, formation)

    def _infer_style_fallback(self, elo: float, formation: str) -> Dict:
        """无球队档案时的回退推断"""
        if "4-3-3" in formation:
            base_style = "possession_based" if elo > 1650 else "counter_attack"
        elif "3-5-2" in formation or "3-4-3" in formation:
            base_style = "wing_play"
        elif "4-2-3-1" in formation:
            base_style = "possession_based"
        elif "4-4-2" in formation:
            base_style = "direct_play"
        elif "5-4-1" in formation or "5-3-2" in formation:
            base_style = "low_block"
        else:
            base_style = "possession_based"

        style_name_map = {
            "possession_based": "控球型", "counter_attack": "防守反击",
            "wing_play": "边路进攻", "direct_play": "直接足球",
            "low_block": "低位防守",
        }

        return {
            "formation": formation,
            "style": style_name_map.get(base_style, base_style),
            "style_id": base_style,
            "strength": "中场控制力强" if elo > 1650 else "防守组织严密",
            "weakness": "高位防线有风险" if elo > 1650 else "进攻效率需提升",
        }

    def _assess_form(self, elo: float) -> str:
        if elo > 1800:
            return "顶级"
        elif elo > 1650:
            return "优秀"
        elif elo > 1500:
            return "良好"
        else:
            return "一般"

    def _describe_elo_gap(self, home_elo: float, away_elo: float) -> str:
        gap = abs(home_elo - away_elo)
        if gap < 30:
            return "两队实力非常接近"
        elif gap < 80:
            return "存在一定实力差距"
        elif gap < 150:
            return "实力差距较为明显"
        else:
            return "实力差距显著"

    def _identify_key_player(self, team: str) -> str:
        return f"{team}的核心球员发挥将是本场关键变量之一"

    def _build_variables(self, home_injuries: List, away_injuries: List) -> List[Dict]:
        return [
            {
                "name": "阵容完整性",
                "status": "uncertain" if home_injuries or away_injuries else "confirmed",
                "impact": "high",
                "description": "伤病/停赛对两队阵容配置的影响",
                "home_detail": f"主队{len(home_injuries)}人受影响" if home_injuries else "主队阵容齐整",
                "away_detail": f"客队{len(away_injuries)}人受影响" if away_injuries else "客队阵容齐整",
                "trend": "stable",
            },
            {
                "name": "战术匹配度",
                "status": "confirmed",
                "impact": "high",
                "description": "两队战术风格的对位分析",
                "trend": "stable",
            },
            {
                "name": "体能状况",
                "status": "uncertain",
                "impact": "medium",
                "description": "赛程密集度对球员体能的影响评估",
                "trend": "stable",
            },
            {
                "name": "心理因素",
                "status": "uncertain",
                "impact": "medium",
                "description": "关键比赛的心理压力和战意评估",
                "trend": "stable",
            },
        ]


# 全局实例
intel_card_service = IntelCardService()
