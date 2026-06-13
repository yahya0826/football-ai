'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import api, { DailyReport, BreakingNewsItem, ScheduleData } from '@/lib/api';

export default function IntelligencePage() {
  const [report, setReport] = useState<DailyReport | null>(null);
  const [breakingNews, setBreakingNews] = useState<BreakingNewsItem[]>([]);
  const [schedule, setSchedule] = useState<ScheduleData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('daily');

  useEffect(() => {
    async function loadData() {
      try {
        const [reportData, newsData, schedData] = await Promise.all([
          api.getDailyReport(),
          api.getBreakingNews(5),
          api.getSchedule(),
        ]);
        setReport(reportData);
        setBreakingNews(newsData.news);
        setSchedule(schedData);
      } catch (err) {
        console.error('Failed to load intelligence data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen py-4 md:py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="page-title text-3xl mb-2">哨前情报站</h1>
          <p className="text-lg" style={{ color: 'var(--text-muted)' }}>
            哨响之前，看懂比赛变量
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {[
            ['daily', '哨前日报'],
            ['schedule', '赛程情报'],
            ['breaking', '临哨快讯'],
            ['review', '哨后复盘'],
          ].map(([key, label]) => (
            <button
              key={key}
              className={`tab ${activeTab === key ? 'active' : ''}`}
              onClick={() => setActiveTab(key)}
            >
              {label}
            </button>
          ))}
        </div>

        {/* 哨前日报 */}
        {activeTab === 'daily' && report && (
          <div>
            <div className="card mb-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">哨前日报</h2>
                <span className="badge badge-primary">{report.date}</span>
              </div>
              <p className="mb-4" style={{ whiteSpace: 'pre-wrap' }}>{report.summary}</p>
              <div className="flex gap-4">
                <span className="badge badge-secondary">共{report.total_matches}场比赛</span>
                {report.key_match_focus && (
                  <span className="badge badge-accent">焦点: {report.key_match_focus}</span>
                )}
              </div>
            </div>

            {report.sections.map((section, idx) => (
              <div key={idx} className="card mb-4">
                <h3 className="font-bold text-lg mb-3">
                  {section.icon && (
                    <span className="mr-2">
                      {section.icon === 'schedule' ? '📋' :
                       section.icon === 'variables' ? '📊' :
                       section.icon === 'alerts' ? '🔔' : '📌'}
                    </span>
                  )}
                  {section.title}
                  {section.priority === 'high' && <span className="badge badge-primary ml-2">重点关注</span>}
                </h3>
                <p style={{ whiteSpace: 'pre-wrap', color: 'var(--text-muted)' }}>
                  {section.content}
                </p>
                {section.items && (
                  <ul className="mt-2 space-y-1">
                    {section.items.map((item, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <span style={{ color: 'var(--primary)' }}>•</span>
                        <span>{item.name || item.description}</span>
                        {item.status && <span className="badge badge-secondary text-xs">{item.status}</span>}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        )}

        {/* 赛程情报 */}
        {activeTab === 'schedule' && schedule && (
          <div>
            <h2 className="text-xl font-bold mb-4">今日赛程与情报</h2>
            <div className="grid gap-4">
              {schedule.matches.map((match) => (
                <Link key={match.match_id} href={`/intelligence/card/${match.match_id}`}>
                  <div className="match-card">
                    <div className="flex justify-between items-center">
                      <span className="font-bold">{match.home_team}</span>
                      <span style={{ color: 'var(--text-muted)' }}>vs</span>
                      <span className="font-bold">{match.away_team}</span>
                    </div>
                    <div className="flex justify-between items-center mt-2">
                      <span className="text-sm" style={{ color: 'var(--text-muted)' }}>{match.venue}</span>
                      <div className="flex gap-2">
                        {match.intel_available && <span className="badge badge-primary">情报可用</span>}
                        <span className="badge badge-secondary">{match.key_variable_count}个变量</span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* 临哨快讯 */}
        {activeTab === 'breaking' && (
          <div>
            <h2 className="text-xl font-bold mb-4">临哨快讯</h2>
            <div className="space-y-3">
              {breakingNews.map((news) => (
                <div key={news.id} className="card">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`badge ${news.urgency === 'high' ? 'badge-primary' : news.urgency === 'medium' ? 'badge-accent' : 'badge-secondary'}`}>
                          {news.urgency === 'high' ? '重要' : news.urgency === 'medium' ? '关注' : '一般'}
                        </span>
                        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                          {news.type === 'lineup' ? '阵容' : news.type === 'injury' ? '伤病' : news.type === 'weather' ? '天气' : '战术'}
                        </span>
                      </div>
                      <h3 className="font-bold">{news.title}</h3>
                      <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>{news.content}</p>
                    </div>
                  </div>
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                      {new Date(news.timestamp).toLocaleString('zh-CN')}
                    </span>
                    {news.verified && <span className="badge badge-secondary text-xs">已确认</span>}
                  </div>
                </div>
              ))}
              {breakingNews.length === 0 && (
                <p className="text-center py-4 md:py-8" style={{ color: 'var(--text-muted)' }}>暂无快讯</p>
              )}
            </div>
          </div>
        )}

        {/* 哨后复盘入口 */}
        {activeTab === 'review' && (
          <div className="text-center py-12">
            <h2 className="text-xl font-bold mb-4">哨后复盘</h2>
            <p className="mb-6" style={{ color: 'var(--text-muted)' }}>
              哨后复盘将验证赛前情报变量是否真正影响了比赛走向
            </p>
            <Link href="/matches" className="btn btn-primary">
              前往比赛列表查看复盘
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
