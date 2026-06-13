"""
临哨快讯服务 — 突发伤病/首发变化/天气变化检测与推送
"""
import os
from typing import Dict, List, Optional
from datetime import datetime
import random
import json
from pathlib import Path


class BreakingNewsService:
    """临哨快讯检测与生成器"""

    def __init__(self, data_dir: str = "data/intelligence"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._news_cache: List[Dict] = []
        self._archived_news: List[Dict] = self._load_archived()

    def _load_archived(self) -> List[Dict]:
        path = self.data_dir / "breaking_news_archive.json"
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []

    def _save_archived(self):
        path = self.data_dir / "breaking_news_archive.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._archived_news[-100:], f, ensure_ascii=False, indent=2)

    def get_latest(self, limit: int = 10) -> List[Dict]:
        """获取最新临哨快讯"""
        if not self._news_cache:
            self._news_cache = self._generate_mock_news()

        return self._news_cache[:limit]

    def get_by_match(self, match_id: int) -> List[Dict]:
        """获取指定比赛的快讯"""
        all_news = self.get_latest(limit=50)
        return [n for n in all_news if n.get("match_id") == match_id]

    def get_by_urgency(self, urgency: str = "high") -> List[Dict]:
        """按紧急程度筛选"""
        all_news = self.get_latest(limit=50)
        return [n for n in all_news if n.get("urgency") == urgency]

    def _generate_mock_news(self) -> List[Dict]:
        """生成模拟临哨快讯"""
        now = datetime.now().isoformat()

        templates = [
            {
                "type": "lineup",
                "urgency": "high",
                "title": "首发名单公布",
                "content": "两队首发名单已经公布。主队排出预期阵型，客队有一处令人关注的变化。详细阵容分析请查看情报卡。",
            },
            {
                "type": "injury",
                "urgency": "high",
                "title": "赛前伤病更新",
                "content": "赛前最后检查确认，关键球员通过体能测试，可以出战本场比赛。这对球队战术安排是重要正面信号。",
            },
            {
                "type": "weather",
                "urgency": "low",
                "title": "天气条件确认",
                "content": "比赛时间段天气条件良好，温度适宜，对比赛节奏和球员体能不会产生额外影响。",
            },
            {
                "type": "tactical",
                "urgency": "medium",
                "title": "赛前热身观察",
                "content": "从赛前热身观察，主队可能排出更具攻击性的阵容。客队则延续防守反击的基本框架。",
            },
            {
                "type": "lineup",
                "urgency": "medium",
                "title": "阵容变动提示",
                "content": "据赛前消息，客队中场位置可能有战术调整，一名技术型球员取代了原有的防守型中场。这将影响中场的控球平衡。",
            },
        ]

        news_items = []
        for i, tpl in enumerate(templates):
            item = {
                "id": f"bn{random.randint(10000, 99999)}",
                "match_id": random.randint(1, 64),
                "type": tpl["type"],
                "urgency": tpl["urgency"],
                "title": tpl["title"],
                "content": tpl["content"],
                "timestamp": now,
                "verified": random.random() > 0.2,
                "source": random.choice(["赛前发布会", "球队官方", "现场记者", "数据分析"]),
            }
            news_items.append(item)

        return news_items

    def archive_news(self, news_item: Dict):
        """归档一条快讯"""
        news_item["archived_at"] = datetime.now().isoformat()
        self._archived_news.append(news_item)
        if len(self._archived_news) > 200:
            self._archived_news = self._archived_news[-100:]
        self._save_archived()

    def clear_cache(self):
        """清除内存缓存"""
        self._news_cache = []

    def generate_summary(self, match_id: int) -> Dict:
        """为一场比赛生成快讯摘要"""
        news = self.get_by_match(match_id)
        high_urgency = [n for n in news if n["urgency"] == "high"]
        medium_urgency = [n for n in news if n["urgency"] == "medium"]

        return {
            "match_id": match_id,
            "total_alerts": len(news),
            "high_urgency_count": len(high_urgency),
            "latest_alert": news[0] if news else None,
            "key_changes": [
                n["title"] for n in high_urgency + medium_urgency[:2]
            ],
            "disclaimer": "快讯基于公开信息，具体以官方确认为准"
        }


# 全局实例
breaking_news_service = BreakingNewsService()
