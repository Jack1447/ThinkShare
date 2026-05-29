import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/Toast';
import Loading from '../components/Loading';

const categoryMap = {
  daily: '日常生活', news: '时事新闻', academic: '学术科研', trade: '二手交易',
};

function CommentItem({ comment, postId, onReply, depth = 0 }) {
  const { user } = useAuth();
  const { addToast } = useToast();
  const [showReply, setShowReply] = useState(false);
  const [replyContent, setReplyContent] = useState('');

  const handleDelete = async () => {
    if (!confirm('确定要删除这条评论吗？所有回复也会被删除。')) return;
    try {
      await api.delete(`/comments/${comment.id}`);
      addToast('评论已删除', 'info');
      onReply();
    } catch (err) {
      addToast('删除失败', 'error');
    }
  };

  const handleReply = async (e) => {
    e.preventDefault();
    if (!replyContent.trim()) return;
    try {
      await api.post(`/posts/${postId}/comments`, { content: replyContent, parent_id: comment.id });
      addToast('回复成功', 'success');
      setReplyContent('');
      setShowReply(false);
      onReply();
    } catch (err) {
      addToast('回复失败', 'error');
    }
  };

  return (
    <div className={`py-4 border-b border-gray-50 last:border-b-0 ${depth > 0 ? 'border-l-2 border-gray-100 pl-3' : ''}`}
      style={{ marginLeft: depth * 24 }}
      id={`comment-${comment.id}`}
    >
      <div className="flex items-center gap-2 mb-2 text-[13px] text-gray-500">
        <Link to={`/user/${comment.user_id}`}>
          <img src={comment.author?.avatar_url || '/static/img/default_avatar.svg'} alt="" className="w-[22px] h-[22px] rounded-full object-cover" />
        </Link>
        <Link to={`/user/${comment.user_id}`} className="font-medium text-gray-500 hover:text-gray-800">
          {comment.author?.nickname}
        </Link>
        <span className="text-xs text-gray-400">
          {comment.created_at ? new Date(comment.created_at).toLocaleString('zh-CN') : ''}
        </span>
        {(comment.user_id === user?.id || user?.is_admin) && (
          <button onClick={handleDelete} className="ml-auto text-gray-300 hover:text-red-400 text-base font-bold">×</button>
        )}
      </div>
      <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{comment.content}</div>
      <button onClick={() => setShowReply(!showReply)} className="text-xs text-gray-400 hover:text-gray-600 mt-2">
        回复
      </button>
      {showReply && (
        <form onSubmit={handleReply} className="mt-2">
          <textarea
            value={replyContent}
            onChange={(e) => setReplyContent(e.target.value)}
            placeholder="写下你的回复..."
            className="w-full px-2.5 py-1.5 border border-gray-200 rounded text-sm resize-y min-h-[50px] outline-none focus:border-gray-400 mb-1.5"
            required
          />
          <div className="flex gap-2">
            <button type="submit" className="px-3 py-1 bg-gray-900 text-white rounded text-xs">回复</button>
            <button type="button" onClick={() => setShowReply(false)} className="px-3 py-1 border border-gray-300 rounded text-xs text-gray-500">取消</button>
          </div>
        </form>
      )}
      {comment.replies?.map((reply) => (
        <CommentItem key={reply.id} comment={reply} postId={postId} onReply={onReply} depth={depth + 1} />
      ))}
    </div>
  );
}

export default function PostDetail() {
  const { postId } = useParams();
  const { user, updateUser } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [contentHtml, setContentHtml] = useState('');
  const [liked, setLiked] = useState(false);
  const [favorited, setFavorited] = useState(false);
  const [likeCount, setLikeCount] = useState(0);
  const [favCount, setFavCount] = useState(0);
  const [commentText, setCommentText] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchPost = () => {
    api.get(`/posts/${postId}`)
      .then((res) => {
        setPost(res.data.post);
        setComments(res.data.comments || []);
        setContentHtml(res.data.content_html);
        setLiked(res.data.user_liked);
        setFavorited(res.data.user_favorited);
        setLikeCount(res.data.post.like_count);
        setFavCount(res.data.post.favorite_count);
      })
      .catch(() => setPost(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchPost(); }, [postId]);

  const handleLike = async () => {
    try {
      const res = await api.post(`/posts/${postId}/like`);
      setLiked(res.data.liked);
      setLikeCount(res.data.like_count);
    } catch (err) { addToast('操作失败', 'error'); }
  };

  const handleFav = async () => {
    try {
      const res = await api.post(`/posts/${postId}/favorite`);
      setFavorited(res.data.favorited);
      setFavCount(res.data.favorite_count);
    } catch (err) { addToast('操作失败', 'error'); }
  };

  const handleDelete = async () => {
    if (!confirm('确定要删除这个帖子吗？所有评论也会被删除。')) return;
    try {
      await api.delete(`/posts/${postId}`);
      addToast('帖子已删除', 'info');
      navigate('/forum');
    } catch (err) { addToast('删除失败', 'error'); }
  };

  const handleComment = async (e) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    try {
      await api.post(`/posts/${postId}/comments`, { content: commentText });
      addToast('评论成功', 'success');
      setCommentText('');
      fetchPost();
    } catch (err) { addToast('评论失败', 'error'); }
  };

  if (loading) return <Loading />;
  if (!post) return <div className="text-center py-20 text-gray-400">帖子不存在</div>;

  return (
    <div className="max-w-[700px] mx-auto">
      <div className="bg-white rounded-lg p-7 mb-4">
        <div className="flex items-center gap-3.5 pb-5 border-b border-gray-100 mb-5">
          <img src={post.author?.avatar_url || '/static/img/default_avatar.svg'} alt="" className="w-12 h-12 rounded-full object-cover" />
          <div className="flex-1">
            <Link to={`/user/${post.user_id}`} className="text-base font-semibold text-gray-800 hover:text-gray-900">
              {post.author?.nickname}
            </Link>
            <div className="text-[13px] text-gray-400 mt-0.5">
              {post.created_at ? new Date(post.created_at).toLocaleString('zh-CN') : ''} · 👁 {post.views} 阅读 ·
              <span className="bg-gray-100 px-2.5 py-0.5 rounded text-xs text-gray-500 ml-1">
                {categoryMap[post.category]}
              </span>
            </div>
          </div>
          {(post.user_id === user?.id || user?.is_admin) && (
            <button onClick={handleDelete} className="text-gray-300 hover:text-red-400 text-lg" title="删除">🗑️</button>
          )}
        </div>
        <h1 className="text-[22px] font-bold text-gray-900 mb-4 leading-relaxed">{post.title}</h1>
        <div className="text-[15px] text-gray-700 leading-[1.8] markdown-body" dangerouslySetInnerHTML={{ __html: contentHtml }} />
        <div className="flex gap-6 pt-4 text-sm text-gray-500">
          <button onClick={handleLike} className={`flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-50 transition ${liked ? 'text-red-500' : ''}`}>
            {liked ? '❤️' : '🤍'} {likeCount} 赞
          </button>
          <button onClick={handleFav} className={`flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-50 transition ${favorited ? 'text-yellow-500' : ''}`}>
            {favorited ? '⭐' : '☆'} {favCount} 收藏
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg p-6">
        <h3 className="text-base font-semibold text-gray-800 mb-4">💬 评论 ({comments.length})</h3>
        <form onSubmit={handleComment} className="mb-5 pb-5 border-b border-gray-100">
          <textarea
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            placeholder="写下你的评论..."
            className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm resize-y min-h-[80px] outline-none focus:border-gray-400 mb-2.5"
            required
          />
          <button type="submit" className="px-4 py-1.5 border border-gray-300 rounded-md text-sm text-gray-500 hover:border-gray-400 hover:text-gray-700 transition">
            发表评论
          </button>
        </form>
        {comments.length > 0 ? (
          comments.map((c) => <CommentItem key={c.id} comment={c} postId={Number(postId)} onReply={fetchPost} />)
        ) : (
          <div className="text-center py-10 text-gray-400 text-sm">暂无评论，来说点什么吧</div>
        )}
      </div>
    </div>
  );
}
