'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import type { LiveMatchSummary } from '@/lib/api';

const POLL_INTERVAL = 30000;

const FLAGS: Record<string, string> = {
  'Argentina': '🇦🇷', 'Brazil': '🇧🇷', 'Germany': '🇩🇪', 'France': '🇫🇷',
  'Spain': '🇪🇸', 'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'Italy': '🇮🇹', 'Netherlands': '🇳🇱',
  'Portugal': '🇵🇹', 'Belgium': '🇧🇪', 'Croatia': '🇭🇷', 'Uruguay': '🇺🇾',
  'Mexico': '🇲🇽', 'United States': '🇺🇸', 'Canada': '🇨🇦',
  'Japan': '🇯🇵', 'South Korea': '🇰🇷', 'Australia': '🇦🇺',
  'Morocco': '🇲🇦', 'Senegal': '🇸🇳', 'Egypt': '🇪🇬', 'Nigeria': '🇳🇬',
  'Colombia': '🇨🇴', 'Switzerland': '🇨🇭', 'Denmark': '🇩🇰',
  'Turkey': '🇹🇷', 'Austria': '🇦🇹', 'Sweden': '🇸🇪', 'Norway': '🇳🇴',
  'Poland': '🇵🇱', 'Serbia': '🇷🇸', 'Czech Republic': '🇨🇿',
  'Ivory Coast': '🇨🇮', 'Ghana': '🇬🇭', 'Cameroon': '🇨🇲',
  'Algeria': '🇩🇿', 'Tunisia': '🇹🇳', 'Ecuador': '🇪🇨', 'Chile': '🇨🇱',
  'Saudi Arabia': '🇸🇦', 'Iran': '🇮🇷', 'Qatar': '🇶🇦',
  'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'Wales': '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
};

function getFlag(name: string): string {
  for (const [k, v] of Object.entries(FLAGS)) {
    if (name.toLowerCase().includes(k.toLowerCase())) return v;
  }
  return '🏳️';
}

function LiveTickerLink({ m, scheduleId }: { m: LiveMatchSummary; scheduleId: number | null }) {
  const href = scheduleId ? `/matches/${scheduleId}` : '/matches';
  return (
    <Link key={m.match_id} href={href} style={{ textDecoration: 'none' }}>
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        fontSize: 'var(--text-xs)',
        color: '#e2e8f0',
        cursor: 'pointer',
      }}>
        <span style={{ fontSize: '0.9rem' }}>{getFlag(m.home_team)}</span>
        <span style={{ fontWeight: 600 }}>{m.home_team_cn || m.home_team}</span>
        <span style={{
          fontWeight: 800,
          color: '#fff',
          background: 'rgba(255,255,255,0.1)',
          padding: '0.1rem 0.4rem',
          borderRadius: '0.25rem',
        }}>
          {m.home_score} - {m.away_score}
        </span>
        <span style={{ fontWeight: 600 }}>{m.away_team_cn || m.away_team}</span>
        <span style={{ fontSize: '0.9rem' }}>{getFlag(m.away_team)}</span>
        <span style={{
          color: '#ef4444',
          fontSize: '10px',
          fontWeight: 700,
        }}>
          {m.clock || m.status_detail}&apos;
        </span>
      </span>
    </Link>
  );
}

export default function LiveScoreTicker() {
  const [liveMatches, setLiveMatches] = useState<LiveMatchSummary[]>([]);
  const [visible, setVisible] = useState(false);
  const [scheduleIds, setScheduleIds] = useState<Record<string, number | null>>({});
  const lookedUp = useRef<Set<string>>(new Set());

  useEffect(() => {
    let mounted = true;
    async function poll() {
      try {
        const data = await api.getLiveScoreboard();
        if (mounted) {
          setLiveMatches(data.live);
          setVisible(data.live.length > 0);
          // Look up schedule match IDs for new live matches
          for (const m of data.live) {
            if (lookedUp.current.has(m.match_id)) continue;
            lookedUp.current.add(m.match_id);
            try {
              const res = await api.findScheduleMatch(m.home_team, m.away_team, m.date?.slice(0, 10));
              if (mounted) {
                setScheduleIds(prev => ({ ...prev, [m.match_id]: res.found ? res.match_id : null }));
              }
            } catch {
              setScheduleIds(prev => ({ ...prev, [m.match_id]: null }));
            }
          }
        }
      } catch { /* silently fail */ }
    }
    poll();
    const t = setInterval(poll, POLL_INTERVAL);
    return () => { mounted = false; clearInterval(t); };
  }, []);

  if (!visible || liveMatches.length === 0) return null;

  const renderItems = (dup?: boolean) =>
    liveMatches.map((m) => (
      <LiveTickerLink key={dup ? `dup-${m.match_id}` : m.match_id} m={m} scheduleId={scheduleIds[m.match_id] ?? null} />
    ));

  return (
    <div style={{
      background: 'linear-gradient(135deg, #1a0a0a, #0a1a0a)',
      borderBottom: '1px solid rgba(239, 68, 68, 0.3)',
      overflow: 'hidden',
      whiteSpace: 'nowrap',
      padding: '0.4rem 0',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '1.5rem',
        animation: liveMatches.length > 2 ? 'ticker-scroll 25s linear infinite' : 'none',
        padding: '0 1rem',
      }}>
        <span style={{
          background: '#ef4444',
          color: '#fff',
          padding: '0.15rem 0.5rem',
          borderRadius: '0.25rem',
          fontSize: '11px',
          fontWeight: 800,
          animation: 'pulse 1.5s infinite',
        }}>
          🔴 LIVE
        </span>
        {renderItems()}
        {/* Duplicate for seamless loop */}
        {liveMatches.length > 2 && renderItems(true)}
      </div>
      <style jsx>{`
        @keyframes ticker-scroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}
