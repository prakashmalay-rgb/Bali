import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FiMessageSquare, FiUser, FiSearch, FiMonitor, FiPhoneCall } from 'react-icons/fi';

const API_BASE_URL = import.meta.env.VITE_BASE_URL || 'https://bali-v92r.onrender.com';

const DashboardChats = () => {
    const [sessions, setSessions] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedSession, setSelectedSession] = useState(null);

    useEffect(() => {
        const fetchChats = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/dashboard-api/chats`);
                if (response.data.success) {
                    setSessions(response.data.sessions);
                    if (response.data.sessions.length > 0) {
                        setSelectedSession(response.data.sessions[0]);
                    }
                }
            } catch (error) {
                console.error("Failed to fetch chat logs:", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchChats();

        // Polling for live updates every 10 seconds
        const interval = setInterval(fetchChats, 10000);
        return () => clearInterval(interval);
    }, []);

    const filteredSessions = sessions.filter(s =>
        s.guest_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.guest_id.includes(searchTerm)
    );

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col space-y-4 font-sans">
            {/* Header */}
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-[#0B97EE] bg-clip-text text-transparent">Concierge Chats</h1>
                    <p className="text-sm text-lightneutral mt-1">Live oversee of all AI WhatsApp interactions</p>
                </div>

                <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-600 rounded-xl border border-emerald-100 font-medium text-sm">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    Live Sync Active
                </div>
            </div>

            {/* Chat Layout Container */}
            <div className="flex-1 flex gap-4 overflow-hidden">

                {/* Left Sidebar: Session List */}
                <div className="w-1/3 bg-white/60 backdrop-blur-xl border border-white rounded-[2rem] shadow-sm flex flex-col h-full overflow-hidden shrink-0">
                    <div className="p-4 border-b border-gray-100/50">
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-lightneutral">
                                <FiSearch />
                            </div>
                            <input
                                type="text"
                                className="block w-full pl-10 pr-4 py-2.5 bg-gray-50/50 border border-gray-100 rounded-xl text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all text-darkgrey"
                                placeholder="Search conversations..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-2 space-y-1">
                        {isLoading && sessions.length === 0 ? (
                            <div className="p-8 text-center text-lightneutral flex flex-col items-center">
                                <div className="w-6 h-6 border-2 border-primary/20 border-t-primary rounded-full animate-spin mb-3" />
                                <p className="text-sm">Connecting to AI engine...</p>
                            </div>
                        ) : filteredSessions.length === 0 ? (
                            <div className="p-8 text-center text-lightneutral">
                                <FiMessageSquare className="w-8 h-8 mx-auto mb-2 opacity-30" />
                                <p className="text-sm font-medium">No live chats found</p>
                                <p className="text-xs mt-1">Chat memory is currently empty.</p>
                            </div>
                        ) : (
                            filteredSessions.map((session) => (
                                <button
                                    key={session.guest_id}
                                    onClick={() => setSelectedSession(session)}
                                    className={`w-full text-left p-4 rounded-2xl transition-all ${selectedSession?.guest_id === session.guest_id ? 'bg-gradient-to-r from-primary/10 to-transparent border border-primary/10' : 'hover:bg-white border border-transparent'}`}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="relative">
                                            <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-500">
                                                <FiUser className="w-5 h-5" />
                                            </div>
                                            <div className="absolute bottom-0 right-0 w-3 h-3 border-2 border-white rounded-full bg-emerald-500" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex justify-between items-baseline mb-0.5">
                                                <h3 className="font-bold text-sm text-neutral truncate">{session.guest_name}</h3>
                                                <span className="text-[10px] font-medium text-lightneutral">{session.last_active}</span>
                                            </div>
                                            <p className="text-xs text-lightneutral truncate">
                                                {session.message_count} messages in history
                                            </p>
                                        </div>
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                </div>

                {/* Right Area: Chat Transcript */}
                <div className="flex-1 bg-white/60 backdrop-blur-xl border border-white rounded-[2rem] shadow-sm flex flex-col h-full overflow-hidden relative">
                    {selectedSession ? (
                        <>
                            {/* Selected Chat Header */}
                            <div className="p-5 border-b border-gray-100/50 flex justify-between items-center bg-white/50">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
                                        <FiUser className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h2 className="font-bold text-neutral">{selectedSession.guest_name}</h2>
                                        <p className="text-xs text-emerald-600 font-medium">Active WhatsApp Session</p>
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <button className="flex items-center gap-2 px-4 py-2 bg-gray-50 hover:bg-gray-100 text-darkgrey rounded-xl border border-gray-100 text-sm font-semibold transition-colors">
                                        <FiMonitor /> Intervene
                                    </button>
                                </div>
                            </div>

                            {/* Transcript Area */}
                            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gradient-to-b from-transparent to-gray-50/30">
                                {selectedSession.transcript.map((msg, index) => {
                                    const isAI = msg.role === 'assistant';
                                    return (
                                        <div key={index} className={`flex ${isAI ? 'justify-start' : 'justify-end'}`}>
                                            <div className={`max-w-[70%] rounded-2xl p-4 shadow-sm ${isAI
                                                    ? 'bg-white border border-gray-100 text-darkgrey rounded-tl-sm'
                                                    : 'bg-primary text-white rounded-tr-sm'
                                                }`}>
                                                <div className="flex items-center gap-2 mb-1.5 opacity-80">
                                                    {isAI ? (
                                                        <span className="text-[10px] uppercase tracking-wider font-bold text-lightneutral">EASY Bali AI</span>
                                                    ) : (
                                                        <span className="text-[10px] uppercase tracking-wider font-bold text-white/80">Guest</span>
                                                    )}
                                                </div>
                                                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                                                    {msg.content}
                                                </p>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-lightneutral p-8 text-center bg-gray-50/20">
                            <div className="w-20 h-20 bg-white shadow-sm rounded-full flex items-center justify-center mb-4">
                                <FiMessageSquare className="w-8 h-8 text-gray-300" />
                            </div>
                            <h3 className="text-lg font-bold text-darkgrey">No Conversation Selected</h3>
                            <p className="text-sm mt-1 max-w-sm">Select a guest from the sidebar to view their live conversation transcript with the EASY Bali AI Concierge.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default DashboardChats;
