"""
AI-powered player form analysis using DeepSeek.
Generates Chinese-language scout reports based on real match data.
"""
import os
import json
import time
from typing import Optional, Dict
from openai import OpenAI


class PlayerAnalysisService:
    """Generate AI-powered player evaluation based on real stats."""

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        self.client = OpenAI(api_key=api_key) if api_key else None
        if self.client:
            self.client.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("AI_MODEL", "deepseek-chat")
        self._cache: Dict[str, dict] = {}

    def analyze_player(
        self,
        name: str,
        name_cn: str,
        position: str,
        club: str,
        team: str,
        stats: Optional[dict],
    ) -> dict:
        """Generate a player analysis based on real stats or profile."""
        cache_key = f"{team}:{name}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            # Check cache freshness (24h)
            if time.time() - cached.get("_ts", 0) < 86400:
                return cached

        if not self.client:
            return self._fallback_analysis(name, name_cn, stats)

        has_real_data = stats and stats.get("has_real_data") and stats.get("appearances", 0) > 0

        if has_real_data:
            prompt = self._build_stats_prompt(name, name_cn, position, club, team, stats)
            data_basis = stats.get("data_source", "desktop") == "desktop" and "2025-26赛季真实比赛数据" or "赛季数据"
        else:
            prompt = self._build_profile_prompt(name, name_cn, position, club, team)
            data_basis = "基于球员履历评估"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是2026世界杯的专业球探分析师。你的分析风格客观、专业、有深度，善于从数据中洞察球员的真实状态。用中文输出，200-350字。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=800,
            )
            analysis = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"DeepSeek API error for {name}: {e}")
            return self._fallback_analysis(name, name_cn, stats)

        result = {
            "player_name": name,
            "player_name_cn": name_cn,
            "team": team,
            "analysis": analysis,
            "data_basis": data_basis,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "_ts": time.time(),
        }
        self._cache[cache_key] = result
        return result

    def _build_stats_prompt(self, name, name_cn, position, club, team, stats) -> str:
        """Build prompt for players with real stats."""
        apps = stats.get("appearances", 0)
        starts = stats.get("starts", 0)
        minutes = stats.get("minutes", 0)
        goals = stats.get("goals", 0)
        assists = stats.get("assists", 0)
        shots = stats.get("shots", 0)
        sot = stats.get("shots_on_target", 0)
        tackles = stats.get("tackles_won", 0)
        interceptions = stats.get("interceptions", 0)
        fouls = stats.get("fouls", 0)
        fouled = stats.get("fouled", 0)
        yc = stats.get("yellow_cards", 0)
        rc = stats.get("red_cards", 0)
        wins = stats.get("wins", 0)
        draws = stats.get("draws", 0)
        losses = stats.get("losses", 0)
        rating = stats.get("rating")
        g90 = stats.get("goals_p90", 0)
        a90 = stats.get("assists_p90", 0)
        shot_conv = stats.get("shot_conversion", 0)
        sot_acc = stats.get("shot_accuracy", 0)
        start_rate = stats.get("start_rate", 0)
        xg = stats.get("xg")
        pass_acc = stats.get("pass_accuracy")

        lines = [
            f"你是2026世界杯的专业球探分析师。请基于以下球员的完整赛季数据，对该球员的近期状态进行专业解读和评估。",
            f"",
            f"--- 球员基本信息 ---",
            f"姓名：{name}（{name_cn}）",
            f"位置：{position}",
            f"俱乐部：{club}",
            f"国家队：{team}",
            f"",
            f"--- 赛季数据（2025-26赛季真实比赛统计） ---",
            f"总出场：{apps}次（首发{starts}次，首发率{start_rate}%），总计{minutes}分钟",
            f"进球：{goals}个（每90分钟{g90}个）",
            f"助攻：{assists}个（每90分钟{a90}个）",
            f"射门：{shots}次，射正{sot}次（射正率{sot_acc}%）",
        ]
        if goals > 0 and shots > 0:
            lines.append(f"射门转化率：{shot_conv}%")
        if pass_acc is not None:
            lines.append(f"传球成功率：{pass_acc}%")
        if xg is not None:
            lines.append(f"预期进球(xG)：{xg}")

        lines += [
            f"抢断：{tackles}次，拦截：{interceptions}次",
            f"犯规：{fouls}次，被犯规：{fouled}次",
            f"黄牌：{yc}张，红牌：{rc}张",
        ]
        if rating is not None:
            lines.append(f"赛季评分：{rating}")

        lines += [
            f"球队战绩：{wins}胜 {draws}平 {losses}负",
            f"",
            f"请从以下角度进行分析（200-350字，既客观又生动）：",
            f"1. 出场稳定性与健康状况 — 是否是球队的绝对主力？是否有伤病困扰？",
            f"2. 进攻/防守贡献评估 — 相对于同位置球员，数据表现如何？亮点和短板是什么？",
            f"3. 近期状态趋势 — 结合赛季数据给出状态判断（优秀/良好/一般/低迷）",
            f"4. 世界杯前景 — 该球员在国家队的角色和世界杯预期表现",
            f"",
            f"注意：务必引用具体数据，避免空洞的套话。用中文输出。",
        ]
        return "\n".join(lines)

    def _build_profile_prompt(self, name, name_cn, position, club, team) -> str:
        """Build prompt for players without real stats — profile-based assessment."""
        return f"""你是2026世界杯的专业球探分析师。以下球员目前暂无2025-26赛季的详细比赛数据，请根据其基本信息进行简要评估。

--- 球员基本信息 ---
姓名：{name}（{name_cn}）
位置：{position}
俱乐部：{club}
国家队：{team}

请从以下角度进行简要分析（150-200字）：
1. 俱乐部背景 — 效力俱乐部的级别和竞争环境
2. 位置特点 — 该位置对球员的核心要求
3. 国家队角色预期 — 在国家队可能担任的角色
4. 世界杯展望 — 大致预期表现

注意：由于缺少赛季真实数据，请注明"基于球员履历评估，待补充赛季数据"，分析要客观保守，不要编造具体数据。用中文输出。"""

    def _fallback_analysis(self, name: str, name_cn: str, stats: Optional[dict]) -> dict:
        """Generate a basic text fallback when AI is unavailable."""
        display_name = name_cn or name
        if stats and stats.get("appearances", 0) > 0:
            apps = stats["appearances"]
            goals = stats.get("goals", 0)
            assists = stats.get("assists", 0)
            rating = stats.get("rating")
            rating_text = f"，赛季评分{rating}" if rating else ""
            text = f"{display_name}在2025-26赛季共出场{apps}次，贡献{goals}球{assists}助{rating_text}。AI深度分析暂不可用，请稍后重试。"
        else:
            text = f"{display_name}的详细赛季数据暂未收录。AI深度分析暂不可用，请稍后重试。"
        return {
            "player_name": name,
            "player_name_cn": name_cn,
            "analysis": text,
            "data_basis": "基础数据摘要",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }


player_analysis_service = PlayerAnalysisService()
