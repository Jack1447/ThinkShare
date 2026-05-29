import { Link } from 'react-router-dom';

const categoryMap = {
  daily: '日常生活',
  news: '时事新闻',
  academic: '学术科研',
  trade: '二手交易',
};

export default function PostCard({ post }) {
  return (
    <Link to={`/post/${post.id}`}>
      <div className="bg-white rounded-lg p-5 mb-2.5 cursor-pointer hover:shadow-md transition-shadow duration-200">
        <div className="flex items-center gap-2 mb-2.5">
          <img
            src={post.author?.avatar_url || '/static/img/default_avatar.svg'}
            alt="avatar"
            className="w-7 h-7 rounded-full object-cover"
          />
          <Link
            to={`/user/${post.user_id}`}
            className="text-[13px] text-gray-500 font-medium hover:text-gray-800"
            onClick={(e) => e.stopPropagation()}
          >
            {post.author?.nickname || '未知用户'}
          </Link>
          <span className="text-xs text-gray-400 ml-auto">
            {post.created_at ? new Date(post.created_at).toLocaleDateString('zh-CN') : ''}
          </span>
        </div>

        <h3 className="text-[17px] font-semibold text-gray-900 mb-2 leading-relaxed">
          {post.title}
        </h3>

        {post.content_plain && (
          <p className="text-sm text-gray-500 leading-relaxed line-clamp-2 mb-3">
            {post.content_plain}
          </p>
        )}

        <div className="flex items-center gap-5 text-[13px] text-gray-400">
          <span className="flex items-center gap-1">❤️ {post.like_count ?? 0}</span>
          <span className="flex items-center gap-1">💬 {post.comment_count ?? 0}</span>
          <span className="flex items-center gap-1">⭐ {post.favorite_count ?? 0}</span>
          <span className="flex items-center gap-1">👁 {post.views ?? 0}</span>
          <span className="ml-auto bg-gray-100 px-2.5 py-0.5 rounded text-xs text-gray-500">
            {categoryMap[post.category] || post.category}
          </span>
        </div>
      </div>
    </Link>
  );
}
