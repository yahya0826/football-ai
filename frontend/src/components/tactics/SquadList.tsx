'use client';

import { useState, useCallback } from 'react';
import { Player } from './types';

interface SquadListProps {
  squad: Player[];
  lineup: (Player | null)[];
  onSwapWithLineup: (lineupIndex: number, squadPlayerId: string) => void;
  onSwapFromBoard?: (lineupIndex: number, squadPlayerId: string) => void;
}

export default function SquadList({ squad, lineup, onSwapWithLineup, onSwapFromBoard }: SquadListProps) {
  const [draggedSquadId, setDraggedSquadId] = useState<string | null>(null);

  const lineupPlayerIds = lineup.map(p => p?.id);

  const handleDragStart = useCallback((e: React.DragEvent, playerId: string) => {
    setDraggedSquadId(playerId);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', 'squad:' + playerId);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, lineupIndex: number) => {
    e.preventDefault();
    const data = e.dataTransfer.getData('text/plain');
    if (data.startsWith('squad:')) {
      const squadPlayerId = data.slice(6);
      if (squadPlayerId) {
        onSwapWithLineup(lineupIndex, squadPlayerId);
      }
    }
    setDraggedSquadId(null);
  }, [onSwapWithLineup]);

  const handleDragEnd = useCallback(() => {
    setDraggedSquadId(null);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);

  const positionGroups = ['GK', 'DF', 'MF', 'FW'];

  const formatPosition = (pos: string) => {
    const posMap: Record<string, string> = {
      GK: '门将',
      DF: '后卫',
      MF: '中场',
      FW: '前锋',
    };
    return posMap[pos] || pos;
  };

  const getPositionGroup = (pos: string) => {
    const normalized = (pos || '').toUpperCase();
    if (normalized === 'GK') return 'GK';
    if (['DF', 'CB', 'LB', 'RB', 'LWB', 'RWB'].includes(normalized)) return 'DF';
    if (['MF', 'CDM', 'CM', 'CAM', 'LM', 'RM'].includes(normalized)) return 'MF';
    if (['FW', 'ST', 'CF', 'LW', 'RW'].includes(normalized)) return 'FW';
    return 'MF';
  };

  const groupedPlayers = squad.reduce((acc, player) => {
    const group = getPositionGroup(player.position);
    if (!acc[group]) acc[group] = [];
    acc[group].push(player);
    return acc;
  }, {} as Record<string, Player[]>);

  return (
    <div style={{
      border: '1px solid #333',
      borderRadius: '0.75rem',
      padding: 'var(--space-md)',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <h2 style={{
        fontSize: 'var(--text-base)',
        marginBottom: '0.25rem',
        fontWeight: 'bold',
      }}>
        球队大名单
      </h2>
      <p style={{
        fontSize: 'var(--text-xs)',
        color: 'var(--text-muted)',
        marginBottom: '0.75rem',
      }}>
        拖拽球员交换场上位置
      </p>

      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
        flex: 1,
        overflowY: 'auto',
      }}>
        {positionGroups.map(group => {
          const players = groupedPlayers[group];
          if (!players || players.length === 0) return null;

          return (
            <div key={group} style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.25rem',
            }}>
              <div style={{
                fontSize: 'var(--text-xs)',
                color: 'var(--text-muted)',
                paddingLeft: '0.25rem',
              }}>
                {formatPosition(group)}
              </div>
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '0.35rem',
              }}>
                {players.map(player => {
                  const isInLineup = lineupPlayerIds.includes(player.id);
                  return (
                    <div
                      key={player.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, player.id)}
                      onDragEnd={handleDragEnd}
                      onDragOver={handleDragOver}
                      onDrop={(e) => {
                        const data = e.dataTransfer.getData('text/plain');
                        if (data.startsWith('board:')) {
                          const boardIndex = parseInt(data.slice(6), 10);
                          if (!isNaN(boardIndex) && onSwapFromBoard) {
                            onSwapFromBoard(boardIndex, player.id);
                          }
                        } else {
                          const lineupIdx = lineup.findIndex(p => p?.id === player.id);
                          if (lineupIdx >= 0) handleDrop(e, lineupIdx);
                        }
                      }}
                      style={{
                        padding: '0.3em 0.6em',
                        background: isInLineup
                          ? 'rgba(16, 185, 129, 0.15)'
                          : 'rgba(255,255,255,0.05)',
                        border: `1px solid ${isInLineup ? 'rgba(16, 185, 129, 0.5)' : '#444'}`,
                        borderRadius: '0.375rem',
                        cursor: 'grab',
                        opacity: draggedSquadId === player.id ? 0.5 : 1,
                        transition: 'all 0.2s',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                      }}
                    >
                      {player.avatar ? (
                        <img
                          src={player.avatar}
                          alt={player.name}
                          style={{
                            width: '1.2rem',
                            height: '1.2rem',
                            borderRadius: '50%',
                            objectFit: 'cover',
                            flexShrink: 0,
                          }}
                        />
                      ) : (
                        <span style={{
                          width: '1.2rem',
                          height: '1.2rem',
                          borderRadius: '50%',
                          background: 'rgba(255,255,255,0.1)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '0.6rem',
                          flexShrink: 0,
                        }}>
                          ⚽
                        </span>
                      )}
                      <span style={{
                        fontWeight: 'bold',
                        color: '#10b981',
                        fontSize: 'var(--text-xs)',
                      }}>
                        #{player.number}
                      </span>
                      <span style={{ fontSize: 'var(--text-xs)' }}>
                        {player.nameCn || player.name}
                      </span>
                      {isInLineup && (
                        <span style={{
                          fontSize: '0.6rem',
                          color: '#10b981',
                          background: 'rgba(16,185,129,0.2)',
                          padding: '0.1rem 0.3rem',
                          borderRadius: '0.25rem',
                        }}>
                          首发
                        </span>
                      )}
                      {player.stats?.matchConfidence && (
                        <span style={{
                          width: '0.4rem',
                          height: '0.4rem',
                          borderRadius: '50%',
                          background: player.stats.matchConfidence === 'high' ? '#10b981' : '#eab308',
                          flexShrink: 0,
                        }}
                        title={player.stats.matchConfidence === 'high' ? '真实数据' : '部分数据'}
                      />
                    )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
