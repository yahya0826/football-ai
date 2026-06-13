'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import api from '@/lib/api';

interface FeedbackEntry {
  id: number;
  text: string;
  rating: number;
  page?: string;
  created_at: string;
}

export default function FeedbackAdminClient() {
  const [entries, setEntries] = useState<FeedbackEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getFeedback();
        setEntries(data.entries);
      } catch (err) {
        setError('无法加载反馈数据');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="min-h-screen py-4 md:py-8">
      <div className="max-w-3xl mx-auto px-4">
        <Link href="/" className="inline-flex items-center gap-2 mb-6" style={{ color: 'var(--text-muted)' }}>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          返回首页
        </Link>

        <h1 className="page-title text-3xl mb-2 text-center">用户反馈</h1>
        <p className="text-center text-sm mb-8" style={{ color: 'var(--text-muted)' }}>
          {loading ? '加载中...' : `共 ${entries.length} 条反馈`}
        </p>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
          </div>
        ) : error ? (
          <div className="card text-center py-8">
            <p style={{ color: 'var(--danger)' }}>{error}</p>
          </div>
        ) : entries.length === 0 ? (
          <div className="card text-center py-8">
            <p style={{ color: 'var(--text-muted)' }}>暂无反馈</p>
          </div>
        ) : (
          <div className="space-y-4">
            {entries.map((entry) => (
              <div key={entry.id} className="card">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="badge badge-secondary">#{entry.id}</span>
                    <span style={{ color: 'var(--accent)', fontSize: '1.1rem' }}>
                      {'★'.repeat(entry.rating)}{'☆'.repeat(5 - entry.rating)}
                    </span>
                    <span className="text-sm font-bold" style={{ color: 'var(--accent)' }}>
                      {entry.rating}/5
                    </span>
                  </div>
                  <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    {new Date(entry.created_at).toLocaleString('zh-CN')}
                  </span>
                </div>
                <p style={{ whiteSpace: 'pre-wrap' }}>{entry.text}</p>
                {entry.page && (
                  <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
                    页面: {entry.page}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
