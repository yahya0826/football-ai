'use client';

import { useState, useEffect } from 'react';
import api, { TeamRoster, RosterPlayer, MatchLineups, TeamLineup, LineupPlayer } from '@/lib/api';

type Formation = '4-4-2' | '4-3-3' | '3-5-2' | '4-2-3-1' | '5-4-1' | '3-4-3';
type Side = 'home' | 'away';

interface FormationConfig {
  def: number;
  mid: number;
  fwd: number;
}

interface PitchSlot {
  player: RosterPlayer | LineupPlayer;
  x: number;
  y: number;
}

const FORMATIONS: Record<Formation, FormationConfig> = {
  '4-4-2': { def: 4, mid: 4, fwd: 2 },
  '4-3-3': { def: 4, mid: 3, fwd: 3 },
  '3-5-2': { def: 3, mid: 5, fwd: 2 },
  '4-2-3-1': { def: 4, mid: 5, fwd: 1 },
  '5-4-1': { def: 5, mid: 4, fwd: 1 },
  '3-4-3': { def: 3, mid: 4, fwd: 3 },
};

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

function displayName(player: RosterPlayer | LineupPlayer): string {
  return player.short_name || player.name || '未知球员';
}

function pickPlayers(roster: TeamRoster, formation: FormationConfig): { starters: RosterPlayer[]; bench: RosterPlayer[] } {
  const gk = roster.players.G.slice(0, 1);
  const def = roster.players.D.slice(0, formation.def);
  const mid = roster.players.M.slice(0, formation.mid);
  const fwd = roster.players.F.slice(0, formation.fwd);
  const starters = [...gk, ...def, ...mid, ...fwd];

  const starterIds = new Set(starters.map(p => p.id));
  const allOthers = [
    ...roster.players.G,
    ...roster.players.D,
    ...roster.players.M,
    ...roster.players.F,
    ...roster.players.U,
  ];
  const bench = allOthers.filter(p => !starterIds.has(p.id));

  return { starters, bench };
}

function buildSlotsFromLineup(starters: LineupPlayer[], formation: Formation, side: Side): PitchSlot[] {
  const gk = starters.filter(p => p.position.startsWith('G'));
  const def = starters.filter(p => p.position.startsWith('D'));
  const mid = starters.filter(p => p.position.startsWith('M'));
  const fwd = starters.filter(p => p.position.startsWith('F'));
  const isHome = side === 'home';
  const mirror = (x: number) => (isHome ? x : 100 - x);

  const slots: PitchSlot[] = [];
  gk.slice(0, 1).forEach(player => slots.push({ player, x: mirror(5.5), y: 50 }));

  linePositions(def.length, mirror(18.5), 17, 83).forEach((pos, i) => {
    if (def[i]) slots.push({ player: def[i], ...pos });
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
      if (line[i]) slots.push({ player: line[i], ...pos });
    });
  });

  linePositions(fwd.length, mirror(45), fwd.length === 1 ? 48 : 24, fwd.length === 1 ? 52 : 76).forEach((pos, i) => {
    if (fwd[i]) slots.push({ player: fwd[i], ...pos });
  });

  return slots;
}

function buildSlots(players: { starters: RosterPlayer[] }, formation: Formation, side: Side): PitchSlot[] {
  const starters = players.starters;
  const gk = starters.filter(p => p.position.startsWith('G'));
  const def = starters.filter(p => p.position.startsWith('D'));
  const mid = starters.filter(p => p.position.startsWith('M'));
  const fwd = starters.filter(p => p.position.startsWith('F'));
  const isHome = side === 'home';
  const mirror = (x: number) => (isHome ? x : 100 - x);

  const slots: PitchSlot[] = [];
  gk.slice(0, 1).forEach(player => slots.push({ player, x: mirror(5.5), y: 50 }));

  linePositions(def.length, mirror(18.5), 17, 83).forEach((pos, i) => {
    if (def[i]) slots.push({ player: def[i], ...pos });
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
      if (line[i]) slots.push({ player: line[i], ...pos });
    });
  });

  linePositions(fwd.length, mirror(45), fwd.length === 1 ? 48 : 24, fwd.length === 1 ? 52 : 76).forEach((pos, i) => {
    if (fwd[i]) slots.push({ player: fwd[i], ...pos });
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

function PitchPlayer({ player, x, y, color }: { player: RosterPlayer | LineupPlayer; x: number; y: number; color: string }) {
  return (
    <div
      style={{
        position: 'absolute',
        left: `${x}%`,
        top: `${y}%`,
        transform: 'translate(-50%, -50%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        minWidth: 82,
        zIndex: 3,
        pointerEvents: 'none',
      }}
      title={`${player.jersey || '?'} ${displayName(player)}`}
    >
      <ShirtMarker color={color} number={player.jersey} />
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

function SubItem({ player }: { player: RosterPlayer | LineupPlayer }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 7,
        minWidth: 0,
        padding: '3px 0',
      }}
    >
      <ShirtMarker color={BENCH_COLOR} number={player.jersey} size={31} />
      <span
        style={{
          minWidth: 0,
          color: 'var(--foreground)',
          fontSize: 16,
          lineHeight: 1.25,
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}
        title={displayName(player)}
      >
        {displayName(player)}
      </span>
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
}

export default function FormationView({ homeTeamId, awayTeamId, homeName, awayName, homeNameCn, awayNameCn, lineups }: Props) {
  // Use real ESPN lineups if available
  const homeLineup: TeamLineup | undefined = lineups?.home;
  const awayLineup: TeamLineup | undefined = lineups?.away;
  const hasRealLineups = !!(homeLineup?.starters?.length && awayLineup?.starters?.length);
  const [homeRoster, setHomeRoster] = useState<TeamRoster | null>(null);
  const [awayRoster, setAwayRoster] = useState<TeamRoster | null>(null);
  const [loading, setLoading] = useState(true);
  const [homeFormation, setHomeFormation] = useState<Formation>('5-4-1');
  const [awayFormation, setAwayFormation] = useState<Formation>('4-2-3-1');

  // Only fetch rosters if real lineups not available
  useEffect(() => {
    if (hasRealLineups) {
      setLoading(false);
      return;
    }
    let mounted = true;
    async function load() {
      setLoading(true);
      try {
        const [home, away] = await Promise.all([
          api.getTeamRoster(homeTeamId),
          api.getTeamRoster(awayTeamId),
        ]);
        if (mounted) {
          setHomeRoster(home);
          setAwayRoster(away);
          const guessFormation = (def: number, mid: number, fwd: number): Formation => {
            if (def >= 5) return '5-4-1';
            if (def === 3 && mid >= 5) return '3-5-2';
            if (def === 3) return '3-4-3';
            if (mid >= 5) return '4-2-3-1';
            if (fwd >= 3) return '4-3-3';
            return '4-4-2';
          };
          setHomeFormation(guessFormation(home.players.D.length, home.players.M.length, home.players.F.length));
          setAwayFormation(guessFormation(away.players.D.length, away.players.M.length, away.players.F.length));
        }
      } catch {
        // Roster not available
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
  }, [homeTeamId, awayTeamId, hasRealLineups]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: TEXT_MUTED, fontSize: 14, background: CARD_BG, border: `1px solid ${CARD_BORDER}`, borderRadius: '1rem' }}>
        加载阵容数据中...
      </div>
    );
  }

  // Build slots from real lineups or fallback to roster guessing
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

  if (hasRealLineups && homeLineup && awayLineup) {
    const hForm = (homeLineup.formation || '4-4-2') as Formation;
    const aForm = (awayLineup.formation || '4-3-3') as Formation;
    displayHomeFormation = ['4-4-2','4-3-3','3-5-2','4-2-3-1','5-4-1','3-4-3'].includes(hForm) ? hForm : '4-4-2';
    displayAwayFormation = ['4-4-2','4-3-3','3-5-2','4-2-3-1','5-4-1','3-4-3'].includes(aForm) ? aForm : '4-3-3';

    homeSlots = buildSlotsFromLineup(homeLineup.starters, displayHomeFormation, 'home');
    awaySlots = buildSlotsFromLineup(awayLineup.starters, displayAwayFormation, 'away');
    homeBench = homeLineup.substitutes;
    awayBench = awayLineup.substitutes;
    resolvedHomeName = homeNameCn || homeName;
    resolvedAwayName = awayNameCn || awayName;
    homeCoach = '';
    awayCoach = '';
    setHomeFormation(displayHomeFormation);
    setAwayFormation(displayAwayFormation);
  } else {
    if (!homeRoster || !awayRoster) {
      return (
        <div style={{ textAlign: 'center', padding: '2rem', color: TEXT_MUTED, fontSize: 14, background: CARD_BG, border: `1px solid ${CARD_BORDER}`, borderRadius: '1rem' }}>
          阵容数据暂不可用（比赛日接入 ESPN 后显示）
        </div>
      );
    }

    const home = pickPlayers(homeRoster, FORMATIONS[homeFormation]);
    const away = pickPlayers(awayRoster, FORMATIONS[awayFormation]);
    homeSlots = buildSlots(home, homeFormation, 'home');
    awaySlots = buildSlots(away, awayFormation, 'away');
    homeBench = home.bench;
    awayBench = away.bench;
    displayHomeFormation = homeFormation;
    displayAwayFormation = awayFormation;
    resolvedHomeName = homeNameCn || homeRoster.team_name_cn || homeName || homeRoster.team_name;
    resolvedAwayName = awayNameCn || awayRoster.team_name_cn || awayName || awayRoster.team_name;
    homeCoach = homeRoster.coach || '';
    awayCoach = awayRoster.coach || '';
  }

  return (
    <div
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

        {homeSlots.map(({ player, x, y }) => (
          <PitchPlayer key={player.id} player={player} x={x} y={y} color={HOME_COLOR} />
        ))}
        {awaySlots.map(({ player, x, y }) => (
          <PitchPlayer key={player.id} player={player} x={x} y={y} color={AWAY_COLOR} />
        ))}
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          background: CARD_BG,
          borderTop: `1px solid ${CARD_BORDER}`,
        }}
      >
        <BenchPanel coach={homeCoach} players={homeBench} />
        <BenchPanel coach={awayCoach} players={awayBench} withBorder={false} />
      </div>
    </div>
  );
}

function BenchPanel({ coach, players, withBorder = true }: { coach: string; players: (RosterPlayer | LineupPlayer)[]; withBorder?: boolean }) {
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
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
          columnGap: 28,
          rowGap: 4,
        }}
      >
        {players.map(player => (
          <SubItem key={player.id} player={player} />
        ))}
      </div>
    </div>
  );
}
