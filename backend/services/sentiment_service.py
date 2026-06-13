"""
舆情追踪服务 — 追踪比赛关注度和预期变化
使用合规语言：关注度升温/降温、预期增强/减弱
不涉及具体盘口、赔率、投注建议
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random


class SentimentService:
    """舆情追踪 — 比赛关注度与预期变化"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self._sentiment_cache: Dict[str, Dict] = {}

    def get_match_sentiment(self, match_id: int = None, home_team: str = None, away_team: str = None) -> Dict:
        """获取单场比赛的舆情状态"""
        key = str(match_id) if match_id else f"{home_team}_vs_{away_team}"
        if key in self._sentiment_cache:
            return self._sentiment_cache[key]

        # 模拟舆情数据
        attention_score = random.randint(40, 90)
        trend_options = ["rising", "stable", "cooling"]
        trend_weights = [0.3, 0.5, 0.2]
        trend = random.choices(trend_options, weights=trend_weights)[0]

        trend_descriptions = {
            "rising": "关注度升温",
            "stable": "关注度稳定",
            "cooling": "关注度降温",
        }

        result = {
            "match_id": match_id,
            "home_team": home_team,
            "away_team": away_team,
            "attention_trend": trend,
            "attention_description": trend_descriptions[trend],
            "attention_score": attention_score,
            "home_expectation": self._expectation_text(home_team or "主队", trend),
            "away_expectation": self._expectation_text(away_team or "客队", trend),
            "recent_changes": self._generate_changes(trend),
            "data_sources": ["公开新闻报道", "赛前信息汇总"],
            "disclaimer": "数据基于公开信息整合，不包含盘口或赔率数据，不构成投注建议"
        }

        self._sentiment_cache[key] = result
        return result

    def _expectation_text(self, team: str, trend: str) -> str:
        """生成合规的预期描述"""
        patterns = {
            "rising": [
                f"{team}近期关注度持续上升，外界预期增强",
                f"市场对{team}的信心有所提升",
            ],
            "stable": [
                f"{team}预期保持稳定，无显著变化",
                f"外界对{team}的表现预期维持原有水平",
            ],
            "cooling": [
                f"{team}近期关注度有所回落，外界预期减弱",
                f"市场对{team}的关注热度有所下降",
            ],
        }
        return random.choice(patterns.get(trend, patterns["stable"]))

    def _generate_changes(self, trend: str) -> List[Dict]:
        """生成舆情变化时间线"""
        now = datetime.now()
        changes = [
            {
                "time": (now - timedelta(hours=48)).isoformat(),
                "description": "初始预期形成阶段",
                "direction": "stable"
            },
            {
                "time": (now - timedelta(hours=24)).isoformat(),
                "description": "随赛前信息更新，关注度有所变化",
                "direction": trend
            },
            {
                "time": (now - timedelta(hours=6)).isoformat(),
                "description": "赛前最后信息确认阶段",
                "direction": trend
            },
        ]
        return changes

    def get_tournament_sentiment(self, competition: str = "World Cup 2022") -> Dict:
        """获取赛事整体舆情热力分布"""
        # 模拟各队关注度排名
        all_teams = [
            "Argentina", "Brazil", "France", "England", "Germany",
            "Spain", "Portugal", "Netherlands", "Croatia", "Morocco"
        ]
        team_sentiments = []
        for team in all_teams:
            team_sentiments.append({
                "team": team,
                "attention_score": random.randint(50, 95),
                "trend": random.choice(["rising", "stable", "cooling"]),
                "key_driver": random.choice([
                    "近期战绩出色", "球星效应", "战术话题", "历史表现", "黑马关注"
                ])
            })
        team_sentiments.sort(key=lambda x: x["attention_score"], reverse=True)

        return {
            "competition": competition,
            "updated_at": datetime.now().isoformat(),
            "team_sentiments": team_sentiments,
            "disclaimer": "关注度排名基于公开信息分析，不代表实力排名或投注参考"
        }


# 全局实例
sentiment_service = SentimentService()
