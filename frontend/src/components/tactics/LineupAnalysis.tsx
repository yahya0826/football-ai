'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts';
import { Player } from './types';
import api from '@/lib/api';
import type { LineupEvalResponse, SetPieceInfo, TeamProjection } from '@/lib/api';

interface LineupAnalysisProps {
  lineup: (Player | null)[];
  formationId: string;
  teamName: string;
}

const DIM_LABELS: Record<string, string> = {
  player_quality: '球员能力',
  balance: '阵容平衡',
  chemistry: '磨合度',
  attack_defense: '攻防均衡',
};

function scoreColor(score: number): string {
  if (score >= 75) return '#10b981';
  if (score >= 55) return '#eab308';
  return '#ef4444';
}

function scoreLabel(score: number): string {
  if (score >= 80) return '优秀';
  if (score >= 65) return '良好';
  if (score >= 50) return '一般';
  if (score >= 35) return '较弱';
  return '不足';
}

export default function LineupAnalysis({ lineup, formationId, teamName }: LineupAnalysisProps) {
  const [data, setData] = useState<LineupEvalResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chartReady, setChartReady] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchAnalysis = useCallback(async () => {
    const filledPlayers = lineup.filter(p => p !== null);
    if (filledPlayers.length === 0 || !teamName) return;

    setLoading(true);
    setError(null);

    try {
      const evalPlayers = lineup.map(p => {
        if (!p) return { id: '', name: '', position: '', club: null, stats: null };
        return {
          id: p.id,
          name: p.name,
          position: p.position,
          club: p.club || null,
          stats: p.stats ? { ...p.stats } : null,
        };
      });

      const result = await api.evaluateLineup({
        lineup: evalPlayers,
        formation_id: formationId,
        team_name: teamName,
      });
      setData(result);
    } catch {
      setError('评估暂不可用');
    } finally {
      setLoading(false);
    }
  }, [lineup, formationId, teamName]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(fetchAnalysis, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [fetchAnalysis]);

  useEffect(() => {
    const id = requestAnimationFrame(() => setChartReady(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const overall = data?.overall_score ?? 0;
  const dimensions = data?.dimensions;

  const radarData = dimensions
    ? Object.entries(dimensions).map(([key, value]) => ({
      subject: DIM_LABELS[key] || key,
      value: Math.max(value, 5),
      fullMark: 100,
    }))
    : [];

  return (
    <div style={{
      flex: '0 0 280px',
      minWidth: '240px',
      maxWidth: '320px',
      border: '1px solid #333',
      borderRadius: '0.75rem',
      padding: 'var(--space-md)',
      background: 'rgba(20, 20, 30, 0.8)',
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-md)',
    }}>
      {/* Title */}
      <div style={{
        fontSize: 'var(--text-sm)',
        fontWeight: 600,
        color: '#e2e8f0',
        borderBottom: '1px solid #333',
        paddingBottom: '0.5rem',
      }}>
        球队阵容分析
      </div>

      {/* Overall Score */}
      <div style={{ textAlign: 'center' }}>
        <div style={{
          fontSize: 'clamp(2.5rem, 5vw, 3.5rem)',
          fontWeight: 800,
          color: scoreColor(overall),
          lineHeight: 1,
        }}>
          {loading && !data ? '...' : overall}
        </div>
        <div style={{
          fontSize: 'var(--text-xs)',
          color: scoreColor(overall),
          fontWeight: 600,
        }}>
          {loading && !data ? '计算中...' : scoreLabel(overall)}
        </div>
      </div>

      {/* Radar chart */}
      <div style={{ height: 170 }}>
        {chartReady ? (
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={radarData}>
            <PolarGrid stroke="rgba(255,255,255,0.12)" />
            <PolarAngleAxis
              dataKey="subject"
              tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 9 }}
            />
            <Radar
              name="评分"
              dataKey="value"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.2}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>
        ) : null}
      </div>

      {/* Loading / Error */}
      {loading && !data && (
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', textAlign: 'center' }}>
          分析中...
        </div>
      )}
      {error && (
        <div style={{ fontSize: 'var(--text-xs)', color: '#eab308' }}>{error}</div>
      )}

      {/* Set Pieces */}
      {data?.set_pieces && (
        <SetPieceSection sp={data.set_pieces} />
      )}

      {/* Team Projections */}
      {data?.projection && (
        <ProjectionSection proj={data.projection} />
      )}
    </div>
  );
}

function SetPieceSection({ sp }: { sp: SetPieceInfo }) {
  return (
    <div style={{
      padding: '0.625rem',
      background: 'rgba(59, 130, 246, 0.06)',
      borderRadius: '0.5rem',
      border: '1px solid rgba(59, 130, 246, 0.15)',
    }}>
      <div style={{
        fontSize: 'var(--text-xs)',
        fontWeight: 600,
        color: '#60a5fa',
        marginBottom: '0.4rem',
      }}>
        定位球主罚
      </div>
      <div style={{ fontSize: 'var(--text-xs)', color: '#d1d5db', lineHeight: 1.7 }}>
        <div>点球: <span style={{ color: '#e2e8f0' }}>{sp.penalty}</span></div>
        <div>角球: <span style={{ color: '#e2e8f0' }}>{sp.corners.join(', ')}</span></div>
        <div>任意球: <span style={{ color: '#e2e8f0' }}>{sp.free_kick}</span></div>
      </div>
    </div>
  );
}

function ProjectionSection({ proj }: { proj: TeamProjection }) {
  const tierLabels: Record<string, string> = {
    champion_contender: '争冠热门',
    dark_horse: '潜在黑马',
    round_of_16: '16强实力',
    group_stage: '小组赛',
  };

  return (
    <div style={{
      padding: '0.625rem',
      background: 'rgba(168, 85, 247, 0.06)',
      borderRadius: '0.5rem',
      border: '1px solid rgba(168, 85, 247, 0.15)',
    }}>
      <div style={{
        fontSize: 'var(--text-xs)',
        fontWeight: 600,
        color: '#a78bfa',
        marginBottom: '0.4rem',
      }}>
        球队预测
      </div>
      <div style={{ fontSize: 'var(--text-xs)', color: '#d1d5db', lineHeight: 1.7 }}>
        <div>胜率: <span style={{ color: '#e2e8f0' }}>{proj.win_pct}%</span></div>
        <div>预期进球: <span style={{ color: '#e2e8f0' }}>{proj.proj_goals}</span></div>
        {proj.exp_games && (
          <div>预期场次: <span style={{ color: '#e2e8f0' }}>{proj.exp_games}场</span></div>
        )}
        {proj.tier && tierLabels[proj.tier] && (
          <div>层级: <span style={{ color: '#e2e8f0' }}>{tierLabels[proj.tier]}</span></div>
        )}
      </div>
    </div>
  );
}
