"""
AI-powered player form analysis using DeepSeek.
Generates Chinese-language scout reports based on real match data.
"""
import os
import json
import time
from pathlib import Path
from typing import Optional, Dict
from openai import OpenAI

BASE_DIR = Path(__file__).parent.parent
PLAYER_CACHE_DIR = BASE_DIR / "data" / "player_analysis"
PLAYER_ANALYSIS_PROMPT_VERSION = "v2"


class PlayerAnalysisService:
    """Generate AI-powered player evaluation based on real stats."""

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        self.client = OpenAI(api_key=api_key) if api_key else None
        if self.client:
            self.client.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("AI_MODEL", "deepseek-chat")
        self._cache: Dict[str, dict] = {}
        PLAYER_CACHE_DIR.mkdir(parents=True, exist_ok=True)

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
        cache_key = f"{PLAYER_ANALYSIS_PROMPT_VERSION}:{team}:{name}"

        # Check in-memory cache first
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Check disk cache
        disk_cached = self._load_from_disk(cache_key)
        if disk_cached:
            self._cache[cache_key] = disk_cached
            return disk_cached

        if not self.client:
            result = self._fallback_analysis(name, name_cn, stats)
            result["_ts"] = time.time()
            self._cache[cache_key] = result
            self._save_to_disk(cache_key, result)
            return result

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
                    {"role": "system", "content": "你是2026世界杯的专业球探分析师。你的分析风格客观、专业、有深度，善于从数据中洞察球员的真实状态。已知被分析对象属于已经确定的大名单球员，但不要在正文中提到“大名单已确定”或类似表述。用中文输出，200-350字。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=800,
            )
            analysis = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"DeepSeek API error for {name}: {e}")
            result = self._fallback_analysis(name, name_cn, stats)
            result["_ts"] = time.time()
            self._cache[cache_key] = result
            self._save_to_disk(cache_key, result)
            return result

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
        self._save_to_disk(cache_key, result)
        return result

    def _disk_path(self, cache_key: str) -> Path:
        safe = cache_key.replace(":", "_").replace("/", "_")
        return PLAYER_CACHE_DIR / f"{safe}.json"

    def _load_from_disk(self, cache_key: str) -> Optional[dict]:
        path = self._disk_path(cache_key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data
        except Exception:
            pass
        return None

    def _save_to_disk(self, cache_key: str, data: dict):
        path = self._disk_path(cache_key)
        try:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

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
        key_passes = stats.get("key_passes")
        progressive_passes = stats.get("progressive_passes")
        clearances = stats.get("clearances")
        blocks = stats.get("blocks")
        saves = stats.get("saves")
        goals_conceded = stats.get("goals_conceded")
        clean_sheets = stats.get("clean_sheets")
        save_pct = stats.get("save_pct")

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
        if key_passes is not None or progressive_passes is not None:
            lines.append(f"关键传球：{key_passes or 0}次，向前传球：{progressive_passes or 0}次")
        if clearances is not None or blocks is not None:
            lines.append(f"解围：{clearances or 0}次，封堵：{blocks or 0}次")
        if saves is not None or goals_conceded is not None or clean_sheets is not None:
            lines.append(f"门将数据：扑救{saves or 0}次，失球{goals_conceded or 0}个，零封{clean_sheets or 0}场，扑救率{save_pct if save_pct is not None else '暂无'}%")

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
            f"1. 个人状态分析 — 结合出场时间、效率、攻防数据判断近期状态，不要只给笼统结论。",
            f"2. 能力带来的变化 — 说明他的能力会给国家队带来什么战术变化或比赛影响，例如推进、终结、防线稳定、出球、压迫、转换速度等。",
            f"3. 隐患与风险 — 指出可能拖累球队的风险，例如效率波动、防守覆盖、纪律性、对抗、伤病/体能、位置适配或样本不足。",
            f"4. 国家队角色 — 判断他更像核心、主力、轮换还是特定场景武器，并说明依据。",
            f"",
            f"注意：务必引用具体数据，避免空洞的套话。不要在正文中提到该球员已经确定进入大名单。用中文输出。",
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

请从以下角度进行简要分析（150-220字）：
1. 个人状态判断 — 只能基于履历、位置和俱乐部背景保守判断，不要编造具体赛季数据。
2. 能力带来的变化 — 说明他的能力可能给国家队带来的战术变化或比赛影响。
3. 隐患与风险 — 指出样本不足、联赛强度、位置适配、对抗或稳定性方面的风险。
4. 国家队角色预期 — 判断更可能是主力、轮换还是特定场景选择。

注意：由于缺少赛季真实数据，请注明"基于球员履历评估，待补充赛季数据"，分析要客观保守，不要编造具体数据。不要在正文中提到该球员已经确定进入大名单。用中文输出。"""

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
