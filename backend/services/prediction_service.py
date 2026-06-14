"""
ELO 评级服务 — 提供球队 ELO 评分查询
被多模块依赖（commentary、intelligence、health、stats）
"""
import pickle
from pathlib import Path
from typing import Dict

from .feature_engineering import FeatureEngineering


class PredictionService:
    """ELO 评级服务"""

    ELO_INITIAL = 1500

    def __init__(self, model_dir: str = "models", data_dir: str = "data"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = Path(data_dir)

        self.elo_ratings: Dict[str, float] = {}
        self.fe = FeatureEngineering(data_dir=str(self.data_dir))

        self._load_elo()

    def _load_elo(self):
        """加载 ELO 评分"""
        elo_path = self.model_dir / "elo_ratings.pkl"
        if elo_path.exists():
            try:
                with open(elo_path, 'rb') as f:
                    self.elo_ratings = pickle.load(f)
            except Exception:
                pass

    def get_elo(self, team: str) -> float:
        """获取球队ELO评分"""
        normalized = self.fe.normalizer.normalize(team)
        return self.elo_ratings.get(normalized, self.ELO_INITIAL)

    def get_model_info(self) -> Dict:
        """获取 ELO 服务元信息"""
        return {
            "n_teams_with_elo": len(self.elo_ratings),
        }


# 全局 ELO 服务实例
prediction_service = PredictionService()


if __name__ == "__main__":
    svc = PredictionService()
    print(f"ELO 信息: {svc.get_model_info()}")
    print(f"Argentina ELO: {svc.get_elo('Argentina')}")
    print(f"Brazil ELO: {svc.get_elo('Brazil')}")
