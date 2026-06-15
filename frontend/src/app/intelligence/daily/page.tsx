'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import api, { DailySummaryResponse } from '@/lib/api';

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch {
    return iso;
  }
}

export default function DailySummarySubPage() {
  const [data, setData] = useState<DailySummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const result = await api.getDailySummary();
        setData(result);
      } catch (err) {
        console.error('Failed to load daily summary:', err);
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

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p style={{ color: 'var(--text-muted)' }}>暂无数据</p>
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

        <div className="card mb-8 text-center">
          <h1 className="page-title text-3xl mb-2">赛程情报</h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            {data.generated_at ? `生成于 ${formatTimestamp(data.generated_at)}` : data.date || ''}
          </p>
        </div>

        {data.generated && data.article ? (
          <div className="card">
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.9 }}>
              {data.article}
            </div>
          </div>
        ) : (
          <div className="card text-center py-8">
            <p style={{ color: 'var(--text-muted)' }}>
              比赛尚未全部结束，总结将在所有比赛完成后自动生成
            </p>
          </div>
        )}

        <p className="text-center text-sm mt-6" style={{ color: 'var(--text-muted)' }}>
          本文由 AI 自动生成，仅供参考
        </p>
      </div>
    </div>
  );
}
