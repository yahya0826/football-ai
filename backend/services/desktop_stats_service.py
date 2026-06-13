"""
Parse desktop WorldCup2026 stats.txt files and aggregate match data into season totals.
"""
import os
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field

DESKTOP_ROOT = Path("C:/Users/ASUS/Desktop/WorldCup2026")

# Desktop short names → API full team names
NAME_MAP: Dict[str, str] = {
    "Bosnia and Herzegovina": "Bosnia and Herzegovina",
    "Bosnia": "Bosnia and Herzegovina",
    "Cape Verde": "Cape Verde",
    "Cape": "Cape Verde",
    "Curacao": "Curaçao",
    "Curaçao": "Curaçao",
    "DR Congo": "DR Congo",
    "DR": "DR Congo",
    "Ivory Coast": "Ivory Coast",
    "Ivory": "Ivory Coast",
    "New Zealand": "New Zealand",
    "New": "New Zealand",
    "Saudi Arabia": "Saudi Arabia",
    "Saudi": "Saudi Arabia",
    "South Africa": "South Africa",
    "South Korea": "South Korea",
    "United States": "United States",
    "USA": "United States",
    "Czechia": "Czech Republic",
    "Czech Republic": "Czech Republic",
}


@dataclass
class AggregatedStats:
    appearances: int = 0
    starts: int = 0
    minutes: int = 0
    goals: int = 0
    assists: int = 0
    pk_scored: int = 0
    pk_attempted: int = 0
    shots: int = 0
    shots_on_target: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    fouls: int = 0
    fouled: int = 0
    offsides: int = 0
    crosses: int = 0
    tackles_won: int = 0
    interceptions: int = 0
    own_goals: int = 0
    pk_won: int = 0
    pk_conceded: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0

    def to_dict(self) -> dict:
        apps = max(self.appearances, 1)
        mins = max(self.minutes, 1)
        return {
            "appearances": self.appearances,
            "starts": self.starts,
            "minutes": self.minutes,
            "goals": self.goals,
            "assists": self.assists,
            "pk_scored": self.pk_scored,
            "pk_attempted": self.pk_attempted,
            "shots": self.shots,
            "shots_on_target": self.shots_on_target,
            "yellow_cards": self.yellow_cards,
            "red_cards": self.red_cards,
            "fouls": self.fouls,
            "fouled": self.fouled,
            "offsides": self.offsides,
            "crosses": self.crosses,
            "tackles_won": self.tackles_won,
            "interceptions": self.interceptions,
            "own_goals": self.own_goals,
            "pk_won": self.pk_won,
            "pk_conceded": self.pk_conceded,
            "wins": self.wins,
            "draws": self.draws,
            "losses": self.losses,
            "goals_p90": round(self.goals / mins * 90, 2),
            "assists_p90": round(self.assists / mins * 90, 2),
            "shots_p90": round(self.shots / mins * 90, 2),
            "tackles_p90": round(self.tackles_won / mins * 90, 2),
            "shot_conversion": round(self.goals / max(self.shots, 1) * 100, 1),
            "shot_accuracy": round(self.shots_on_target / max(self.shots, 1) * 100, 1),
            "start_rate": round(self.starts / max(self.appearances, 1) * 100, 1),
            "data_source": "desktop",
        }


class DesktopStatsService:
    """Parse desktop WorldCup2026 stats.txt files and provide aggregated stats."""

    def __init__(self):
        self._cache: Dict[Tuple[str, str], Optional[AggregatedStats]] = {}

    def _extract_team_en(self, folder_name: str) -> str:
        """Extract English team name from folder like 'South_Africa_南非'."""
        parts = folder_name.split("_")
        # Find where Chinese characters start
        eng_parts = []
        for p in parts:
            if p and "一" <= p[0] <= "鿿":
                break
            eng_parts.append(p)
        return " ".join(eng_parts)

    def _normalize_team_name(self, desktop_team_en: str) -> str:
        """Map desktop team name to API team name."""
        if desktop_team_en in NAME_MAP:
            return NAME_MAP[desktop_team_en]
        return desktop_team_en

    def _normalize_player_name(self, folder_name: str) -> str:
        """Convert player folder name like 'Luka_Modrić_C' to 'Luka Modrić'."""
        # Strip _C (captain) or _VC (vice-captain) suffix
        name = folder_name
        if name.endswith("_C"):
            name = name[:-2]
        elif name.endswith("_VC"):
            name = name[:-3]
        return name.replace("_", " ")

    def _parse_result(self, result_str: str) -> Tuple[int, int, int]:
        """Parse W/D/L from result string like 'W 3–0' or 'D 1–1'."""
        if not result_str:
            return (0, 0, 0)
        w = d = l = 0
        if result_str.startswith("W"):
            w = 1
        elif result_str.startswith("D"):
            d = 1
        elif result_str.startswith("L"):
            l = 1
        return (w, d, l)

    def _is_summary_row(self, fields: List[str]) -> bool:
        """Check if row is the W-D-L summary/footer line."""
        if not fields or not fields[0]:
            return False
        first = fields[0].strip()
        # Summary row has pattern like "25-13-11" (W-D-L)
        # Date rows have pattern like "2025-07-01" — exclude those (4-digit year)
        if re.match(r"^\d{4}-\d{2}-\d{2}$", first):
            return False
        return bool(re.match(r"^\d+-\d+-\d+$", first))

    def _is_footer(self, line: str) -> bool:
        """Check if line is a footer like 'Includes all matches from...'"""
        return line.startswith("Includes") or line.startswith("Stats include")

    def _safe_int(self, val: str) -> int:
        """Parse int from string, returning 0 for empty/invalid."""
        if not val or not val.strip():
            return 0
        try:
            return int(val.strip())
        except (ValueError, TypeError):
            return 0

    def parse_stats_file(self, filepath: str) -> Optional[AggregatedStats]:
        """Parse a single stats.txt file and return aggregated stats."""
        if not os.path.exists(filepath):
            return None

        # Check for empty file
        if os.path.getsize(filepath) == 0:
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            return None

        if len(lines) < 2:
            return None

        stats = AggregatedStats()
        in_match_rows = False
        header_found = False

        for line in lines:
            line = line.rstrip("\n").rstrip("\r")

            # Skip empty lines
            if not line.strip():
                continue

            # Skip footer lines
            if self._is_footer(line.strip()):
                continue

            # Split by tab
            fields = line.split("\t")

            # Skip summary rows (W-D-L pattern)
            if self._is_summary_row(fields):
                # Also try to parse summary for aggregate stats if we haven't collected any
                if stats.appearances > 0:
                    continue
                # If no match rows were parsed, extract from summary
                if len(fields) >= 5:
                    # Parse W-D-L
                    wdl_parts = fields[0].strip().split("-")
                    if len(wdl_parts) == 3:
                        stats.wins = self._safe_int(wdl_parts[0])
                        stats.draws = self._safe_int(wdl_parts[1])
                        stats.losses = self._safe_int(wdl_parts[2])
                    # Games: "38/49" format
                    gp = fields[1].strip().split("/")
                    if len(gp) >= 1:
                        stats.appearances = self._safe_int(gp[0])
                    if len(gp) >= 2:
                        stats.starts = self._safe_int(gp[0])
                    stats.minutes = self._safe_int(fields[2].replace(",", "")) if len(fields) > 2 else 0
                    stats.goals = self._safe_int(fields[3]) if len(fields) > 3 else 0
                    stats.assists = self._safe_int(fields[4]) if len(fields) > 4 else 0
                    stats.pk_scored = self._safe_int(fields[5]) if len(fields) > 5 else 0
                    stats.pk_attempted = self._safe_int(fields[6]) if len(fields) > 6 else 0
                    stats.shots = self._safe_int(fields[7]) if len(fields) > 7 else 0
                    stats.shots_on_target = self._safe_int(fields[8]) if len(fields) > 8 else 0
                    stats.yellow_cards = self._safe_int(fields[9]) if len(fields) > 9 else 0
                    stats.red_cards = self._safe_int(fields[10]) if len(fields) > 10 else 0
                    stats.fouls = self._safe_int(fields[11]) if len(fields) > 11 else 0
                    stats.fouled = self._safe_int(fields[12]) if len(fields) > 12 else 0
                    stats.offsides = self._safe_int(fields[13]) if len(fields) > 13 else 0
                    stats.crosses = self._safe_int(fields[14]) if len(fields) > 14 else 0
                    stats.tackles_won = self._safe_int(fields[15]) if len(fields) > 15 else 0
                    stats.interceptions = self._safe_int(fields[16]) if len(fields) > 16 else 0
                continue

            # Skip header lines
            if "Performance" in fields[0] or "Date\t" in line or (
                len(fields) > 1 and fields[0].strip() == "Date"
            ):
                header_found = True
                in_match_rows = True
                continue

            # Parse match data rows
            if not in_match_rows or not header_found:
                continue

            # Need at least date + result
            if len(fields) < 6:
                continue

            date = fields[0].strip()
            if not date or not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
                continue

            # Match row found
            stats.appearances += 1

            # Start type (column 8, 0-indexed)
            start = fields[8].strip() if len(fields) > 8 else ""
            if start in ("Y", "Y*"):
                stats.starts += 1

            # Minutes (column 10)
            stats.minutes += self._safe_int(fields[10]) if len(fields) > 10 else 0

            # Goals (11), Assists (12)
            stats.goals += self._safe_int(fields[11]) if len(fields) > 11 else 0
            stats.assists += self._safe_int(fields[12]) if len(fields) > 12 else 0

            # PK (13, 14)
            stats.pk_scored += self._safe_int(fields[13]) if len(fields) > 13 else 0
            stats.pk_attempted += self._safe_int(fields[14]) if len(fields) > 14 else 0

            # Shots (15), SoT (16)
            stats.shots += self._safe_int(fields[15]) if len(fields) > 15 else 0
            stats.shots_on_target += self._safe_int(fields[16]) if len(fields) > 16 else 0

            # Cards (17, 18)
            stats.yellow_cards += self._safe_int(fields[17]) if len(fields) > 17 else 0
            stats.red_cards += self._safe_int(fields[18]) if len(fields) > 18 else 0

            # Fouls (19), Fouled (20), Offsides (21), Crosses (22)
            stats.fouls += self._safe_int(fields[19]) if len(fields) > 19 else 0
            stats.fouled += self._safe_int(fields[20]) if len(fields) > 20 else 0
            stats.offsides += self._safe_int(fields[21]) if len(fields) > 21 else 0
            stats.crosses += self._safe_int(fields[22]) if len(fields) > 22 else 0

            # Tackles (23), Interceptions (24)
            stats.tackles_won += self._safe_int(fields[23]) if len(fields) > 23 else 0
            stats.interceptions += self._safe_int(fields[24]) if len(fields) > 24 else 0

            # OG (25), PKwon (26), PKcon (27)
            stats.own_goals += self._safe_int(fields[25]) if len(fields) > 25 else 0
            stats.pk_won += self._safe_int(fields[26]) if len(fields) > 26 else 0
            stats.pk_conceded += self._safe_int(fields[27]) if len(fields) > 27 else 0

            # Result (column 5, 0-indexed)
            result = fields[5].strip() if len(fields) > 5 else ""
            w, d, l = self._parse_result(result)
            stats.wins += w
            stats.draws += d
            stats.losses += l

        return stats if stats.appearances > 0 else None

    def get_player_stats(self, team_name: str, player_name: str) -> Optional[dict]:
        """Get aggregated stats for a specific player from desktop data."""
        cache_key = (team_name, player_name)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            return cached.to_dict() if cached else None

        # Find the player's stats.txt on desktop
        filepath = self._find_stats_file(team_name, player_name)
        if filepath is None:
            self._cache[cache_key] = None
            return None

        stats = self.parse_stats_file(str(filepath))
        self._cache[cache_key] = stats
        return stats.to_dict() if stats else None

    def _find_stats_file(self, team_name: str, player_name: str) -> Optional[Path]:
        """Locate the desktop stats.txt for a given player and team."""
        if not DESKTOP_ROOT.exists():
            return None

        # Normalize player name for matching (strip diacritics, lowercase with underscores)
        player_key = self._name_key(player_name)

        for group_dir in sorted(DESKTOP_ROOT.iterdir()):
            if not group_dir.is_dir():
                continue
            for team_dir in sorted(group_dir.iterdir()):
                if not team_dir.is_dir():
                    continue
                team_en = self._extract_team_en(team_dir.name)
                team_api = self._normalize_team_name(team_en)

                if team_api.lower() != team_name.lower():
                    continue

                # Search for player folder
                for player_dir in team_dir.iterdir():
                    if not player_dir.is_dir():
                        continue
                    dir_key = self._name_key(player_dir.name)
                    if dir_key == player_key:
                        return player_dir / "stats.txt"

        return None

    def _name_key(self, name: str) -> str:
        """Create a diacritic-insensitive, case-insensitive comparison key."""
        import unicodedata
        clean = name.lower()
        if clean.endswith("_c") or clean.endswith("_vc"):
            clean = clean.rsplit("_", 1)[0]
        # Strip all separators (spaces, underscores, hyphens)
        clean = clean.replace("_", "").replace(" ", "").replace("-", "")
        ascii_name = unicodedata.normalize("NFKD", clean).encode("ascii", "ignore").decode()
        return ascii_name

    def get_team_players_stats(self, team_name: str) -> Dict[str, dict]:
        """Get all players' stats for a team from desktop data."""
        result = {}
        if not DESKTOP_ROOT.exists():
            return result

        for group_dir in sorted(DESKTOP_ROOT.iterdir()):
            if not group_dir.is_dir():
                continue
            for team_dir in sorted(group_dir.iterdir()):
                if not team_dir.is_dir():
                    continue
                team_en = self._extract_team_en(team_dir.name)
                team_api = self._normalize_team_name(team_en)

                if team_api.lower() != team_name.lower():
                    continue

                # Found team directory, scan all players
                for player_dir in team_dir.iterdir():
                    if not player_dir.is_dir():
                        continue
                    stats_file = player_dir / "stats.txt"
                    player_name = self._normalize_player_name(player_dir.name)

                    stats = self.parse_stats_file(str(stats_file))
                    if stats:
                        result[player_name] = stats.to_dict()

                return result  # Found matching team, done

        return result


desktop_stats_service = DesktopStatsService()
