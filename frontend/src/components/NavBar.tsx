'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import FeedbackModal from './FeedbackModal';

const NAV_ITEMS = [
  { href: '/', label: '首页' },
  { href: '/tactics', label: '战术分析' },
  { href: '/intelligence', label: '哨前情报' },
  { href: '/matches', label: '比赛' },
  { href: '/knowledge', label: '知识库' },
];

export default function NavBar() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (menuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [menuOpen]);

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <nav className="navbar">
      <div className="container-responsive">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2">
              <svg className="w-8 h-8 text-primary" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
                <path d="M12 2 L12 22 M2 12 L22 12 M4.93 4.93 L19.07 19.07 M4.93 19.07 L19.07 4.93" stroke="currentColor" strokeWidth="1.5" />
                <circle cx="12" cy="12" r="3" />
              </svg>
              <span className="text-xl font-bold" style={{ color: 'var(--primary)' }}>世界杯AI助手</span>
            </Link>

            <div className="hidden md:flex items-center gap-1">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`nav-link${isActive(item.href) ? ' active' : ''}`}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <span className="badge badge-primary">2026 世界杯</span>

            <button
              onClick={() => setFeedbackOpen(true)}
              title="产品反馈"
              style={{
                background: 'rgba(129, 140, 248, 0.15)',
                color: 'var(--secondary)',
                border: '1px solid rgba(129, 140, 248, 0.3)',
                padding: '0.4rem 0.9rem',
                borderRadius: '0.5rem',
                fontSize: 'var(--text-sm)',
                fontWeight: 600,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.2s',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = 'rgba(129, 140, 248, 0.25)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = 'rgba(129, 140, 248, 0.15)';
              }}
            >
              💬 反馈
            </button>

            <button
              className="md:hidden flex flex-col justify-center items-center w-10 h-10 rounded-lg"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--card-border)' }}
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label={menuOpen ? '关闭菜单' : '打开菜单'}
            >
              <span style={{
                display: 'block',
                width: '1.25rem',
                height: '2px',
                background: 'var(--foreground)',
                marginBottom: '4px',
                transition: 'all 0.2s',
                transform: menuOpen ? 'rotate(45deg) translate(3px, 5px)' : 'none',
              }} />
              <span style={{
                display: 'block',
                width: '1.25rem',
                height: '2px',
                background: 'var(--foreground)',
                transition: 'all 0.2s',
                opacity: menuOpen ? 0 : 1,
              }} />
              <span style={{
                display: 'block',
                width: '1.25rem',
                height: '2px',
                background: 'var(--foreground)',
                marginTop: '4px',
                transition: 'all 0.2s',
                transform: menuOpen ? 'rotate(-45deg) translate(3px, -5px)' : 'none',
              }} />
            </button>
          </div>
        </div>
      </div>

      {menuOpen && (
        <>
          <div
            className="mobile-menu-backdrop"
            onClick={() => setMenuOpen(false)}
          />
          <div className="mobile-menu-sheet">
            <div style={{
              width: '2.5rem',
              height: '0.25rem',
              borderRadius: '0.25rem',
              background: 'var(--card-border)',
              margin: '0 auto var(--space-md)',
            }} />
            <div className="flex flex-col gap-1">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="mobile-nav-link"
                  style={isActive(item.href) ? {
                    background: 'rgba(16, 185, 129, 0.1)',
                    color: 'var(--primary)',
                  } : {}}
                  onClick={() => setMenuOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        </>
      )}

      <FeedbackModal open={feedbackOpen} onClose={() => setFeedbackOpen(false)} />
    </nav>
  );
}
