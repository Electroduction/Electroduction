import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { io } from 'socket.io-client';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

const SOCKET_URL = import.meta.env.VITE_API_URL?.replace('/api','') || 'http://localhost:5000';

export default function Messages() {
  const { userId: paramUserId } = useParams();
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [activeUser, setActiveUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMsg, setNewMsg] = useState('');
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [typing, setTyping] = useState(false);
  const socketRef = useRef(null);
  const bottomRef = useRef(null);

  // Connect Socket.IO
  useEffect(() => {
    if (!user) return;
    const socket = io(SOCKET_URL, { transports: ['websocket'] });
    socketRef.current = socket;
    socket.emit('join', user.id);

    socket.on('new_message', (msg) => {
      setMessages(prev => [...prev, msg]);
      setConversations(prev => prev.map(c =>
        c.user_id === msg.sender_id ? { ...c, last_message: msg.content } : c
      ));
    });

    socket.on('typing', ({ userId, isTyping }) => {
      if (userId === activeUser?.user_id) setTyping(isTyping);
    });

    return () => socket.disconnect();
  }, [user, activeUser?.user_id]);

  const fetchConversations = useCallback(async () => {
    try {
      const r = await api.get('/messages/conversations');
      setConversations(r.data.conversations || []);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchConversations(); }, [fetchConversations]);

  useEffect(() => {
    if (paramUserId) {
      api.get(`/messages/${paramUserId}`)
        .then(r => {
          setMessages(r.data.messages || []);
          // find or build activeUser from first message
          const msgs = r.data.messages || [];
          if (msgs.length > 0) {
            const other = msgs[0].sender_id === user?.id
              ? { user_id: msgs[0].recipient_id, display_name: msgs[0].recipient_display_name, username: msgs[0].recipient_username }
              : { user_id: msgs[0].sender_id, display_name: msgs[0].sender_display_name, username: msgs[0].sender_username };
            setActiveUser(other);
          }
        })
        .catch(() => {});
    }
  }, [paramUserId, user?.id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const openConversation = async (conv) => {
    setActiveUser(conv);
    navigate(`/messages/${conv.user_id}`);
    try {
      const r = await api.get(`/messages/${conv.user_id}`);
      setMessages(r.data.messages || []);
    } catch { toast.error('Could not load messages'); }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMsg.trim() || !activeUser) return;
    setSending(true);
    try {
      await api.post('/messages', { recipientId: activeUser.user_id, content: newMsg });
      const optimistic = {
        id: Date.now(), sender_id: user.id, recipient_id: activeUser.user_id,
        content: newMsg, created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, optimistic]);
      socketRef.current?.emit('send_message', { recipientId: activeUser.user_id, message: optimistic });
      setNewMsg('');
      fetchConversations();
    } catch { toast.error('Failed to send message'); }
    finally { setSending(false); }
  };

  const handleTyping = (e) => {
    setNewMsg(e.target.value);
    socketRef.current?.emit('typing', { recipientId: activeUser?.user_id, isTyping: e.target.value.length > 0 });
  };

  const timeLabel = (dt) => new Date(dt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const initials = (name) => (name || '?').split(' ').map(w => w[0]).join('').toUpperCase().slice(0,2);

  if (!user) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-500">Sign in to access messages</p>
        <button onClick={() => navigate('/login')} className="btn-primary mt-4">Sign in</button>
      </div>
    );
  }

  return (
    <div className="card p-0 overflow-hidden" style={{ height: 'calc(100vh - 180px)' }}>
      <div className="flex h-full">
        {/* Sidebar */}
        <div className="w-72 border-r dark:border-gray-700 flex flex-col flex-shrink-0">
          <div className="p-4 border-b dark:border-gray-700">
            <h2 className="font-bold text-lg">Messages</h2>
          </div>
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="p-4 text-center text-gray-400 text-sm">Loading…</div>
            ) : conversations.length === 0 ? (
              <div className="p-4 text-center text-gray-400 text-sm">No conversations yet</div>
            ) : (
              conversations.map(c => (
                <button key={c.user_id} onClick={() => openConversation(c)}
                  className={`w-full flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left ${activeUser?.user_id === c.user_id ? 'bg-primary-50 dark:bg-primary-900/20' : ''}`}>
                  <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center text-primary-600 font-bold text-sm flex-shrink-0">
                    {initials(c.display_name || c.username)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-sm truncate">{c.display_name || c.username}</span>
                      {c.unread_count > 0 && (
                        <span className="badge bg-primary-600 text-white text-xs ml-1">{c.unread_count}</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 truncate">{c.last_message || 'Start a conversation'}</p>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Chat area */}
        {activeUser ? (
          <div className="flex-1 flex flex-col min-w-0">
            <div className="p-4 border-b dark:border-gray-700 flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center text-primary-600 font-bold text-sm">
                {initials(activeUser.display_name || activeUser.username)}
              </div>
              <div>
                <div className="font-semibold">{activeUser.display_name || activeUser.username}</div>
                {typing && <div className="text-xs text-gray-400">Typing…</div>}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.map((m, i) => {
                const mine = m.sender_id === user.id;
                return (
                  <div key={m.id || i} className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl text-sm leading-relaxed ${
                      mine ? 'bg-primary-600 text-white rounded-br-sm' : 'bg-gray-100 dark:bg-gray-700 rounded-bl-sm'
                    }`}>
                      <p>{m.content}</p>
                      <p className={`text-xs mt-1 ${mine ? 'text-primary-200' : 'text-gray-400'}`}>{timeLabel(m.created_at)}</p>
                    </div>
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>

            <form onSubmit={sendMessage} className="p-4 border-t dark:border-gray-700 flex gap-2">
              <input value={newMsg} onChange={handleTyping} placeholder="Type a message…"
                className="input flex-1" autoComplete="off" />
              <button type="submit" disabled={sending || !newMsg.trim()} className="btn-primary px-5">
                {sending ? '…' : 'Send'}
              </button>
            </form>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <div className="text-5xl mb-4">💬</div>
              <p>Select a conversation or search for a member</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
