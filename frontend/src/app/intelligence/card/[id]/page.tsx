'use client';

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import api, { IntelCard } from '@/lib/api';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function IntelCardPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const matchId = parseInt(resolvedParams.id);
  const [card, setCard] = useState<IntelCard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getIntelCard(matchId);
        setCard(data);
      } catch (err) {
        console.error('Failed to load intel card:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [matchId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!card) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p style={{ color: 'var(--text-muted)' }}>情报卡数据不可用</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-4 md:py-8">
      <div className="max-w-4xl mx-auto px-4">
        <Link href="/intelligence" className="inline-flex items-center gap-2 mb-6" style={{ color: 'var(--text-muted)' }}>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          返回情报站
        </Link>

        <h1 className="page-title text-3xl mb-8 text-center">哨前情报卡</h1>

        {/* Match Header */}
        <div className="card mb-8 text-center">
          <div className="flex justify-center items-center gap-8">
            <TeamHeader team={card.home_team} side="home" />
            <div className="text-2xl font-bold" style={{ color: 'var(--primary)' }}>VS</div>
            <TeamHeader team={card.away_team} side="away" />
          </div>
          {card.match_context.style_clash && (
            <p className="mt-4 text-sm" style={{ color: 'var(--text-muted)' }}>
              {card.match_context.style_clash} | 实力{gap_text(card.match_context.favorite || '')}
            </p>
          )}
        </div>

        {/* Team Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <TeamDetailCard team={card.home_team} />
          <TeamDetailCard team={card.away_team} />
        </div>

        {/* Key Variables */}
        <div className="card mb-6">
          <h2 className="text-xl font-bold mb-4">关键变量追踪</h2>
          <div className="space-y-3">
            {card.key_variables.map((v, idx) => (
              <div key={idx} className="p-3 rounded-lg" style={{ background: 'var(--card-bg)' }}>
                <div className="flex justify-between items-center mb-1">
                  <span className="font-bold">{v.name}</span>
                  <div className="flex gap-2">
                    <span className={`badge ${v.impact === 'high' ? 'badge-primary' : v.impact === 'medium' ? 'badge-accent' : 'badge-secondary'}`}>
                      {v.impact === 'high' ? '高影响' : v.impact === 'medium' ? '中影响' : '低影响'}
                    </span>
                    <span className="badge badge-secondary">
                      {v.status === 'confirmed' ? '已确认' : v.status === 'uncertain' ? '待确认' : '变化中'}
                    </span>
                  </div>
                </div>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{v.description}</p>
                {(v.home_detail || v.away_detail) && (
                  <div className="flex justify-between mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                    <span>{v.home_detail}</span>
                    <span>{v.away_detail}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Prediction Insight */}
        {card.prediction_insight && (
          <div className="card mb-6">
            <h2 className="text-xl font-bold mb-2">模型预测参考</h2>
            <p>{card.prediction_insight}</p>
            {card.confidence_note && (
              <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>{card.confidence_note}</p>
            )}
          </div>
        )}

        <p className="text-center text-sm" style={{ color: 'var(--text-muted)' }}>
          {card.disclaimer}
        </p>
      </div>
    </div>
  );
}

function TeamHeader({ team, side }: { team: any; side: string }) {
  return (
    <div>
      <div className="font-bold text-2xl">{team.name}</div>
      <div className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
        ELO: {team.elo?.toFixed(0) || '1500'}
      </div>
      <div className="text-sm" style={{ color: side === 'home' ? 'var(--primary)' : 'var(--danger)' }}>
        {team.recent_form}
      </div>
    </div>
  );
}

function TeamDetailCard({ team }: { team: any }) {
  return (
    <div className="card">
      <h3 className="font-bold text-lg mb-3">{team.name}</h3>
      <div className="space-y-2 text-sm">
        <div>
          <span className="stat-label">状态: </span>
          <span>{team.recent_form}</span>
        </div>
        <div>
          <span className="stat-label">预计阵型: </span>
          <span>{team.predicted_lineup?.formation || '未知'}</span>
        </div>
        <div>
          <span className="stat-label">战术风格: </span>
          <span>{team.style?.style || team.tactical_note || '分析中'}</span>
        </div>
        {team.key_player && (
          <div>
            <span className="stat-label">关键球员: </span>
            <span>{team.key_player}</span>
          </div>
        )}
        {team.injuries && team.injuries.length > 0 && (
          <div>
            <span className="stat-label">伤病: </span>
            <div className="mt-1 space-y-1">
              {team.injuries.map((inj: any, idx: number) => (
                <div key={idx} className="flex items-center gap-2">
                  <span className={`badge ${inj.impact === 'high' ? 'badge-primary' : 'badge-secondary'}`}>
                    {inj.status === 'out' ? '缺阵' : inj.status === 'doubtful' ? '存疑' : '可能'}
                  </span>
                  <span>{inj.player}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function gap_text(favorite: string): string {
  if (favorite === '实力接近') return '接近';
  return `稍偏向${favorite}`;
}
