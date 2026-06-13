"""训练预测模型 V2 — 使用海量数据 + 25+特征 + 集成模型"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.data_service import data_service
from services.prediction_service import PredictionService


if __name__ == "__main__":
    print("=" * 60)
    print("  世界杯预测模型训练 V2")
    print("  模型: LightGBM + XGBoost 集成")
    print("  特征: 27维 (ELO + 近期状态 + 交锋 + 背景)")
    print("=" * 60)

    # 1. 加载海量数据
    print("\n[1/4] 加载数据...")
    use_full = "--full" in sys.argv

    if use_full:
        # 确保有全量数据
        data_service.build_international_dataset()

    matches = data_service.get_international_matches()
    print(f"  比赛总数: {len(matches)}")
    if not matches.empty:
        print(f"  球队数: {matches['home_team'].nunique()}")
        print(f"  时间范围: {matches['match_date'].min()} ~ {matches['match_date'].max()}")

    # 2. 初始化预测服务并训练
    print("\n[2/4] 训练模型...")
    ps = PredictionService()
    success = ps.train(matches)

    if not success:
        print("\n训练失败，请先运行 'python generate_data.py --full' 生成训练数据")
        sys.exit(1)

    # 3. 模型信息
    print(f"\n[3/4] 模型信息:")
    info = ps.get_model_info()
    for k, v in info.items():
        print(f"  {k}: {v}")

    # 4. 测试预测
    print(f"\n[4/4] 预测测试:")
    test_pairs = [
        ("Argentina", "Brazil"),
        ("France", "Germany"),
        ("England", "Spain"),
        ("Argentina", "France"),
        ("Japan", "South Korea"),
        ("Morocco", "Croatia"),
        ("Netherlands", "Portugal"),
    ]
    for home, away in test_pairs:
        result = ps.predict(home, away)
        print(f"  {home} vs {away}: "
              f"主胜={result['home_win']:.1%} "
              f"平={result['draw']:.1%} "
              f"客胜={result['away_win']:.1%} "
              f"({result['data_quality']})")

    print(f"\n{'=' * 60}")
    print("  训练完成！模型已保存到 models/ 目录")
    print(f"{'=' * 60}")
