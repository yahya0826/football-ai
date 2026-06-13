"""
预测服务 V2 — 基于海量数据的集成模型预测
特征: 25+维 (ELO + 近期状态 + 交锋记录 + 比赛背景 + 赛事级别)
模型: LightGBM + XGBoost 集成
输出: 胜负平概率 + 置信区间 + 特征重要性
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from typing import Dict, Optional, List
from sklearn.preprocessing import LabelEncoder
from sklearn.calibration import CalibratedClassifierCV
import lightgbm as lgb

from .feature_engineering import FeatureEngineering


class PredictionService:
    """比赛预测服务 V2 — 集成模型架构"""

    ELO_INITIAL = 1500

    def __init__(self, model_dir: str = "models", data_dir: str = "data"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = Path(data_dir)

        self.model = None
        self.model_xgb = None
        self.calibrator = None
        self.team_encoder = LabelEncoder()
        self.elo_ratings: Dict[str, float] = {}
        self.feature_importance: Dict[str, float] = {}

        self.fe = FeatureEngineering(data_dir=str(self.data_dir))
        self._feature_names = self.fe.get_feature_names()

        self._load_models()

    # ====== 模型加载/保存 ======

    def _load_models(self):
        """加载所有已保存模型"""
        # 主模型 LightGBM
        lgb_path = self.model_dir / "match_predictor_lgb.pkl"
        if lgb_path.exists():
            try:
                with open(lgb_path, 'rb') as f:
                    self.model = pickle.load(f)
                print("LightGBM模型已加载")
            except Exception as e:
                print(f"加载LightGBM失败: {e}")

        # 辅助模型 XGBoost
        xgb_path = self.model_dir / "match_predictor_xgb.pkl"
        if xgb_path.exists():
            try:
                xgb = self._try_load_xgboost(xgb_path)
                if xgb:
                    self.model_xgb = xgb
                    print("XGBoost模型已加载")
            except Exception as e:
                print(f"加载XGBoost失败: {e}")

        # 校准器
        cal_path = self.model_dir / "calibrator.pkl"
        if cal_path.exists():
            try:
                with open(cal_path, 'rb') as f:
                    self.calibrator = pickle.load(f)
            except:
                pass

        # ELO ratings
        elo_path = self.model_dir / "elo_ratings.pkl"
        if elo_path.exists():
            try:
                with open(elo_path, 'rb') as f:
                    self.elo_ratings = pickle.load(f)
            except:
                pass

        # Feature importance
        fi_path = self.model_dir / "feature_importance.json"
        if fi_path.exists():
            import json
            try:
                with open(fi_path, 'r') as f:
                    self.feature_importance = json.load(f)
            except:
                pass

        # Team encoder
        encoder_path = self.model_dir / "team_encoder.pkl"
        if encoder_path.exists():
            try:
                with open(encoder_path, 'rb') as f:
                    self.team_encoder = pickle.load(f)
            except:
                pass

    def _try_load_xgboost(self, path):
        """尝试加载XGBoost（可能未安装）"""
        try:
            import xgboost as xgb
            with open(path, 'rb') as f:
                return pickle.load(f)
        except ImportError:
            print("XGBoost未安装，跳过")
            return None

    def _save_models(self):
        """保存所有模型"""
        if self.model is not None:
            with open(self.model_dir / "match_predictor_lgb.pkl", 'wb') as f:
                pickle.dump(self.model, f)

        if self.model_xgb is not None:
            with open(self.model_dir / "match_predictor_xgb.pkl", 'wb') as f:
                pickle.dump(self.model_xgb, f)

        if self.calibrator is not None:
            with open(self.model_dir / "calibrator.pkl", 'wb') as f:
                pickle.dump(self.calibrator, f)

        with open(self.model_dir / "elo_ratings.pkl", 'wb') as f:
            pickle.dump(self.elo_ratings, f)

        with open(self.model_dir / "team_encoder.pkl", 'wb') as f:
            pickle.dump(self.team_encoder, f)

        if self.feature_importance:
            import json
            with open(self.model_dir / "feature_importance.json", 'w') as f:
                json.dump(self.feature_importance, f, indent=2)

    # ====== 训练 ======

    def train(self, matches_df: Optional[pd.DataFrame] = None, events_df: Optional[pd.DataFrame] = None):
        """使用海量数据训练集成预测模型"""
        if matches_df is None or matches_df.empty:
            matches_df = self.fe.load_international_matches()

        if len(matches_df) < 50:
            print(f"训练数据不足 ({len(matches_df)} 场)，需要至少50场")
            return False

        print(f"\n{'='*60}")
        print(f"开始训练预测模型 — {len(matches_df)} 场比赛")
        print(f"{'='*60}")

        # Step 1: 计算特征矩阵
        features_df = self.fe.compute_full_feature_matrix(matches_df)
        if features_df.empty:
            print("特征矩阵为空")
            return False

        # 保存ELO
        self.elo_ratings = self.fe._latest_elos

        # Step 2: 准备训练数据
        feature_cols = self._feature_names
        X = features_df[feature_cols].values.astype(np.float64)
        y = features_df["result"].values.astype(np.int64)

        # 处理NaN
        X = np.nan_to_num(X, nan=0.0)

        print(f"特征矩阵: {X.shape[0]} 行 x {X.shape[1]} 列")
        print(f"标签分布: 主胜={(y==0).sum()}, 平={(y==1).sum()}, 客胜={(y==2).sum()}")

        # Step 3: 时序分割（后20%数据作为验证集）
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        print(f"训练集: {len(X_train)}, 验证集: {len(X_val)}")

        # Step 4: 训练 LightGBM
        self.model = lgb.LGBMClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=7,
            num_leaves=63,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_samples=20,
            reg_alpha=0.1,
            reg_lambda=0.1,
            random_state=42,
            verbose=-1,
            class_weight="balanced",
        )
        self.model.fit(X_train, y_train)

        # Step 5: 尝试训练 XGBoost
        try:
            import xgboost as xgb
            self.model_xgb = xgb.XGBClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=0.1,
                random_state=42,
                verbosity=0,
            )
            self.model_xgb.fit(X_train, y_train)
            print("XGBoost训练完成")
        except ImportError:
            print("XGBoost不可用，仅使用LightGBM")
            self.model_xgb = None

        # Step 6: 校准概率
        try:
            self.calibrator = CalibratedClassifierCV(
                self.model, method="isotonic", cv="prefit"
            )
            self.calibrator.fit(X_val, y_val)
            print("概率校准完成 (Isotonic)")
        except Exception as e:
            print(f"校准失败: {e}，使用原始概率")
            self.calibrator = None

        # Step 7: 评估
        self._evaluate(X_val, y_val, feature_cols)

        # Step 8: 保存
        self._save_models()
        print("\n模型已保存到 models/ 目录")

        return True

    def _evaluate(self, X_val, y_val, feature_cols):
        """评估模型并输出报告"""
        # LightGBM预测
        lgb_pred = self.model.predict(X_val)
        lgb_acc = (lgb_pred == y_val).mean()
        lgb_proba = self.model.predict_proba(X_val)
        lgb_logloss = -np.mean(np.log(
            lgb_proba[np.arange(len(y_val)), y_val] + 1e-10
        ))

        print(f"\n--- 模型评估 ---")
        print(f"LightGBM Accuracy: {lgb_acc:.4f}")
        print(f"LightGBM Log Loss: {lgb_logloss:.4f}")

        # XGBoost评估
        if self.model_xgb is not None:
            xgb_pred = self.model_xgb.predict(X_val)
            xgb_acc = (xgb_pred == y_val).mean()
            xgb_proba = self.model_xgb.predict_proba(X_val)
            xgb_logloss = -np.mean(np.log(
                xgb_proba[np.arange(len(y_val)), y_val] + 1e-10
            ))
            print(f"XGBoost Accuracy: {xgb_acc:.4f}")
            print(f"XGBoost Log Loss: {xgb_logloss:.4f}")

        # 特征重要性
        importances = self.model.feature_importances_
        self.feature_importance = {}
        print(f"\n--- Top 10 特征重要性 ---")
        indices = np.argsort(importances)[::-1][:10]
        for i in indices:
            name = feature_cols[i] if i < len(feature_cols) else f"feat_{i}"
            self.feature_importance[name] = float(importances[i])
            print(f"  {name}: {importances[i]:.4f}")

        # 基准对比
        baseline_acc = max(
            (y_val == 0).mean(),
            (y_val == 1).mean(),
            (y_val == 2).mean(),
        )
        print(f"\n基准准确率 (多数类): {baseline_acc:.4f}")
        print(f"相对提升: {(lgb_acc - baseline_acc) / baseline_acc * 100:.1f}%")

    # ====== 预测 ======

    def predict(self, home_team: str, away_team: str, match_context: Optional[dict] = None) -> Dict:
        """
        预测比赛结果 V2
        返回: {home_win, draw, away_win, home_elo, away_elo,
               confidence_interval, feature_importance, data_quality, top_features}
        """
        # 获取ELO
        home_elo = self.elo_ratings.get(
            self.fe.normalizer.normalize(home_team), self.ELO_INITIAL
        )
        away_elo = self.elo_ratings.get(
            self.fe.normalizer.normalize(away_team), self.ELO_INITIAL
        )

        # 构建特征
        try:
            features = self.fe.build_prediction_features(home_team, away_team)
            features = np.nan_to_num(features, nan=0.0)
            data_quality = "high"
        except Exception as e:
            print(f"特征构建异常: {e}")
            features = self.fe._minimal_features(home_team, away_team)
            data_quality = "low"

        # 检测特征完整度
        nonzero_ratio = np.count_nonzero(features) / max(len(features), 1)
        if nonzero_ratio < 0.3:
            data_quality = "low"
        elif nonzero_ratio < 0.7:
            data_quality = "medium"

        # 预测
        if self.model is not None:
            features_2d = features.reshape(1, -1)

            # LightGBM概率
            lgb_probs = self.model.predict_proba(features_2d)[0]

            # XGBoost概率（如果有）
            if self.model_xgb is not None:
                xgb_probs = self.model_xgb.predict_proba(features_2d)[0]
                weights = [0.6, 0.4]  # LightGBM权重更高
                probs = weights[0] * lgb_probs + weights[1] * xgb_probs
            else:
                probs = lgb_probs

            # 校准（如果有）
            if self.calibrator is not None:
                try:
                    probs = self.calibrator.predict_proba(features_2d)[0]
                except:
                    pass

            # 置信区间（简化方法：基于特征完整度调整范围）
            quality_factor = {"high": 0.03, "medium": 0.06, "low": 0.12}[data_quality]
            confidence_interval = {
                "home": [max(0, probs[0] - quality_factor), min(1, probs[0] + quality_factor)],
                "draw": [max(0, probs[1] - quality_factor), min(1, probs[1] + quality_factor)],
                "away": [max(0, probs[2] - quality_factor), min(1, probs[2] + quality_factor)],
            }

            # 归一化
            total = probs.sum()
            if total > 0:
                probs = probs / total

            result = {
                "home_win": float(probs[0]),
                "draw": float(probs[1]),
                "away_win": float(probs[2]),
                "home_elo": home_elo,
                "away_elo": away_elo,
                "confidence_interval": confidence_interval,
                "data_quality": data_quality,
                "top_features": self._get_top_contributing_features(features),
            }
        else:
            # 无模型：使用ELO概率（与V1兼容）
            elo_diff = home_elo - away_elo
            expected = 1.0 / (1.0 + 10.0 ** ((away_elo - home_elo - 50) / 400.0))
            draw_prob = 0.25

            result = {
                "home_win": float(expected * (1 - draw_prob)),
                "draw": float(draw_prob),
                "away_win": float((1 - expected) * (1 - draw_prob)),
                "home_elo": home_elo,
                "away_elo": away_elo,
                "confidence_interval": {
                    "home": [0, 1], "draw": [0, 1], "away": [0, 1]
                },
                "data_quality": "low",
                "top_features": [],
            }

        return result

    def _get_top_contributing_features(self, features: np.ndarray) -> List[Dict]:
        """计算特征贡献度排序（简化为特征值×重要性）"""
        if not self.feature_importance:
            return []

        contributions = []
        for i, name in enumerate(self._feature_names):
            if i < len(features) and name in self.feature_importance:
                value = float(features[i])
                importance = self.feature_importance[name]
                contributions.append({
                    "feature": name,
                    "value": round(value, 4),
                    "importance": round(importance, 4),
                    "contribution": round(value * importance, 6),
                })

        contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        return contributions[:8]

    def get_elo(self, team: str) -> float:
        """获取球队ELO评分"""
        normalized = self.fe.normalizer.normalize(team)
        return self.elo_ratings.get(normalized, self.ELO_INITIAL)

    def update_with_result(self, home_team: str, away_team: str, home_score: int, away_score: int):
        """根据实际结果更新ELO"""
        home = self.fe.normalizer.normalize(home_team)
        away = self.fe.normalizer.normalize(away_team)

        home_elo = self.elo_ratings.get(home, self.ELO_INITIAL)
        away_elo = self.elo_ratings.get(away, self.ELO_INITIAL)

        # 简单ELO更新
        if home_score > away_score:
            result = 1
        elif home_score < away_score:
            result = -1
        else:
            result = 0

        k = 32
        expected = 1.0 / (1.0 + 10.0 ** ((away_elo - home_elo - 50) / 400.0))
        actual = 1.0 if result == 1 else (0.5 if result == 0 else 0.0)

        self.elo_ratings[home] = home_elo + k * (actual - expected)
        self.elo_ratings[away] = away_elo + k * ((1 - actual) - (1 - expected))

        with open(self.model_dir / "elo_ratings.pkl", 'wb') as f:
            pickle.dump(self.elo_ratings, f)

    def get_model_info(self) -> Dict:
        """获取模型元信息"""
        return {
            "model_loaded": self.model is not None,
            "xgb_loaded": self.model_xgb is not None,
            "calibrated": self.calibrator is not None,
            "n_features": len(self._feature_names),
            "n_teams_with_elo": len(self.elo_ratings),
            "top_features": list(self.feature_importance.keys())[:5]
            if self.feature_importance else [],
        }


# 全局预测服务实例
prediction_service = PredictionService()


if __name__ == "__main__":
    svc = PredictionService()
    print(f"模型信息: {svc.get_model_info()}")

    # 测试预测
    result = svc.predict("Argentina", "Brazil")
    print(f"\n阿根廷 vs 巴西:")
    print(f"  主胜: {result['home_win']:.1%}")
    print(f"  平局: {result['draw']:.1%}")
    print(f"  客胜: {result['away_win']:.1%}")
    print(f"  ELO: {result['home_elo']:.0f} vs {result['away_elo']:.0f}")
    print(f"  数据质量: {result['data_quality']}")
