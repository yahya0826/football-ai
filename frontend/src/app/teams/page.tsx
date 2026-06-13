'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api, { TeamListItem, TeamsListResponse } from '@/lib/api';

const CONFED_NAME: Record<string, string> = {
  UEFA: '欧洲 (UEFA)',
  CONMEBOL: '南美洲 (CONMEBOL)',
  AFC: '亚洲 (AFC)',
  CAF: '非洲 (CAF)',
  CONCACAF: '中北美 (CONCACAF)',
  OFC: '大洋洲 (OFC)',
};

const GROUP_COLORS = [
  '#10b981', '#6366f1', '#f59e0b', '#ef4444',
  '#06b6d4', '#ec4899', '#84cc16', '#f97316',
  '#14b8a6', '#8b5cf6', '#eab308', '#dc2626',
];

export default function TeamsPage() {
  const router = useRouter();
  const [data, setData] = useState<TeamsListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterConfed, setFilterConfed] = useState<string>('');
  const [filterGroup, setFilterGroup] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('group');
  const [search, setSearch] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const result = await api.getTeams({
          confederation: filterConfed || undefined,
          group: filterGroup || undefined,
          sort_by: sortBy,
          search: search || undefined,
        });
        setData(result);
      } catch (err) {
        console.error('Failed to load teams:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [filterConfed, filterGroup, sortBy, search]);

  const getWinRate = (stats: TeamListItem['stats']) => {
    if (!stats || stats.total_matches === 0) return 0;
    return ((stats.wins / stats.total_matches) * 100).toFixed(1);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen py-4 md:py-8">
      <div className="max-w-7xl mx-auto px-4">
        <h1 className="page-title text-3xl mb-2 text-center">2026世界杯球队</h1>
        <p className="text-center mb-8" style={{ color: 'var(--text-muted)' }}>
          48支参赛球队 · 12个小组 · 6大洲联
        </p>

        {/* Filters */}
        <div className="card mb-6">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1" style={{ minWidth: '12.5rem' }}>
              <label className="block text-sm mb-1" style={{ color: 'var(--text-muted)' }}>搜索球队</label>
              <input
                type="text"
                className="input"
                placeholder="输入球队名称..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm mb-1" style={{ color: 'var(--text-muted)' }}>洲联</label>
              <select
                className="input"
                value={filterConfed}
                onChange={(e) => setFilterConfed(e.target.value)}
              >
                <option value="">全部</option>
                {data?.confederations.map((c) => (
                  <option key={c.name} value={c.name}>{CONFED_NAME[c.name] || c.name} ({c.count})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm mb-1" style={{ color: 'var(--text-muted)' }}>小组</label>
              <select
                className="input"
                value={filterGroup}
                onChange={(e) => setFilterGroup(e.target.value)}
              >
                <option value="">全部</option>
                {data?.groups.map((g) => (
                  <option key={g} value={g}>Group {g}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm mb-1" style={{ color: 'var(--text-muted)' }}>排序</label>
              <select
                className="input"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="group">按小组</option>
                <option value="win_rate">按胜率</option>
                <option value="matches">按比赛数</option>
                <option value="name">按名称</option>
              </select>
            </div>
          </div>
        </div>

        {/* Teams Grid */}
        {data && data.teams.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data.teams.map((team, idx) => {
              const winRate = getWinRate(team.stats);
              const groupIdx = team.group.charCodeAt(0) - 65;
              const groupColor = GROUP_COLORS[groupIdx % GROUP_COLORS.length];

              return (
                <div
                  key={team.team_en}
                  className="card cursor-pointer"
                  onClick={() => router.push(`/teams/${encodeURIComponent(team.team_en)}`)}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-12 h-12 rounded-full flex items-center justify-center font-bold text-white text-lg"
                        style={{ background: groupColor }}
                      >
                        {team.team_en.substring(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <h3 className="font-bold text-base">{team.team_cn}</h3>
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{team.team_en}</p>
                      </div>
                    </div>
                  </div>

                  {/* Group & Confederation */}
                  <div className="flex gap-2 mb-3">
                    <span className="badge text-xs" style={{
                      background: `${groupColor}20`,
                      color: groupColor,
                    }}>
                      Group {team.group}
                    </span>
                    <span className="badge badge-secondary text-xs">{team.confederation}</span>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-2 text-center text-sm">
                    <div>
                      <div className="font-bold" style={{ color: 'var(--success)' }}>{team.stats?.wins || 0}</div>
                      <div className="text-xs" style={{ color: 'var(--text-muted)' }}>胜</div>
                    </div>
                    <div>
                      <div className="font-bold" style={{ color: 'var(--secondary)' }}>{team.stats?.draws || 0}</div>
                      <div className="text-xs" style={{ color: 'var(--text-muted)' }}>平</div>
                    </div>
                    <div>
                      <div className="font-bold" style={{ color: 'var(--danger)' }}>{team.stats?.losses || 0}</div>
                      <div className="text-xs" style={{ color: 'var(--text-muted)' }}>负</div>
                    </div>
                  </div>

                  {/* Win rate bar */}
                  <div className="mt-3">
                    <div className="flex justify-between text-xs mb-1">
                      <span style={{ color: 'var(--text-muted)' }}>近20年胜率</span>
                      <span className="font-bold" style={{ color: 'var(--primary)' }}>{winRate}%</span>
                    </div>
                    <div className="prob-bar">
                      <div
                        className="prob-fill home"
                        style={{ width: `${winRate}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-16">
            <p className="text-lg" style={{ color: 'var(--text-muted)' }}>没有找到匹配的球队</p>
          </div>
        )}
      </div>
    </div>
  );
}
