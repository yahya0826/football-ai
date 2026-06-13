'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import api, { PredictResponse, ScheduleMatch } from '@/lib/api';
import LiveScoreTicker from '@/components/LiveScoreTicker';

function HeroSection() {
  return (
    <section className="relative py-4 md:py-8 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-r from-emerald-900/20 via-transparent to-indigo-900/20" />
      <div className="relative max-w-4xl mx-auto px-4 text-center">
        <img
          src="/images/hero-banner.png"
          alt="2026世界杯AI助手"
          className="mx-auto img-responsive"
          style={{ maxHeight: '320px' }}
        />
        <div className="flex items-center justify-center gap-4 flex-wrap mt-6">
          <Link href="/predict" className="btn btn-primary">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            开始预测
          </Link>
          <Link href="/knowledge" className="btn btn-secondary">
            探索知识库
          </Link>
        </div>
      </div>
    </section>
  );
}

function QuickPredict() {
  const [homeTeam, setHomeTeam] = useState('Argentina');
  const [awayTeam, setAwayTeam] = useState('Brazil');
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePredict = async () => {
    if (!homeTeam || !awayTeam) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.predict(homeTeam, awayTeam);
      setResult(res);
    } catch (err) {
      setError('预测失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="py-6 md:py-12">
      <div className="max-w-4xl mx-auto px-4">
        <h2 className="text-2xl font-bold mb-6 text-center">快速比赛预测</h2>
        <div className="card">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>主队</label>
              <input
                type="text"
                className="input"
                value={homeTeam}
                onChange={(e) => setHomeTeam(e.target.value)}
                placeholder="输入主队名称"
              />
            </div>
            <div className="flex items-center justify-center">
              <span style={{ color: 'var(--text-muted)' }}>VS</span>
            </div>
            <div>
              <label className="block text-sm mb-2" style={{ color: 'var(--text-muted)' }}>客队</label>
              <input
                type="text"
                className="input"
                value={awayTeam}
                onChange={(e) => setAwayTeam(e.target.value)}
                placeholder="输入客队名称"
              />
            </div>
          </div>
          <button
            className="btn btn-primary w-full"
            onClick={handlePredict}
            disabled={loading}
          >
            {loading ? (
              <>
                <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                预测中...
              </>
            ) : '发起预测'}
          </button>

          {error && (
            <p className="text-center mt-4" style={{ color: 'var(--danger)' }}>{error}</p>
          )}

          {result && (
            <div className="mt-6">
              <div className="flex justify-between items-center mb-4">
                <span className="font-bold">{result.home_team}</span>
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>ELO: {result.home_elo.toFixed(0)}</span>
              </div>

              <div className="prob-bar mb-2">
                <div className="prob-fill home" style={{ width: `${result.home_win_prob * 100}%` }} />
              </div>
              <div className="prob-bar mb-2">
                <div className="prob-fill draw" style={{ width: `${result.draw_prob * 100}%` }} />
              </div>
              <div className="prob-bar mb-4">
                <div className="prob-fill away" style={{ width: `${result.away_win_prob * 100}%` }} />
              </div>

              <div className="flex justify-between items-center mb-4">
                <span className="font-bold">{result.away_team}</span>
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>ELO: {result.away_elo.toFixed(0)}</span>
              </div>

              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-3 rounded-lg" style={{ background: 'rgba(16, 185, 129, 0.1)' }}>
                  <div className="stat-value">{result.home_win_prob.toFixed(1)}%</div>
                  <div className="stat-label">主队胜</div>
                </div>
                <div className="p-3 rounded-lg" style={{ background: 'rgba(99, 102, 241, 0.1)' }}>
                  <div className="stat-value">{result.draw_prob.toFixed(1)}%</div>
                  <div className="stat-label">平局</div>
                </div>
                <div className="p-3 rounded-lg" style={{ background: 'rgba(239, 68, 68, 0.1)' }}>
                  <div className="stat-value">{result.away_win_prob.toFixed(1)}%</div>
                  <div className="stat-label">客队胜</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function RecentMatches() {
  const [matches, setMatches] = useState<ScheduleMatch[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadMatches() {
      try {
        const data = await api.getMatchSchedule();
        const today = '2026-06-14';
        const completed = data.matches
          .filter(m => m.home_score != null && m.date <= today)
          .sort((a, b) => b.date.localeCompare(a.date) || b.time_bj.localeCompare(a.time_bj))
          .slice(0, 6);
        setMatches(completed);
      } catch (err) {
        console.error('Failed to load matches:', err);
      } finally {
        setLoading(false);
      }
    }
    loadMatches();
  }, []);

  if (loading) {
    return (
      <section className="py-6 md:py-12">
        <div className="max-w-4xl mx-auto px-4">
          <div className="animate-pulse h-48 rounded-lg" style={{ background: 'var(--card-bg)' }} />
        </div>
      </section>
    );
  }

  return (
    <section className="py-6 md:py-12">
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">最近比赛</h2>
          <Link href="/matches" className="text-sm" style={{ color: 'var(--primary)' }}>
            查看全部
          </Link>
        </div>
        <div className="grid gap-4">
          {matches.map((match) => (
            <Link key={match.match_id} href={`/matches/${match.match_id}`}>
              <div className="match-card">
                <div className="flex justify-between items-center">
                  <div className="flex-1">
                    <div className="flex justify-between items-center">
                      <div className="text-right flex-1">
                        <span className="font-medium">{match.home_team_cn}</span>
                        <span className="text-xs block" style={{ color: 'var(--text-muted)' }}>{match.home_team}</span>
                      </div>
                      <div className="mx-4 text-center">
                        <span className="match-score" style={{ color: 'var(--primary)' }}>
                          {match.home_score} - {match.away_score}
                        </span>
                      </div>
                      <div className="text-left flex-1">
                        <span className="font-medium">{match.away_team_cn}</span>
                        <span className="text-xs block" style={{ color: 'var(--text-muted)' }}>{match.away_team}</span>
                      </div>
                    </div>
                    <p className="text-sm text-center mt-2" style={{ color: 'var(--text-muted)' }}>
                      {match.date} · {match.time_bj} · {match.group ? `小组${match.group}第${match.round}轮` : match.stage}
                    </p>
                  </div>
                </div>
              </div>
            </Link>
          ))}
          {matches.length === 0 && (
            <p className="text-center py-8" style={{ color: 'var(--text-muted)' }}>
              暂无比赛数据
            </p>
          )}
        </div>
      </div>
    </section>
  );
}

function IntelPreview() {
  const [dailyData, setDailyData] = useState<{ summary: string; total_matches: number } | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getDailyReport();
        setDailyData({ summary: data.summary, total_matches: data.total_matches });
      } catch { /* silently fail */ }
    }
    load();
  }, []);

  return (
    <section className="py-6 md:py-12">
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">哨前情报站</h2>
          <Link href="/intelligence" className="text-sm" style={{ color: 'var(--primary)' }}>
            查看完整情报
          </Link>
        </div>
        <div className="card">
          <p className="mb-4" style={{ color: 'var(--text-muted)' }}>
            {dailyData?.summary || '哨响之前，看懂比赛变量' || '数据加载中...'}
          </p>
          <div className="flex gap-4">
            <Link href="/intelligence/daily" className="btn btn-primary text-sm">哨前日报</Link>
            <Link href="/intelligence/breaking" className="btn btn-secondary text-sm">临哨快讯</Link>
            <Link href="/intelligence" className="btn btn-secondary text-sm">情报卡</Link>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  return (
    <div>
      <LiveScoreTicker />
      <HeroSection />
      <QuickPredict />
      <RecentMatches />
      <IntelPreview />
    </div>
  );
}
