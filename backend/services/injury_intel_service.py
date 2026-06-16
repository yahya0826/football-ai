"""
临哨快讯服务 — 赛前伤病情报 + 预测首发 + 球队状态
数据来源：RotoWire 文章爬取 + DeepSeek 中文翻译
若 RotoWire 不可用，fallback 到 DeepSeek 基于 ESPN 数据生成
"""
import os
import json
import re
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from openai import OpenAI

import httpx
from bs4 import BeautifulSoup

from .live_match_service import TEAM_NAMES_CN

DATA_DIR = Path(__file__).parent.parent / "data" / "intelligence"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 伤病状态中文标签
INJURY_STATUS_CN: Dict[str, str] = {
    "out": "缺阵",
    "doubtful": "出战成疑",
    "game-time decision": "赛前决定",
    "game-time call": "赛前决定",
    "probable": "大概率出战",
    "questionable": "可能缺阵",
    "day-to-day": "每日观察",
    "injured": "受伤",
    "suspended": "停赛",
}

# 常见球员中英文名映射（逐步扩展）
PLAYER_NAMES_CN: Dict[str, str] = {
    "Lionel Messi": "梅西",
    "Cristiano Ronaldo": "C罗",
    "Kylian Mbappé": "姆巴佩",
    "Kylian Mbappe": "姆巴佩",
    "Erling Haaland": "哈兰德",
    "Kevin De Bruyne": "德布劳内",
    "Mohamed Salah": "萨拉赫",
    "Harry Kane": "凯恩",
    "Lamine Yamal": "亚马尔",
    "Neymar": "内马尔",
    "Vinicius Jr.": "维尼修斯",
    "Jude Bellingham": "贝林厄姆",
    "Lautaro Martínez": "劳塔罗·马丁内斯",
    "Lautaro Martinez": "劳塔罗·马丁内斯",
    "Julian Alvarez": "阿尔瓦雷斯",
    "Julián Álvarez": "阿尔瓦雷斯",
    "Rodri": "罗德里",
    "Federico Valverde": "巴尔韦德",
    "Florian Wirtz": "维尔茨",
    "Jamal Musiala": "穆西亚拉",
    "Pedri": "佩德里",
    "Gavi": "加维",
    "Luka Modric": "莫德里奇",
    "Luka Modrić": "莫德里奇",
    "Robert Lewandowski": "莱万多夫斯基",
    "Raphinha": "拉菲尼亚",
    "Bruno Fernandes": "B费",
    "Bernardo Silva": "B席",
    "Phil Foden": "福登",
    "Bukayo Saka": "萨卡",
    "Declan Rice": "赖斯",
    "Virgil van Dijk": "范戴克",
    "Thibaut Courtois": "库尔图瓦",
    "Alisson": "阿利松",
    "Antoine Griezmann": "格列兹曼",
    "Ousmane Dembélé": "登贝莱",
    "Ronald Araujo": "阿劳霍",
    "Ronald Araújo": "阿劳霍",
    "Nico Williams": "尼科·威廉姆斯",
    "Kaoru Mitoma": "三笘薰",
    "Heung-min Son": "孙兴慜",
    "Son Heung-min": "孙兴慜",
    "Takefusa Kubo": "久保建英",
    "Martin Ødegaard": "厄德高",
    "Martin Odegaard": "厄德高",
    "David Alaba": "阿拉巴",
    "Kalidou Koulibaly": "库利巴利",
    "Achraf Hakimi": "阿什拉夫",
    "Emiliano Martínez": "E.马丁内斯",
    "Emiliano Martinez": "E.马丁内斯",
}


class InjuryIntelService:
    """赛前伤病情报服务"""

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        self.client = OpenAI(api_key=api_key) if api_key else None
        if self.client:
            self.client.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("AI_MODEL", "deepseek-chat")
        self._memory_cache: Dict[str, Dict] = {}

    # ── public API ────────────────────────────────────────────

    def get_injuries(self, date: str = None, force_refresh: bool = False) -> Dict:
        """获取指定日期的伤病情报（按队伍分组）"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        cache_file = DATA_DIR / f"injuries_{date}.json"

        # 检查缓存
        if not force_refresh and date in self._memory_cache:
            return self._memory_cache[date]

        if not force_refresh and cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                self._memory_cache[date] = cached
                return cached
            except Exception:
                pass

        # 生成新数据
        result = self._build_intel(date)
        result["_cache_ts"] = time.time()

        # 保存缓存
        self._memory_cache[date] = result
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return result

    def check_staleness_and_refresh(self, date: str = None):
        """检查缓存是否过期，过期则刷新（供后台调度器调用）"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        cache_file = DATA_DIR / f"injuries_{date}.json"
        if not cache_file.exists():
            print(f"[InjuryIntel] No cache for {date}, generating...")
            self.get_injuries(date)
            return

        ttl = self._get_ttl(date)
        mtime = cache_file.stat().st_mtime
        if time.time() - mtime > ttl:
            print(f"[InjuryIntel] Cache stale for {date}, refreshing...")
            self.get_injuries(date, force_refresh=True)

    # ── internal ──────────────────────────────────────────────

    def _get_ttl(self, date: str) -> int:
        """根据比赛临近程度返回缓存 TTL（秒）"""
        try:
            target = datetime.strptime(date, "%Y-%m-%d")
            now = datetime.now()
            hours_until = (target - now).total_seconds() / 3600

            if hours_until < 0:
                return 86400  # 已过的日期，24h
            elif hours_until < 6:
                return 3600   # 6h 内开赛，1h TTL
            elif hours_until < 24:
                return 10800  # 24h 内，3h TTL
            elif hours_until < 48:
                return 21600  # 48h 内，6h TTL
            else:
                return 43200  # 更早，12h TTL
        except Exception:
            return 21600

    def _build_intel(self, date: str) -> Dict:
        """构建完整伤病情报"""
        from .live_match_service import live_match_service

        matches = live_match_service.get_today_matches(date)
        teams_intel: Dict[str, Dict] = {}

        if not matches:
            return self._empty_result(date)

        # 先尝试 RotoWire 爬取
        raw_data = self._scrape_rotowire(matches, date)
        if raw_data:
            teams_intel = self._translate_intel(raw_data)
        else:
            # Fallback: 用 DeepSeek 基于球队知识库生成
            teams_intel = self._generate_fallback_intel(matches)

        return {
            "date": date,
            "last_updated": datetime.now().isoformat(),
            "teams": teams_intel,
            "total_teams": len(teams_intel),
        }

    def _scrape_rotowire(self, matches: List[Dict], date: str) -> Optional[List[Dict]]:
        """爬取 RotoWire 赛前预览文章，返回原始数据列表"""
        results = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # 先尝试获取 soccer 首页的文章列表
        listing_urls = [
            "https://www.rotowire.com/soccer/",
            "https://www.rotowire.com/soccer/articles.php",
        ]

        article_urls: Dict[str, str] = {}  # match_key -> url

        for listing_url in listing_urls:
            try:
                with httpx.Client(timeout=15, follow_redirects=True) as client:
                    resp = client.get(listing_url, headers=headers)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        # 找所有预览文章链接
                        for a in soup.find_all('a', href=True):
                            href = a['href']
                            if 'preview' in href.lower() or 'predicted-lineups' in href.lower():
                                full_url = href if href.startswith('http') else f"https://www.rotowire.com{href}"
                                # 尝试匹配球队名
                                for m in matches:
                                    home = m.get("home_team", "")
                                    away = m.get("away_team", "")
                                    key = f"{home.lower()}|{away.lower()}"
                                    if key not in article_urls:
                                        href_lower = href.lower()
                                        home_slug = home.lower().replace(" ", "-")
                                        away_slug = away.lower().replace(" ", "-")
                                        if home_slug in href_lower and away_slug in href_lower:
                                            article_urls[key] = full_url
                        if article_urls:
                            break
            except Exception as e:
                print(f"[InjuryIntel] Failed to fetch listing {listing_url}: {e}")
                continue

        # 如果首页没找到链接，尝试直接构造 URL 搜索
        if not article_urls:
            article_urls = self._search_article_urls(matches, headers)

        # 爬取每篇文章
        for match_key, url in article_urls.items():
            try:
                raw = self._parse_article(url, headers, match_key, matches)
                if raw:
                    results.append(raw)
            except Exception as e:
                print(f"[InjuryIntel] Failed to parse {url}: {e}")

        return results if results else None

    def _search_article_urls(self, matches: List[Dict], headers: Dict) -> Dict[str, str]:
        """通过 Google 搜索找到 RotoWire 文章 URL（当首页抓取失败时）"""
        import urllib.parse
        urls = {}

        for m in matches[:8]:
            home = m.get("home_team", "")
            away = m.get("away_team", "")
            key = f"{home.lower()}|{away.lower()}"
            query = f'site:rotowire.com "{home} vs {away}" preview predicted lineups 2026 world cup'
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"

            try:
                with httpx.Client(timeout=10, follow_redirects=True) as client:
                    resp = client.get(search_url, headers=headers)
                    if resp.status_code == 200:
                        # 从 Google 结果中提取 rotowire URL
                        hrefs = re.findall(r'https?://[^"\']*rotowire\.com[^"\']*', resp.text)
                        for href in hrefs:
                            href_clean = href.split('&')[0]
                            if 'preview' in href_clean.lower() or 'lineups' in href_clean.lower():
                                urls[key] = href_clean
                                break
            except Exception as e:
                print(f"[InjuryIntel] Search failed for {home} vs {away}: {e}")

        return urls

    def _parse_article(self, url: str, headers: Dict, match_key: str,
                       matches: List[Dict]) -> Optional[Dict]:
        """解析单篇 RotoWire 预览文章"""
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)

        # 匹配比赛队伍
        home_team = away_team = ""
        for m in matches:
            h = m.get("home_team", "")
            a = m.get("away_team", "")
            if f"{h.lower()}|{a.lower()}" == match_key:
                home_team = h
                away_team = a
                break

        if not home_team:
            parts = match_key.split("|")
            home_team = parts[0].title() if parts else ""
            away_team = parts[1].title() if len(parts) > 1 else ""

        return {
            "home_team": home_team,
            "away_team": away_team,
            "raw_text": text[:8000],  # 截取前8000字符
            "source_url": url,
        }

    def _translate_intel(self, raw_data: List[Dict]) -> Dict[str, Dict]:
        """用 DeepSeek 将英文情报翻译/结构化提取为中文"""
        if not self.client:
            return self._manual_extract(raw_data)

        teams_result: Dict[str, Dict] = {}

        for entry in raw_data:
            home = entry["home_team"]
            away = entry["away_team"]
            text = entry.get("raw_text", "")

            if not text:
                continue

            # 用 AI 提取结构化伤病情报
            home_cn = TEAM_NAMES_CN.get(home, home)
            away_cn = TEAM_NAMES_CN.get(away, away)

            prompt = f"""请从以下英文世界杯赛前预览文章中提取结构化信息，全部翻译为中文。

文章内容：
{text[:5000]}

请以 JSON 格式返回以下内容（只输出 JSON，不要其他文字）：
```json
{{
  "{home}": {{
    "name_cn": "{home_cn}",
    "injuries": [
      {{"player": "英文原名", "player_cn": "中文译名", "status": "out|doubtful|questionable|probable|day-to-day", "status_cn": "缺阵|出战成疑|可能缺阵|大概率出战|每日观察", "detail": "伤病详情（中文）"}}
    ],
    "predicted_lineup": {{
      "formation": "4-3-3",
      "players": ["球员1", "球员2", ...]
    }},
    "recent_form": "球队近期状态（中文，30字以内）",
    "score_prediction": "比分预测原文",
    "score_prediction_cn": "比分预测中文"
  }},
  "{away}": {{ ... 同上结构 ... }}
}}
```

要求：
1. 伤病状态判断：out→缺阵, doubtful→出战成疑, game-time decision→赛前决定, probable→大概率出战, questionable→可能缺阵
2. 球员中文名请使用常见译名（如 Messi→梅西, Mbappe→姆巴佩）
3. 如果文中没有明确信息，相应字段返回空数组或空字符串
4. predicted_lineup.players 只列出预测首发11人
"""

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是足球情报分析助手，擅长提取和翻译赛前信息。只输出 JSON。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                )
                result_text = response.choices[0].message.content.strip()
                # 提取 JSON 块
                json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(1)
                parsed = json.loads(result_text)
                if isinstance(parsed, dict):
                    for team_name, team_data in parsed.items():
                        if isinstance(team_data, dict):
                            teams_result[team_name] = team_data
            except Exception as e:
                print(f"[InjuryIntel] AI extraction failed for {home} vs {away}: {e}")
                # 对该场比赛做手动提取
                manual = self._manual_extract_single(entry)
                teams_result.update(manual)

        return teams_result

    def _manual_extract(self, raw_data: List[Dict]) -> Dict[str, Dict]:
        """手动从文章中提取关键信息（无需 AI）"""
        result: Dict[str, Dict] = {}
        for entry in raw_data:
            manual = self._manual_extract_single(entry)
            result.update(manual)
        return result

    def _manual_extract_single(self, entry: Dict) -> Dict[str, Dict]:
        """手动提取单篇文章信息"""
        home = entry.get("home_team", "")
        away = entry.get("away_team", "")
        text = entry.get("raw_text", "")
        home_cn = TEAM_NAMES_CN.get(home, home)
        away_cn = TEAM_NAMES_CN.get(away, away)

        def extract_injuries(team_name: str, txt: str) -> List[Dict]:
            injuries = []
            team_idx = txt.lower().find(team_name.lower())
            if team_idx == -1:
                return injuries
            # 在球队名周围搜索伤病关键词
            context = txt[max(0, team_idx-200):team_idx+2000]
            injury_keywords = ['out', 'injury', 'injured', 'doubtful', 'questionable',
                             'doubt', 'game-time', 'hamstring', 'calf', 'ankle', 'knee',
                             'quad', 'groin', 'thigh', 'muscular', 'issue', 'miss',
                             'absent', 'unavailable', 'fitness', 'strain', 'knock']

            lines = context.split('\n')
            for line in lines:
                line_lower = line.lower()
                if any(kw in line_lower for kw in injury_keywords) and len(line) > 20:
                    # 尝试提取球员名和状态
                    status = "questionable"
                    status_cn = "可能缺阵"
                    if re.search(r'\bout\b', line_lower):
                        status = "out"
                        status_cn = "缺阵"
                    elif 'doubtful' in line_lower or 'doubt' in line_lower:
                        status = "doubtful"
                        status_cn = "出战成疑"
                    elif 'probable' in line_lower:
                        status = "probable"
                        status_cn = "大概率出战"

                    # 尝试提取球员名（大写字母开头的名字）
                    name_match = re.search(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+(?:\s[A-Z][a-z]+)?)?)', line)
                    player_name = name_match.group(1) if name_match else ""
                    player_cn = PLAYER_NAMES_CN.get(player_name, player_name)

                    if len(player_name) > 3:
                        injuries.append({
                            "player": player_name,
                            "player_cn": player_cn,
                            "status": status,
                            "status_cn": status_cn,
                            "detail": line.strip()[:200],
                            "source": "rotowire",
                        })
                        if len(injuries) >= 5:
                            break
            return injuries

        return {
            home: {
                "name_cn": home_cn,
                "injuries": extract_injuries(home, text),
                "predicted_lineup": {"formation": "", "players": []},
                "recent_form": "",
                "score_prediction": "",
                "score_prediction_cn": "",
            },
            away: {
                "name_cn": away_cn,
                "injuries": extract_injuries(away, text),
                "predicted_lineup": {"formation": "", "players": []},
                "recent_form": "",
                "score_prediction": "",
                "score_prediction_cn": "",
            },
        }

    def _generate_fallback_intel(self, matches: List[Dict]) -> Dict[str, Dict]:
        """当 RotoWire 不可用时，用 DeepSeek 基于球队数据生成赛前情报"""
        if not self.client:
            return self._minimal_intel(matches)

        from .knowledge_service import knowledge_service
        from .live_match_service import live_match_service

        teams_result: Dict[str, Dict] = {}

        for m in matches:
            home = m.get("home_team", "")
            away = m.get("away_team", "")
            home_cn = TEAM_NAMES_CN.get(home, home)
            away_cn = TEAM_NAMES_CN.get(away, away)

            # 收集球队知识库信息
            home_profile = knowledge_service.get_team_profile(home) if knowledge_service else {}
            away_profile = knowledge_service.get_team_profile(away) if knowledge_service else {}

            home_tactical = home_profile.get("tactical_profile", {}) if home_profile else {}
            away_tactical = away_profile.get("tactical_profile", {}) if away_profile else {}

            prompt = f"""请为以下世界杯比赛生成赛前情报（中文，专业足球分析风格）。

比赛：{home_cn}({home}) vs {away_cn}({away})

主队{home_cn}信息：
- 战术风格：{json.dumps(home_tactical, ensure_ascii=False) if home_tactical else "数据暂缺"}
- 球队档案：{json.dumps(home_profile.get('basic_info', {}), ensure_ascii=False) if home_profile else "数据暂缺"}

客队{away_cn}信息：
- 战术风格：{json.dumps(away_tactical, ensure_ascii=False) if away_tactical else "数据暂缺"}
- 球队档案：{json.dumps(away_profile.get('basic_info', {}), ensure_ascii=False) if away_profile else "数据暂缺"}

请返回 JSON：
```json
{{
  "{home}": {{
    "name_cn": "{home_cn}",
    "injuries": [],
    "predicted_lineup": {{"formation": "", "players": []}},
    "recent_form": "基于球队实力的简要评估（中文，30字）",
    "score_prediction": "",
    "score_prediction_cn": ""
  }},
  "{away}": {{ ... }}
}}
```

注意：伤病信息如无可靠来源请留空，不要编造。"""

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是足球情报分析助手。只输出 JSON。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500,
                )
                result_text = response.choices[0].message.content.strip()
                json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(1)
                parsed = json.loads(result_text)
                if isinstance(parsed, dict):
                    teams_result.update(parsed)
            except Exception as e:
                print(f"[InjuryIntel] Fallback AI failed for {home} vs {away}: {e}")
                teams_result[home] = {
                    "name_cn": home_cn,
                    "injuries": [],
                    "predicted_lineup": {"formation": "", "players": []},
                    "recent_form": "情报暂缺",
                    "score_prediction": "",
                    "score_prediction_cn": "",
                }
                teams_result[away] = {
                    "name_cn": away_cn,
                    "injuries": [],
                    "predicted_lineup": {"formation": "", "players": []},
                    "recent_form": "情报暂缺",
                    "score_prediction": "",
                    "score_prediction_cn": "",
                }

        return teams_result

    def _minimal_intel(self, matches: List[Dict]) -> Dict[str, Dict]:
        """最小情报（无 AI 时的最终 fallback）"""
        result: Dict[str, Dict] = {}
        for m in matches:
            for team in [m.get("home_team", ""), m.get("away_team", "")]:
                if team and team not in result:
                    result[team] = {
                        "name_cn": TEAM_NAMES_CN.get(team, team),
                        "injuries": [],
                        "predicted_lineup": {"formation": "", "players": []},
                        "recent_form": "数据暂缺，请等待更新",
                        "score_prediction": "",
                        "score_prediction_cn": "",
                    }
        return result

    def _empty_result(self, date: str) -> Dict:
        return {
            "date": date,
            "last_updated": datetime.now().isoformat(),
            "teams": {},
            "total_teams": 0,
        }


# 全局实例
injury_intel_service = InjuryIntelService()
