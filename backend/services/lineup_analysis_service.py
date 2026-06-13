"""
Lineup Analysis Service - 球队阵容综合分析

Pure computation engine evaluating 11-player lineups across 4 dimensions:
  1. Player Quality Index (35%) - individual player strength based on league tier + stats
  2. Positional Balance (25%) - formation coverage, natural position fit
  3. Chemistry (20%) - club/league teammates, national team experience
  4. Attack-Defense Balance (20%) - offensive vs defensive quality distribution

All computation is instant (no AI/API calls) → real-time updates on drag-and-drop.
"""

import json
from pathlib import Path
from typing import Optional, Dict, List, Any

DATA_DIR = Path(__file__).parent.parent / "data" / "knowledge"

# ── Position groups ────────────────────────────────────────────
GK_POSITIONS = {"GK"}
DEF_POSITIONS = {"CB", "LB", "RB", "LWB", "RWB", "DF"}
MID_POSITIONS = {"CDM", "CM", "CAM", "LM", "RM", "MF"}
FWD_POSITIONS = {"LW", "RW", "ST", "CF", "FW"}

# Natural slot compatibilities
SLOT_COMPAT: Dict[str, set] = {
    "GK": {"GK"},
    "CB": {"CB", "DF"},
    "LB": {"LB", "LWB", "DF"},
    "RB": {"RB", "RWB", "DF"},
    "LWB": {"LWB", "LB", "DF"},
    "RWB": {"RWB", "RB", "DF"},
    "CDM": {"CDM", "CM", "MF"},
    "CM": {"CM", "CDM", "CAM", "MF"},
    "CAM": {"CAM", "CM", "MF"},
    "LM": {"LM", "LW", "MF"},
    "RM": {"RM", "RW", "MF"},
    "LW": {"LW", "LM", "FW"},
    "RW": {"RW", "RM", "FW"},
    "ST": {"ST", "CF", "FW"},
    "CF": {"CF", "ST", "FW"},
}


class LineupAnalysisService:
    def __init__(self):
        self._league_tiers: Optional[Dict] = None
        self._set_pieces: Optional[Dict] = None
        self._projections: Optional[Dict] = None

    # ── data loading ───────────────────────────────────────────

    def _load_json(self, filename: str) -> Dict:
        path = DATA_DIR / filename
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    @property
    def league_data(self) -> Dict:
        if self._league_tiers is None:
            self._league_tiers = self._load_json("league_tiers.json")
        return self._league_tiers

    @property
    def set_pieces(self) -> Dict:
        if self._set_pieces is None:
            data = self._load_json("set_piece_takers.json")
            self._set_pieces = data.get("teams", {})
        return self._set_pieces

    @property
    def projections(self) -> Dict:
        if self._projections is None:
            data = self._load_json("team_projections.json")
            self._projections = data.get("teams", {})
        return self._projections

    # ── public API ─────────────────────────────────────────────

    def analyze_lineup(
        self,
        lineup: List[Dict],
        formation_id: str,
        team_name: str,
    ) -> Dict[str, Any]:
        """
        Full lineup evaluation.

        Args:
            lineup: List of 11 player dicts with keys:
                id, name, position, club, stats, attributes, number
            formation_id: e.g. "4-3-3", "4-4-2", "3-5-2", "4-2-3-1"
            team_name: National team name (e.g. "Croatia")

        Returns:
            {
                overall_score: int (0-100),
                dimensions: { player_quality, balance, chemistry, attack_defense },
                highlights: [...],
                concerns: [...],
                set_pieces: { penalty, corners, free_kick },
                projection: { win_pct, proj_goals, exp_games } | None
            }
        """
        # Fill missing slots with None
        padded = list(lineup[:11]) + [None] * (11 - len(lineup))

        # 1. Player Quality (35%)
        pqi_scores = [self._player_quality(p) for p in padded]
        pqi_avg = sum(pqi_scores) / max(len([s for s in pqi_scores if s > 0]), 1)
        player_quality = round(pqi_avg)

        # 2. Positional Balance (25%)
        balance = self._compute_balance(padded, formation_id)

        # 3. Chemistry (20%)
        chemistry = self._compute_chemistry(padded)

        # 4. Attack-Defense Balance (20%)
        att_def = self._compute_attack_defense(padded, formation_id)

        # Overall score
        overall = round(
            player_quality * 0.35
            + balance * 0.25
            + chemistry * 0.20
            + att_def * 0.20
        )

        # Generate insights
        highlights, concerns = self._generate_insights(
            padded, formation_id, player_quality, balance, chemistry, att_def
        )

        # Set pieces & projections
        sp = self._get_set_pieces(team_name)
        proj = self._get_projection(team_name)

        return {
            "overall_score": max(min(overall, 100), 0),
            "dimensions": {
                "player_quality": max(min(player_quality, 100), 0),
                "balance": max(min(balance, 100), 0),
                "chemistry": max(min(chemistry, 100), 0),
                "attack_defense": max(min(att_def, 100), 0),
            },
            "highlights": highlights,
            "concerns": concerns,
            "set_pieces": sp,
            "projection": proj,
        }

    # ── Dimension 1: Player Quality Index (35%) ─────────────────

    def _player_quality(self, player: Optional[Dict]) -> int:
        """Score a single player 0-100 based on league tier + performance + position fit."""
        if player is None:
            return 0

        club = (player.get("club") or "").strip()
        stats = player.get("stats") or {}
        has_real = stats.get("has_real_data") if isinstance(stats, dict) else False

        # 1. League tier base score
        tier = self._get_club_tier(club)
        tier_scores = self.league_data.get("tier_scores", {})
        tier_map = {"1": 95, "2": 80, "3": 65, "4": 50, "5": 35}
        for k, v in (tier_scores or tier_map).items():
            tier_map[str(k)] = v
        base = tier_map.get(str(tier), 35)

        # 2. Performance bonus (real data only, up to +15)
        bonus = 0
        if has_real and stats:
            minutes = stats.get("minutes", 0) or 0
            goals = stats.get("goals", 0) or 0
            assists = stats.get("assists", 0) or 0
            rating = stats.get("rating", 6.0) or 6.0

            if minutes >= 2000:
                bonus += 5
            elif minutes >= 900:
                bonus += 2
            if goals + assists >= 10:
                bonus += 5
            elif goals + assists >= 5:
                bonus += 2
            if isinstance(rating, (int, float)) and rating >= 7.0:
                bonus += 5
            elif isinstance(rating, (int, float)) and rating >= 6.5:
                bonus += 2

        return min(base + bonus, 100)

    def _get_club_tier(self, club: str) -> int:
        """Look up club's league tier. Falls back to 5 (unknown)."""
        if not club:
            return 5
        club_league = self.league_data.get("club_league", {})
        league_tiers = self.league_data.get("league_tiers", {})

        # Exact match
        league = club_league.get(club)
        if league:
            return league_tiers.get(league, 5)

        # Substring match (e.g., "AC Milan" matches "Milan")
        club_lower = club.lower()
        for c, l in club_league.items():
            if c.lower() in club_lower or club_lower in c.lower():
                return league_tiers.get(l, 5)

        return 5

    # ── Dimension 2: Positional Balance (25%) ──────────────────

    def _compute_balance(self, lineup: List[Optional[Dict]], formation_id: str) -> int:
        """Score positional balance based on coverage and natural fit."""
        formation_positions = self._get_formation_positions(formation_id)

        # Check which positions are filled
        filled = 0
        natural_fit = 0
        missing_key = False

        for i, slot_pos in enumerate(formation_positions):
            player = lineup[i] if i < len(lineup) else None
            if player is None:
                if slot_pos == "GK":
                    missing_key = True
                continue

            filled += 1
            player_pos = (player.get("position") or "").upper()

            # Natural fit check
            compat = SLOT_COMPAT.get(slot_pos, {slot_pos})
            if player_pos in compat or player_pos == slot_pos:
                natural_fit += 1

        # Coverage score (60%)
        if filled == 0:
            coverage = 0
        else:
            coverage = (filled / 11) * 100

        # Natural fit ratio (40%)
        fit_ratio = (natural_fit / max(filled, 1)) * 100

        score = coverage * 0.6 + fit_ratio * 0.4

        # Penalties
        if missing_key:
            score -= 30
        unfilled_def = sum(1 for i, s in enumerate(formation_positions)
                           if s in DEF_POSITIONS and (i >= len(lineup) or lineup[i] is None))
        score -= unfilled_def * 15

        # Too many players out of position
        out_of_pos = filled - natural_fit
        if out_of_pos > 3:
            score -= 10

        return max(min(round(score), 100), 0)

    def _get_formation_positions(self, formation_id: str) -> List[str]:
        """Get the 11 position slots for a given formation."""
        formations = {
            "4-3-3":  ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CM", "LW", "ST", "RW"],
            "4-4-2":  ["GK", "LB", "CB", "CB", "RB", "LM", "CM", "CM", "RM", "ST", "ST"],
            "3-5-2":  ["GK", "CB", "CB", "CB", "LWB", "CM", "CM", "CM", "RWB", "ST", "ST"],
            "4-2-3-1":["GK", "LB", "CB", "CB", "RB", "CDM", "CDM", "LW", "CAM", "RW", "ST"],
            "5-3-2":  ["GK", "LWB", "CB", "CB", "CB", "RWB", "CM", "CM", "CM", "ST", "ST"],
            "3-4-3":  ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "RM", "LW", "ST", "RW"],
            "4-5-1":  ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CM", "LW", "RW", "ST"],
        }
        return formations.get(formation_id, formations["4-3-3"])

    # ── Dimension 3: Chemistry (20%) ───────────────────────────

    def _compute_chemistry(self, lineup: List[Optional[Dict]]) -> int:
        """Score chemistry based on club teammates, same league, and experience."""
        players = [p for p in lineup if p is not None]
        if not players:
            return 0

        n = len(players)
        clubs: Dict[str, int] = {}
        leagues: Dict[str, int] = {}
        total_exp = 0

        for p in players:
            club = (p.get("club") or "").lower().strip()
            if club:
                clubs[club] = clubs.get(club, 0) + 1
                league = self._get_league_name(p.get("club", ""))
                if league:
                    leagues[league] = leagues.get(league, 0) + 1
            # National team experience proxy: use stats minutes as persistence indicator
            stats = p.get("stats") or {}
            minutes = stats.get("minutes", 0) if isinstance(stats, dict) else 0
            total_exp += min(minutes, 4000)

        # Club chemistry (50%): bonus for club teammates
        club_bonus = 0
        for count in clubs.values():
            if count >= 3:
                club_bonus += 20
            elif count == 2:
                club_bonus += 12
        club_bonus = min(club_bonus, 50)

        # League chemistry (30%): bonus for same league
        league_bonus = 0
        for count in leagues.values():
            if count >= 4:
                league_bonus += 15
            elif count >= 2:
                league_bonus += 8
        league_bonus = min(league_bonus, 30)

        # Experience bonus (20%): based on minutes played
        avg_exp = total_exp / max(n, 1)
        exp_bonus = min((avg_exp / 3000) * 20, 20)  # 3000min ≈ full

        return min(round(club_bonus + league_bonus + exp_bonus), 100)

    def _get_league_name(self, club: str) -> str:
        if not club:
            return ""
        club_league = self.league_data.get("club_league", {})
        league = club_league.get(club)
        if league:
            return league
        club_lower = club.lower()
        for c, l in club_league.items():
            if c.lower() in club_lower or club_lower in c.lower():
                return l
        return ""

    # ── Dimension 4: Attack-Defense Balance (20%) ──────────────

    def _compute_attack_defense(self, lineup: List[Optional[Dict]], formation_id: str) -> int:
        """Score attack-defense balance. Penalizes extremes: all-attack or all-defense."""
        formation_positions = self._get_formation_positions(formation_id)

        att_quality: List[int] = []
        def_quality: List[int] = []

        for i, slot_pos in enumerate(formation_positions):
            player = lineup[i] if i < len(lineup) else None
            score = self._player_quality(player) if player else 0

            if slot_pos in DEF_POSITIONS or slot_pos in GK_POSITIONS:
                def_quality.append(score)
            else:
                att_quality.append(score)

        avg_att = sum(att_quality) / max(len(att_quality), 1)
        avg_def = sum(def_quality) / max(len(def_quality), 1)

        # Ideal: both attack and defense are strong and balanced
        diff = abs(avg_att - avg_def)
        avg_both = (avg_att + avg_def) / 2

        # Deduction for imbalance
        imbalance_penalty = min(diff * 0.5, 30)

        # Also penalize if both are very low
        quality_score = min(avg_both, 100)

        return max(min(round(quality_score - imbalance_penalty), 100), 0)

    # ── Insights Generator ──────────────────────────────────────

    def _generate_insights(
        self,
        lineup: List[Optional[Dict]],
        formation_id: str,
        pqi: int,
        balance: int,
        chemistry: int,
        att_def: int,
    ) -> tuple:
        """Generate highlights and concerns in Chinese based on dimension scores."""
        highlights: List[str] = []
        concerns: List[str] = []

        players = [p for p in lineup if p is not None]
        formation_positions = self._get_formation_positions(formation_id)

        # Player quality highlights
        elite_players = [p for p in players if self._player_quality(p) >= 85]
        if elite_players:
            names = [p.get("name", "") for p in elite_players[:3]]
            highlights.append(f"核心球员: {', '.join(names)} — 效力顶级联赛，个人能力突出")

        if pqi >= 80:
            highlights.append("球员整体素质高，多数球员来自顶级联赛")
        elif pqi < 50:
            concerns.append("球员整体联赛等级偏低，面对强队时个体差距明显")

        # Balance highlights
        if balance >= 85:
            highlights.append("阵容配置均衡，各位置均有合适人选")
        elif balance < 55:
            concerns.append("阵容平衡性不足，部分位置缺乏合适球员")

        # Chemistry highlights
        if chemistry >= 70:
            highlights.append("阵容磨合度高 — 球员来自同联赛/同俱乐部，利于战术执行")
        elif chemistry < 35:
            concerns.append("阵容磨合度较低，球员分布在不同联赛，默契度存疑")

        # Attack-defence balance
        # Count attacking vs defensive slots filled with quality
        att_slots = sum(1 for i, s in enumerate(formation_positions)
                        if s not in DEF_POSITIONS and s not in GK_POSITIONS
                        and i < len(lineup) and lineup[i] is not None
                        and self._player_quality(lineup[i]) >= 70)
        def_slots = sum(1 for i, s in enumerate(formation_positions)
                        if (s in DEF_POSITIONS or s in GK_POSITIONS)
                        and i < len(lineup) and lineup[i] is not None
                        and self._player_quality(lineup[i]) >= 70)
        def_count = sum(1 for i, s in enumerate(formation_positions)
                        if s in DEF_POSITIONS)

        if att_slots >= 5 and def_slots >= def_count:
            highlights.append("攻防两端人员配置合理，攻守均衡")
        elif att_slots >= 5 and def_slots < max(def_count // 2, 1):
            concerns.append("攻击线豪华但防线偏弱，头重脚轻")
        elif def_slots >= def_count and att_slots < 2:
            concerns.append("防守人员充足但攻击线乏力，破门能力存疑")

        if att_def >= 80:
            highlights.append("攻防质量均衡，无明显短板")
        elif att_def < 45:
            concerns.append("攻防质量失衡，面对均衡型球队将吃力")

        # Fill minimum counts
        if len(highlights) < 2:
            if players:
                highlights.append(f"阵型{formation_id}配置，{len(players)}名球员就位")
        if len(concerns) < 1:
            if len(players) < 11:
                concerns.append(f"阵容不足11人，还有{11 - len(players)}个位置待补充")

        return highlights[:4], concerns[:3]

    # ── Set Pieces & Projections ───────────────────────────────

    def _get_set_pieces(self, team_name: str) -> Optional[Dict]:
        """Get set-piece taker info for a national team."""
        # Try exact match
        data = self.set_pieces.get(team_name)
        if data:
            return data
        # Try case-insensitive
        team_lower = team_name.lower()
        for name, info in self.set_pieces.items():
            if name.lower() == team_lower:
                return info
        return None

    def _get_projection(self, team_name: str) -> Optional[Dict]:
        """Get team projection data."""
        data = self.projections.get(team_name)
        if data:
            return data
        team_lower = team_name.lower()
        for name, info in self.projections.items():
            if name.lower() == team_lower:
                return info
        return None


# Singleton
lineup_analysis_service = LineupAnalysisService()
