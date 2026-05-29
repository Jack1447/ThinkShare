import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/Toast';
import Loading from '../components/Loading';
import EmptyState from '../components/EmptyState';

export default function Notifications() {
  const { updateUser } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [notifs, setNotifs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/notifications')
      .then((res) => setNotifs(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const readAll = async () => {
    try {
      await api.post('/notifications/read-all');
      setNotifs((prev) => prev.map((n) => ({ ...n, is_read: true })));
      addToast('已全部标为已读', 'success');
    } catch (err) { addToast('操作失败', 'error'); }
  };

  const readOne = async (n) => {
    if (!n.is_read) {
      try { await api.post(`/notifications/${n.id}/read`); } catch {}
    }
    if (n.link && n.link.startsWith('/')) {
      navigate(n.link.replace('?tab=', '?'));
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="max-w-[700px] mx-auto">
      <div className="bg-white rounded-lg p-4 px-6 mb-2.5 flex justify-between items-center">
        <h2 className="text-lg font-semibold">🔔 消息通知</h2>
        {notifs.length > 0 && (
          <button onClick={readAll} className="px-3 py-1 border border-gray-300 rounded text-xs text-gray-500 hover:border-gray-400 transition">
            全部已读
          </button>
        )}
      </div>

      {notifs.length > 0 ? (
        notifs.map((n) => (
          <div
            key={n.id}
            onClick={() => readOne(n)}
            className={`block bg-white rounded-lg p-4 px-6 mb-1.5 hover:bg-gray-50 transition cursor-pointer ${!n.is_read ? 'bg-blue-50/30' : ''}`}
          >
            <div className="flex items-center gap-3">
              <img src={n.from_user?.avatar_url || '/static/img/default_avatar.svg'} alt="" className="w-9 h-9 rounded-full object-cover" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-700">{n.content}</p>
                <span className="text-xs text-gray-400">{new Date(n.created_at).toLocaleString('zh-CN')}</span>
              </div>
              {!n.is_read && <span className="w-2 h-2 bg-red-500 rounded-full flex-shrink-0"></span>}
            </div>
          </div>
        ))
      ) : (
        <div className="bg-white rounded-lg"><EmptyState message="暂无通知" /></div>
      )}
    </div>
  );
}
