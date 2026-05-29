import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useState } from 'react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState('post');

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}&type=${searchType}`);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="fixed top-0 left-0 right-0 h-14 bg-white border-b border-gray-200 flex items-center justify-between px-8 z-50 shadow-sm">
      <Link to="/forum" className="text-xl font-bold text-gray-900 tracking-tight">
        📚 校园交流平台
      </Link>

      <form onSubmit={handleSearch} className="flex items-center flex-1 max-w-md mx-5">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="搜索帖子或用户..."
          className="flex-1 px-3 py-1.5 border border-gray-300 border-r-0 rounded-l-md text-sm outline-none focus:border-gray-400"
        />
        <select
          value={searchType}
          onChange={(e) => setSearchType(e.target.value)}
          className="px-2 py-1.5 border border-gray-300 border-r-0 text-sm text-gray-500 bg-gray-50 outline-none cursor-pointer"
        >
          <option value="post">帖子</option>
          <option value="user">用户</option>
        </select>
        <button
          type="submit"
          className="px-3.5 py-1.5 border border-gray-300 rounded-r-md bg-gray-50 text-sm text-gray-500 hover:bg-gray-100 transition"
        >
          搜索
        </button>
      </form>

      <div className="flex items-center gap-5">
        <Link to="/notifications" className="relative text-lg text-gray-500 hover:text-gray-700">
          🔔
          {user?.unread_count > 0 && (
            <span className="absolute -top-1.5 -right-2 bg-red-500 text-white text-[10px] font-bold min-w-[16px] h-4 leading-4 text-center rounded-full px-1">
              {user.unread_count}
            </span>
          )}
        </Link>

        <img
          src={user?.avatar_url || '/static/img/default_avatar.svg'}
          alt="avatar"
          className="w-7 h-7 rounded-full object-cover"
        />
        <span className="text-sm text-gray-400">{user?.nickname}</span>

        <Link to="/profile" className="text-sm text-gray-500 hover:text-gray-700">我的主页</Link>

        {user?.is_admin && (
          <Link to="/admin" className="text-sm text-gray-500 hover:text-gray-700">⚙️ 管理</Link>
        )}

        <button onClick={handleLogout} className="text-sm text-gray-500 hover:text-gray-700">
          退出
        </button>
      </div>
    </nav>
  );
}
