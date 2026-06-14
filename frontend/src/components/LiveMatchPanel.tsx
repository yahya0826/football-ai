'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import type { LiveMatchDetail, LiveEvent } from '@/lib/api';

const POLL_INTERVAL = 30000;

interface Props {
  matchId: string;
}

const EVENT_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  goal: { icon: '⚽', color: '#fff', bg: 'rgba(16, 185, 129, 0.15)' },
  yellow_card: { icon: '🟨', color: '#fbbf24', bg: 'rgba(251, 191, 36, 0.08)' },
  red_card: { icon: '🟥', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },
  substitution: { icon: '🔄', color: '#94a3b8', bg: 'rgba(148, 163, 184, 0.08)' },
  kickoff: { icon: '⏱️', color: '#64748b', bg: 'transparent' },
  halftime: { icon: '⏸️', color: '#64748b', bg: 'transparent' },
  fulltime: { icon: '🏁', color: '#64748b', bg: 'transparent' },
};

const STAT_KEYS = [
  'possessionPct',
  'totalShots',
  'shotsOnTarget',
  'shotPct',
  'blockedShots',
  'wonCorners',
  'foulsCommitted',
  'yellowCards',
  'redCards',
  'offsides',
  'saves',
  'totalPasses',
  'passingPct',
  'totalCrosses',
  'totalTackles',
  'interceptions',
  'totalClearance',
];

function EventItem({ ev }: { ev: LiveEvent }) {
  const cfg = EVENT_CONFIG[ev.type] || EVENT_CONFIG.kickoff;
  const descCn = ev.description_cn || ev.text;

  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: '0.4rem', padding: '0.3rem 0.4rem',
      borderRadius: '0.3rem', background: cfg.bg, fontSize: 'var(--text-xs)',
    }}>
      <span style={{ fontSize: '0.85rem', flexShrink: 0, marginTop: 1 }}>{cfg.icon}</span>
      <span style={{ color: 'var(--text-muted)', fontSize: '10px', fontWeight: 600, minWidth: '2rem', flexShrink: 0 }}>
        {ev.minute}&apos;
      </span>
      <span style={{ color: '#e2e8f0', lineHeight: 1.4 }}>
        {descCn || ev.text}
      </span>
    </div>
  );
}

function StatBar({ label, homeVal, awayVal, homeColor = '#3b82f6', awayColor = '#ef4444' }: {
  label: string; homeVal: string; awayVal: string;
  homeColor?: string; awayColor?: string;
}) {
  const h = parseFloat(homeVal) || 0;
  const a = parseFloat(awayVal) || 0;
  const total = h + a;
  const hPct = total > 0 ? (h / total) * 100 : 50;
  const aPct = total > 0 ? (a / total) * 100 : 50;

  return (
    <div style={{ marginBottom: '0.55rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.15rem', fontSize: '11px' }}>
        <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{homeVal}</span>
        <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>{label}</span>
        <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{awayVal}</span>
      </div>
      <div style={{ display: 'flex', height: '4px', borderRadius: '2px', overflow: 'hidden', background: 'rgba(255,255,255,0.06)' }}>
        <div style={{ width: `${hPct}%`, background: homeColor, transition: 'width 0.5s ease' }} />
        <div style={{ width: `${aPct}%`, background: awayColor, transition: 'width 0.5s ease' }} />
      </div>
    </div>
  );
}

export default function LiveMatchPanel({ matchId }: Props) {
  const [data, setData] = useState<LiveMatchDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    async function poll() {
      try {
        const detail = await api.getLiveMatchDetail(matchId);
        if (mounted) {
          setData(detail);
          setLoading(false);
          setError('');
        }
      } catch (err) {
        console.error('[LiveMatchPanel] Fetch error:', err);
        if (mounted) { setError('无法加载实时数据'); setLoading(false); }
      }
    }
    poll();
    const t = setInterval(poll, POLL_INTERVAL);
    return () => { mounted = false; clearInterval(t); };
  }, [matchId]);

  if (loading) {
    return (
      <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>
        正在加载实时数据…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>
        {error || '暂无实时数据'}
      </div>
    );
  }

  const { status, home, away, events, statistics } = data;
  const isLive = status.state === 'live' || status.state === 'halftime';
  const homeStats = statistics?.home?.stats || {};
  const awayStats = statistics?.away?.stats || {};
  const homeName = home.name_cn || home.name;
  const awayName = away.name_cn || away.name;
  const statusLabel = status.state_cn || (status.state === 'live' ? '进行中' : status.state === 'halftime' ? '中场休息' : status.state === 'finished' ? '已结束' : status.detail);

  return (
    <div style={{
      background: 'rgba(255,255,255,0.02)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: '0.75rem',
      overflow: 'hidden',
    }}>
      {/* Score Banner */}
      <div style={{
        background: isLive
          ? 'linear-gradient(135deg, rgba(239,68,68,0.15), rgba(59,130,246,0.1))'
          : 'linear-gradient(135deg, rgba(100,116,139,0.1), rgba(59,130,246,0.08))',
        padding: '1.25rem 1rem',
        textAlign: 'center',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}>
        {/* Status badge */}
        <div style={{ marginBottom: '0.75rem' }}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.35rem',
            background: isLive ? '#ef4444' : status.state === 'finished' ? '#64748b' : '#f59e0b',
            color: '#fff', padding: '0.2rem 0.7rem', borderRadius: '1rem',
            fontSize: '11px', fontWeight: 700,
            animation: isLive ? 'pulse 1.5s infinite' : 'none',
          }}>
            {isLive && <span style={{
              width: 6, height: 6, borderRadius: '50%', background: '#fff',
              display: 'inline-block', animation: 'pulse 1.5s infinite',
            }} />}
            {isLive ? `🔴 ${statusLabel}` : statusLabel}
            {isLive && status.clock && ` ${status.clock}`}
          </span>
        </div>

        {/* Score */}
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ flex: 1, textAlign: 'right' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#e2e8f0' }}>{homeName}</div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{home.abbrev}</div>
          </div>
          <div style={{
            fontSize: '2.5rem', fontWeight: 900, color: '#fff',
            background: 'rgba(255,255,255,0.05)', padding: '0.3rem 1.2rem',
            borderRadius: '0.5rem', letterSpacing: '0.15em',
          }}>
            {home.score} - {away.score}
          </div>
          <div style={{ flex: 1, textAlign: 'left' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#e2e8f0' }}>{awayName}</div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{away.abbrev}</div>
          </div>
        </div>
      </div>

      {/* Events + Stats columns */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0' }}>
        {/* Events Timeline */}
        <div style={{ padding: '0.75rem', borderRight: '1px solid rgba(255,255,255,0.04)' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            比赛事件
          </div>
          <div style={{ maxHeight: '20rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            {events.length === 0 && (
              <div style={{ color: 'var(--text-muted)', fontSize: '10px', padding: '0.5rem 0' }}>暂无事件</div>
            )}
            {[...events].reverse().map((ev, i) => (
              <EventItem key={i} ev={ev} />
            ))}
          </div>
        </div>

        {/* Statistics */}
        <div style={{ padding: '0.75rem' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            技术统计
          </div>
          <div>
            {STAT_KEYS.map(key => {
              const hStat = homeStats[key];
              const aStat = awayStats[key];
              if (!hStat && !aStat) return null;
              const cnLabel = hStat?.label_cn || aStat?.label_cn || hStat?.label || aStat?.label || key;
              return (
                <StatBar
                  key={key}
                  label={cnLabel}
                  homeVal={hStat?.value || '0'}
                  awayVal={aStat?.value || '0'}
                />
              );
            })}
            {Object.keys(homeStats).length === 0 && (
              <div style={{ color: 'var(--text-muted)', fontSize: '10px', padding: '0.5rem 0' }}>暂无统计数据</div>
            )}
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
      `}</style>
    </div>
  );
}
