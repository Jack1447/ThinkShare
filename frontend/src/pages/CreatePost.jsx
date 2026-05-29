import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useToast } from '../components/Toast';

export default function CreatePost() {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('');
  const [content, setContent] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !content.trim() || !category) {
      addToast('所有字段都必须填写', 'error');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('/posts', { title: title.trim(), content: content.trim(), category });
      addToast('帖子发布成功！', 'success');
      navigate(`/post/${res.data.id}`);
    } catch (err) {
      addToast(err.response?.data?.message || '发布失败', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-[800px] mx-auto">
      <div className="bg-white rounded-lg p-7">
        <h2 className="text-xl font-bold text-gray-900 mb-6">✏️ 发布新帖</h2>
        <form onSubmit={handleSubmit}>
          <div className="flex gap-4 items-end mb-5">
            <div className="flex-1">
              <label className="block text-[13px] text-gray-500 font-medium mb-1.5">标题</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="请输入标题"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm outline-none focus:border-gray-400"
                required
              />
            </div>
            <div className="w-[180px] flex-shrink-0">
              <label className="block text-[13px] text-gray-500 font-medium mb-1.5">板块</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm outline-none focus:border-gray-400 bg-white"
                required
              >
                <option value="">选择板块</option>
                <option value="daily">日常生活</option>
                <option value="news">时事新闻</option>
                <option value="academic">学术科研</option>
                <option value="trade">二手交易</option>
              </select>
            </div>
          </div>

          <div className="mb-5">
            <label className="block text-[13px] text-gray-500 font-medium mb-1.5">内容（支持 Markdown）</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="分享你的想法..."
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm resize-y min-h-[300px] outline-none focus:border-gray-400 font-mono"
              required
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <Link to="/forum" className="px-4 py-2 border border-gray-300 rounded-md text-sm text-gray-500 hover:border-gray-400 transition">取消</Link>
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2 bg-gray-900 text-white rounded-md text-sm font-medium hover:bg-gray-700 transition disabled:opacity-50"
            >
              {submitting ? '发布中...' : '发布帖子'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
