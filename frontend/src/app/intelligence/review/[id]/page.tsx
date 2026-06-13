'use client';

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import api, { ReviewData } from '@/lib/api';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ReviewPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const matchId = parseInt(resolvedParams.id);
  const [review, setReview] = useState<ReviewData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getPostMatchReview(matchId);
        setReview(data);
      } catch (err) {
        console.error('Failed to load review:', err);
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

  if (!review) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p style={{ color: 'var(--text-muted)' }}>复盘数据不可用</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-4 md:py-8">
      <div className="max-w-4xl mx-auto px-4">
        <Link href={`/matches/${matchId}`} className="inline-flex items-center gap-2 mb-6" style={{ color: 'var(--text-muted)' }}>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          返回比赛详情
        </Link>

        <div className="card mb-8 text-center">
          <h1 className="page-title text-3xl mb-3">哨后复盘</h1>
          <div className="text-4xl font-bold mb-2" style={{ color: 'var(--primary)' }}>
            {review.final_score}
          </div>
          <p className="text-lg">{review.home_team} vs {review.away_team}</p>
        </div>

        {/* Prediction Accuracy */}
        <div className="card mb-6">
          <h2 className="text-xl font-bold mb-3">预测评估</h2>
          <div className="p-4 rounded-lg" style={{ background: 'var(--card-bg)' }}>
            <div className="flex items-center gap-3 mb-2">
              <span className={`badge ${review.prediction_accuracy.rating.includes('正确') ? 'badge-primary' : 'badge-accent'}`}>
                {review.prediction_accuracy.rating}
              </span>
              <span className="text-sm" style={{ color: 'var(--text-muted)' }}>{review.prediction_accuracy.accuracy}</span>
            </div>
            {review.prediction_accuracy.detail && (
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{review.prediction_accuracy.detail}</p>
            )}
          </div>
        </div>

        {/* Variable Verification */}
        <div className="card mb-6">
          <h2 className="text-xl font-bold mb-4">变量验证</h2>
          <div className="space-y-3">
            {review.variable_verification.map((v, idx) => (
              <div key={idx} className="p-3 rounded-lg" style={{ background: 'var(--card-bg)' }}>
                <div className="flex justify-between items-center mb-1">
                  <span className="font-bold">{v.variable}</span>
                  <span className={`badge ${v.verified ? 'badge-primary' : 'badge-accent'}`}>
                    {v.verified ? '已验证' : '待验证'}
                  </span>
                </div>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{v.analysis}</p>
                <div className="grid grid-cols-2 gap-4 mt-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                  <div>赛前: {v.pre_match_assessment}</div>
                  <div>实际: {v.actual_impact}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Turning Points */}
        <div className="card mb-6">
          <h2 className="text-xl font-bold mb-3">关键转折点</h2>
          <ul className="space-y-2">
            {review.key_turning_points.map((point, idx) => (
              <li key={idx} className="flex items-center gap-2">
                <span style={{ color: 'var(--primary)' }}>{idx + 1}.</span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Summary */}
        <div className="card mb-6">
          <h2 className="text-xl font-bold mb-3">复盘总结</h2>
          <p style={{ whiteSpace: 'pre-wrap' }}>{review.summary}</p>
          {review.lessons_learned && (
            <div className="mt-3">
              <h3 className="font-bold mb-2">经验总结</h3>
              <ul className="space-y-1">
                {review.lessons_learned.map((lesson, idx) => (
                  <li key={idx} className="flex items-center gap-2 text-sm">
                    <span style={{ color: 'var(--primary)' }}>•</span>
                    <span style={{ color: 'var(--text-muted)' }}>{lesson}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <p className="text-center text-sm" style={{ color: 'var(--text-muted)' }}>{review.disclaimer}</p>
      </div>
    </div>
  );
}
