"""
数据获取服务 - 优先使用本地缓存数据，回退到StatsBomb API
"""
import pandas as pd
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class DataService:
    """世界杯数据服务 — 支持多数据源（本地缓存 / StatsBomb / Kaggle国际比赛）"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._matches_cache = None
        self._events_cache = {}
        self._intl_matches_cache = None
        self._features_cache = None
        self._team_features_cache = None
        self._use_local = self._check_local_data()

    def _check_local_data(self) -> bool:
        """检查是否有本地缓存数据"""
        return (self.data_dir / "matches.parquet").exists()

    def _try_statsbomb(func):
        """装饰器：优先使用本地数据，失败时尝试StatsBomb API"""
        def wrapper(self, *args, **kwargs):
            # 如果有本地数据，直接使用
            if self._use_local:
                return func(self, *args, **kwargs)
            # 否则尝试StatsBomb
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                print(f"数据获取失败: {e}")
                return pd.DataFrame() if func.__name__ != 'get_competitions' else []
        return wrapper

    def get_competitions(self) -> List[Dict]:
        """获取所有可用赛事"""
        if self._use_local:
            return [{
                'competition_id': 43,
                'competition_name': 'World Cup 2022',
                'season_id': 106,
                'season_name': '2022',
                'country_name': 'Qatar'
            }]
        try:
            from statsbombpy import sb
            competitions = sb.competitions()
            return competitions.to_dict('records')
        except Exception as e:
            print(f"获取赛事列表失败: {e}")
            return [{
                'competition_id': 43,
                'competition_name': 'World Cup 2022',
                'season_id': 106,
                'season_name': '2022',
                'country_name': 'Qatar'
            }]

    def get_worldcup_competition_id(self) -> Tuple[int, int]:
        """获取男足世界杯的competition_id和season_id"""
        return (43, 106)

    def get_matches(self, competition_id: int = 43, season_id: int = 106) -> pd.DataFrame:
        """获取比赛列表"""
        if self._matches_cache is not None:
            return self._matches_cache

        # 优先从本地加载
        local_path = self.data_dir / "matches.parquet"
        if local_path.exists():
            try:
                self._matches_cache = pd.read_parquet(local_path)
                return self._matches_cache
            except Exception as e:
                print(f"加载本地比赛数据失败: {e}")

        # 回退到StatsBomb API
        try:
            from statsbombpy import sb
            matches = sb.matches(competition_id=competition_id, season_id=season_id)
            self._matches_cache = matches
            return matches
        except Exception as e:
            print(f"获取比赛列表失败: {e}")
            return pd.DataFrame()

    def get_match_events(self, match_id: int) -> pd.DataFrame:
        """获取指定比赛的事件数据"""
        if match_id in self._events_cache:
            return self._events_cache[match_id]

        # 优先从本地加载
        local_path = self.data_dir / "events.parquet"
        if local_path.exists():
            try:
                all_events = pd.read_parquet(local_path)
                events = all_events[all_events['match_id'] == match_id]
                if not events.empty:
                    self._events_cache[match_id] = events
                    return events
            except Exception as e:
                print(f"加载本地事件数据失败: {e}")

        # 回退到StatsBomb API
        try:
            from statsbombpy import sb
            events = sb.events(match_id=match_id)
            self._events_cache[match_id] = events
            return events
        except Exception as e:
            print(f"获取比赛事件失败 (match_id={match_id}): {e}")
            return pd.DataFrame()

    def get_match_lineups(self, match_id: int) -> pd.DataFrame:
        """获取比赛阵容数据"""
        try:
            from statsbombpy import sb
            lineups = sb.lineups(match_id=match_id)
            return lineups
        except Exception as e:
            print(f"获取阵容数据失败 (match_id={match_id}): {e}")
            return pd.DataFrame()

    def extract_shots(self, events: pd.DataFrame) -> pd.DataFrame:
        """从事件数据中提取射门数据"""
        if events.empty:
            return pd.DataFrame()

        shots = events[events['type'] == 'Shot'].copy()
        if shots.empty:
            return pd.DataFrame()

        shot_features = []
        for _, shot in shots.iterrows():
            feature = {
                'match_id': shot.get('match_id'),
                'team': shot.get('team'),
                'player': shot.get('player'),
                'location': shot.get('location'),
                'shot_statsbomb_xg': shot.get('shot_statsbomb_xg'),
                'shot_body_part': shot.get('shot_body_part'),
                'shot_type': shot.get('shot_type'),
                'shot_outcome': shot.get('shot_outcome'),
                'minute': shot.get('minute')
            }
            shot_features.append(feature)
        return pd.DataFrame(shot_features)

    def extract_passes(self, events: pd.DataFrame) -> pd.DataFrame:
        """从事件数据中提取传球数据"""
        if events.empty:
            return pd.DataFrame()

        passes = events[events['type'] == 'Pass'].copy()
        if passes.empty:
            return pd.DataFrame()

        pass_features = []
        for _, pas in passes.iterrows():
            feature = {
                'match_id': pas.get('match_id'),
                'team': pas.get('team'),
                'player': pas.get('player'),
                'location': pas.get('location'),
                'pass_end_location': pas.get('pass_end_location'),
                'pass_outcome': pas.get('pass_outcome'),
                'minute': pas.get('minute')
            }
            pass_features.append(feature)
        return pd.DataFrame(pass_features)

    def extract_corners(self, events: pd.DataFrame) -> Dict[str, int]:
        """提取角球统计"""
        if events.empty:
            return {}
        corners = events[events['type'].isin(['Corner', 'Free Kick'])]
        teams = events['team'].unique()
        result = {}
        for team in teams:
            team_corners = corners[corners['team'] == team]
            result[team] = len(team_corners)
        return result

    def extract_fouls(self, events: pd.DataFrame) -> Dict[str, int]:
        """提取犯规统计"""
        if events.empty:
            return {}
        fouls = events[events['type'] == 'Foul Won']
        yellow = events[events['type'] == 'Yellow Card']
        red = events[events['type'] == 'Red Card']
        teams = events['team'].unique()
        result = {}
        for team in teams:
            result[team] = {
                'fouls': len(fouls[fouls['team'] == team]),
                'yellows': len(yellow[yellow['team'] == team]),
                'reds': len(red[red['team'] == team])
            }
        return result

    def get_team_stats(self, events: pd.DataFrame, team: str) -> Dict:
        """获取球队比赛统计"""
        if events.empty:
            return {}

        team_events = events[events['team'] == team]
        shots = team_events[team_events['type'] == 'Shot']
        passes = team_events[team_events['type'] == 'Pass']
        goals = shots[shots['shot_outcome'] == 'Goal']
        shots_on_target = shots[shots['shot_outcome'].isin(['Goal', 'Saved', 'Saved Off T'])]
        completed_passes = passes[passes['pass_outcome'].isna() | (passes['pass_outcome'] == '')]

        corner_stats = self.extract_corners(events)
        foul_stats = self.extract_fouls(events)

        team_corners = corner_stats.get(team, 0)
        team_fouls_data = foul_stats.get(team, {'fouls': 0, 'yellows': 0, 'reds': 0})

        return {
            'team': team,
            'total_shots': len(shots),
            'shots_on_target': len(shots_on_target),
            'goals': len(goals),
            'total_passes': len(passes),
            'completed_passes': len(completed_passes),
            'pass_accuracy': len(completed_passes) / len(passes) * 100 if len(passes) > 0 else 0,
            'possession': len(team_events) / len(events) * 100 if len(events) > 0 else 50,
            'corners': team_corners if isinstance(team_corners, int) else team_corners,
            'fouls': team_fouls_data.get('fouls', 0) if isinstance(team_fouls_data, dict) else 0,
            'yellows': team_fouls_data.get('yellows', 0) if isinstance(team_fouls_data, dict) else 0,
            'reds': team_fouls_data.get('reds', 0) if isinstance(team_fouls_data, dict) else 0
        }

    def save_data(self, name: str, data: pd.DataFrame):
        """保存数据到本地"""
        path = self.data_dir / f"{name}.parquet"
        data.to_parquet(path)
        print(f"数据已保存: {path}")

    def load_data(self, name: str) -> Optional[pd.DataFrame]:
        """从本地加载数据"""
        path = self.data_dir / f"{name}.parquet"
        if path.exists():
            return pd.read_parquet(path)
        return None

    def cache_all_worldcup_data(self):
        """缓存所有世界杯数据"""
        # 如果有本地数据则跳过
        if self._use_local:
            print("本地数据已存在，跳过API拉取")
            return

        try:
            from statsbombpy import sb
            matches = sb.matches(competition_id=43, season_id=106)
            if matches.empty:
                print("无法获取比赛数据")
                return

            print(f"获取到 {len(matches)} 场世界杯比赛")
            self.save_data("matches", matches)

            all_events = []
            for _, match in matches.iterrows():
                match_id = match['match_id']
                events = sb.events(match_id=match_id)
                if not events.empty:
                    events['match_id'] = match_id
                    all_events.append(events)
                    print(f"已获取 match_id={match_id} 的事件数据")

            if all_events:
                all_events_df = pd.concat(all_events, ignore_index=True)
                self.save_data("events", all_events_df)
                print(f"共缓存 {len(all_events)} 场比赛的事件数据")
        except Exception as e:
            print(f"缓存数据失败: {e}")
            print("请运行 generate_data.py 生成本地测试数据")


    def get_international_matches(self) -> pd.DataFrame:
        """获取国际比赛历史数据（用于模型训练）"""
        if self._intl_matches_cache is not None:
            return self._intl_matches_cache

        path = self.data_dir / "international_matches.parquet"
        if path.exists():
            try:
                self._intl_matches_cache = pd.read_parquet(path)
                print(f"加载国际比赛数据: {len(self._intl_matches_cache)} 场")
                return self._intl_matches_cache
            except Exception as e:
                print(f"加载国际比赛数据失败: {e}")

        # 回退到本地世界杯数据
        matches = self.get_matches()
        if not matches.empty:
            self._intl_matches_cache = matches
        return matches

    def get_features(self) -> pd.DataFrame:
        """获取预计算的特征矩阵"""
        if self._features_cache is not None:
            return self._features_cache

        path = self.data_dir / "features.parquet"
        if path.exists():
            try:
                self._features_cache = pd.read_parquet(path)
                return self._features_cache
            except Exception as e:
                print(f"加载特征矩阵失败: {e}")
        return pd.DataFrame()

    def get_team_features(self) -> pd.DataFrame:
        """获取球队特征数据"""
        if self._team_features_cache is not None:
            return self._team_features_cache

        path = self.data_dir / "team_features.parquet"
        if path.exists():
            try:
                self._team_features_cache = pd.read_parquet(path)
                return self._team_features_cache
            except Exception as e:
                print(f"加载球队特征失败: {e}")
        return pd.DataFrame()

    def get_team_list(self) -> list[str]:
        """获取所有已知球队列表"""
        matches = self.get_international_matches()
        if matches.empty:
            return []
        teams = set(matches["home_team"].unique()) | set(matches["away_team"].unique())
        return sorted(teams)

    def build_international_dataset(self) -> pd.DataFrame:
        """
        构建可用于模型训练的国际比赛数据集
        从Kaggle国际比赛数据格式转换为标准格式
        """
        path = self.data_dir / "international_matches.parquet"
        if path.exists():
            return self.get_international_matches()

        # 如果没有数据，生成丰富的模拟历史数据
        print("生成模拟历史数据集...")
        import sys
        import subprocess
        subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "generate_data.py"), "--full"],
            check=False,
        )
        return self.get_international_matches()

    def analyze_team_strength(self, team: str) -> dict:
        """分析球队综合实力"""
        matches = self.get_international_matches()
        features = self.get_features()

        result = {"team": team, "total_matches": 0, "wins": 0, "draws": 0, "losses": 0,
                  "goals_scored": 0, "goals_conceded": 0}

        if matches.empty:
            return result

        home_matches = matches[matches["home_team"] == team]
        away_matches = matches[matches["away_team"] == team]

        result["total_matches"] = len(home_matches) + len(away_matches)

        for _, m in home_matches.iterrows():
            result["goals_scored"] += int(m["home_score"])
            result["goals_conceded"] += int(m["away_score"])
            if m["home_score"] > m["away_score"]:
                result["wins"] += 1
            elif m["home_score"] == m["away_score"]:
                result["draws"] += 1
            else:
                result["losses"] += 1

        for _, m in away_matches.iterrows():
            result["goals_scored"] += int(m["away_score"])
            result["goals_conceded"] += int(m["home_score"])
            if m["away_score"] > m["home_score"]:
                result["wins"] += 1
            elif m["away_score"] == m["home_score"]:
                result["draws"] += 1
            else:
                result["losses"] += 1

        total = max(result["total_matches"], 1)
        result["win_rate"] = result["wins"] / total

        return result


# 全局数据服务实例
data_service = DataService()


if __name__ == "__main__":
    service = DataService()
    matches = service.get_matches()
    print(f"世界杯比赛数量: {len(matches)}")
    if not matches.empty:
        print(matches[['match_id', 'home_team', 'away_team', 'home_score', 'away_score']].head())
