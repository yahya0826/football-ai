'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import api, { MatchDetailResponse, RecentMatch } from '@/lib/api';
import LiveMatchPanel from '@/components/LiveMatchPanel';

const FLAGS: Record<string, string> = {
  'Mexico': '🇲🇽', 'South Africa': '🇿🇦', 'South Korea': '🇰🇷', 'Czech Republic': '🇨🇿',
  'Canada': '🇨🇦', 'Bosnia and Herzegovina': '🇧🇦', 'Qatar': '🇶🇦', 'Switzerland': '🇨🇭',
  'Brazil': '🇧🇷', 'Morocco': '🇲🇦', 'Haiti': '🇭🇹', 'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
  'United States': '🇺🇸', 'Paraguay': '🇵🇾', 'Australia': '🇦🇺', 'Turkey': '🇹🇷',
  'Germany': '🇩🇪', 'Curaçao': '🇨🇼', 'Ivory Coast': '🇨🇮', 'Ecuador': '🇪🇨',
  'Netherlands': '🇳🇱', 'Japan': '🇯🇵', 'Sweden': '🇸🇪', 'Tunisia': '🇹🇳',
  'Belgium': '🇧🇪', 'Egypt': '🇪🇬', 'Iran': '🇮🇷', 'New Zealand': '🇳🇿',
  'Spain': '🇪🇸', 'Cape Verde': '🇨🇻', 'Saudi Arabia': '🇸🇦', 'Uruguay': '🇺🇾',
  'France': '🇫🇷', 'Senegal': '🇸🇳', 'Iraq': '🇮🇶', 'Norway': '🇳🇴',
  'Argentina': '🇦🇷', 'Algeria': '🇩🇿', 'Austria': '🇦🇹', 'Jordan': '🇯🇴',
  'Portugal': '🇵🇹', 'DR Congo': '🇨🇩', 'Uzbekistan': '🇺🇿', 'Colombia': '🇨🇴',
  'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'Croatia': '🇭🇷', 'Ghana': '🇬🇭', 'Panama': '🇵🇦',
};

const RESULT_COLORS: Record<string, string> = { W: '#10b981', D: '#eab308', L: '#ef4444' };
const RESULT_LABELS: Record<string, string> = { W: '胜', D: '平', L: '负' };

function getFlag(team: string) { return FLAGS[team] || '🏳️'; }

export default function MatchDetailClient() {
  const params = useParams();
  const matchId = parseInt(params.id as string);

  const [detail, setDetail] = useState<MatchDetailResponse | null>(null);
  const [highlights, setHighlights] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [hlLoading, setHlLoading] = useState(false);
  const [liveMatchId, setLiveMatchId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await api.getScheduleMatch(matchId);
        setDetail(data);
      } catch (err) {
        console.error('Failed to load match:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [matchId]);

  useEffect(() => {
    if (!detail?.match) return;
    const match = detail.match;
    setHlLoading(true);
    api.getMatchHighlights(matchId, {
      home_team: match.home_team,
      away_team: match.away_team,
      home_team_cn: match.home_team_cn,
      away_team_cn: match.away_team_cn,
      group: match.group,
      stage: match.stage,
      venue: match.venue,
    }).then(hl => {
      setHighlights(hl.highlights);
    }).catch(console.error).finally(() => setHlLoading(false));
  }, [detail?.match?.match_id]);

  useEffect(() => {
    if (!detail?.match) return;
    const m = detail.match;
    api.getLiveMatchLookup(m.home_team, m.away_team, m.date).then(res => {
      if (res.found && res.match_id) setLiveMatchId(res.match_id);
    }).catch(() => {});
  }, [detail?.match?.match_id]);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>加载中…</div>;
  }

  if (!detail?.match) {
    return <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>比赛不存在</div>;
  }

  const match = detail.match;

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '1.5rem 1rem' }}>
      <Link href="/matches" style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', textDecoration: 'none' }}>
        ← 返回赛程
      </Link>

      {liveMatchId && (
        <div style={{ margin: '1rem 0 1.5rem' }}>
          <LiveMatchPanel matchId={liveMatchId} />
        </div>
      )}

      <div style={{ textAlign: 'center', margin: '1.5rem 0 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1.5rem', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '3rem' }}>{getFlag(match.home_team)}</span>
          <div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff' }}>{match.home_team_cn}</div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>{match.home_team}</div>
          </div>
          <span style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f0c059' }}>VS</span>
          <div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff' }}>{match.away_team_cn}</div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>{match.away_team}</div>
          </div>
          <span style={{ fontSize: '3rem' }}>{getFlag(match.away_team)}</span>
        </div>
        <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', marginTop: '0.75rem' }}>
          {match.date} · 北京时间 {match.time_bj} · {match.venue}
          {match.group && ` · ${match.group}组 第${match.round}轮`}
          {match.stage !== 'group' && ` · ${match.stage === 'final' ? '决赛' : match.stage === 'semi_final' ? '半决赛' : match.stage === 'quarter_final' ? '1/4决赛' : match.stage === 'round_of_16' ? '1/8决赛' : '1/16决赛'}`}
        </div>
      </div>

      <SectionCard title="历史交锋记录">
        {detail.h2h && detail.h2h.total_matches > 0 ? (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-around', marginBottom: '0.75rem' }}>
              <StatBlock value={detail.h2h.home_wins} label={`${match.home_team_cn}胜`} color="#3b82f6" />
              <StatBlock value={detail.h2h.draws} label="平局" color="#eab308" />
              <StatBlock value={detail.h2h.away_wins} label={`${match.away_team_cn}胜`} color="#ef4444" />
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', maxHeight: '8rem', overflowY: 'auto' }}>
              {detail.h2h.matches.slice(-10).reverse().map((m, i) => (
                <div key={i} style={{ padding: '0.2rem 0', borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                  {m.date} · {m.home_team} {m.home_score}-{m.away_score} {m.away_team}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>暂无历史交锋数据</div>
        )}
      </SectionCard>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <SectionCard title={`${match.home_team_cn} 近期战绩`}>
          <RecentForm recent={detail.home_recent} />
        </SectionCard>
        <SectionCard title={`${match.away_team_cn} 近期战绩`}>
          <RecentForm recent={detail.away_recent} />
        </SectionCard>
      </div>

      <SectionCard title="比赛看点 & 关注点">
        {hlLoading ? (
          <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', textAlign: 'center', padding: '1rem' }}>
            AI 正在分析比赛看点…
          </div>
        ) : highlights ? (
          <div style={{ fontSize: 'var(--text-sm)', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
            {highlights}
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>暂无数据</div>
        )}
      </SectionCard>
    </div>
  );
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{
      padding: '1rem', background: 'rgba(255,255,255,0.03)',
      borderRadius: '0.75rem', border: '1px solid rgba(255,255,255,0.06)',
      marginBottom: '0.75rem',
    }}>
      <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
        {title}
      </div>
      {children}
    </div>
  );
}

function StatBlock({ value, label, color }: { value: number; label: string; color: string }) {
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontSize: '1.4rem', fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{label}</div>
    </div>
  );
}

function RecentForm({ recent }: { recent: RecentMatch[] | null }) {
  if (!recent || recent.length === 0) {
    return <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>暂无数据</div>;
  }
  const wins = recent.filter(r => r.result === 'W').length;
  const draws = recent.filter(r => r.result === 'D').length;

  return (
    <div>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', fontSize: 'var(--text-xs)' }}>
        <span style={{ color: '#10b981' }}>{wins}胜</span>
        <span style={{ color: '#eab308' }}>{draws}平</span>
        <span style={{ color: '#ef4444' }}>{recent.length - wins - draws}负</span>
        <span style={{ color: 'var(--text-muted)' }}>· 近{recent.length}场</span>
      </div>
      <div style={{ display: 'flex', gap: '0.15rem', marginBottom: '0.5rem' }}>
        {recent.slice(0, 10).map((r, i) => (
          <div key={i} style={{
            width: '1.3rem', height: '1.3rem', borderRadius: '0.2rem',
            background: RESULT_COLORS[r.result] || '#555',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '9px', fontWeight: 700, color: '#fff',
          }}>
            {RESULT_LABELS[r.result]}
          </div>
        ))}
      </div>
      <div style={{ fontSize: '10px', color: 'var(--text-muted)', maxHeight: '8rem', overflowY: 'auto' }}>
        {recent.slice(0, 10).map((r, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.1rem 0', borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
            <span>{r.date}</span>
            <span>{r.home_team} {r.home_score}-{r.away_score} {r.away_team}</span>
            <span style={{ color: RESULT_COLORS[r.result], fontWeight: 600 }}>{RESULT_LABELS[r.result]}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
