'use client';

import { useState } from 'react';
import Link from 'next/link';
import api, { PredictResponse } from '@/lib/api';

export default function PredictPage() {
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [preview, setPreview] = useState<string>('');
  const [intelCard, setIntelCard] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'predict' | 'preview' | 'intel'>('predict');

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

  const handlePreview = async () => {
    if (!homeTeam || !awayTeam) return;
    setLoadingPreview(true);
    try {
      const res = await api.getPrematchPreview(homeTeam, awayTeam);
      setPreview(res.preview);
    } catch (err) {
      console.error('Failed to load preview:', err);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleIntelCard = async () => {
    if (!homeTeam || !awayTeam) return;
    try {
      const data = await api.getIntelCardByTeams(homeTeam, awayTeam);
      setIntelCard(data);
    } catch (err) {
      console.error('Failed to load intel card:', err);
    }
  };

  const handleCompare = async (tab: 'predict' | 'preview' | 'intel') => {
    setActiveTab(tab);
    if (tab === 'preview' && homeTeam && awayTeam && !preview) {
      handlePreview();
    }
    if (tab === 'intel' && homeTeam && awayTeam && !intelCard) {
      handleIntelCard();
    }
  };

  return (
    <div className="min-h-screen py-4 md:py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="page-title text-3xl mb-8 text-center">比赛预测</h1>

        {/* Team Input */}
        <div className="card mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
          <div className="flex gap-4 mt-6">
            <button
              className="btn btn-primary flex-1"
              onClick={handlePredict}
              disabled={loading || !homeTeam || !awayTeam}
            >
              {loading ? '预测中...' : '发起预测'}
            </button>
          </div>
        </div>

        {/* Results Tabs */}
        {result && (
          <>
            <div className="flex gap-2 mb-6">
              <button
                className={`tab ${activeTab === 'predict' ? 'active' : ''}`}
                onClick={() => handleCompare('predict')}
              >
                预测结果
              </button>
              <button
                className={`tab ${activeTab === 'preview' ? 'active' : ''}`}
                onClick={() => handleCompare('preview')}
              >
                赛前前瞻
              </button>
              <button
                className={`tab ${activeTab === 'intel' ? 'active' : ''}`}
                onClick={() => handleCompare('intel')}
              >
                情报卡
              </button>
            </div>

            {activeTab === 'predict' && (
              <div className="card">
                <h3 className="text-xl font-bold mb-6 text-center">
                  {result.home_team} vs {result.away_team}
                </h3>

                {/* ELO Ratings */}
                <div className="grid grid-cols-2 gap-4 mb-8">
                  <div className="text-center p-4 rounded-lg" style={{ background: 'rgba(16, 185, 129, 0.1)' }}>
                    <div className="text-3xl font-bold" style={{ color: 'var(--primary)' }}>
                      {result.home_elo.toFixed(0)}
                    </div>
                    <div className="stat-label">主队ELO</div>
                  </div>
                  <div className="text-center p-4 rounded-lg" style={{ background: 'rgba(239, 68, 68, 0.1)' }}>
                    <div className="text-3xl font-bold" style={{ color: 'var(--danger)' }}>
                      {result.away_elo.toFixed(0)}
                    </div>
                    <div className="stat-label">客队ELO</div>
                  </div>
                </div>

                {/* Win Probabilities */}
                <div className="space-y-4 mb-6">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="font-medium">{result.home_team} 胜</span>
                      <span>{(result.home_win_prob * 100).toFixed(1)}%</span>
                    </div>
                    <div className="prob-bar">
                      <div className="prob-fill home" style={{ width: `${result.home_win_prob * 100}%` }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="font-medium">平局</span>
                      <span>{(result.draw_prob * 100).toFixed(1)}%</span>
                    </div>
                    <div className="prob-bar">
                      <div className="prob-fill draw" style={{ width: `${result.draw_prob * 100}%` }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="font-medium">{result.away_team} 胜</span>
                      <span>{(result.away_win_prob * 100).toFixed(1)}%</span>
                    </div>
                    <div className="prob-bar">
                      <div className="prob-fill away" style={{ width: `${result.away_win_prob * 100}%` }} />
                    </div>
                  </div>
                </div>

                {/* Prediction */}
                <div className="text-center p-4 rounded-lg" style={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
                  <div className="stat-label mb-2">预测结果</div>
                  <div className="text-2xl font-bold">
                    {result.home_win_prob > result.away_win_prob
                      ? result.home_team
                      : result.away_win_prob > result.home_win_prob
                        ? result.away_team
                        : '平局'}
                    <span className="text-sm font-normal ml-2" style={{ color: 'var(--text-muted)' }}>
                      ({(Math.max(result.home_win_prob, result.draw_prob, result.away_win_prob) * 100).toFixed(1)}% 概率)
                    </span>
                  </div>
                  {result.data_quality && (
                    <span className={`badge mt-2 ${result.data_quality === 'high' ? 'badge-primary' : result.data_quality === 'medium' ? 'badge-accent' : 'badge-secondary'}`}>
                      数据质量: {result.data_quality === 'high' ? '高' : result.data_quality === 'medium' ? '中' : '低'}
                    </span>
                  )}
                </div>

                {/* Confidence Intervals */}
                {result.confidence_interval && (
                  <div className="mt-6">
                    <h4 className="font-bold mb-3">置信区间 (80%)</h4>
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>{result.home_team} 胜</span>
                          <span style={{ color: 'var(--text-muted)' }}>
                            {(result.confidence_interval.home[0] * 100).toFixed(1)}% - {(result.confidence_interval.home[1] * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="prob-bar" style={{ height: 6 }}>
                          <div className="prob-fill home" style={{
                            width: `${(result.confidence_interval.home[1] - result.confidence_interval.home[0]) * 100}%`,
                            marginLeft: `${result.confidence_interval.home[0] * 100}%`,
                            opacity: 0.5
                          }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>平局</span>
                          <span style={{ color: 'var(--text-muted)' }}>
                            {(result.confidence_interval.draw[0] * 100).toFixed(1)}% - {(result.confidence_interval.draw[1] * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="prob-bar" style={{ height: 6 }}>
                          <div className="prob-fill draw" style={{
                            width: `${(result.confidence_interval.draw[1] - result.confidence_interval.draw[0]) * 100}%`,
                            marginLeft: `${result.confidence_interval.draw[0] * 100}%`,
                            opacity: 0.5
                          }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>{result.away_team} 胜</span>
                          <span style={{ color: 'var(--text-muted)' }}>
                            {(result.confidence_interval.away[0] * 100).toFixed(1)}% - {(result.confidence_interval.away[1] * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="prob-bar" style={{ height: 6 }}>
                          <div className="prob-fill away" style={{
                            width: `${(result.confidence_interval.away[1] - result.confidence_interval.away[0]) * 100}%`,
                            marginLeft: `${result.confidence_interval.away[0] * 100}%`,
                            opacity: 0.5
                          }} />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Top Features */}
                {result.top_features && result.top_features.length > 0 && (
                  <div className="mt-6">
                    <h4 className="font-bold mb-3">关键影响因素</h4>
                    <div className="space-y-2">
                      {result.top_features.map((feat, idx) => (
                        <div key={idx} className="flex items-center gap-3 p-2 rounded-lg" style={{ background: 'var(--card-bg)' }}>
                          <span className="text-xs font-bold w-6 h-6 flex items-center justify-center rounded-full" style={{
                            background: feat.contribution > 0 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                            color: feat.contribution > 0 ? 'var(--primary)' : 'var(--danger)'
                          }}>
                            {idx + 1}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between text-sm">
                              <span className="truncate">{feat.feature}</span>
                              <span style={{ color: feat.contribution > 0 ? 'var(--primary)' : 'var(--danger)' }}>
                                {feat.contribution > 0 ? '+' : ''}{feat.contribution.toFixed(1)}%
                              </span>
                            </div>
                            <div className="prob-bar mt-1" style={{ height: 3 }}>
                              <div className="prob-fill" style={{
                                width: `${Math.min(Math.abs(feat.importance) * 100, 100)}%`,
                                background: feat.contribution > 0 ? 'var(--primary)' : 'var(--danger)',
                                opacity: 0.6
                              }} />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'preview' && (
              <div className="card">
                <h3 className="text-xl font-bold mb-4">赛前前瞻</h3>
                {loadingPreview ? (
                  <div className="flex items-center justify-center py-4 md:py-8">
                    <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
                  </div>
                ) : preview ? (
                  <div style={{ whiteSpace: 'pre-wrap' }}>{preview}</div>
                ) : (
                  <p style={{ color: 'var(--text-muted)' }}>点击"赛前前瞻"标签加载内容</p>
                )}
              </div>
            )}
          </>
        )}

        {error && (
          <p className="text-center mt-4" style={{ color: 'var(--danger)' }}>{error}</p>
        )}

        {/* Quick Teams */}
        <div className="mt-12">
          <h2 className="text-xl font-bold mb-4">快速选择</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {['Argentina', 'Brazil', 'Germany', 'France', 'Spain', 'England', 'Italy', 'Netherlands'].map((team) => (
              <button
                key={team}
                className="btn btn-secondary"
                onClick={() => {
                  if (!homeTeam) {
                    setHomeTeam(team);
                  } else if (!awayTeam) {
                    setAwayTeam(team);
                  } else {
                    setHomeTeam(team);
                    setAwayTeam('');
                  }
                }}
              >
                {team}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}