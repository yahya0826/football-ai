"""
每日比赛总结服务 — 所有比赛结束后用 DeepSeek 生成比赛日总结文章
定时检测 → 自动生成 → 永久保存
"""
import os
import json
import re
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from pathlib import Path
from openai import OpenAI

from .live_match_service import TEAM_NAMES_CN

DATA_DIR = Path(__file__).parent.parent / "data" / "intelligence" / "daily_summaries"
SCHEDULE_PATH = Path(__file__).parent.parent / "data" / "schedule_2026.json"
BEIJING_TZ = timezone(timedelta(hours=8))
DATA_DIR.mkdir(parents=True, exist_ok=True)


class DailySummaryService:
    """比赛日总结生成器"""

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        self.client = OpenAI(api_key=api_key) if api_key else None
        if self.client:
            self.client.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("AI_MODEL", "deepseek-chat")
        self._memory_cache: Dict[str, Dict] = {}

    # ── public API ────────────────────────────────────────────

    def get_daily_summary(self, date: str = None) -> Dict:
        """获取指定日期的比赛总结。未生成则尝试生成，未全部结束则返回进度。"""
        if date is None:
            date = self._today_bj()

        # 先从持久缓存读取
        cache_file = DATA_DIR / f"{date}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                if self._is_valid_summary_cache(date, cached):
                    return cached
            except Exception:
                pass

        # 尝试生成
        result = self.check_and_generate(date)

        if result:
            return result

        # 尚未全部结束，返回进度
        matches = self._get_schedule_day_matches(date)
        total = len(matches)
        completed = sum(1 for m in matches
                       if m.get("state", "") == "finished")

        # 格式化中文日期
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            month = dt.month
            day = dt.day
            date_cn = f"{month}月{day}日"
        except Exception:
            date_cn = date

        return {
            "date": date,
            "date_cn": date_cn,
            "title": f"{date_cn}世界杯比赛总结",
            "generated": False,
            "matches_total": total,
            "matches_completed": completed,
        }

    def check_and_generate(self, date: str = None) -> Optional[Dict]:
        """检查是否所有比赛结束，是则生成总结。返回生成结果或 None。"""
        if date is None:
            date = self._today_bj()

        # 检查是否已生成
        cache_file = DATA_DIR / f"{date}.json"
        if cache_file.exists():
            return None  # 已生成，不重复

        matches = self._get_schedule_day_matches(date)

        if not matches:
            return None

        # 检查所有比赛是否结束
        all_finished = all(
            m.get("state", "") == "finished"
            for m in matches
        )

        if not all_finished:
            return None

        # 全部结束 → 生成总结
        return self._generate_summary(date, matches)

    def get_all_summaries(self) -> List[Dict]:
        """获取所有已生成的总结列表"""
        summaries = []
        for f in sorted(DATA_DIR.glob("*.json"), reverse=True):
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    if data.get("generated"):
                        summaries.append({
                            "date": data.get("date", ""),
                            "title": data.get("title", ""),
                            "matches_count": data.get("matches_count", 0),
                            "generated_at": data.get("generated_at", ""),
                        })
            except Exception:
                continue
        return summaries[:30]

    def check_and_generate(self, date: str = None) -> Optional[Dict]:
        """Generate a persisted summary only for product schedule matches."""
        if date is None:
            date = self._today_bj()

        cached = self._load_summary_cache(date)
        if cached and self._is_valid_summary_cache(date, cached):
            return None

        matches = self._get_schedule_day_matches(date)
        if not matches:
            return None

        all_finished = all(m.get("state", "") == "finished" for m in matches)
        if not all_finished:
            return None

        return self._generate_summary(date, matches)

    # ── internal ──────────────────────────────────────────────

    @staticmethod
    def _today_bj() -> str:
        return datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")

    def _load_schedule_matches(self, date: str) -> List[Dict]:
        if not SCHEDULE_PATH.exists():
            return []
        try:
            data = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
        return [
            m for m in data.get("matches", [])
            if m.get("date") == date and not self._is_placeholder_match(m)
        ]

    @staticmethod
    def _is_placeholder_match(match: Dict) -> bool:
        if match.get("stage") == "group":
            return False
        teams = [match.get("home_team", ""), match.get("away_team", "")]
        return any(any(ch.isdigit() for ch in team) or "/" in team for team in teams)

    def _get_schedule_day_matches(self, date: str) -> List[Dict]:
        """Return only product schedule matches for a Beijing match day, enriched with ESPN status."""
        from .live_match_service import live_match_service

        schedule_matches = self._load_schedule_matches(date)
        result: List[Dict] = []

        for match in schedule_matches:
            home = match.get("home_team", "")
            away = match.get("away_team", "")
            item = {
                "match_id": match.get("match_id"),
                "schedule_match_id": match.get("match_id"),
                "home_team": home,
                "away_team": away,
                "home_team_cn": match.get("home_team_cn") or TEAM_NAMES_CN.get(home, home),
                "away_team_cn": match.get("away_team_cn") or TEAM_NAMES_CN.get(away, away),
                "home_score": 0,
                "away_score": 0,
                "state": "scheduled",
                "date": match.get("date", date),
                "time_bj": match.get("time_bj", ""),
                "stage": match.get("stage", ""),
                "group": match.get("group", ""),
            }

            espn_id = live_match_service.find_match_by_teams(home, away, date)
            if espn_id:
                detail = live_match_service.get_match_detail(espn_id)
                if detail:
                    item.update({
                        "match_id": espn_id,
                        "espn_match_id": espn_id,
                        "home_score": int(detail.get("home", {}).get("score", 0) or 0),
                        "away_score": int(detail.get("away", {}).get("score", 0) or 0),
                        "state": detail.get("status", {}).get("state", "scheduled"),
                        "date_bj": detail.get("date_bj", date),
                    })

            result.append(item)

        return result

    @staticmethod
    def _load_summary_cache(date: str) -> Optional[Dict]:
        cache_file = DATA_DIR / f"{date}.json"
        if not cache_file.exists():
            return None
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def _is_valid_summary_cache(self, date: str, data: Dict) -> bool:
        if not data.get("generated"):
            return True
        schedule_count = len(self._load_schedule_matches(date))
        return (
            data.get("source") == "schedule_2026"
            and data.get("matches_count") == schedule_count
        )

    def _generate_summary(self, date: str, matches: List[Dict]) -> Dict:
        """生成比赛日总结文章"""
        # 格式化中文日期
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            month = dt.month
            day = dt.day
            date_cn = f"{month}月{day}日"
        except Exception:
            date_cn = date

        # 收集每场比赛的终场分析
        match_summaries = []
        for m in matches:
            home = m.get("home_team", "")
            away = m.get("away_team", "")
            home_cn = TEAM_NAMES_CN.get(home, home)
            away_cn = TEAM_NAMES_CN.get(away, away)
            home_score = m.get("home_score", "?")
            away_score = m.get("away_score", "?")

            # 尝试获取更详细的终场分析
            analysis_text = ""
            match_id = m.get("match_id", "")
            if match_id:
                analysis_text = self._get_match_analysis(match_id)

            match_summaries.append({
                "home_team": home,
                "home_team_cn": home_cn,
                "away_team": away,
                "away_team_cn": away_cn,
                "score": f"{home_score}-{away_score}",
                "analysis": analysis_text,
            })

        # 构建 DeepSeek prompt
        match_lines = []
        for ms in match_summaries:
            lines = [f"## {ms['home_team_cn']} vs {ms['away_team_cn']}"]
            lines.append(f"比分：{ms['score']}")
            if ms['analysis']:
                lines.append(f"终场分析：{ms['analysis']}")
            match_lines.append("\n".join(lines))

        prompt = f"""你是世界杯比赛日总结编辑。请根据以下比赛日全部比赛的数据和分析，撰写一篇中文比赛日总结文章（500-800字）。

比赛日：{date_cn}
今日共 {len(match_summaries)} 场比赛：

{chr(10).join(match_lines)}

要求：
1. 标题格式："{date_cn}世界杯比赛总结"
2. 开头概述今日赛况，点出最精彩/最意外的比赛（1-2段）
3. 每场比赛独立成段，包含：比分、关键球员表现、比赛走势和高光时刻
4. 结尾总结今日亮点，可简要提及后续赛程
5. 语言生动专业，面向中国球迷，有现场感
6. 不能照搬终场分析原文，要进行变化、丰富和重写
7. 不提及任何盘口、赔率、投注相关内容
8. 使用 Markdown 格式（## 小标题，**加粗**重点）"""

        # 生成
        article = ""
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是世界杯比赛日总结编辑，擅长撰写生动专业的赛事回顾文章。面向中国球迷，语言简洁有力。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                )
                article = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[DailySummary] AI generation failed: {e}")
                article = self._fallback_summary(date_cn, match_summaries)
        else:
            article = self._fallback_summary(date_cn, match_summaries)

        # 从生成的文章中提取标题
        title = f"{date_cn}世界杯比赛总结"
        title_match = re.match(r'#+\s*(.+?)(?:\n|$)', article)
        if title_match:
            title = title_match.group(1).strip()

        result = {
            "date": date,
            "title": title,
            "date_cn": date_cn,
            "source": "schedule_2026",
            "matches_count": len(match_summaries),
            "matches": match_summaries,
            "article": article,
            "generated_at": datetime.now().isoformat(),
            "generated": True,
        }

        # 持久保存
        cache_file = DATA_DIR / f"{date}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"[DailySummary] Generated and saved summary for {date}: {title}")
        return result

    def _get_match_analysis(self, match_id: str) -> str:
        """获取比赛的终场分析文本"""
        try:
            from .live_match_service import live_match_service
            from .match_analysis_service import analyze_match

            detail = live_match_service.get_match_detail(match_id)
            if not detail:
                return ""

            home_id = detail.get("home", {}).get("team_id", "")
            away_id = detail.get("away", {}).get("team_id", "")
            analysis = analyze_match(detail, home_id, away_id)

            return analysis.get("analysis", "")
        except Exception as e:
            print(f"[DailySummary] Failed to get analysis for {match_id}: {e}")
            return ""

    def _fallback_summary(self, date_cn: str, match_summaries: List[Dict]) -> str:
        """备用总结（无 AI 时）"""
        lines = [f"# {date_cn}世界杯比赛总结\n"]
        lines.append(f"{date_cn}世界杯共进行了{len(match_summaries)}场比赛。\n")

        for ms in match_summaries:
            lines.append(
                f"## {ms['home_team_cn']} vs {ms['away_team_cn']}\n\n"
                f"最终比分 **{ms['score']}**。\n"
            )
            if ms['analysis']:
                lines.append(f"{ms['analysis'][:300]}\n")

        lines.append("\n> 本总结由 AI 自动生成，仅供参考。")
        return "\n\n".join(lines)


# 全局实例
daily_summary_service = DailySummaryService()
