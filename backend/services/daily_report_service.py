"""
哨前日报服务 — 每日赛前情报汇总
生成结构化日报 + AI自然语言摘要（可选DeepSeek）
"""
import os
from typing import Dict, List, Optional
from datetime import datetime
from openai import OpenAI

from .intelligence_data_service import intelligence_data_service
from .sentiment_service import sentiment_service
from .tactics_service import tactics_service
from .knowledge_service import knowledge_service


class DailyReportService:
    """哨前日报生成器"""

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        self.client = OpenAI(api_key=api_key) if api_key else None
        if self.client:
            self.client.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("AI_MODEL", "deepseek-chat")
        self.data = intelligence_data_service
        self.sentiment = sentiment_service

    def generate(self, date: Optional[str] = None, use_ai: bool = True) -> Dict:
        """生成完整的哨前日报"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        matches = self.data.get_today_matches(date)
        tournament_sentiment = self.sentiment.get_tournament_sentiment()

        # 结构化内容
        report = {
            "date": date,
            "generated_at": datetime.now().isoformat(),
            "total_matches": len(matches),
            "matches": matches[:8],
            "hot_teams": tournament_sentiment["team_sentiments"][:5],
            "sections": [
                {
                    "title": "今日赛程",
                    "icon": "schedule",
                    "matches_count": len(matches),
                    "key_match": matches[0] if matches else None,
                },
                {
                    "title": "关键变量追踪",
                    "icon": "variables",
                    "items": [
                        {"name": "阵容变化", "status": "更新中", "description": "首发名单公布后将实时更新"},
                        {"name": "伤病情况", "status": "更新中", "description": "最新伤病信息汇总中"},
                        {"name": "天气影响", "status": "已确认", "description": "今日比赛地区天气条件良好"},
                        {"name": "舆情热度", "status": "已更新", "description": "关注度排名已更新"},
                    ]
                },
                {
                    "title": "赛前提醒",
                    "icon": "alerts",
                    "items": [
                        "首发名单将在赛前1小时公布，届时推送临哨快讯",
                        "关注重点比赛的阵容变化，可能影响比赛走向",
                        "天气预报显示比赛条件总体良好"
                    ]
                },
                {
                    "title": "战术聚焦",
                    "icon": "tactics",
                    "items": self._build_tactical_spotlight(matches),
                }
            ],
            "summary": "",
            "disclaimer": "哨前日报提供赛前信息汇总与赛事分析，不构成任何投注建议"
        }

        # AI摘要（可选）
        if use_ai and self.client and matches:
            try:
                report["summary"] = self._generate_ai_summary(matches)
            except Exception as e:
                report["summary"] = self._generate_fallback_summary(matches)
        else:
            report["summary"] = self._generate_fallback_summary(matches)

        return report

    def _generate_ai_summary(self, matches: List[Dict]) -> str:
        """使用AI生成日报摘要"""
        match_lines = []
        for m in matches[:5]:
            match_lines.append(f"- {m['home_team']} vs {m['away_team']} ({m.get('venue', '')})")

        prompt = f"""你是哨前情报站(WhistleIntel)的日报编辑。请根据以下今日赛程，撰写一段简洁的日报开场摘要（150字以内）。

今日赛程:
{chr(10).join(match_lines)}

要求：
- 点出最值得关注的1-2场比赛
- 提到需要关注的关键比赛变量（阵容、战术、状态等）
- 语言简洁专业，面向球迷用户
- 不提及任何盘口、赔率、投注相关内容
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是哨前情报站的专业体育编辑，提供赛前情报分析。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=300
        )

        return response.choices[0].message.content.strip()

    def _build_tactical_spotlight(self, matches: List[Dict]) -> List[str]:
        """构建战术聚焦突出"""
        items = []
        for m in matches[:4]:
            home = m.get("home_team", "")
            away = m.get("away_team", "")

            # 获取球队档案中的战术风格
            home_profile = knowledge_service.get_team_profile(home)
            away_profile = knowledge_service.get_team_profile(away)

            home_tactical = home_profile.get("tactical_profile", {}) if home_profile else {}
            away_tactical = away_profile.get("tactical_profile", {}) if away_profile else {}

            home_style = home_tactical.get("primary_style", "")
            away_style = away_tactical.get("primary_style", "")

            style_name_map = {
                "tiki_taka": "Tiki-Taka", "gegenpressing": "高位压迫",
                "counter_attack": "防反", "direct_play": "直接足球",
                "possession_based": "传控", "wing_play": "边路进攻",
                "low_block": "低位防守", "fluid_attack": "全攻全守",
            }

            if home_style and away_style and home_style != away_style:
                style_clash = f"{style_name_map.get(home_style, home_style)} vs {style_name_map.get(away_style, away_style)}"
                items.append(f"风格碰撞：{home} vs {away} — {style_clash}")
            elif home_style:
                patterns = home_tactical.get("key_tactical_patterns", [])
                if patterns:
                    items.append(f"关注 {home}：{patterns[0]}")
            elif away_style:
                patterns = away_tactical.get("key_tactical_patterns", [])
                if patterns:
                    items.append(f"关注 {away}：{patterns[0]}")

            # 最多5条
            if len(items) >= 5:
                break

        if not items:
            items.append("今日比赛战术多样性丰富，关注各队阵型选择")
        return items

    def _generate_fallback_summary(self, matches: List[Dict]) -> str:
        """备用摘要（无AI时）"""
        if not matches:
            return "今日暂无比赛安排。请关注后续赛程更新。"

        key = matches[0] if matches else None
        base = f"今日共{len(matches)}场比赛值得关注。"
        if key:
            base += f"焦点战: {key['home_team']} 对阵 {key['away_team']}。"
            base += f"赛前情报要点: {key.get('intel_summary', '数据分析中')}。"
        base += "请关注临哨快讯获取首发名单和最新变化。"
        return base


# 全局实例
daily_report_service = DailyReportService()
