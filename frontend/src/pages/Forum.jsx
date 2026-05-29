import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
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

export default function Forum() {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeCategory = searchParams.get('category') || 'all';
  const [posts, setPosts] = useState([]);
  const [hotPosts, setHotPosts] = useState([]);
  const [stats, setStats] = useState({ total_posts: 0, total_users: 0, today_posts: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.get('/forum', { params: { category: activeCategory } })
      .then((res) => {
        setPosts(res.data.posts);
        setHotPosts(res.data.hot_posts);
        setStats(res.data.stats);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [activeCategory]);

  return (
    <div className="flex gap-5">
      <aside className="w-[180px] flex-shrink-0 sticky top-20 self-start">
        <div className="bg-white rounded-lg py-2">
          {categories.map((cat) => (
            <Link
              key={cat.key}
              to={cat.key === 'all' ? '/forum' : `/forum?category=${cat.key}`}
              className={`block px-5 py-2.5 text-sm border-l-[3px] transition
                ${activeCategory === cat.key
                  ? 'text-gray-900 font-semibold border-gray-900 bg-gray-50'
                  : 'text-gray-500 border-transparent hover:bg-gray-50 hover:text-gray-700'
                }`}
            >
              {cat.label}
            </Link>
          ))}
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        {loading ? (
          <Loading />
        ) : posts.length > 0 ? (
          posts.map((post) => <PostCard key={post.id} post={post} />)
        ) : (
          <div className="bg-white rounded-lg">
            <EmptyState message="暂无帖子，快来发布第一个帖子吧！" />
          </div>
        )}
      </main>

      <aside className="w-[280px] flex-shrink-0 sticky top-20 self-start flex flex-col gap-4">
        <div className="bg-white rounded-lg p-5">
          <Link
            to="/create-post"
            className="block w-full text-center py-2 bg-gray-900 text-white rounded-md text-sm font-medium hover:bg-gray-700 transition"
          >
            ✏️ 发布新帖
          </Link>
        </div>

        <div className="bg-white rounded-lg p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2.5 border-b border-gray-100">
            🔥 热门帖子
          </h3>
          {hotPosts.length > 0 ? (
            <ul>
              {hotPosts.map((hp, i) => (
                <li key={hp.id} className="py-2 border-b border-gray-50 last:border-b-0">
                  <Link to={`/post/${hp.id}`} className="text-[13px] text-gray-600 hover:text-gray-900 block leading-relaxed">
                    <span className={`inline-block w-5 text-xs font-bold ${i < 3 ? 'text-orange-500' : 'text-gray-400'}`}>
                      {i + 1}.
                    </span>
                    {hp.title}
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-[13px] text-gray-300">暂无热帖</p>
          )}
        </div>

        <div className="bg-white rounded-lg p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2.5 border-b border-gray-100">
            📊 论坛统计
          </h3>
          <div className="flex justify-between py-1.5 text-[13px] text-gray-500">
            <span>帖子总数</span>
            <span className="font-semibold text-gray-700">{stats.total_posts}</span>
          </div>
          <div className="flex justify-between py-1.5 text-[13px] text-gray-500">
            <span>用户总数</span>
            <span className="font-semibold text-gray-700">{stats.total_users}</span>
          </div>
          <div className="flex justify-between py-1.5 text-[13px] text-gray-500">
            <span>今日新增</span>
            <span className="font-semibold text-gray-700">{stats.today_posts}</span>
          </div>
        </div>
      </aside>
    </div>
  );
}
