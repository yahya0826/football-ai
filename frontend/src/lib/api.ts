/**
 * API 客户端 - 与后端通信
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | undefined>;
}

async function fetchAPI<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { params, ...fetchOptions } = options;

  let url = `${API_BASE}${endpoint}`;

  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, String(value));
      }
    });
    const query = searchParams.toString();
    if (query) {
      url += `?${query}`;
    }
  }

  const response = await fetch(url, {
    ...fetchOptions,
    headers: {
      'Content-Type': 'application/json',
      ...fetchOptions.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// 类型定义
export interface Match {
  match_id: number;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  date: string;
  competition: string;
  season: string;
  venue: string;
  status: string;
}

export interface MatchStats {
  match_id: number;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  home_shots: number;
  away_shots: number;
  home_shots_on_target: number;
  away_shots_on_target: number;
  home_possession: number;
  away_possession: number;
  home_pass_accuracy: number;
  away_pass_accuracy: number;
  home_xg: number;
  away_xg: number;
  home_corners: number;
  away_corners: number;
  home_fouls: number;
  away_fouls: number;
  home_yellows: number;
  away_yellows: number;
  home_reds: number;
  away_reds: number;
}

export interface MatchEvent {
  type: string;
  minute: number;
  team: string;
  player: string;
  description: string;
}

export interface KnowledgeItem {
  question: string;
  answer: string;
  category: string;
  relevance?: number;
}

export interface DailyReport {
  date: string;
  generated_at: string;
  total_matches: number;
  key_match_focus: string;
  sections: ReportSection[];
  summary: string;
  disclaimer: string;
}

export interface ReportSection {
  title: string;
  icon?: string;
  type?: string;
  content: string;
  priority?: string;
  matches_count?: number;
  key_match?: Match | null;
  items?: ReportItem[];
}

export interface ReportItem {
  name: string;
  status?: string;
  description?: string;
}

export interface TeamIntel {
  name: string;
  elo: number;
  recent_form: string;
  injuries: InjuryItem[];
  predicted_lineup: LineupInfo;
  tactical_note: string;
  key_player: string;
  style?: StyleInfo;
  recent_news?: NewsItem[];
}

export interface InjuryItem {
  player: string;
  type?: string;
  status: string;
  impact: string;
  expected_return?: string;
  position?: string;
}

export interface LineupInfo {
  team: string;
  formation: string;
  confidence: string;
  key_changes?: string[];
  note: string;
}

export interface StyleInfo {
  formation: string;
  style: string;
  strength: string;
  weakness: string;
}

export interface NewsItem {
  title: string;
  source: string;
  type: string;
  summary: string;
}

export interface IntelCard {
  home_team: TeamIntel;
  away_team: TeamIntel;
  match_context: MatchContext;
  key_variables: KeyVariable[];
  prediction_insight?: string;
  confidence_note?: string;
  sentiment?: SentimentData;
  status?: string;
  disclaimer?: string;
}

export interface MatchContext {
  venue?: string;
  weather?: string;
  referee?: string;
  importance?: string;
  score?: string;
  elo_gap?: string;
  elo_gap_description?: string;
  style_clash?: string;
  favorite?: string;
}

export interface KeyVariable {
  name: string;
  status: 'confirmed' | 'uncertain' | 'changing' | 'tracking';
  impact: 'high' | 'medium' | 'low';
  description: string;
  trend: string;
  home_detail?: string;
  away_detail?: string;
  home_status?: string;
  away_status?: string;
}

export interface BreakingNewsItem {
  id: string;
  type: string;
  urgency: string;
  title: string;
  content: string;
  timestamp: string;
  verified?: boolean;
  source?: string;
  match_id?: number;
}

export interface ReviewData {
  match_id: number;
  home_team: string;
  away_team: string;
  final_score: string;
  prediction_accuracy: { status: string; accuracy: string; rating: string; detail?: string };
  variable_verification: VariableVerification[];
  key_turning_points: string[];
  summary: string;
  lessons_learned?: string[];
  disclaimer?: string;
}

export interface VariableVerification {
  variable: string;
  pre_match_assessment: string;
  actual_impact: string;
  verified: boolean;
  analysis: string;
}

export interface SentimentData {
  attention_trend: string;
  attention_description: string;
  attention_score: number;
  home_expectation: string;
  away_expectation: string;
  recent_changes?: { time: string; description: string; direction: string }[];
  disclaimer?: string;
}

export interface ScheduleData {
  date: string;
  matches: { match_id: number; home_team: string; away_team: string; date: string; venue: string; intel_available: boolean; key_variable_count: number }[];
  total: number;
}

// ── 临哨快讯 / 伤病情报 (Injury Intel) ──────────────────

export interface InjuryIntelItem {
  player: string;
  player_cn: string;
  status: string;
  status_cn: string;
  detail: string;
  source: string;
}

export interface TeamInjuryIntel {
  name_cn: string;
  injuries: InjuryIntelItem[];
  predicted_lineup: {
    formation: string;
    formation_cn?: string;
    players: string[];
    players_cn?: string[];
  };
  recent_form: string;
  score_prediction?: string;
  score_prediction_cn?: string;
}

export interface InjuriesResponse {
  date: string;
  last_updated: string;
  teams: Record<string, TeamInjuryIntel>;
  total_teams?: number;
}

export interface TeamProfile {
  team: string;
  confederation: string;
  world_cup_titles: number;
  playing_style: string;
  strength: string;
  weakness: string;
  key_formation: string;
  history: string;
  rivalries: string[];
}

export interface TacticalTerm {
  term: string;
  category: string;
  explanation: string;
}

// Team section types (new teams module)
export interface TeamBasic {
  team_en: string;
  team_cn: string;
  confederation: string;
  group: string;
  world_cup_titles?: number;
  fifa_ranking?: number;
  elo_rating?: number;
  playing_style?: string;
  strength?: string;
  weakness?: string;
  key_formation?: string;
  history?: string;
  odds?: Record<string, any>;
}

export interface TeamListItem {
  team_en: string;
  team_cn: string;
  confederation: string;
  group: string;
  stats: TeamStats;
  total_matches_20y: number;
}

export interface TeamStats {
  total_matches: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
}

export interface MatchRecord {
  date: string;
  home_team: string;
  away_team: string;
  home_score: string;
  away_score: string;
  tournament: string;
  city: string;
  country: string;
  neutral: string;
}

export interface TeamDetail {
  team: TeamBasic;
  recent_form: {
    stats: TeamStats;
    recent_matches: MatchRecord[];
    matches_by_year: Record<string, number>;
    tournament_breakdown: Record<string, number>;
    total_matches_20y: number;
  };
  pre_match: {
    group_analysis: any;
    key_players: any;
    prediction: any;
  };
}

export interface TeamsListResponse {
  total: number;
  teams: TeamListItem[];
  confederations: { name: string; count: number }[];
  groups: string[];
}

// 赛程相关类型
export interface ScheduleMatch {
  match_id: number;
  stage: string;
  group: string;
  round: number;
  date: string;
  time_bj: string;
  home_team: string;
  away_team: string;
  home_team_cn: string;
  away_team_cn: string;
  venue: string;
  city: string;
  country: string;
  note?: string;
  home_score?: number;
  away_score?: number;
}

export interface ScheduleGroup {
  name: string;
  teams: string[];
  teams_cn: string[];
}

export interface ScheduleVenue {
  name: string;
  name_cn: string;
  city: string;
  city_cn: string;
  country: string;
  capacity: number;
}

export interface StageLabel {
  name: string;
  name_cn: string;
  rounds: number;
}

export interface MatchScheduleResponse {
  total: number;
  groups?: Record<string, ScheduleGroup>;
  venues?: ScheduleVenue[];
  stage_labels?: Record<string, StageLabel>;
  matches: ScheduleMatch[];
}

export interface H2HData {
  total_matches: number;
  home_wins: number;
  away_wins: number;
  draws: number;
  matches: Array<{
    date: string;
    home_team: string;
    away_team: string;
    home_score: string | number;
    away_score: string | number;
    tournament: string;
    city?: string;
    neutral?: string;
  }>;
}

export interface RecentMatch {
  date: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  tournament: string;
  result: 'W' | 'D' | 'L';
  is_home: boolean;
}

export interface MatchTeamProfile {
  team: string;
  playing_style?: string;
  strength?: string;
  weakness?: string;
  key_formation?: string;
  tactical_profile?: Record<string, unknown>;
}

export interface MatchDetailResponse {
  match: ScheduleMatch;
  h2h: H2HData | null;
  home_recent: RecentMatch[] | null;
  away_recent: RecentMatch[] | null;
  highlights: string | null;
  team_profiles: {
    home: MatchTeamProfile | null;
    away: MatchTeamProfile | null;
  } | null;
}

// API 函数
export const api = {
  // 赛程相关
  async getMatchSchedule(params?: {
    stage?: string;
    group?: string;
    date_from?: string;
    date_to?: string;
    team?: string;
  }): Promise<MatchScheduleResponse> {
    return fetchAPI('/api/schedule', { params });
  },

  async getScheduleDates(): Promise<{ dates: string[]; count: number }> {
    return fetchAPI('/api/schedule/dates');
  },

  async getScheduleMatch(matchId: number): Promise<MatchDetailResponse> {
    return fetchAPI(`/api/schedule/${matchId}`);
  },

  // 旧比赛数据（保留兼容）
  async getMatches(competitionId = 43, seasonId = 106): Promise<{ matches: Match[]; total: number }> {
    return fetchAPI('/api/matches', { params: { competition_id: competitionId, season_id: seasonId } });
  },

  async getMatchDetail(matchId: number): Promise<{ stats: MatchStats; events: MatchEvent[] }> {
    return fetchAPI(`/api/matches/${matchId}`);
  },

  // 可视化相关
  async getVisualization(matchId: number): Promise<{
    match_id: number;
    home_team: string;
    away_team: string;
    visualizations: Record<string, string | null>;
  }> {
    return fetchAPI(`/api/visual/${matchId}`);
  },

  async getXgChart(matchId: number): Promise<{ match_id: number; xg_chart: string }> {
    return fetchAPI(`/api/visual/xg/${matchId}`);
  },

  async getShotmap(matchId: number, team?: string): Promise<{ match_id: number; team?: string; shotmap: string }> {
    return fetchAPI(`/api/visual/shotmap/${matchId}`, { params: { team } });
  },

  async getHeatmap(matchId: number, team: string): Promise<{ match_id: number; team: string; heatmap: string }> {
    return fetchAPI(`/api/visual/heatmap/${matchId}`, { params: { team } });
  },

  // AI解说相关
  async getCommentary(matchId: number, focusTeam?: string): Promise<{ match_id: number; commentary: string; stats: MatchStats }> {
    return fetchAPI('/api/commentary', {
      method: 'POST',
      body: JSON.stringify({ match_id: matchId, focus_team: focusTeam }),
    });
  },

  async getTacticalAnalysis(matchId: number): Promise<{ match_id: number; analysis: string; stats: MatchStats }> {
    return fetchAPI('/api/commentary/tactical', {
      method: 'POST',
      body: JSON.stringify({ match_id: matchId }),
    });
  },

  // 知识库相关
  async askKnowledge(question: string): Promise<{ question: string; answer: string }> {
    return fetchAPI('/api/knowledge/ask', {
      method: 'POST',
      body: JSON.stringify({ question }),
    });
  },

  async searchKnowledge(q: string, topK = 3): Promise<{ query: string; results: KnowledgeItem[]; total: number }> {
    return fetchAPI('/api/knowledge/search', { params: { q, top_k: topK } });
  },

  async getKnowledgeCategories(): Promise<{ categories: string[]; items: Record<string, KnowledgeItem[]> }> {
    return fetchAPI('/api/knowledge/categories');
  },

  async getRandomKnowledge(count = 5): Promise<{ items: KnowledgeItem[]; total: number }> {
    return fetchAPI('/api/knowledge/random', { params: { count } });
  },

  // 哨前情报 (WhistleIntel)

  // 临哨快讯 — 伤病情报 + 预测首发 + 球队状态
  async getInjuryIntel(date?: string, forceRefresh = false): Promise<InjuriesResponse> {
    return fetchAPI('/api/intelligence/injuries', { params: { date, force_refresh: forceRefresh ? 'true' : 'false' } });
  },

  async getIntelCard(matchId: number): Promise<IntelCard> {
    return fetchAPI(`/api/intelligence/intel-card/${matchId}`);
  },

  async getPostMatchReview(matchId: number): Promise<ReviewData> {
    return fetchAPI(`/api/intelligence/review/${matchId}`);
  },

  async getSchedule(date?: string): Promise<ScheduleData> {
    return fetchAPI('/api/intelligence/schedule', { params: { date } });
  },

  async getSentiment(matchId: number): Promise<SentimentData & { match_id: number }> {
    return fetchAPI(`/api/intelligence/sentiment/${matchId}`);
  },

  async getKeyVariables(matchId?: number, homeTeam?: string, awayTeam?: string): Promise<{ variables: { category: string; variables: { name: string; status: string; last_update: string }[] }[] }> {
    return fetchAPI('/api/intelligence/variables', { params: { match_id: matchId, home_team: homeTeam, away_team: awayTeam } });
  },

  // 知识库扩展
  async getTeamProfiles(): Promise<TeamProfile[]> {
    return fetchAPI('/api/knowledge/teams');
  },

  async getTeamProfile(teamName: string): Promise<TeamProfile> {
    return fetchAPI(`/api/knowledge/teams/${encodeURIComponent(teamName)}`);
  },

  async getTacticalGlossary(): Promise<TacticalTerm[]> {
    return fetchAPI('/api/knowledge/tactical-glossary');
  },

  // 球队板块 (Teams)
  async getTeams(params?: {
    confederation?: string;
    group?: string;
    search?: string;
    sort_by?: string;
  }): Promise<TeamsListResponse> {
    return fetchAPI('/api/teams', { params });
  },

  async getTeamDetail(teamName: string): Promise<TeamDetail> {
    return fetchAPI(`/api/teams/${encodeURIComponent(teamName)}`);
  },

  async getTeamMatches(
    teamName: string,
    params?: { limit?: number; tournament?: string; year_from?: number; year_to?: number }
  ): Promise<{ team: string; total: number; matches: MatchRecord[] }> {
    return fetchAPI(`/api/teams/${encodeURIComponent(teamName)}/matches`, { params });
  },

  async getTeamStats(teamName: string): Promise<{
    team: string;
    stats: TeamStats;
    win_rate: number;
    draw_rate: number;
    loss_rate: number;
    goals_per_match: number;
    conceded_per_match: number;
  }> {
    return fetchAPI(`/api/teams/${encodeURIComponent(teamName)}/stats`);
  },

  // 系统
  async healthCheck(): Promise<{ status: string; services: Record<string, string> }> {
    return fetchAPI('/api/health');
  },

  async getStats(): Promise<{
    total_matches: number;
    knowledge_count: number;
    categories_count: number;
    elo_teams: number;
    model_loaded: boolean;
  }> {
    return fetchAPI('/api/stats');
  },

  // ── 战术分析 (Tactics) ──────────────────────────

  async getFormations(): Promise<{ formations: FormationData[]; total: number }> {
    return fetchAPI('/api/tactics/formations');
  },

  async getFormationDetail(formationId: string): Promise<FormationDetail> {
    return fetchAPI(`/api/tactics/formations/${encodeURIComponent(formationId)}`);
  },

  async getFormationMatchup(homeFormation: string, awayFormation: string): Promise<FormationMatchupResult> {
    return fetchAPI('/api/tactics/matchup', { params: { home_formation: homeFormation, away_formation: awayFormation } });
  },

  async analyzeLineup(request: LineupAnalysisRequest): Promise<LineupAnalysisResult> {
    return fetchAPI('/api/tactics/lineup-analysis', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  async scorePlayerFit(attributes: Record<string, number>, position: string, formationId?: string): Promise<PlayerFitResult> {
    return fetchAPI('/api/tactics/player-fit', {
      method: 'POST',
      body: JSON.stringify({ attributes, position, formation_id: formationId || '4-3-3' }),
    });
  },

  async getPlayingStyles(): Promise<{ styles: StyleData[]; total: number }> {
    return fetchAPI('/api/tactics/styles');
  },

  async getStyleMatchup(styleA: string, styleB: string): Promise<StyleMatchupResult> {
    return fetchAPI('/api/tactics/style-matchup', { params: { style_a: styleA, style_b: styleB } });
  },

  async identifyTeamStyle(lineup: TacticalPlayerData[], formationId: string): Promise<TeamStyleResult> {
    return fetchAPI('/api/tactics/team-style', {
      method: 'POST',
      body: JSON.stringify({ lineup, formation_id: formationId }),
    });
  },

  async getPositionRequirements(): Promise<{ positions: PositionRequirement[]; total: number }> {
    return fetchAPI('/api/tactics/positions');
  },

  // 球员数据 (战术板)
  async getTeamPlayers(teamName: string): Promise<TeamPlayersResponse> {
    return fetchAPI(`/api/teams/${encodeURIComponent(teamName)}/players`);
  },

  async getPlayerDetail(teamName: string, playerName: string): Promise<PlayerDetailResponse> {
    return fetchAPI(`/api/teams/${encodeURIComponent(teamName)}/players/${encodeURIComponent(playerName)}`);
  },

  async getPlayersIndex(): Promise<PlayersIndexResponse> {
    return fetchAPI('/api/players/index');
  },

  async getPlayerAnalysis(teamName: string, playerName: string): Promise<PlayerAnalysisResponse> {
    return fetchAPI(`/api/players/${encodeURIComponent(teamName)}/${encodeURIComponent(playerName)}/analysis`, {
      method: 'POST',
    });
  },

  // ── 阵容评估 (Lineup Evaluation) ──────────────

  async evaluateLineup(request: LineupEvalRequest): Promise<LineupEvalResponse> {
    return fetchAPI('/api/tactics/lineup-evaluation', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  async getPredictedLineup(teamName: string): Promise<PredictedLineupResponse> {
    return fetchAPI(`/api/tactics/predicted-lineup/${encodeURIComponent(teamName)}`);
  },

  // ── 实时比赛 (Live Match) ──────────────────

  async getLiveScoreboard(date?: string): Promise<LiveScoreboardResponse> {
    return fetchAPI('/api/live/scoreboard', { params: date ? { date } : undefined });
  },

  async getLiveMatchDetail(matchId: string): Promise<LiveMatchDetail> {
    return fetchAPI(`/api/live/matches/${matchId}`);
  },

  async getLiveMatchLookup(homeTeam: string, awayTeam: string, date?: string): Promise<{ match_id: string | null; found: boolean }> {
    return fetchAPI('/api/live/match-lookup', { params: { home_team: homeTeam, away_team: awayTeam, date } });
  },

  async getLiveMatchAnalysis(matchId: string): Promise<MatchAnalysisResponse> {
    return fetchAPI(`/api/live/matches/${matchId}/analysis`);
  },

  async findScheduleMatch(homeTeam: string, awayTeam: string, date?: string): Promise<{ match_id: number | null; found: boolean }> {
    return fetchAPI('/api/live/schedule-match', { params: { home_team: homeTeam, away_team: awayTeam, date } });
  },

  async getTeamRoster(teamId: string): Promise<TeamRoster> {
    return fetchAPI(`/api/live/roster/${teamId}`);
  },

  async getPlayerLiveAnalysis(
    matchId: string,
    playerId: string,
    params: { team_id: string; player_name: string; position: string; clock?: string }
  ): Promise<PlayerLiveAnalysisResponse> {
    return fetchAPI(`/api/live/matches/${matchId}/players/${playerId}/analysis`, { params });
  },

  // ── 反馈 (Feedback) ──────────────────

  async submitFeedback(data: { text: string; rating: number; page?: string }): Promise<{ success: boolean; message: string }> {
    return fetchAPI('/api/feedback', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getFeedback(): Promise<{ entries: { id: number; text: string; rating: number; page?: string; created_at: string }[]; total: number }> {
    return fetchAPI('/api/feedback');
  },
};

// 球员数据类型
export interface ApiPlayer {
  id: string;
  name: string;
  name_cn?: string;
  position: string;
  position_display?: string;
  number: number;
  club: string;
  age: number;
  national_caps: number;
  national_goals: number;
  avatar?: string;
  stats: ApiPlayerStats | null;
}

export interface ApiPlayerStats {
  rating: number;
  goals?: number;
  assists?: number;
  appearances?: number;
  starts?: number;
  minutes?: number;
  yellow_cards?: number;
  red_cards?: number;
  xg?: number;
  shots_total?: number;
  shots_on_target?: number;
  shot_accuracy?: number;
  pass_accuracy?: number;
  progressive_passes?: number;
  key_passes?: number;
  tackles?: number;
  interceptions?: number;
  clearances?: number;
  blocks?: number;
  touches?: number;
  dribble_success_rate?: number;
  match_confidence?: string | null;
  data_source?: string;
  has_real_data?: boolean;
  // per90 fields
  goals_p90?: number;
  assists_p90?: number;
  xg_p90?: number;
  xa_p90?: number;
  shots_p90?: number;
  key_passes_p90?: number;
  tackles_p90?: number;
  interceptions_p90?: number;
  start_rate?: number;
  shot_conversion?: number;
  // desktop-specific fields
  fouls?: number;
  fouled?: number;
  offsides?: number;
  crosses?: number;
  tackles_won?: number;
  pk_scored?: number;
  pk_attempted?: number;
  pk_won?: number;
  pk_conceded?: number;
  own_goals?: number;
  saves?: number;
  goals_conceded?: number;
  clean_sheets?: number;
  save_pct?: number;
  wins?: number;
  draws?: number;
  losses?: number;
  // pre-derived attributes from server
  _attributes?: {
    speed: number;
    shooting: number;
    passing: number;
    dribbling: number;
    defending: number;
    physical: number;
  };
}

export interface PlayerAnalysisResponse {
  player_name: string;
  player_name_cn?: string;
  team: string;
  analysis: string;
  data_basis: string;
  generated_at: string;
}

export interface TeamPlayersResponse {
  team: string;
  total_players: number;
  matched_count?: number;
  players: ApiPlayer[];
}

export interface PlayerDetailResponse {
  player: ApiPlayer;
  team: string;
}

export interface PlayersIndexResponse {
  teams: Record<string, { total: number; matched: number }>;
  total_teams: number;
  last_updated?: string;
}

// ── 战术分析类型 ────────────────────────────────

export interface FormationData {
  id: string;
  name: string;
  name_cn: string;
  category: string;
  description: string;
  strengths: string[];
  weaknesses: string[];
}

export interface FormationDetail extends FormationData {
  lines: { defense: number; midfield: number; attack: number };
  tactical_principles: { attack: string[]; defense: string[]; transition: string[] };
  player_requirements: Record<string, Record<string, unknown>>;
  best_against: string[];
  worst_against: string[];
  famous_examples: string[];
}

export interface FormationMatchupResult {
  home_formation: string;
  away_formation: string;
  home_advantage_score: number;
  key_battle_zones: string[];
  statistical_tendency?: { possession?: string; xg?: string; win_rate?: string };
  tactical_note: string;
  home_strengths: string[];
  away_strengths: string[];
  home_weaknesses: string[];
  away_weaknesses: string[];
}

export interface TacticalPlayerData {
  name: string;
  player_id: string;
  position: string;
  attributes: Record<string, number>;
}

export interface LineupAnalysisRequest {
  home_lineup: TacticalPlayerData[];
  away_lineup: TacticalPlayerData[];
  home_formation: string;
  away_formation: string;
}

export interface LineupAnalysisResult {
  formation_matchup: FormationMatchupResult;
  position_comparisons: PositionComparison[];
  key_matchups: KeyMatchup[];
  home_team_profile: TeamProfile6D;
  away_team_profile: TeamProfile6D;
  overall_tactical_advantage: number;
  interpretation: string;
}

export interface PositionComparison {
  zone: string;
  zone_cn: string;
  home_avg_attributes: Record<string, number>;
  away_avg_attributes: Record<string, number>;
  advantage: string;
  home_players_count: number;
  away_players_count: number;
}

export interface KeyMatchup {
  position: string;
  position_cn: string;
  home_player: { name: string; player_id: string; fit_score: number; fit: string };
  away_player: { name: string; player_id: string; fit_score: number; fit: string };
  advantage: string;
}

export interface TeamProfile6D {
  overall: Record<string, number>;
  lines: Record<string, Record<string, number>>;
}

export interface PlayerFitResult {
  score: number;
  fit: string;
  gaps: { attribute: string; current: number; ideal: number; gap: number; direction: string }[];
  formation_modifier?: number;
}

export interface StyleData {
  id: string;
  name: string;
  name_cn: string;
  description: string;
  principles: string[];
  preferred_formations: string[];
}

export interface StyleMatchupResult {
  style_a: string;
  style_a_name: string;
  style_b: string;
  style_b_name: string;
  advantage_for_a: number;
  dynamics: string;
  key_factors: string[];
}

export interface TeamStyleResult {
  primary_style: { style_id: string; style_name: string; style_name_cn: string; match_score: number } | null;
  top_styles: { style_id: string; style_name: string; style_name_cn: string; match_score: number }[];
  formation: string;
}

export interface PositionRequirement {
  position: string;
  name: string;
  name_cn: string;
  line: string;
  description: string;
  primary_attributes: string[];
  secondary_attributes: string[];
  ideal_profile: Record<string, number>;
  weight_vector: Record<string, number>;
}

// ── 预测首发类型 (Predicted Lineup) ──────────

export interface PredictedLineupPlayer {
  id: string;
  name: string;
  position: string;
  club: string;
  number: number;
  avatar?: string | null;
  stats: ApiPlayerStats | null;
}

export interface PredictedLineupResponse {
  team: string;
  formation: string;
  positions: string[];
  players: PredictedLineupPlayer[];
  matched_count: number;
  total: number;
}

// ── 阵容评估类型 (Lineup Evaluation) ──────────

export interface LineupEvalPlayer {
  id?: string;
  name?: string;
  position?: string;
  club?: string | null;
  stats?: Record<string, unknown> | null;
}

export interface LineupEvalRequest {
  lineup: LineupEvalPlayer[];
  formation_id: string;
  team_name: string;
}

export interface LineupEvalDimensions {
  player_quality: number;
  balance: number;
  chemistry: number;
  attack_defense: number;
}

export interface SetPieceInfo {
  penalty: string;
  corners: string[];
  free_kick: string;
}

export interface TeamProjection {
  win_pct: number;
  proj_goals: number;
  proj_assists?: number;
  exp_games?: number;
  group_stage_win_pct?: number;
  knockout_pct?: number;
  tier?: string;
}

export interface LineupEvalResponse {
  overall_score: number;
  dimensions: LineupEvalDimensions;
  highlights: string[];
  concerns: string[];
  set_pieces: SetPieceInfo | null;
  projection: TeamProjection | null;
}

// ── 实时比赛类型 (Live Match) ──────────────────

export interface LiveMatchSummary {
  match_id: string;
  name: string;
  date: string;
  date_bj?: string;
  state: 'live' | 'halftime' | 'finished' | 'scheduled';
  state_cn?: string;
  status_detail: string;
  period: number;
  clock: string;
  home_team: string;
  away_team: string;
  home_team_id?: string;
  away_team_id?: string;
  home_team_cn?: string;
  away_team_cn?: string;
  home_score: number;
  away_score: number;
  venue: string;
  broadcast?: string;
}

export interface LiveScoreboardResponse {
  live: LiveMatchSummary[];
  today: LiveMatchSummary[];
  live_count: number;
  total_today: number;
}

export interface LiveEvent {
  type: 'goal' | 'yellow_card' | 'red_card' | 'substitution' | 'kickoff' | 'halftime' | 'fulltime';
  type_cn?: string;
  minute: string;
  team: string;
  team_cn?: string;
  player: string;
  player_in: string;
  player_out: string;
  assist: string;
  text: string;
  description_cn?: string;
}

export interface LiveMatchDetail {
  match_id: string;
  date_bj?: string;
  status: {
    state: string;
    state_cn?: string;
    detail: string;
    period: number;
    clock: string;
    completed: boolean;
  };
  home: {
    name: string;
    name_cn?: string;
    abbrev: string;
    logo: string;
    score: number;
    team_id: string;
  };
  away: {
    name: string;
    name_cn?: string;
    abbrev: string;
    logo: string;
    score: number;
    team_id: string;
  };
  events: LiveEvent[];
  statistics: Record<string, {
    team_name: string;
    team_name_cn?: string;
    stats: Record<string, { label: string; label_cn?: string; value: string }>;
  }>;
}

// ── 比赛分析类型 (Match Analysis) ──────────────────

export interface MatchAnalysis {
  type: 'halftime' | 'fulltime' | 'live' | 'scheduled';
  summary: string;
  analysis: string;
  key_stats: string[];
  momentum: string;
  star_performers: string[];
}

export interface MatchAnalysisResponse {
  match_id: string;
  status: {
    state: string;
    state_cn?: string;
    detail: string;
    period: number;
    clock: string;
    completed: boolean;
  };
  home: {
    name: string;
    name_cn?: string;
    abbrev: string;
    logo: string;
    score: number;
    team_id: string;
  };
  away: {
    name: string;
    name_cn?: string;
    abbrev: string;
    logo: string;
    score: number;
    team_id: string;
  };
  events: LiveEvent[];
  statistics: Record<string, {
    team_name: string;
    team_name_cn?: string;
    stats: Record<string, { label: string; label_cn?: string; value: string }>;
  }>;
  analysis: MatchAnalysis;
  lineups?: MatchLineups;
}

// ── 阵容类型 (Roster) ──────────────────

export interface LineupPlayer {
  id: string;
  name: string;
  short_name: string;
  jersey: string;
  position: string;
  position_name: string;
  starter: boolean;
  formation_place: number;
  active: boolean;
}

export interface TeamLineup {
  formation: string;
  starters: LineupPlayer[];
  substitutes: LineupPlayer[];
}

export interface MatchLineups {
  home?: TeamLineup;
  away?: TeamLineup;
}

export interface RosterPlayer {
  id: string;
  name: string;
  short_name: string;
  jersey: string;
  position: string;
  position_name: string;
  headshot: string;
  height: string;
  weight: string;
  age: number;
}

export interface TeamRoster {
  team_id: string;
  team_name: string;
  team_name_cn: string;
  coach: string;
  players: {
    G: RosterPlayer[];
    D: RosterPlayer[];
    M: RosterPlayer[];
    F: RosterPlayer[];
    U: RosterPlayer[];
  };
  total_players: number;
  position_labels: Record<string, string>;
}

// ── 球员实时分析类型 (Player Live Analysis) ──────────────────

export interface PlayerLiveStat {
  label: string;
  value: string;
}

export interface IntervalAnalysis {
  interval_key: string;
  interval_label: string;
  generated: boolean;
  analysis: string;
}

export interface PlayerLiveAnalysisResponse {
  player_id: string;
  player_name: string;
  position: string;
  stats: Record<string, PlayerLiveStat>;
  stats_available: boolean;
  current_interval: string;
  clock: string;
  match_state: string;
  latest_analysis?: IntervalAnalysis;
  analyses: Record<string, IntervalAnalysis>;
}

export default api;
