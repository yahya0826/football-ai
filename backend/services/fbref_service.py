"""
FBref 球员数据抓取服务 - 获取2025-26赛季七大联赛完整球员统计
"""
import re
import json
import time
import pandas as pd
import httpx
from pathlib import Path
from typing import Dict, List, Optional

# 七大联赛 fbref 配置
LEAGUES = {
    "Big5": {
        "name": "五大联赛综合",
        "url": "https://fbref.com/en/comps/Big5/Big-5-European-Leagues-Stats",
        "comp_id": "Big5",
    },
    "Eredivisie": {
        "name": "荷甲",
        "url": "https://fbref.com/en/comps/23/Eredivisie-Stats",
        "comp_id": "23",
    },
    "Primeira-Liga": {
        "name": "葡超",
        "url": "https://fbref.com/en/comps/32/Primeira-Liga-Stats",
        "comp_id": "32",
    },
}

STAT_TYPES = ["standard", "shooting", "passing", "defense", "possession"]

# 俱乐部名标准化映射（解决 Wikipedia 与 fbref 名称不一致）
CLUB_ALIASES = {
    "manchester united": "Manchester Utd",
    "man utd": "Manchester Utd",
    "man united": "Manchester Utd",
    "manchester city": "Manchester City",
    "man city": "Manchester City",
    "tottenham hotspur": "Tottenham",
    "wolverhampton wanderers": "Wolves",
    "leeds united": "Leeds United",
    "newcastle united": "Newcastle Utd",
    "nottingham forest": "Nott'ham Forest",
    "bayern munich": "Bayern Munich",
    "fc bayern münchen": "Bayern Munich",
    "borussia dortmund": "Dortmund",
    "bayer leverkusen": "Leverkusen",
    "rb leipzig": "RB Leipzig",
    "real madrid": "Real Madrid",
    "fc barcelona": "Barcelona",
    "atlético madrid": "Atlético Madrid",
    "atl. madrid": "Atlético Madrid",
    "paris saint-germain": "Paris S-G",
    "psg": "Paris S-G",
    "fc porto": "Porto",
    "benfica": "Benfica",
    "sporting cp": "Sporting CP",
    "ajax": "Ajax",
    "psv eindhoven": "PSV Eindhoven",
    "feyenoord": "Feyenoord",
    "napoli": "Napoli",
    "juventus": "Juventus",
    "ac milan": "Milan",
    "internazionale": "Inter",
    "inter milan": "Inter",
}


class FBrefService:
    """FBref 球员数据服务"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "fbref_raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, pd.DataFrame] = {}

    def fetch_all_leagues(self) -> Dict[str, pd.DataFrame]:
        """抓取所有联赛的球员数据，返回 {league_key: combined_df}"""
        all_data = {}
        for league_key, league_info in LEAGUES.items():
            print(f"\n📊 抓取 {league_info['name']} ({league_key})...")
            df = self.fetch_league_players(league_key)
            if df is not None and not df.empty:
                all_data[league_key] = df
                print(f"  获取 {len(df)} 名球员")
            else:
                print(f"  未获取到数据")
            time.sleep(3)  # 礼貌延迟
        return all_data

    def fetch_league_players(self, league_key: str) -> Optional[pd.DataFrame]:
        """抓取单个联赛的球员综合数据"""
        league_info = LEAGUES[league_key]

        all_stats = {}
        for stat_type in STAT_TYPES:
            df = self._fetch_stat_table(league_info["url"], stat_type)
            if df is not None and not df.empty:
                all_stats[stat_type] = df
            time.sleep(1.2)

        if not all_stats:
            return None

        # 以 standard 表为基础，合并其他统计
        base = all_stats.get("standard")
        if base is None:
            return None

        result = base.copy()
        result["league"] = league_info["name"]
        result["league_key"] = league_key

        # 合并 shooting
        if "shooting" in all_stats:
            result = self._merge_stats(result, all_stats["shooting"], [
                "Shots_Total", "Shots_on_target", "xG", "npxG",
                "Shots_total_distance", "Average_Shot_Distance",
            ])

        # 合并 passing
        if "passing" in all_stats:
            result = self._merge_stats(result, all_stats["passing"], [
                "Passes_Total", "Passes_completed", "Pass_Completion%",
                "Progressive_Passes", "Key_Passes", "Passes_Into_Final_Third",
                "Crosses", "Through_Balls",
            ])

        # 合并 defense
        if "defense" in all_stats:
            result = self._merge_stats(result, all_stats["defense"], [
                "Tackles", "Interceptions", "Blocks",
                "Clearances", "Aerials_Won", "Aerial_win%",
            ])

        # 合并 possession
        if "possession" in all_stats:
            result = self._merge_stats(result, all_stats["possession"], [
                "Touches", "Take_Ons_Attempted", "Take_Ons_Success%",
                "Carries", "Carries_Progressive_Distance",
                "Fouls_Drawn", "Dispossessed",
            ])

        # 保存原始数据
        raw_path = self.raw_dir / f"{league_key}_2025-26.parquet"
        result.to_parquet(raw_path)
        print(f"  已保存: {raw_path}")

        return result

    def _fetch_stat_table(self, base_url: str, stat_type: str) -> Optional[pd.DataFrame]:
        """抓取单个统计类型的表格"""
        try:
            html = httpx.get(base_url, timeout=30).text

            # fbref 将表格数据放在 HTML 注释中
            table_id = f"stats_{stat_type}"
            table_html = self._extract_commented_table(html, table_id)
            if not table_html:
                return None

            # 如果表格在注释中，用正则提取；直接读 HTML
            dfs = pd.read_html(table_html)
            if not dfs:
                return None

            df = dfs[0]

            # fbref 表格通常有多级列名，取第一行作为列名
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(str(c).strip() for c in col if 'Unnamed' not in str(c)).strip('_')
                              for col in df.columns]

            # 清理列名中的空格和特殊字符
            df.columns = [re.sub(r'\s+', '_', str(c)).strip() for c in df.columns]

            # 移除重复行（每20行出现的列标题重复行）
            first_col = df.columns[0]
            df = df[~df[first_col].astype(str).str.contains("Rk|Player", na=False)]

            # 丢弃全空行
            df = df.dropna(how="all")

            return df
        except Exception as e:
            print(f"  警告: 获取 {stat_type} 失败: {e}")
            return None

    def _extract_commented_table(self, html: str, table_id: str) -> Optional[str]:
        """从 HTML 注释中提取表格"""
        # 找到对应的 div
        div_pattern = rf'<div[^>]*id="{table_id}"[^>]*>(.*?)</div>\s*(?:</div>\s*)?$'
        # 使用更精确的匹配
        pattern = rf'id="{table_id}"'
        match = re.search(pattern, html)
        if not match:
            return None

        # 从匹配位置往后找 <!-- 和对应的 -->
        start = match.start()
        snippet = html[start:start + 200000]  # 取足够长的片段

        # 找 <!-- 注释开始
        comment_start = snippet.find("<!--")
        if comment_start == -1:
            # 表格可能直接渲染在 div 中（没有被注释），尝试直接提取
            div_start = snippet.find("<div")
            div_end = self._find_matching_close(snippet, div_start)
            if div_end > 0:
                return snippet[div_start:div_end]
            return None

        comment_end = snippet.find("-->", comment_start)
        if comment_end == -1:
            return None

        comment_content = snippet[comment_start + 4:comment_end].strip()

        # 注释内容可能是完整的表格 HTML
        if "<table" in comment_content:
            return comment_content
        # 也可能是完整的 div 内表格
        if "<div" in comment_content and "<table" in comment_content:
            return comment_content

        return None

    def _find_matching_close(self, html: str, start: int) -> int:
        """简单找到匹配的闭合 div"""
        depth = 0
        i = start
        while i < len(html):
            if html[i:i+4] == "<div":
                depth += 1
                i += 4
            elif html[i:i+5] == "</div":
                depth -= 1
                if depth == 0:
                    return i + 6
                i += 5
            else:
                i += 1
        return -1

    def _merge_stats(self, base: pd.DataFrame, other: pd.DataFrame,
                     columns: List[str]) -> pd.DataFrame:
        """按球员名合并统计数据"""
        result = base.copy()
        player_col_base = self._find_player_column(base)
        player_col_other = self._find_player_column(other)

        if not player_col_base or not player_col_other:
            return result

        # 在小表上建立映射
        name_to_vals = {}
        for _, row in other.iterrows():
            name = str(row[player_col_other]).strip()
            vals = {}
            for col in columns:
                actual_col = self._find_column_by_name(other, col)
                if actual_col:
                    vals[col] = row[actual_col]
            name_to_vals[name.lower()] = vals

        for col in columns:
            result[col] = None

        for idx, row in result.iterrows():
            name = str(row[player_col_base]).strip().lower()
            if name in name_to_vals:
                for col, val in name_to_vals[name].items():
                    result.at[idx, col] = val

        return result

    def _find_player_column(self, df: pd.DataFrame) -> Optional[str]:
        """查找球员名列"""
        for col in df.columns:
            col_lower = col.lower()
            if "player" in col_lower or "name" in col_lower:
                return col
        # 通常第一列是 Rk，第二列是 Player
        if len(df.columns) > 1:
            return df.columns[1]
        return None

    def _find_column_by_name(self, df: pd.DataFrame, name: str) -> Optional[str]:
        """模糊查找列名"""
        name_lower = name.lower().replace("_", " ").strip()
        for col in df.columns:
            col_lower = col.lower().replace("_", " ").strip()
            if name_lower in col_lower or col_lower in name_lower:
                return col
        # 更宽松的匹配
        keywords = name_lower.split()
        for col in df.columns:
            col_lower = col.lower().replace("_", " ").strip()
            if all(kw in col_lower for kw in keywords):
                return col
        return None

    def normalize_player_name(self, name: str) -> str:
        """标准化球员名（去除音调、多余空格）"""
        name = name.strip()
        # 常见特殊字符标准化
        replacements = {
            "é": "e", "è": "e", "ê": "e", "ë": "e",
            "á": "a", "à": "a", "â": "a", "ã": "a", "ä": "a",
            "í": "i", "ì": "i", "î": "i", "ï": "i",
            "ó": "o", "ò": "o", "ô": "o", "õ": "o", "ö": "o",
            "ú": "u", "ù": "u", "û": "u", "ü": "u",
            "ñ": "n", "ç": "c", "ý": "y",
            "ć": "c", "č": "c", "š": "s", "ž": "z", "đ": "d",
            "ł": "l", "ń": "n", "ś": "s", "ź": "z",
        }
        result = ""
        for char in name:
            result += replacements.get(char, char)
        return result.lower().strip()

    def match_player(self, squad_player: dict, fbref_df: pd.DataFrame) -> Optional[dict]:
        """将大名单球员与 fbref 数据匹配"""
        squad_name = self.normalize_player_name(squad_player["name"])
        squad_club = squad_player.get("club", "").lower().strip()

        player_col = self._find_player_column(fbref_df)
        if not player_col:
            return None

        # 第一轮：精确姓名 + 俱乐部匹配
        for _, row in fbref_df.iterrows():
            fb_name = self.normalize_player_name(str(row[player_col]))
            if squad_name == fb_name:
                stats = self._extract_player_stats(row)
                stats["match_confidence"] = "high"
                return stats

        # 第二轮：姓名包含关系
        for _, row in fbref_df.iterrows():
            fb_name = self.normalize_player_name(str(row[player_col]))
            if self._fuzzy_name_match(squad_name, fb_name):
                stats = self._extract_player_stats(row)
                stats["match_confidence"] = "medium"
                return stats

        return None

    def _fuzzy_name_match(self, name1: str, name2: str) -> bool:
        """宽松姓名匹配"""
        if name1 in name2 or name2 in name1:
            return True
        parts1 = name1.split()
        parts2 = name2.split()
        if len(parts1) >= 2 and len(parts2) >= 2:
            # 姓相同（通常是最后一个词）
            if parts1[-1] == parts2[-1]:
                # 且至少一个名的前几个字母匹配
                shared_first = sum(1 for p1 in parts1[:-1] for p2 in parts2[:-1]
                                   if p1[:3] == p2[:3])
                if shared_first >= 1:
                    return True
        return False

    def _extract_player_stats(self, row) -> dict:
        """从 fbref 行数据提取标准化球员统计"""
        stats = {"rating": 0.0}
        row_dict = row.to_dict()

        for key, val in row_dict.items():
            key_lower = key.lower()
            try:
                num_val = float(val) if not isinstance(val, (int, float)) or pd.notna(val) else 0.0
            except (ValueError, TypeError):
                num_val = 0.0

            # 标准数据
            if "goals" in key_lower and "xg" not in key_lower and "own" not in key_lower:
                stats["goals"] = int(num_val)
            elif "assists" in key_lower:
                stats["assists"] = int(num_val)
            elif "minutes" in key_lower and "90s" not in key_lower:
                stats["minutes"] = int(num_val)
            elif "appearances" in key_lower or "mp" == key_lower.strip() or "_mp" in key_lower:
                stats["appearances"] = int(num_val)
            elif "starts" in key_lower:
                stats["starts"] = int(num_val)
            elif "yellow" in key_lower or "crdy" in key_lower:
                stats["yellow_cards"] = int(num_val)
            elif "red" in key_lower or "crdr" in key_lower:
                stats["red_cards"] = int(num_val)
            # 射门
            elif "shots_total" in key_lower or "shots_" == key_lower:
                stats["shots_total"] = int(num_val)
            elif "shots_on_target" in key_lower or "sot" in key_lower:
                stats["shots_on_target"] = int(num_val)
            elif key_lower == "xg" or "expected_goals" in key_lower:
                stats["xg"] = round(num_val, 2)
            # 传球
            elif "passes_total" in key_lower or "passes_completed" in key_lower:
                stats[key_lower.replace(" ", "_")] = int(num_val)
            elif "pass_completion" in key_lower:
                stats["pass_accuracy"] = round(num_val, 1)
            elif "progressive_passes" in key_lower:
                stats["progressive_passes"] = int(num_val)
            elif "key_passes" in key_lower:
                stats["key_passes"] = int(num_val)
            # 防守
            elif key_lower == "tackles":
                stats["tackles"] = int(num_val)
            elif "interceptions" in key_lower:
                stats["interceptions"] = int(num_val)
            elif "clearances" in key_lower:
                stats["clearances"] = int(num_val)
            elif "blocks" in key_lower:
                stats["blocks"] = int(num_val)
            # 控球
            elif "touches" in key_lower and "att" not in key_lower:
                stats["touches"] = int(num_val)
            elif "take_ons_success" in key_lower:
                stats["dribble_success_rate"] = round(num_val, 1)

        # 推导评分: 基于关键指标的综合评分 (0-10)
        goals = stats.get("goals", 0)
        assists = stats.get("assists", 0)
        xg = stats.get("xg", 0)
        pass_acc = stats.get("pass_accuracy", 0)
        appearances = max(stats.get("appearances", 1), 1)

        rating = 6.0
        rating += min(goals / appearances * 10, 1.5)
        rating += min(assists / appearances * 8, 1.0)
        rating += min((pass_acc - 70) / 30, 1.0) if pass_acc > 70 else 0
        stats["rating"] = round(min(rating, 9.9), 1)

        return stats


# 全局实例
fbref_service = FBrefService()


if __name__ == "__main__":
    print("=== FBref 球员数据抓取 ===")
    service = FBrefService()
    data = service.fetch_all_leagues()
    for league, df in data.items():
        print(f"\n{LEAGUES[league]['name']}: {len(df)} 名球员")
        print(f"  列: {list(df.columns[:10])}...")
