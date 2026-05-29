import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/Toast';

export default function Register() {
  const { register } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: '',
    nickname: '',
    password: '',
    passwordConfirm: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { username, nickname, password, passwordConfirm } = form;

    if (!username.trim() || !nickname.trim() || !password) {
      addToast('所有字段都必须填写', 'error');
      return;
    }
    if (password !== passwordConfirm) {
      addToast('两次密码输入不一致', 'error');
      return;
    }
    if (password.length < 6) {
      addToast('密码至少需要6位', 'error');
      return;
    }

    setSubmitting(true);
    try {
      await register(username.trim(), nickname.trim(), password);
      addToast('注册成功！请登录', 'success');
      navigate('/login');
    } catch (err) {
      addToast(err.response?.data?.message || '注册失败，该用户名可能已被注册', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const update = (key, value) => setForm({ ...form, [key]: value });

  return (
    <div className="w-full max-w-[400px] bg-white rounded-xl shadow-sm p-12 mx-4">
      <h1 className="text-center text-2xl font-bold text-gray-900 mb-1">📚 校园交流平台</h1>
      <p className="text-center text-sm text-gray-400 mb-8">注册新账号</p>

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-[13px] text-gray-500 font-medium mb-1.5">用户名</label>
          <input
            type="text"
            value={form.username}
            onChange={(e) => update('username', e.target.value)}
            placeholder="请设置登录用户名"
            className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm outline-none focus:border-gray-400 transition"
            required
          />
        </div>

        <div className="mb-4">
          <label className="block text-[13px] text-gray-500 font-medium mb-1.5">昵称</label>
          <input
            type="text"
            value={form.nickname}
            onChange={(e) => update('nickname', e.target.value)}
            placeholder="你在论坛中的显示名称"
            className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm outline-none focus:border-gray-400 transition"
            required
          />
        </div>

        <div className="mb-4">
          <label className="block text-[13px] text-gray-500 font-medium mb-1.5">密码</label>
          <input
            type="password"
            value={form.password}
            onChange={(e) => update('password', e.target.value)}
            placeholder="至少6位密码"
            className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm outline-none focus:border-gray-400 transition"
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-[13px] text-gray-500 font-medium mb-1.5">确认密码</label>
          <input
            type="password"
            value={form.passwordConfirm}
            onChange={(e) => update('passwordConfirm', e.target.value)}
            placeholder="再次输入密码"
            className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm outline-none focus:border-gray-400 transition"
            required
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2.5 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-700 transition disabled:opacity-50"
        >
          {submitting ? '注册中...' : '注册'}
        </button>
      </form>

      <p className="text-center mt-5 text-[13px] text-gray-400">
        已有账号？<Link to="/login" className="text-gray-700 font-medium hover:underline">立即登录</Link>
      </p>
    </div>
  );
}
