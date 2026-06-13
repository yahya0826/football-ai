"""
特征工程模块 — 统一特征提取器
所有预测/情报/复盘服务通过此模块获取特征，保证一致性
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from data.elo_calculator import EloCalculator
from data.team_normalizer import TeamNormalizer


class FeatureEngineering:
    """25+特征提取器，从海量比赛数据构建特征矩阵"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.normalizer = TeamNormalizer()
        self.elo_calc = EloCalculator()

        # 缓存
        self._matches_df: Optional[pd.DataFrame] = None
        self._elo_records: Optional[pd.DataFrame] = None
        self._latest_elos: dict[str, float] = {}
        self._features_cache: Optional[pd.DataFrame] = None

    # ====== 数据加载 ======

    def load_international_matches(self) -> pd.DataFrame:
        """加载国际比赛数据（优先Kaggle数据集，回退到本地生成）"""
        path = self.data_dir / "international_matches.parquet"
        if path.exists():
            return pd.read_parquet(path)
        # 回退到本地世界杯数据
        wc_path = self.data_dir / "matches.parquet"
        if wc_path.exists():
            return pd.read_parquet(wc_path)
        return pd.DataFrame()

    def load_team_features(self) -> pd.DataFrame:
        """加载球队特征数据"""
        path = self.data_dir / "team_features.parquet"
        if path.exists():
            return pd.read_parquet(path)
        return pd.DataFrame()

    # ====== 全量特征计算 ======

    def compute_full_feature_matrix(self, matches_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        从比赛数据计算完整的特征矩阵
        每行一场比赛，列是所有特征 + 目标变量
        """
        if matches_df is None:
            matches_df = self.load_international_matches()

        if matches_df.empty:
            print("无比赛数据，使用生成数据")
            return self._generate_fallback_features()

        matches_df = matches_df.copy()
        matches_df = matches_df.sort_values("match_date").reset_index(drop=True)

        # 确保必要列存在
        self._ensure_columns(matches_df)

        # 标准化队名
        matches_df["home_team"] = matches_df["home_team"].apply(self.normalizer.normalize)
        matches_df["away_team"] = matches_df["away_team"].apply(self.normalizer.normalize)

        # 更新known_teams
        all_teams = set(matches_df["home_team"].unique()) | set(matches_df["away_team"].unique())
        self.normalizer.add_known_teams(list(all_teams))

        print(f"计算特征矩阵: {len(matches_df)} 场比赛, {len(all_teams)} 支球队")

        # Step 1: 计算时序ELO
        elo_df = self.elo_calc.compute_all(matches_df)
        self._elo_records = elo_df
        self._latest_elos = self.elo_calc.get_latest_elos()

        # Step 2: 逐行构建特征向量
        feature_rows = []
        for idx in range(len(matches_df)):
            row = matches_df.iloc[idx]
            features = self._compute_single_match_features(matches_df, idx)
            features["home_team"] = row["home_team"]
            features["away_team"] = row["away_team"]
            features["match_date"] = str(row["match_date"])
            features["home_score"] = row["home_score"]
            features["away_score"] = row["away_score"]

            # 目标变量
            if row["home_score"] > row["away_score"]:
                features["result"] = 0  # 主胜
            elif row["home_score"] < row["away_score"]:
                features["result"] = 2  # 客胜
            else:
                features["result"] = 1  # 平局

            feature_rows.append(features)

        features_df = pd.DataFrame(feature_rows)
        self._features_cache = features_df
        self._matches_df = matches_df

        # 保存
        features_df.to_parquet(self.data_dir / "features.parquet")
        print(f"特征矩阵已保存: {len(features_df)} 行 x {len(features_df.columns)} 列")

        return features_df

    def _compute_single_match_features(self, matches_df: pd.DataFrame, idx: int) -> dict:
        """计算单场比赛的完整特征向量（25+特征）"""
        row = matches_df.iloc[idx]
        home = row["home_team"]
        away = row["away_team"]
        date = str(row["match_date"])

        features = {}

        # === 球队强度特征 (6个) ===
        home_elo = self.elo_calc.get_elo(home, date)
        away_elo = self.elo_calc.get_elo(away, date)

        features["home_elo"] = home_elo
        features["away_elo"] = away_elo
        features["elo_diff"] = home_elo - away_elo
        features["elo_ratio"] = home_elo / max(away_elo, 1)
        features["elo_diff_norm"] = (home_elo - away_elo) / 400.0
        features["home_elo_norm"] = home_elo / 2000.0
        features["away_elo_norm"] = away_elo / 2000.0

        # === 近期状态特征 (8个) ===
        home_recent = self._get_recent_matches(matches_df, home, date, n=5)
        away_recent = self._get_recent_matches(matches_df, away, date, n=5)
        home_recent_10 = self._get_recent_matches(matches_df, home, date, n=10)

        features["home_recent_win_rate_5"] = self._win_rate(home_recent, home)
        features["away_recent_win_rate_5"] = self._win_rate(away_recent, away)
        features["home_avg_goals_scored_5"] = self._avg_goals_scored(home_recent, home)
        features["away_avg_goals_scored_5"] = self._avg_goals_scored(away_recent, away)
        features["home_avg_goals_conceded_5"] = self._avg_goals_conceded(home_recent, home)
        features["away_avg_goals_conceded_5"] = self._avg_goals_conceded(away_recent, away)
        features["home_form_trend"] = self._form_trend(home_recent_10, home)
        features["away_form_trend"] = self._form_trend(
            self._get_recent_matches(matches_df, away, date, n=10), away
        )

        # === 交锋记录特征 (4个) ===
        h2h = self._get_h2h_matches(matches_df, home, away, date)
        features["h2h_home_win_ratio"] = self._h2h_win_ratio(h2h, home)
        features["h2h_avg_total_goals"] = self._h2h_avg_goals(h2h)
        features["h2h_last_result"] = self._h2h_last_result(h2h, home)
        features["h2h_match_count"] = min(len(h2h), 20) / 20.0  # 归一化

        # === 比赛背景特征 (4个) ===
        features["is_knockout"] = 1.0 if row.get("tournament_type", "") in ("knockout", "final") else 0.0
        features["is_neutral"] = 1.0 if row.get("neutral_venue", True) else 0.0
        features["home_advantage"] = 0.0 if row.get("neutral_venue", True) else 0.5

        # 休息天数差
        home_rest = self._get_rest_days(matches_df, home, date)
        away_rest = self._get_rest_days(matches_df, away, date)
        features["rest_days_diff"] = (home_rest - away_rest) / 7.0  # 归一化到周

        # === 赛事级别特征 (3个) ===
        tourney_type = row.get("tournament_type", "friendly")
        importance_map = {"friendly": 0, "qualifier": 1, "group": 2, "knockout": 3, "final": 4}
        features["tournament_importance"] = importance_map.get(tourney_type, 0) / 4.0
        features["is_friendly"] = 1.0 if tourney_type == "friendly" else 0.0
        features["is_final"] = 1.0 if tourney_type == "final" else 0.0

        return features

    # ====== 实时预测特征 ======

    def build_prediction_features(self, home_team: str, away_team: str, match_date: Optional[str] = None) -> np.ndarray:
        """
        为实时预测构建特征向量
        与训练时使用完全相同的特征定义和顺序
        """
        home = self.normalizer.normalize(home_team)
        away = self.normalizer.normalize(away_team)

        date = match_date or pd.Timestamp.now().strftime("%Y-%m-%d")
        matches_df = self._matches_df if self._matches_df is not None else self.load_international_matches()

        if matches_df.empty:
            return self._minimal_features(home, away)

        # 在历史数据末尾追加一行虚拟行来计算特征
        virtual_row = {
            "home_team": home,
            "away_team": away,
            "home_score": 0,
            "away_score": 0,
            "match_date": date,
            "tournament_type": "group",
            "neutral_venue": True,
        }

        if isinstance(matches_df, pd.DataFrame) and not matches_df.empty:
            # 追加虚拟行
            temp_df = pd.concat([matches_df, pd.DataFrame([virtual_row])], ignore_index=True)
            idx = len(temp_df) - 1
        else:
            temp_df = pd.DataFrame([virtual_row])
            idx = 0

        # 使用已计算的ELO记录（不修改）
        features_dict = self._compute_single_match_features(temp_df, idx)

        # 按固定顺序转为numpy数组（去掉非特征列）
        feature_order = [
            "home_elo", "away_elo", "elo_diff", "elo_ratio", "elo_diff_norm",
            "home_elo_norm", "away_elo_norm",
            "home_recent_win_rate_5", "away_recent_win_rate_5",
            "home_avg_goals_scored_5", "away_avg_goals_scored_5",
            "home_avg_goals_conceded_5", "away_avg_goals_conceded_5",
            "home_form_trend", "away_form_trend",
            "h2h_home_win_ratio", "h2h_avg_total_goals", "h2h_last_result", "h2h_match_count",
            "is_knockout", "is_neutral", "home_advantage", "rest_days_diff",
            "tournament_importance", "is_friendly", "is_final",
        ]

        feat_array = np.array([features_dict.get(k, 0.0) for k in feature_order], dtype=np.float64)
        return feat_array

    def _minimal_features(self, home: str, away: str) -> np.ndarray:
        """降级：仅使用ELO的特征"""
        home_elo = self.elo_calc.get_elo(home)
        away_elo = self.elo_calc.get_elo(away)
        features = [
            home_elo, away_elo, home_elo - away_elo,
            home_elo / max(away_elo, 1), (home_elo - away_elo) / 400.0,
            home_elo / 2000.0, away_elo / 2000.0,
            0.5, 0.5, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0,
            0.5, 2.5, 0.5, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.5, 0.0, 0.0,
        ]
        return np.array(features, dtype=np.float64)

    # ====== 辅助计算函数 ======

    def _get_recent_matches(self, df: pd.DataFrame, team: str, before_date: str, n: int = 5) -> pd.DataFrame:
        """获取某队在指定日期前最近N场比赛"""
        mask = (
            ((df["home_team"] == team) | (df["away_team"] == team))
            & (df["match_date"] < before_date)
        )
        recent = df[mask].sort_values("match_date", ascending=False).head(n)
        return recent

    def _win_rate(self, recent_df: pd.DataFrame, team: str) -> float:
        """计算近期胜率"""
        if recent_df.empty:
            return 0.5
        wins = 0
        for _, row in recent_df.iterrows():
            if row["home_team"] == team and row["home_score"] > row["away_score"]:
                wins += 1
            elif row["away_team"] == team and row["away_score"] > row["home_score"]:
                wins += 1
        return wins / len(recent_df)

    def _avg_goals_scored(self, recent_df: pd.DataFrame, team: str) -> float:
        if recent_df.empty:
            return 1.0
        goals = 0
        for _, row in recent_df.iterrows():
            goals += row["home_score"] if row["home_team"] == team else row["away_score"]
        return goals / len(recent_df)

    def _avg_goals_conceded(self, recent_df: pd.DataFrame, team: str) -> float:
        if recent_df.empty:
            return 1.0
        conceded = 0
        for _, row in recent_df.iterrows():
            conceded += row["away_score"] if row["home_team"] == team else row["home_score"]
        return conceded / len(recent_df)

    def _form_trend(self, recent_df: pd.DataFrame, team: str) -> float:
        """形态趋势：使用近期结果的线性回归斜率"""
        if len(recent_df) < 3:
            return 0.0
        results = []
        for _, row in recent_df.iterrows():
            if row["home_team"] == team:
                if row["home_score"] > row["away_score"]:
                    results.append(3)
                elif row["home_score"] == row["away_score"]:
                    results.append(1)
                else:
                    results.append(0)
            else:
                if row["away_score"] > row["home_score"]:
                    results.append(3)
                elif row["away_score"] == row["home_score"]:
                    results.append(1)
                else:
                    results.append(0)

        x = np.arange(len(results))
        y = np.array(results)
        if np.std(y) == 0:
            return 0.0
        slope = np.polyfit(x, y, 1)[0]
        return float(np.clip(slope / 3.0, -1.0, 1.0))

    def _get_h2h_matches(self, df: pd.DataFrame, team_a: str, team_b: str, before_date: str) -> pd.DataFrame:
        """获取两队历史交锋记录"""
        mask = (
            (
                ((df["home_team"] == team_a) & (df["away_team"] == team_b))
                | ((df["home_team"] == team_b) & (df["away_team"] == team_a))
            )
            & (df["match_date"] < before_date)
        )
        return df[mask].sort_values("match_date", ascending=False)

    def _h2h_win_ratio(self, h2h_df: pd.DataFrame, team: str) -> float:
        if h2h_df.empty:
            return 0.5
        wins = 0
        for _, row in h2h_df.iterrows():
            if row["home_team"] == team and row["home_score"] > row["away_score"]:
                wins += 1
            elif row["away_team"] == team and row["away_score"] > row["home_score"]:
                wins += 1
        return wins / len(h2h_df)

    def _h2h_avg_goals(self, h2h_df: pd.DataFrame) -> float:
        if h2h_df.empty:
            return 2.5
        return h2h_df["home_score"].sum() / max(len(h2h_df), 1) + h2h_df["away_score"].sum() / max(len(h2h_df), 1)

    def _h2h_last_result(self, h2h_df: pd.DataFrame, team: str) -> float:
        """最近一次交锋结果: 1=主队视角胜, 0.5=平, 0=负"""
        if h2h_df.empty:
            return 0.5
        last = h2h_df.iloc[0]
        if last["home_team"] == team:
            if last["home_score"] > last["away_score"]:
                return 1.0
            elif last["home_score"] == last["away_score"]:
                return 0.5
            return 0.0
        else:
            if last["away_score"] > last["home_score"]:
                return 1.0
            elif last["away_score"] == last["home_score"]:
                return 0.5
            return 0.0

    def _get_rest_days(self, df: pd.DataFrame, team: str, before_date: str) -> float:
        """计算球队休息天数"""
        mask = ((df["home_team"] == team) | (df["away_team"] == team)) & (df["match_date"] < before_date)
        recent = df[mask].sort_values("match_date", ascending=False)
        if recent.empty:
            return 7.0  # 默认7天
        last_date = pd.Timestamp(recent.iloc[0]["match_date"])
        rest = (pd.Timestamp(before_date) - last_date).days
        return min(rest, 30.0)

    def _ensure_columns(self, df: pd.DataFrame):
        """确保必要列存在"""
        defaults = {
            "tournament_type": "friendly",
            "neutral_venue": True,
            "home_score": 0,
            "away_score": 0,
        }
        for col, default in defaults.items():
            if col not in df.columns:
                df[col] = default

    def _generate_fallback_features(self) -> pd.DataFrame:
        """降级：基于2022世界杯生成特征矩阵"""
        print("使用本地世界杯数据生成特征矩阵...")
        wc_path = self.data_dir / "matches.parquet"
        if not wc_path.exists():
            # 运行生成脚本
            import subprocess
            subprocess.run([sys.executable, str(Path(__file__).parent.parent / "generate_data.py")], check=False)

        if wc_path.exists():
            df = pd.read_parquet(wc_path)
            return self.compute_full_feature_matrix(df)

        print("无法生成特征矩阵")
        return pd.DataFrame()

    def get_feature_names(self) -> list[str]:
        return [
            "home_elo", "away_elo", "elo_diff", "elo_ratio", "elo_diff_norm",
            "home_elo_norm", "away_elo_norm",
            "home_recent_win_rate_5", "away_recent_win_rate_5",
            "home_avg_goals_scored_5", "away_avg_goals_scored_5",
            "home_avg_goals_conceded_5", "away_avg_goals_conceded_5",
            "home_form_trend", "away_form_trend",
            "h2h_home_win_ratio", "h2h_avg_total_goals", "h2h_last_result", "h2h_match_count",
            "is_knockout", "is_neutral", "home_advantage", "rest_days_diff",
            "tournament_importance", "is_friendly", "is_final",
        ]


if __name__ == "__main__":
    fe = FeatureEngineering()
    feat_df = fe.compute_full_feature_matrix()
    print(f"\n特征矩阵: {feat_df.shape}")
    print(f"特征列: {fe.get_feature_names()}")
    print(f"\n前5行:")
    print(feat_df.head())
