'use client';

import { useState } from 'react';
import api from '@/lib/api';
import type { Player, PlayerAttributes } from './types';
import type {
  PlayerFitResult,
  TeamStyleResult,
  TeamProfile6D,
  PositionComparison,
} from '@/lib/api';

interface Props {
  lineup: (Player | null)[];
  formation: string;
  teamName: string;
}

const ATTR_LABELS: Record<string, string> = {
  speed: '速度', shooting: '射门', passing: '传球',
  dribbling: '盘带', defending: '防守', physical: '身体',
};
const ATTR_COLORS: Record<string, string> = {
  speed: '#f43f5e', shooting: '#f97316', passing: '#3b82f6',
  dribbling: '#8b5cf6', defending: '#10b981', physical: '#eab308',
};
const FIT_LABELS: Record<string, { label: string; color: string }> = {
  excellent: { label: '顶级适配', color: '#10b981' },
  good: { label: '良好', color: '#3b82f6' },
  acceptable: { label: '合格', color: '#eab308' },
  poor: { label: '偏低', color: '#f97316' },
  misfit: { label: '不适配', color: '#ef4444' },
};

export default function TacticalAnalysis({ lineup, formation, teamName }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<{
    playerFits: (PlayerFitResult & { playerName: string; position: string })[];
    teamStyle: TeamStyleResult | null;
    teamProfile: TeamProfile6D | null;
  } | null>(null);

  const validLineup = lineup.filter((p): p is Player => p !== null && p.attributes !== undefined);

  const runAnalysis = async () => {
    if (validLineup.length === 0) return;
    setLoading(true);
    setError(null);

    try {
      // 1. 球员位置适配分析
      const positions = getFormationPositions(formation);
      const fitPromises = validLineup.map(async (player, i) => {
        const pos = positions[i] || player.position;
        const result = await api.scorePlayerFit(
          { ...player.attributes! } as Record<string, number>,
          pos,
          formation
        );
        return { ...result, playerName: player.name, position: pos };
      });
      const playerFits = await Promise.all(fitPromises);

      // 2. 球队风格识别
      const tacticalPlayers = validLineup.map((p, i) => ({
        name: p.name,
        player_id: p.id,
        position: positions[i] || p.position,
        attributes: { ...p.attributes! } as Record<string, number>,
      }));
      const teamStyle = await api.identifyTeamStyle(tacticalPlayers, formation);

      // 3. 球队属性画像（前端计算）
      const teamProfile = computeTeamProfile(validLineup, positions);

      setAnalysis({ playerFits, teamStyle, teamProfile });
    } catch (e) {
      setError(e instanceof Error ? e.message : '分析失败');
    } finally {
      setLoading(false);
    }
  };

  const avgFit = analysis
    ? Math.round(analysis.playerFits.reduce((s, f) => s + f.score, 0) / analysis.playerFits.length)
    : 0;

  return (
    <div style={{ marginTop: '1.5rem' }}>
      {/* 触发按钮 */}
      {!analysis && (
        <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
          <button
            onClick={runAnalysis}
            disabled={loading || validLineup.length === 0}
            style={{
              padding: '0.75rem 2rem',
              fontSize: '1rem',
              fontWeight: 600,
              borderRadius: '0.75rem',
              border: 'none',
              background: loading ? '#555' : 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              color: '#fff',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
            }}
          >
            {loading ? '正在分析…' : '开始战术分析'}
          </button>
          {validLineup.length === 0 && (
            <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', marginTop: '0.5rem' }}>
              需要先加载包含属性数据的球员阵容
            </p>
          )}
        </div>
      )}

      {/* 错误 */}
      {error && (
        <div style={{ padding: '0.75rem', background: 'rgba(239,68,68,0.1)', borderRadius: '0.5rem', color: '#ef4444', fontSize: 'var(--text-sm)', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {/* 加载中 */}
      {loading && (
        <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          正在从战术引擎获取分析结果…
        </div>
      )}

      {/* 分析结果 */}
      {analysis && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* 操作栏 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>
              {teamName} · {formation} 战术分析
            </h3>
            <button
              onClick={runAnalysis}
              disabled={loading}
              style={{
                padding: '0.4rem 1rem',
                fontSize: 'var(--text-sm)',
                borderRadius: '0.5rem',
                border: '1px solid #555',
                background: 'transparent',
                color: 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              重新分析
            </button>
          </div>

          {/* 总览卡: 风格 + 均分 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <StatCard
              title="识别风格"
              value={analysis.teamStyle?.primary_style?.style_name_cn || '未知'}
              subtitle={`整体适配均分: ${avgFit}/100`}
              color={avgFit >= 65 ? '#10b981' : avgFit >= 50 ? '#eab308' : '#ef4444'}
            />
            <StatCard
              title="阵型结构"
              value={formation}
              subtitle={`${validLineup.length} 名球员参与分析`}
              color="#3b82f6"
            />
          </div>

          {/* 备选风格 */}
          {analysis.teamStyle && analysis.teamStyle.top_styles.length > 1 && (
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {analysis.teamStyle.top_styles.map((s, i) => (
                <span
                  key={s.style_id}
                  style={{
                    padding: '0.2rem 0.6rem',
                    borderRadius: '1rem',
                    fontSize: 'var(--text-xs)',
                    background: i === 0 ? 'rgba(59,130,246,0.2)' : 'rgba(255,255,255,0.05)',
                    color: i === 0 ? '#3b82f6' : 'var(--text-muted)',
                    border: `1px solid ${i === 0 ? '#3b82f6' : '#333'}`,
                  }}
                >
                  {s.style_name_cn} {s.match_score}
                </span>
              ))}
            </div>
          )}

          {/* 6D属性雷达 */}
          {analysis.teamProfile && (
            <Section title="球队6D属性画像">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
                {Object.entries(ATTR_LABELS).map(([key, label]) => {
                  const val = analysis.teamProfile!.overall[key] || 60;
                  return (
                    <div key={key}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', marginBottom: '0.25rem' }}>
                        <span style={{ color: 'var(--text-muted)' }}>{label}</span>
                        <span style={{ fontWeight: 600, color: ATTR_COLORS[key] }}>{val}</span>
                      </div>
                      <div style={{ height: 4, background: '#222', borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${val}%`, background: ATTR_COLORS[key], borderRadius: 2, transition: 'width 0.5s' }} />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* 各线对比 */}
              {analysis.teamProfile.lines && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', marginTop: '0.75rem' }}>
                  {(['DEF', 'MID', 'FWD'] as const).map(line => {
                    const lineData = analysis.teamProfile!.lines[line];
                    if (!lineData) return null;
                    const lineNames: Record<string, string> = { DEF: '防线', MID: '中场', FWD: '锋线' };
                    const avg = Math.round(Object.values(lineData).reduce((a, b) => a + b, 0) / 6);
                    return (
                      <div key={line} style={{ padding: '0.5rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.5rem', textAlign: 'center' }}>
                        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>{lineNames[line]}</div>
                        <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{avg}</div>
                      </div>
                    );
                  })}
                </div>
              )}
            </Section>
          )}

          {/* 球员适配评分 */}
          <Section title="球员-位置适配评分">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {analysis.playerFits
                .sort((a, b) => b.score - a.score)
                .map((fit) => {
                  const fitInfo = FIT_LABELS[fit.fit] || FIT_LABELS.acceptable;
                  return (
                    <div
                      key={fit.playerName + fit.position}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem',
                        padding: '0.5rem 0.75rem',
                        background: 'rgba(255,255,255,0.03)',
                        borderRadius: '0.5rem',
                      }}
                    >
                      <div style={{ width: '6rem', fontSize: 'var(--text-sm)', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {fit.playerName}
                      </div>
                      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', width: '2.5rem' }}>
                        {fit.position}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ height: 4, background: '#222', borderRadius: 2, overflow: 'hidden' }}>
                          <div
                            style={{
                              height: '100%',
                              width: `${fit.score}%`,
                              background: fitInfo.color,
                              borderRadius: 2,
                              transition: 'width 0.5s',
                            }}
                          />
                        </div>
                      </div>
                      <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: fitInfo.color, width: '2.5rem', textAlign: 'right' }}>
                        {fit.score}
                      </div>
                      <div style={{ fontSize: 'var(--text-xs)', color: fitInfo.color, width: '3.5rem', textAlign: 'right' }}>
                        {fitInfo.label}
                      </div>
                    </div>
                  );
                })}
            </div>

            {/* 差距分析 */}
            {analysis.playerFits.some(f => f.gaps.length > 0) && (
              <details style={{ marginTop: '0.75rem' }}>
                <summary style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', cursor: 'pointer' }}>
                  查看差距分析
                </summary>
                <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {analysis.playerFits
                    .filter(f => f.gaps.length > 0)
                    .map(fit => (
                      <div key={fit.playerName} style={{ fontSize: 'var(--text-xs)' }}>
                        <span style={{ fontWeight: 600 }}>{fit.playerName}</span>
                        <span style={{ color: 'var(--text-muted)' }}> ({fit.position}): </span>
                        {fit.gaps.map(g => (
                          <span key={g.attribute} style={{ color: '#f97316', marginRight: '0.5rem' }}>
                            {ATTR_LABELS[g.attribute]} {g.direction}理想{g.gap}分
                          </span>
                        ))}
                      </div>
                    ))}
                </div>
              </details>
            )}
          </Section>
        </div>
      )}
    </div>
  );
}

/* ── 辅助组件 ──────────────────────────── */

function StatCard({ title, value, subtitle, color }: {
  title: string; value: string; subtitle: string; color: string;
}) {
  return (
    <div style={{
      padding: '0.75rem 1rem',
      background: 'rgba(255,255,255,0.04)',
      borderRadius: '0.75rem',
      border: '1px solid rgba(255,255,255,0.06)',
    }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{title}</div>
      <div style={{ fontSize: '1.3rem', fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '0.15rem' }}>{subtitle}</div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{
      padding: '1rem',
      background: 'rgba(255,255,255,0.03)',
      borderRadius: '0.75rem',
      border: '1px solid rgba(255,255,255,0.06)',
    }}>
      <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--text-muted)' }}>
        {title}
      </div>
      {children}
    </div>
  );
}

/* ── 工具函数 ──────────────────────────── */

function getFormationPositions(formation: string): string[] {
  const positions: Record<string, string[]> = {
    '4-3-3': ['GK', 'LB', 'CB', 'CB', 'RB', 'CM', 'CM', 'CM', 'LW', 'ST', 'RW'],
    '4-4-2': ['GK', 'LB', 'CB', 'CB', 'RB', 'LM', 'CM', 'CM', 'RM', 'ST', 'ST'],
    '3-5-2': ['GK', 'CB', 'CB', 'CB', 'LWB', 'CM', 'CM', 'CM', 'RWB', 'ST', 'ST'],
    '4-2-3-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'CDM', 'LW', 'CAM', 'RW', 'ST'],
    '3-4-3': ['GK', 'CB', 'CB', 'CB', 'LM', 'CM', 'CM', 'RM', 'LW', 'ST', 'RW'],
    '5-4-1': ['GK', 'LWB', 'CB', 'CB', 'CB', 'RWB', 'LM', 'CM', 'CM', 'RM', 'ST'],
    '4-1-4-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'LM', 'CM', 'CM', 'RM', 'ST'],
    '3-4-2-1': ['GK', 'CB', 'CB', 'CB', 'LM', 'CM', 'CM', 'RM', 'CAM', 'CAM', 'ST'],
    '4-3-2-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CM', 'CM', 'CM', 'CAM', 'CAM', 'ST'],
    '5-3-2': ['GK', 'LWB', 'CB', 'CB', 'CB', 'RWB', 'CM', 'CM', 'CM', 'ST', 'ST'],
  };
  return positions[formation] || Array.from({ length: 11 }, (_, i) => `P${i}`);
}

function computeTeamProfile(lineup: Player[], positions: string[]): TeamProfile6D {
  const overall: Record<string, number> = { speed: 0, shooting: 0, passing: 0, dribbling: 0, defending: 0, physical: 0 };
  const lines: Record<string, Record<string, number>> = { DEF: { ...overall }, MID: { ...overall }, FWD: { ...overall } };
  const counts: Record<string, number> = { DEF: 0, MID: 0, FWD: 0 };

  const attrKeys = ['speed', 'shooting', 'passing', 'dribbling', 'defending', 'physical'];

  lineup.forEach((player, i) => {
    const attrs = player.attributes as Record<string, number> | undefined;
    if (!attrs) return;
    const pos = positions[i] || player.position;
    const line = getPositionLine(pos);
    attrKeys.forEach(k => {
      const v = attrs[k] || 60;
      overall[k] += v;
      if (line !== 'GK' && line in lines) {
        lines[line][k] += v;
        counts[line] = (counts[line] || 0) + 1;
      }
    });
  });

  const total = lineup.length || 1;
  attrKeys.forEach(k => { overall[k] = Math.round(overall[k] / total); });
  (['DEF', 'MID', 'FWD'] as const).forEach(line => {
    const c = counts[line] || 1;
    attrKeys.forEach(k => { lines[line][k] = Math.round(lines[line][k] / c); });
  });

  return { overall, lines };
}

function getPositionLine(pos: string): 'DEF' | 'MID' | 'FWD' | 'GK' {
  if (pos === 'GK') return 'GK';
  if (['CB', 'LB', 'RB', 'LWB', 'RWB', 'DF'].includes(pos)) return 'DEF';
  if (['CDM', 'CM', 'CAM', 'LM', 'RM', 'MF'].includes(pos)) return 'MID';
  return 'FWD';
}
