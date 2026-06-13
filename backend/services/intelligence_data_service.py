"""
情报数据服务 — 赛前情报数据层
聚合：赛程、球队状态、伤病、首发预测、天气
支持模拟数据模式用于demo
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import random
import json


class IntelligenceDataService:
    """哨前情报数据服务"""

    def __init__(self, data_dir: str = "data", cache_dir: str = "data/intelligence"):
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._news_cache: Optional[List[Dict]] = None
        self._injury_cache: Dict[str, List[Dict]] = {}

    # ====== 赛程数据 ======

    def get_today_matches(self, date: Optional[str] = None) -> List[Dict]:
        """获取今日赛程及情报概要"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # 从本地数据获取
        matches_path = self.data_dir / "matches.parquet"
        if matches_path.exists():
            df = pd.read_parquet(matches_path)
            matches = []
            for _, row in df.head(8).iterrows():
                matches.append({
                    "match_id": int(row.get("match_id", 0)),
                    "home_team": row["home_team"],
                    "away_team": row["away_team"],
                    "date": str(row.get("match_date", date)),
                    "venue": row.get("venue", "待定"),
                    "intel_summary": self._generate_intel_summary(
                        row["home_team"], row["away_team"]
                    ),
                })
            return matches
        return []

    def _generate_intel_summary(self, home: str, away: str) -> str:
        """生成简短情报摘要"""
        templates = [
            f"{home}近期状态稳定，{away}客场需要关注体能分布",
            f"本场关键在于{home}的中场控制力与{away}的防线稳定性",
            f"关注{home}和{away}的阵容变化，首发名单将有重要信息",
        ]
        return random.choice(templates)

    # ====== 伤病与停赛 ======

    def get_injuries(self, team: str) -> List[Dict]:
        """获取球队伤病/停赛信息"""
        if team in self._injury_cache:
            return self._injury_cache[team]

        # 模拟伤病数据（实际应接入API）
        possible_injuries = [
            {"player": f"{team} 中场核心", "type": "肌肉拉伤", "status": "doubtful",
             "expected_return": "1周内", "impact": "high", "position": "中场"},
            {"player": f"{team} 后卫", "type": "累计黄牌停赛", "status": "out",
             "expected_return": "下轮复出", "impact": "medium", "position": "后卫"},
            {"player": f"{team} 前锋", "type": "轻微撞击", "status": "probable",
             "expected_return": "即将复出", "impact": "low", "position": "前锋"},
        ]

        # 随机选0-2条
        n = random.randint(0, min(2, len(possible_injuries)))
        injuries = random.sample(possible_injuries, n) if n > 0 else []

        self._injury_cache[team] = injuries
        return injuries

    # ====== 首发预测 ======

    def predict_lineup(self, team: str) -> Dict:
        """预测首发阵容（基于历史模式）"""
        formations = ["4-3-3", "4-2-3-1", "3-5-2", "4-4-2", "3-4-3"]
        return {
            "team": team,
            "formation": random.choice(formations),
            "confidence": random.choice(["high", "medium", "low"]),
            "key_changes": [
                "主力框架预计不变",
                "个别位置可能有轮换"
            ],
            "note": "首发预测基于近期比赛模式，实际阵容以赛前1小时公布为准"
        }

    # ====== 天气数据 ======

    def get_weather(self, venue: str = "Unknown") -> Dict:
        """获取比赛天气（可接入open-meteo免费API）"""
        conditions = ["晴", "多云", "小雨", "阴天"]
        return {
            "venue": venue,
            "temperature": f"{random.randint(15, 32)}°C",
            "condition": random.choice(conditions),
            "humidity": f"{random.randint(40, 85)}%",
            "wind": f"{random.randint(5, 25)} km/h",
            "impact_on_match": "天气条件对比赛影响较小" if random.random() > 0.2 else "需关注风力对传球的影响"
        }

    # ====== 新闻聚合 ======

    def get_team_news(self, team: str, limit: int = 5) -> List[Dict]:
        """获取球队相关新闻"""
        # 模拟新闻数据
        templates = [
            {"title": f"{team}主帅赛前发布会：球队状态正佳", "source": "赛前发布会",
             "type": "press", "summary": "主教练在赛前发布会上表示球队备战充分"},
            {"title": f"{team}训练营传来积极信号", "source": "训练报道",
             "type": "training", "summary": "球队训练氛围良好，核心球员状态回升"},
            {"title": f"关注{team}的战术调整", "source": "战术分析",
             "type": "tactical", "summary": "分析师认为本场可能有战术上的新变化"},
        ]
        return templates[:limit]

    def get_breaking_news(self) -> List[Dict]:
        """获取突发事件/临哨快讯"""
        if self._news_cache:
            return self._news_cache

        now = datetime.now().isoformat()
        news = [
            {
                "id": f"bn{random.randint(1000, 9999)}",
                "type": random.choice(["lineup", "injury", "weather", "tactical"]),
                "title": random.choice([
                    "首发名单即将公布",
                    "天气变化可能影响比赛节奏",
                    "赛前热身观察：核心球员状态需关注",
                ]),
                "content": "更多详情将在比赛临近时更新",
                "timestamp": now,
                "urgency": random.choice(["high", "medium", "low"]),
                "verified": random.random() > 0.3,
            }
            for _ in range(random.randint(2, 5))
        ]
        self._news_cache = news
        return news

    # ====== 教练发布会 ======

    def get_press_conference(self, team: str) -> Dict:
        """获取教练赛前发布会摘要"""
        quotes = [
            f"我们对这场比赛做了充分准备，{team}的状态很好",
            "尊重对手，但我们有信心踢出自己的风格",
            "球队目前有一些小伤病需要评估，但整体框架不会有大的变化",
        ]
        return {
            "team": team,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "key_quotes": random.sample(quotes, min(2, len(quotes))),
            "tone": random.choice(["confident", "cautious", "neutral"]),
            "key_info": {
                "injuries_update": "正在评估中",
                "lineup_hints": "基本框架不变，个别位置竞争激烈",
                "tactical_hints": "会针对对手特点做针对性布置",
            }
        }


# 全局实例
intelligence_data_service = IntelligenceDataService()
