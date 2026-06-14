'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import api, { ScheduleMatch } from '@/lib/api';
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

function RecentMatches() {
  const [matches, setMatches] = useState<ScheduleMatch[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadMatches() {
      try {
        const data = await api.getMatchSchedule();
        const today = '2026-06-14';
        const completed = data.matches
          .filter(m => m.home_score != null && m.away_score != null && m.date <= today)
          .sort((a, b) => b.date.localeCompare(a.date) || b.time_bj.localeCompare(a.time_bj))
          .slice(0, 5);
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

export default function Home() {
  return (
    <div>
      <LiveScoreTicker />
      <HeroSection />
      <RecentMatches />
    </div>
  );
}
