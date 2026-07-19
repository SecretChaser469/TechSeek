'use client';

import { useState, useEffect, useRef } from 'react';
import { apiRequest } from '../../api';
import { Bot, Send, User, MessageCircle, MoreVertical } from 'lucide-react';

export default function MessagesPage() {
    const [chats, setChats] = useState<any[]>([]);
    const [selectedChat, setSelectedChat] = useState<any>(null);
    const [messages, setMessages] = useState<any[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const [currentUser, setCurrentUser] = useState<any>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        async function fetchInitial() {
            try {
                const u = await apiRequest('/api/users/me');
                setCurrentUser(u);
                const fetchedChats = await apiRequest('/api/chats');
                setChats(fetchedChats);
            } catch (error) {
                console.error("Failed to load chats:", error);
            } finally {
                setLoading(false);
            }
        }
        fetchInitial();
    }, []);

    useEffect(() => {
        if (selectedChat) {
            fetchMessages();
        }
    }, [selectedChat]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const fetchMessages = async () => {
        if (!selectedChat) return;
        try {
            const msgs = await apiRequest(`/api/chats/${selectedChat.id}/messages`);
            setMessages(msgs);
        } catch (error) {
            console.error("Failed to fetch messages:", error);
        }
    };

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newMessage.trim() || !selectedChat) return;
        try {
            const sent = await apiRequest(`/api/chats/${selectedChat.id}/messages`, 'POST', { content: newMessage });
            setMessages([...messages, sent]);
            setNewMessage('');

            // Re-fetch in case of bot reply (simulated delay a bit for realism)
            if (selectedChat.is_bot_chat) {
                setTimeout(fetchMessages, 1500);
            }
        } catch (error) {
            console.error("Failed to send message:", error);
        }
    };

    const handleCreateBotChat = async () => {
        try {
            const newChat = await apiRequest('/api/chats', 'POST', { is_bot_chat: true, participant_ids: [] });
            setChats([...chats, newChat]);
            setSelectedChat(newChat);
        } catch (error) {
            console.error("Failed to start bot chat", error);
        }
    };

    if (loading) {
        return <div className="space-y-6 animate-pulse p-4">Loading messages...</div>;
    }

    return (
        <div className="flex bg-black/40 border border-white/5 rounded-xl overflow-hidden shadow-2xl h-[calc(100vh-140px)]">
            {/* Sidebar */}
            <div className="w-1/3 bg-black/20 border-r border-white/5 flex flex-col">
                <div className="p-4 border-b border-white/5 flex justify-between items-center">
                    <h2 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
                        <MessageCircle className="w-5 h-5 text-indigo-400" />
                        <span>Conversations</span>
                    </h2>
                </div>
                <div className="p-3 border-b border-white/5">
                    <button
                        onClick={handleCreateBotChat}
                        className="w-full flex items-center justify-center space-x-2 py-2 px-4 rounded-lg bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600/30 transition-all font-semibold shadow-sm border border-indigo-500/20"
                    >
                        <Bot className="w-4 h-4" />
                        <span>New Assistant Chat</span>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto overflow-x-hidden p-2 space-y-1 scrollbar-thin scrollbar-thumb-white/10">
                    {chats.map(chat => (
                        <div
                            key={chat.id}
                            onClick={() => setSelectedChat(chat)}
                            className={`p-3 cursor-pointer rounded-lg flex items-center space-x-3 transition-colors ${selectedChat?.id === chat.id ? 'bg-indigo-900/30 border border-indigo-500/30' : 'hover:bg-white/5 border border-transparent'}`}
                        >
                            <div className="w-10 h-10 rounded-full flex-shrink-0 flex items-center justify-center bg-black/30 border border-white/10">
                                {chat.is_bot_chat ? <Bot className="w-5 h-5 text-indigo-400" /> : <User className="w-5 h-5 text-gray-400" />}
                            </div>
                            <div className="flex-1 min-w-0">
                                <h3 className="text-sm font-semibold text-white truncate">
                                    {chat.is_bot_chat ? 'TechSeek AI Assistant' : `Chat #${chat.id}`}
                                </h3>
                                <p className="text-xs text-gray-400 truncate">
                                    Started: {new Date(chat.created_at).toLocaleDateString()}
                                </p>
                            </div>
                        </div>
                    ))}
                    {chats.length === 0 && (
                        <div className="px-4 py-8 text-center text-xs text-slate-500 flex flex-col items-center">
                            <MessageCircle className="w-8 h-8 mb-2 opacity-20" />
                            <p>No conversations yet.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 flex flex-col relative bg-transparent">
                {selectedChat ? (
                    <>
                        <div className="h-16 border-b border-white/5 px-6 flex items-center justify-between bg-black/20 z-10 shadow-sm">
                            <div className="flex items-center space-x-3">
                                <div className="w-9 h-9 rounded-full flex items-center justify-center bg-indigo-500/10 border border-indigo-500/20">
                                    {selectedChat.is_bot_chat ? <Bot className="w-4 h-4 text-indigo-400" /> : <User className="w-4 h-4 text-white" />}
                                </div>
                                <h2 className="font-bold text-white text-lg tracking-tight shadow-black/50">
                                    {selectedChat.is_bot_chat ? 'TechSeek AI Assistant' : `Conversation #${selectedChat.id}`}
                                </h2>
                            </div>
                            <MoreVertical className="w-5 h-5 text-gray-400 cursor-pointer hover:text-white" />
                        </div>

                        <div className="flex-1 overflow-y-auto p-6 space-y-4 pt-8 bg-[url('https://transparenttextures.com/patterns/micro-carbon.png')]">
                            {messages.map((msg, idx) => {
                                const isMine = msg.sender_id === currentUser?.id;
                                const isBot = !msg.sender_id;
                                return (
                                    <div key={idx} className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}>
                                        <div className={`max-w-[70%] p-4 rounded-xl shadow-lg border relative ${isMine
                                                ? 'bg-indigo-600 border-indigo-500 text-white rounded-tr-sm'
                                                : isBot
                                                    ? 'bg-[#1e2338] border-[#2c324a] text-gray-200 rounded-tl-sm'
                                                    : 'bg-[#2a2d3d] border-[#3f4356] text-gray-100 rounded-tl-sm'
                                            }`}>
                                            <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                                            <span className="text-[10px] opacity-50 mt-1 block w-full text-right">
                                                {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                        </div>
                                    </div>
                                );
                            })}

                            {messages.length === 0 && (
                                <div className="absolute inset-0 flex flex-col items-center justify-center opacity-50 pointer-events-none">
                                    <MessageCircle className="w-16 h-16 text-indigo-500 mb-4" />
                                    <p className="text-gray-300 font-medium">Say hello to start the conversation</p>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        <div className="p-4 bg-black/40 border-t border-white/5 backdrop-blur-md">
                            <form onSubmit={handleSendMessage} className="flex space-x-2">
                                <input
                                    type="text"
                                    value={newMessage}
                                    onChange={(e) => setNewMessage(e.target.value)}
                                    placeholder={selectedChat.is_bot_chat ? "Ask me anything..." : "Send a message..."}
                                    className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all font-medium text-sm"
                                />
                                <button
                                    type="submit"
                                    disabled={!newMessage.trim()}
                                    className="px-5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-900/50 disabled:text-gray-500 text-white rounded-lg transition-all flex items-center justify-center flex-shrink-0 shadow-lg"
                                >
                                    <Send className="w-5 h-5" />
                                </button>
                            </form>
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-center p-8 bg-[url('https://transparenttextures.com/patterns/black-mamba.png')]">
                        <div className="w-20 h-20 bg-indigo-500/10 rounded-full flex items-center justify-center mb-6 shadow-xl border border-indigo-500/20">
                            <Bot className="w-10 h-10 text-indigo-400" />
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-2 tracking-tight block drop-shadow-lg">Select or Start a Chat</h3>
                        <p className="text-sm text-gray-400 max-w-sm leading-relaxed">
                            Connect with mentors, team members, or chat with the AI assistant for portfolio summaries and help.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
