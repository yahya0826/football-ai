"""
球队名称标准化 — 跨数据源模糊匹配
支持 StatsBomb / Kaggle / FIFA 三种数据源的名称映射
"""
from difflib import get_close_matches
import re


class TeamNormalizer:
    """标准化不同数据源的球队名称"""

    # 主要球队别名映射
    ALIASES = {
        "united states": "united states",
        "usa": "united states",
        "us": "united states",
        "korea republic": "south korea",
        "korea dpr": "north korea",
        "korea, republic of": "south korea",
        "korea, democratic people's republic of": "north korea",
        "côte d'ivoire": "ivory coast",
        "cote d'ivoire": "ivory coast",
        "czech republic": "czech republic",
        "czechia": "czech republic",
        "bosnia and herzegovina": "bosnia-herzegovina",
        "bosnia-herzegovina": "bosnia-herzegovina",
        "bosnia & herzegovina": "bosnia-herzegovina",
        "trinidad and tobago": "trinidad and tobago",
        "trinidad & tobago": "trinidad and tobago",
        "st. kitts and nevis": "st. kitts and nevis",
        "saint kitts and nevis": "st. kitts and nevis",
        "saint vincent and the grenadines": "st. vincent and the grenadines",
        "st. vincent and the grenadines": "st. vincent and the grenadines",
        "saint lucia": "st. lucia",
        "st. lucia": "st. lucia",
        "antigua and barbuda": "antigua and barbuda",
        "antigua & barbuda": "antigua and barbuda",
        "papua new guinea": "papua new guinea",
        "timor-leste": "east timor",
        "east timor": "east timor",
        "the gambia": "gambia",
        "gambia": "gambia",
        "congo dr": "dr congo",
        "dr congo": "dr congo",
        "democratic republic of the congo": "dr congo",
        "congo": "congo",
        "cape verde": "cape verde",
        "cabo verde": "cape verde",
        "united arab emirates": "united arab emirates",
        "uae": "united arab emirates",
        "kingdom of saudi arabia": "saudi arabia",
        "china pr": "china",
        "china, people's republic of": "china",
        "türkiye": "turkey",
        "turkey": "turkey",
        "north macedonia": "north macedonia",
        "macedonia": "north macedonia",
        "eswatini": "eswatini",
        "swaziland": "eswatini",
    }

    def __init__(self, known_teams: list = None):
        self.known_teams = set(known_teams) if known_teams else set()
        self.cache: dict[str, str] = {}

    def normalize(self, name: str) -> str:
        """标准化一个球队名"""
        if not isinstance(name, str):
            return str(name) if name else "unknown"

        key = name.strip().lower()
        if key in self.cache:
            return self.cache[key]

        # Step 1: 精确别名匹配
        if key in self.ALIASES:
            result = self.ALIASES[key].title()
            self.cache[key] = result
            return result

        # Step 2: 清理特殊字符
        cleaned = re.sub(r'[^\w\s\-]', '', key).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)

        if cleaned in self.ALIASES:
            result = self.ALIASES[cleaned].title()
            self.cache[key] = result
            return result

        # Step 3: 模糊匹配
        if self.known_teams:
            known_lower = {t.lower(): t for t in self.known_teams}
            matches = get_close_matches(cleaned, list(known_lower.keys()), n=1, cutoff=0.85)
            if matches:
                result = known_lower[matches[0]]
                self.cache[key] = result
                return result

        # Step 4: 返回清洗后的名称
        result = cleaned.title()
        self.cache[key] = result
        return result

    def add_known_teams(self, teams: list):
        """添加已知球队列表用于模糊匹配"""
        for t in teams:
            if isinstance(t, str):
                self.known_teams.add(t.strip())
