'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import api, { DailyReport } from '@/lib/api';

export default function DailyReportPage() {
  const [report, setReport] = useState<DailyReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getDailyReport();
        setReport(data);
      } catch (err) {
        console.error('Failed to load daily report:', err);
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

  if (!report) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p style={{ color: 'var(--text-muted)' }}>暂无日报数据</p>
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
          <h1 className="page-title text-3xl mb-2">哨前日报</h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{report.date}</p>
          <div className="flex justify-center gap-4 mt-4">
            <span className="badge badge-primary">{report.total_matches}场比赛</span>
            {report.key_match_focus && <span className="badge badge-accent">焦点: {report.key_match_focus}</span>}
          </div>
        </div>

        <div className="card mb-6">
          <h2 className="font-bold text-lg mb-3">今日摘要</h2>
          <p style={{ whiteSpace: 'pre-wrap' }}>{report.summary}</p>
        </div>

        {report.sections.map((section, idx) => (
          <div key={idx} className="card mb-4">
            <h3 className="font-bold text-lg mb-3">
              {section.icon === 'schedule' ? '📋 ' :
               section.icon === 'variables' ? '📊 ' :
               section.icon === 'alerts' ? '🔔 ' : ''}
              {section.title}
            </h3>
            <p style={{ whiteSpace: 'pre-wrap', color: 'var(--text-muted)' }}>
              {section.content}
            </p>
            {section.items && (
              <div className="mt-3 space-y-2">
                {section.items.map((item, i) => (
                  <div key={i} className="flex items-center gap-3 p-2 rounded" style={{ background: 'var(--card-bg)' }}>
                    <span style={{ color: 'var(--primary)' }}>•</span>
                    <span className="font-medium">{item.name || item.description}</span>
                    {item.status && <span className="badge badge-secondary text-xs">{item.status}</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        <p className="text-center text-sm mt-6" style={{ color: 'var(--text-muted)' }}>
          {report.disclaimer}
        </p>
      </div>
    </div>
  );
}
