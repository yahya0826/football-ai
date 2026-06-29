'use client';

import { useState, useCallback } from 'react';
import { Player, FORMATIONS, Formation } from './types';

interface TacticalBoardProps {
  lineup: (Player | null)[];
  formation: Formation;
  selectedPlayerId: string | null;
  onPlayerClick: (player: Player) => void;
  onSwapPlayer: (fromIndex: number, toIndex: number) => void;
  onFormationChange: (formation: Formation) => void;
  onSwapWithSquad?: (lineupIndex: number, squadPlayerId: string) => void;
}

const FIELD_COLORS = {
  grass: '#2d5a27',
  lines: 'rgba(255, 255, 255, 0.8)',
  penalty: 'rgba(255, 255, 255, 0.6)',
};

const POSITION_NAMES: Record<string, string> = {
  GK: '门将',
  CB: '中后卫',
  LB: '左后卫',
  RB: '右后卫',
  LWB: '左边翼卫',
  RWB: '右边翼卫',
  CDM: '后腰',
  CM: '中前卫',
  CAM: '前腰',
  LM: '左边锋',
  RM: '右边锋',
  LW: '左边锋',
  RW: '右边锋',
  ST: '中锋',
};

export default function TacticalBoard({
  lineup,
  formation,
  selectedPlayerId,
  onPlayerClick,
  onSwapPlayer,
  onFormationChange,
  onSwapWithSquad,
}: TacticalBoardProps) {
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  const handleDragStart = useCallback((e: React.DragEvent, index: number) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', 'board:' + String(index));
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent, index: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverIndex(index);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOverIndex(null);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, targetIndex: number) => {
    e.preventDefault();
    const data = e.dataTransfer.getData('text/plain');
    if (data.startsWith('squad:')) {
      const squadPlayerId = data.slice(6);
      if (squadPlayerId && onSwapWithSquad) {
        onSwapWithSquad(targetIndex, squadPlayerId);
      }
    } else if (data.startsWith('board:') && draggedIndex !== null && draggedIndex !== targetIndex) {
      onSwapPlayer(draggedIndex, targetIndex);
    }
    setDraggedIndex(null);
    setDragOverIndex(null);
  }, [draggedIndex, onSwapPlayer, onSwapWithSquad]);

  const handleDragEnd = useCallback(() => {
    setDraggedIndex(null);
    setDragOverIndex(null);
  }, []);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-md)',
      height: '100%',
    }}>
      {/* Formation selector */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        flexWrap: 'wrap',
      }}>
        {Object.values(FORMATIONS).map((f) => (
          <button
            key={f.id}
            onClick={() => onFormationChange(f)}
            style={{
              padding: '0.6em 1.2em',
              fontSize: 'var(--text-sm)',
              borderRadius: '0.5rem',
              border: formation.id === f.id ? '2px solid #10b981' : '1px solid #333',
              background: formation.id === f.id ? 'rgba(16, 185, 129, 0.2)' : 'transparent',
              color: formation.id === f.id ? '#10b981' : '#fff',
              cursor: 'pointer',
              fontWeight: formation.id === f.id ? 'bold' : 'normal',
              transition: 'all 0.2s',
            }}
          >
            {f.name}
          </button>
        ))}
      </div>

      {/* Pitch container */}
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        minHeight: 'clamp(28rem, 50vh, 47rem)',
        width: '100%',
      }}>
        {/* Pitch */}
        <div className="tactical-board-pitch" style={{
          width: '100%',
          maxWidth: 'min(80%, 42rem)',
          aspectRatio: '1 / 1.4',
          background: FIELD_COLORS.grass,
          borderRadius: '0.75rem',
          position: 'relative',
          overflow: 'hidden',
        }}>
          {/* Pitch markings */}
          <svg
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              opacity: 0.8,
            }}
            viewBox="0 0 100 65"
            preserveAspectRatio="none"
          >
            <rect x="1" y="1" width="98" height="63" fill="none" stroke={FIELD_COLORS.lines} strokeWidth="0.6" />
            <line x1="50" y1="1" x2="50" y2="64" stroke={FIELD_COLORS.lines} strokeWidth="0.45" />
            <circle cx="50" cy="32.5" r="6" fill="none" stroke={FIELD_COLORS.lines} strokeWidth="0.45" />
            <circle cx="50" cy="32.5" r="0.5" fill={FIELD_COLORS.lines} />
            <rect x="30" y="1" width="40" height="16" fill="none" stroke={FIELD_COLORS.lines} strokeWidth="0.45" />
            <rect x="38" y="1" width="24" height="6" fill="none" stroke={FIELD_COLORS.lines} strokeWidth="0.45" />
            <circle cx="50" cy="10" r="0.3" fill={FIELD_COLORS.lines} />
            <rect x="30" y="48" width="40" height="16" fill="none" stroke={FIELD_COLORS.lines} strokeWidth="0.45" />
            <rect x="38" y="58" width="24" height="6" fill="none" stroke={FIELD_COLORS.lines} strokeWidth="0.45" />
            <circle cx="50" cy="55" r="0.3" fill={FIELD_COLORS.lines} />
          </svg>

          {/* Player positions */}
          <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}>
            {formation.positions.map((pos, index) => {
              const player = lineup[index];
              const isSelected = player?.id === selectedPlayerId;
              const isDragOver = dragOverIndex === index;
              const isDragging = draggedIndex === index;

              return (
                <div
                  key={index}
                  draggable={!!player}
                  onDragStart={(e) => player && handleDragStart(e, index)}
                  onDragOver={(e) => handleDragOver(e, index)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, index)}
                  onDragEnd={handleDragEnd}
                  onClick={() => player && onPlayerClick(player)}
                  style={{
                    position: 'absolute',
                    left: `${pos.x}%`,
                    top: `${pos.y}%`,
                    transform: 'translate(-50%, -50%)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    cursor: player ? 'grab' : 'default',
                    opacity: isDragging ? 0.5 : 1,
                    zIndex: isDragOver ? 10 : isSelected ? 5 : 1,
                  }}
                >
                  {/* Position label */}
                  <div className="tactical-board-position-label" style={{
                    fontSize: 'clamp(1.1rem, 1.4vw, 1.3rem)',
                    color: 'rgba(255,255,255,0.8)',
                    marginBottom: '0.2em',
                    fontWeight: 500,
                  }}>
                    {POSITION_NAMES[pos.position] || pos.position}
                  </div>
                  {/* Player circle */}
                  <div className="tactical-board-player-circle" style={{
                    width: player ? 'clamp(3rem, 5vw, 4.9rem)' : 'clamp(2.25rem, 3.5vw, 3.4rem)',
                    height: player ? 'clamp(3rem, 5vw, 4.9rem)' : 'clamp(2.25rem, 3.5vw, 3.4rem)',
                    borderRadius: '50%',
                    background: player
                      ? isSelected
                        ? '#10b981'
                        : 'rgba(255, 255, 255, 0.9)'
                      : 'rgba(255, 255, 255, 0.2)',
                    border: `2px solid ${isSelected ? '#10b981' : 'rgba(0,0,0,0.3)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: player ? 'clamp(1.9rem, 3vw, 2.6rem)' : 'clamp(1.35rem, 2.2vw, 1.9rem)',
                    transition: 'all 0.2s',
                    boxShadow: isSelected ? '0 0 15px rgba(16, 185, 129, 0.7)' : 'none',
                  }}>
                    {player ? (
                      player.avatar ? (
                        <img
                          src={player.avatar}
                          alt={player.name}
                          style={{
                            width: '100%',
                            height: '100%',
                            borderRadius: '50%',
                            objectFit: 'cover',
                          }}
                        />
                      ) : '⚽'
                    ) : '?'}
                  </div>
                  {/* Player name */}
                  {player && (
                    <div className="tactical-board-player-name" style={{
                      marginTop: '0.3em',
                      padding: '0.2em 0.5em',
                      background: 'rgba(0, 0, 0, 0.8)',
                      borderRadius: '0.25rem',
                      fontSize: 'clamp(1.2rem, 1.5vw, 1.35rem)',
                      color: '#fff',
                      fontWeight: 500,
                      whiteSpace: 'nowrap',
                      maxWidth: '7.5rem',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}>
                      {player.nameCn || player.name}
                    </div>
                  )}
                  {/* Jersey number */}
                  {player && (
                    <div className="tactical-board-player-number" style={{
                      fontSize: 'clamp(1.05rem, 1.3vw, 1.28rem)',
                      color: 'rgba(255,255,255,0.9)',
                      marginTop: '0.15em',
                    }}>
                      {player.number}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
