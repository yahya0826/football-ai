'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import api, { DailySummaryResponse, InjuriesResponse, TeamInjuryIntel } from '@/lib/api';

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

function getFlag(team: string): string {
  return FLAGS[team] || '🏳️';
}

function getStatusBadge(status: string, statusCn: string): { bg: string; color: string } {
  switch (status) {
    case 'out': return { bg: 'rgba(239,68,68,0.12)', color: '#ef4444' };
    case 'doubtful': return { bg: 'rgba(245,158,11,0.12)', color: '#f59e0b' };
    case 'questionable': return { bg: 'rgba(245,158,11,0.1)', color: '#f59e0b' };
    case 'game-time decision': return { bg: 'rgba(168,85,247,0.12)', color: '#a855f7' };
    case 'probable': return { bg: 'rgba(34,197,94,0.12)', color: '#22c55e' };
    default: return { bg: 'rgba(148,163,184,0.1)', color: '#94a3b8' };
  }
}

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch {
    return iso;
  }
}

// ── 赛程情报：每日总结文章 ──────────────────────────────

function DailySummaryTab({ data, loading }: { data: DailySummaryResponse | null; loading: boolean }) {
  const [refreshing, setRefreshing] = useState(false);

  async function handleRefresh() {
    setRefreshing(true);
    window.location.reload();
  }

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!data) {
    return <p className="text-center py-16" style={{ color: 'var(--text-muted)' }}>暂无数据</p>;
  }

  // 文章尚未生成（比赛未全部结束）
  if (!data.generated) {
    const total = data.matches_total ?? data.matches_count ?? 0;
    const completed = data.matches_completed ?? 0;
    return (
      <div>
        <div className="card text-center py-12">
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📝</div>
          <h2 className="text-xl font-bold mb-3">{data.title || '比赛日总结'}</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
            今日 {total} 场比赛，已完成 {completed}/{total}
          </p>
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="animate-spin w-4 h-4 border-2 border-primary border-t-transparent rounded-full" />
            <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
              所有比赛结束后将自动生成总结文章
            </span>
          </div>
          {/* 进度条 */}
          <div style={{
            maxWidth: 300, margin: '0 auto', height: 6,
            background: 'var(--border)', borderRadius: 3, overflow: 'hidden'
          }}>
            <div style={{
              height: '100%', width: `${total > 0 ? (completed / total) * 100 : 0}%`,
              background: 'var(--primary)', borderRadius: 3, transition: 'width 0.5s'
            }} />
          </div>
          <p className="text-xs mt-3" style={{ color: 'var(--text-muted)' }}>
            系统每 15 分钟自动检测一次
          </p>
        </div>

        {/* 历史已生成总结 */}
        <div className="mt-8">
          <h3 className="font-bold mb-3" style={{ color: 'var(--text-muted)' }}>
            历史比赛总结
          </h3>
          <PastSummaries />
        </div>
      </div>
    );
  }

  // 已生成 → 渲染 Markdown 文章
  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-xl font-bold">{data.title}</h2>
          {data.generated_at && (
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
              生成于 {formatTimestamp(data.generated_at)}
            </span>
          )}
        </div>
        <button onClick={handleRefresh} className="btn btn-secondary text-sm" disabled={refreshing}>
          {refreshing ? '刷新中...' : '↻ 刷新'}
        </button>
      </div>

      {/* 比赛快览卡片 */}
      {data.matches && data.matches.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          {data.matches.map((m, i) => (
            <div key={i} className="card" style={{ padding: '0.5rem 0.75rem', minWidth: 180 }}>
              <div className="flex items-center gap-1 mb-1">
                <span>{getFlag(m.home_team)}</span>
                <span className="text-sm font-bold">{m.home_team_cn}</span>
              </div>
              <div className="flex items-center gap-1">
                <span>{getFlag(m.away_team)}</span>
                <span className="text-sm font-bold">{m.away_team_cn}</span>
              </div>
              <div className="text-right mt-1">
                <span className="badge badge-primary">{m.score}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* AI 文章正文 */}
      {data.article ? (
        <div className="card">
          <div
            className="prose"
            style={{ whiteSpace: 'pre-wrap', lineHeight: 1.9, fontSize: '0.95rem' }}
          >
            {data.article}
          </div>
        </div>
      ) : (
        <p className="text-center py-8" style={{ color: 'var(--text-muted)' }}>文章内容生成中...</p>
      )}

      <div className="text-center mt-4">
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
          本文由 AI 自动生成，仅供参考
        </span>
      </div>

      {/* 历史总结 */}
      <div className="mt-8">
        <h3 className="font-bold mb-3" style={{ color: 'var(--text-muted)' }}>
          历史比赛总结
        </h3>
        <PastSummaries />
      </div>
    </div>
  );
}

function PastSummaries() {
  return (
    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
      历史总结将自动保存在系统中，可通过日期切换查看
    </p>
  );
}

// ── 临哨快讯：伤病情报 + 预测首发 ──────────────────────────

function BreakingTab({ data, loading }: { data: InjuriesResponse | null; loading: boolean }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    // 有伤病的队伍默认展开
    if (data?.teams) {
      const expandedMap: Record<string, boolean> = {};
      Object.entries(data.teams).forEach(([key, team]) => {
        if (team.injuries && team.injuries.length > 0) {
          expandedMap[key] = true;
        }
      });
      setExpanded(expandedMap);
    }
  }, [data]);

  function toggleTeam(key: string) {
    setExpanded(prev => ({ ...prev, [key]: !prev[key] }));
  }

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!data || !data.teams || Object.keys(data.teams).length === 0) {
    return (
      <div className="text-center py-16">
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏥</div>
        <p style={{ color: 'var(--text-muted)' }}>暂无伤病情报数据</p>
        <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
          数据将在赛前48小时开始自动更新
        </p>
      </div>
    );
  }

  const teams = Object.entries(data.teams);
  // 有伤病的排前面
  teams.sort(([, a], [, b]) => (b.injuries?.length || 0) - (a.injuries?.length || 0));

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">临哨快讯</h2>
        {data.last_updated && (
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            更新于 {formatTimestamp(data.last_updated)}
          </span>
        )}
      </div>

      <div className="space-y-3">
        {teams.map(([key, team]) => (
          <div key={key} className="card" style={{ cursor: 'pointer' }} onClick={() => toggleTeam(key)}>
            {/* 队伍头部 */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">{getFlag(key)}</span>
                <span className="font-bold">{team.name_cn || key}</span>
                {team.injuries && team.injuries.length > 0 && (
                  <span className="badge" style={{
                    background: 'rgba(239,68,68,0.12)', color: '#ef4444', fontSize: '0.7rem'
                  }}>
                    {team.injuries.length}人伤病
                  </span>
                )}
              </div>
              <span style={{
                transform: expanded[key] ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s',
                color: 'var(--text-muted)',
                fontSize: '0.8rem',
              }}>
                ▼
              </span>
            </div>

            {/* 展开详情 */}
            {expanded[key] && (
              <div className="mt-3 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
                {/* 预测阵容 */}
                {team.predicted_lineup?.formation && (
                  <div className="mb-3">
                    <span className="text-xs font-bold" style={{ color: 'var(--text-muted)' }}>
                      📋 预测阵型：
                    </span>
                    <span className="badge badge-secondary ml-1">
                      {team.predicted_lineup.formation}
                    </span>
                    {team.predicted_lineup.players && team.predicted_lineup.players.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {(team.predicted_lineup.players_cn || team.predicted_lineup.players).slice(0, 11).map((p, i) => (
                          <span key={i} className="text-xs" style={{
                            padding: '0.1rem 0.4rem', borderRadius: '0.25rem',
                            background: 'var(--card-bg)', border: '1px solid var(--border)'
                          }}>
                            {p}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 伤病情报 */}
                {team.injuries && team.injuries.length > 0 ? (
                  <div className="mb-3">
                    <span className="text-xs font-bold" style={{ color: 'var(--text-muted)' }}>
                      🏥 伤病情报：
                    </span>
                    <div className="mt-1 space-y-1">
                      {team.injuries.map((inj, i) => {
                        const badge = getStatusBadge(inj.status, inj.status_cn);
                        return (
                          <div key={i} className="flex items-start gap-2 text-sm" style={{
                            padding: '0.3rem 0.5rem', borderRadius: '0.25rem',
                            background: 'var(--card-bg)'
                          }}>
                            <span style={{ minWidth: 'fit-content' }}>
                              {inj.player_cn || inj.player}
                            </span>
                            <span style={{
                              padding: '0.05rem 0.35rem', borderRadius: '0.2rem',
                              background: badge.bg, color: badge.color,
                              fontSize: '0.7rem', fontWeight: 600, whiteSpace: 'nowrap',
                            }}>
                              {inj.status_cn}
                            </span>
                            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                              {inj.detail}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="mb-3">
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                      🏥 无伤病报告
                    </span>
                  </div>
                )}

                {/* 近期状态 */}
                {team.recent_form && (
                  <div className="mb-2">
                    <span className="text-xs font-bold" style={{ color: 'var(--text-muted)' }}>
                      📊 近期状态：
                    </span>
                    <span className="text-xs ml-1">{team.recent_form}</span>
                  </div>
                )}

                {/* 比分预测 */}
                {team.score_prediction_cn && (
                  <div>
                    <span className="text-xs font-bold" style={{ color: 'var(--text-muted)' }}>
                      🔮 赛前预测：
                    </span>
                    <span className="text-xs ml-1">{team.score_prediction_cn}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="text-center mt-6">
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
          数据来源：公开赛前报道 | 自动更新 | 赛前1小时以 ESPN 确认首发为准
        </span>
      </div>
    </div>
  );
}

// ── 哨后复盘（保留现状）──────────────────────────────────

function ReviewTab() {
  return (
    <div className="text-center py-12">
      <h2 className="text-xl font-bold mb-4">哨后复盘</h2>
      <p className="mb-6" style={{ color: 'var(--text-muted)' }}>
        哨后复盘将验证赛前情报变量是否真正影响了比赛走向
      </p>
      <Link href="/matches" className="btn btn-primary">
        前往比赛列表查看复盘
      </Link>
    </div>
  );
}

// ── 主页面 ────────────────────────────────────────────

export default function IntelligencePage() {
  const [activeTab, setActiveTab] = useState('schedule');
  const [dailySummary, setDailySummary] = useState<DailySummaryResponse | null>(null);
  const [injuries, setInjuries] = useState<InjuriesResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        // 并行加载赛程情报和临哨快讯
        const [summaryData, injuriesData] = await Promise.all([
          api.getDailySummary(),
          api.getInjuryIntel(),
        ]);
        setDailySummary(summaryData);
        setInjuries(injuriesData);
      } catch (err) {
        console.error('Failed to load intelligence data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="min-h-screen py-4 md:py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="page-title text-3xl mb-2">哨前情报站</h1>
          <p className="text-lg" style={{ color: 'var(--text-muted)' }}>
            哨响之前，看懂比赛变量
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {[
            ['schedule', '赛程情报'],
            ['breaking', '临哨快讯'],
            ['review', '哨后复盘'],
          ].map(([key, label]) => (
            <button
              key={key}
              className={`tab ${activeTab === key ? 'active' : ''}`}
              onClick={() => setActiveTab(key)}
            >
              {label}
            </button>
          ))}
        </div>

        {/* 赛程情报 */}
        {activeTab === 'schedule' && (
          <DailySummaryTab data={dailySummary} loading={loading} />
        )}

        {/* 临哨快讯 */}
        {activeTab === 'breaking' && (
          <BreakingTab data={injuries} loading={loading} />
        )}

        {/* 哨后复盘 */}
        {activeTab === 'review' && <ReviewTab />}
      </div>
    </div>
  );
}
