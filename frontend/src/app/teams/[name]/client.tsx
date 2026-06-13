'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import api, { TeamDetail, MatchRecord, TeamStats } from '@/lib/api';

type Tab = 'basic' | 'recent' | 'analysis';

const CONFED_CN: Record<string, string> = {
  UEFA: '欧洲足联',
  CONMEBOL: '南美足联',
  AFC: '亚洲足联',
  CAF: '非洲足联',
  CONCACAF: '中北美及加勒比足联',
  OFC: '大洋洲足联',
};

export default function TeamDetailClient() {
  const params = useParams();
  const router = useRouter();
  const teamName = params.name as string;

  const [team, setTeam] = useState<TeamDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<Tab>('basic');

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getTeamDetail(decodeURIComponent(teamName));
        setTeam(data);
      } catch (err) {
        setError('球队数据加载失败');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [teamName]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error || !team) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-xl" style={{ color: 'var(--danger)' }}>{error || '未找到球队'}</p>
        <button className="btn btn-secondary" onClick={() => router.push('/teams')}>
          返回球队列表
        </button>
      </div>
    );
  }

  const t = team.team;
  const stats = team.recent_form?.stats;
  const total = stats?.total_matches || 1;
  const winRate = ((stats?.wins || 0) / total * 100).toFixed(1);
  const goalsPerMatch = ((stats?.goals_for || 0) / total).toFixed(2);
  const concededPerMatch = ((stats?.goals_against || 0) / total).toFixed(2);

  const groupIdx = t.group.charCodeAt(0) - 65;
  const groupColors = ['#10b981','#6366f1','#f59e0b','#ef4444','#06b6d4','#ec4899','#84cc16','#f97316','#14b8a6','#8b5cf6','#eab308','#dc2626'];
  const groupColor = groupColors[groupIdx % groupColors.length];

  return (
    <div className="min-h-screen py-4 md:py-8">
      <div className="max-w-5xl mx-auto px-4">
        <button
          className="btn btn-secondary mb-4 text-sm"
          onClick={() => router.push('/teams')}
        >
          ← 返回球队列表
        </button>

        <div className="card mb-6">
          <div className="flex items-center gap-4 mb-4">
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center font-bold text-white text-2xl"
              style={{ background: groupColor }}
            >
              {t.team_en.substring(0, 2).toUpperCase()}
            </div>
            <div>
              <h1 className="text-2xl font-bold">{t.team_cn}</h1>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{t.team_en}</p>
              <div className="flex gap-2 mt-1">
                <span className="badge text-xs" style={{ background: `${groupColor}20`, color: groupColor }}>
                  Group {t.group}
                </span>
                <span className="badge badge-secondary text-xs">{CONFED_CN[t.confederation] || t.confederation}</span>
                {t.world_cup_titles ? (
                  <span className="badge badge-accent text-xs">{t.world_cup_titles}次世界杯冠军</span>
                ) : null}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 sm:grid-cols-5 gap-4 text-center">
            <div>
              <div className="stat-value">{stats?.total_matches || 0}</div>
              <div className="stat-label">近20年比赛</div>
            </div>
            <div>
              <div className="stat-value" style={{ color: 'var(--success)' }}>{winRate}%</div>
              <div className="stat-label">胜率</div>
            </div>
            <div>
              <div className="stat-value">{goalsPerMatch}</div>
              <div className="stat-label">场均进球</div>
            </div>
            <div>
              <div className="stat-value">{concededPerMatch}</div>
              <div className="stat-label">场均失球</div>
            </div>
            <div>
              <div className="stat-value">{team.recent_form?.total_matches_20y || 0}</div>
              <div className="stat-label">历史比赛</div>
            </div>
          </div>
        </div>

        <div className="flex gap-2 mb-6 flex-wrap">
          {(['basic', 'recent', 'analysis'] as Tab[]).map((tab) => (
            <button
              key={tab}
              className={`tab ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab === 'basic' && '基本情况'}
              {tab === 'recent' && '最近战况'}
              {tab === 'analysis' && '赛前分析'}
            </button>
          ))}
        </div>

        {activeTab === 'basic' && <BasicInfoTab team={team} />}
        {activeTab === 'recent' && <RecentFormTab team={team} />}
        {activeTab === 'analysis' && <AnalysisTab team={team} />}
      </div>
    </div>
  );
}

function BasicInfoTab({ team }: { team: TeamDetail }) {
  const t = team.team;

  return (
    <div className="space-y-6">
      {t.playing_style && (
        <div className="card">
          <h2 className="text-xl font-bold mb-4">球队概况</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span style={{ color: 'var(--text-muted)' }}>战术风格：</span>
              <span className="font-bold">{t.playing_style}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>常用阵型：</span>
              <span className="font-bold">{t.key_formation}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>优势：</span>
              <span>{t.strength}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>短板：</span>
              <span>{t.weakness}</span>
            </div>
          </div>
          {t.history && (
            <div className="mt-3">
              <span className="text-sm" style={{ color: 'var(--text-muted)' }}>历史：</span>
              <p className="text-sm mt-1">{t.history}</p>
            </div>
          )}
        </div>
      )}

      <div className="card">
        <h2 className="text-xl font-bold mb-4">排名数据</h2>
        <div className="flex gap-6">
          <div className="text-center">
            <div className="stat-value">{t.elo_rating || '--'}</div>
            <div className="stat-label">ELO 评分</div>
          </div>
          <div className="text-center">
            <div className="stat-value">{t.fifa_ranking || '--'}</div>
            <div className="stat-label">FIFA 排名</div>
          </div>
        </div>
      </div>

      {t.odds && Object.keys(t.odds).length > 0 && (
        <div className="card">
          <h2 className="text-xl font-bold mb-4">夺冠赔率</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            {Object.entries(t.odds).map(([platform, odd]) => (
              <div key={platform} className="flex justify-between p-2 rounded" style={{ background: 'rgba(255,255,255,0.03)' }}>
                <span style={{ color: 'var(--text-muted)' }}>{platform}</span>
                <span className="font-bold">{odd}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <h2 className="text-xl font-bold mb-4">球员名单</h2>
        <p style={{ color: 'var(--text-muted)' }}>
          球员名单数据正在采集中，即将上线...
        </p>
      </div>
    </div>
  );
}

function RecentFormTab({ team }: { team: TeamDetail }) {
  const stats = team.recent_form;
  const matches = stats?.recent_matches || [];
  const matchesByYear = stats?.matches_by_year || {};
  const tournaments = stats?.tournament_breakdown || {};

  const resultBadge = (m: MatchRecord) => {
    const isHome = m.home_team === team.team.team_en;
    try {
      const hs = parseInt(m.home_score);
      const away = parseInt(m.away_score);
      if (isNaN(hs) || isNaN(away)) return <span className="badge badge-secondary text-xs">未赛</span>;

      const win = isHome ? hs > away : away > hs;
      const draw = hs === away;
      return (
        <span
          className="badge text-xs"
          style={{
            background: win ? 'rgba(34,197,94,0.2)' : draw ? 'rgba(99,102,241,0.2)' : 'rgba(239,68,68,0.2)',
            color: win ? 'var(--success)' : draw ? 'var(--secondary)' : 'var(--danger)',
          }}
        >
          {win ? '胜' : draw ? '平' : '负'}
        </span>
      );
    } catch {
      return <span className="badge badge-secondary text-xs">--</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-xl font-bold mb-4">近20年战绩总览</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center p-3 rounded" style={{ background: 'rgba(34,197,94,0.08)' }}>
            <div className="text-2xl font-bold" style={{ color: 'var(--success)' }}>{stats?.stats?.wins || 0}</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>胜</div>
          </div>
          <div className="text-center p-3 rounded" style={{ background: 'rgba(99,102,241,0.08)' }}>
            <div className="text-2xl font-bold" style={{ color: 'var(--secondary)' }}>{stats?.stats?.draws || 0}</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>平</div>
          </div>
          <div className="text-center p-3 rounded" style={{ background: 'rgba(239,68,68,0.08)' }}>
            <div className="text-2xl font-bold" style={{ color: 'var(--danger)' }}>{stats?.stats?.losses || 0}</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>负</div>
          </div>
          <div className="text-center p-3 rounded" style={{ background: 'rgba(245,158,11,0.08)' }}>
            <div className="text-2xl font-bold" style={{ color: 'var(--accent)' }}>
              {stats?.stats ? (stats.stats.goals_for - stats.stats.goals_against) : '--'}
            </div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>净胜球</div>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-xl font-bold mb-4">年度比赛分布</h2>
        <div className="space-y-2">
          {Object.entries(matchesByYear).slice(0, 20).map(([year, count]) => (
            <div key={year} className="flex items-center gap-3 text-sm">
              <span className="w-12 text-right" style={{ color: 'var(--text-muted)' }}>{year}</span>
              <div className="flex-1 prob-bar" style={{ height: 12 }}>
                <div
                  className="prob-fill home"
                  style={{ width: `${Math.min((count as number) / 30 * 100, 100)}%` }}
                />
              </div>
              <span className="w-8 font-bold">{count}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h2 className="text-xl font-bold mb-4">赛事分布</h2>
        <div className="flex flex-wrap gap-2">
          {Object.entries(tournaments).slice(0, 10).map(([tour, count]) => (
            <span key={tour} className="badge" style={{ background: 'rgba(255,255,255,0.05)' }}>
              {tour}: {count}场
            </span>
          ))}
        </div>
      </div>

      <div className="card">
        <h2 className="text-xl font-bold mb-4">最近10场比赛</h2>
        <div className="space-y-2">
          {matches.map((m, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-3 rounded"
              style={{ background: idx % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent' }}
            >
              <div className="flex items-center gap-3">
                {resultBadge(m)}
                <span className="text-sm font-medium">{m.home_team}</span>
                <span className="text-sm font-bold">
                  {m.home_score || '?'} - {m.away_score || '?'}
                </span>
                <span className="text-sm font-medium">{m.away_team}</span>
              </div>
              <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                <span>{m.tournament}</span>
                <span>{m.date}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function AnalysisTab({ team }: { team: TeamDetail }) {
  const t = team.team;

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-xl font-bold mb-4">小组情况 - Group {t.group}</h2>
        <p style={{ color: 'var(--text-muted)' }}>
          {t.team_cn}被分在2026世界杯 Group {t.group}。
          同组对手信息将在小组分析完成后展示。
        </p>
      </div>

      <div className="card">
        <h2 className="text-xl font-bold mb-4">关键球员</h2>
        <p style={{ color: 'var(--text-muted)' }}>
          关键球员分析将在球员数据采集完成后上线。
        </p>
      </div>

      <div className="card">
        <h2 className="text-xl font-bold mb-4">赛前预判</h2>
        <div className="p-4 rounded text-center" style={{ background: 'rgba(255,255,255,0.03)' }}>
          <p className="text-lg mb-2" style={{ color: 'var(--text-muted)' }}>
            综合分析与预测模型即将上线
          </p>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            将基于ELO评分、近期状态、伤病情况和历史交锋数据进行综合评估
          </p>
        </div>
      </div>
    </div>
  );
}
