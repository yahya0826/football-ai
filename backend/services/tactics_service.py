"""
战术分析服务 — 阵型分析、对位分析、球员适配、组合分析
"""
import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class TacticsService:
    """战术分析引擎"""

    def __init__(self, data_dir: str = "data/knowledge"):
        self.data_dir = Path(data_dir)
        self._formation_encyclopedia: List[Dict] = []
        self._formation_matchup: List[Dict] = []
        self._playing_styles: List[Dict] = []
        self._style_matchup: List[Dict] = []
        self._position_requirements: List[Dict] = []
        self._load_all()

    def _load_all(self):
        for filename, attr in [
            ("formation_encyclopedia.json", "_formation_encyclopedia"),
            ("formation_matchup.json", "_formation_matchup"),
            ("playing_styles.json", "_playing_styles"),
            ("style_matchup.json", "_style_matchup"),
            ("position_requirements.json", "_position_requirements"),
        ]:
            path = self.data_dir / filename
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    setattr(self, attr, json.load(f))

    # ═══════════════════════════════════════════════════════════
    # 数据查找
    # ═══════════════════════════════════════════════════════════

    def _get_formation(self, formation_id: str) -> Optional[Dict]:
        for f in self._formation_encyclopedia:
            if f["id"] == formation_id:
                return f
        return None

    def _get_position_req(self, position: str) -> Optional[Dict]:
        for r in self._position_requirements:
            if r["position"] == position:
                return r
        return None

    def _get_matchup_entry(self, home_form: str, away_form: str) -> Optional[Dict]:
        for m in self._formation_matchup:
            if m["home_formation"] == home_form and m["away_formation"] == away_form:
                return m
        return None

    def _get_style(self, style_id: str) -> Optional[Dict]:
        for s in self._playing_styles:
            if s["id"] == style_id:
                return s
        return None

    def _get_style_matchup(self, style_a: str, style_b: str) -> Optional[Dict]:
        for sm in self._style_matchup:
            if sm["style_a"] == style_a and sm["style_b"] == style_b:
                return sm
        return None

    # ═══════════════════════════════════════════════════════════
    # 位置映射
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def _position_to_line(position: str) -> str:
        if position == "GK":
            return "GK"
        if position in ("CB", "LB", "RB", "LWB", "RWB", "DF"):
            return "DEF"
        if position in ("CDM", "CM", "CAM", "LM", "RM", "MF"):
            return "MID"
        return "FWD"

    @staticmethod
    def _find_matching_position(away_positions: List[str], home_pos: str) -> Optional[int]:
        home_line = TacticsService._position_to_line(home_pos)
        for i, away_pos in enumerate(away_positions):
            if TacticsService._position_to_line(away_pos) == home_line:
                return i
        if home_pos in away_positions:
            return away_positions.index(home_pos)
        return None

    def _map_slot_to_req_key(self, position: str, formation: Dict) -> str:
        pos_reqs = formation.get("player_requirements", {})
        if position in pos_reqs:
            return position
        possible_names = [
            position,
            f"{position}_defensive", f"{position}_attacking",
            f"{position}_box_to_box", f"{position}_creative",
            f"{position}_holder", f"{position}_central",
            f"{position}_left", f"{position}_right",
            f"{position}_target", f"{position}_poacher",
            f"{position}_deep_playmaker",
        ]
        for name in possible_names:
            if name in pos_reqs:
                return name
        return position

    # ═══════════════════════════════════════════════════════════
    # 算法1: 球员-位置适配评分
    # ═══════════════════════════════════════════════════════════

    def score_player_for_position(
        self, attributes: Dict[str, int], position: str
    ) -> Dict:
        """基于加权欧氏距离计算球员对特定位置的适配分(0-100)"""
        req = self._get_position_req(position)
        if not req:
            return {"score": 60, "fit": "acceptable", "gaps": []}

        weight_vec = req["weight_vector"]
        ideal = req["ideal_profile"]

        total_weight = 0.0
        weighted_sq_dist = 0.0
        gaps = []

        for attr_name in ["speed", "shooting", "passing", "dribbling", "defending", "physical"]:
            w = weight_vec.get(attr_name, 0)
            if w == 0:
                continue
            player_val = float(attributes.get(attr_name, 60))
            ideal_val = float(ideal.get(attr_name, 60))
            normalized_diff = (ideal_val - player_val) / 100.0
            weighted_sq_dist += w * (normalized_diff ** 2)
            total_weight += w
            if abs(normalized_diff) > 0.15:
                dir_str = "低于" if player_val < ideal_val else "超过"
                gaps.append({
                    "attribute": attr_name,
                    "current": round(player_val),
                    "ideal": round(ideal_val),
                    "gap": round(ideal_val - player_val),
                    "direction": dir_str,
                })

        if total_weight == 0:
            return {"score": 60, "fit": "acceptable", "gaps": []}

        mse = weighted_sq_dist / total_weight
        score = max(0, min(100, 100 * (1 - np.sqrt(mse))))

        if score >= 80:
            fit = "excellent"
        elif score >= 65:
            fit = "good"
        elif score >= 50:
            fit = "acceptable"
        elif score >= 35:
            fit = "poor"
        else:
            fit = "misfit"

        return {"score": round(score), "fit": fit, "gaps": gaps}

    # ═══════════════════════════════════════════════════════════
    # 算法2: 球员-阵型-位置适配评分
    # ═══════════════════════════════════════════════════════════

    def score_player_for_formation(
        self, attributes: Dict[str, int], position: str, formation_id: str
    ) -> Dict:
        """在位置适配基础上叠加阵型特定最低属性要求"""
        base = self.score_player_for_position(attributes, position)

        formation = self._get_formation(formation_id)
        if not formation:
            return base

        req_key = self._map_slot_to_req_key(position, formation)
        pos_reqs = formation.get("player_requirements", {}).get(req_key, {})

        modifier = 0
        for attr_name in ["speed", "shooting", "passing", "dribbling", "defending", "physical"]:
            min_key = f"{attr_name}_min"
            if min_key in pos_reqs and pos_reqs[min_key] is not None:
                player_val = attributes.get(attr_name, 60)
                if player_val < pos_reqs[min_key]:
                    modifier -= 2

        base["score"] = max(10, min(100, base["score"] + modifier))
        base["formation_modifier"] = modifier
        return base

    # ═══════════════════════════════════════════════════════════
    # 算法3: 阵型对位分析
    # ═══════════════════════════════════════════════════════════

    def analyze_formation_matchup(
        self, home_formation: str, away_formation: str
    ) -> Dict:
        """分析两种阵型的战术对位关系"""
        entry = self._get_matchup_entry(home_formation, away_formation)
        home_entry = self._get_formation(home_formation)
        away_entry = self._get_formation(away_formation)

        if entry and home_entry and away_entry:
            return {
                "home_formation": home_formation,
                "away_formation": away_formation,
                "home_advantage_score": entry.get("home_advantage_score", 0),
                "key_battle_zones": entry.get("key_battle_zones", []),
                "statistical_tendency": entry.get("statistical_tendency", {}),
                "tactical_note": entry.get("tactical_note", ""),
                "home_strengths": home_entry.get("strengths", []),
                "away_strengths": away_entry.get("strengths", []),
                "home_weaknesses": home_entry.get("weaknesses", []),
                "away_weaknesses": away_entry.get("weaknesses", []),
            }

        if home_entry and away_entry:
            return self._compute_matchup_from_principles(home_formation, away_formation)

        return {
            "home_formation": home_formation,
            "away_formation": away_formation,
            "home_advantage_score": 0,
            "key_battle_zones": [],
            "tactical_note": "阵型数据不完整，无法生成完整分析",
        }

    def _compute_matchup_from_principles(
        self, home_form: str, away_form: str
    ) -> Dict:
        """基于阵型原理推算对位分析（回退方案）"""
        home_entry = self._get_formation(home_form)
        away_entry = self._get_formation(away_form)

        home_mid = sum(1 for p in home_entry["position_ids"]
                      if self._position_to_line(p) == "MID")
        away_mid = sum(1 for p in away_entry["position_ids"]
                      if self._position_to_line(p) == "MID")

        advantage = (home_mid - away_mid) * 0.05
        advantage = max(-0.3, min(0.3, advantage))

        return {
            "home_formation": home_form,
            "away_formation": away_form,
            "home_advantage_score": round(advantage, 2),
            "key_battle_zones": ["中场控制权", "边路对决"],
            "tactical_note": f"基于阵型原理推算：{home_form}对阵{away_form}。中场人数对比{home_mid}vs{away_mid}是核心变量。",
            "home_strengths": home_entry.get("strengths", []) if home_entry else [],
            "away_strengths": away_entry.get("strengths", []) if away_entry else [],
            "home_weaknesses": home_entry.get("weaknesses", []) if home_entry else [],
            "away_weaknesses": away_entry.get("weaknesses", []) if away_entry else [],
        }

    # ═══════════════════════════════════════════════════════════
    # 算法4: 阵容vs阵容对位分析（核心）
    # ═══════════════════════════════════════════════════════════

    def analyze_lineup_matchup(
        self,
        home_lineup: List[Dict],
        away_lineup: List[Dict],
        home_formation: str,
        away_formation: str,
    ) -> Dict:
        """
        完整的首发阵容对位分析。
        输入: 两队11人阵容（每人含position和attributes）
        """
        formation_analysis = self.analyze_formation_matchup(home_formation, away_formation)

        home_formation_info = self._get_formation(home_formation)
        away_formation_info = self._get_formation(away_formation)

        # 位置组对比
        position_comparisons = self._compare_position_groups(
            home_lineup, away_lineup, home_formation, away_formation
        )

        # 关键对位
        key_matchups = self._build_key_matchups(
            home_lineup, away_lineup, home_formation, away_formation
        )

        # 球队属性画像
        home_profile = self._compute_team_profile(home_lineup, home_formation)
        away_profile = self._compute_team_profile(away_lineup, away_formation)

        # 综合优势
        attr_advantage = self._attribute_advantage_score(
            home_profile["overall"], away_profile["overall"]
        )
        matchup_advantage = self._count_matchup_advantages(key_matchups)

        overall = (
            0.40 * formation_analysis.get("home_advantage_score", 0)
            + 0.35 * attr_advantage
            + 0.25 * matchup_advantage
        )

        return {
            "formation_matchup": formation_analysis,
            "position_comparisons": position_comparisons,
            "key_matchups": key_matchups,
            "home_team_profile": home_profile,
            "away_team_profile": away_profile,
            "overall_tactical_advantage": round(overall, 3),
            "interpretation": self._interpret_advantage(round(overall, 3)),
        }

    def _compare_position_groups(
        self, home: List[Dict], away: List[Dict],
        home_form: str, away_form: str
    ) -> List[Dict]:
        comparisons = []
        for zone in ["GK", "DEF", "MID", "FWD"]:
            home_players = [p for p in home
                           if self._position_to_line(p.get("position", "")) == zone]
            away_players = [p for p in away
                           if self._position_to_line(p.get("position", "")) == zone]
            if home_players and away_players:
                home_avg = self._average_attributes(home_players)
                away_avg = self._average_attributes(away_players)
                advantage = self._compare_attribute_profiles(home_avg, away_avg)
                comparisons.append({
                    "zone": zone,
                    "zone_cn": {"GK": "门将", "DEF": "后卫线", "MID": "中场", "FWD": "锋线"}[zone],
                    "home_avg_attributes": home_avg,
                    "away_avg_attributes": away_avg,
                    "advantage": advantage,
                    "home_players_count": len(home_players),
                    "away_players_count": len(away_players),
                })
        return comparisons

    def _build_key_matchups(
        self, home: List[Dict], away: List[Dict],
        home_form: str, away_form: str
    ) -> List[Dict]:
        matchups = []
        home_formation = self._get_formation(home_form)
        away_formation = self._get_formation(away_form)

        if not home_formation or not away_formation:
            return matchups

        home_positions = home_formation.get("position_ids", [])
        away_positions = away_formation.get("position_ids", [])

        for i, pos in enumerate(home_positions):
            if i >= len(home):
                continue
            away_idx = self._find_matching_position(away_positions, pos)
            if away_idx is not None and away_idx < len(away):
                h_p = home[i]
                a_p = away[away_idx]
                h_attrs = h_p.get("attributes", {})
                a_attrs = a_p.get("attributes", {})

                h_fit = self.score_player_for_formation(h_attrs, pos, home_form)
                a_fit = self.score_player_for_formation(a_attrs, pos, away_form)

                adv = "home" if h_fit["score"] > a_fit["score"] + 5 \
                    else ("away" if a_fit["score"] > h_fit["score"] + 5 else "balanced")

                matchups.append({
                    "position": pos,
                    "position_cn": self._position_cn(pos),
                    "home_player": {
                        "name": h_p.get("name", ""),
                        "player_id": h_p.get("player_id", ""),
                        "fit_score": h_fit["score"],
                        "fit": h_fit["fit"],
                    },
                    "away_player": {
                        "name": a_p.get("name", ""),
                        "player_id": a_p.get("player_id", ""),
                        "fit_score": a_fit["score"],
                        "fit": a_fit["fit"],
                    },
                    "advantage": adv,
                })
        return matchups

    # ═══════════════════════════════════════════════════════════
    # 算法5: 球队属性画像
    # ═══════════════════════════════════════════════════════════

    def _compute_team_profile(
        self, lineup: List[Dict], formation_id: str
    ) -> Dict:
        overall = {"speed": 0, "shooting": 0, "passing": 0,
                   "dribbling": 0, "defending": 0, "physical": 0}
        line_profiles = {
            "DEF": defaultdict(float), "MID": defaultdict(float), "FWD": defaultdict(float)
        }
        line_counts = {"DEF": 0, "MID": 0, "FWD": 0}
        total_count = 0

        formation = self._get_formation(formation_id)
        position_ids = formation.get("position_ids", []) if formation else []

        for i, player in enumerate(lineup):
            if not player:
                continue
            attrs = player.get("attributes", {})
            if not attrs:
                continue
            pos = position_ids[i] if i < len(position_ids) else player.get("position", "FWD")
            line = self._position_to_line(pos)

            for attr in ["speed", "shooting", "passing", "dribbling", "defending", "physical"]:
                val = attrs.get(attr, 60)
                overall[attr] += val
                if line in line_profiles:
                    line_profiles[line][attr] += val
                    line_counts[line] += 1
            total_count += 1

        if total_count > 0:
            for attr in overall:
                overall[attr] = round(overall[attr] / total_count)

        for line in line_profiles:
            if line_counts[line] > 0:
                for attr in line_profiles[line]:
                    line_profiles[line][attr] = round(
                        line_profiles[line][attr] / line_counts[line]
                    )

        return {
            "overall": overall,
            "lines": {
                line: dict(line_profiles[line]) for line in line_profiles
                if line_counts[line] > 0
            },
        }

    # ═══════════════════════════════════════════════════════════
    # 算法6: 球队风格识别
    # ═══════════════════════════════════════════════════════════

    def identify_team_style(
        self, lineup: List[Dict], formation_id: str
    ) -> Dict:
        """根据阵容属性识别最匹配的战术风格"""
        profile = self._compute_team_profile(lineup, formation_id)
        overall = profile["overall"]

        scores = []
        for style in self._playing_styles:
            score = self._compute_style_match_score(overall, formation_id, style)
            scores.append({
                "style_id": style["id"],
                "style_name": style["name"],
                "style_name_cn": style.get("name_cn", style["name"]),
                "match_score": round(score, 1),
            })

        scores.sort(key=lambda x: x["match_score"], reverse=True)

        top = scores[0] if scores else None
        return {
            "primary_style": top,
            "top_styles": scores[:3],
            "formation": formation_id,
        }

    def _compute_style_match_score(
        self, overall: Dict[str, int], formation_id: str, style: Dict
    ) -> float:
        reqs = style.get("required_team_attributes", {})
        total = 0.0

        weights = {
            "avg_passing_min": 0.20, "avg_dribbling_min": 0.15,
            "avg_speed_min": 0.18, "avg_shooting_min": 0.15,
            "avg_defending_min": 0.17, "avg_physical_min": 0.15,
        }

        attr_map = {
            "avg_passing_min": "passing", "avg_dribbling_min": "dribbling",
            "avg_speed_min": "speed", "avg_shooting_min": "shooting",
            "avg_defending_min": "defending", "avg_physical_min": "physical",
        }

        for req_key, attr_name in attr_map.items():
            if req_key in reqs:
                team_val = overall.get(attr_name, 60)
                req_val = reqs[req_key]
                match = min(1.0, team_val / max(req_val, 1))
                total += match * weights.get(req_key, 0.15)

        # 阵型加分
        if formation_id in style.get("preferred_formations", []):
            total += 0.08

        return min(1.0, total) * 100

    # ═══════════════════════════════════════════════════════════
    # 风格对位分析
    # ═══════════════════════════════════════════════════════════

    def analyze_style_matchup(self, style_a: str, style_b: str) -> Dict:
        entry = self._get_style_matchup(style_a, style_b)
        if entry:
            style_a_data = self._get_style(style_a)
            style_b_data = self._get_style(style_b)
            return {
                "style_a": style_a,
                "style_a_name": style_a_data.get("name_cn", style_a) if style_a_data else style_a,
                "style_b": style_b,
                "style_b_name": style_b_data.get("name_cn", style_b) if style_b_data else style_b,
                "advantage_for_a": entry["advantage_for_a"],
                "dynamics": entry["dynamics"],
                "key_factors": entry["key_factors"],
            }

        # 检查反向
        reverse = self._get_style_matchup(style_b, style_a)
        if reverse:
            return self.analyze_style_matchup(style_b, style_a)

        return {
            "style_a": style_a,
            "style_b": style_b,
            "advantage_for_a": 0,
            "dynamics": "两种风格的数据暂不可用",
            "key_factors": [],
        }

    # ═══════════════════════════════════════════════════════════
    # 工具方法
    # ═══════════════════════════════════════════════════════════

    def _average_attributes(self, players: List[Dict]) -> Dict[str, int]:
        if not players:
            return {}
        sums = defaultdict(float)
        counts = defaultdict(int)
        for p in players:
            attrs = p.get("attributes", {})
            for k in ["speed", "shooting", "passing", "dribbling", "defending", "physical"]:
                val = attrs.get(k)
                if val is not None:
                    sums[k] += val
                    counts[k] += 1
        return {k: round(sums[k] / counts[k]) if counts[k] > 0 else 60 for k in sums}

    def _compare_attribute_profiles(
        self, profile_a: Dict, profile_b: Dict
    ) -> str:
        """比较两组属性画像，判定哪个更强"""
        score_a = 0
        score_b = 0
        for attr in ["speed", "shooting", "passing", "dribbling", "defending", "physical"]:
            a = profile_a.get(attr, 60)
            b = profile_b.get(attr, 60)
            if a > b + 4:
                score_a += 1
            elif b > a + 4:
                score_b += 1
        if score_a > score_b:
            return "home"
        elif score_b > score_a:
            return "away"
        return "balanced"

    def _attribute_advantage_score(
        self, home_profile: Dict, away_profile: Dict
    ) -> float:
        """基于两队总体属性差异计算优势分"""
        total_diff = 0
        for attr in ["speed", "shooting", "passing", "dribbling", "defending", "physical"]:
            h = home_profile.get(attr, 60)
            a = away_profile.get(attr, 60)
            total_diff += (h - a) / 100.0
        return max(-0.35, min(0.35, total_diff / 6))

    def _count_matchup_advantages(self, matchups: List[Dict]) -> float:
        if not matchups:
            return 0
        home_wins = sum(1 for m in matchups if m["advantage"] == "home")
        away_wins = sum(1 for m in matchups if m["advantage"] == "away")
        return (home_wins - away_wins) / max(len(matchups), 1)

    @staticmethod
    def _interpret_advantage(score: float) -> str:
        if score > 0.15:
            return "主队有明显的战术优势"
        elif score > 0.05:
            return "主队略微占优"
        elif score > -0.05:
            return "两队战术对位均衡"
        elif score > -0.15:
            return "客队略微占优"
        return "客队有明显的战术优势"

    @staticmethod
    def _position_cn(pos: str) -> str:
        mapping = {
            "GK": "门将", "CB": "中卫", "LB": "左后卫", "RB": "右后卫",
            "LWB": "左翼卫", "RWB": "右翼卫", "CDM": "后腰", "CM": "中前卫",
            "CAM": "前腰", "LM": "左前卫", "RM": "右前卫",
            "LW": "左边锋", "RW": "右边锋", "ST": "中锋", "CF": "影锋",
            "DF": "后卫", "MF": "中场", "FW": "前锋",
        }
        return mapping.get(pos, pos)

    # ═══════════════════════════════════════════════════════════
    # 公共查询接口
    # ═══════════════════════════════════════════════════════════

    def get_all_formations(self) -> List[Dict]:
        return [
            {
                "id": f["id"], "name": f["name"], "name_cn": f.get("name_cn", f["name"]),
                "category": f.get("category", ""), "description": f.get("description", ""),
                "strengths": f.get("strengths", []), "weaknesses": f.get("weaknesses", []),
            }
            for f in self._formation_encyclopedia
        ]

    def get_formation_detail(self, formation_id: str) -> Optional[Dict]:
        formation = self._get_formation(formation_id)
        if not formation:
            return None
        return formation

    def get_all_styles(self) -> List[Dict]:
        return [
            {
                "id": s["id"], "name": s["name"], "name_cn": s.get("name_cn", s["name"]),
                "description": s.get("description", ""), "principles": s.get("principles", []),
                "preferred_formations": s.get("preferred_formations", []),
            }
            for s in self._playing_styles
        ]

    def get_position_requirements(self) -> List[Dict]:
        return self._position_requirements

    # ═══════════════════════════════════════════════════════════
    # AI 战术解说 (DeepSeek)
    # ═══════════════════════════════════════════════════════════

    def generate_tactical_commentary(
        self,
        home_team: str,
        away_team: str,
        home_formation: str,
        away_formation: str,
        home_style: Optional[Dict] = None,
        away_style: Optional[Dict] = None,
        home_lineup: Optional[List[Dict]] = None,
        away_lineup: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        使用DeepSeek生成AI战术解说。
        综合阵型对位、风格对位、阵容适配数据，生成专业战术预览。
        """
        client = None
        api_key = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        if api_key:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            client.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

        # 收集结构化战术数据
        formation_matchup = self.analyze_formation_matchup(home_formation, away_formation)
        style_matchup = None
        if home_style and away_style:
            home_style_id = home_style.get("primary_style") or home_style.get("style_id", "")
            away_style_id = away_style.get("primary_style") or away_style.get("style_id", "")
            if home_style_id and away_style_id:
                style_matchup = self.analyze_style_matchup(home_style_id, away_style_id)

        # 阵容分析
        lineup_analysis = None
        if home_lineup and away_lineup:
            try:
                lineup_analysis = self.analyze_lineup_matchup(
                    home_lineup, away_lineup, home_formation, away_formation
                )
            except Exception:
                pass

        commentary_data = {
            "match": f"{home_team} vs {away_team}",
            "formations": {
                "home": home_formation,
                "away": away_formation,
                "home_advantage": formation_matchup.get("home_advantage_score", 0),
                "key_zones": formation_matchup.get("key_battle_zones", []),
                "tactical_note": formation_matchup.get("tactical_note", ""),
            },
            "style_matchup": style_matchup,
            "lineup_analysis": lineup_analysis,
        }

        # 如果AI可用，生成叙事性战术解说
        narrative = None
        if client:
            try:
                narrative = self._generate_narrative(client, commentary_data, home_team, away_team)
            except Exception as e:
                narrative = self._build_structured_summary(commentary_data, home_team, away_team)
        else:
            narrative = self._build_structured_summary(commentary_data, home_team, away_team)

        return {
            "structured_data": commentary_data,
            "narrative": narrative,
        }

    def _generate_narrative(self, client, data: Dict, home: str, away: str) -> str:
        """用DeepSeek生成叙事性战术分析"""
        formations = data["formations"]
        style_data = data.get("style_matchup")
        lineup_data = data.get("lineup_analysis")

        prompt_parts = [
            f"你是一位资深的足球战术分析师。请为 {home} vs {away} 这场比赛撰写一段专业的赛前战术预览。",
            "",
            f"## 阵型对位",
            f"主队{home}: {formations['home']}阵型",
            f"客队{away}: {formations['away']}阵型",
            f"阵型优势分: {formations['home_advantage']:+.2f} (正值=主队优势)",
            f"关键争夺区域: {', '.join(formations.get('key_zones', []))}",
        ]

        if style_data:
            prompt_parts.extend([
                "",
                f"## 风格对位",
                f"主队风格: {style_data.get('style_a_name', '')}",
                f"客队风格: {style_data.get('style_b_name', '')}",
                f"风格优劣: 优势值{style_data.get('advantage_for_a', 0):+.2f}",
                f"对位动态: {style_data.get('dynamics', '')}",
                f"关键因素: {', '.join(style_data.get('key_factors', []))}",
            ])

        if lineup_data:
            interpretation = lineup_data.get("interpretation", "")
            overall = lineup_data.get("overall_tactical_advantage", 0)
            prompt_parts.extend([
                "",
                f"## 阵容分析",
                f"综合战术优势: {overall:+.3f}",
                f"整体判断: {interpretation}",
            ])

        prompt_parts.extend([
            "",
            "请从以下维度进行分析（300-500字）：",
            "1. 阵型对位的核心矛盾点",
            "2. 风格碰撞的战术看点",
            "3. 决定比赛走向的关键区域",
            "4. 战术层面的胜负手预测",
            "",
            "要求：专业但不晦涩，让球迷能看懂战术博弈的核心逻辑。直接开始分析，不使用markdown标题。",
        ])

        prompt = "\n".join(prompt_parts)
        model = os.environ.get("AI_MODEL", "deepseek-chat")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位专业的足球战术分析师，擅长用通俗语言解释复杂的战术概念。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=800,
        )

        return response.choices[0].message.content

    def _build_structured_summary(self, data: Dict, home: str, away: str) -> str:
        """无AI时的结构化总结"""
        formations = data["formations"]
        parts = [
            f"{home} vs {away} 赛前战术分析",
            f"",
            f"阵型: {home} {formations['home']} vs {away} {formations['away']}",
            f"阵型优势分: {formations['home_advantage']:+.2f}",
            f"关键区域: {', '.join(formations.get('key_zones', []))}",
        ]
        style_data = data.get("style_matchup")
        if style_data:
            parts.extend([
                f"",
                f"风格对位: {style_data.get('style_a_name', '')} vs {style_data.get('style_b_name', '')}",
                f"对位动态: {style_data.get('dynamics', '')}",
            ])
        lineup_data = data.get("lineup_analysis")
        if lineup_data:
            parts.append(f"综合判断: {lineup_data.get('interpretation', '')}")
        return "\n".join(parts)


# 全局实例
tactics_service = TacticsService()
