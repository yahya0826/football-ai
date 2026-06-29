'use client';

import { useState, useEffect, useCallback } from 'react';
import Image from 'next/image';
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
  G: '守门员',
  LWB: '左边翼卫', RWB: '右边翼卫', CDM: '后腰', CM: '中场',
  CAM: '前腰', LM: '左中场', RM: '右中场', LW: '左边锋',
  RW: '右边锋', ST: '前锋', CF: '前锋', FW: '前锋',
  DF: '后卫', MF: '中场',
};

type PositionGroup = 'GK' | 'DF' | 'MF' | 'FW';
type StatItemData = { label: string; value: string | number; highlight?: boolean };

function StatItem({ label, value, highlight }: StatItemData) {
  return (
    <div style={{
      background: highlight ? 'rgba(16, 185, 129, 0.12)' : 'rgba(255,255,255,0.04)',
      borderRadius: '0.5rem',
      padding: '0.6rem 0.5rem',
      textAlign: 'center',
      minWidth: 0,
    }}>
      <div style={{
        fontSize: 'clamp(0.95rem, 2vw, 1.15rem)',
        fontWeight: 700,
        color: highlight ? '#10b981' : '#e2e8f0',
        overflowWrap: 'anywhere',
      }}>
        {value}
      </div>
      <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '0.2rem', lineHeight: 1.35 }}>
        {label}
      </div>
    </div>
  );
}

function getPositionGroup(position: string, positionCn?: string): PositionGroup {
  const normalized = position.trim().toUpperCase();
  if (['GK', 'G', 'GOALKEEPER'].includes(normalized) || positionCn?.includes('门')) return 'GK';
  if (['CB', 'LB', 'RB', 'LWB', 'RWB', 'DF'].includes(normalized)) return 'DF';
  if (['CDM', 'CM', 'CAM', 'LM', 'RM', 'MF'].includes(normalized)) return 'MF';
  return 'FW';
}

function formatNumber(value: number | undefined | null, digits = 0): string | number {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return '-';
  return digits > 0 ? Number(value).toFixed(digits) : value;
}

function percent(value: number | undefined | null): string {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return '-';
  return `${value}%`;
}

function ratio(numerator: number | undefined | null, denominator: number | undefined | null): string {
  if (numerator === undefined || numerator === null || denominator === undefined || denominator === null) return '-';
  const n = Number(numerator);
  const d = Number(denominator);
  if (Number.isNaN(n) || Number.isNaN(d)) return '-';
  if (d <= 0) return `${n}/0`;
  return `${n}/${d} (${Math.round((n / d) * 100)}%)`;
}

function getPositionStats(player: Player): StatItemData[] {
  const stats = player.stats;
  if (!stats) return [];

  const shots = stats.shots ?? stats.shotsTotal;
  const tackles = stats.tacklesWon ?? stats.tackles;
  const shotsOnTargetAgainst = stats.shotsOnTargetAgainst
    ?? (stats.saves !== undefined && stats.goalsConceded !== undefined
      ? stats.saves + stats.goalsConceded
      : undefined);
  const savePct = stats.savePct
    ?? (shotsOnTargetAgainst && stats.saves !== undefined
      ? Number(((stats.saves / shotsOnTargetAgainst) * 100).toFixed(1))
      : undefined);

  switch (getPositionGroup(player.position, player.positionCn)) {
    case 'GK':
      return [
        { label: 'SoTA 对手射正', value: formatNumber(shotsOnTargetAgainst) },
        { label: 'GA 失球', value: formatNumber(stats.goalsConceded) },
        { label: 'Saves 扑救', value: formatNumber(stats.saves), highlight: (stats.saves ?? 0) > 0 },
        { label: 'Save% 扑救率', value: percent(savePct), highlight: (savePct ?? 0) >= 70 },
        { label: 'CS 零封', value: formatNumber(stats.cleanSheets), highlight: (stats.cleanSheets ?? 0) > 0 },
        { label: 'PKatt 对手点球', value: formatNumber(stats.pkAttempted) },
        { label: 'PKA 点球失球', value: formatNumber(stats.penaltyGoalsAllowed) },
        { label: 'PKsv 点球扑救', value: formatNumber(stats.penaltySaves), highlight: (stats.penaltySaves ?? 0) > 0 },
      ];
    case 'DF':
      return [
        { label: 'Gls 进球', value: stats.goals, highlight: stats.goals > 0 },
        { label: 'Ast 助攻', value: stats.assists, highlight: stats.assists > 0 },
        { label: 'PK 点球进球', value: formatNumber(stats.pkScored), highlight: (stats.pkScored ?? 0) > 0 },
        { label: 'PKatt 主罚点球', value: formatNumber(stats.pkAttempted) },
        { label: 'CrdY 黄牌', value: stats.yellowCards },
        { label: 'CrdR 红牌', value: stats.redCards },
        { label: 'Fls 犯规', value: formatNumber(stats.fouls) },
        { label: 'Crs 传中', value: formatNumber(stats.crosses), highlight: (stats.crosses ?? 0) > 0 },
        { label: 'TklW 抢断', value: formatNumber(tackles), highlight: (tackles ?? 0) > 0 },
        { label: 'Int 拦截', value: formatNumber(stats.interceptions), highlight: (stats.interceptions ?? 0) > 0 },
        { label: 'OG 乌龙球', value: formatNumber(stats.ownGoals) },
      ];
    case 'MF':
      return [
        { label: 'Gls 进球', value: stats.goals, highlight: stats.goals > 0 },
        { label: 'Ast 助攻', value: stats.assists, highlight: stats.assists > 0 },
        { label: 'PK 点球进球', value: formatNumber(stats.pkScored), highlight: (stats.pkScored ?? 0) > 0 },
        { label: 'PKatt 主罚点球', value: formatNumber(stats.pkAttempted) },
        { label: 'SoT/Sh 射正/射门', value: ratio(stats.shotsOnTarget, shots) },
        { label: 'CrdY 黄牌', value: stats.yellowCards },
        { label: 'CrdR 红牌', value: stats.redCards },
        { label: 'Fls 犯规', value: formatNumber(stats.fouls) },
        { label: 'Fld 被犯规', value: formatNumber(stats.fouled), highlight: (stats.fouled ?? 0) > 0 },
        { label: 'Crs 传中', value: formatNumber(stats.crosses), highlight: (stats.crosses ?? 0) > 0 },
        { label: '关键传球', value: formatNumber(stats.keyPasses), highlight: (stats.keyPasses ?? 0) > 0 },
        { label: 'TklW 抢断', value: formatNumber(tackles), highlight: (tackles ?? 0) > 0 },
        { label: 'Int 拦截', value: formatNumber(stats.interceptions), highlight: (stats.interceptions ?? 0) > 0 },
      ];
    case 'FW':
      return [
        { label: 'Gls 进球', value: stats.goals, highlight: stats.goals > 0 },
        { label: 'Ast 助攻', value: stats.assists, highlight: stats.assists > 0 },
        { label: 'PK 点球进球', value: formatNumber(stats.pkScored), highlight: (stats.pkScored ?? 0) > 0 },
        { label: 'PKatt 主罚点球', value: formatNumber(stats.pkAttempted) },
        { label: 'SoT/Sh 射正/射门', value: ratio(stats.shotsOnTarget, shots), highlight: (stats.shotsOnTarget ?? 0) > 0 },
        { label: 'Fld 被犯规', value: formatNumber(stats.fouled), highlight: (stats.fouled ?? 0) > 0 },
        { label: 'Off 越位', value: formatNumber(stats.offsides) },
        { label: 'Crs 传中', value: formatNumber(stats.crosses), highlight: (stats.crosses ?? 0) > 0 },
        { label: '每90分钟进球', value: formatNumber(stats.goalsP90, 2), highlight: (stats.goalsP90 ?? 0) > 0.3 },
      ];
  }
}

export default function PlayerInfoPanel({ player, teamName }: PlayerInfoPanelProps) {
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisBasis, setAnalysisBasis] = useState<string>('');
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [chartReady, setChartReady] = useState(false);

  const fetchAnalysis = useCallback(async () => {
    if (!player || !teamName) return;
    setAnalysisLoading(true);
    setAnalysisError(null);
    try {
      const result = await api.getPlayerAnalysis(teamName, player.name);
      setAnalysis(result.analysis);
      setAnalysisBasis(result.data_basis);
    } catch {
      setAnalysisError('AI分析暂不可用');
    } finally {
      setAnalysisLoading(false);
    }
  }, [player, teamName]);

  useEffect(() => {
    let mounted = true;
    Promise.resolve().then(() => {
      if (!mounted) return;
      setAnalysis(null);
      setAnalysisError(null);
      if (player) {
        fetchAnalysis();
      }
    });
    return () => { mounted = false; };
  }, [player, fetchAnalysis]);

  useEffect(() => {
    const id = requestAnimationFrame(() => setChartReady(true));
    return () => cancelAnimationFrame(id);
  }, []);

  if (!player) {
    return (
      <div style={{
        width: '100%', minHeight: 'clamp(16rem, 45vh, 25rem)',
        border: '1px solid #333', borderRadius: '0.75rem',
        padding: 'var(--space-lg)', display: 'flex',
        flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        color: 'var(--text-muted)', background: 'rgba(20, 20, 30, 0.5)',
      }}>
        <div style={{ fontSize: 'clamp(2.5rem, 6vw, 3.5rem)', marginBottom: '1rem' }}>←</div>
        <p style={{ fontSize: 'var(--text-base)' }}>点击战术板球员查看详细数据</p>
      </div>
    );
  }

  const attributes = player.attributes || { speed: 50, shooting: 50, passing: 50, dribbling: 50, defending: 50, physical: 50 };
  const stats = player.stats;
  const hasRealData = stats?.hasRealData;
  const dataSource = stats?.dataSource;
  const positionStats = getPositionStats(player);
  const basicStats: StatItemData[] = stats ? [
    { label: '出场次数', value: stats.appearances, highlight: stats.appearances > 0 },
    { label: '首发', value: stats.starts, highlight: stats.starts > 0 },
    { label: '评分', value: formatNumber(stats.rating, 1), highlight: stats.rating >= 7 },
  ] : [];

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
            <Image
              src={player.avatar}
              alt={player.name}
              width={90}
              height={90}
              unoptimized
              style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }}
            />
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

      {hasRealData && stats ? (
        <div style={{ marginBottom: 'var(--space-md)' }}>
          <h4 style={{ fontSize: 'var(--text-sm)', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>
            基础数据
          </h4>
          <div className="player-stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.4rem', marginBottom: '0.75rem' }}>
            {basicStats.map((item) => (
              <StatItem key={item.label} label={item.label} value={item.value} highlight={item.highlight} />
            ))}
          </div>
          <h4 style={{ fontSize: 'var(--text-sm)', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>
            位置关注指标
          </h4>
          <div className="player-stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.4rem' }}>
            {positionStats.map((item) => (
              <StatItem key={item.label} label={item.label} value={item.value} highlight={item.highlight} />
            ))}
          </div>
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

      <div style={{ marginBottom: 'var(--space-md)' }}>
        <h4 style={{ fontSize: 'var(--text-sm)', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>
          能力雷达图
        </h4>
        {chartReady ? (
          <ResponsiveContainer width="100%" height={180}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,0.15)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 12 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} />
              <Radar name="能力值" dataKey="value" stroke="#10b981" fill="#10b981" fillOpacity={0.25} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        ) : null}
      </div>

      <div style={{
        padding: '0.875rem', background: 'rgba(16, 185, 129, 0.06)',
        borderRadius: '0.625rem', border: '1px solid rgba(16, 185, 129, 0.15)',
      }}>
        <h4 style={{ fontSize: 'var(--text-sm)', marginBottom: '0.5rem', color: '#10b981' }}>
          AI 球探报告
        </h4>
        {analysisLoading ? (
          <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', textAlign: 'center', padding: '1rem' }}>
            AI 正在分析球员数据...
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
