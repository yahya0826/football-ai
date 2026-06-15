'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import api, { InjuriesResponse } from '@/lib/api';

const FLAGS: Record<string, string> = {
  'Argentina': '🇦🇷', 'Brazil': '🇧🇷', 'Germany': '🇩🇪', 'Spain': '🇪🇸',
  'France': '🇫🇷', 'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'Netherlands': '🇳🇱', 'Portugal': '🇵🇹',
  'Belgium': '🇧🇪', 'Italy': '🇮🇹', 'Croatia': '🇭🇷', 'Uruguay': '🇺🇾',
};

function getFlag(team: string): string {
  return FLAGS[team] || '🏳️';
}

function getStatusBadge(status: string): { bg: string; color: string } {
  switch (status) {
    case 'out': return { bg: 'rgba(239,68,68,0.12)', color: '#ef4444' };
    case 'doubtful': return { bg: 'rgba(245,158,11,0.12)', color: '#f59e0b' };
    case 'probable': return { bg: 'rgba(34,197,94,0.12)', color: '#22c55e' };
    default: return { bg: 'rgba(148,163,184,0.1)', color: '#94a3b8' };
  }
}

export default function BreakingNewsPage() {
  const [data, setData] = useState<InjuriesResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const result = await api.getInjuryIntel();
        setData(result);
      } catch (err) {
        console.error('Failed to load injury intel:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  const teams = data?.teams ? Object.entries(data.teams) : [];

  return (
    <div className="min-h-screen py-4 md:py-8">
      <div className="max-w-4xl mx-auto px-4">
        <Link href="/intelligence" className="inline-flex items-center gap-2 mb-6" style={{ color: 'var(--text-muted)' }}>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          返回情报站
        </Link>

        <h1 className="page-title text-3xl mb-8 text-center">临哨快讯</h1>

        {data?.last_updated && (
          <p className="text-center text-sm mb-6" style={{ color: 'var(--text-muted)' }}>
            最后更新：{new Date(data.last_updated).toLocaleString('zh-CN')}
          </p>
        )}

        <div className="space-y-4">
          {teams.map(([key, team]) => (
            <div key={key} className="card">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">{getFlag(key)}</span>
                <h2 className="font-bold text-lg">{team.name_cn || key}</h2>
                {team.injuries && team.injuries.length > 0 && (
                  <span className="badge" style={{ background: 'rgba(239,68,68,0.12)', color: '#ef4444' }}>
                    {team.injuries.length}人伤病
                  </span>
                )}
              </div>

              {/* 预测阵容 */}
              {team.predicted_lineup?.formation && (
                <div className="mb-3">
                  <span className="text-sm font-bold">阵型：</span>
                  <span className="badge badge-secondary">{team.predicted_lineup.formation}</span>
                </div>
              )}

              {/* 伤病列表 */}
              {team.injuries && team.injuries.length > 0 && (
                <div className="space-y-2">
                  {team.injuries.map((inj, i) => {
                    const badge = getStatusBadge(inj.status);
                    return (
                      <div key={i} className="flex items-center gap-2 text-sm p-2 rounded" style={{ background: 'var(--card-bg)' }}>
                        <span className="font-medium">{inj.player_cn || inj.player}</span>
                        <span style={{
                          padding: '0.1rem 0.4rem', borderRadius: '0.2rem',
                          background: badge.bg, color: badge.color,
                          fontSize: '0.7rem', fontWeight: 600,
                        }}>
                          {inj.status_cn}
                        </span>
                        <span style={{ color: 'var(--text-muted)' }}>{inj.detail}</span>
                      </div>
                    );
                  })}
                </div>
              )}

              {(!team.injuries || team.injuries.length === 0) && (
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>无伤病报告</p>
              )}

              {team.recent_form && (
                <p className="text-sm mt-2" style={{ color: 'var(--text-muted)' }}>
                  📊 {team.recent_form}
                </p>
              )}
            </div>
          ))}
        </div>

        {teams.length === 0 && (
          <div className="text-center py-12">
            <p style={{ color: 'var(--text-muted)' }}>暂无快讯数据</p>
          </div>
        )}
      </div>
    </div>
  );
}
