'use client';

import { useState, useEffect, useRef } from 'react';
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
          style={{ maxHeight: '640px' }}
        />
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

function shuffleArray<T>(arr: T[], n: number): T[] {
  const shuffled = [...arr];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled.slice(0, n);
}

function RecentMatches() {
  const [matches, setMatches] = useState<ScheduleMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const randomMatches = useRef<ScheduleMatch[]>([]);

  useEffect(() => {
    async function loadMatches() {
      try {
        const data = await api.getMatchSchedule();
        randomMatches.current = shuffleArray(data.matches, 5);
        setMatches(randomMatches.current);
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

  const today = '2026-06-14';

  return (
    <section className="py-6 md:py-12">
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">随机比赛</h2>
          <Link href="/matches" className="text-sm" style={{ color: 'var(--primary)' }}>
            查看全部
          </Link>
        </div>
        <div className="grid gap-4">
          {matches.map((match) => {
            const isPast = match.date <= today;
            const hasScore = match.home_score != null && match.away_score != null;
            return (
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
                          {hasScore ? (
                            <span className="match-score" style={{ color: 'var(--primary)' }}>
                              {match.home_score} - {match.away_score}
                            </span>
                          ) : (
                            <span className="text-lg font-bold" style={{ color: 'var(--text-muted)' }}>
                              VS
                            </span>
                          )}
                        </div>
                        <div className="text-left flex-1">
                          <span className="font-medium">{match.away_team_cn}</span>
                          <span className="text-xs block" style={{ color: 'var(--text-muted)' }}>{match.away_team}</span>
                        </div>
                      </div>
                      <div className="flex justify-center items-center gap-2 mt-2">
                        {isPast && !hasScore && (
                          <span className="badge badge-accent">已结束</span>
                        )}
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                          {match.date} · {match.time_bj} · {match.group ? `小组${match.group}第${match.round}轮` : match.stage}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            );
          })}
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

export default function Home() {
  return (
    <div>
      <LiveScoreTicker />
      <HeroSection />
      <QuickPredict />
      <RecentMatches />
    </div>
  );
}
