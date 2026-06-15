"""
每日比赛总结服务 — 所有比赛结束后用 DeepSeek 生成比赛日总结文章
定时检测 → 自动生成 → 永久保存
"""
import os
import json
import re
import time
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from openai import OpenAI

from .live_match_service import TEAM_NAMES_CN

DATA_DIR = Path(__file__).parent.parent / "data" / "intelligence" / "daily_summaries"
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
            date = datetime.now().strftime("%Y-%m-%d")

        # 先从持久缓存读取
        cache_file = DATA_DIR / f"{date}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

        # 尝试生成
        result = self.check_and_generate(date)

        if result:
            return result

        # 尚未全部结束，返回进度
        from .live_match_service import live_match_service
        matches = live_match_service.get_today_matches(date)
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
            date = datetime.now().strftime("%Y-%m-%d")

        # 检查是否已生成
        cache_file = DATA_DIR / f"{date}.json"
        if cache_file.exists():
            return None  # 已生成，不重复

        from .live_match_service import live_match_service
        matches = live_match_service.get_today_matches(date)

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

    # ── internal ──────────────────────────────────────────────

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
