'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import api, { RosterPlayer, MatchLineups, TeamLineup, LineupPlayer, LiveEvent, PlayerLiveAnalysisResponse, IntervalAnalysis } from '@/lib/api';

type Formation = '4-4-2' | '4-3-3' | '3-5-2' | '4-2-3-1' | '5-4-1' | '3-4-3';
type Side = 'home' | 'away';

interface PitchSlot {
  player: RosterPlayer | LineupPlayer;
  x: number;
  y: number;
  subStatus?: 'in' | 'out';
}

const HOME_COLOR = '#10b981';
const AWAY_COLOR = '#818cf8';
const BENCH_COLOR = '#475569';
const CARD_BG = 'var(--card-bg)';
const CARD_BORDER = 'var(--card-border)';
const TEXT_MUTED = 'var(--text-muted)';

function linePositions(count: number, x: number, yMin: number, yMax: number): { x: number; y: number }[] {
  if (count <= 1) return [{ x, y: (yMin + yMax) / 2 }];
  return Array.from({ length: count }, (_, i) => ({
    x,
    y: yMin + (i / (count - 1)) * (yMax - yMin),
  }));
}

function splitMidfield(players: (RosterPlayer | LineupPlayer)[], formation: Formation): (RosterPlayer | LineupPlayer)[][] {
  if (formation === '4-2-3-1') {
    return [players.slice(0, 2), players.slice(2, 5)];
  }
  if (formation === '3-5-2') {
    return [players.slice(0, 3), players.slice(3, 5)];
  }
  return [players];
}

/** Map ESPN detailed position codes to G/D/M/F groups */
function getPositionGroup(pos: string): string {
  const base = pos.split('-')[0]; // "CF-L" → "CF", "CM-R" → "CM"
  const gk = new Set(['G', 'GK']);
  const def = new Set(['D', 'DF', 'CD', 'CB', 'RB', 'LB', 'RWB', 'LWB', 'SW']);
  const mid = new Set(['M', 'MF', 'CM', 'CDM', 'CAM', 'DM', 'AM', 'RM', 'LM']);
  const fwd = new Set(['F', 'FW', 'CF', 'ST', 'LW', 'RW', 'RF', 'LF']);
  if (gk.has(base)) return 'G';
  if (def.has(base)) return 'D';
  if (mid.has(base)) return 'M';
  if (fwd.has(base)) return 'F';
  return 'U';
}

function displayName(player: RosterPlayer | LineupPlayer): string {
  return player.short_name || player.name || '未知球员';
}

/** Normalize a name for comparison: lowercase, remove diacritics and special chars */
function nameKey(s: string): string {
  return s.toLowerCase()
    .normalize('NFKD').replace(/[̀-ͯ]/g, '') // strip diacritics
    .replace(/[^a-z]/g, '');
}

/** Fuzzy-match an event player name to a lineup player */
function findPlayerByName(eventName: string, players: LineupPlayer[]): LineupPlayer | null {
  if (!eventName || players.length === 0) return null;
  const target = nameKey(eventName);
  if (!target) return null;

  // Exact normalized match
  for (const p of players) {
    if (nameKey(p.name) === target || nameKey(p.short_name) === target) return p;
  }

  // Last-name match (for name variations across ESPN sources)
  const parts = target.match(/[a-z]+/g) || [];
  const lastName = parts.length > 0 ? parts[parts.length - 1] : '';
  if (lastName.length >= 4) {
    for (const p of players) {
      const pk = nameKey(p.name);
      if (pk.includes(lastName) || lastName.includes(pk)) return p;
    }
  }

  // First-name initial + last-name match
  if (parts.length >= 2 && parts[0] && parts[0].length >= 2) {
    const firstInit = parts[0].substring(0, 2);
    for (const p of players) {
      const pk = nameKey(p.name);
      if (pk.startsWith(firstInit) && pk.includes(lastName)) return p;
    }
  }

  return null;
}

/** Process substitution events: returns subbed-off IDs, subbed-on IDs, and replacement mapping */
function processSubstitutions(
  events: LiveEvent[] | undefined,
  homeLineup: TeamLineup | undefined,
  awayLineup: TeamLineup | undefined,
): {
  homeSubbedOut: Set<string>;
  homeSubbedIn: Set<string>;
  awaySubbedOut: Set<string>;
  awaySubbedIn: Set<string>;
  homeReplacements: Map<string, LineupPlayer>;  // subbedOut id → replacement player
  awayReplacements: Map<string, LineupPlayer>;
} {
  const homeSubbedOut = new Set<string>();
  const homeSubbedIn = new Set<string>();
  const awaySubbedOut = new Set<string>();
  const awaySubbedIn = new Set<string>();
  const homeReplacements = new Map<string, LineupPlayer>();
  const awayReplacements = new Map<string, LineupPlayer>();

  if (!events || !homeLineup || !awayLineup) {
    return { homeSubbedOut, homeSubbedIn, awaySubbedOut, awaySubbedIn, homeReplacements, awayReplacements };
  }

  const allHome = [...homeLineup.starters, ...homeLineup.substitutes];
  const allAway = [...awayLineup.starters, ...awayLineup.substitutes];

  for (const ev of events) {
    if (ev.type !== 'substitution') continue;

    // Determine side from the player being substituted off first, then match
    // the incoming player only within that same team. This avoids cross-team
    // name collisions when two players have similar names.
    const homePlayerOut = findPlayerByName(ev.player_out, allHome);
    const awayPlayerOut = findPlayerByName(ev.player_out, allAway);
    const outInHome = !!homePlayerOut && !awayPlayerOut;
    const outInAway = !!awayPlayerOut && !homePlayerOut;

    if (outInHome) {
      const playerOut = homePlayerOut;
      const playerIn = findPlayerByName(ev.player_in, homeLineup.substitutes);
      if (!playerOut || !playerIn) continue;
      homeSubbedOut.add(playerOut.id);
      homeSubbedIn.add(playerIn.id);
      homeReplacements.set(playerOut.id, playerIn);
    } else if (outInAway) {
      const playerOut = awayPlayerOut;
      const playerIn = findPlayerByName(ev.player_in, awayLineup.substitutes);
      if (!playerOut || !playerIn) continue;
      awaySubbedOut.add(playerOut.id);
      awaySubbedIn.add(playerIn.id);
      awayReplacements.set(playerOut.id, playerIn);
    }
  }

  return { homeSubbedOut, homeSubbedIn, awaySubbedOut, awaySubbedIn, homeReplacements, awayReplacements };
}

function appendSubbedOutPlayers(
  substitutes: LineupPlayer[],
  starters: LineupPlayer[],
  subbedOut: Set<string>,
): LineupPlayer[] {
  const subbedOutPlayers = starters.filter(player => subbedOut.has(player.id));
  if (subbedOutPlayers.length === 0) return substitutes;

  const seen = new Set<string>();
  return [...subbedOutPlayers, ...substitutes].filter((player) => {
    if (seen.has(player.id)) return false;
    seen.add(player.id);
    return true;
  });
}

function buildSlotsFromLineup(
  starters: LineupPlayer[],
  formation: Formation,
  side: Side,
  replacements: Map<string, LineupPlayer> = new Map(),
  subbedIn: Set<string> = new Set(),
): PitchSlot[] {
  // Apply substitutions: replace subbed-out players with subbed-in players.
  // ESPN sets substitute positions to "SUB" — inherit original starter's position for grouping.
  const activeStarters = starters.map((starter) => {
    const replacement = replacements.get(starter.id);
    if (!replacement) return starter;
    if (getPositionGroup(replacement.position) === 'U') {
      return { ...replacement, position: starter.position };
    }
    return replacement;
  });

  const gk = activeStarters.filter(p => getPositionGroup(p.position) === 'G');
  const def = activeStarters.filter(p => getPositionGroup(p.position) === 'D');
  const mid = activeStarters.filter(p => getPositionGroup(p.position) === 'M');
  const fwd = activeStarters.filter(p => getPositionGroup(p.position) === 'F');
  const isHome = side === 'home';
  const mirror = (x: number) => (isHome ? x : 100 - x);

  const slots: PitchSlot[] = [];
  gk.slice(0, 1).forEach(player => slots.push({
    player,
    x: mirror(5.5), y: 50,
    subStatus: subbedIn.has(player.id) ? 'in' : undefined,
  }));

  linePositions(def.length, mirror(18.5), 17, 83).forEach((pos, i) => {
    if (def[i]) slots.push({
      player: def[i], ...pos,
      subStatus: subbedIn.has(def[i].id) ? 'in' : undefined,
    });
  });

  const midfieldLines = splitMidfield(mid, formation);
  const midfieldXs =
    midfieldLines.length === 1
      ? [29.5]
      : formation === '4-2-3-1'
        ? [28, 38]
        : [28, 38];

  midfieldLines.forEach((line, lineIndex) => {
    linePositions(line.length, mirror(midfieldXs[lineIndex]), 20, 80).forEach((pos, i) => {
      if (line[i]) slots.push({
        player: line[i], ...pos,
        subStatus: subbedIn.has(line[i].id) ? 'in' : undefined,
      });
    });
  });

  linePositions(fwd.length, mirror(45), fwd.length === 1 ? 48 : 24, fwd.length === 1 ? 52 : 76).forEach((pos, i) => {
    if (fwd[i]) slots.push({
      player: fwd[i], ...pos,
      subStatus: subbedIn.has(fwd[i].id) ? 'in' : undefined,
    });
  });

  return slots;
}

function ShirtMarker({ color, number, size = 46 }: { color: string; number?: string; size?: number }) {
  return (
    <div
      style={{
        width: size,
        height: size * 0.9,
        position: 'relative',
        color: '#fff',
        fontSize: size * 0.46,
        fontWeight: 800,
        lineHeight: `${size * 0.9}px`,
        textAlign: 'center',
        textShadow: '0 1px 1px rgba(0,0,0,0.35)',
        filter: 'drop-shadow(0 1px 1px rgba(0,0,0,0.3))',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: color,
          border: '2px solid rgba(240,240,240,0.92)',
          boxShadow: 'inset 0 -8px 14px rgba(0,0,0,0.18), inset 0 8px 12px rgba(255,255,255,0.12)',
          clipPath:
            'polygon(20% 0%, 35% 0%, 42% 10%, 58% 10%, 65% 0%, 80% 0%, 100% 25%, 88% 43%, 78% 36%, 78% 100%, 22% 100%, 22% 36%, 12% 43%, 0% 25%)',
        }}
      />
      <span style={{ position: 'relative', zIndex: 1 }}>{number || '?'}</span>
    </div>
  );
}

function PitchPlayer({ player, x, y, color, onClick, isSelected, subStatus }: {
  player: RosterPlayer | LineupPlayer;
  x: number; y: number;
  color: string;
  onClick?: () => void;
  isSelected?: boolean;
  subStatus?: 'in' | 'out';
}) {
  return (
    <div
      onClick={onClick}
      style={{
        position: 'absolute',
        left: `${x}%`,
        top: `${y}%`,
        transform: 'translate(-50%, -50%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        minWidth: 82,
        zIndex: isSelected ? 20 : 3,
        cursor: 'pointer',
        pointerEvents: 'auto',
        transition: 'transform 0.15s, filter 0.15s',
        filter: isSelected ? 'drop-shadow(0 0 8px rgba(255,255,255,0.7)) brightness(1.2)' : undefined,
        opacity: subStatus === 'out' ? 0.55 : 1,
      }}
      title={`${player.jersey || '?'} ${displayName(player)}${subStatus === 'in' ? ' (替补登场)' : subStatus === 'out' ? ' (被换下)' : ''}`}
    >
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 4 }}>
        <ShirtMarker color={color} number={player.jersey} />
        {subStatus && (
          <span style={{
            fontSize: 18,
            fontWeight: 900,
            color: subStatus === 'in' ? '#10b981' : '#ef4444',
            filter: `drop-shadow(0 0 3px ${subStatus === 'in' ? '#10b981' : '#ef4444'})`,
            lineHeight: 1,
          }}>
            {subStatus === 'in' ? '▲' : '▼'}
          </span>
        )}
      </div>
      <div
        style={{
          maxWidth: 92,
          marginTop: 3,
          color: '#fff',
          fontSize: 15,
          fontWeight: 800,
          lineHeight: 1.08,
          textAlign: 'center',
          textShadow: '0 1px 2px rgba(0,0,0,0.9)',
          wordBreak: 'keep-all',
          overflowWrap: 'anywhere',
        }}
      >
        {displayName(player)}
      </div>
    </div>
  );
}

function SubItem({ player, subStatus }: { player: RosterPlayer | LineupPlayer; subStatus?: 'in' | 'out' }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 7,
        minWidth: 0,
        padding: '3px 0',
        opacity: subStatus === 'in' ? 0.55 : 1,
      }}
      title={subStatus === 'in' ? '已替补登场' : subStatus === 'out' ? '已被换下' : undefined}
    >
      <ShirtMarker
        color={subStatus === 'in' ? '#10b981' : subStatus === 'out' ? '#ef4444' : BENCH_COLOR}
        number={player.jersey}
        size={31}
      />
      {subStatus && (
        <span
          aria-label={subStatus === 'out' ? '已被换下' : '已替补登场'}
          style={{
            flex: '0 0 auto',
            color: subStatus === 'out' ? '#ef4444' : '#10b981',
            fontSize: 16,
            fontWeight: 900,
            lineHeight: 1,
          }}
        >
          {subStatus === 'out' ? '▼' : '▲'}
        </span>
      )}
      <span
        style={{
          minWidth: 0,
          color: subStatus === 'in' ? '#10b981' : subStatus === 'out' ? '#ef4444' : 'var(--foreground)',
          fontSize: 16,
          lineHeight: 1.25,
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}
        title={displayName(player)}
      >
        {displayName(player)}
        {subStatus === 'in' && <span style={{ marginLeft: 3, fontSize: 11 }}>▲</span>}
        {subStatus === 'out' && <span style={{ marginLeft: 3, fontSize: 11 }}>▼</span>}
      </span>
    </div>
  );
}

const INTERVAL_TABS = [
  { key: 'p1', label: '25\'' },
  { key: 'p2', label: '中场' },
  { key: 'p3', label: '65\'' },
  { key: 'p4', label: '终场' },
];

interface SelectedPlayerInfo {
  player: RosterPlayer | LineupPlayer;
  x: number;
  y: number;
  side: 'home' | 'away';
  teamId: string;
}

function PlayerPopover({
  info,
  analysis,
  loading,
  onClose,
}: {
  info: SelectedPlayerInfo;
  analysis: PlayerLiveAnalysisResponse | null;
  loading: boolean;
  onClose: () => void;
}) {
  const [activeTab, setActiveTab] = useState('p1');
  const popoverRef = useRef<HTMLDivElement>(null);

  // Auto-select current interval tab when analysis loads
  useEffect(() => {
    if (analysis?.current_interval) {
      setActiveTab(analysis.current_interval);
    }
  }, [analysis?.current_interval]);

  // Close on click outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    // Delay to avoid immediate close from the same click
    const timer = setTimeout(() => document.addEventListener('click', handleClick), 100);
    return () => { clearTimeout(timer); document.removeEventListener('click', handleClick); };
  }, [onClose]);

  const player = info.player;
  const color = info.side === 'home' ? HOME_COLOR : AWAY_COLOR;
  const hasStats = analysis?.stats_available && Object.keys(analysis?.stats || {}).length > 0;
  const currentAnalyses = analysis?.analyses || {};
  const activeData: IntervalAnalysis | undefined = currentAnalyses[activeTab];

  return (
    <div
      ref={popoverRef}
      onClick={(e) => e.stopPropagation()}
      style={{
        position: 'absolute',
        left: `${info.x}%`,
        top: `${info.y > 50 ? info.y - 18 : info.y + 14}%`,
        transform: info.x > 70 ? 'translate(-95%, -50%)' : info.x < 30 ? 'translate(-5%, -50%)' : 'translate(-50%, -50%)',
        width: 280,
        maxHeight: 420,
        overflowY: 'auto',
        background: 'rgba(15,23,42,0.97)',
        border: `1px solid ${color}`,
        borderRadius: '0.75rem',
        boxShadow: `0 8px 32px rgba(0,0,0,0.5), 0 0 16px ${color}33`,
        zIndex: 30,
        padding: '0.8rem',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.6rem' }}>
        <ShirtMarker color={color} number={player.jersey} size={34} />
        <div style={{ minWidth: 0 }}>
          <div style={{ color: '#fff', fontSize: 14, fontWeight: 700, lineHeight: 1.2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {displayName(player)}
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: 11 }}>
            #{player.jersey} · {analysis?.position || player.position || ''}
          </div>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onClose(); }}
          style={{
            marginLeft: 'auto', width: 22, height: 22,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            border: '1px solid rgba(255,255,255,0.15)', borderRadius: '0.3rem',
            background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)',
            fontSize: 12, cursor: 'pointer', flexShrink: 0,
          }}
        >
          ✕
        </button>
      </div>

      {/* Stats grid */}
      {hasStats ? (
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
          gap: '0.3rem', marginBottom: '0.6rem',
        }}>
          {Object.entries(analysis!.stats).slice(0, 12).map(([key, stat]) => (
            <div key={key} style={{
              background: 'rgba(255,255,255,0.04)',
              borderRadius: '0.3rem',
              padding: '0.25rem 0.35rem',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', lineHeight: 1.1 }}>
                {stat.value || '0'}
              </div>
              <div style={{ fontSize: 9, color: 'var(--text-muted)', lineHeight: 1.2 }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      ) : loading ? (
        <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--text-muted)', fontSize: 12 }}>
          ⏳ 正在获取球员数据…
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '0.6rem', color: 'var(--text-muted)', fontSize: 11, marginBottom: '0.4rem' }}>
          暂无实时个人数据
        </div>
      )}

      {/* AI Analysis tabs */}
      <div style={{
        borderTop: '1px solid rgba(255,255,255,0.08)',
        paddingTop: '0.6rem',
      }}>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: '0.4rem', fontWeight: 600 }}>
          🤖 AI 表现分析
        </div>

        {/* Tab buttons */}
        <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '0.5rem' }}>
          {INTERVAL_TABS.map(tab => {
            const data = currentAnalyses[tab.key];
            const isCurrent = analysis?.current_interval === tab.key;
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  flex: 1,
                  padding: '0.25rem 0.2rem',
                  borderRadius: '0.3rem',
                  border: isActive
                    ? `1px solid ${isCurrent ? '#f59e0b' : color}`
                    : '1px solid rgba(255,255,255,0.08)',
                  background: isActive
                    ? `rgba(${isCurrent ? '245,158,11' : color === HOME_COLOR ? '16,185,129' : '129,140,248'}, 0.12)`
                    : 'transparent',
                  color: isActive ? '#fff' : 'var(--text-muted)',
                  fontSize: 10,
                  fontWeight: isActive ? 700 : 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  position: 'relative' as const,
                }}
              >
                {tab.label}
                {isCurrent && (
                  <span style={{
                    position: 'absolute', top: -4, right: -4,
                    width: 7, height: 7,
                    borderRadius: '50%', background: '#f59e0b',
                  }} />
                )}
              </button>
            );
          })}
        </div>

        {/* Analysis text */}
        <div style={{
          fontSize: 11,
          color: '#cbd5e1',
          lineHeight: 1.7,
          minHeight: '3rem',
          maxHeight: '10rem',
          overflowY: 'auto',
        }}>
          {loading && !analysis ? (
            <span style={{ color: 'var(--text-muted)' }}>AI 分析生成中…</span>
          ) : !activeData?.generated ? (
            <span style={{ color: 'var(--text-muted)' }}>该时段分析尚未生成</span>
          ) : (
            activeData.analysis
          )}
        </div>
      </div>
    </div>
  );
}

interface Props {
  homeTeamId: string;
  awayTeamId: string;
  homeName: string;
  awayName: string;
  homeNameCn: string;
  awayNameCn: string;
  lineups?: MatchLineups | null;
  matchId?: string;
  events?: LiveEvent[];
}

export default function FormationView({ homeTeamId, awayTeamId, homeName, awayName, homeNameCn, awayNameCn, lineups, matchId, events }: Props) {
  // Use real ESPN lineups if available
  const homeLineup: TeamLineup | undefined = lineups?.home;
  const awayLineup: TeamLineup | undefined = lineups?.away;
  const hasRealLineups = !!(homeLineup?.starters?.length && awayLineup?.starters?.length);
  const [loading, setLoading] = useState(!hasRealLineups);
  const [homeFormation, setHomeFormation] = useState<Formation>('5-4-1');
  const [awayFormation, setAwayFormation] = useState<Formation>('4-2-3-1');

  // Player popover state
  const [selectedPlayer, setSelectedPlayer] = useState<SelectedPlayerInfo | null>(null);
  const [playerAnalysis, setPlayerAnalysis] = useState<PlayerLiveAnalysisResponse | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  // Fetch player analysis when a player is selected
  useEffect(() => {
    if (!selectedPlayer || !matchId) return;
    setAnalysisLoading(true);
    setPlayerAnalysis(null);
    let mounted = true;

    const teamId = selectedPlayer.side === 'home' ? homeTeamId : awayTeamId;
    const name = (selectedPlayer.player as LineupPlayer).name || (selectedPlayer.player as RosterPlayer).name || '';
    const pos = selectedPlayer.player.position || '';

    api.getPlayerLiveAnalysis(matchId, selectedPlayer.player.id, {
      team_id: teamId,
      player_name: name,
      position: pos,
    }).then(data => {
      if (mounted) { setPlayerAnalysis(data); setAnalysisLoading(false); }
    }).catch(() => {
      if (mounted) setAnalysisLoading(false);
    });

    return () => { mounted = false; };
  }, [selectedPlayer, matchId, homeTeamId, awayTeamId]);

  // Show the formation only after ESPN publishes real starters for both teams.
  // Do not guess a starting XI from team rosters before official lineups exist.
  useEffect(() => {
    setLoading(false);
  }, [hasRealLineups]);

  // Sync formation state from real lineups (must be in effect, not during render)
  useEffect(() => {
    if (!hasRealLineups || !homeLineup || !awayLineup) return;
    const hForm = (homeLineup.formation || '4-4-2') as Formation;
    const aForm = (awayLineup.formation || '4-3-3') as Formation;
    const validFormations: Formation[] = ['4-4-2', '4-3-3', '3-5-2', '4-2-3-1', '5-4-1', '3-4-3'];
    setHomeFormation(validFormations.includes(hForm) ? hForm : '4-4-2');
    setAwayFormation(validFormations.includes(aForm) ? aForm : '4-3-3');
  }, [hasRealLineups, homeLineup?.formation, awayLineup?.formation]);

  // Process substitution events
  const subs = useMemo(() => processSubstitutions(events, homeLineup, awayLineup), [events, homeLineup, awayLineup]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: TEXT_MUTED, fontSize: 14, background: CARD_BG, border: `1px solid ${CARD_BORDER}`, borderRadius: '1rem' }}>
        加载阵容数据中...
      </div>
    );
  }

  if (!hasRealLineups || !homeLineup || !awayLineup) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '2rem',
        color: TEXT_MUTED,
        fontSize: 14,
        background: CARD_BG,
        border: `1px solid ${CARD_BORDER}`,
        borderRadius: '1rem',
        marginTop: '1.25rem',
      }}>
        阵容尚未公布
      </div>
    );
  }

  // Build slots from real ESPN lineups.
  let homeSlots: PitchSlot[];
  let awaySlots: PitchSlot[];
  let homeBench: RosterPlayer[] | LineupPlayer[];
  let awayBench: RosterPlayer[] | LineupPlayer[];
  let displayHomeFormation: Formation;
  let displayAwayFormation: Formation;
  let resolvedHomeName: string;
  let resolvedAwayName: string;
  let homeCoach: string;
  let awayCoach: string;

  const hForm = (homeLineup.formation || '4-4-2') as Formation;
  const aForm = (awayLineup.formation || '4-3-3') as Formation;
  displayHomeFormation = ['4-4-2','4-3-3','3-5-2','4-2-3-1','5-4-1','3-4-3'].includes(hForm) ? hForm : '4-4-2';
  displayAwayFormation = ['4-4-2','4-3-3','3-5-2','4-2-3-1','5-4-1','3-4-3'].includes(aForm) ? aForm : '4-3-3';

  homeSlots = buildSlotsFromLineup(homeLineup.starters, displayHomeFormation, 'home', subs.homeReplacements, subs.homeSubbedIn);
  awaySlots = buildSlotsFromLineup(awayLineup.starters, displayAwayFormation, 'away', subs.awayReplacements, subs.awaySubbedIn);
  homeBench = appendSubbedOutPlayers(homeLineup.substitutes, homeLineup.starters, subs.homeSubbedOut);
  awayBench = appendSubbedOutPlayers(awayLineup.substitutes, awayLineup.starters, subs.awaySubbedOut);
  resolvedHomeName = homeNameCn || homeName;
  resolvedAwayName = awayNameCn || awayName;
  homeCoach = '';
  awayCoach = '';

  return (
    <div
      className="responsive-formation"
      style={{
        background: CARD_BG,
        border: `1px solid ${CARD_BORDER}`,
        borderRadius: '1rem',
        marginTop: '1.25rem',
        overflow: 'hidden',
        boxShadow: '0 18px 45px rgba(0,0,0,0.26)',
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr',
          alignItems: 'center',
          minHeight: 43,
          background: 'linear-gradient(135deg, rgba(16,185,129,0.24), rgba(129,140,248,0.22))',
          color: '#fff',
          fontSize: 22,
          fontWeight: 800,
          textAlign: 'center',
          borderBottom: `1px solid ${CARD_BORDER}`,
          textShadow: '0 1px 1px rgba(0,0,0,0.35)',
        }}
      >
        <div>{resolvedHomeName}</div>
        <div>首发阵型</div>
        <div>{resolvedAwayName}</div>
      </div>

      <div
        className="responsive-pitch"
        style={{
          position: 'relative',
          width: '100%',
          aspectRatio: '1.58 / 1',
          minHeight: 430,
          overflow: 'hidden',
          backgroundColor: '#075f34',
          backgroundImage:
            'radial-gradient(circle at 35% 35%, rgba(251,191,36,0.08), transparent 24%), radial-gradient(circle at 72% 42%, rgba(129,140,248,0.08), transparent 26%), repeating-linear-gradient(0deg, rgba(255,255,255,0.035) 0 2px, rgba(0,0,0,0.04) 2px 5px), repeating-linear-gradient(90deg, rgba(16,185,129,0.13) 0 56px, rgba(6,95,70,0.28) 56px 112px)',
          boxShadow: 'inset 0 0 70px rgba(0,0,0,0.36)',
        }}
      >
        <div style={{ position: 'absolute', inset: 8, border: '2px solid rgba(236,253,245,0.5)' }} />
        <div style={{ position: 'absolute', left: '50%', top: 8, bottom: 8, borderLeft: '2px solid rgba(236,253,245,0.5)' }} />
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            width: '18%',
            aspectRatio: '1 / 1',
            transform: 'translate(-50%, -50%)',
            border: '2px solid rgba(236,253,245,0.5)',
            borderRadius: '50%',
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            width: 7,
            height: 7,
            transform: 'translate(-50%, -50%)',
            borderRadius: '50%',
            background: 'rgba(236,253,245,0.72)',
          }}
        />

        <div style={{ position: 'absolute', left: 8, top: '29%', width: '9%', height: '42%', border: '2px solid rgba(236,253,245,0.38)', borderLeft: 0 }} />
        <div style={{ position: 'absolute', right: 8, top: '29%', width: '9%', height: '42%', border: '2px solid rgba(236,253,245,0.38)', borderRight: 0 }} />
        <div style={{ position: 'absolute', left: 8, top: '39%', width: '18%', height: '22%', border: '2px solid rgba(236,253,245,0.38)', borderLeft: 0 }} />
        <div style={{ position: 'absolute', right: 8, top: '39%', width: '18%', height: '22%', border: '2px solid rgba(236,253,245,0.38)', borderRight: 0 }} />
        <div
          style={{
            position: 'absolute',
            left: '18%',
            top: '50%',
            width: '14%',
            aspectRatio: '1 / 1',
            transform: 'translate(-50%, -50%)',
            border: '2px solid rgba(236,253,245,0.3)',
            borderRadius: '50%',
          }}
        />
        <div
          style={{
            position: 'absolute',
            right: '18%',
            top: '50%',
            width: '14%',
            aspectRatio: '1 / 1',
            transform: 'translate(50%, -50%)',
            border: '2px solid rgba(236,253,245,0.3)',
            borderRadius: '50%',
          }}
        />
        <div style={{ position: 'absolute', left: 8, top: '29%', width: '18%', height: '42%', background: '#075f34' }} />
        <div style={{ position: 'absolute', right: 8, top: '29%', width: '18%', height: '42%', background: '#075f34' }} />
        <div style={{ position: 'absolute', left: 8, top: '39%', width: '18%', height: '22%', border: '2px solid rgba(236,253,245,0.38)', borderLeft: 0, zIndex: 1 }} />
        <div style={{ position: 'absolute', right: 8, top: '39%', width: '18%', height: '22%', border: '2px solid rgba(236,253,245,0.38)', borderRight: 0, zIndex: 1 }} />

        <div style={{ position: 'absolute', left: 16, top: 13, color: '#fff', fontSize: 18, fontWeight: 700, lineHeight: 1.25, textShadow: '0 1px 2px #000', zIndex: 4 }}>
          <div>{resolvedHomeName}</div>
          <div>{displayHomeFormation}</div>
        </div>
        <div style={{ position: 'absolute', right: 16, top: 13, color: '#fff', fontSize: 18, fontWeight: 700, lineHeight: 1.25, textAlign: 'right', textShadow: '0 1px 2px #000', zIndex: 4 }}>
          <div>{resolvedAwayName}</div>
          <div>{displayAwayFormation}</div>
        </div>

        {homeSlots.map(({ player, x, y, subStatus }) => (
          <PitchPlayer
            key={player.id}
            player={player}
            x={x} y={y}
            color={HOME_COLOR}
            subStatus={subStatus}
            isSelected={selectedPlayer?.player.id === player.id && selectedPlayer?.side === 'home'}
            onClick={() => {
              if (selectedPlayer?.player.id === player.id && selectedPlayer?.side === 'home') {
                setSelectedPlayer(null);
                setPlayerAnalysis(null);
              } else {
                setSelectedPlayer({ player, x, y, side: 'home', teamId: homeTeamId });
              }
            }}
          />
        ))}
        {awaySlots.map(({ player, x, y, subStatus }) => (
          <PitchPlayer
            key={player.id}
            player={player}
            x={x} y={y}
            color={AWAY_COLOR}
            subStatus={subStatus}
            isSelected={selectedPlayer?.player.id === player.id && selectedPlayer?.side === 'away'}
            onClick={() => {
              if (selectedPlayer?.player.id === player.id && selectedPlayer?.side === 'away') {
                setSelectedPlayer(null);
                setPlayerAnalysis(null);
              } else {
                setSelectedPlayer({ player, x, y, side: 'away', teamId: awayTeamId });
              }
            }}
          />
        ))}

        {/* Player Popover */}
        {selectedPlayer && (
          <PlayerPopover
            info={selectedPlayer}
            analysis={playerAnalysis}
            loading={analysisLoading}
            onClose={() => { setSelectedPlayer(null); setPlayerAnalysis(null); }}
          />
        )}
      </div>

      <div
        className="responsive-bench-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          background: CARD_BG,
          borderTop: `1px solid ${CARD_BORDER}`,
        }}
      >
        <BenchPanel coach={homeCoach} players={homeBench} subbedIn={subs.homeSubbedIn} subbedOut={subs.homeSubbedOut} />
        <BenchPanel coach={awayCoach} players={awayBench} subbedIn={subs.awaySubbedIn} subbedOut={subs.awaySubbedOut} withBorder={false} />
      </div>
    </div>
  );
}

function BenchPanel({ coach, players, subbedIn, subbedOut, withBorder = true }: {
  coach: string;
  players: (RosterPlayer | LineupPlayer)[];
  subbedIn?: Set<string>;
  subbedOut?: Set<string>;
  withBorder?: boolean;
}) {
  return (
    <div
      style={{
        padding: '16px 18px 14px',
        borderRight: withBorder ? `1px solid ${CARD_BORDER}` : undefined,
        minWidth: 0,
      }}
    >
      <div
        style={{
          textAlign: 'center',
          color: 'var(--foreground)',
          fontSize: 20,
          lineHeight: 1.2,
          marginBottom: 14,
        }}
      >
        主教练：{coach || '--'}
      </div>
      <div
        className="responsive-bench-list"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
          columnGap: 28,
          rowGap: 4,
        }}
      >
        {players.map(player => {
          const isSubbedIn = subbedIn?.has(player.id);
          const isSubbedOut = subbedOut?.has(player.id);
          const subStatus = isSubbedIn ? 'in' as const : isSubbedOut ? 'out' as const : undefined;
          return <SubItem key={player.id} player={player} subStatus={subStatus} />;
        })}
      </div>
    </div>
  );
}
