'use client';

import type { GroupStageInsight, GroupStageTeamSummary } from '@/lib/api';

interface Props {
  insight?: GroupStageInsight | null;
}

function record(summary: GroupStageTeamSummary) {
  return `${summary.wins}胜${summary.draws}平${summary.losses}负`;
}

function keyPlayers(summary: GroupStageTeamSummary) {
  if (!summary.key_players?.length) return '暂无';
  return summary.key_players.map(player => `${player.name} ${player.goals}球`).join('、');
}

function TeamSummaryCard({ summary }: { summary: GroupStageTeamSummary }) {
  return (
    <div style={{
      padding: '0.85rem',
      borderRadius: '0.5rem',
      background: 'rgba(255,255,255,0.035)',
      border: '1px solid rgba(255,255,255,0.06)',
      minWidth: 0,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', marginBottom: '0.65rem' }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ color: '#e2e8f0', fontSize: 'var(--text-sm)', fontWeight: 700 }}>
            {summary.team_cn || summary.team}
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '10px', marginTop: '0.15rem' }}>
            小组赛已获取 {summary.matches} 场
          </div>
        </div>
        <div style={{ color: '#10b981', fontSize: 'var(--text-xs)', fontWeight: 700, whiteSpace: 'nowrap' }}>
          {record(summary)}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.4rem', marginBottom: '0.65rem' }}>
        <Metric value={`${summary.goals_for}/${summary.goals_against}`} label="进/失球" />
        <Metric value={`${summary.shots_on_target}/${summary.shots}`} label="射正/射门" />
        <Metric value={`${summary.avg_possession}%`} label="控球率" />
      </div>

      <div style={{ color: 'var(--text-muted)', fontSize: '11px', lineHeight: 1.7 }}>
        传球成功率 {summary.pass_accuracy}% · 角球 {summary.corners} · 黄牌 {summary.yellow_cards}
      </div>
      <div style={{ color: '#cbd5e1', fontSize: '11px', lineHeight: 1.7, marginTop: '0.25rem' }}>
        关键球员：{keyPlayers(summary)}
      </div>
    </div>
  );
}

function Metric({ value, label }: { value: string | number; label: string }) {
  return (
    <div style={{
      textAlign: 'center',
      padding: '0.45rem 0.35rem',
      borderRadius: '0.375rem',
      background: 'rgba(15,23,42,0.55)',
    }}>
      <div style={{ color: '#f8fafc', fontSize: 'var(--text-sm)', fontWeight: 700 }}>{value}</div>
      <div style={{ color: 'var(--text-muted)', fontSize: '10px', marginTop: '0.1rem' }}>{label}</div>
    </div>
  );
}

export default function GroupStageInsightPanel({ insight }: Props) {
  if (!insight?.available) return null;

  return (
    <section style={{
      padding: '1rem',
      borderRadius: '0.75rem',
      border: '1px solid rgba(16,185,129,0.16)',
      background: 'linear-gradient(135deg, rgba(16,185,129,0.06), rgba(15,23,42,0.72))',
      marginBottom: '0.85rem',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
        <div>
          <h3 style={{ fontSize: 'var(--text-base)', color: '#e2e8f0', fontWeight: 800, margin: 0 }}>
            小组赛实时数据洞察
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '10px', margin: '0.2rem 0 0' }}>
            {insight.source} · {insight.generated_by_ai ? 'AI分析' : '规则分析'}
          </p>
        </div>
      </div>

      <div className="group-stage-team-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.65rem', marginBottom: '0.75rem' }}>
        <TeamSummaryCard summary={insight.home} />
        <TeamSummaryCard summary={insight.away} />
      </div>

      {insight.comparison?.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.75rem' }}>
          {insight.comparison.map((point, index) => (
            <span key={index} style={{
              color: '#a7f3d0',
              background: 'rgba(16,185,129,0.09)',
              border: '1px solid rgba(16,185,129,0.16)',
              borderRadius: '999px',
              padding: '0.25rem 0.55rem',
              fontSize: '10px',
              lineHeight: 1.45,
            }}>
              {point}
            </span>
          ))}
        </div>
      )}

      <div style={{
        color: '#d1d5db',
        fontSize: 'var(--text-xs)',
        lineHeight: 1.85,
        whiteSpace: 'pre-wrap',
      }}>
        {insight.analysis}
      </div>

      <style jsx>{`
        @media (max-width: 767px) {
          .group-stage-team-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </section>
  );
}
