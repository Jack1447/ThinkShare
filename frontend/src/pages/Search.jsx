import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import api from '../services/api';
import PostCard from '../components/PostCard';
import Loading from '../components/Loading';
import EmptyState from '../components/EmptyState';

const categories = [
  { key: 'all', label: '全部' },
  { key: 'daily', label: '日常生活' },
  { key: 'news', label: '时事新闻' },
  { key: 'academic', label: '学术科研' },
  { key: 'trade', label: '二手交易' },
];

const timeFilters = [
  { key: 'all', label: '不限' },
  { key: 'day', label: '一天内' },
  { key: 'half_month', label: '半个月内' },
  { key: 'month', label: '一个月内' },
  { key: 'half_year', label: '半年内' },
];

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const q = searchParams.get('q') || '';
  const searchType = searchParams.get('type') || 'post';
  const activeCategory = searchParams.get('category') || 'all';
  const activeTime = searchParams.get('time') || 'all';
  const [posts, setPosts] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);

  const setParam = (key, value) => {
    const params = new URLSearchParams(searchParams);
    params.set(key, value);
    setSearchParams(params);
  };

  useEffect(() => {
    if (!q) return;
    setLoading(true);
    api.get('/search', { params: { q, type: searchType, category: activeCategory, time: activeTime } })
      .then((res) => {
        setPosts(res.data.posts || []);
        setUsers(res.data.users || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [q, searchType, activeCategory, activeTime]);

  return (
    <div className="flex gap-5">
      <aside className="w-[180px] flex-shrink-0 sticky top-20 self-start">
        <div className="bg-white rounded-lg py-2">
          <Link to="/forum" className="block px-5 py-2.5 text-sm text-gray-500 hover:bg-gray-50">← 返回论坛</Link>
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        <div className="bg-white rounded-lg p-4 px-6 mb-4">
          <h2 className="text-base font-semibold mb-3">🔍 搜索结果：{q}</h2>

          {searchType === 'post' && (
            <>
              <div className="flex border-b-2 border-gray-100 mb-2">
                {categories.map((c) => (
                  <button key={c.key} onClick={() => setParam('category', c.key)}
                    className={`px-3.5 py-1.5 text-[13px] border-b-2 -mb-0.5 ${activeCategory === c.key ? 'text-gray-900 font-semibold border-gray-900' : 'text-gray-500 border-transparent'}`}>
                    {c.label}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-0">
                <span className="text-[13px] text-gray-400 mr-2 py-1">时间：</span>
                {timeFilters.map((t) => (
                  <button key={t.key} onClick={() => setParam('time', t.key)}
                    className={`px-3 py-1 text-[13px] ${activeTime === t.key ? 'text-gray-900 font-semibold' : 'text-gray-500'}`}>
                    {t.label}
                  </button>
                ))}
              </div>
            </>
          )}

          <div className="flex gap-2 mt-3">
            <button onClick={() => setParam('type', 'post')}
              className={`px-4 py-1 border rounded text-[13px] transition ${searchType === 'post' ? 'bg-gray-900 text-white border-gray-900' : 'border-gray-300 text-gray-500'}`}>
              📄 帖子
            </button>
            <button onClick={() => setParam('type', 'user')}
              className={`px-4 py-1 border rounded text-[13px] transition ${searchType === 'user' ? 'bg-gray-900 text-white border-gray-900' : 'border-gray-300 text-gray-500'}`}>
              👤 用户
            </button>
          </div>
        </div>

        {loading ? <Loading /> : (
          <>
            {searchType === 'post' && (
              posts.length > 0 ? posts.map((p) => <PostCard key={p.id} post={p} />)
              : <div className="bg-white rounded-lg"><EmptyState message="未找到相关帖子" /></div>
            )}
            {searchType === 'user' && (
              users.length > 0 ? (
                <div className="bg-white rounded-lg p-5">
                  {users.map((u) => (
                    <div key={u.id} className="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
                      <div className="flex items-center gap-2.5">
                        <img src={u.avatar_url || '/static/img/default_avatar.svg'} alt="" className="w-9 h-9 rounded-full object-cover" />
                        <span className="text-sm font-medium">{u.nickname}</span>
                        <span className="text-xs text-gray-400">@{u.username}</span>
                      </div>
                      <Link to={`/user/${u.id}`} className="px-3 py-1 border border-gray-300 rounded text-xs text-gray-500 hover:border-gray-400">查看主页</Link>
                    </div>
                  ))}
                </div>
              ) : <div className="bg-white rounded-lg"><EmptyState message="未找到相关用户" /></div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
