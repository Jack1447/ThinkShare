import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/Toast';
import api from '../services/api';
import PostCard from '../components/PostCard';
import Loading from '../components/Loading';
import EmptyState from '../components/EmptyState';

const tabs = [
  { key: 'posts', label: '我的帖子' },
  { key: 'favorites', label: '我的收藏' },
  { key: 'following', label: '我的关注' },
  { key: 'followers', label: '关注我的' },
  { key: 'friends', label: '长时好友' },
  { key: 'short', label: '短时联系人' },
  { key: 'privacy', label: '隐私设置' },
];

export default function Profile() {
  const { user, updateUser } = useAuth();
  const { addToast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'posts';
  const catFilter = searchParams.get('cat') || 'all';
  const [nickname, setNickname] = useState(user?.nickname || '');
  const [editing, setEditing] = useState(false);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = () => {
    api.get('/user/profile')
      .then((res) => setProfile(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchProfile(); }, []);

  const handleAvatarChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('avatar', file);
    try {
      const res = await api.post('/user/avatar', formData);
      updateUser({ ...user, avatar_url: res.data.avatar_url });
      addToast('头像上传成功', 'success');
    } catch (err) {
      addToast(err.response?.data?.message || '上传失败', 'error');
    }
  };

  const handleNicknameSave = async () => {
    if (!nickname.trim()) return;
    try {
      await api.put('/user/profile', { nickname: nickname.trim() });
      updateUser({ ...user, nickname: nickname.trim() });
      addToast('昵称更新成功', 'success');
      setEditing(false);
    } catch (err) {
      addToast(err.response?.data?.message || '更新失败', 'error');
    }
  };

  const handlePrivacySave = async () => {
    const ps = profile?.privacy;
    if (!ps) return;
    try {
      await api.put('/user/profile', ps);
      addToast('隐私设置已保存', 'success');
    } catch (err) {
      addToast('保存失败', 'error');
    }
  };

  const togglePrivacy = (key) => {
    setProfile((prev) => prev ? {
      ...prev,
      privacy: { ...prev.privacy, [key]: !prev.privacy[key] }
    } : prev);
  };

  const handleFriendAction = async (reqId, action) => {
    try {
      await api.put(`/friends/requests/${reqId}`, { action });
      addToast(action === 'accept' ? '已同意' : '已拒绝', 'success');
      fetchProfile();
    } catch (err) { addToast('操作失败', 'error'); }
  };

  if (loading) return <Loading />;
  if (!profile) return <div className="text-center py-20 text-gray-400">加载失败</div>;

  const filteredPosts = catFilter === 'all'
    ? (profile.posts || [])
    : (profile.posts || []).filter((p) => p.category === catFilter);

  const filteredFavs = catFilter === 'all'
    ? (profile.favorited_posts || [])
    : (profile.favorited_posts || []).filter((p) => p.category === catFilter);

  return (
    <div className="max-w-[800px] mx-auto">
      <div className="bg-white rounded-lg p-8 flex items-center gap-6 mb-5">
        <div className="relative cursor-pointer flex-shrink-0 group" onClick={() => document.getElementById('avatar-upload').click()}>
          <img src={user?.avatar_url || '/static/img/default_avatar.svg'} alt="" className="w-20 h-20 rounded-full object-cover" />
          <div className="absolute inset-0 rounded-full bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
            <span className="text-white text-[11px]">更换头像</span>
          </div>
          <input id="avatar-upload" type="file" accept="image/*" className="hidden" onChange={handleAvatarChange} />
        </div>
        <div className="flex-1">
          {editing ? (
            <div className="flex items-center gap-2">
              <input type="text" value={nickname} onChange={(e) => setNickname(e.target.value)}
                className="px-2.5 py-1 border border-gray-300 rounded text-lg font-semibold outline-none w-[180px]" />
              <button onClick={handleNicknameSave} className="px-3 py-1 bg-gray-900 text-white rounded text-[13px]">保存</button>
              <button onClick={() => { setEditing(false); setNickname(user?.nickname || ''); }}
                className="px-3 py-1 border border-gray-300 rounded text-[13px] text-gray-500">取消</button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <h2 className="text-[22px] font-semibold">{user?.nickname}</h2>
              <button onClick={() => setEditing(true)} className="text-sm opacity-40 hover:opacity-100 transition">✏️</button>
            </div>
          )}
          <div className="flex gap-6 text-[13px] text-gray-500 mt-2">
            <span>获赞 <strong className="text-gray-700">{profile.user?.like_count ?? 0}</strong></span>
            <span>关注 <strong className="text-gray-700">{profile.user?.following_count ?? 0}</strong></span>
            <span>粉丝 <strong className="text-gray-700">{profile.user?.follower_count ?? 0}</strong></span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg">
        <div className="flex border-b-2 border-gray-100">
          {tabs.map((tab) => (
            <button key={tab.key} onClick={() => { setSearchParams({ tab: tab.key }); }}
              className={`px-4 py-2.5 text-sm border-b-2 -mb-0.5 transition ${activeTab === tab.key ? 'text-gray-900 font-semibold border-gray-900' : 'text-gray-500 border-transparent hover:text-gray-700'}`}>
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {/* Posts */}
          {(activeTab === 'posts' || activeTab === 'favorites') && (
            <div className="flex gap-0 mb-5 border-b border-gray-100">
              {['all', 'daily', 'news', 'academic', 'trade'].map((k) => (
                <button key={k} onClick={() => setSearchParams({ tab: activeTab, cat: k })}
                  className={`px-3 py-1 text-xs ${catFilter === k ? 'text-gray-900 font-semibold' : 'text-gray-400'}`}>
                  {k === 'all' ? '全部' : k === 'daily' ? '日常' : k === 'news' ? '新闻' : k === 'academic' ? '学术' : '交易'}
                </button>
              ))}
            </div>
          )}

          {activeTab === 'posts' && (
            filteredPosts.length > 0 ? filteredPosts.map((p) => <PostCard key={p.id} post={p} />)
            : <EmptyState message="还没有发布过帖子" />
          )}

          {activeTab === 'favorites' && (
            filteredFavs.length > 0 ? filteredFavs.map((p) => <PostCard key={p.id} post={p} />)
            : <EmptyState message="还没有收藏任何帖子" />
          )}

          {activeTab === 'friends' && (
            <>
              {profile.pending_requests?.length > 0 && (
                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <h3 className="text-xs text-gray-500 font-medium mb-2">待处理的好友请求</h3>
                  {profile.pending_requests.map((r) => (
                    <div key={r.id} className="flex items-center justify-between py-2">
                      <div className="flex items-center gap-2">
                        <img src={r.user.avatar_url} alt="" className="w-8 h-8 rounded-full" />
                        <span className="text-sm">{r.user.nickname}</span>
                      </div>
                      <div className="flex gap-1.5">
                        <button onClick={() => handleFriendAction(r.id, 'accept')} className="px-2.5 py-1 bg-gray-900 text-white rounded text-xs">同意</button>
                        <button onClick={() => handleFriendAction(r.id, 'reject')} className="px-2.5 py-1 border border-gray-300 rounded text-xs text-gray-500">拒绝</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {profile.my_sent_requests?.length > 0 && (
                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <h3 className="text-xs text-gray-500 font-medium mb-2">等待对方通过的请求</h3>
                  {profile.my_sent_requests.map((r) => (
                    <div key={r.id} className="flex items-center gap-2 py-2">
                      <img src={r.user.avatar_url} alt="" className="w-8 h-8 rounded-full" />
                      <span className="text-sm">{r.user.nickname}</span>
                      <span className="text-xs text-gray-400 ml-auto">⏳ 等待中</span>
                    </div>
                  ))}
                </div>
              )}
              {profile.friend_users?.length > 0 ? (
                profile.friend_users.map((f) => (
                  <div key={f.id} className="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
                    <div className="flex items-center gap-2.5">
                      <img src={f.avatar_url} alt="" className="w-9 h-9 rounded-full" />
                      <span className="text-sm font-medium">{f.nickname}</span>
                    </div>
                    <Link to={`/chat/${f.id}`} className="px-3 py-1 border border-gray-300 rounded text-xs text-gray-500">发消息</Link>
                  </div>
                ))
              ) : <EmptyState message="暂无长时好友" />}
            </>
          )}

          {activeTab === 'short' && (
            profile.short_contacts?.length > 0 ? (
              profile.short_contacts.map((c) => (
                <div key={c.id} className="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
                  <div className="flex items-center gap-2.5">
                    <img src={c.avatar_url} alt="" className="w-9 h-9 rounded-full" />
                    <span className="text-sm font-medium">{c.nickname}</span>
                  </div>
                  <Link to={`/chat/${c.id}`} className="px-3 py-1 border border-gray-300 rounded text-xs text-gray-500">发消息</Link>
                </div>
              ))
            ) : <EmptyState message="暂无短时联系人" />
          )}

          {activeTab === 'following' && (
            profile.following?.length > 0 ? (
              profile.following.map((f) => (
                <div key={f.id} className="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
                  <div className="flex items-center gap-2.5">
                    <img src={f.avatar_url} alt="" className="w-9 h-9 rounded-full" />
                    <span className="text-sm font-medium">{f.nickname}</span>
                  </div>
                  <Link to={`/user/${f.id}`} className="px-3 py-1 border border-gray-300 rounded text-xs text-gray-500">查看主页</Link>
                </div>
              ))
            ) : <EmptyState message="你还没有关注任何人" />
          )}

          {activeTab === 'followers' && (
            profile.followers?.length > 0 ? (
              profile.followers.map((f) => (
                <div key={f.id} className="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
                  <div className="flex items-center gap-2.5">
                    <img src={f.avatar_url} alt="" className="w-9 h-9 rounded-full" />
                    <span className="text-sm font-medium">{f.nickname}</span>
                  </div>
                  <Link to={`/user/${f.id}`} className="px-3 py-1 border border-gray-300 rounded text-xs text-gray-500">查看主页</Link>
                </div>
              ))
            ) : <EmptyState message="还没有粉丝" />
          )}

          {activeTab === 'privacy' && (
            <div className="space-y-3">
              <div className="flex justify-between items-center pb-2">
                <h3 className="text-sm font-semibold text-gray-700">🔒 隐私设置</h3>
                <button onClick={handlePrivacySave} className="px-4 py-2 bg-gray-900 text-white rounded-md text-sm">保存设置</button>
              </div>
              {Object.entries(profile.privacy || {}).map(([k, v]) => (
                <div key={k} className="flex justify-between items-center py-2.5 border-b border-gray-50 last:border-0">
                  <span className="text-sm text-gray-600">
                    {k === 'show_posts' && '允许他人查看我的帖子'}
                    {k === 'show_favorites' && '允许他人查看我的收藏'}
                    {k === 'show_following' && '允许他人查看我的关注'}
                    {k === 'allow_short_chat' && '允许他人与我短时聊天'}
                    {k === 'allow_friend_request' && '允许他人添加我为好友'}
                  </span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" checked={v} onChange={() => togglePrivacy(k)} />
                    <div className="w-11 h-6 bg-gray-300 peer-checked:bg-gray-900 rounded-full after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-5"></div>
                  </label>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
