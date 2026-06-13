"""
AI解说服务 - 使用OpenAI API生成比赛解说
"""
import os
from typing import Dict, List, Optional
from openai import OpenAI
import json

class CommentaryService:
    """AI比赛解说服务"""

    SYSTEM_PROMPT = """你是一位专业的足球解说员，拥有20年以上的解说经验。你的解说风格：
- 专业、热情但不失客观
- 善于分析战术细节
- 语言生动，能让观众身临其境
- 数据解读精准，擅长将数据转化为叙述

请根据提供的比赛数据，生成专业的比赛解说和深度分析。"""

    COMMENTARY_TEMPLATE = """
## 比赛概览
[简要介绍比赛背景和两支球队]

## 上半场/全场解说
[按时间线展开的详细解说，包含关键时刻的描述]

## 战术分析
[分析两队的战术选择和执行情况]

## 关键球员表现
[评价发挥出色的球员]

## 数据解读
[解读比赛关键数据，如xG、控球率、射门等]

## 总结
[比赛结果的深层意义]
"""

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        self.client = OpenAI(api_key=api_key) if api_key else None
        if self.client:
            self.client.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("AI_MODEL", "deepseek-chat")

    def _format_match_stats(self, stats: Dict) -> str:
        """格式化比赛统计数据"""
        formatted = []
        formatted.append(f"比分: {stats.get('home_score', 0)} - {stats.get('away_score', 0)}")
        formatted.append(f"主队: {stats.get('home_team', 'Unknown')}")
        formatted.append(f"客队: {stats.get('away_team', 'Unknown')}")
        formatted.append("")
        formatted.append("--- 比赛统计 ---")
        formatted.append(f"射门: {stats.get('home_shots', 0)} - {stats.get('away_shots', 0)}")
        formatted.append(f"射正: {stats.get('home_shots_on_target', 0)} - {stats.get('away_shots_on_target', 0)}")
        formatted.append(f"控球率: {stats.get('home_possession', 50):.1f}% - {stats.get('away_possession', 50):.1f}%")
        formatted.append(f"传球成功率: {stats.get('home_pass_accuracy', 0):.1f}% - {stats.get('away_pass_accuracy', 0):.1f}%")
        formatted.append(f"角球: {stats.get('home_corners', 0)} - {stats.get('away_corners', 0)}")
        formatted.append(f"犯规: {stats.get('home_fouls', 0)} - {stats.get('away_fouls', 0)}")
        formatted.append(f"黄牌: {stats.get('home_yellows', 0)} - {stats.get('away_yellows', 0)}")
        formatted.append(f"xG: {stats.get('home_xg', 0):.2f} - {stats.get('away_xg', 0):.2f}")
        return "\n".join(formatted)

    def _format_events(self, events: List[Dict]) -> str:
        """格式化事件列表"""
        if not events:
            return "暂无事件数据"

        formatted = []
        for event in events[:20]:  # 限制事件数量
            minute = event.get('minute', 0)
            team = event.get('team', 'Unknown')
            event_type = event.get('type', 'Event')
            description = event.get('description', '')

            formatted.append(f"{minute}' - {team} - {event_type}: {description}")

        return "\n".join(formatted)

    def generate_match_commentary(self, stats: Dict, events: List[Dict], focus_team: Optional[str] = None) -> str:
        """生成完整比赛解说"""
        if not self.client:
            return self._generate_fallback_commentary(stats)

        try:
            stats_text = self._format_match_stats(stats)
            events_text = self._format_events(events)

            user_prompt = f"""
请为以下足球比赛生成专业解说：

{stats_text}

## 重要事件
{events_text}

{"## 重点关注球队" if focus_team else ""}
{focus_team if focus_team else ""}

请生成一段精彩的比赛解说，包含：
1. 比赛开局点评
2. 关键时刻的生动描述
3. 战术层面的深度分析
4. 球员表现评价
5. 比赛结果的解读

风格要求：专业热情，语言生动，800字左右。
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"生成解说失败: {e}")
            return self._generate_fallback_commentary(stats)

    def generate_tactical_analysis(self, stats: Dict) -> str:
        """生成战术分析"""
        if not self.client:
            return self._generate_fallback_tactical(stats)

        try:
            stats_text = self._format_match_stats(stats)

            user_prompt = f"""
作为战术分析师，请深度分析这场比赛的战术层面：

{stats_text}

请分析：
1. 两队的阵型和战术风格
2. 攻防转换的特点
3. 关键区域的争夺
4. 教练的战术调整
5. 这场比赛的战术意义

要求：专业深入，400字左右。
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的足球战术分析师。"},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                max_tokens=800
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"生成战术分析失败: {e}")
            return self._generate_fallback_tactical(stats)

    def generate_player_ratings(self, stats: Dict) -> str:
        """生成球员评分和评语"""
        if not self.client:
            return self._generate_fallback_ratings(stats)

        try:
            stats_text = self._format_match_stats(stats)

            user_prompt = f"""
请为这场比赛的球员表现打分（1-10分）：

{stats_text}

请给出：
1. 主队MVP球员及评语
2. 客队MVP球员及评语
3. 两名表现欠佳的球员及原因
4. 整体评分总结

格式清晰，评价客观。
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的足球评论员。"},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=600
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"生成球员评分失败: {e}")
            return self._generate_fallback_ratings(stats)

    def generate_prematch_preview(self, home_team: str, away_team: str, home_elo: float, away_elo: float,
                                   home_recent: List[str], away_recent: List[str]) -> str:
        """生成赛前前瞻"""
        if not self.client:
            return self._generate_fallback_preview(home_team, away_team, home_elo, away_elo)

        try:
            user_prompt = f"""
请为这场即将到来的比赛撰写赛前前瞻：

主队: {home_team} (ELO: {home_elo:.0f})
客队: {away_team} (ELO: {away_elo:.0f})

主队近期战绩: {', '.join(home_recent[-5:]) if home_recent else '无数据'}
客队近期战绩: {', '.join(away_recent[-5:]) if away_recent else '无数据'}

请分析：
1. 两队近期状态和战意
2. 关键球员伤停情况（假设健康）
3. 历史交锋记录
4. 战术预测
5. 比分预测

风格：专业、有见地、让读者期待比赛。
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的足球记者和解说员。"},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"生成赛前前瞻失败: {e}")
            return self._generate_fallback_preview(home_team, away_team, home_elo, away_elo)

    def _generate_fallback_commentary(self, stats: Dict) -> str:
        """备用解说（当API不可用时）"""
        home = stats.get('home_team', '主队')
        away = stats.get('away_team', '客队')
        home_score = stats.get('home_score', 0)
        away_score = stats.get('away_score', 0)

        return f"""
## {home} vs {away} 比赛解说

各位观众朋友们好！欢迎来到这场精彩的比赛！

最终比分定格在 **{home_score} - {away_score}**，这是一场激动人心的对决。

### 比赛进程
主队{home}展现了强大的主场气势，在进攻端创造了不少威胁。客队{away}同样不甘示弱，防守端表现出色的同时也制造了几次有威胁的反击。

### 关键数据
- 射门次数反映了双方对胜利的渴望
- 控球率显示了两队对比赛节奏的争夺
- xG数据揭示了真正的得分机会

### 战术点评
从战术层面来看，双方都展现了自己的特点。这场比赛的质量相当高，相信观众朋友们也感受到了足球的魅力。

让我们期待下一场更加精彩的对决！
"""

    def _generate_fallback_tactical(self, stats: Dict) -> str:
        """备用战术分析"""
        return """
从战术角度分析，这场比赛展现了两队不同的战术理念。主场球队倾向于控球打法，而客队则更注重快速转换。关键时刻的战术调整往往决定了比赛的走向。
"""

    def _generate_fallback_ratings(self, stats: Dict) -> str:
        """备用球员评分"""
        return """
本场最佳球员授予主队核心，他/她在关键时刻展现了自己的价值。客队门将表现稳健，多次化解危机。双方都有值得肯定的球员表现。
"""

    def _generate_fallback_preview(self, home: str, away: str, home_elo: float, away_elo: float) -> str:
        """备用赛前前瞻"""
        return f"""
今晚的重点对决将在{home}和{away}之间展开。

根据ELO评分系统，主队{home}({home_elo:.0f})略占优势，但客队{away}({away_elo:.0f})同样有机会。

这场比赛将是技术与战术的较量，让我们拭目以待！
"""


# 全局解说服务实例
commentary_service = CommentaryService()


if __name__ == "__main__":
    service = CommentaryService()
    print("AI解说服务已初始化")