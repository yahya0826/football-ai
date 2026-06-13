'use client';

import { useState, useEffect } from 'react';
import api, { KnowledgeItem, TeamProfile } from '@/lib/api';

export default function KnowledgePage() {
  const [categories, setCategories] = useState<string[]>([]);
  const [items, setItems] = useState<Record<string, KnowledgeItem[]>>({});
  const [activeCategory, setActiveCategory] = useState<string>('全部');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<KnowledgeItem[]>([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loadingAnswer, setLoadingAnswer] = useState(false);
  const [loading, setLoading] = useState(true);
  const [randomItems, setRandomItems] = useState<KnowledgeItem[]>([]);
  const [teams, setTeams] = useState<TeamProfile[]>([]);
  const [loadingTeams, setLoadingTeams] = useState(false);
  const [mode, setMode] = useState<'knowledge' | 'teams'>('knowledge');

  useEffect(() => {
    async function loadKnowledge() {
      try {
        const data = await api.getKnowledgeCategories();
        setCategories(['全部', ...data.categories]);
        setItems(data.items);
      } catch (err) {
        console.error('Failed to load knowledge:', err);
      } finally {
        setLoading(false);
      }
    }

    async function loadRandom() {
      try {
        const data = await api.getRandomKnowledge(3);
        setRandomItems(data.items);
      } catch (err) {
        console.error('Failed to load random knowledge:', err);
      }
    }

    async function loadTeams() {
      setLoadingTeams(true);
      try {
        const data = await api.getTeamProfiles();
        setTeams(data);
      } catch (err) {
        console.error('Failed to load team profiles:', err);
      } finally {
        setLoadingTeams(false);
      }
    }

    loadKnowledge();
    loadRandom();
    loadTeams();
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    try {
      const data = await api.searchKnowledge(searchQuery);
      setSearchResults(data.results);
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) return;
    setLoadingAnswer(true);
    try {
      const data = await api.askKnowledge(question);
      setAnswer(data.answer);
    } catch (err) {
      console.error('Ask failed:', err);
      setAnswer('抱歉，我无法回答这个问题。');
    } finally {
      setLoadingAnswer(false);
    }
  };

  const displayedItems = activeCategory === '全部'
    ? Object.values(items).flat()
    : items[activeCategory] || [];

  const allItems = searchQuery ? searchResults : displayedItems;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen py-4 md:py-8">
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="page-title text-3xl mb-8 text-center">世界杯知识百库</h1>

        {/* Ask Section */}
        <div className="card mb-8">
          <h2 className="text-xl font-bold mb-4">向AI助手提问</h2>
          <div className="flex gap-4 mb-4">
            <input
              type="text"
              className="input flex-1"
              placeholder="例如：世界杯历史最佳射手是谁？"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
            />
            <button
              className="btn btn-primary"
              onClick={handleAsk}
              disabled={loadingAnswer}
            >
              {loadingAnswer ? '回答中...' : '提问'}
            </button>
          </div>
          {answer && (
            <div className="p-4 rounded-lg" style={{ background: 'rgba(16, 185, 129, 0.1)' }}>
              <div className="stat-label mb-2">回答</div>
              <p style={{ whiteSpace: 'pre-wrap' }}>{answer}</p>
            </div>
          )}
        </div>

        {/* Search */}
        <div className="card mb-8">
          <h2 className="text-xl font-bold mb-4">搜索知识库</h2>
          <div className="flex gap-4">
            <input
              type="text"
              className="input flex-1"
              placeholder="搜索关键词..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button className="btn btn-secondary" onClick={handleSearch}>
              搜索
            </button>
          </div>
        </div>

        {/* Mode Switch */}
        <div className="flex gap-2 mb-6">
          <button
            className={`tab ${mode === 'knowledge' ? 'active' : ''}`}
            onClick={() => setMode('knowledge')}
          >
            知识百库
          </button>
          <button
            className={`tab ${mode === 'teams' ? 'active' : ''}`}
            onClick={() => setMode('teams')}
          >
            球队档案
          </button>
        </div>

        {mode === 'knowledge' && (
          <>
            {/* Random Knowledge */}
            {randomItems.length > 0 && !searchQuery && (
              <div className="mb-8">
                <h2 className="text-xl font-bold mb-4">随机知识</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {randomItems.map((item, idx) => (
                    <div key={idx} className="knowledge-card">
                      <span className="badge badge-secondary mb-2">{item.category}</span>
                      <h3 className="font-bold mb-2">{item.question}</h3>
                      <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                        {item.answer.substring(0, 100)}...
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Categories */}
            {!searchQuery && (
              <div className="mb-6">
                <h2 className="text-xl font-bold mb-4">分类浏览</h2>
                <div className="flex flex-wrap gap-2">
                  {categories.map((cat) => (
                    <button
                      key={cat}
                      className={`tab ${activeCategory === cat ? 'active' : ''}`}
                      onClick={() => setActiveCategory(cat)}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Results */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {allItems.map((item, idx) => (
                <div key={idx} className="knowledge-card">
                  <span className="badge badge-secondary mb-2">{item.category}</span>
                  <h3 className="font-bold mb-2">{item.question}</h3>
                  <p style={{ color: 'var(--text-muted)' }}>{item.answer}</p>
                </div>
              ))}
            </div>

            {allItems.length === 0 && (
              <div className="text-center py-16">
                <p className="text-lg" style={{ color: 'var(--text-muted)' }}>
                  {searchQuery ? '没有找到相关知识' : '该分类暂无知识条目'}
                </p>
              </div>
            )}
          </>
        )}

        {mode === 'teams' && (
          <>
            {loadingTeams ? (
              <div className="flex items-center justify-center py-16">
                <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
              </div>
            ) : teams.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {teams.map((team) => (
                  <div key={team.team} className="card">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg"
                        style={{ background: 'var(--primary)', color: '#fff' }}>
                        {team.team.substring(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <h3 className="font-bold">{team.team}</h3>
                        <span className="badge badge-secondary text-xs">{team.confederation}</span>
                      </div>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span style={{ color: 'var(--text-muted)' }}>世界杯冠军</span>
                        <span className="font-bold">{team.world_cup_titles || 0}次</span>
                      </div>
                      <div className="flex justify-between">
                        <span style={{ color: 'var(--text-muted)' }}>战术风格</span>
                        <span>{team.playing_style}</span>
                      </div>
                      <div className="flex justify-between">
                        <span style={{ color: 'var(--text-muted)' }}>阵型</span>
                        <span>{team.key_formation}</span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>优势</span>
                        <p className="text-xs mt-0.5">{team.strength}</p>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>短板</span>
                        <p className="text-xs mt-0.5">{team.weakness}</p>
                      </div>
                      {team.rivalries && team.rivalries.length > 0 && (
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>宿敌</span>
                          <p className="text-xs mt-0.5">{team.rivalries.join('、')}</p>
                        </div>
                      )}
                      <details className="mt-2">
                        <summary className="cursor-pointer text-xs" style={{ color: 'var(--primary)' }}>历史简介</summary>
                        <p className="mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>{team.history}</p>
                      </details>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-16">
                <p className="text-lg" style={{ color: 'var(--text-muted)' }}>暂无球队档案数据</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}