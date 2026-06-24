'use client';

import { useState, useCallback, useEffect } from 'react';
import TacticalBoard from './TacticalBoard';
import PlayerInfoPanel from './PlayerInfoPanel';
import SquadList from './SquadList';
import TacticalAnalysis from './TacticalAnalysis';
import LineupAnalysis from './LineupAnalysis';
import { Player, FORMATIONS, Formation, apiPlayerToPlayer } from './types';
import api from '@/lib/api';
import type { PlayersIndexResponse } from '@/lib/api';

const FORMATION_POSITIONS = [
  'GK', 'LB', 'CB', 'CB', 'RB',
  'CM', 'CM', 'CM',
  'LW', 'ST', 'RW',
];

const TEAM_NAMES_CN: Record<string, string> = {
  'England': '英格兰', 'France': '法国', 'Croatia': '克罗地亚', 'Norway': '挪威',
  'Portugal': '葡萄牙', 'Germany': '德国', 'Netherlands': '荷兰', 'Switzerland': '瑞士',
  'Scotland': '苏格兰', 'Spain': '西班牙', 'Austria': '奥地利', 'Belgium': '比利时',
  'Bosnia and Herzegovina': '波黑', 'Sweden': '瑞典',
  'Turkey': '土耳其', 'Czech Republic': '捷克',
  'Argentina': '阿根廷', 'Brazil': '巴西', 'Colombia': '哥伦比亚', 'Ecuador': '厄瓜多尔',
  'Paraguay': '巴拉圭', 'Uruguay': '乌拉圭',
  'Australia': '澳大利亚', 'Iran': '伊朗', 'Japan': '日本', 'Jordan': '约旦',
  'Uzbekistan': '乌兹别克斯坦', 'Qatar': '卡塔尔', 'Saudi Arabia': '沙特阿拉伯',
  'South Korea': '韩国', 'Iraq': '伊拉克',
  'Algeria': '阿尔及利亚', 'Cape Verde': '佛得角', 'DR Congo': '刚果民主共和国',
  'Egypt': '埃及', 'Ghana': '加纳', 'Ivory Coast': '科特迪瓦', 'Morocco': '摩洛哥',
  'Senegal': '塞内加尔', 'South Africa': '南非', 'Tunisia': '突尼斯',
  'United States': '美国', 'Mexico': '墨西哥', 'Canada': '加拿大',
  'Panama': '巴拿马', 'Haiti': '海地', 'Curaçao': '库拉索', 'New Zealand': '新西兰',
};

function teamDisplayName(en: string): string {
  return TEAM_NAMES_CN[en] || en;
}

export default function TacticsPage() {
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [currentFormation, setCurrentFormation] = useState<Formation>(FORMATIONS['4-3-3']);
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [availableTeams, setAvailableTeams] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [lineup, setLineup] = useState<(Player | null)[]>(
    Array.from({ length: 11 }, () => null)
  );
  const [squad, setSquad] = useState<Player[]>([]);

  useEffect(() => {
    api.getPlayersIndex().then((index: PlayersIndexResponse) => {
      const teams = Object.keys(index.teams || {}).sort();
      setAvailableTeams(teams);
      if (teams.length > 0 && !selectedTeam) {
        setSelectedTeam(teams[0]);
      }
    }).catch(() => {
      api.getTeams().then(res => {
        const teams = res.teams.map(t => t.team_en).sort();
        setAvailableTeams(teams);
        if (teams.length > 0 && !selectedTeam) {
          setSelectedTeam(teams[0]);
        }
      }).catch(() => {
        setError('Cannot connect to backend');
      });
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!selectedTeam) return;

    let mounted = true;
    Promise.resolve().then(() => {
      if (mounted) {
        setLoading(true);
        setError(null);
      }
    });

    Promise.all([
      api.getTeamPlayers(selectedTeam),
      api.getPredictedLineup(selectedTeam).catch(() => null),
    ])
      .then(([data, predicted]) => {
        if (!mounted) return;
        const players = data.players.map(apiPlayerToPlayer);
        setSquad(players);

        if (predicted && predicted.players.length > 0) {
          // Use predicted lineup as default
          const predictedPlayers: Player[] = predicted.players.map(pp => {
            // If matched to real player, use that data; otherwise create synthetic player
            const realPlayer = players.find(p => p.id === pp.id);
            if (realPlayer) return realPlayer;
            // Unmatched predicted player — create a placeholder
            return {
              id: pp.id,
              name: pp.name,
              position: pp.position,
              number: pp.number,
              club: pp.club || undefined,
              avatar: pp.avatar || undefined,
              stats: undefined,
              attributes: undefined,
            };
          });

          // Build lineup from predicted positions
          const positions = predicted.positions.length === 11 ? predicted.positions : FORMATION_POSITIONS;
          const newLineup: (Player | null)[] = Array.from({ length: 11 }, () => null);

          for (let i = 0; i < Math.min(positions.length, 11); i++) {
            if (i < predictedPlayers.length) {
              newLineup[i] = predictedPlayers[i];
            }
          }

          setLineup(newLineup);

          // Set formation from predicted data
          const predictedFormation = predicted.formation || '4-3-3';
          if (FORMATIONS[predictedFormation]) {
            setCurrentFormation(FORMATIONS[predictedFormation]);
          }
        } else {
          // Fallback: auto-assign by position
          const newLineup = buildLineup(players, FORMATION_POSITIONS);
          setLineup(newLineup);
          setCurrentFormation(FORMATIONS['4-3-3']);
        }

        setSelectedPlayer(null);
      })
      .catch(() => {
        if (!mounted) return;
        setError('无法连接后端服务，请确认后端已启动（端口8000）');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => { mounted = false; };
  }, [selectedTeam]);

  const handlePlayerClick = useCallback((player: Player) => {
    setSelectedPlayer(player);
  }, []);

  const handleSwapPlayer = useCallback((fromIndex: number, toIndex: number) => {
    setLineup(prev => {
      const newLineup = [...prev];
      [newLineup[fromIndex], newLineup[toIndex]] = [newLineup[toIndex], newLineup[fromIndex]];
      return newLineup;
    });
  }, []);

  /** 战术板球员 与 大名单球员 互换 */
  const handleSwapBoardWithSquad = useCallback((lineupIndex: number, squadPlayerId: string) => {
    setLineup(prev => {
      const newLineup = [...prev];
      const squadPlayer = squad.find(p => p.id === squadPlayerId) || null;
      const existingIndex = newLineup.findIndex(p => p?.id === squadPlayerId);
      if (existingIndex >= 0) {
        // squad player already in lineup: swap the two positions
        [newLineup[lineupIndex], newLineup[existingIndex]] = [newLineup[existingIndex], newLineup[lineupIndex]];
      } else {
        newLineup[lineupIndex] = squadPlayer;
      }
      return newLineup;
    });
  }, [squad]);

  const handleFormationChange = useCallback((formation: Formation) => {
    setCurrentFormation(formation);
  }, []);

  const handleTeamChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedTeam(e.target.value);
  }, []);

  return (
    <div style={{
      padding: 'var(--space-md)',
      minHeight: 'calc(100vh - 120px)',
      maxWidth: 'var(--container-max)',
      margin: '0 auto',
      width: '100%',
    }}>
      {/* Header */}
      <div style={{
        marginBottom: '1rem',
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
      }}>
        <div>
          <h1 className="page-title" style={{ marginBottom: '0.25rem' }}>
            战术分析
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>
            拖拽球员交换位置 · 点击查看详细数据
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <label style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
            球队:
          </label>
          <select
            value={selectedTeam}
            onChange={handleTeamChange}
            style={{
              padding: '0.5em 1em',
              fontSize: 'var(--text-sm)',
              borderRadius: '0.5rem',
              border: '1px solid #444',
              background: 'rgba(20, 20, 30, 0.9)',
              color: '#fff',
              cursor: 'pointer',
              minWidth: '10rem',
            }}
          >
            {availableTeams.map(team => (
              <option key={team} value={team}>{teamDisplayName(team)}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Loading / Error */}
      {loading && (
        <div style={{
          padding: '1rem',
          background: 'rgba(16, 185, 129, 0.1)',
          borderRadius: '0.5rem',
          marginBottom: '1rem',
          fontSize: 'var(--text-sm)',
        }}>
          Loading player data...
        </div>
      )}
      {error && (
        <div style={{
          padding: '1rem',
          background: 'rgba(234, 179, 8, 0.1)',
          borderRadius: '0.5rem',
          marginBottom: '1rem',
          fontSize: 'var(--text-sm)',
          color: '#eab308',
        }}>
          {error}
        </div>
      )}

      {!loading && !error && squad.length > 0 && (
        <div style={{
          marginBottom: '0.75rem',
          fontSize: 'var(--text-xs)',
          color: 'var(--text-muted)',
        }}>
          {squad.length} players,
          {squad.filter(p => p.stats?.matchConfidence === 'high' || p.stats?.matchConfidence === 'medium').length} with real data
          {selectedTeam && (
            <span> · Source: 2025-26 season (Sofascore + FPL)</span>
          )}
        </div>
      )}

      {/* Main layout: LineupAnalysis (left) | TacticalBoard + PlayerInfo (center) | SquadList (far right) */}
      <div className="tactics-layout" style={{
        display: 'flex',
        gap: 'var(--space-md)',
        alignItems: 'flex-start',
      }}>
        {/* Far Left: Lineup Analysis */}
        <div className="tactics-lineup-analysis">
          <LineupAnalysis
            lineup={lineup}
            formationId={currentFormation.id}
            teamName={selectedTeam}
          />
        </div>

        {/* Center: Tactical Board + PlayerInfoPanel + TacticalAnalysis */}
        <div className="tactics-board-column" style={{
          flex: '1 1 auto',
          minWidth: 0,
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-md)',
        }}>
          <TacticalBoard
            lineup={lineup}
            formation={currentFormation}
            selectedPlayerId={selectedPlayer?.id || null}
            onPlayerClick={handlePlayerClick}
            onSwapPlayer={handleSwapPlayer}
            onFormationChange={handleFormationChange}
            onSwapWithSquad={handleSwapBoardWithSquad}
          />

          {/* Player info panel below tactical board */}
          <PlayerInfoPanel player={selectedPlayer} teamName={selectedTeam} />

          {/* Tactical Analysis */}
          <TacticalAnalysis
            lineup={lineup}
            formation={currentFormation.id}
            teamName={selectedTeam}
          />
        </div>

        {/* Far right: SquadList */}
        <div className="tactics-squad-panel" style={{
          flex: '0 0 20%',
          minWidth: '10rem',
          maxWidth: '14rem',
        }}>
          <SquadList
            squad={squad}
            lineup={lineup}
            onSwapWithLineup={handleSwapBoardWithSquad}
            onSwapFromBoard={handleSwapBoardWithSquad}
          />
        </div>
      </div>
      <style jsx>{`
        @media (max-width: 767px) {
          .tactics-layout {
            flex-direction: column;
          }
          .tactics-board-column {
            order: 1;
            width: 100%;
          }
          .tactics-squad-panel {
            order: 2;
            width: 100%;
            max-width: none !important;
            flex: none !important;
          }
          .tactics-lineup-analysis {
            order: 3;
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}

function buildLineup(players: Player[], positions: string[]): (Player | null)[] {
  const used = new Set<string>();
  const lineup: (Player | null)[] = [];

  for (const pos of positions) {
    const candidate = players.find(p => {
      if (used.has(p.id)) return false;
      return p.position === pos || positionMatches(p.position, pos);
    });
    if (candidate) {
      used.add(candidate.id);
      lineup.push(candidate);
    } else {
      lineup.push(null);
    }
  }

  return lineup;
}

function positionMatches(playerPos: string, slotPos: string): boolean {
  // 门将只能踢门将位置，其他位置门将不能踢
  if (slotPos === 'GK') return playerPos === 'GK';
  if (playerPos === 'GK') return false;
  // 非门将球员可以在任何非门将位置上出现
  return true;
}
