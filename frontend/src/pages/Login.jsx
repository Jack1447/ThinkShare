import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/Toast';

export default function Login() {
  const { login } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', password: '' });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.username.trim() || !form.password) return;
    setSubmitting(true);
    try {
      await login(form.username.trim(), form.password);
      addToast('登录成功！', 'success');
      navigate('/forum');
    } catch (err) {
      addToast(err.response?.data?.message || '用户名或密码错误', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-[400px] bg-white rounded-xl shadow-sm p-12 mx-4">
      <h1 className="text-center text-2xl font-bold text-gray-900 mb-1">📚 校园交流平台</h1>
      <p className="text-center text-sm text-gray-400 mb-8">登录你的账号</p>

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-[13px] text-gray-500 font-medium mb-1.5">用户名</label>
          <input
            type="text"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            placeholder="请输入用户名"
            className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm outline-none focus:border-gray-400 transition"
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-[13px] text-gray-500 font-medium mb-1.5">密码</label>
          <input
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            placeholder="请输入密码"
            className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm outline-none focus:border-gray-400 transition"
            required
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2.5 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-700 transition disabled:opacity-50"
        >
          {submitting ? '登录中...' : '登录'}
        </button>
      </form>

      <p className="text-center mt-5 text-[13px] text-gray-400">
        还没有账号？<Link to="/register" className="text-gray-700 font-medium hover:underline">立即注册</Link>
      </p>
    </div>
  );
}
