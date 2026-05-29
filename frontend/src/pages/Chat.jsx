import { useState, useRef, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/Toast';
import api from '../services/api';
import Loading from '../components/Loading';

export default function Chat() {
  const { peerId } = useParams();
  const { user } = useAuth();
  const { addToast } = useToast();
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [peer, setPeer] = useState(null);
  const [chatType, setChatType] = useState('short');
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const messagesEnd = useRef(null);

  const scrollToBottom = () => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [messages]);

  useEffect(() => {
    setLoading(true);
    api.get(`/chat/${peerId}`)
      .then((res) => {
        setPeer(res.data.peer);
        setMessages(res.data.messages || []);
        setChatType(res.data.chat_type);
        setTotalCount(res.data.total_count);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [peerId]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    try {
      const res = await api.post(`/chat/${peerId}`, { content: text });
      setText('');
      setTotalCount((c) => c + 1);
      setMessages((prev) => [...prev, res.data]);
    } catch (err) {
      addToast(err.response?.data?.message || '发送失败', 'error');
    }
  };

  const handleAddFriend = async () => {
    try {
      await api.post(`/friends/${peerId}`);
      addToast('好友请求已发送', 'success');
    } catch (err) {
      addToast(err.response?.data?.message || '操作失败', 'error');
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="max-w-[700px] mx-auto">
      <div className="bg-white rounded-lg overflow-hidden flex flex-col h-[600px]">
        <div className="px-5 py-3.5 border-b border-gray-100 bg-gray-50 flex items-center gap-3 text-[15px] font-semibold">
          <Link to="/forum" className="text-gray-400 hover:text-gray-600 font-normal">← 返回</Link>
          <span>与 {peer?.nickname || `用户${peerId}`} 聊天</span>
          {chatType === 'short' && (
            <span className="ml-auto text-xs text-gray-400 font-normal bg-gray-200 px-2 py-0.5 rounded-full">
              短时 {totalCount}/10
            </span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-3 scrollbar-thin">
          {messages.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
              还没有消息，打个招呼吧！
            </div>
          ) : (
            messages.map((msg, i) => (
              <div
                key={msg.id || i}
                className={`max-w-[70%] px-3.5 py-2.5 rounded-lg text-sm leading-relaxed ${
                  msg.sender_id === user?.id
                    ? 'self-end bg-gray-900 text-white'
                    : 'self-start bg-gray-100 text-gray-800'
                }`}
              >
                {msg.content}
                {msg.file_url && (
                  <a href={msg.file_url} target="_blank" rel="noopener noreferrer">
                    <img src={msg.file_url} alt={msg.file_name || 'file'} className="max-w-[200px] max-h-[200px] rounded mt-1" />
                  </a>
                )}
              </div>
            ))
          )}
          <div ref={messagesEnd} />
        </div>

        <form onSubmit={handleSend} className="flex px-4 py-3 border-t border-gray-100 gap-2.5">
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={chatType === 'short' && totalCount >= 10 ? '已达上限' : '输入消息...'}
            disabled={chatType === 'short' && totalCount >= 10}
            className="flex-1 px-3 py-2 border border-gray-200 rounded-md text-sm outline-none focus:border-gray-400 disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={chatType === 'short' && totalCount >= 10}
            className="px-4 py-2 bg-gray-900 text-white rounded-md text-sm font-medium hover:bg-gray-700 transition disabled:opacity-50"
          >
            发送
          </button>
        </form>
      </div>

      {chatType === 'short' && (
        <div className="text-center mt-3">
          <button onClick={handleAddFriend} className="text-sm text-gray-400 hover:text-gray-600 underline">
            ➕ 添加好友可解锁无限聊天
          </button>
        </div>
      )}
    </div>
  );
}
