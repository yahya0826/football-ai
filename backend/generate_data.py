"""
生成2022世界杯本地数据（64场比赛 + 模拟事件数据）
用于离线开发和测试，无需访问StatsBomb API
"""
import pandas as pd
import numpy as np
import random
from pathlib import Path

random.seed(42)
np.random.seed(42)

data_dir = Path('data')
data_dir.mkdir(parents=True, exist_ok=True)

# ====== 生成历史国际比赛数据（用于模型训练） ======
def generate_historical_international_matches():
    """生成丰富的模拟历史国际比赛数据（模拟真实分布）"""
    all_teams = [
        "Argentina", "Brazil", "France", "Germany", "England", "Spain", "Italy", "Netherlands",
        "Portugal", "Belgium", "Croatia", "Uruguay", "Mexico", "United States", "Japan",
        "South Korea", "Morocco", "Senegal", "Australia", "Poland", "Switzerland", "Serbia",
        "Denmark", "Tunisia", "Cameroon", "Ghana", "Saudi Arabia", "Qatar", "Ecuador",
        "Iran", "Wales", "Costa Rica", "Canada", "Sweden", "Norway", "Chile", "Colombia",
        "Peru", "Paraguay", "Nigeria", "Egypt", "Algeria", "Ivory Coast", "South Africa",
        "Russia", "Turkey", "Greece", "Czech Republic", "Austria", "Scotland", "Ireland",
        "Ukraine", "Romania", "Bulgaria", "Hungary", "Slovakia", "Slovenia", "Iceland",
    ]

    # 球队实力层级（ELO基础分）
    tiers = {
        "tier1": ["Argentina", "Brazil", "France", "Germany", "England", "Spain", "Italy", "Netherlands"],
        "tier2": ["Portugal", "Belgium", "Croatia", "Uruguay", "Mexico", "United States", "Japan",
                  "South Korea", "Morocco", "Senegal", "Denmark", "Switzerland"],
        "tier3": ["Poland", "Serbia", "Australia", "Tunisia", "Cameroon", "Ghana", "Saudi Arabia",
                  "Qatar", "Ecuador", "Iran", "Wales", "Costa Rica", "Canada", "Sweden",
                  "Norway", "Chile", "Colombia", "Peru", "Paraguay", "Nigeria", "Egypt"],
        "tier4": ["Algeria", "Ivory Coast", "South Africa", "Russia", "Turkey", "Greece",
                  "Czech Republic", "Austria", "Scotland", "Ireland", "Ukraine", "Romania",
                  "Bulgaria", "Hungary", "Slovakia", "Slovenia", "Iceland"],
    }

    tier_elo = {"tier1": (1700, 1950), "tier2": (1500, 1750), "tier3": (1300, 1550), "tier4": (1100, 1350)}
    team_tier = {}
    team_base_elo = {}
    for tier, teams in tiers.items():
        min_e, max_e = tier_elo[tier]
        for team in teams:
            team_tier[team] = tier
            team_base_elo[team] = random.randint(min_e, max_e)

    # 生成2000-2025年的比赛
    tournaments = [
        ("friendly", 0.35), ("qualifier", 0.30), ("group", 0.20),
        ("knockout", 0.10), ("final", 0.05),
    ]

    match_id = 10000
    all_matches = []
    current_elos = dict(team_base_elo)

    for year in range(2000, 2026):
        for month in range(1, 13):
            # 每月生成一定数量的比赛
            n_matches = random.randint(15, 60)
            for _ in range(n_matches):
                # 选择球队对
                home = random.choice(all_teams)
                away = random.choice([t for t in all_teams if t != home])

                # 根据权重选择赛事类型
                tourney_type = random.choices(
                    [t[0] for t in tournaments],
                    weights=[t[1] for t in tournaments]
                )[0]

                # 模拟比赛结果
                home_elo = current_elos[home]
                away_elo = current_elos[away]

                # 中立场地（大部分国际比赛是中立场地）
                neutral = random.random() < 0.75
                ha = 0 if neutral else 50

                # 期望进球数（基于ELO差）
                elo_diff = home_elo - away_elo + ha
                expected_home_goals = 1.2 + elo_diff / 400 * 0.5
                expected_away_goals = 1.2 - elo_diff / 400 * 0.5

                home_score = max(0, int(round(np.random.poisson(max(0.2, expected_home_goals)))))
                away_score = max(0, int(round(np.random.poisson(max(0.2, expected_away_goals)))))

                # 随机波动
                if random.random() < 0.05:  # 5%概率爆冷
                    if home_score == away_score:
                        home_score += random.randint(1, 3)
                    elif home_score > away_score:
                        away_score = home_score + random.randint(1, 2)
                    else:
                        home_score = away_score + random.randint(1, 2)

                # 生成日期
                day = random.randint(1, 28)
                date_str = f"{year}-{month:02d}-{day:02d}"

                all_matches.append({
                    "match_id": match_id,
                    "home_team": home,
                    "away_team": away,
                    "home_score": home_score,
                    "away_score": away_score,
                    "match_date": date_str,
                    "tournament_type": tourney_type,
                    "neutral_venue": neutral,
                    "competition": tourney_type.title(),
                    "season": str(year),
                })

                match_id += 1

    matches_df = pd.DataFrame(all_matches)
    matches_df.to_parquet(data_dir / "international_matches.parquet")
    print(f"生成历史国际比赛数据: {len(matches_df)} 场 (2000-2025)")
    return matches_df


# ====== 2022世界杯全部64场比赛真实数据 ======
matches_data = [
    # 小组赛 A组
    {'match_id': 1, 'home_team': 'Qatar', 'away_team': 'Ecuador', 'home_score': 0, 'away_score': 2, 'match_date': '2022-11-20', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Bayt Stadium', 'status': 'completed'},
    {'match_id': 2, 'home_team': 'Senegal', 'away_team': 'Netherlands', 'home_score': 0, 'away_score': 2, 'match_date': '2022-11-21', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Thumama Stadium', 'status': 'completed'},
    {'match_id': 3, 'home_team': 'Qatar', 'away_team': 'Senegal', 'home_score': 1, 'away_score': 3, 'match_date': '2022-11-25', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Thumama Stadium', 'status': 'completed'},
    {'match_id': 4, 'home_team': 'Netherlands', 'away_team': 'Ecuador', 'home_score': 1, 'away_score': 1, 'match_date': '2022-11-25', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Khalifa International Stadium', 'status': 'completed'},
    {'match_id': 5, 'home_team': 'Ecuador', 'away_team': 'Senegal', 'home_score': 1, 'away_score': 2, 'match_date': '2022-11-29', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Khalifa International Stadium', 'status': 'completed'},
    {'match_id': 6, 'home_team': 'Netherlands', 'away_team': 'Qatar', 'home_score': 2, 'away_score': 0, 'match_date': '2022-11-29', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Bayt Stadium', 'status': 'completed'},
    # 小组赛 B组
    {'match_id': 7, 'home_team': 'England', 'away_team': 'Iran', 'home_score': 6, 'away_score': 2, 'match_date': '2022-11-21', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Khalifa International Stadium', 'status': 'completed'},
    {'match_id': 8, 'home_team': 'United States', 'away_team': 'Wales', 'home_score': 1, 'away_score': 1, 'match_date': '2022-11-21', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Ahmad bin Ali Stadium', 'status': 'completed'},
    {'match_id': 9, 'home_team': 'Wales', 'away_team': 'Iran', 'home_score': 0, 'away_score': 2, 'match_date': '2022-11-25', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Ahmad bin Ali Stadium', 'status': 'completed'},
    {'match_id': 10, 'home_team': 'England', 'away_team': 'United States', 'home_score': 0, 'away_score': 0, 'match_date': '2022-11-25', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Bayt Stadium', 'status': 'completed'},
    {'match_id': 11, 'home_team': 'Wales', 'away_team': 'England', 'home_score': 0, 'away_score': 3, 'match_date': '2022-11-29', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Ahmad bin Ali Stadium', 'status': 'completed'},
    {'match_id': 12, 'home_team': 'Iran', 'away_team': 'United States', 'home_score': 0, 'away_score': 1, 'match_date': '2022-11-29', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Thumama Stadium', 'status': 'completed'},
    # 小组赛 C组
    {'match_id': 13, 'home_team': 'Argentina', 'away_team': 'Saudi Arabia', 'home_score': 1, 'away_score': 2, 'match_date': '2022-11-22', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Lusail Stadium', 'status': 'completed'},
    {'match_id': 14, 'home_team': 'Mexico', 'away_team': 'Poland', 'home_score': 0, 'away_score': 0, 'match_date': '2022-11-22', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Stadium 974', 'status': 'completed'},
    {'match_id': 15, 'home_team': 'Poland', 'away_team': 'Saudi Arabia', 'home_score': 2, 'away_score': 0, 'match_date': '2022-11-26', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Education City Stadium', 'status': 'completed'},
    {'match_id': 16, 'home_team': 'Argentina', 'away_team': 'Mexico', 'home_score': 2, 'away_score': 0, 'match_date': '2022-11-26', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Lusail Stadium', 'status': 'completed'},
    {'match_id': 17, 'home_team': 'Poland', 'away_team': 'Argentina', 'home_score': 0, 'away_score': 2, 'match_date': '2022-11-30', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Stadium 974', 'status': 'completed'},
    {'match_id': 18, 'home_team': 'Saudi Arabia', 'away_team': 'Mexico', 'home_score': 1, 'away_score': 2, 'match_date': '2022-11-30', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Lusail Stadium', 'status': 'completed'},
    # 小组赛 D组
    {'match_id': 19, 'home_team': 'Denmark', 'away_team': 'Tunisia', 'home_score': 0, 'away_score': 0, 'match_date': '2022-11-22', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Education City Stadium', 'status': 'completed'},
    {'match_id': 20, 'home_team': 'France', 'away_team': 'Australia', 'home_score': 4, 'away_score': 1, 'match_date': '2022-11-22', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Janoub Stadium', 'status': 'completed'},
    {'match_id': 21, 'home_team': 'Tunisia', 'away_team': 'Australia', 'home_score': 0, 'away_score': 1, 'match_date': '2022-11-26', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Janoub Stadium', 'status': 'completed'},
    {'match_id': 22, 'home_team': 'France', 'away_team': 'Denmark', 'home_score': 2, 'away_score': 1, 'match_date': '2022-11-26', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Stadium 974', 'status': 'completed'},
    {'match_id': 23, 'home_team': 'Australia', 'away_team': 'Denmark', 'home_score': 1, 'away_score': 0, 'match_date': '2022-11-30', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Janoub Stadium', 'status': 'completed'},
    {'match_id': 24, 'home_team': 'Tunisia', 'away_team': 'France', 'home_score': 1, 'away_score': 0, 'match_date': '2022-11-30', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Education City Stadium', 'status': 'completed'},
    # 小组赛 E组
    {'match_id': 25, 'home_team': 'Germany', 'away_team': 'Japan', 'home_score': 1, 'away_score': 2, 'match_date': '2022-11-23', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Khalifa International Stadium', 'status': 'completed'},
    {'match_id': 26, 'home_team': 'Spain', 'away_team': 'Costa Rica', 'home_score': 7, 'away_score': 0, 'match_date': '2022-11-23', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Thumama Stadium', 'status': 'completed'},
    {'match_id': 27, 'home_team': 'Japan', 'away_team': 'Costa Rica', 'home_score': 0, 'away_score': 1, 'match_date': '2022-11-27', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Ahmad bin Ali Stadium', 'status': 'completed'},
    {'match_id': 28, 'home_team': 'Spain', 'away_team': 'Germany', 'home_score': 1, 'away_score': 1, 'match_date': '2022-11-27', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Bayt Stadium', 'status': 'completed'},
    {'match_id': 29, 'home_team': 'Japan', 'away_team': 'Spain', 'home_score': 2, 'away_score': 1, 'match_date': '2022-12-01', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Khalifa International Stadium', 'status': 'completed'},
    {'match_id': 30, 'home_team': 'Costa Rica', 'away_team': 'Germany', 'home_score': 2, 'away_score': 4, 'match_date': '2022-12-01', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Bayt Stadium', 'status': 'completed'},
    # 小组赛 F组
    {'match_id': 31, 'home_team': 'Morocco', 'away_team': 'Croatia', 'home_score': 0, 'away_score': 0, 'match_date': '2022-11-23', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Bayt Stadium', 'status': 'completed'},
    {'match_id': 32, 'home_team': 'Belgium', 'away_team': 'Canada', 'home_score': 1, 'away_score': 0, 'match_date': '2022-11-23', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Ahmad bin Ali Stadium', 'status': 'completed'},
    {'match_id': 33, 'home_team': 'Belgium', 'away_team': 'Morocco', 'home_score': 0, 'away_score': 2, 'match_date': '2022-11-27', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Thumama Stadium', 'status': 'completed'},
    {'match_id': 34, 'home_team': 'Croatia', 'away_team': 'Canada', 'home_score': 4, 'away_score': 1, 'match_date': '2022-11-27', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Khalifa International Stadium', 'status': 'completed'},
    {'match_id': 35, 'home_team': 'Croatia', 'away_team': 'Belgium', 'home_score': 0, 'away_score': 0, 'match_date': '2022-12-01', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Ahmad bin Ali Stadium', 'status': 'completed'},
    {'match_id': 36, 'home_team': 'Canada', 'away_team': 'Morocco', 'home_score': 1, 'away_score': 2, 'match_date': '2022-12-01', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Thumama Stadium', 'status': 'completed'},
    # 小组赛 G组
    {'match_id': 37, 'home_team': 'Switzerland', 'away_team': 'Cameroon', 'home_score': 1, 'away_score': 0, 'match_date': '2022-11-24', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Janoub Stadium', 'status': 'completed'},
    {'match_id': 38, 'home_team': 'Brazil', 'away_team': 'Serbia', 'home_score': 2, 'away_score': 0, 'match_date': '2022-11-24', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Lusail Stadium', 'status': 'completed'},
    {'match_id': 39, 'home_team': 'Cameroon', 'away_team': 'Serbia', 'home_score': 3, 'away_score': 3, 'match_date': '2022-11-28', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Janoub Stadium', 'status': 'completed'},
    {'match_id': 40, 'home_team': 'Brazil', 'away_team': 'Switzerland', 'home_score': 1, 'away_score': 0, 'match_date': '2022-11-28', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Stadium 974', 'status': 'completed'},
    {'match_id': 41, 'home_team': 'Serbia', 'away_team': 'Switzerland', 'home_score': 2, 'away_score': 3, 'match_date': '2022-12-02', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Stadium 974', 'status': 'completed'},
    {'match_id': 42, 'home_team': 'Cameroon', 'away_team': 'Brazil', 'home_score': 1, 'away_score': 0, 'match_date': '2022-12-02', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Lusail Stadium', 'status': 'completed'},
    # 小组赛 H组
    {'match_id': 43, 'home_team': 'Uruguay', 'away_team': 'South Korea', 'home_score': 0, 'away_score': 0, 'match_date': '2022-11-24', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Education City Stadium', 'status': 'completed'},
    {'match_id': 44, 'home_team': 'Portugal', 'away_team': 'Ghana', 'home_score': 3, 'away_score': 2, 'match_date': '2022-11-24', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Stadium 974', 'status': 'completed'},
    {'match_id': 45, 'home_team': 'South Korea', 'away_team': 'Ghana', 'home_score': 2, 'away_score': 3, 'match_date': '2022-11-28', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Education City Stadium', 'status': 'completed'},
    {'match_id': 46, 'home_team': 'Portugal', 'away_team': 'Uruguay', 'home_score': 2, 'away_score': 0, 'match_date': '2022-11-28', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Lusail Stadium', 'status': 'completed'},
    {'match_id': 47, 'home_team': 'Ghana', 'away_team': 'Uruguay', 'home_score': 0, 'away_score': 2, 'match_date': '2022-12-02', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Janoub Stadium', 'status': 'completed'},
    {'match_id': 48, 'home_team': 'South Korea', 'away_team': 'Portugal', 'home_score': 2, 'away_score': 1, 'match_date': '2022-12-02', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Education City Stadium', 'status': 'completed'},
    # 1/8决赛
    {'match_id': 49, 'home_team': 'Netherlands', 'away_team': 'United States', 'home_score': 3, 'away_score': 1, 'match_date': '2022-12-03', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Khalifa International Stadium', 'status': 'completed'},
    {'match_id': 50, 'home_team': 'Argentina', 'away_team': 'Australia', 'home_score': 2, 'away_score': 1, 'match_date': '2022-12-03', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Ahmad bin Ali Stadium', 'status': 'completed'},
    {'match_id': 51, 'home_team': 'France', 'away_team': 'Poland', 'home_score': 3, 'away_score': 1, 'match_date': '2022-12-04', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Thumama Stadium', 'status': 'completed'},
    {'match_id': 52, 'home_team': 'England', 'away_team': 'Senegal', 'home_score': 3, 'away_score': 0, 'match_date': '2022-12-04', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Bayt Stadium', 'status': 'completed'},
    {'match_id': 53, 'home_team': 'Japan', 'away_team': 'Croatia', 'home_score': 1, 'away_score': 1, 'match_date': '2022-12-05', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Janoub Stadium', 'status': 'completed'},
    {'match_id': 54, 'home_team': 'Brazil', 'away_team': 'South Korea', 'home_score': 4, 'away_score': 1, 'match_date': '2022-12-05', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Stadium 974', 'status': 'completed'},
    {'match_id': 55, 'home_team': 'Morocco', 'away_team': 'Spain', 'home_score': 0, 'away_score': 0, 'match_date': '2022-12-06', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Education City Stadium', 'status': 'completed'},
    {'match_id': 56, 'home_team': 'Portugal', 'away_team': 'Switzerland', 'home_score': 6, 'away_score': 1, 'match_date': '2022-12-06', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Lusail Stadium', 'status': 'completed'},
    # 1/4决赛
    {'match_id': 57, 'home_team': 'Croatia', 'away_team': 'Brazil', 'home_score': 1, 'away_score': 1, 'match_date': '2022-12-09', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Education City Stadium', 'status': 'completed'},
    {'match_id': 58, 'home_team': 'Netherlands', 'away_team': 'Argentina', 'home_score': 2, 'away_score': 2, 'match_date': '2022-12-09', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Lusail Stadium', 'status': 'completed'},
    {'match_id': 59, 'home_team': 'Morocco', 'away_team': 'Portugal', 'home_score': 1, 'away_score': 0, 'match_date': '2022-12-10', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Thumama Stadium', 'status': 'completed'},
    {'match_id': 60, 'home_team': 'England', 'away_team': 'France', 'home_score': 1, 'away_score': 2, 'match_date': '2022-12-10', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Bayt Stadium', 'status': 'completed'},
    # 半决赛
    {'match_id': 61, 'home_team': 'Argentina', 'away_team': 'Croatia', 'home_score': 3, 'away_score': 0, 'match_date': '2022-12-13', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Lusail Stadium', 'status': 'completed'},
    {'match_id': 62, 'home_team': 'France', 'away_team': 'Morocco', 'home_score': 2, 'away_score': 0, 'match_date': '2022-12-14', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Al Bayt Stadium', 'status': 'completed'},
    # 三四名决赛
    {'match_id': 63, 'home_team': 'Croatia', 'away_team': 'Morocco', 'home_score': 2, 'away_score': 1, 'match_date': '2022-12-17', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Khalifa International Stadium', 'status': 'completed'},
    # 决赛
    {'match_id': 64, 'home_team': 'Argentina', 'away_team': 'France', 'home_score': 3, 'away_score': 3, 'match_date': '2022-12-18', 'competition': 'World Cup 2022', 'season': '2022', 'venue': 'Lusail Stadium', 'status': 'completed'},
]

matches_df = pd.DataFrame(matches_data)
print(f'Created {len(matches_df)} matches')
matches_df.to_parquet(data_dir / 'matches.parquet')
print('Saved matches.parquet')

# ====== 生成模拟事件数据 ======
all_events = []
event_types = ['Shot', 'Pass', 'Foul Won', 'Yellow Card', 'Red Card', 'Goal', 'Corner', 'Free Kick']
shot_outcomes = ['Goal', 'Saved', 'Blocked', 'Wayward', 'Saved Off T']
pass_outcomes = [None, None, None, 'Incomplete', 'Out', 'Pass offside']

for match in matches_data:
    match_id = match['match_id']
    home = match['home_team']
    away = match['away_team']

    n_events = random.randint(80, 150)
    for i in range(n_events):
        minute = random.randint(0, 90)
        if minute >= 90:
            minute = 90 + random.randint(0, 7)

        team = home if random.random() < 0.52 else away
        event_type = random.choice(event_types)

        if team == home:
            x = random.uniform(30, 95)
        else:
            x = random.uniform(5, 70)
        y = random.uniform(5, 95)

        event = {
            'match_id': match_id,
            'team': team,
            'type': event_type,
            'minute': minute,
            'second': random.randint(0, 59),
            'location': [x, y],
            'player': f'Player_{team}_{random.randint(1, 23)}',
            'timestamp': f'00:{minute:02d}:{random.randint(0, 59):02d}'
        }

        if event_type == 'Shot':
            event['shot_outcome'] = random.choice(shot_outcomes)
            event['shot_body_part'] = random.choice(['Right Foot', 'Left Foot', 'Head'])
            event['shot_type'] = random.choice(['Open Play', 'Free Kick', 'Penalty', 'Corner'])
            dist = 100 - x
            angle = abs(y - 50) / 50
            event['shot_statsbomb_xg'] = round(np.exp(-0.07 * dist) * (1 - 0.3 * angle) * random.uniform(0.5, 1.5), 4)
        elif event_type == 'Pass':
            event['pass_outcome'] = random.choice(pass_outcomes)
            event['pass_end_location'] = [x + random.uniform(-30, 30), y + random.uniform(-30, 30)]

        all_events.append(event)

events_df = pd.DataFrame(all_events)
print(f'Created {len(events_df)} events across all matches')
events_df.to_parquet(data_dir / 'events.parquet')
print('Saved events.parquet')

teams_list = sorted(set([m['home_team'] for m in matches_data] + [m['away_team'] for m in matches_data]))
print(f'\nTotal teams: {len(teams_list)}')
print('Teams:', ', '.join(teams_list))

# ====== 如果指定--full，生成完整历史数据 ======
import sys
if "--full" in sys.argv:
    print("\n=== 生成完整历史国际比赛数据集 ===")
    intl_df = generate_historical_international_matches()
    print(f"历史数据: {len(intl_df)} 场, {intl_df['home_team'].nunique()} 支球队")
    print(f"赛事分布:\n{intl_df['tournament_type'].value_counts().to_string()}")

print('\nDone!')
