'use client';

import { useState, useEffect, useMemo } from 'react';
import api, { ScheduleMatch, MatchScheduleResponse, MatchDetailResponse, MatchHighlightsResponse, H2HData, RecentMatch, LiveScoreboardResponse, LiveMatchSummary, MatchAnalysisResponse, MatchAnalysis, LiveEvent } from '@/lib/api';
import LiveMatchPanel from '@/components/LiveMatchPanel';

const STAGE_TABS: Record<string, { label: string; key: string }> = {
  all: { label: '全部比赛', key: 'all' },
  group: { label: '小组赛', key: 'group' },
  round_of_32: { label: '1/16决赛', key: 'round_of_32' },
  round_of_16: { label: '1/8决赛', key: 'round_of_16' },
  quarter_final: { label: '1/4决赛', key: 'quarter_final' },
  semi_final: { label: '半决赛', key: 'semi_final' },
  third_place: { label: '季军赛', key: 'third_place' },
  final: { label: '决赛', key: 'final' },
};

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

const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

function getFlag(team: string): string {
  return FLAGS[team] || '🏳️';
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  const month = d.getMonth() + 1;
  const day = d.getDate();
  const weekday = WEEKDAYS[d.getDay()];
  return `${month}月${day}日 ${weekday}`;
}

function isKnockoutPlaceholder(m: ScheduleMatch): boolean {
  if (m.stage === 'group') return false;
  const hasDigit = (s: string) => /\d/.test(s);
  return hasDigit(m.home_team) || hasDigit(m.away_team) || m.home_team.includes('第') || m.away_team.includes('第');
}

export default function SchedulePage() {
  const [schedule, setSchedule] = useState<MatchScheduleResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeStage, setActiveStage] = useState('all');
  const [selectedGroup, setSelectedGroup] = useState('');
  const [selectedMatch, setSelectedMatch] = useState<ScheduleMatch | null>(null);
  const [matchDetail, setMatchDetail] = useState<MatchDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [aiHighlights, setAiHighlights] = useState<string | null>(null);
  const [highlightsLoading, setHighlightsLoading] = useState(false);
  const [liveMatchId, setLiveMatchId] = useState<string | null>(null);
  const [liveLookupDone, setLiveLookupDone] = useState(false);

  // Today view state
  const [viewMode, setViewMode] = useState<'all' | 'today'>('all');
  const [todayDate, setTodayDate] = useState('2026-06-13');
  const [liveScoreboard, setLiveScoreboard] = useState<LiveScoreboardResponse | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getMatchSchedule();
        setSchedule(data);
      } catch (err) {
        console.error('Failed to load schedule:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Auto-select first match of first date on load
  useEffect(() => {
    if (!schedule || selectedMatch) return;
    const sorted = [...schedule.matches]
      .filter(m => !isKnockoutPlaceholder(m))
      .sort((a, b) => a.date.localeCompare(b.date) || a.time_bj.localeCompare(b.time_bj));
    if (sorted.length > 0) {
      handleMatchClick(sorted[0]);
    }
  }, [schedule]);

  // Fetch live scoreboard for today view
  useEffect(() => {
    if (viewMode !== 'today') return;
    let mounted = true;
    async function poll() {
      try {
        const data = await api.getLiveScoreboard();
        if (mounted) setLiveScoreboard(data);
      } catch { /* silently fail */ }
    }
    poll();
    const t = setInterval(poll, 30000);
    return () => { mounted = false; clearInterval(t); };
  }, [viewMode]);

  // Set initial today date from schedule
  useEffect(() => {
    if (!schedule) return;
    const today = '2026-06-13';
    const dates = [...new Set(schedule.matches.map(m => m.date))].sort();
    if (dates.includes(today)) {
      setTodayDate(today);
    } else if (dates.length > 0) {
      setTodayDate(dates[0]);
    }
  }, [schedule]);

  const filteredMatches = useMemo(() => {
    if (!schedule) return [];
    let matches = schedule.matches;
    if (activeStage !== 'all') {
      matches = matches.filter(m => m.stage === activeStage);
    }
    if (selectedGroup) {
      matches = matches.filter(m => m.group === selectedGroup);
    }
    return matches;
  }, [schedule, activeStage, selectedGroup]);

  const matchesByDate = useMemo(() => {
    const groups: Record<string, ScheduleMatch[]> = {};
    filteredMatches.forEach(m => {
      if (!groups[m.date]) groups[m.date] = [];
      groups[m.date].push(m);
    });
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
  }, [filteredMatches]);

  const handleMatchClick = async (match: ScheduleMatch) => {
    if (isKnockoutPlaceholder(match)) return;
    setViewMode('all');
    setSelectedMatch(match);
    setMatchDetail(null);
    setAiHighlights(null);
    setLiveMatchId(null);
    setLiveLookupDone(false);

    // Load schedule detail
    setDetailLoading(true);
    try {
      const detail = await api.getScheduleMatch(match.match_id);
      setMatchDetail(detail);
    } catch (err) {
      console.error('Failed to load match detail:', err);
    } finally {
      setDetailLoading(false);
    }

    // Load AI highlights
    setHighlightsLoading(true);
    try {
      const hl = await api.getMatchHighlights(match.match_id, {
        home_team: match.home_team,
        away_team: match.away_team,
        home_team_cn: match.home_team_cn,
        away_team_cn: match.away_team_cn,
        group: match.group,
        stage: match.stage,
        venue: match.venue,
      });
      setAiHighlights(hl.highlights);
    } catch (err) {
      console.error('Failed to load highlights:', err);
    } finally {
      setHighlightsLoading(false);
    }

    // Look up ESPN live match
    try {
      const res = await api.getLiveMatchLookup(match.home_team, match.away_team, match.date);
      if (res.found && res.match_id) {
        setLiveMatchId(res.match_id);
      }
    } catch (err) {
      console.error('Live lookup failed:', err);
    } finally {
      setLiveLookupDone(true);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh', color: 'var(--text-muted)' }}>
        正在加载赛程…
      </div>
    );
  }

  const groups = schedule?.groups ? Object.keys(schedule.groups) : [];
  const stageCounts: Record<string, number> = {};
  if (schedule) {
    schedule.matches.forEach(m => {
      stageCounts[m.stage] = (stageCounts[m.stage] || 0) + 1;
    });
  }

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '1.5rem 1rem' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, margin: '0 0 0.5rem', background: 'linear-gradient(135deg, #f0c059, #3b82f6, #ef4444)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          2026 世界杯赛程
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', margin: 0 }}>
          6月12日 — 7月20日 · 104场比赛 · 16座球场 · 美国/加拿大/墨西哥
        </p>
      </div>

      {/* ── Tab Switcher ── */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
        {(['all', 'today'] as const).map(mode => (
          <button
            key={mode}
            onClick={() => setViewMode(mode)}
            style={{
              padding: '0.55rem 1.5rem',
              borderRadius: '0.6rem',
              border: viewMode === mode ? '1px solid #3b82f6' : '1px solid #333',
              background: viewMode === mode ? 'rgba(59,130,246,0.12)' : 'transparent',
              color: viewMode === mode ? '#3b82f6' : 'var(--text-muted)',
              fontSize: 'var(--text-sm)',
              fontWeight: viewMode === mode ? 700 : 500,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            {mode === 'all' ? '📋 全部赛程' : '🔥 今日比赛'}
          </button>
        ))}
      </div>

      {/* ── Today View ── */}
      {viewMode === 'today' ? (
        <TodayView
          schedule={schedule}
          liveScoreboard={liveScoreboard}
          todayDate={todayDate}
          onDateChange={setTodayDate}
          onMatchClick={handleMatchClick}
        />
      ) : (
        <>

      {/* Stage Tabs */}
      <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', marginBottom: '1rem', justifyContent: 'center' }}>
        {Object.entries(STAGE_TABS).map(([key, { label }]) => {
          const count = stageCounts[key] || 0;
          const displayLabel = key === 'all' ? `${label}(${schedule?.total || 0})` : `${label}(${count})`;
          return (
            <button
              key={key}
              onClick={() => { setActiveStage(key); setSelectedGroup(''); }}
              style={{
                padding: '0.35rem 0.75rem', borderRadius: '1.25rem',
                border: activeStage === key ? '1px solid #3b82f6' : '1px solid #333',
                background: activeStage === key ? 'rgba(59,130,246,0.15)' : 'transparent',
                color: activeStage === key ? '#3b82f6' : 'var(--text-muted)',
                fontSize: 'var(--text-xs)', cursor: 'pointer',
                fontWeight: activeStage === key ? 600 : 400, transition: 'all 0.2s',
              }}
            >
              {label}
              {count > 0 && key !== 'all' && <span style={{ marginLeft: 2, opacity: 0.7 }}> {count}</span>}
            </button>
          );
        })}
      </div>

      {/* Group filter */}
      {activeStage === 'group' && (
        <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', marginBottom: '1rem', justifyContent: 'center' }}>
          <button
            onClick={() => setSelectedGroup('')}
            style={{
              padding: '0.3rem 0.6rem', borderRadius: '1rem',
              border: !selectedGroup ? '1px solid #f0c059' : '1px solid #333',
              background: !selectedGroup ? 'rgba(240,192,89,0.1)' : 'transparent',
              color: !selectedGroup ? '#f0c059' : 'var(--text-muted)',
              fontSize: 'var(--text-xs)', cursor: 'pointer',
            }}
          >
            全部
          </button>
          {groups.map(g => (
            <button
              key={g}
              onClick={() => setSelectedGroup(g)}
              style={{
                padding: '0.3rem 0.6rem', borderRadius: '1rem',
                border: selectedGroup === g ? '1px solid #3b82f6' : '1px solid #333',
                background: selectedGroup === g ? 'rgba(59,130,246,0.1)' : 'transparent',
                color: selectedGroup === g ? '#3b82f6' : 'var(--text-muted)',
                fontSize: 'var(--text-xs)', cursor: 'pointer',
              }}
            >
              {g}组
            </button>
          ))}
        </div>
      )}

      {/* ── Two-Column Layout ── */}
      <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'flex-start' }}>
        {/* ── LEFT: Match List (40%) ── */}
        <div style={{
          flex: '0 0 40%',
          maxHeight: 'calc(100vh - 280px)',
          overflowY: 'auto',
          paddingRight: '0.5rem',
        }}>
          {matchesByDate.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
              该筛选条件下暂无比赛
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {matchesByDate.map(([date, matches]) => (
                <div key={date}>
                  <div style={{
                    fontSize: 'var(--text-sm)', fontWeight: 700, color: '#f0c059',
                    padding: '0.4rem 0.6rem', background: 'rgba(240,192,89,0.06)',
                    borderRadius: '0.5rem', marginBottom: '0.4rem',
                    display: 'flex', alignItems: 'center', gap: '0.5rem',
                    position: 'sticky', top: 0, zIndex: 5,
                    backdropFilter: 'blur(8px)',
                  }}>
                    <span style={{ fontSize: '1rem' }}>📅</span>
                    {formatDate(date)}
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: 'auto' }}>
                      {matches.length}场
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                    {matches.sort((a, b) => a.time_bj.localeCompare(b.time_bj)).map(match => {
                      const placeholder = isKnockoutPlaceholder(match);
                      const isSelected = selectedMatch?.match_id === match.match_id;
                      return (
                        <div
                          key={match.match_id}
                          onClick={() => handleMatchClick(match)}
                          style={{
                            display: 'flex', alignItems: 'center', gap: '0.5rem',
                            padding: '0.5rem 0.75rem',
                            background: isSelected ? 'rgba(59,130,246,0.1)' : 'rgba(255,255,255,0.02)',
                            borderRadius: '0.6rem',
                            border: `1px solid ${isSelected ? 'rgba(59,130,246,0.35)' : 'rgba(255,255,255,0.04)'}`,
                            cursor: placeholder ? 'default' : 'pointer',
                            transition: 'all 0.15s',
                            opacity: placeholder ? 0.45 : 1,
                          }}
                        >
                          <div style={{ textAlign: 'center', minWidth: '2.5rem' }}>
                            <div style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: '#fff' }}>
                              {match.time_bj}
                            </div>
                          </div>
                          {match.group && (
                            <div style={{
                              padding: '0.1rem 0.35rem', borderRadius: '0.25rem',
                              background: 'rgba(240,192,89,0.1)', color: '#f0c059',
                              fontSize: '9px', fontWeight: 600, flexShrink: 0,
                            }}>
                              {match.group}
                            </div>
                          )}
                          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                            <span style={{ flex: 1, textAlign: 'right', fontSize: 'var(--text-xs)', fontWeight: isSelected ? 700 : 500 }}>
                              {match.home_team_cn}
                            </span>
                            <span style={{ fontSize: '0.8rem', flexShrink: 0 }}>{getFlag(match.home_team)}</span>
                            <span style={{ fontSize: '10px', color: 'var(--text-muted)', flexShrink: 0 }}>VS</span>
                            <span style={{ fontSize: '0.8rem', flexShrink: 0 }}>{getFlag(match.away_team)}</span>
                            <span style={{ flex: 1, fontSize: 'var(--text-xs)', fontWeight: isSelected ? 700 : 500 }}>
                              {match.away_team_cn}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── RIGHT: Match Detail (60%) ── */}
        <div style={{
          flex: '1',
          maxHeight: 'calc(100vh - 280px)',
          overflowY: 'auto',
        }}>
          {selectedMatch ? (
            <MatchDetailPanel
              match={selectedMatch}
              detail={matchDetail}
              aiHighlights={aiHighlights}
              detailLoading={detailLoading}
              highlightsLoading={highlightsLoading}
              liveMatchId={liveMatchId}
              liveLookupDone={liveLookupDone}
            />
          ) : (
            <div style={{
              textAlign: 'center', padding: '4rem 2rem', color: 'var(--text-muted)',
            }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚽</div>
              <div style={{ fontSize: 'var(--text-base)', marginBottom: '0.5rem' }}>请从左侧列表选择一场比赛</div>
              <div style={{ fontSize: 'var(--text-xs)' }}>点击比赛即可查看详细信息、AI分析和实时数据</div>
            </div>
          )}
        </div>
      </div>
        </>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────
   Today View: Hero Card + Timeline
   ───────────────────────────────────────────── */

function TodayView({
  schedule, liveScoreboard, todayDate, onDateChange, onMatchClick,
}: {
  schedule: MatchScheduleResponse | null;
  liveScoreboard: LiveScoreboardResponse | null;
  todayDate: string;
  onDateChange: (d: string) => void;
  onMatchClick: (m: ScheduleMatch) => void;
}) {
  const [heroAnalysis, setHeroAnalysis] = useState<MatchAnalysisResponse | null>(null);

  if (!schedule) {
    return <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>加载中…</div>;
  }

  // Compute available dates from schedule
  const allDates = [...new Set(schedule.matches.map(m => m.date))].sort();
  const todayIdx = allDates.indexOf(todayDate);
  const displayDates = allDates.slice(Math.max(0, todayIdx - 3), Math.min(allDates.length, todayIdx + 4));

  // Matches for selected date
  const dayMatches = schedule.matches
    .filter(m => m.date === todayDate)
    .sort((a, b) => a.time_bj.localeCompare(b.time_bj));

  if (dayMatches.length === 0) {
    return (
      <div>
        <DateNav dates={displayDates} selected={todayDate} onChange={onDateChange} />
        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📅</div>
          <div>该日期暂无比赛</div>
        </div>
      </div>
    );
  }

  // Build live lookup map from ESPN data
  const liveMap = new Map<string, LiveMatchSummary>();
  if (liveScoreboard) {
    for (const m of liveScoreboard.today) {
      const key = `${m.home_team}|${m.away_team}`;
      liveMap.set(key, m);
    }
  }

  const getLiveFor = (m: ScheduleMatch): LiveMatchSummary | undefined => {
    for (const [key, live] of liveMap) {
      const hNorm = (s: string) => s.toLowerCase().replace(/\band\b/, '').replace(/[&\-.]/g, ' ').replace(/\s+/g, ' ').trim();
      const [lh, la] = key.split('|');
      if (hNorm(m.home_team).includes(hNorm(lh)) || hNorm(lh).includes(hNorm(m.home_team))) {
        if (hNorm(m.away_team).includes(hNorm(la)) || hNorm(la).includes(hNorm(m.away_team))) {
          return live;
        }
      }
    }
    return undefined;
  };

  // Find featured match: live first, then first match of day
  let heroMatch = dayMatches[0];
  let heroLive: LiveMatchSummary | undefined;
  let heroEspnId: string | undefined;
  for (const m of dayMatches) {
    const live = getLiveFor(m);
    if (live && (live.state === 'live' || live.state === 'halftime')) {
      heroMatch = m;
      heroLive = live;
      heroEspnId = live.match_id;
      break;
    }
  }
  if (!heroLive) {
    const fallback = getLiveFor(heroMatch);
    if (fallback) {
      heroLive = fallback;
      heroEspnId = fallback.match_id;
    }
  }

  // Fetch ESPN match ID via direct lookup if not found in scoreboard
  const [lookedUpEspnId, setLookedUpEspnId] = useState<string | null>(null);
  useEffect(() => {
    if (heroEspnId) { setLookedUpEspnId(heroEspnId); return; }
    let mounted = true;
    api.getLiveMatchLookup(heroMatch.home_team, heroMatch.away_team, heroMatch.date).then(res => {
      if (mounted && res.found && res.match_id) setLookedUpEspnId(res.match_id);
    }).catch(() => {});
    return () => { mounted = false; };
  }, [heroMatch.match_id, heroEspnId, heroMatch.home_team, heroMatch.away_team]);
  const effectiveEspnId = heroEspnId || lookedUpEspnId;

  // Fetch analysis for hero match
  useEffect(() => {
    if (!effectiveEspnId) { setHeroAnalysis(null); return; }
    let mounted = true;
    api.getLiveMatchAnalysis(effectiveEspnId).then(data => {
      if (mounted) setHeroAnalysis(data);
    }).catch(() => {});
    const t = setInterval(() => {
      api.getLiveMatchAnalysis(effectiveEspnId).then(data => {
        if (mounted) setHeroAnalysis(data);
      }).catch(() => {});
    }, 30000);
    return () => { mounted = false; clearInterval(t); };
  }, [effectiveEspnId]);

  const timelineMatches = dayMatches.filter(m => m.match_id !== heroMatch.match_id);

  return (
    <div>
      <DateNav dates={displayDates} selected={todayDate} onChange={onDateChange} />

      {/* Hero Card */}
      <HeroCard match={heroMatch} live={heroLive} analysis={heroAnalysis} onClick={() => onMatchClick(heroMatch)} />

      {/* Analysis Panel */}
      {heroAnalysis?.analysis && (heroAnalysis.analysis.type === 'halftime' || heroAnalysis.analysis.type === 'fulltime') && (
        <AnalysisPanel analysis={heroAnalysis.analysis} homeName={heroMatch.home_team_cn} awayName={heroMatch.away_team_cn} />
      )}

      {/* Timeline */}
      {timelineMatches.length > 0 && (
        <div style={{ marginTop: '1.5rem' }}>
          <div style={{
            fontSize: 'var(--text-sm)', fontWeight: 700, color: 'var(--text-muted)',
            marginBottom: '0.75rem', paddingLeft: '0.5rem',
          }}>
            当日其他比赛
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {timelineMatches.map(m => {
              const live = getLiveFor(m);
              return (
                <TimelineCard
                  key={m.match_id}
                  match={m}
                  live={live}
                  onClick={() => onMatchClick(m)}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function DateNav({ dates, selected, onChange }: { dates: string[]; selected: string; onChange: (d: string) => void }) {
  return (
    <div style={{
      display: 'flex', gap: '0.35rem', overflowX: 'auto',
      padding: '0.5rem 0 1rem', justifyContent: 'center',
    }}>
      {dates.map(d => {
        const dateObj = new Date(d + 'T00:00:00');
        const month = dateObj.getMonth() + 1;
        const day = dateObj.getDate();
        const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
        const wd = weekdays[dateObj.getDay()];
        const isToday = d === '2026-06-13';
        const isSelected = d === selected;
        return (
          <button
            key={d}
            onClick={() => onChange(d)}
            style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              padding: '0.5rem 0.9rem', borderRadius: '0.6rem',
              border: isSelected ? '1px solid #3b82f6' : '1px solid #333',
              background: isSelected ? 'rgba(59,130,246,0.12)' : 'rgba(255,255,255,0.02)',
              color: isSelected ? '#3b82f6' : 'var(--text-muted)',
              cursor: 'pointer', transition: 'all 0.15s',
              minWidth: '3.5rem',
            }}
          >
            <span style={{ fontSize: '10px', opacity: 0.7 }}>{wd}</span>
            <span style={{ fontSize: '1.1rem', fontWeight: 700 }}>
              {month}/{day}
            </span>
            {isToday && (
              <span style={{ fontSize: '9px', color: '#ef4444', fontWeight: 600 }}>今天</span>
            )}
          </button>
        );
      })}
    </div>
  );
}

function HeroCard({ match, live, analysis, onClick }: { match: ScheduleMatch; live?: LiveMatchSummary; analysis?: MatchAnalysisResponse | null; onClick: () => void }) {
  const state = live?.state || analysis?.status?.state;
  const isLive = state === 'live' || state === 'halftime';
  const isFinished = state === 'finished';
  const hScore = live?.home_score ?? analysis?.home?.score ?? 0;
  const aScore = live?.away_score ?? analysis?.away?.score ?? 0;
  const hasScore = live || (analysis?.home?.score !== undefined && analysis?.away?.score !== undefined);
  const scoreDisplay = hasScore ? `${hScore} - ${aScore}` : null;
  const clockDisplay = live?.clock || analysis?.status?.clock || '';

  // Recent key events (last 3)
  const recentEvents = analysis?.events?.slice(-3).reverse() || [];

  // Key stats from analysis
  const keyStats = analysis?.analysis?.key_stats || [];

  // Short stat bars for live matches
  const hasStats = analysis?.statistics && (analysis.statistics as any).home?.stats;

  return (
    <div
      onClick={onClick}
      style={{
        cursor: 'pointer',
        borderRadius: '1rem',
        overflow: 'hidden',
        border: isLive ? '1px solid rgba(239,68,68,0.4)' : '1px solid rgba(255,255,255,0.08)',
        background: isLive
          ? 'linear-gradient(135deg, rgba(239,68,68,0.12), rgba(30,10,10,0.9), rgba(59,130,246,0.08))'
          : isFinished
            ? 'linear-gradient(135deg, rgba(100,116,139,0.1), rgba(20,20,20,0.9))'
            : 'linear-gradient(135deg, rgba(240,192,89,0.08), rgba(15,15,25,0.9), rgba(59,130,246,0.06))',
        transition: 'all 0.2s',
      }}
    >
      {/* Status bar */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '0.6rem 1.25rem',
        background: 'rgba(0,0,0,0.3)',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {isLive ? (
            <span style={{
              background: '#ef4444', color: '#fff', padding: '0.15rem 0.6rem',
              borderRadius: '1rem', fontSize: '11px', fontWeight: 800,
              animation: 'pulse 1.5s infinite',
            }}>
              🔴 直播中
            </span>
          ) : isFinished ? (
            <span style={{
              background: '#64748b', color: '#fff', padding: '0.15rem 0.6rem',
              borderRadius: '1rem', fontSize: '11px', fontWeight: 700,
            }}>
              🏁 已结束
            </span>
          ) : (
            <span style={{
              background: 'rgba(240,192,89,0.15)', color: '#f0c059',
              padding: '0.15rem 0.6rem', borderRadius: '1rem',
              fontSize: '11px', fontWeight: 700,
            }}>
              📋 即将开始
            </span>
          )}
          {isLive && clockDisplay && (
            <span style={{ color: '#ef4444', fontSize: 'var(--text-sm)', fontWeight: 700 }}>
              {clockDisplay}&apos;
            </span>
          )}
          {analysis?.analysis?.momentum && (
            <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
              {analysis.analysis.momentum}
            </span>
          )}
        </div>
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          {match.venue}
        </div>
      </div>

      {/* Main content */}
      <div style={{ padding: '2rem 1.5rem 0.5rem', textAlign: 'center' }}>
        {/* Teams + Score */}
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ flex: 1, textAlign: 'center' }}>
            <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>{getFlag(match.home_team)}</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>{match.home_team_cn}</div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{match.home_team}</div>
          </div>

          <div style={{ flexShrink: 0 }}>
            {scoreDisplay ? (
              <div style={{
                fontSize: '2.5rem', fontWeight: 900, color: '#fff',
                background: 'rgba(255,255,255,0.06)', padding: '0.5rem 1.5rem',
                borderRadius: '0.75rem', letterSpacing: '0.1em',
              }}>
                {scoreDisplay}
              </div>
            ) : (
              <div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f0c059' }}>VS</div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  {match.time_bj}
                </div>
              </div>
            )}
          </div>

          <div style={{ flex: 1, textAlign: 'center' }}>
            <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>{getFlag(match.away_team)}</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>{match.away_team_cn}</div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{match.away_team}</div>
          </div>
        </div>

        {/* Match info footer */}
        <div style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
          <InfoBadge label="日期" value={match.date} />
          <InfoBadge label="时间" value={`北京时间 ${match.time_bj}`} />
          {match.group && <InfoBadge label="小组" value={`${match.group}组 第${match.round}轮`} />}
          {match.stage !== 'group' && (
            <InfoBadge label="阶段" value={match.stage === 'final' ? '决赛' : match.stage === 'semi_final' ? '半决赛' : match.stage === 'quarter_final' ? '1/4决赛' : match.stage === 'round_of_16' ? '1/8决赛' : '1/16决赛'} />
          )}
          <InfoBadge label="球场" value={`${match.venue}, ${match.city}`} />
        </div>

        {match.note && (
          <div style={{ marginTop: '1rem', fontSize: 'var(--text-xs)', color: '#f0c059', fontWeight: 600 }}>
            ⭐ {match.note}
          </div>
        )}
      </div>

      {/* Live events ticker */}
      {recentEvents.length > 0 && (
        <div style={{
          margin: '0.75rem 1.25rem',
          padding: '0.5rem 0.75rem',
          background: 'rgba(0,0,0,0.25)',
          borderRadius: '0.5rem',
          display: 'flex', flexDirection: 'column', gap: '0.3rem',
          maxHeight: '8rem', overflowY: 'auto',
        }}>
          {recentEvents.map((ev: LiveEvent, i: number) => {
            const icon = ev.type === 'goal' ? '⚽' : ev.type === 'yellow_card' ? '🟨' : ev.type === 'red_card' ? '🟥' : ev.type === 'substitution' ? '🔄' : '';
            return (
              <div key={i} style={{ display: 'flex', gap: '0.4rem', fontSize: '11px', alignItems: 'flex-start' }}>
                <span style={{ flexShrink: 0 }}>{icon}</span>
                <span style={{ color: '#94a3b8', fontWeight: 600, minWidth: '2rem', flexShrink: 0 }}>{ev.minute}&apos;</span>
                <span style={{ color: '#e2e8f0', lineHeight: 1.4 }}>
                  {ev.description_cn || ev.text}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Mini stat bars for live/finished matches */}
      {hasStats && (isLive || isFinished) && (
        <div style={{
          margin: '0.75rem 1.25rem',
          padding: '0.5rem 0.75rem',
          display: 'flex', gap: '1rem', justifyContent: 'center',
          fontSize: '11px',
        }}>
          {keyStats.slice(0, 3).map((s, i) => (
            <span key={i} style={{ color: 'var(--text-muted)' }}>{s}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function InfoBadge({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{label}</span>
      <span style={{ fontSize: 'var(--text-xs)', color: '#cbd5e1', fontWeight: 600 }}>{value}</span>
    </div>
  );
}

function AnalysisPanel({ analysis, homeName, awayName }: { analysis: MatchAnalysis; homeName: string; awayName: string }) {
  const isHalftime = analysis.type === 'halftime';
  return (
    <div style={{
      marginTop: '1.25rem',
      padding: '1.25rem',
      background: isHalftime
        ? 'linear-gradient(135deg, rgba(245,158,11,0.06), rgba(30,20,10,0.9))'
        : 'linear-gradient(135deg, rgba(100,116,139,0.08), rgba(20,20,25,0.9))',
      borderRadius: '0.75rem',
      border: isHalftime ? '1px solid rgba(245,158,11,0.2)' : '1px solid rgba(255,255,255,0.06)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <span style={{ fontSize: '1.1rem' }}>
          {isHalftime ? '⏸️' : '🏁'}
        </span>
        <span style={{
          fontSize: 'var(--text-sm)', fontWeight: 700,
          color: isHalftime ? '#f59e0b' : '#94a3b8',
        }}>
          {isHalftime ? '中场分析' : '全场分析'}
        </span>
        <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
          {analysis.momentum}
        </span>
      </div>

      {/* Summary */}
      <div style={{
        fontSize: 'var(--text-sm)', fontWeight: 600, color: '#e2e8f0',
        marginBottom: '0.75rem', lineHeight: 1.6,
      }}>
        {analysis.summary}
      </div>

      {/* Analysis text */}
      {analysis.analysis && (
        <div style={{
          fontSize: 'var(--text-xs)', color: '#cbd5e1',
          lineHeight: 1.8, whiteSpace: 'pre-wrap',
          marginBottom: '0.75rem',
        }}>
          {analysis.analysis}
        </div>
      )}

      {/* Key stats */}
      {analysis.key_stats.length > 0 && (
        <div style={{
          display: 'flex', gap: '1rem', flexWrap: 'wrap',
          padding: '0.5rem 0.75rem',
          background: 'rgba(255,255,255,0.03)',
          borderRadius: '0.5rem',
          marginBottom: '0.5rem',
        }}>
          {analysis.key_stats.map((s, i) => (
            <span key={i} style={{ fontSize: '10px', color: '#94a3b8', fontWeight: 500 }}>{s}</span>
          ))}
        </div>
      )}

      {/* Star performers */}
      {analysis.star_performers.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '10px' }}>
          <span style={{ color: 'var(--text-muted)' }}>关键球员：</span>
          {analysis.star_performers.map((p, i) => (
            <span key={i} style={{
              padding: '0.1rem 0.5rem', borderRadius: '0.25rem',
              background: 'rgba(240,192,89,0.1)', color: '#f0c059',
              fontWeight: 600,
            }}>
              ⭐ {p}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function TimelineCard({ match, live, onClick }: { match: ScheduleMatch; live?: LiveMatchSummary; onClick: () => void }) {
  const isLive = live && (live.state === 'live' || live.state === 'halftime');
  const isFinished = live && live.state === 'finished';
  const hasEspn = !!live;

  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: '1rem',
        padding: '0.75rem 1rem',
        background: isFinished ? 'rgba(100,116,139,0.04)' : 'rgba(255,255,255,0.02)',
        borderRadius: '0.6rem',
        border: isLive ? '1px solid rgba(239,68,68,0.25)'
          : isFinished ? '1px solid rgba(100,116,139,0.2)'
          : '1px solid rgba(255,255,255,0.04)',
        cursor: 'pointer',
        transition: 'all 0.15s',
      }}
    >
      {/* Time column */}
      <div style={{ minWidth: '3.5rem', textAlign: 'center' }}>
        {isLive ? (
          <span style={{
            background: '#ef4444', color: '#fff', padding: '0.1rem 0.45rem',
            borderRadius: '0.25rem', fontSize: '10px', fontWeight: 700,
            animation: 'pulse 1.5s infinite', display: 'inline-block',
          }}>
            🔴 LIVE
          </span>
        ) : isFinished ? (
          <div>
            <span style={{
              fontSize: 'var(--text-sm)', fontWeight: 800, color: '#cbd5e1',
              display: 'block',
            }}>
              {live?.home_score}-{live?.away_score}
            </span>
            <span style={{
              fontSize: '9px', color: '#64748b', fontWeight: 600,
              display: 'block', marginTop: '0.1rem',
            }}>
              已结束
            </span>
          </div>
        ) : (
          <span style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: '#fff' }}>
            {match.time_bj}
          </span>
        )}
        {isLive && live?.clock && (
          <div style={{ fontSize: '10px', color: '#ef4444', marginTop: '0.15rem', fontWeight: 600 }}>
            {live.clock}&apos;
          </div>
        )}
      </div>

      {/* Match info */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontSize: '0.85rem' }}>{getFlag(match.home_team)}</span>
        <span style={{ fontSize: 'var(--text-xs)', fontWeight: isFinished ? 500 : 600, color: isFinished ? '#94a3b8' : '#e2e8f0' }}>
          {match.home_team_cn}
        </span>
        {isLive || isFinished ? (
          <span style={{
            fontSize: 'var(--text-xs)', fontWeight: 800, color: '#fff',
            background: isFinished ? 'rgba(100,116,139,0.15)' : 'rgba(255,255,255,0.08)',
            padding: '0.1rem 0.45rem', borderRadius: '0.25rem',
          }}>
            {live?.home_score} - {live?.away_score}
          </span>
        ) : (
          <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>VS</span>
        )}
        <span style={{ fontSize: 'var(--text-xs)', fontWeight: isFinished ? 500 : 600, color: isFinished ? '#94a3b8' : '#e2e8f0' }}>
          {match.away_team_cn}
        </span>
        <span style={{ fontSize: '0.85rem' }}>{getFlag(match.away_team)}</span>

        {/* Right side info */}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.4rem', flexShrink: 0 }}>
          {hasEspn && isFinished && (
            <span style={{
              fontSize: '9px', color: '#64748b', fontWeight: 500,
              padding: '0.1rem 0.3rem', borderRadius: '0.2rem',
              background: 'rgba(100,116,139,0.1)',
            }}>
              📡 ESPN
            </span>
          )}
          {match.group && (
            <span style={{
              padding: '0.1rem 0.35rem', borderRadius: '0.25rem',
              background: 'rgba(240,192,89,0.08)', color: '#f0c059',
              fontSize: '9px', fontWeight: 600,
            }}>
              {match.group}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   Right Panel: Match Detail + AI + Live Data
   ───────────────────────────────────────────── */

function MatchDetailPanel({
  match, detail, aiHighlights, detailLoading, highlightsLoading,
  liveMatchId, liveLookupDone,
}: {
  match: ScheduleMatch;
  detail: MatchDetailResponse | null;
  aiHighlights: string | null;
  detailLoading: boolean;
  highlightsLoading: boolean;
  liveMatchId: string | null;
  liveLookupDone: boolean;
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Guide prompt */}
      <div style={{
        fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center',
        padding: '0.3rem 0', borderBottom: '1px solid rgba(255,255,255,0.04)',
      }}>
        💡 点击左侧比赛卡片切换查看详情
      </div>

      {/* ── Live Match Panel ── */}
      {liveMatchId && (
        <LiveMatchPanel matchId={liveMatchId} />
      )}

      {/* Match header */}
      <div style={{
        textAlign: 'center', padding: '1.25rem',
        background: 'rgba(255,255,255,0.02)',
        borderRadius: '0.75rem',
        border: '1px solid rgba(255,255,255,0.06)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '2.5rem' }}>{getFlag(match.home_team)}</span>
          <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>{match.home_team_cn}</span>
          <span style={{ fontSize: 'var(--text-lg)', fontWeight: 800, color: '#f0c059' }}>VS</span>
          <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>{match.away_team_cn}</span>
          <span style={{ fontSize: '2.5rem' }}>{getFlag(match.away_team)}</span>
        </div>
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          {match.date} 北京时间 {match.time_bj} · {match.venue} · {match.city}
          {match.group && ` · ${match.group}组 第${match.round}轮`}
          {match.stage !== 'group' && (
            ` · ${match.stage === 'final' ? '决赛' : match.stage === 'semi_final' ? '半决赛' : match.stage === 'quarter_final' ? '1/4决赛' : match.stage === 'round_of_16' ? '1/8决赛' : match.stage === 'round_of_32' ? '1/16决赛' : ''}`
          )}
        </div>
        {match.note && (
          <div style={{ marginTop: '0.5rem', fontSize: 'var(--text-xs)', color: '#f0c059', fontWeight: 600 }}>
            ⭐ {match.note}
          </div>
        )}
      </div>

      {/* Detail + Live Loading State */}
      {detailLoading ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>
          正在加载比赛数据…
        </div>
      ) : (
        <>
          {/* Live data status (when no ESPN match found but lookup is done) */}
          {liveLookupDone && !liveMatchId && (
            <div style={{
              padding: '0.5rem 0.75rem', borderRadius: '0.5rem',
              background: 'rgba(100,116,139,0.08)', border: '1px solid rgba(100,116,139,0.15)',
              fontSize: '11px', color: '#94a3b8', textAlign: 'center',
            }}>
              📡 该比赛暂无实时数据（比赛日将自动接入ESPN）
            </div>
          )}

          {/* Detail grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <DetailCard title="历史交锋记录">
              <H2HSection h2h={detail?.h2h ?? null} homeCn={match.home_team_cn} awayCn={match.away_team_cn} />
            </DetailCard>

            <DetailCard title="球队档案">
              <TeamProfileSection profiles={detail?.team_profiles ?? null} homeCn={match.home_team_cn} awayCn={match.away_team_cn} />
            </DetailCard>

            <DetailCard title={`${match.home_team_cn} 近期战绩`}>
              <RecentFormSection recent={detail?.home_recent ?? null} team={match.home_team} teamCn={match.home_team_cn} />
            </DetailCard>

            <DetailCard title={`${match.away_team_cn} 近期战绩`}>
              <RecentFormSection recent={detail?.away_recent ?? null} team={match.away_team} teamCn={match.away_team_cn} />
            </DetailCard>
          </div>

          {/* AI Highlights */}
          <DetailCard title="比赛看点 & 关注点" fullWidth>
            {highlightsLoading ? (
              <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', padding: '1rem', textAlign: 'center' }}>
                AI 正在分析比赛看点…
              </div>
            ) : aiHighlights ? (
              <div style={{ fontSize: 'var(--text-sm)', lineHeight: 1.8, whiteSpace: 'pre-wrap', padding: '0.5rem' }}>
                {aiHighlights}
              </div>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', textAlign: 'center', padding: '1rem' }}>
                正在获取AI分析…
              </div>
            )}
          </DetailCard>
        </>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────
   Sub-components
   ───────────────────────────────────────────── */

function DetailCard({ title, children, fullWidth }: { title: string; children: React.ReactNode; fullWidth?: boolean }) {
  return (
    <div style={{
      padding: '0.75rem 1rem',
      background: 'rgba(255,255,255,0.02)',
      borderRadius: '0.5rem',
      border: '1px solid rgba(255,255,255,0.05)',
      gridColumn: fullWidth ? '1 / -1' : undefined,
    }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.5rem', fontWeight: 600 }}>
        {title}
      </div>
      {children}
    </div>
  );
}

function H2HSection({ h2h, homeCn, awayCn }: { h2h: H2HData | null; homeCn: string; awayCn: string }) {
  if (!h2h || h2h.total_matches === 0) {
    return <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>暂无两队历史交锋记录</div>;
  }
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-around', marginBottom: '0.5rem' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: '#3b82f6' }}>{h2h.home_wins}</div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{homeCn}胜</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: '#eab308' }}>{h2h.draws}</div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>平局</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: '#ef4444' }}>{h2h.away_wins}</div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{awayCn}胜</div>
        </div>
      </div>
      <div style={{ textAlign: 'center', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
        共交手 {h2h.total_matches} 次
      </div>
      {h2h.matches.length > 0 && (
        <div style={{ marginTop: '0.5rem', fontSize: '10px', maxHeight: '6rem', overflowY: 'auto' }}>
          {h2h.matches.slice(-5).reverse().map((m, i) => (
            <div key={i} style={{ padding: '0.15rem 0', borderBottom: '1px solid rgba(255,255,255,0.03)', color: 'var(--text-muted)' }}>
              {m.date} {m.home_team} {m.home_score}-{m.away_score} {m.away_team}
              {m.tournament && ` (${m.tournament})`}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TeamProfileSection({ profiles, homeCn, awayCn }: { profiles: { home: { playing_style?: string; strength?: string; weakness?: string; key_formation?: string } | null; away: { playing_style?: string; strength?: string; weakness?: string; key_formation?: string } | null } | null; homeCn: string; awayCn: string }) {
  if (!profiles) {
    return <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>暂无球队档案</div>;
  }
  return (
    <div style={{ display: 'flex', gap: '1rem' }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: '0.3rem' }}>{homeCn}</div>
        {profiles.home ? (
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            {profiles.home.playing_style && <div>风格：{profiles.home.playing_style}</div>}
            {profiles.home.key_formation && <div>阵型：{profiles.home.key_formation}</div>}
            {profiles.home.strength && <div style={{ color: '#10b981' }}>优势：{profiles.home.strength}</div>}
            {profiles.home.weakness && <div style={{ color: '#ef4444' }}>弱点：{profiles.home.weakness}</div>}
          </div>
        ) : <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>暂无档案</div>}
      </div>
      <div style={{ width: 1, background: 'rgba(255,255,255,0.06)' }} />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: '0.3rem' }}>{awayCn}</div>
        {profiles.away ? (
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            {profiles.away.playing_style && <div>风格：{profiles.away.playing_style}</div>}
            {profiles.away.key_formation && <div>阵型：{profiles.away.key_formation}</div>}
            {profiles.away.strength && <div style={{ color: '#10b981' }}>优势：{profiles.away.strength}</div>}
            {profiles.away.weakness && <div style={{ color: '#ef4444' }}>弱点：{profiles.away.weakness}</div>}
          </div>
        ) : <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>暂无档案</div>}
      </div>
    </div>
  );
}

function RecentFormSection({ recent, teamCn }: { recent: RecentMatch[] | null; team: string; teamCn: string }) {
  if (!recent || recent.length === 0) {
    return <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>暂无近期比赛数据</div>;
  }
  const wins = recent.filter(r => r.result === 'W').length;
  const draws = recent.filter(r => r.result === 'D').length;
  const losses = recent.filter(r => r.result === 'L').length;
  const resultColors: Record<string, string> = { W: '#10b981', D: '#eab308', L: '#ef4444' };
  const resultLabels: Record<string, string> = { W: '胜', D: '平', L: '负' };
  return (
    <div>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', fontSize: 'var(--text-xs)' }}>
        <span style={{ color: '#10b981' }}>{wins}胜</span>
        <span style={{ color: '#eab308' }}>{draws}平</span>
        <span style={{ color: '#ef4444' }}>{losses}负</span>
        <span style={{ color: 'var(--text-muted)' }}>· 近{recent.length}场</span>
      </div>
      <div style={{ display: 'flex', gap: '0.15rem', marginBottom: '0.5rem' }}>
        {recent.slice(0, 10).map((r, i) => (
          <div key={i} style={{
            width: '1.4rem', height: '1.4rem', borderRadius: '0.25rem',
            background: resultColors[r.result] || '#555',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '10px', fontWeight: 700, color: '#fff',
          }} title={`${r.date}: ${r.home_team} ${r.home_score}-${r.away_score} ${r.away_team}`}>
            {resultLabels[r.result]}
          </div>
        ))}
      </div>
      <div style={{ fontSize: '10px', maxHeight: '8rem', overflowY: 'auto' }}>
        {recent.slice(0, 10).map((r, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.15rem 0', borderBottom: '1px solid rgba(255,255,255,0.02)', color: 'var(--text-muted)' }}>
            <span>{r.date}</span>
            <span>
              {r.is_home ? '🏠' : '✈️'} {r.home_team} {r.home_score}-{r.away_score} {r.away_team}
            </span>
            <span style={{ color: resultColors[r.result], fontWeight: 600 }}>
              {resultLabels[r.result]}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
