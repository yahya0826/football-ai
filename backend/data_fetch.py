"""
数据获取脚本 - 生成本地世界杯数据用于开发测试
如果网络可访问StatsBomb，会自动从API拉取；否则使用本地生成数据
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.data_service import data_service

if __name__ == "__main__":
    print("=== 世界杯数据获取 ===")

    # 检查本地数据
    if (Path("data") / "matches.parquet").exists():
        print("本地数据已存在")
        matches = data_service.get_matches()
        events_sample = data_service.get_match_events(matches.iloc[0]['match_id'])
        print(f"比赛数量: {len(matches)}")
        print(f"首场事件数量: {len(events_sample)}")
        print("\n前5场比赛:")
        print(matches[['match_id', 'home_team', 'away_team', 'home_score', 'away_score']].head())
    else:
        print("本地数据不存在，尝试从StatsBomb API拉取...")
        data_service.cache_all_worldcup_data()

        if not (Path("data") / "matches.parquet").exists():
            print("\nStatsBomb API不可用（可能网络受限），请运行:")
            print("  python generate_data.py")
