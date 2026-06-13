"""
时序ELO评分计算器
支持：自适应K因子、进球差倍率、衰减回归、主客场优势调整
"""
import pandas as pd
import numpy as np
from typing import Optional


class EloCalculator:
    """计算并维护全历史ELO评分"""

    INITIAL_ELO = 1500
    REGRESSION_THRESHOLD_DAYS = 1460  # 4年无比赛回归均值
    REGRESSION_STRENGTH = 0.5  # 回归强度

    def __init__(self, k_base: float = 32, home_advantage: float = 50):
        self.k_base = k_base
        self.home_advantage = home_advantage
        self.elo_history: dict[str, list[dict]] = {}  # team -> [{date, elo, match_id}]

    def get_k_factor(self, tournament_type: str = "group") -> float:
        """根据赛事重要性返回自适应K因子"""
        k_map = {
            "friendly": self.k_base * 0.5,
            "qualifier": self.k_base * 1.0,
            "group": self.k_base * 1.25,
            "knockout": self.k_base * 1.5,
            "final": self.k_base * 2.0,
        }
        return k_map.get(tournament_type, self.k_base)

    def goal_diff_multiplier(self, goal_diff: int) -> float:
        """进球差倍率：大胜/大败影响更大"""
        if goal_diff <= 0:
            return 1.0
        if goal_diff == 1:
            return 1.0
        if goal_diff == 2:
            return 1.5
        return (11 + goal_diff) / 8  # 世界杯公式

    def get_elo(self, team: str, date: Optional[str] = None) -> float:
        """获取球队在指定日期前的ELO评分"""
        if team not in self.elo_history or not self.elo_history[team]:
            return self.INITIAL_ELO

        history = self.elo_history[team]
        if date is None:
            return history[-1]["elo"]

        # 找到日期之前的最新ELO
        for entry in reversed(history):
            if entry["date"] <= date:
                elo = entry["elo"]
                # 如果距离上次比赛超过阈值，向均值回归
                days_since = (pd.Timestamp(date) - pd.Timestamp(entry["date"])).days
                if days_since > self.REGRESSION_THRESHOLD_DAYS:
                    excess_days = days_since - self.REGRESSION_THRESHOLD_DAYS
                    decay = min(1.0, excess_days / 730 * self.REGRESSION_STRENGTH)
                    elo = elo + (self.INITIAL_ELO - elo) * decay
                return elo

        return self.INITIAL_ELO

    def set_elo(self, team: str, elo: float, date: str, match_id: Optional[int] = None):
        """记录一次ELO评分"""
        if team not in self.elo_history:
            self.elo_history[team] = []
        self.elo_history[team].append({
            "date": str(date),
            "elo": elo,
            "match_id": match_id,
        })

    def calculate_match(
        self,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        match_date: str,
        tournament_type: str = "group",
        neutral_venue: bool = False,
    ) -> tuple[float, float]:
        """计算一场比赛后的新ELO评分，返回 (new_home_elo, new_away_elo)"""
        home_elo = self.get_elo(home_team, match_date)
        away_elo = self.get_elo(away_team, match_date)

        ha = 0 if neutral_venue else self.home_advantage

        # 期望胜率
        expected_home = 1.0 / (1.0 + 10.0 ** ((away_elo - home_elo - ha) / 400.0))

        # 实际结果
        if home_score > away_score:
            actual_home = 1.0
        elif home_score < away_score:
            actual_home = 0.0
        else:
            actual_home = 0.5

        # 进球差倍率
        goal_diff = abs(home_score - away_score)
        gd_mult = self.goal_diff_multiplier(goal_diff)
        k = self.get_k_factor(tournament_type) * gd_mult

        new_home = home_elo + k * (actual_home - expected_home)
        new_away = away_elo + k * ((1 - actual_home) - (1 - expected_home))

        self.set_elo(home_team, new_home, match_date)
        self.set_elo(away_team, new_away, match_date)

        return new_home, new_away

    def compute_all(self, matches_df: pd.DataFrame) -> pd.DataFrame:
        """
        从比赛DataFrame计算所有历史ELO
        必须包含: home_team, away_team, home_score, away_score, match_date
        可选: tournament_type, neutral_venue
        """
        matches_df = matches_df.sort_values("match_date").reset_index(drop=True)
        self.elo_history = {}

        elo_records = []
        for _, row in matches_df.iterrows():
            home_elo_before = self.get_elo(row["home_team"], str(row["match_date"]))
            away_elo_before = self.get_elo(row["away_team"], str(row["match_date"]))

            new_home, new_away = self.calculate_match(
                home_team=row["home_team"],
                away_team=row["away_team"],
                home_score=row["home_score"],
                away_score=row["away_score"],
                match_date=str(row["match_date"]),
                tournament_type=row.get("tournament_type", "friendly"),
                neutral_venue=row.get("neutral_venue", True),
            )

            elo_records.append({
                "home_team": row["home_team"],
                "away_team": row["away_team"],
                "match_date": str(row["match_date"]),
                "home_elo_before": home_elo_before,
                "away_elo_before": away_elo_before,
                "home_elo_after": new_home,
                "away_elo_after": new_away,
            })

        return pd.DataFrame(elo_records)

    def get_latest_elos(self) -> dict[str, float]:
        """获取所有球队的最新ELO评分"""
        result = {}
        for team, history in self.elo_history.items():
            if history:
                result[team] = history[-1]["elo"]
            else:
                result[team] = self.INITIAL_ELO
        return result
