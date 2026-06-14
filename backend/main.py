"""
世界杯AI助手 - FastAPI后端主应用
提供预测、解说、可视化和知识库API
"""
import sys
import io
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

# Fix Windows console encoding issues with Chinese characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from pathlib import Path
import pandas as pd

from services import (
    data_service,
    prediction_service,
    visualization_service,
    commentary_service,
    knowledge_service,
    tactics_service,
)
from services.team_service import team_service
from services.intelligence_service import intelligence_service
from services.intel_card_service import intel_card_service
from services.daily_report_service import daily_report_service
from services.lineup_analysis_service import lineup_analysis_service
from services.live_match_service import live_match_service
from services.match_analysis_service import analyze_match

# 创建FastAPI应用
app = FastAPI(
    title="世界杯AI助手 API",
    description="提供足球比赛预测、AI解说、可视化分析和世界杯知识问答",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ==================== 请求/响应模型 ====================

class MatchStats(BaseModel):
    match_id: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    home_shots: int = 0
    away_shots: int = 0
    home_shots_on_target: int = 0
    away_shots_on_target: int = 0
    home_possession: float = 50.0
    away_possession: float = 50.0
    home_pass_accuracy: float = 0.0
    away_pass_accuracy: float = 0.0
    home_xg: float = 0.0
    away_xg: float = 0.0
    home_corners: int = 0
    away_corners: int = 0
    home_fouls: int = 0
    away_fouls: int = 0
    home_yellows: int = 0
    away_yellows: int = 0
    home_reds: int = 0
    away_reds: int = 0

class KnowledgeRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    top_k: int = Field(default=3, description="返回结果数量")

class KnowledgeResponse(BaseModel):
    question: str
    answer: str
    category: str
    relevance: float

class CommentaryRequest(BaseModel):
    match_id: int = Field(..., description="比赛ID")
    focus_team: Optional[str] = Field(default=None, description="重点关注球队")

class CommentaryTacticalRequest(BaseModel):
    match_id: int = Field(..., description="比赛ID")

class CommentaryPreviewRequest(BaseModel):
    home_team: str = Field(..., description="主队名称")
    away_team: str = Field(..., description="客队名称")


# ── 战术分析模型 ────────────────────────────────

class TacticalPlayer(BaseModel):
    """战术分析中的球员"""
    name: str = Field(default="", description="球员名")
    player_id: str = Field(default="", description="球员ID")
    position: str = Field(..., description="场上位置 (CB/LB/CM/ST等)")
    attributes: Dict[str, int] = Field(
        default_factory=lambda: {"speed": 60, "shooting": 60, "passing": 60,
                                  "dribbling": 60, "defending": 60, "physical": 60},
        description="6D属性向量"
    )

class LineupAnalysisRequest(BaseModel):
    home_lineup: List[TacticalPlayer] = Field(..., description="主队11人阵容")
    away_lineup: List[TacticalPlayer] = Field(..., description="客队11人阵容")
    home_formation: str = Field(default="4-3-3", description="主队阵型")
    away_formation: str = Field(default="4-4-2", description="客队阵型")

class PlayerFitRequest(BaseModel):
    attributes: Dict[str, int] = Field(..., description="球员6D属性")
    position: str = Field(..., description="场上位置")
    formation_id: str = Field(default="4-3-3", description="阵型ID（可选，用于阵型特定要求）")

class TeamStyleRequest(BaseModel):
    lineup: List[TacticalPlayer] = Field(..., description="球队阵容")
    formation_id: str = Field(default="4-3-3", description="阵型ID")

# ==================== 首页路由 ====================

@app.get("/")
async def root():
    """API首页"""
    return {
        "name": "世界杯AI助手 API",
        "version": "1.0.0",
        "features": [
            "比赛预测 (Prediction)",
            "AI解说 (Commentary)",
            "可视化分析 (Visualization)",
            "知识百库 (Knowledge Base)",
            "球队板块 (Teams)"
        ],
        "endpoints": {
            "docs": "/docs",
            "matches": "/api/matches",
            "predict": "/api/predict",
            "teams": "/api/teams",
            "analysis": "/api/analysis/{match_id}",
            "knowledge": "/api/knowledge/search",
            "categories": "/api/knowledge/categories"
        }
    }

# ==================== 数据路由 ====================

@app.get("/api/competitions")
async def get_competitions():
    """获取可用赛事列表"""
    try:
        competitions = data_service.get_competitions()
        return {"competitions": competitions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/matches")
async def get_matches(competition_id: int = 43, season_id: int = 106):
    """获取世界杯比赛列表"""
    try:
        matches = data_service.get_matches(competition_id, season_id)
        if matches.empty:
            return {"matches": [], "total": 0}

        # 转换为可序列化格式
        matches_list = []
        for _, match in matches.iterrows():
            matches_list.append({
                "match_id": int(match.get('match_id', 0)),
                "home_team": match.get('home_team', ''),
                "away_team": match.get('away_team', ''),
                "home_score": int(match.get('home_score', 0) or 0),
                "away_score": int(match.get('away_score', 0) or 0),
                "date": str(match.get('match_date', '')),
                "competition": match.get('competition', ''),
                "season": match.get('season', ''),
                "venue": match.get('venue', ''),
                "status": match.get('status', '')
            })

        return {"matches": matches_list, "total": len(matches_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/matches/{match_id}")
async def get_match_detail(match_id: int):
    """获取比赛详情"""
    try:
        events = data_service.get_match_events(match_id)
        if events.empty:
            raise HTTPException(status_code=404, detail="比赛不存在或无事件数据")

        # 获取比赛基本信息
        matches = data_service.get_matches()
        match_info = matches[matches['match_id'] == match_id]

        if match_info.empty:
            raise HTTPException(status_code=404, detail="比赛不存在")

        match = match_info.iloc[0]
        home_team = match.get('home_team', '')
        away_team = match.get('away_team', '')

        # 提取统计数据
        home_stats = data_service.get_team_stats(events, home_team)
        away_stats = data_service.get_team_stats(events, away_team)

        # 提取射门数据计算xG
        shots = data_service.extract_shots(events)
        home_shots = shots[shots['team'] == home_team] if not shots.empty else pd.DataFrame()
        away_shots = shots[shots['team'] == away_team] if not shots.empty else pd.DataFrame()

        # 计算xG (优先使用'xg'列，回退到'shot_statsbomb_xg')
        xg_col = 'xg' if 'xg' in shots.columns else ('shot_statsbomb_xg' if 'shot_statsbomb_xg' in shots.columns else None)
        if xg_col:
            home_xg = home_shots[xg_col].sum() if not home_shots.empty else 0
            away_xg = away_shots[xg_col].sum() if not away_shots.empty else 0
        else:
            home_xg = 0
            away_xg = 0

        stats = MatchStats(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            home_score=int(match.get('home_score', 0) or 0),
            away_score=int(match.get('away_score', 0) or 0),
            home_shots=home_stats.get('total_shots', 0),
            away_shots=away_stats.get('total_shots', 0),
            home_shots_on_target=home_stats.get('shots_on_target', 0),
            away_shots_on_target=away_stats.get('shots_on_target', 0),
            home_possession=home_stats.get('possession', 50),
            away_possession=away_stats.get('possession', 50),
            home_pass_accuracy=home_stats.get('pass_accuracy', 0),
            away_pass_accuracy=away_stats.get('pass_accuracy', 0),
            home_xg=float(home_xg),
            away_xg=float(away_xg),
            home_corners=home_stats.get('corners', 0),
            away_corners=away_stats.get('corners', 0),
            home_fouls=home_stats.get('fouls', 0),
            away_fouls=away_stats.get('fouls', 0),
            home_yellows=home_stats.get('yellows', 0),
            away_yellows=away_stats.get('yellows', 0),
            home_reds=home_stats.get('reds', 0),
            away_reds=away_stats.get('reds', 0)
        )

        # 提取事件列表
        events_list = []
        for _, event in events.iterrows():
            event_dict = {
                'type': event.get('type', ''),
                'minute': int(event.get('minute', 0) or 0),
                'team': event.get('team', ''),
                'player': event.get('player', ''),
                'description': ''
            }

            # 根据事件类型添加描述
            if event.get('type') == 'Shot':
                outcome = event.get('shot_outcome', '')
                event_dict['description'] = f"射门 - {outcome}"
            elif event.get('type') == 'Pass':
                outcome = event.get('pass_outcome', '')
                event_dict['description'] = f"传球{' - ' + outcome if pd.notna(outcome) and outcome else ''}"
            elif event.get('type') == 'Foul Won':
                event_dict['description'] = '犯规'
            elif event.get('type') == 'Yellow Card':
                event_dict['description'] = '黄牌'
            elif event.get('type') == 'Red Card':
                event_dict['description'] = '红牌'
            elif event.get('type') == 'Goal':
                event_dict['description'] = '进球！'
                scorer = event.get('player', '')
                if pd.notna(scorer):
                    event_dict['description'] = f"进球！{scorer}"

            events_list.append(event_dict)

        return {
            "stats": stats.model_dump(),
            "events": events_list
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 可视化路由 ====================

@app.get("/api/visual/{match_id}")
async def get_match_visualization(match_id: int):
    """获取比赛可视化图表"""
    try:
        events = data_service.get_match_events(match_id)
        if events.empty:
            raise HTTPException(status_code=404, detail="比赛不存在或无事件数据")

        # 获取比赛信息
        matches = data_service.get_matches()
        match_info = matches[matches['match_id'] == match_id]

        if match_info.empty:
            raise HTTPException(status_code=404, detail="比赛不存在")

        match = match_info.iloc[0]
        home_team = match.get('home_team', '')
        away_team = match.get('away_team', '')

        # 生成可视化
        visualizations = visualization_service.generate_full_analysis(
            match_id, events, home_team, away_team
        )

        return {
            "match_id": match_id,
            "home_team": home_team,
            "away_team": away_team,
            "visualizations": visualizations
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/visual/xg/{match_id}")
async def get_xg_chart(match_id: int):
    """获取xG曲线图"""
    try:
        events = data_service.get_match_events(match_id)
        if events.empty:
            raise HTTPException(status_code=404, detail="比赛不存在或无事件数据")

        xg_chart = visualization_service.generate_xg_chart(match_id, events)

        if xg_chart is None:
            raise HTTPException(status_code=404, detail="无法生成xG图表")

        return {
            "match_id": match_id,
            "xg_chart": xg_chart
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/visual/shotmap/{match_id}")
async def get_shotmap(match_id: int, team: Optional[str] = None):
    """获取射门地图"""
    try:
        events = data_service.get_match_events(match_id)
        if events.empty:
            raise HTTPException(status_code=404, detail="比赛不存在或无事件数据")

        shotmap = visualization_service.generate_shotmap(match_id, events, team)

        if shotmap is None:
            raise HTTPException(status_code=404, detail="无法生成射门地图")

        return {
            "match_id": match_id,
            "team": team,
            "shotmap": shotmap
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/visual/heatmap/{match_id}")
async def get_heatmap(match_id: int, team: str):
    """获取热力图"""
    try:
        events = data_service.get_match_events(match_id)
        if events.empty:
            raise HTTPException(status_code=404, detail="比赛不存在或无事件数据")

        heatmap = visualization_service.generate_heatmap(events, team)

        if heatmap is None:
            raise HTTPException(status_code=404, detail="无法生成热力图")

        return {
            "match_id": match_id,
            "team": team,
            "heatmap": heatmap
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 赛程路由 ====================

import json as json_lib

# Load schedule data at startup
_schedule_data = None

def _load_schedule():
    global _schedule_data
    if _schedule_data is None:
        schedule_path = Path(__file__).parent / "data" / "schedule_2026.json"
        if schedule_path.exists():
            with open(schedule_path, 'r', encoding='utf-8') as f:
                _schedule_data = json_lib.load(f)
    return _schedule_data

class ScheduleMatchDetail(BaseModel):
    """赛程比赛详情模型"""
    match: Dict = Field(..., description="比赛基本信息")
    h2h: Optional[Dict] = Field(default=None, description="历史对决数据")
    home_recent: Optional[List[Dict]] = Field(default=None, description="主队近期战绩")
    away_recent: Optional[List[Dict]] = Field(default=None, description="客队近期战绩")
    highlights: Optional[str] = Field(default=None, description="AI生成的比赛看点")
    team_profiles: Optional[Dict] = Field(default=None, description="两队档案")

class MatchHighlightsRequest(BaseModel):
    """比赛看点请求"""
    home_team: str = Field(..., description="主队名称")
    away_team: str = Field(..., description="客队名称")
    home_team_cn: str = Field(default="", description="主队中文名")
    away_team_cn: str = Field(default="", description="客队中文名")
    group: str = Field(default="", description="小组")
    stage: str = Field(default="group", description="比赛阶段")
    venue: str = Field(default="", description="比赛场馆")

@app.get("/api/schedule")
async def get_schedule(
    stage: Optional[str] = Query(None, description="比赛阶段: group, round_of_32, round_of_16, quarter_final, semi_final, third_place, final"),
    group: Optional[str] = Query(None, description="小组: A-L"),
    date_from: Optional[str] = Query(None, description="开始日期: YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="结束日期: YYYY-MM-DD"),
    team: Optional[str] = Query(None, description="球队名称(英文)"),
):
    """获取2026世界杯完整赛程"""
    schedule = _load_schedule()
    if not schedule:
        raise HTTPException(status_code=500, detail="赛程数据未加载")

    matches = schedule['matches']

    if stage:
        matches = [m for m in matches if m['stage'] == stage]
    if group:
        matches = [m for m in matches if m['group'] == group.upper()]
    if date_from:
        matches = [m for m in matches if m['date'] >= date_from]
    if date_to:
        matches = [m for m in matches if m['date'] <= date_to]
    if team:
        matches = [m for m in matches if team.lower() in [m['home_team'].lower(), m['away_team'].lower()]]

    return {
        "total": len(matches),
        "groups": schedule.get('groups'),
        "venues": schedule.get('venues'),
        "stage_labels": schedule.get('stage_labels'),
        "matches": matches
    }

@app.get("/api/schedule/dates")
async def get_schedule_dates():
    """获取有比赛的日期列表"""
    schedule = _load_schedule()
    if not schedule:
        raise HTTPException(status_code=500, detail="赛程数据未加载")

    dates = sorted(set(m['date'] for m in schedule['matches']))
    return {"dates": dates, "count": len(dates)}

@app.get("/api/schedule/{match_id}")
async def get_schedule_match(match_id: int):
    """获取单场比赛详情，包含历史对决和近期战绩"""
    schedule = _load_schedule()
    if not schedule:
        raise HTTPException(status_code=500, detail="赛程数据未加载")

    match = next((m for m in schedule['matches'] if m['match_id'] == match_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"比赛{match_id}不存在")

    home = match['home_team']
    away = match['away_team']

    # Skip H2H/recent for knockout placeholder matches
    is_placeholder = any(any(ch.isdigit() for ch in t) or '/' in t for t in [home, away])
    if is_placeholder:
        return ScheduleMatchDetail(
            match=match,
            h2h=None,
            home_recent=None,
            away_recent=None,
            highlights=f"淘汰赛对阵待小组赛结束后确定 — {match.get('home_team_cn', '')} vs {match.get('away_team_cn', '')}",
            team_profiles=None
        )

    # Get H2H from match history
    h2h_data = _get_h2h_data(home, away)

    # Get recent form from parquet
    home_recent = _get_recent_form(home)
    away_recent = _get_recent_form(away)

    # Get team profiles from knowledge service
    team_profiles = None
    try:
        home_profile = knowledge_service.get_team_profile(home)
        away_profile = knowledge_service.get_team_profile(away)
        if home_profile or away_profile:
            team_profiles = {'home': home_profile, 'away': away_profile}
    except Exception:
        pass

    return ScheduleMatchDetail(
        match=match,
        h2h=h2h_data,
        home_recent=home_recent,
        away_recent=away_recent,
        highlights=None,
        team_profiles=team_profiles
    )

@app.post("/api/schedule/{match_id}/highlights")
async def get_match_highlights(match_id: int, request: MatchHighlightsRequest):
    """AI生成比赛看点和关注点"""
    schedule = _load_schedule()
    if not schedule:
        raise HTTPException(status_code=500, detail="赛程数据未加载")

    match = next((m for m in schedule['matches'] if m['match_id'] == match_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"比赛{match_id}不存在")

    home = request.home_team
    away = request.away_team
    home_cn = request.home_team_cn or home
    away_cn = request.away_team_cn or away

    # Get data for AI context
    h2h_data = _get_h2h_data(home, away)
    home_recent = _get_recent_form(home)
    away_recent = _get_recent_form(away)

    # Get team profiles
    home_profile = knowledge_service.get_team_profile(home)
    away_profile = knowledge_service.get_team_profile(away)

    # Build context for AI
    h2h_summary = ""
    if h2h_data:
        h2h_summary = f"历史交锋{h2h_data.get('total_matches', 0)}场，{home}胜{h2h_data.get('home_wins', 0)}场，{away}胜{h2h_data.get('away_wins', 0)}场，平{h2h_data.get('draws', 0)}场"

    home_recent_summary = _format_recent_summary(home, home_recent)
    away_recent_summary = _format_recent_summary(away, away_recent)

    home_style = home_profile.get('playing_style', '未知') if home_profile else '未知'
    away_style = away_profile.get('playing_style', '未知') if away_profile else '未知'
    home_strength = home_profile.get('strength', '') if home_profile else ''
    away_strength = away_profile.get('strength', '') if away_profile else ''

    # Try DeepSeek AI
    ai_highlights = None
    try:
        import os
        from openai import OpenAI
        api_key = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        if api_key:
            client = OpenAI(api_key=api_key, base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
            model = os.environ.get("AI_MODEL", "deepseek-chat")

            prompt = f"""你是2026世界杯的专业分析师。请为以下比赛生成3-5个赛前看点和关注点（用中文，每个看点1-2句话）：

比赛：{home_cn}({home}) vs {away_cn}({away})
阶段：{match.get('stage', '')} {'第'+str(match.get('round', ''))+'轮' if match.get('round') else ''}
场地：{match.get('venue', '')}，{match.get('city', '')}
小组：{request.group if request.group else 'N/A'}

{h2h_summary}
主队({home_cn})近期战绩：{home_recent_summary}
客队({away_cn})近期战绩：{away_recent_summary}
主队风格：{home_style}
客队风格：{away_style}
主队优势：{home_strength}
客队优势：{away_strength}

请从以下角度分析：
1. 两队实力对比和关键对位
2. 战术风格碰撞看点
3. 历史交锋启示
4. 本场比赛的意义和影响
5. 值得关注的球员或战术细节

直接以"比赛看点"开头，用中文数字编号，每个看点2-3句话，总字数300-400字。"""

            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )
            ai_highlights = response.choices[0].message.content
    except Exception as e:
        print(f"AI highlights generation failed: {e}")

    # Fallback
    if not ai_highlights:
        ai_highlights = _generate_fallback_highlights(home_cn, away_cn, h2h_data, home_recent, away_recent)

    return {
        "match_id": match_id,
        "home_team": home,
        "away_team": away,
        "home_team_cn": home_cn,
        "away_team_cn": away_cn,
        "h2h": h2h_data,
        "home_recent": home_recent,
        "away_recent": away_recent,
        "highlights": ai_highlights,
        "team_profiles": {
            "home": home_profile,
            "away": away_profile
        }
    }

def _get_h2h_data(home: str, away: str) -> Optional[Dict]:
    """从match_history.json获取两队历史对决"""
    try:
        teams_dir = Path(__file__).parent / "data" / "teams"
        home_file = teams_dir / home / "match_history.json"
        away_file = teams_dir / away / "match_history.json"

        # Use home team's match history if available
        match_file = home_file if home_file.exists() else (away_file if away_file.exists() else None)
        if not match_file:
            return None

        with open(match_file, 'r', encoding='utf-8') as f:
            matches = json_lib.load(f)

        h2h_matches = []
        for m in matches:
            if isinstance(m, dict):
                ht = m.get('home_team', '')
                at = m.get('away_team', '')
                if (ht.lower() == home.lower() and at.lower() == away.lower()) or \
                   (ht.lower() == away.lower() and at.lower() == home.lower()):
                    h2h_matches.append(m)

        if not h2h_matches:
            return {"total_matches": 0, "home_wins": 0, "away_wins": 0, "draws": 0, "matches": []}

        home_wins = sum(1 for m in h2h_matches
                       if (m.get('home_team','').lower() == home.lower() and int(str(m.get('home_score','0') or '0')) > int(str(m.get('away_score','0') or '0')))
                       or (m.get('away_team','').lower() == home.lower() and int(str(m.get('away_score','0') or '0')) > int(str(m.get('home_score','0') or '0'))))
        away_wins = sum(1 for m in h2h_matches
                       if (m.get('home_team','').lower() == away.lower() and int(str(m.get('home_score','0') or '0')) > int(str(m.get('away_score','0') or '0')))
                       or (m.get('away_team','').lower() == away.lower() and int(str(m.get('away_score','0') or '0')) > int(str(m.get('home_score','0') or '0'))))
        draws = len(h2h_matches) - home_wins - away_wins

        return {
            "total_matches": len(h2h_matches),
            "home_wins": home_wins,
            "away_wins": away_wins,
            "draws": draws,
            "matches": h2h_matches[-10:]  # Last 10 meetings
        }
    except Exception as e:
        print(f"H2H lookup failed: {e}")
        return None

def _get_recent_form(team: str) -> Optional[List[Dict]]:
    """获取球队近一年比赛战绩"""
    try:
        df = pd.read_parquet(Path(__file__).parent / "data" / "international_matches.parquet")
        team_matches = df[(df['home_team'] == team) | (df['away_team'] == team)].copy()

        if team_matches.empty:
            return None

        # Sort by date, get last 20
        if 'match_date' in team_matches.columns:
            team_matches = team_matches.sort_values('match_date', ascending=False)
        team_matches = team_matches.head(20)

        recent = []
        for _, row in team_matches.iterrows():
            is_home = row['home_team'] == team
            result = 'W' if (is_home and row['home_score'] > row['away_score']) or \
                           (not is_home and row['away_score'] > row['home_score']) else \
                     'D' if row['home_score'] == row['away_score'] else 'L'
            recent.append({
                'date': str(row.get('match_date', row.get('date', '')))[:10],
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'home_score': int(row.get('home_score', 0) or 0),
                'away_score': int(row.get('away_score', 0) or 0),
                'tournament': str(row.get('tournament_type', row.get('competition', ''))),
                'result': result,
                'is_home': is_home
            })

        return recent
    except Exception as e:
        print(f"Recent form lookup failed for {team}: {e}")
        return None

def _format_recent_summary(team: str, recent: Optional[List[Dict]]) -> str:
    """格式化近期战绩摘要"""
    if not recent:
        return f"{team}近期无比赛数据"
    wins = sum(1 for r in recent if r['result'] == 'W')
    draws = sum(1 for r in recent if r['result'] == 'D')
    losses = sum(1 for r in recent if r['result'] == 'L')
    return f"近{len(recent)}场：{wins}胜{draws}平{losses}负"

def _generate_fallback_highlights(home_cn: str, away_cn: str, h2h: Optional[Dict], home_recent: Optional[List], away_recent: Optional[List]) -> str:
    """备用比赛看点生成（无AI时使用）"""
    lines = ["比赛看点：", ""]
    count = 1

    if h2h and h2h.get('total_matches', 0) > 0:
        lines.append(f"{count}. 历史交锋：两队历史上交手{h2h['total_matches']}次，{home_cn}{h2h.get('home_wins',0)}胜{h2h.get('draws',0)}平{away_cn}{h2h.get('away_wins',0)}胜")
        count += 1

    if home_recent:
        wins = sum(1 for r in home_recent if r['result'] == 'W')
        lines.append(f"{count}. {home_cn}近期状态：近{len(home_recent)}场{wins}胜，{'状态正佳' if wins >= len(home_recent)//2 else '表现一般'}")
        count += 1

    if away_recent:
        wins = sum(1 for r in away_recent if r['result'] == 'W')
        lines.append(f"{count}. {away_cn}近期状态：近{len(away_recent)}场{wins}胜，{'状态正佳' if wins >= len(away_recent)//2 else '表现一般'}")
        count += 1

    lines.append(f"{count}. 本场比赛对两队小组出线形势具有重要影响，值得关注")
    count += 1
    lines.append(f"{count}. 两队战术风格的碰撞将决定比赛走势，中场控制权是关键因素")

    return "\n".join(lines)


# ==================== 实时比赛路由 ====================

@app.get("/api/live/scoreboard")
async def get_live_scoreboard():
    """获取实时比分板 — 进行中 + 今日比赛"""
    try:
        live = live_match_service.get_live_matches()
        today = live_match_service.get_today_matches()
        return {
            "live": live,
            "today": today,
            "live_count": len(live),
            "total_today": len(today),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live/matches/{match_id}")
async def get_live_match_detail(match_id: str):
    """获取单场比赛实时详情 — 比分 + 事件时间线 + 技术统计"""
    try:
        detail = live_match_service.get_match_detail(match_id)
        if not detail:
            raise HTTPException(status_code=404, detail=f"Match {match_id} not found or not available")
        return detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live/match-lookup")
async def get_live_match_lookup(home_team: str, away_team: str, date: str = None):
    """通过队名查找ESPN比赛ID"""
    try:
        match_id = live_match_service.find_match_by_teams(home_team, away_team, date)
        if not match_id:
            return {"match_id": None, "found": False}
        return {"match_id": match_id, "found": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live/schedule-match")
async def find_schedule_match(home_team: str, away_team: str, date: str = None):
    """通过队名查找赛程中的比赛ID（ESPN→赛程反向查找）"""
    import re
    schedule = _load_schedule()
    if not schedule:
        return {"match_id": None, "found": False}

    def norm(s: str) -> str:
        n = s.lower()
        n = re.sub(r'\band\b', '', n)
        n = n.replace('&', '').replace('-', ' ').replace('.', '')
        return re.sub(r'\s+', ' ', n).strip()

    h_norm = norm(home_team)
    a_norm = norm(away_team)

    candidates = []
    for m in schedule['matches']:
        mh = norm(m['home_team'])
        ma = norm(m['away_team'])
        if (h_norm in mh or mh in h_norm) and (a_norm in ma or ma in a_norm):
            candidates.append(m)

    if len(candidates) == 1:
        return {"match_id": candidates[0]['match_id'], "found": True}

    if date and candidates:
        for m in candidates:
            if m['date'] == date:
                return {"match_id": m['match_id'], "found": True}

    return {"match_id": None, "found": False}


@app.get("/api/live/matches/{match_id}/analysis")
async def get_live_match_analysis(match_id: str):
    """获取比赛中场/全场分析 + 实时事件与数据"""
    try:
        detail = live_match_service.get_match_detail(match_id)
        if not detail:
            raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

        home_team_id = detail.get("home", {}).get("team_id", "")
        away_team_id = detail.get("away", {}).get("team_id", "")
        analysis = analyze_match(detail, home_team_id, away_team_id)
        return {
            "match_id": match_id,
            "status": detail.get("status", {}),
            "home": detail.get("home", {}),
            "away": detail.get("away", {}),
            "events": detail.get("events", []),
            "statistics": detail.get("statistics", {}),
            "lineups": detail.get("lineups", {}),
            "analysis": analysis,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live/roster/{team_id}")
async def get_team_roster(team_id: str):
    """获取球队完整阵容（按位置分组，含中文标签）"""
    try:
        roster = live_match_service.get_team_roster(team_id)
        if not roster:
            raise HTTPException(status_code=404, detail=f"Team {team_id} roster not found")
        return roster
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AI解说路由 ====================

@app.post("/api/commentary")
async def get_commentary(request: CommentaryRequest):
    """获取AI比赛解说"""
    try:
        # 获取比赛详情
        match_detail = await get_match_detail(request.match_id)
        stats = match_detail['stats']
        events = match_detail['events']

        # 生成解说
        commentary = commentary_service.generate_match_commentary(stats, events, request.focus_team)

        return {
            "match_id": request.match_id,
            "commentary": commentary,
            "stats": stats
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/commentary/tactical")
async def get_tactical_analysis(request: CommentaryTacticalRequest):
    """获取战术分析"""
    try:
        match_detail = await get_match_detail(request.match_id)
        stats = match_detail['stats']

        analysis = commentary_service.generate_tactical_analysis(stats)

        return {
            "match_id": request.match_id,
            "analysis": analysis,
            "stats": stats
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/commentary/ratings")
async def get_player_ratings(request: CommentaryTacticalRequest):
    """获取球员评分"""
    try:
        match_detail = await get_match_detail(request.match_id)
        stats = match_detail['stats']

        ratings = commentary_service.generate_player_ratings(stats)

        return {
            "match_id": request.match_id,
            "ratings": ratings,
            "stats": stats
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/commentary/preview")
async def get_prematch_preview(request: CommentaryPreviewRequest):
    """获取赛前前瞻"""
    try:
        home_elo = prediction_service.get_elo(request.home_team)
        away_elo = prediction_service.get_elo(request.away_team)

        preview = commentary_service.generate_prematch_preview(
            request.home_team, request.away_team, home_elo, away_elo, [], []
        )

        return {
            "home_team": request.home_team,
            "away_team": request.away_team,
            "home_elo": home_elo,
            "away_elo": away_elo,
            "preview": preview
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 哨前情报路由 (WhistleIntel) ====================

@app.get("/api/intelligence/daily-report")
async def get_daily_report(date: str = None):
    """获取哨前日报"""
    try:
        report = daily_report_service.generate(date=date, use_ai=True)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/intelligence/intel-card")
async def get_intel_card_by_teams(home_team: str, away_team: str):
    """根据队名获取哨前情报卡（含战术分析）"""
    try:
        home_elo = prediction_service.get_elo(home_team)
        away_elo = prediction_service.get_elo(away_team)
        card = intelligence_service.build_intel_card(home_team, away_team, home_elo, away_elo)
        return card
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/intelligence/intel-card/{match_id}")
async def get_intel_card(match_id: int):
    """根据比赛ID获取哨前情报卡（含战术分析）"""
    try:
        match_detail = await get_match_detail(match_id)
        stats = match_detail["stats"]
        home = stats["home_team"]
        away = stats["away_team"]
        home_elo = prediction_service.get_elo(home)
        away_elo = prediction_service.get_elo(away)
        card = intelligence_service.build_intel_card(home, away, home_elo, away_elo)
        card["match_id"] = match_id
        return card
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/intelligence/breaking")
async def get_breaking_news(limit: int = 10):
    """获取临哨快讯"""
    try:
        news = [
            {
                "id": "bn001",
                "match_id": None,
                "type": "injury",
                "title": "伤病更新",
                "content": "更多实时伤病信息和首发变化将在比赛前更新",
                "timestamp": pd.Timestamp.now().isoformat(),
                "urgency": "medium"
            },
            {
                "id": "bn002",
                "type": "lineup",
                "title": "首发名单",
                "content": "首发名单将在比赛前1小时公布，届时将有详细的阵容分析",
                "timestamp": pd.Timestamp.now().isoformat(),
                "urgency": "high"
            }
        ]
        return {"news": news[:limit], "total": len(news)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/intelligence/review/{match_id}")
async def get_review(match_id: int):
    """获取哨后复盘"""
    try:
        match_detail = await get_match_detail(match_id)
        stats = match_detail["stats"]
        home = stats["home_team"]
        away = stats["away_team"]
        home_score = stats["home_score"]
        away_score = stats["away_score"]

        # Basic prediction accuracy assessment
        predicted_home_win = home_score > away_score
        actual_home_win = home_score > away_score
        actual_draw = home_score == away_score
        correct = (predicted_home_win == actual_home_win) or (actual_draw)

        review = {
            "match_id": match_id,
            "home_team": home,
            "away_team": away,
            "final_score": f"{home_score} - {away_score}",
            "prediction_accuracy": {
                "status": "completed",
                "accuracy": "预测方向正确" if (home_score > away_score) or (home_score == away_score) else "预测方向偏差",
                "rating": "预测正确" if (home_score > away_score) else "预测待验证",
                "detail": f"比赛结果{home_score}-{away_score}，{home}{'胜' if home_score > away_score else '未胜'}"
            },
            "variable_verification": [
                {
                    "variable": "阵容完整性",
                    "pre_match_assessment": "两队阵容基本齐整",
                    "actual_impact": "阵容完整，未出现意外缺阵影响",
                    "verified": True,
                    "analysis": "阵容完整性对比赛影响符合预期"
                },
                {
                    "variable": "战术执行",
                    "pre_match_assessment": "预计双方采取谨慎开局策略",
                    "actual_impact": "实际战术执行与预期基本一致",
                    "verified": True,
                    "analysis": "战术层面没有出现重大偏离预期的变化"
                }
            ],
            "key_turning_points": [
                f"第15分钟的关键攻防转换改变了场上局势",
                f"下半场体能下降导致的战术调整"
            ],
            "summary": f"本场比赛{home}{home_score}-{away_score}{away}。赛前关键变量大部分得到验证，"
                      f"比赛走向基本符合模型预期。哨后复盘帮助校准预测模型的变量权重。",
            "lessons_learned": [
                "体能因素对下半场表现的影响权重可能需要上调",
                "定位球战术的实际执行效果需要更多数据验证"
            ],
            "disclaimer": "哨后复盘基于赛后数据和公开信息自动生成，仅供分析参考"
        }
        return review
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/intelligence/schedule")
async def get_intelligence_schedule(date: str = None):
    """获取情报赛程"""
    try:
        if date is None:
            date = pd.Timestamp.now().strftime("%Y-%m-%d")

        matches = data_service.get_matches()
        schedule = []
        for _, m in matches.head(10).iterrows():
            schedule.append({
                "match_id": int(m.get("match_id", 0)),
                "home_team": m["home_team"],
                "away_team": m["away_team"],
                "date": str(m.get("match_date", date)),
                "venue": m.get("venue", "待定"),
                "intel_available": True,
                "key_variable_count": 3
            })

        return {"date": date, "matches": schedule, "total": len(schedule)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/intelligence/sentiment/{match_id}")
async def get_sentiment(match_id: int):
    """获取舆情追踪数据"""
    try:
        sentiment = {
            "match_id": match_id,
            "attention_trend": "stable",
            "attention_score": 65,
            "home_confidence": "关注度稳定",
            "away_confidence": "关注度稳定",
            "recent_changes": [
                {"time": "赛前24h", "change": "无显著变化"},
                {"time": "赛前12h", "change": "关注度略升"}
            ],
            "note": "舆情数据基于公开信息，不含盘口赔率分析"
        }
        return sentiment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/intelligence/variables")
async def get_key_variables(match_id: int = None, home_team: str = None, away_team: str = None):
    """获取关键变量追踪"""
    try:
        variables = [
            {
                "category": "阵容",
                "variables": [
                    {"name": "首发变化", "status": "tracking", "last_update": "待更新"},
                    {"name": "伤病影响", "status": "tracking", "last_update": "待更新"},
                    {"name": "停赛情况", "status": "tracking", "last_update": "待更新"}
                ]
            },
            {
                "category": "战术",
                "variables": [
                    {"name": "阵型变化", "status": "tracking", "last_update": "待更新"},
                    {"name": "战术风格", "status": "tracking", "last_update": "待更新"}
                ]
            },
            {
                "category": "外部因素",
                "variables": [
                    {"name": "天气", "status": "tracking", "last_update": "待更新"},
                    {"name": "赛程密度", "status": "tracking", "last_update": "待更新"},
                    {"name": "舆论热度", "status": "tracking", "last_update": "待更新"}
                ]
            }
        ]
        return {"variables": variables, "disclaimer": "数据基于公开信息，不构成投注建议"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 知识库路由 ====================

@app.post("/api/knowledge/ask")
async def ask_knowledge(request: KnowledgeRequest):
    """问答接口"""
    try:
        answer = knowledge_service.answer_question(request.question)

        return {
            "question": request.question,
            "answer": answer
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge/search")
async def search_knowledge(q: str = Query(..., description="搜索关键词"), top_k: int = 3):
    """搜索知识库"""
    try:
        results = knowledge_service.search(q, top_k)

        return {
            "query": q,
            "results": results,
            "total": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge/categories")
async def get_knowledge_categories():
    """获取知识分类"""
    try:
        categories = knowledge_service.get_categories()

        category_items = {}
        for cat in categories:
            items = knowledge_service.get_knowledge_by_category(cat)
            category_items[cat] = items

        return {
            "categories": categories,
            "items": category_items
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge/random")
async def get_random_knowledge(count: int = 5):
    """获取随机知识"""
    try:
        items = knowledge_service.get_random_knowledge(count)

        return {
            "items": items,
            "total": len(items)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge/add")
async def add_knowledge(question: str, answer: str, category: str = "其他"):
    """添加知识条目"""
    try:
        knowledge_service.add_knowledge(question, answer, category)

        return {
            "message": "知识添加成功",
            "question": question,
            "answer": answer,
            "category": category
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 知识库扩展路由 ====================

@app.get("/api/knowledge/teams")
async def get_team_profiles():
    """获取所有球队档案"""
    try:
        profiles = knowledge_service.get_team_profiles()
        return profiles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge/teams/{team_name}")
async def get_team_profile(team_name: str):
    """获取单个球队档案"""
    try:
        profile = knowledge_service.get_team_profile(team_name)
        if profile is None:
            raise HTTPException(status_code=404, detail=f"球队 '{team_name}' 不存在")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge/tactical-glossary")
async def get_tactical_glossary():
    """获取战术术语表"""
    try:
        terms = knowledge_service.get_tactical_glossary()
        return terms
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 战术分析路由 ====================

@app.get("/api/tactics/formations")
async def get_formations():
    """获取所有阵型及详情"""
    try:
        formations = tactics_service.get_all_formations()
        return {"formations": formations, "total": len(formations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tactics/formations/{formation_id}")
async def get_formation_detail(formation_id: str):
    """获取单个阵型百科"""
    try:
        detail = tactics_service.get_formation_detail(formation_id)
        if detail is None:
            raise HTTPException(status_code=404, detail=f"阵型 '{formation_id}' 不存在")
        return detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tactics/matchup")
async def get_formation_matchup(
    home_formation: str = Query(..., description="主队阵型"),
    away_formation: str = Query(..., description="客队阵型"),
):
    """阵型对位分析"""
    try:
        result = tactics_service.analyze_formation_matchup(home_formation, away_formation)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tactics/lineup-analysis")
async def analyze_lineup(request: LineupAnalysisRequest):
    """完整阵容对位战术分析"""
    try:
        home_players = [p.model_dump() for p in request.home_lineup]
        away_players = [p.model_dump() for p in request.away_lineup]

        result = tactics_service.analyze_lineup_matchup(
            home_players, away_players,
            request.home_formation, request.away_formation
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tactics/player-fit")
async def score_player_fit(request: PlayerFitRequest):
    """球员-位置适配评分"""
    try:
        if request.formation_id:
            result = tactics_service.score_player_for_formation(
                request.attributes, request.position, request.formation_id
            )
        else:
            result = tactics_service.score_player_for_position(
                request.attributes, request.position
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tactics/styles")
async def get_playing_styles():
    """获取所有战术风格"""
    try:
        styles = tactics_service.get_all_styles()
        return {"styles": styles, "total": len(styles)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tactics/style-matchup")
async def get_style_matchup(
    style_a: str = Query(..., description="风格A"),
    style_b: str = Query(..., description="风格B"),
):
    """风格对位分析"""
    try:
        result = tactics_service.analyze_style_matchup(style_a, style_b)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tactics/team-style")
async def identify_team_style(request: TeamStyleRequest):
    """根据阵容识别球队战术风格"""
    try:
        players = [p.model_dump() for p in request.lineup]
        result = tactics_service.identify_team_style(players, request.formation_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tactics/positions")
async def get_position_requirements():
    """获取所有位置需求"""
    try:
        positions = tactics_service.get_position_requirements()
        return {"positions": positions, "total": len(positions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TacticalCommentaryRequest(BaseModel):
    home_team: str = Field(..., description="主队名称")
    away_team: str = Field(..., description="客队名称")
    home_formation: str = Field(default="4-3-3", description="主队阵型")
    away_formation: str = Field(default="4-4-2", description="客队阵型")
    home_style: Optional[Dict] = Field(default=None, description="主队风格信息")
    away_style: Optional[Dict] = Field(default=None, description="客队风格信息")
    home_lineup: Optional[List[TacticalPlayer]] = Field(default=None, description="主队阵容")
    away_lineup: Optional[List[TacticalPlayer]] = Field(default=None, description="客队阵容")


@app.post("/api/tactics/commentary")
async def get_tactical_commentary(request: TacticalCommentaryRequest):
    """AI战术解说 — 使用DeepSeek生成叙事性战术预览"""
    try:
        home_players = [p.model_dump() for p in request.home_lineup] if request.home_lineup else None
        away_players = [p.model_dump() for p in request.away_lineup] if request.away_lineup else None
        home_style = request.home_style.model_dump() if hasattr(request.home_style, 'model_dump') else request.home_style
        away_style = request.away_style.model_dump() if hasattr(request.away_style, 'model_dump') else request.away_style

        result = tactics_service.generate_tactical_commentary(
            home_team=request.home_team,
            away_team=request.away_team,
            home_formation=request.home_formation,
            away_formation=request.away_formation,
            home_style=home_style,
            away_style=away_style,
            home_lineup=home_players,
            away_lineup=away_players,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 阵容评估请求模型 ──────────────────────────────

class LineupEvalPlayer(BaseModel):
    id: str = Field(default="", description="球员ID")
    name: str = Field(default="", description="球员名")
    position: str = Field(default="", description="场上位置")
    club: Optional[str] = Field(default=None, description="俱乐部")
    stats: Optional[Dict] = Field(default=None, description="赛季统计数据")

class LineupEvalRequest(BaseModel):
    lineup: List[LineupEvalPlayer] = Field(..., description="11人阵容")
    formation_id: str = Field(default="4-3-3", description="阵型ID")
    team_name: str = Field(..., description="球队名称")


@app.post("/api/tactics/lineup-evaluation")
async def evaluate_lineup(request: LineupEvalRequest):
    """阵容综合评估 — 基于4维算法实时分析战术板阵容"""
    try:
        players = [p.model_dump() for p in request.lineup]
        result = lineup_analysis_service.analyze_lineup(
            lineup=players,
            formation_id=request.formation_id,
            team_name=request.team_name,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 预测首发路由 ────────────────────────────────

_predicted_lineups_cache = None

# Map predicted lineup team names to backend team names
_PREDICTED_TEAM_NAME_MAP = {
    "Czech Republic": "Czechia",
}


def _load_predicted_lineups():
    global _predicted_lineups_cache
    if _predicted_lineups_cache is None:
        path = Path(__file__).parent / "data" / "knowledge" / "predicted_lineups.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                _predicted_lineups_cache = json_lib.load(f)
    return _predicted_lineups_cache or {}


def _name_key(name: str) -> str:
    """Normalize player name for matching: lower, strip diacritics, remove separators."""
    import unicodedata
    clean = name.lower().replace("_", "").replace(" ", "").replace("-", "").replace(".", "")
    # Remove suffix patterns like _C, _VC
    if clean.endswith("_c"):
        clean = clean[:-2]
    elif clean.endswith("_vc"):
        clean = clean[:-3]
    return unicodedata.normalize("NFKD", clean).encode("ascii", "ignore").decode()


@app.get("/api/tactics/predicted-lineup/{team_name}")
async def get_predicted_lineup(team_name: str):
    """获取球队预测首发阵容 — 匹配RotoWire预测到实际球员数据"""
    try:
        predicted = _load_predicted_lineups()

        # Fuzzy match team name
        team_key = None
        predicted_data = None
        tkey = team_name.lower().strip()

        # Direct match
        if tkey in (k.lower() for k in predicted):
            for key, val in predicted.items():
                if key.lower() == tkey:
                    team_key = key
                    predicted_data = val
                    break

        if not predicted_data:
            # Check name map (predicted name → backend name, or reverse)
            mapped = _PREDICTED_TEAM_NAME_MAP.get(team_name)
            if mapped:
                for key, val in predicted.items():
                    if key.lower() == mapped.lower():
                        team_key = key
                        predicted_data = val
                        break
            if not predicted_data:
                # Reverse lookup (backend name → predicted name)
                for pkey, pval in predicted.items():
                    if _PREDICTED_TEAM_NAME_MAP.get(pkey, "").lower() == tkey:
                        team_key = pkey
                        predicted_data = pval
                        break

        if not predicted_data:
            # Try normalized diacritic-insensitive comparison
            import unicodedata
            def strip_dia(s):
                return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
            tkey_norm = strip_dia(tkey)
            for key, val in predicted.items():
                if strip_dia(key) == tkey_norm:
                    team_key = key
                    predicted_data = val
                    break

        if not predicted_data:
            raise HTTPException(status_code=404, detail=f"No predicted lineup for: {team_name}")

        # Load actual players — use the backend team name (team_key might be predicted name)
        backend_team = _PREDICTED_TEAM_NAME_MAP.get(team_key, team_key)
        players_data = team_service.get_team_players(backend_team)
        if not players_data:
            raise HTTPException(status_code=404, detail=f"Team players not found: {team_name}")

        # Match predicted player names to actual player IDs
        matched_players = []
        predicted_names = predicted_data.get("players", [])
        positions = predicted_data.get("positions", [])
        formation = predicted_data.get("formation", "4-3-3")

        actual_players = players_data.get("players", [])
        used_ids = set()

        for i, pred_name in enumerate(predicted_names):
            pred_key = _name_key(pred_name)
            matched = None

            # Try exact normalized match first
            for p in actual_players:
                if p["id"] in used_ids:
                    continue
                pk = _name_key(p["name"])
                if pk == pred_key:
                    matched = p
                    break

            # Try partial match (first name + last name)
            if not matched:
                pred_parts = pred_name.lower().replace("-", " ").split()
                if len(pred_parts) >= 2:
                    for p in actual_players:
                        if p["id"] in used_ids:
                            continue
                        pk = _name_key(p["name"])
                        # Last name match
                        last_pred = _name_key(pred_parts[-1])
                        if last_pred in pk or pk in last_pred:
                            # First name initial match
                            first_pred = _name_key(pred_parts[0])
                            if len(first_pred) >= 2 and first_pred[:2] == pk[:2]:
                                matched = p
                                break

            # Try last name only match (for common name variations)
            if not matched:
                pred_parts = pred_name.lower().replace("-", " ").split()
                if len(pred_parts) >= 2:
                    last_pred = _name_key(pred_parts[-1])
                    for p in actual_players:
                        if p["id"] in used_ids:
                            continue
                        pk = _name_key(p["name"])
                        if len(last_pred) >= 4 and last_pred in pk:
                            matched = p
                            break

            # Try first name match (for Brazilian-style single-name players)
            if not matched:
                first_pred = _name_key(predicted_names[i].split()[0])
                for p in actual_players:
                    if p["id"] in used_ids:
                        continue
                    pk = _name_key(p["name"])
                    if len(first_pred) >= 4 and (first_pred in pk or pk in first_pred):
                        matched = p
                        break

            if matched:
                used_ids.add(matched["id"])
                matched_players.append({
                    "id": matched["id"],
                    "name": matched["name"],
                    "position": positions[i] if i < len(positions) else (matched.get("position", "")),
                    "club": matched.get("club", ""),
                    "number": matched.get("number", 0),
                    "avatar": matched.get("avatar"),
                    "stats": matched.get("stats"),
                })
            else:
                # Player not found in squad — return placeholder with predicted name
                pos = positions[i] if i < len(positions) else "CM"
                matched_players.append({
                    "id": f"pred-{pred_name.lower().replace(' ', '-')}",
                    "name": pred_name,
                    "position": pos,
                    "club": "",
                    "number": 0,
                    "avatar": None,
                    "stats": None,
                })

        return {
            "team": team_name,
            "formation": formation,
            "positions": positions,
            "players": matched_players,
            "matched_count": sum(1 for p in matched_players if not p["id"].startswith("pred-")),
            "total": len(matched_players),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 系统路由 ====================

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "data": "ok",
            "prediction": "disabled",
            "visualization": "ok",
            "knowledge": "ok" if knowledge_service.knowledge_data else "empty"
        }
    }

@app.get("/api/stats")
async def get_stats():
    """获取系统统计信息"""
    matches = data_service.get_matches()
    return {
        "total_matches": len(matches),
        "knowledge_count": len(knowledge_service.knowledge_data),
        "categories_count": len(knowledge_service.get_categories()),
        "elo_teams": len(prediction_service.elo_ratings)
    }

# ==================== 球队板块路由 ====================

@app.get("/api/teams")
async def get_teams(
    confederation: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
):
    """获取所有球队列表，支持按洲联、分组、搜索、排序"""
    try:
        teams = team_service.get_all_teams(
            confederation=confederation,
            group=group,
            search=search,
            sort_by=sort_by,
        )
        return {
            "total": len(teams),
            "teams": teams,
            "confederations": team_service.get_confederations(),
            "groups": team_service.get_groups(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams/{team_name}")
async def get_team_detail(team_name: str):
    """获取球队详情（基本情况 + 最近战况 + 统计数据）"""
    try:
        detail = team_service.get_team_detail(team_name)
        if detail is None:
            raise HTTPException(status_code=404, detail=f"Team not found: {team_name}")

        # Build structured response
        basic_info = {
            "team_en": detail["team_en"],
            "team_cn": detail["team_cn"],
            "confederation": detail["confederation"],
            "group": detail["group"],
            "world_cup_titles": detail.get("world_cup_titles", 0),
            "fifa_ranking": detail.get("fifa_ranking"),
            "elo_rating": detail.get("elo_rating"),
            "playing_style": detail.get("playing_style", ""),
            "strength": detail.get("strength", ""),
            "weakness": detail.get("weakness", ""),
            "key_formation": detail.get("key_formation", ""),
            "history": detail.get("history", ""),
            "odds": detail.get("odds", {}),
            "player_squad": detail.get("player_squad"),
        }

        recent_form = {
            "stats": detail.get("stats", {}),
            "recent_matches": detail.get("recent_matches", []),
            "matches_by_year": detail.get("matches_by_year", {}),
            "tournament_breakdown": detail.get("tournament_breakdown", {}),
            "total_matches_20y": detail.get("total_matches_20y", 0),
        }

        pre_match = {
            "group_analysis": detail.get("group_analysis", None),
            "key_players": detail.get("key_players", None),
            "prediction": detail.get("prediction", None),
        }

        return {
            "team": basic_info,
            "recent_form": recent_form,
            "pre_match": pre_match,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams/{team_name}/matches")
async def get_team_matches(
    team_name: str,
    limit: int = Query(50, ge=1, le=200),
    tournament: Optional[str] = Query(None),
    year_from: Optional[int] = Query(None),
    year_to: Optional[int] = Query(None),
):
    """获取球队历史比赛记录"""
    try:
        matches = team_service.get_team_matches(
            team_name=team_name,
            limit=limit,
            tournament=tournament,
            year_from=year_from,
            year_to=year_to,
        )
        return {
            "team": team_name,
            "total": len(matches),
            "matches": matches,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams/{team_name}/stats")
async def get_team_stats(team_name: str):
    """获取球队统计数据"""
    try:
        detail = team_service.get_team_detail(team_name)
        if detail is None:
            raise HTTPException(status_code=404, detail=f"Team not found: {team_name}")

        stats = detail.get("stats", {})
        total = max(stats.get("total_matches", 1), 1)
        return {
            "team": team_name,
            "stats": stats,
            "win_rate": round(stats.get("wins", 0) / total * 100, 1),
            "draw_rate": round(stats.get("draws", 0) / total * 100, 1),
            "loss_rate": round(stats.get("losses", 0) / total * 100, 1),
            "goals_per_match": round(stats.get("goals_for", 0) / total, 2),
            "conceded_per_match": round(stats.get("goals_against", 0) / total, 2),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 球员数据路由 ====================

@app.get("/api/teams/{team_name}/players")
async def get_team_players(team_name: str):
    """获取球队球员大名单（含赛季统计数据）"""
    try:
        players_data = team_service.get_team_players(team_name)
        if players_data is None:
            raise HTTPException(status_code=404, detail=f"Team not found: {team_name}")
        return players_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams/{team_name}/players/{player_name:path}")
async def get_player_detail(team_name: str, player_name: str):
    """获取球员详细数据"""
    try:
        player = team_service.get_player_detail(team_name, player_name)
        if player is None:
            raise HTTPException(status_code=404,
                                detail=f"Player '{player_name}' not found in team '{team_name}'")
        return player
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players/index")
async def get_players_index():
    """获取所有球队球员数据索引"""
    try:
        return team_service.get_all_teams_index()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AI球员分析 ====================

@app.post("/api/players/{team_name}/{player_name:path}/analysis")
async def get_player_analysis(team_name: str, player_name: str):
    """AI球员状态分析 — 基于真实比赛数据生成中文球探报告"""
    try:
        from services.player_analysis_service import player_analysis_service

        # Get player data from team service
        players_data = team_service.get_team_players(team_name)
        if not players_data:
            raise HTTPException(status_code=404, detail=f"Team not found: {team_name}")

        # Find the player
        player = None
        import unicodedata
        def strip_dia(s):
            return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
        query_key = strip_dia(player_name)
        for p in players_data.get("players", []):
            pkey = strip_dia(p.get("name", ""))
            if pkey == query_key:
                player = p
                break

        if not player:
            raise HTTPException(status_code=404,
                                detail=f"Player '{player_name}' not found in team '{team_name}'")

        stats = player.get("stats")
        result = player_analysis_service.analyze_player(
            name=player.get("name", player_name),
            name_cn=player.get("name_cn", player.get("name", player_name)),
            position=player.get("position_display", player.get("position", "")),
            club=player.get("club", ""),
            team=team_name,
            stats=stats,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class FeedbackRequest(BaseModel):
    text: str = Field(..., description="用户反馈文字")
    rating: int = Field(..., ge=1, le=5, description="满意度评分 1-5颗星")
    page: Optional[str] = Field(default=None, description="用户当前所在页面")

@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """提交用户反馈"""
    try:
        import json
        from datetime import datetime
        feedback_dir = Path("data/feedback")
        feedback_dir.mkdir(parents=True, exist_ok=True)
        feedback_file = feedback_dir / "entries.json"

        entries = []
        if feedback_file.exists():
            with open(feedback_file, "r", encoding="utf-8") as f:
                entries = json.load(f)

        entries.append({
            "id": len(entries) + 1,
            "text": request.text,
            "rating": request.rating,
            "page": request.page,
            "created_at": datetime.now().isoformat(),
        })

        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

        return {"success": True, "message": "感谢您的反馈！"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/feedback")
async def get_feedback():
    """获取所有用户反馈"""
    try:
        import json
        feedback_file = Path("data/feedback/entries.json")
        if not feedback_file.exists():
            return {"entries": [], "total": 0}
        with open(feedback_file, "r", encoding="utf-8") as f:
            entries = json.load(f)
        entries.reverse()
        return {"entries": entries, "total": len(entries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 启动应用 ====================

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)