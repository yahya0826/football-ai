'use client';

import { useState, useEffect, useCallback } from 'react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts';
import { Player, PlayerAttributes } from './types';
import api from '@/lib/api';

interface PlayerInfoPanelProps {
  player: Player | null;
  teamName?: string;
}

const ATTRIBUTE_LABELS: Record<keyof PlayerAttributes, string> = {
  speed: '速度',
  shooting: '射门',
  passing: '传球',
  dribbling: '盘带',
  defending: '防守',
  physical: '身体',
};

const POSITION_CN: Record<string, string> = {
  GK: '守门员', CB: '中后卫', LB: '左后卫', RB: '右后卫',
  LWB: '左边翼卫', RWB: '右边翼卫', CDM: '后腰', CM: '中前卫',
  CAM: '前腰', LM: '左中场', RM: '右中场', LW: '左边锋',
  RW: '右边锋', ST: '中锋', CF: '中锋', FW: '前锋',
  DF: '后卫', MF: '中场',
};

function StatItem({ label, value, highlight }: { label: string; value: string | number; highlight?: boolean }) {
  return (
    <div style={{
      background: highlight ? 'rgba(16, 185, 129, 0.12)' : 'rgba(255,255,255,0.04)',
      borderRadius: '0.5rem',
      padding: '0.6rem 0.5rem',
      textAlign: 'center',
    }}>
      <div style={{
        fontSize: 'clamp(1rem, 2vw, 1.2rem)',
        fontWeight: 700,
        color: highlight ? '#10b981' : '#e2e8f0',
      }}>
        {value}
      </div>
      <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
        {label}
      </div>
    </div>
  );
}

export default function PlayerInfoPanel({ player, teamName }: PlayerInfoPanelProps) {
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisBasis, setAnalysisBasis] = useState<string>('');
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const fetchAnalysis = useCallback(async () => {
    if (!player || !teamName) return;
    setAnalysisLoading(true);
    setAnalysisError(null);
    try {
      const result = await api.getPlayerAnalysis(teamName, player.name);
      setAnalysis(result.analysis);
      setAnalysisBasis(result.data_basis);
    } catch (err) {
      setAnalysisError('AI分析暂不可用');
    } finally {
      setAnalysisLoading(false);
    }
  }, [player, teamName]);

  useEffect(() => {
    setAnalysis(null);
    setAnalysisError(null);
    if (player) {
      fetchAnalysis();
    }
  }, [player, fetchAnalysis]);

  if (!player) {
    return (
      <div style={{
        width: '100%', minHeight: 'clamp(16rem, 45vh, 25rem)',
        border: '1px solid #333', borderRadius: '0.75rem',
        padding: 'var(--space-lg)', display: 'flex',
        flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        color: 'var(--text-muted)', background: 'rgba(20, 20, 30, 0.5)',
      }}>
        <div style={{ fontSize: 'clamp(2.5rem, 6vw, 3.5rem)', marginBottom: '1rem' }}>👈</div>
        <p style={{ fontSize: 'var(--text-base)' }}>点击战术板球员查看详细数据</p>
      </div>
    );
  }

  const attributes = player.attributes || { speed: 50, shooting: 50, passing: 50, dribbling: 50, defending: 50, physical: 50 };
  const stats = player.stats;
  const hasRealData = stats?.hasRealData;
  const dataSource = stats?.dataSource;

  const radarData = Object.entries(attributes).map(([key, value]) => ({
    subject: ATTRIBUTE_LABELS[key as keyof PlayerAttributes],
    value: Math.max(value, 10),
    fullMark: 100,
  }));

  return (
    <div style={{
      width: '100%', border: '1px solid #333', borderRadius: '0.75rem',
      padding: 'var(--space-lg)', background: 'rgba(20, 20, 30, 0.8)',
    }}>
      {/* Player header */}
      <div style={{ display: 'flex', gap: 'var(--space-md)', marginBottom: 'var(--space-lg)', flexWrap: 'wrap' }}>
        <div style={{
          width: 'clamp(4rem, 10vw, 5.625rem)', height: 'clamp(4rem, 10vw, 5.625rem)',
          borderRadius: '50%',
          background: player.avatar ? 'transparent' : 'linear-gradient(135deg, #10b981, #059669)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 'clamp(1.75rem, 5vw, 2.75rem)',
          border: '3px solid rgba(16, 185, 129, 0.5)', flexShrink: 0, overflow: 'hidden',
        }}>
          {player.avatar ? (
            <img src={player.avatar} alt={player.name}
              style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} />
          ) : '⚽'}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 style={{ fontSize: 'clamp(1.2rem, 2.5vw, 1.5rem)', fontWeight: 'bold', marginBottom: '0.25rem' }}>
            {player.nameCn || player.name}
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', marginBottom: '0.25rem' }}>
            {player.name}
          </p>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ padding: '0.2em 0.5em', background: 'rgba(16, 185, 129, 0.2)', borderRadius: '0.375rem', fontSize: 'var(--text-xs)', color: '#10b981' }}>
              #{player.number}
            </span>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
              {player.positionCn || POSITION_CN[player.position] || player.position}
            </span>
            {player.club && (
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                {player.club}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Data source badge */}
      <div style={{
        padding: '0.5rem 0.75rem', borderRadius: '0.5rem', marginBottom: 'var(--space-md)',
        background: hasRealData ? 'rgba(16, 185, 129, 0.1)' : 'rgba(234, 179, 8, 0.1)',
        border: hasRealData ? '1px solid rgba(16, 185, 129, 0.25)' : '1px solid rgba(234, 179, 8, 0.25)',
        fontSize: 'var(--text-xs)',
      }}>
        {hasRealData ? (
          <span style={{ color: '#10b981' }}>
            ✓ 真实比赛数据（{dataSource === 'desktop' ? '2025-26赛季' : dataSource || '外部数据源'}）
          </span>
        ) : (
          <span style={{ color: '#eab308' }}>
            △ 赛季数据暂缺，显示球员履历信息
          </span>
        )}
      </div>

      {/* Season stats — only show when real data exists */}
      {hasRealData && stats ? (
        <div style={{ marginBottom: 'var(--space-md)' }}>
          <h4 style={{ fontSize: 'var(--text-sm)', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>
            赛季数据
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.4rem', marginBottom: '0.5rem' }}>
            <StatItem label="出场" value={stats.appearances} highlight />
            <StatItem label="首发" value={`${stats.starts} (${stats.startRate ?? Math.round(stats.starts / Math.max(stats.appearances, 1) * 100)}%)`} />
            <StatItem label="时间" value={`${Math.floor(stats.minutes / 60)}h`} />
            <StatItem label="进球" value={stats.goals} highlight={stats.goals > 0} />
            <StatItem label="助攻" value={stats.assists} highlight={stats.assists > 0} />
            <StatItem label="射门" value={stats.shotsTotal ?? stats.shots ?? 0} />
            <StatItem label="射正率" value={stats.shotAccuracy ? `${stats.shotAccuracy}%` : '-'} />
            <StatItem label="黄牌" value={stats.yellowCards} />
          </div>
          {/* Second row: per-90 and advanced */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.4rem' }}>
            {stats.goalsP90 !== undefined && <StatItem label="每90分进球" value={stats.goalsP90.toFixed(2)} />}
            {stats.assistsP90 !== undefined && <StatItem label="每90分助攻" value={stats.assistsP90.toFixed(2)} />}
            {stats.tacklesWon !== undefined && <StatItem label="抢断" value={stats.tacklesWon} />}
            {stats.interceptions !== undefined && <StatItem label="拦截" value={stats.interceptions} />}
          </div>
          {/* W-D-L */}
          {stats.wins !== undefined && (
            <div style={{ marginTop: '0.5rem', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', display: 'flex', gap: '0.75rem' }}>
              <span style={{ color: '#10b981' }}>{stats.wins}胜</span>
              <span style={{ color: '#eab308' }}>{stats.draws}平</span>
              <span style={{ color: '#ef4444' }}>{stats.losses}负</span>
              <span>· 球队战绩</span>
            </div>
          )}
        </div>
      ) : (
        <div style={{ marginBottom: 'var(--space-md)', padding: '1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: 'var(--text-sm)', background: 'rgba(255,255,255,0.02)', borderRadius: '0.5rem' }}>
          暂无赛季比赛数据，待数据补充后显示
        </div>
      )}

      {/* Advanced stats from Sofascore */}
      {stats && (stats.passAccuracy || stats.xg !== undefined || stats.keyPasses !== undefined) && (
        <div style={{ marginBottom: 'var(--space-md)' }}>
          <h4 style={{ fontSize: 'var(--text-sm)', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>
            进阶数据 {stats.matchConfidence ? `(${stats.matchConfidence === 'high' ? '高可信度' : '中等可信度'})` : ''}
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.4rem' }}>
            {stats.xg !== undefined && stats.xg !== null && <StatItem label="xG" value={Number(stats.xg).toFixed(1)} />}
            {stats.passAccuracy !== undefined && stats.passAccuracy !== null && <StatItem label="传球%" value={`${stats.passAccuracy}%`} />}
            {stats.keyPasses !== undefined && stats.keyPasses !== null && <StatItem label="关键传" value={stats.keyPasses} />}
            {stats.dribbleSuccessRate !== undefined && stats.dribbleSuccessRate !== null && <StatItem label="过人%" value={`${stats.dribbleSuccessRate}%`} />}
            {stats.progressivePasses !== undefined && stats.progressivePasses !== null && <StatItem label="向前传" value={stats.progressivePasses} />}
          </div>
        </div>
      )}

      {/* Radar chart */}
      <div style={{ marginBottom: 'var(--space-md)' }}>
        <h4 style={{ fontSize: 'var(--text-sm)', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>
          能力雷达图
        </h4>
        <ResponsiveContainer width="100%" height={180}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="rgba(255,255,255,0.15)" />
            <PolarAngleAxis dataKey="subject" tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 12 }} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} />
            <Radar name="能力值" dataKey="value" stroke="#10b981" fill="#10b981" fillOpacity={0.25} strokeWidth={2} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* AI Scout Report */}
      <div style={{
        padding: '0.875rem', background: 'rgba(16, 185, 129, 0.06)',
        borderRadius: '0.625rem', border: '1px solid rgba(16, 185, 129, 0.15)',
      }}>
        <h4 style={{ fontSize: 'var(--text-sm)', marginBottom: '0.5rem', color: '#10b981' }}>
          AI 球探报告
        </h4>
        {analysisLoading ? (
          <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', textAlign: 'center', padding: '1rem' }}>
            AI 正在分析球员数据…
          </div>
        ) : analysisError ? (
          <div style={{ color: '#eab308', fontSize: 'var(--text-xs)' }}>{analysisError}</div>
        ) : analysis ? (
          <div>
            <div style={{ fontSize: 'var(--text-xs)', lineHeight: 1.85, color: '#d1d5db', whiteSpace: 'pre-wrap' }}>
              {analysis}
            </div>
            <div style={{ marginTop: '0.5rem', fontSize: '10px', color: 'var(--text-muted)' }}>
              数据依据：{analysisBasis || '赛季数据'}
            </div>
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-xs)' }}>点击球员查看 AI 分析</div>
        )}
      </div>

      <style jsx>{`
        @media (max-width: 767px) {
          .player-stats-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }
      `}</style>
    </div>
  );
}
