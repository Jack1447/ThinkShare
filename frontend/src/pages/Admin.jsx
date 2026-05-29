import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { useToast } from '../components/Toast';
import Loading from '../components/Loading';

export default function Admin() {
  const { addToast } = useToast();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = () => {
    api.get('/admin')
      .then((res) => setData(res.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const handleBan = async (userId, nickname) => {
    if (!confirm(`确定要封禁用户 ${nickname} 吗？`)) return;
    try {
      await api.post(`/admin/ban/${userId}`);
      addToast(`用户 ${nickname} 已被封禁`, 'success');
      fetchData();
    } catch (err) { addToast('操作失败', 'error'); }
  };

  const handleUnban = async (userId, nickname) => {
    if (!confirm(`确定要解封用户 ${nickname} 吗？`)) return;
    try {
      await api.post(`/admin/unban/${userId}`);
      addToast(`用户 ${nickname} 已解封`, 'success');
      fetchData();
    } catch (err) { addToast('操作失败', 'error'); }
  };

  if (loading) return <Loading />;
  if (!data) return <div className="text-center py-20 text-gray-400">无权访问或加载失败</div>;

  const { stats, users } = data;

  return (
    <div className="max-w-[900px] mx-auto">
      <div className="bg-white rounded-lg p-4 px-6 mb-4 flex justify-between items-center">
        <h2 className="text-lg font-semibold">⚙️ 管理后台</h2>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: '用户总数', value: stats.total_users },
          { label: '帖子总数', value: stats.total_posts },
          { label: '评论总数', value: stats.total_comments },
          { label: '已封禁', value: stats.banned_users, color: 'text-red-500' },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-lg p-5 text-center">
            <span className={`block text-2xl font-bold ${s.color || 'text-gray-900'}`}>{s.value}</span>
            <span className="block text-[13px] text-gray-400 mt-1">{s.label}</span>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-lg p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">👥 用户列表</h3>
        {users.map((u) => (
          <div key={u.id} className="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
            <div className="flex items-center gap-2.5">
              <img src={u.avatar_url || '/static/img/default_avatar.svg'} alt="" className="w-9 h-9 rounded-full" />
              <span className="text-sm font-medium">{u.nickname}</span>
              <span className="text-xs text-gray-400">@{u.username}</span>
              {u.is_admin && <span className="bg-gray-900 text-white text-[11px] px-2 py-0.5 rounded-full font-medium">管理员</span>}
              {u.is_banned && <span className="bg-red-500 text-white text-[11px] px-2 py-0.5 rounded-full font-medium">已封禁</span>}
            </div>
            <span className="text-xs text-gray-400">{new Date(u.created_at).toLocaleDateString('zh-CN')} 注册</span>
            <div className="flex gap-1.5">
              <Link to={`/user/${u.id}`} className="px-2.5 py-1 border border-gray-300 rounded text-xs text-gray-500">查看</Link>
              {!u.is_admin && (
                u.is_banned
                  ? <button onClick={() => handleUnban(u.id, u.nickname)} className="px-2.5 py-1 bg-gray-900 text-white rounded text-xs">解封</button>
                  : <button onClick={() => handleBan(u.id, u.nickname)} className="px-2.5 py-1 bg-red-500 text-white rounded text-xs">封禁</button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
