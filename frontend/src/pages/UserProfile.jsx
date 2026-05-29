import { useState, useEffect } from 'react';
import { useParams, Link, useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/Toast';
import api from '../services/api';
import PostCard from '../components/PostCard';
import Loading from '../components/Loading';
import EmptyState from '../components/EmptyState';

const tabs = [
  { key: 'posts', label: 'TA的帖子' },
  { key: 'favorites', label: 'TA的收藏' },
  { key: 'following', label: 'TA的关注' },
];

export default function UserProfile() {
  const { userId } = useParams();
  const { user: me } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'posts';
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const isMe = me?.id === Number(userId);

  useEffect(() => {
    if (isMe) { navigate('/profile'); return; }
    setLoading(true);
    api.get(`/users/${userId}`)
      .then((res) => setData(res.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [userId, isMe]);

  const handleFollow = async () => {
    try {
      await api.post(`/users/${userId}/follow`);
      setData((prev) => prev ? { ...prev, is_following: true } : prev);
      addToast('已关注', 'success');
    } catch (err) { addToast('操作失败', 'error'); }
  };

  const handleUnfollow = async () => {
    try {
      await api.delete(`/users/${userId}/follow`);
      setData((prev) => prev ? { ...prev, is_following: false } : prev);
      addToast('已取消关注', 'info');
    } catch (err) { addToast('操作失败', 'error'); }
  };

  const handleAddFriend = async () => {
    try {
      await api.post(`/friends/${userId}`);
      setData((prev) => prev ? { ...prev, friend_status: 'pending' } : prev);
      addToast('好友请求已发送', 'success');
    } catch (err) { addToast(err.response?.data?.message || '操作失败', 'error'); }
  };

  if (loading) return <Loading />;
  if (!data) return <div className="text-center py-20 text-gray-400">用户不存在</div>;
  const { user: target, privacy } = data;

  return (
    <div className="max-w-[800px] mx-auto">
      <div className="bg-white rounded-lg p-8 flex items-center gap-6 mb-5">
        <img src={target.avatar_url || '/static/img/default_avatar.svg'} alt="" className="w-20 h-20 rounded-full object-cover" />
        <div className="flex-1">
          <h2 className="text-[22px] font-semibold">{target.nickname}</h2>
          <div className="flex gap-6 text-[13px] text-gray-500 mt-2">
            <span>获赞 <strong className="text-gray-700">{target.like_count ?? 0}</strong></span>
            <span>关注 <strong className="text-gray-700">{data.following_count ?? 0}</strong></span>
            <span>粉丝 <strong className="text-gray-700">{data.follower_count ?? 0}</strong></span>
          </div>
          <div className="flex gap-2 mt-3">
            {data.is_following ? (
              <button onClick={handleUnfollow} className="px-3 py-1 border border-gray-300 rounded text-xs text-gray-500">✅ 已关注</button>
            ) : (
              <button onClick={handleFollow} className="px-3 py-1 border border-gray-300 rounded text-xs text-gray-500">➕ 关注</button>
            )}
            {privacy?.allow_short_chat && (
              <Link to={`/chat/${userId}`} className="px-3 py-1 bg-gray-900 text-white rounded text-xs">💬 发消息</Link>
            )}
            {privacy?.allow_friend_request && data.friend_status !== 'friend' && data.friend_status !== 'pending' && (
              <button onClick={handleAddFriend} className="px-3 py-1 border border-gray-300 rounded text-xs text-gray-500">➕ 添加好友</button>
            )}
            {data.friend_status === 'pending' && (
              <span className="px-3 py-1 border border-gray-300 rounded text-xs text-gray-400">⏳ 已发送请求</span>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg">
        <div className="flex border-b-2 border-gray-100">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setSearchParams({ tab: tab.key })}
              className={`px-4 py-2.5 text-sm border-b-2 -mb-0.5 transition ${activeTab === tab.key ? 'text-gray-900 font-semibold border-gray-900' : 'text-gray-500 border-transparent'}`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="p-6">
          {activeTab === 'posts' && (
            privacy?.show_posts ? (
              data.posts?.length > 0 ? data.posts.map((p) => <PostCard key={p.id} post={p} />)
              : <EmptyState message="暂无帖子" />
            ) : <EmptyState message="该用户隐藏了帖子列表" />
          )}
          {activeTab === 'favorites' && (
            privacy?.show_favorites ? (
              data.favorited_posts?.length > 0 ? data.favorited_posts.map((p) => <PostCard key={p.id} post={p} />)
              : <EmptyState message="暂无收藏" />
            ) : <EmptyState message="该用户隐藏了收藏列表" />
          )}
          {activeTab === 'following' && (
            privacy?.show_following ? (
              data.following?.length > 0 ? (
                data.following.map((f) => (
                  <div key={f.id} className="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
                    <div className="flex items-center gap-2.5">
                      <img src={f.avatar_url} alt="" className="w-9 h-9 rounded-full" />
                      <span className="text-sm font-medium">{f.nickname}</span>
                    </div>
                    <Link to={`/user/${f.id}`} className="px-3 py-1 border border-gray-300 rounded text-xs text-gray-500">查看主页</Link>
                  </div>
                ))
              ) : <EmptyState message="暂无关注" />
            ) : <EmptyState message="该用户隐藏了关注列表" />
          )}
        </div>
      </div>
    </div>
  );
}
