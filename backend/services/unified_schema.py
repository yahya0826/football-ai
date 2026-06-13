"""
统一球员数据模型 v1.0
- 定义标准化数据类、字段映射表
- 多源数据合并优先级策略
- per90 衍生计算、雷达图六维推导
- 可信度评级和数据溯源
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum
import math
import datetime


# ═══════════════════════════════════════════════════════════
# 枚举定义
# ═══════════════════════════════════════════════════════════

class DataSource(str, Enum):
    FPL = "FPL"
    SOFASCORE = "Sofascore"
    FOTMOB = "FotMob"
    API_FOOTBALL = "API-Football"
    ESTIMATED = "estimated"


class Confidence(str, Enum):
    HIGH = "high"         # 有 xG/xA + 传球/盘带/防守各至少2项
    MEDIUM = "medium"     # 至少有 rating + goals + assists + minutes
    LOW = "low"           # 仅有估算值
    NONE = "none"         # 无任何数据


# ═══════════════════════════════════════════════════════════
# 统一球员数据模型
# ═══════════════════════════════════════════════════════════

@dataclass
class BaseStats:
    """基础统计（所有位置通用，必填级别）"""
    appearances: int = 0
    starts: int = 0
    minutes: int = 0
    goals: int = 0
    assists: int = 0
    rating: float = 0.0
    yellow_cards: int = 0
    red_cards: int = 0


@dataclass
class ShootingStats:
    """射门维度"""
    xg: Optional[float] = None
    xg_per_shot: Optional[float] = None
    np_xg: Optional[float] = None
    shots_total: Optional[int] = None
    shots_on_target: Optional[int] = None
    shot_accuracy: Optional[float] = None
    penalty_goals: Optional[int] = None
    big_chances_missed: Optional[int] = None


@dataclass
class PassingStats:
    """传球维度"""
    passes_accuracy: Optional[float] = None
    key_passes: Optional[int] = None
    big_chances_created: Optional[int] = None
    xa: Optional[float] = None
    crosses_accuracy: Optional[float] = None
    long_balls_accuracy: Optional[float] = None
    progressive_passes: Optional[int] = None


@dataclass
class DribblingStats:
    """盘带/控球维度"""
    dribbles_success_rate: Optional[float] = None
    touches: Optional[int] = None
    touches_in_box: Optional[int] = None
    dispossessed: Optional[int] = None
    dribbled_past: Optional[int] = None


@dataclass
class DefendingStats:
    """防守维度"""
    tackles: Optional[int] = None
    interceptions: Optional[int] = None
    clearances: Optional[int] = None
    blocks: Optional[int] = None
    recoveries: Optional[int] = None
    poss_won_final_3rd: Optional[int] = None


@dataclass
class DuelsStats:
    """对抗维度"""
    ground_duels_won_pct: Optional[float] = None
    aerial_duels_won_pct: Optional[float] = None
    fouls_drawn: Optional[int] = None
    fouls_committed: Optional[int] = None


@dataclass
class GoalkeeperStats:
    """门将专项"""
    saves: Optional[int] = None
    save_pct: Optional[float] = None
    goals_conceded: Optional[int] = None
    clean_sheets: Optional[int] = None
    goals_prevented: Optional[float] = None
    penalties_saved: Optional[int] = None


@dataclass
class Per90Stats:
    """每90分钟自动计算"""
    goals_p90: Optional[float] = None
    assists_p90: Optional[float] = None
    xg_p90: Optional[float] = None
    xa_p90: Optional[float] = None
    shots_p90: Optional[float] = None
    key_passes_p90: Optional[float] = None
    tackles_p90: Optional[float] = None
    interceptions_p90: Optional[float] = None


@dataclass
class PlayerAttributes:
    """战术板雷达图六维 (0-100)"""
    speed: int = 60
    shooting: int = 60
    passing: int = 60
    dribbling: int = 60
    defending: int = 60
    physical: int = 60


@dataclass
class SourceInfo:
    """数据溯源"""
    primary: DataSource = DataSource.ESTIMATED
    league: Optional[str] = None
    season: str = "2025-26"
    fetched_at: str = ""
    fields_sources: Dict[str, str] = field(default_factory=dict)


@dataclass
class UnifiedPlayerStats:
    """统一球员数据模型（顶层容器）"""
    identity: Dict[str, str] = field(default_factory=dict)
    season: BaseStats = field(default_factory=BaseStats)
    shooting: Optional[ShootingStats] = None
    passing: Optional[PassingStats] = None
    dribbling: Optional[DribblingStats] = None
    defending: Optional[DefendingStats] = None
    duels: Optional[DuelsStats] = None
    goalkeeper: Optional[GoalkeeperStats] = None
    per90: Optional[Per90Stats] = None
    attributes: PlayerAttributes = field(default_factory=PlayerAttributes)
    confidence: Confidence = Confidence.NONE
    source: SourceInfo = field(default_factory=SourceInfo)


# ═══════════════════════════════════════════════════════════
# 字段映射表：各数据源 → 统一字段
# ═══════════════════════════════════════════════════════════

FPL_FIELD_MAP = {
    "season.appearances": "starts",
    "season.starts": "starts",
    "season.minutes": "minutes",
    "season.goals": "goals_scored",
    "season.assists": "assists",
    "season.yellow_cards": "yellow_cards",
    "season.red_cards": "red_cards",
    "shooting.xg": "expected_goals",
    "passing.xa": "expected_assists",
    "goalkeeper.saves": "saves",
}

SOFASCORE_FIELD_MAP = {
    "season.appearances": "appearances",
    "season.minutes": "minutesPlayed",
    "season.goals": "goals",
    "season.assists": "assists",
    "season.rating": "rating",
    "season.yellow_cards": "yellowCards",
    "season.red_cards": "redCards",
    "shooting.xg": "expectedGoals",
    "shooting.shots_total": "totalShots",
    "shooting.shots_on_target": "shotsOnTarget",
    "shooting.penalty_goals": "penaltyGoals",
    "shooting.big_chances_missed": "bigChancesMissed",
    "passing.passes_accuracy": "accuratePassesPercentage",
    "passing.key_passes": "keyPasses",
    "passing.big_chances_created": "bigChancesCreated",
    "passing.xa": "expectedAssists",
    "passing.long_balls_accuracy": "accurateLongBallsPercentage",
    "dribbling.dribbles_success_rate": "successfulDribblesPercentage",
    "dribbling.dispossessed": "possessionLost",
    "defending.tackles": "tackles",
    "defending.interceptions": "interceptions",
    "defending.clearances": "clearances",
    "goalkeeper.saves": "saves",
    "goalkeeper.goals_prevented": "goalsPrevented",
}

FOTMOB_FIELD_MAP = {
    "season.appearances": "playedMatches",
    "season.minutes": "minutesPlayed",
    "season.goals": "goals",
    "season.assists": "total_att_assist",
    "season.rating": "rating",
    "season.yellow_cards": "yellow_card",
    "season.red_cards": "red_card",
    "shooting.xg": "expected_goals",
    "shooting.np_xg": "non_penalty_xg",
    "shooting.shots_total": "total_scoring_att",
    "shooting.shots_on_target": "ontarget_scoring_att",
    "shooting.big_chances_missed": "big_chance_missed",
    "passing.passes_accuracy": "accurate_pass_pct",
    "passing.key_passes": "big_chance_created",
    "passing.xa": "expected_assists",
    "passing.crosses_accuracy": "successful_crosses_pct",
    "passing.long_balls_accuracy": "accurate_long_balls_pct",
    "dribbling.dribbles_success_rate": "successful_dribbles_pct",
    "dribbling.touches": "touches",
    "dribbling.touches_in_box": "touches_in_box",
    "dribbling.dispossessed": "dispossessed",
    "defending.tackles": "won_tackle",
    "defending.interceptions": "interception",
    "defending.clearances": "effective_clearance",
    "defending.blocks": "outfielder_block",
    "defending.poss_won_final_3rd": "poss_won_att_3rd",
    "duels.ground_duels_won_pct": "duels_won_pct",
    "duels.aerial_duels_won_pct": "aerial_won_pct",
    "duels.fouls_drawn": "fouls_won",
    "duels.fouls_committed": "fouls_committed",
    "goalkeeper.saves": "saves",
    "goalkeeper.save_pct": "_save_percentage",
    "goalkeeper.goals_conceded": "goals_conceded",
    "goalkeeper.clean_sheets": "clean_sheet",
    "goalkeeper.goals_prevented": "_goals_prevented",
}

API_FOOTBALL_FIELD_MAP = {
    "season.appearances": "games.appearences",
    "season.minutes": "games.minutes",
    "season.rating": "games.rating",
    "season.yellow_cards": "cards.yellow",
    "season.red_cards": "cards.red",
    "shooting.shots_total": "shots.total",
    "shooting.shots_on_target": "shots.on",
    "passing.passes_accuracy": "passes.accuracy",
    "passing.key_passes": "passes.key",
    "dribbling.dribbled_past": "dribbles.past",
    "defending.tackles": "tackles.total",
    "defending.interceptions": "tackles.interceptions",
    "defending.blocks": "tackles.blocks",
    "duels.ground_duels_won_pct": "duels_won_pct",
    "duels.fouls_drawn": "fouls.drawn",
    "duels.fouls_committed": "fouls.committed",
    "goalkeeper.saves": "goals.saves",
    "goalkeeper.goals_conceded": "goals.conceded",
}

# 多源合并优先级：按字段组逐组指定（数值越小越优先）
MERGE_PRIORITY = {
    "season":      [DataSource.SOFASCORE, DataSource.FOTMOB, DataSource.API_FOOTBALL, DataSource.FPL],
    "shooting":    [DataSource.FOTMOB, DataSource.SOFASCORE, DataSource.API_FOOTBALL, DataSource.FPL],
    "passing":     [DataSource.SOFASCORE, DataSource.FOTMOB, DataSource.API_FOOTBALL],
    "dribbling":   [DataSource.FOTMOB, DataSource.SOFASCORE, DataSource.API_FOOTBALL],
    "defending":   [DataSource.FOTMOB, DataSource.API_FOOTBALL, DataSource.SOFASCORE],
    "duels":       [DataSource.FOTMOB, DataSource.API_FOOTBALL],
    "goalkeeper":  [DataSource.FOTMOB, DataSource.SOFASCORE, DataSource.API_FOOTBALL],
    "rating":      [DataSource.SOFASCORE, DataSource.FOTMOB, DataSource.API_FOOTBALL],
}


# ═══════════════════════════════════════════════════════════
# 数据转换和合并引擎
# ═══════════════════════════════════════════════════════════

class UnifiedSchemaEngine:
    """将不同数据源转换为统一格式，并支持多源合并"""

    def __init__(self):
        self._field_maps = {
            DataSource.FPL: FPL_FIELD_MAP,
            DataSource.SOFASCORE: SOFASCORE_FIELD_MAP,
            DataSource.FOTMOB: FOTMOB_FIELD_MAP,
            DataSource.API_FOOTBALL: API_FOOTBALL_FIELD_MAP,
        }

    # ── 单源转换 ────────────────────────────────

    def convert_from_fpl(self, fpl_data: dict, position: str, club: str) -> UnifiedPlayerStats:
        """从 FPL 数据创建统一球员统计"""
        return self._convert(DataSource.FPL, fpl_data, position, club)

    def convert_from_sofascore(self, row: dict, position: str, club: str) -> UnifiedPlayerStats:
        """从 Sofascore datafc 行创建统一球员统计"""
        return self._convert(DataSource.SOFASCORE, row, position, club)

    def _convert(self, source: DataSource, raw: dict, position: str, club: str) -> UnifiedPlayerStats:
        """核心转换逻辑"""
        stats = UnifiedPlayerStats()
        stats.source.primary = source
        stats.source.fetched_at = datetime.datetime.now().isoformat()
        stats.source.league = raw.get("league", "")

        field_map = self._field_maps.get(source, {})

        # season
        s = stats.season
        for unified, raw_key in field_map.items():
            if not unified.startswith("season."):
                continue
            val = self._get_nested(raw, raw_key)
            if val is None:
                continue
            field_name = unified.split(".")[1]
            setattr(s, field_name, val)

        # 已有 rating 就说明有真实数据
        if s.rating > 0 or s.minutes > 0:
            stats.confidence = Confidence.MEDIUM

        # sub groups
        for group_name, group_class, prefix in [
            ("shooting", ShootingStats, "shooting."),
            ("passing", PassingStats, "passing."),
            ("dribbling", DribblingStats, "dribbling."),
            ("defending", DefendingStats, "defending."),
            ("duels", DuelsStats, "duels."),
            ("goalkeeper", GoalkeeperStats, "goalkeeper."),
        ]:
            group = group_class()
            has_any = False
            for unified, raw_key in field_map.items():
                if not unified.startswith(prefix):
                    continue
                val = self._get_nested(raw, raw_key)
                if val is None:
                    continue
                field_name = unified.split(".")[1]
                setattr(group, field_name, val)
                has_any = True
            if has_any:
                setattr(stats, group_name, group)

        # derive per90, attributes, confidence
        self._derive_per90(stats)
        self._derive_attributes(stats)
        self._assess_confidence(stats)

        # 将 position 带入 identity
        stats.identity = {"position": position, "club": club}

        return stats

    # ── 多源合并 ────────────────────────────────

    def merge(self, sources: Dict[DataSource, UnifiedPlayerStats], position: str) -> UnifiedPlayerStats:
        """按字段组优先级合并多个来源的数据"""
        if not sources:
            return UnifiedPlayerStats()
        if len(sources) == 1:
            return list(sources.values())[0]

        merged = UnifiedPlayerStats()
        merged.identity["position"] = position

        # season: 按优先级取
        for src in MERGE_PRIORITY["season"]:
            if src in sources and sources[src].season.rating > 0:
                merged.season = sources[src].season
                break
        else:
            merged.season = list(sources.values())[0].season

        # rating: 单独优先（Sofascore 算法最成熟）
        for src in MERGE_PRIORITY["rating"]:
            if src in sources and sources[src].season.rating > 0:
                merged.season.rating = sources[src].season.rating
                break

        # 子组：逐字段组选择最优源
        for group_name in ["shooting", "passing", "dribbling", "defending", "duels", "goalkeeper"]:
            priority = MERGE_PRIORITY.get(group_name, [])
            for src in priority:
                if src in sources and getattr(sources[src], group_name) is not None:
                    setattr(merged, group_name, getattr(sources[src], group_name))
                    break

        # 溯源
        merged.source.primary = sources[list(sources.keys())[0]].source.primary
        merged.source.fetched_at = datetime.datetime.now().isoformat()
        merged.source.fields_sources = self._trace_fields(sources)

        self._derive_per90(merged)
        self._derive_attributes(merged)
        self._assess_confidence(merged)

        return merged

    def _trace_fields(self, sources: Dict[DataSource, UnifiedPlayerStats]) -> Dict[str, str]:
        """记录每个字段来自哪个数据源"""
        trace = {}
        for src, stats in sources.items():
            src_name = src.value
            for group_name, group in [
                ("season", stats.season),
                ("shooting", stats.shooting),
                ("passing", stats.passing),
                ("dribbling", stats.dribbling),
                ("defending", stats.defending),
                ("duels", stats.duels),
                ("goalkeeper", stats.goalkeeper),
            ]:
                if group is None:
                    continue
                if isinstance(group, BaseStats):
                    for f in group.__dataclass_fields__:
                        if getattr(group, f) not in (0, 0.0, None):
                            trace[f"{group_name}.{f}"] = src_name
                else:
                    for f in group.__dataclass_fields__:
                        if getattr(group, f) is not None:
                            trace[f"{group_name}.{f}"] = src_name
        return trace

    # ── 衍生计算 ────────────────────────────────

    def _derive_per90(self, stats: UnifiedPlayerStats):
        """计算每90分钟数据"""
        mins = stats.season.minutes
        if mins <= 0:
            return
        mult = 90.0 / mins

        s = stats.season
        p90 = Per90Stats()
        p90.goals_p90 = round(s.goals * mult, 2)
        p90.assists_p90 = round(s.assists * mult, 2)

        if stats.shooting and stats.shooting.xg is not None:
            p90.xg_p90 = round(stats.shooting.xg * mult, 2)
        if stats.passing and stats.passing.xa is not None:
            p90.xa_p90 = round(stats.passing.xa * mult, 2)
        if stats.shooting and stats.shooting.shots_total is not None:
            p90.shots_p90 = round(stats.shooting.shots_total * mult, 2)
        if stats.passing and stats.passing.key_passes is not None:
            p90.key_passes_p90 = round(stats.passing.key_passes * mult, 2)
        if stats.defending and stats.defending.tackles is not None:
            p90.tackles_p90 = round(stats.defending.tackles * mult, 2)
        if stats.defending and stats.defending.interceptions is not None:
            p90.interceptions_p90 = round(stats.defending.interceptions * mult, 2)

        stats.per90 = p90

    def _derive_attributes(self, stats: UnifiedPlayerStats):
        """从赛季数据推导雷达图六维 (0-100)"""
        attr = PlayerAttributes()
        s = stats.season
        apps = max(s.appearances, s.starts, 1)
        p90 = stats.per90

        # shooting: goal rate + shot accuracy
        goal_rate = min(s.goals / apps * 10, 1) if apps > 0 else 0.5
        shot_acc = 0.5
        if stats.shooting:
            if stats.shooting.shot_accuracy:
                shot_acc = stats.shooting.shot_accuracy / 100
            elif stats.shooting.shots_total and stats.shooting.shots_total > 0:
                sot = stats.shooting.shots_on_target or 0
                shot_acc = min(sot / stats.shooting.shots_total, 1)
        attr.shooting = int(45 + goal_rate * 30 + shot_acc * 25)
        attr.shooting = min(max(attr.shooting, 30), 99)

        # passing: accuracy + key passes
        pass_acc = 0.75
        if stats.passing and stats.passing.passes_accuracy:
            pass_acc = stats.passing.passes_accuracy / 100
        attr.passing = int(min(max(pass_acc * 95, 50), 95))

        # dribbling: dribble success rate
        dribble_rate = 0.55
        if stats.dribbling and stats.dribbling.dribbles_success_rate:
            dribble_rate = stats.dribbling.dribbles_success_rate / 100
        attr.dribbling = int(min(max(dribble_rate * 95, 40), 95))

        # defending: tackles + interceptions per game
        if stats.defending:
            def_per_game = ((stats.defending.tackles or 0) + (stats.defending.interceptions or 0)) / apps
            attr.defending = int(45 + min(def_per_game / 5, 1) * 50)
        attr.defending = min(max(attr.defending, 25), 95)

        # physical: minutes per app + duels
        mins_per_app = s.minutes / apps if apps > 0 else 70
        attr.physical = int(55 + min(mins_per_app / 90, 1) * 35)
        if stats.duels:
            if stats.duels.ground_duels_won_pct:
                attr.physical = int((attr.physical + stats.duels.ground_duels_won_pct) / 2)

        # speed: progressive passes + dribble synergy
        prog = 0
        if stats.passing and stats.passing.progressive_passes:
            prog = stats.passing.progressive_passes / apps
        attr.speed = int(55 + min(prog / 10, 1) * 30)
        attr.speed = min(max(attr.speed, 40), 95)

        stats.attributes = attr

    def _assess_confidence(self, stats: UnifiedPlayerStats):
        """评估数据可信度"""
        if stats.season.rating <= 0 or stats.season.minutes <= 0:
            stats.confidence = Confidence.NONE
            return

        # 计数各维度有多少有效字段
        shooting_count = self._count_fields(stats.shooting)
        passing_count = self._count_fields(stats.passing)
        dribbling_count = self._count_fields(stats.dribbling)
        defending_count = self._count_fields(stats.defending)

        has_xg = stats.shooting and stats.shooting.xg is not None
        has_xa = stats.passing and stats.passing.xa is not None

        if has_xg and has_xa and shooting_count >= 2 and passing_count >= 2 and defending_count >= 2:
            stats.confidence = Confidence.HIGH
        else:
            stats.confidence = Confidence.MEDIUM

    @staticmethod
    def _count_fields(group) -> int:
        if group is None:
            return 0
        return sum(1 for f in group.__dataclass_fields__ if getattr(group, f) is not None)

    @staticmethod
    def _get_nested(data: dict, path: str):
        """取值：支持 'a.b.c' 嵌套路径"""
        keys = path.split(".")
        val = data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                try:
                    val = getattr(val, k, None)
                except Exception:
                    return None
            if val is None:
                return None
        return val

    # ── JSON 序列化 ────────────────────────────────

    def to_dict(self, stats: UnifiedPlayerStats) -> dict:
        """将 UnifiedPlayerStats 转为 API 可输出的扁平 dict"""
        s = stats.season
        result = {
            "appearances": s.appearances,
            "starts": s.starts,
            "minutes": s.minutes,
            "goals": s.goals,
            "assists": s.assists,
            "rating": s.rating,
            "yellow_cards": s.yellow_cards,
            "red_cards": s.red_cards,
        }

        # sub groups
        for attr_name in ["shooting", "passing", "dribbling", "defending", "duels", "goalkeeper"]:
            group = getattr(stats, attr_name)
            if group is None:
                continue
            for f in group.__dataclass_fields__:
                val = getattr(group, f)
                if val is not None:
                    result[f] = val

        # per90
        p90 = stats.per90
        if p90:
            for f in p90.__dataclass_fields__:
                val = getattr(p90, f)
                if val is not None:
                    result[f] = val

        # attributes
        attr = stats.attributes
        result["_attributes"] = {
            "speed": attr.speed,
            "shooting": attr.shooting,
            "passing": attr.passing,
            "dribbling": attr.dribbling,
            "defending": attr.defending,
            "physical": attr.physical,
        }

        # meta
        result["_confidence"] = stats.confidence.value
        result["_source"] = stats.source.primary.value
        if stats.source.league:
            result["_league"] = stats.source.league

        return result

    def to_api_dict(self, stats: UnifiedPlayerStats) -> dict:
        """转换为前端 API 兼容格式（兼容现有 PlayerStats 接口）"""
        s = stats.season
        result = {
            "appearances": s.appearances,
            "starts": s.starts,
            "minutes": s.minutes,
            "goals": s.goals,
            "assists": s.assists,
            "rating": round(s.rating, 1) if s.rating else 6.0,
            "yellow_cards": s.yellow_cards,
            "red_cards": s.red_cards,
        }

        # shooting
        if stats.shooting:
            sh = stats.shooting
            result["xg"] = self._safe_float(sh.xg, 2)
            result["shots_total"] = sh.shots_total
            result["shots_on_target"] = sh.shots_on_target
            result["shot_accuracy"] = self._safe_float(sh.shot_accuracy, 1)

        # passing
        if stats.passing:
            ps = stats.passing
            result["pass_accuracy"] = self._safe_float(ps.passes_accuracy, 1)
            result["key_passes"] = ps.key_passes
            result["progressive_passes"] = ps.progressive_passes

        # dribbling
        if stats.dribbling:
            dr = stats.dribbling
            result["dribble_success_rate"] = self._safe_float(dr.dribbles_success_rate, 1)

        # defending
        if stats.defending:
            df = stats.defending
            result["tackles"] = df.tackles
            result["interceptions"] = df.interceptions
            result["clearances"] = df.clearances

        # per90
        if stats.per90:
            p90 = stats.per90
            for f in p90.__dataclass_fields__:
                val = getattr(p90, f)
                if val is not None:
                    result[f] = self._safe_float(val, 2)

        # meta
        result["match_confidence"] = stats.confidence.value
        result["data_source"] = stats.source.primary.value

        # attributes
        if stats.attributes:
            a = stats.attributes
            result["_attributes"] = {
                "speed": a.speed,
                "shooting": a.shooting,
                "passing": a.passing,
                "dribbling": a.dribbling,
                "defending": a.defending,
                "physical": a.physical,
            }

        return self._sanitize_dict(result)

    @staticmethod
    def _safe_float(val, decimals: int) -> Optional[float]:
        """安全转换浮点数，NaN/Inf → None"""
        if val is None:
            return None
        try:
            if math.isnan(val) or math.isinf(val):
                return None
        except (TypeError, ValueError):
            pass
        return round(float(val), decimals)

    @staticmethod
    def _sanitize_dict(d: dict) -> dict:
        """清理 dict 中的 NaN/Inf 值"""
        for k, v in d.items():
            if v is None:
                continue
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                d[k] = None
            elif isinstance(v, dict):
                d[k] = UnifiedSchemaEngine._sanitize_dict(v)
        return d


# ═══════════════════════════════════════════════════════════
# 模块级单例
# ═══════════════════════════════════════════════════════════

engine = UnifiedSchemaEngine()
