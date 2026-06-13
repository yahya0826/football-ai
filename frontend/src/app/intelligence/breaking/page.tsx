'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import api, { BreakingNewsItem } from '@/lib/api';

export default function BreakingNewsPage() {
  const [news, setNews] = useState<BreakingNewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [urgencyFilter, setUrgencyFilter] = useState('all');

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getBreakingNews(20);
        setNews(data.news);
      } catch (err) {
        console.error('Failed to load breaking news:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = urgencyFilter === 'all'
    ? news
    : news.filter(n => n.urgency === urgencyFilter);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
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

        <h1 className="page-title text-3xl mb-8 text-center">临哨快讯</h1>

        {/* Filter */}
        <div className="flex gap-2 mb-6">
          {[
            ['all', '全部'],
            ['high', '重要'],
            ['medium', '关注'],
            ['low', '一般'],
          ].map(([key, label]) => (
            <button
              key={key}
              className={`tab ${urgencyFilter === key ? 'active' : ''}`}
              onClick={() => setUrgencyFilter(key)}
            >
              {label}
            </button>
          ))}
        </div>

        {/* News Feed */}
        <div className="space-y-3">
          {filtered.map((item) => (
            <div key={item.id} className="card">
              <div className="flex items-start gap-4">
                {item.type === 'lineup' && <span className="text-2xl">📋</span>}
                {item.type === 'injury' && <span className="text-2xl">🏥</span>}
                {item.type === 'weather' && <span className="text-2xl">🌤️</span>}
                {item.type === 'tactical' && <span className="text-2xl">📊</span>}

                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`badge ${item.urgency === 'high' ? 'badge-primary' : item.urgency === 'medium' ? 'badge-accent' : 'badge-secondary'}`}>
                      {item.urgency === 'high' ? '重要' : item.urgency === 'medium' ? '关注' : '一般'}
                    </span>
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                      {item.type === 'lineup' ? '阵容' :
                       item.type === 'injury' ? '伤病' :
                       item.type === 'weather' ? '天气' : '战术'}
                    </span>
                    {item.source && (
                      <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        来源: {item.source}
                      </span>
                    )}
                  </div>
                  <h3 className="font-bold text-lg">{item.title}</h3>
                  <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>{item.content}</p>
                </div>
              </div>

              <div className="flex justify-between items-center mt-3">
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  {new Date(item.timestamp).toLocaleString('zh-CN')}
                </span>
                <div className="flex gap-2">
                  {item.verified !== undefined && (
                    <span className={`badge ${item.verified ? 'badge-primary' : 'badge-accent'} text-xs`}>
                      {item.verified ? '已确认' : '待确认'}
                    </span>
                  )}
                  {item.match_id && (
                    <Link href={`/matches/${item.match_id}`} className="text-xs" style={{ color: 'var(--primary)' }}>
                      查看比赛
                    </Link>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-12">
            <p style={{ color: 'var(--text-muted)' }}>暂无快讯</p>
          </div>
        )}
      </div>
    </div>
  );
}
