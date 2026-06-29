import type { ApiPlayer } from '@/lib/api';

export interface Player {
  id: string;
  name: string;
  nameCn?: string;
  position: string;
  positionCn?: string;
  number: number;
  club?: string;
  avatar?: string;
  stats?: PlayerStats;
  attributes?: PlayerAttributes;
}

export interface PlayerStats {
  appearances: number;
  starts: number;
  minutes: number;
  goals: number;
  assists: number;
  yellowCards: number;
  redCards: number;
  rating: number;
  // fbref 扩展数据
  xg?: number;
  shotsTotal?: number;
  shotsOnTarget?: number;
  passAccuracy?: number;
  progressivePasses?: number;
  keyPasses?: number;
  tackles?: number;
  interceptions?: number;
  clearances?: number;
  blocks?: number;
  touches?: number;
  dribbleSuccessRate?: number;
  matchConfidence?: string | null;
  dataSource?: string;
  hasRealData?: boolean;
  // desktop-specific fields
  fouls?: number;
  fouled?: number;
  offsides?: number;
  crosses?: number;
  tacklesWon?: number;
  pkScored?: number;
  pkAttempted?: number;
  ownGoals?: number;
  shots?: number;
  shotAccuracy?: number;
  goalsP90?: number;
  assistsP90?: number;
  startRate?: number;
  shotConversion?: number;
  xgP90?: number;
  saves?: number;
  shotsOnTargetAgainst?: number;
  goalsConceded?: number;
  cleanSheets?: number;
  savePct?: number;
  penaltyGoalsAllowed?: number;
  penaltySaves?: number;
  wins?: number;
  draws?: number;
  losses?: number;
}

export interface PlayerAttributes {
  speed: number;
  shooting: number;
  passing: number;
  dribbling: number;
  defending: number;
  physical: number;
}

export interface Formation {
  id: string;
  name: string;
  positions: FormationPosition[];
}

export interface FormationPosition {
  x: number;
  y: number;
  position: string;
}

/** 将后端 API 球员数据转换为战术板 Player 类型 */
export function apiPlayerToPlayer(api: ApiPlayer): Player {
  const posCn = POSITION_CN_MAP[api.position] || api.position_display || api.position;

  let stats: PlayerStats | undefined;
  if (api.stats) {
    const s = api.stats;
    stats = {
      appearances: s.appearances ?? 0,
      starts: s.starts ?? 0,
      minutes: s.minutes ?? 0,
      goals: s.goals ?? 0,
      assists: s.assists ?? 0,
      yellowCards: s.yellow_cards ?? 0,
      redCards: s.red_cards ?? 0,
      rating: s.rating ?? 6.0,
      xg: s.xg,
      shotsTotal: s.shots_total ?? s.shots,
      shotsOnTarget: s.shots_on_target,
      passAccuracy: s.pass_accuracy,
      progressivePasses: s.progressive_passes,
      keyPasses: s.key_passes,
      tackles: s.tackles,
      interceptions: s.interceptions,
      clearances: s.clearances,
      blocks: s.blocks,
      touches: s.touches,
      dribbleSuccessRate: s.dribble_success_rate,
      matchConfidence: s.match_confidence,
      dataSource: s.data_source,
      hasRealData: s.has_real_data,
      fouls: s.fouls,
      fouled: s.fouled,
      offsides: s.offsides,
      crosses: s.crosses,
      tacklesWon: s.tackles_won,
      pkScored: s.pk_scored,
      pkAttempted: s.pk_attempted,
      ownGoals: s.own_goals,
      shots: s.shots ?? s.shots_total,
      shotAccuracy: s.shot_accuracy,
      goalsP90: s.goals_p90,
      assistsP90: s.assists_p90,
      xgP90: s.xg_p90,
      startRate: s.start_rate,
      shotConversion: s.shot_conversion,
      saves: s.saves,
      shotsOnTargetAgainst: s.shots_on_target_against,
      goalsConceded: s.goals_conceded,
      cleanSheets: s.clean_sheets,
      savePct: s.save_pct,
      penaltyGoalsAllowed: s.penalty_goals_allowed,
      penaltySaves: s.penalty_saves,
      wins: s.wins,
      draws: s.draws,
      losses: s.losses,
    };
  }

  let attributes: PlayerAttributes | undefined;
  if (api.stats?._attributes) {
    attributes = api.stats._attributes;
  } else if (api.stats) {
    attributes = deriveAttributes(api.stats);
  }

  return {
    id: api.id,
    name: api.name,
    nameCn: api.name_cn,
    position: api.position,
    positionCn: posCn,
    number: api.number || 0,
    club: api.club,
    avatar: api.avatar,
    stats,
    attributes,
  };
}

/** 从 fbref 赛季数据推导球员能力属性 (0-100) */
function deriveAttributes(s: ApiPlayer['stats']): PlayerAttributes {
  if (!s) {
    return { speed: 70, shooting: 70, passing: 70, dribbling: 70, defending: 70, physical: 70 };
  }

  const apps = Math.max(s.appearances ?? 1, 1);

  // 射门: 基于进球率 + xG
  const goalRate = Math.min((s.goals ?? 0) / apps * 10, 1);
  const shooting = Math.round(55 + goalRate * 35);

  // 传球: 基于传球成功率
  const passAcc = s.pass_accuracy ?? 75;
  const passing = Math.round(Math.min(Math.max(passAcc, 60), 95));

  // 盘带: 基于过人成功率
  const dribbleRate = s.dribble_success_rate ?? 55;
  const dribbling = Math.round(Math.min(Math.max(dribbleRate, 50), 95));

  // 防守: 基于抢断+拦截
  const defPerGame = ((s.tackles ?? 0) + (s.interceptions ?? 0)) / apps;
  const defending = Math.round(50 + Math.min(defPerGame / 5, 1) * 40);

  // 身体: 基于出场时间稳定性
  const minsPerApp = (s.minutes ?? 0) / apps;
  const physical = Math.round(60 + Math.min(minsPerApp / 90, 1) * 30);

  // 速度: 基于位置 + 盘带综合推算
  const speed = Math.round(60 + Math.min(((s.progressive_passes ?? 0) / apps / 10), 1) * 30);

  return { speed, shooting, passing, dribbling, defending, physical };
}

const POSITION_CN_MAP: Record<string, string> = {
  GK: '门将',
  CB: '中后卫',
  LB: '左后卫',
  RB: '右后卫',
  LWB: '左边翼卫',
  RWB: '右边翼卫',
  CDM: '后腰',
  CM: '中前卫',
  CAM: '前腰',
  LM: '左边锋',
  RM: '右边锋',
  LW: '左边锋',
  RW: '右边锋',
  ST: '中锋',
};

export const FORMATIONS: Record<string, Formation> = {
  '4-4-2': {
    id: '4-4-2',
    name: '4-4-2',
    positions: [
      { x: 50, y: 92, position: 'GK' },
      { x: 15, y: 72, position: 'LB' },
      { x: 38, y: 72, position: 'CB' },
      { x: 62, y: 72, position: 'CB' },
      { x: 85, y: 72, position: 'RB' },
      { x: 15, y: 50, position: 'LM' },
      { x: 38, y: 50, position: 'CM' },
      { x: 62, y: 50, position: 'CM' },
      { x: 85, y: 50, position: 'RM' },
      { x: 35, y: 22, position: 'ST' },
      { x: 65, y: 22, position: 'ST' },
    ],
  },
  '4-3-3': {
    id: '4-3-3',
    name: '4-3-3',
    positions: [
      { x: 50, y: 92, position: 'GK' },
      { x: 15, y: 72, position: 'LB' },
      { x: 38, y: 72, position: 'CB' },
      { x: 62, y: 72, position: 'CB' },
      { x: 85, y: 72, position: 'RB' },
      { x: 20, y: 50, position: 'CM' },
      { x: 50, y: 50, position: 'CM' },
      { x: 80, y: 50, position: 'CM' },
      { x: 15, y: 22, position: 'LW' },
      { x: 50, y: 22, position: 'ST' },
      { x: 85, y: 22, position: 'RW' },
    ],
  },
  '3-5-2': {
    id: '3-5-2',
    name: '3-5-2',
    positions: [
      { x: 50, y: 92, position: 'GK' },
      { x: 20, y: 72, position: 'CB' },
      { x: 50, y: 72, position: 'CB' },
      { x: 80, y: 72, position: 'CB' },
      { x: 10, y: 50, position: 'LWB' },
      { x: 30, y: 50, position: 'CM' },
      { x: 50, y: 50, position: 'CM' },
      { x: 70, y: 50, position: 'CM' },
      { x: 90, y: 50, position: 'RWB' },
      { x: 35, y: 22, position: 'ST' },
      { x: 65, y: 22, position: 'ST' },
    ],
  },
  '4-2-3-1': {
    id: '4-2-3-1',
    name: '4-2-3-1',
    positions: [
      { x: 50, y: 92, position: 'GK' },
      { x: 15, y: 72, position: 'LB' },
      { x: 38, y: 72, position: 'CB' },
      { x: 62, y: 72, position: 'CB' },
      { x: 85, y: 72, position: 'RB' },
      { x: 30, y: 50, position: 'CDM' },
      { x: 70, y: 50, position: 'CDM' },
      { x: 15, y: 30, position: 'LW' },
      { x: 50, y: 30, position: 'CAM' },
      { x: 85, y: 30, position: 'RW' },
      { x: 50, y: 12, position: 'ST' },
    ],
  },
};

export const MOCK_SQUAD: Player[] = [
  { id: '1', name: 'Alisson', nameCn: '阿利森', position: 'GK', number: 1 },
  { id: '2', name: 'Alexander-Arnold', nameCn: '阿诺德', position: 'RB', number: 66 },
  { id: '3', name: 'Van Dijk', nameCn: '范戴克', position: 'CB', number: 4 },
  { id: '4', name: 'Konate', nameCn: '科纳特', position: 'CB', number: 5 },
  { id: '5', name: 'Robertson', nameCn: '罗伯逊', position: 'LB', number: 26 },
  { id: '6', name: 'Mac Allister', nameCn: '麦卡利斯特', position: 'CM', number: 10 },
  { id: '7', name: 'Szoboszlai', nameCn: '索博斯洛伊', position: 'CM', number: 8 },
  { id: '8', name: 'Gravenberch', nameCn: '格拉文贝赫', position: 'CM', number: 38 },
  { id: '9', name: 'Salah', nameCn: '萨拉赫', position: 'RW', number: 11 },
  { id: '10', name: 'Nunez', nameCn: '努涅斯', position: 'ST', number: 9 },
  { id: '11', name: 'Diaz', nameCn: '迪亚斯', position: 'LW', number: 7 },
  { id: '12', name: 'Kelleher', nameCn: '凯莱赫', position: 'GK', number: 62 },
  { id: '13', name: 'Gomez', nameCn: '戈麦斯', position: 'RB', number: 2 },
  { id: '14', name: 'Quansah', nameCn: '宽萨', position: 'CB', number: 78 },
  { id: '15', name: 'Simons', nameCn: '西蒙斯', position: 'CAM', number: 18 },
  { id: '16', name: 'Elliott', nameCn: '埃利奥特', position: 'CM', number: 19 },
  { id: '17', name: 'Gakpo', nameCn: '加克波', position: 'LW', number: 27 },
  { id: '18', name: 'Jota', nameCn: '若塔', position: 'ST', number: 20 },
];
