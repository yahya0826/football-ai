'use client';

import { useState } from 'react';
import api from '@/lib/api';

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function FeedbackModal({ open, onClose }: Props) {
  const [text, setText] = useState('');
  const [rating, setRating] = useState(0);
  const [hoverStar, setHoverStar] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');

  if (!open) return null;

  async function handleSubmit() {
    if (!text.trim() || rating === 0) return;
    setSubmitting(true);
    setError('');
    try {
      await api.submitFeedback({
        text: text.trim(),
        rating,
        page: window.location.pathname,
      });
      setDone(true);
    } catch {
      setError('提交失败，请稍后重试');
    } finally {
      setSubmitting(false);
    }
  }

  function handleClose() {
    setText('');
    setRating(0);
    setHoverStar(0);
    setDone(false);
    setError('');
    onClose();
  }

  const stars = [1, 2, 3, 4, 5];

  return (
    <>
      <div className="mobile-menu-backdrop" onClick={handleClose} />

      <div style={{
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        zIndex: 300,
        background: 'var(--card-bg)',
        border: '1px solid var(--card-border)',
        borderRadius: '1rem',
        padding: 'var(--space-lg)',
        width: 'min(90vw, 28rem)',
        animation: 'fadeIn 0.2s ease',
      }}>
        {done ? (
          <div className="text-center py-4">
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✅</div>
            <h3 className="text-xl font-bold mb-2">感谢反馈！</h3>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>你的意见将帮助我们改进产品</p>
            <button className="btn btn-primary mt-4 w-full" onClick={handleClose}>关闭</button>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">产品反馈</h2>
              <button
                onClick={handleClose}
                style={{ color: 'var(--text-muted)', fontSize: '1.5rem', lineHeight: 1 }}
              >
                ✕
              </button>
            </div>

            <textarea
              className="input mb-4"
              rows={4}
              placeholder="请输入你的反馈意见..."
              value={text}
              onChange={e => setText(e.target.value)}
              maxLength={500}
            />

            <div className="mb-2">
              <span className="stat-label">满意度</span>
            </div>
            <div className="flex items-center gap-1 mb-4">
              {stars.map(n => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setRating(n)}
                  onMouseEnter={() => setHoverStar(n)}
                  onMouseLeave={() => setHoverStar(0)}
                  style={{
                    fontSize: '2rem',
                    color: n <= (hoverStar || rating) ? 'var(--accent)' : 'var(--card-border)',
                    transition: 'color 0.15s',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: 0,
                    lineHeight: 1,
                  }}
                >
                  ★
                </button>
              ))}
              {rating > 0 && (
                <span className="text-sm ml-2" style={{ color: 'var(--text-muted)' }}>
                  {rating}/5
                </span>
              )}
            </div>

            {error && (
              <p className="text-sm mb-3" style={{ color: 'var(--danger)' }}>{error}</p>
            )}

            <button
              className="btn btn-primary w-full"
              onClick={handleSubmit}
              disabled={!text.trim() || rating === 0 || submitting}
              style={{ opacity: (!text.trim() || rating === 0) ? 0.5 : 1 }}
            >
              {submitting ? '提交中...' : '提交反馈'}
            </button>
          </>
        )}
      </div>
    </>
  );
}
