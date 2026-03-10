import { useState, useEffect } from 'react';
import { FiStar, FiSearch, FiUser, FiHome, FiMessageSquare } from 'react-icons/fi';
import { API_BASE_URL, apiRequest } from '../../api/apiClient';
import axios from 'axios';

const FeedbackView = () => {
    const [feedback, setFeedback] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchFeedback();
    }, []);

    const fetchFeedback = async () => {
        setIsLoading(true);
        try {
            const response = await apiRequest(() => axios.get(`${API_BASE_URL}/dashboard-api/feedback`));
            if (response.data.success) {
                setFeedback(response.data.feedback);
            }
        } catch (error) {
            console.error('Failed to fetch feedback');
        } finally {
            setIsLoading(false);
        }
    };

    const filteredFeedback = feedback.filter(f =>
        f.guest_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        f.villa_code?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const avgRating = feedback.length > 0
        ? (feedback.reduce((sum, f) => sum + (f.rating || 0), 0) / feedback.length).toFixed(1)
        : null;
    const positive = feedback.filter(f => f.rating >= 4).length;
    const critical = feedback.filter(f => f.rating < 4).length;

    const renderStars = (rating) => {
        return (
            <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map(star => (
                    <FiStar
                        key={star}
                        className={`${star <= rating ? 'text-amber-400 fill-amber-400' : 'text-gray-200'}`}
                        size={16}
                    />
                ))}
            </div>
        );
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-black text-neutral uppercase tracking-tight">Guest <span className="text-amber-500">Feedback</span></h1>
                    <p className="text-sm font-medium text-lightneutral mt-1">Review management and satisfaction tracking.</p>
                </div>
            </div>

            {feedback.length > 0 && (
                <div className="grid grid-cols-3 gap-4">
                    <div className="bg-white/70 backdrop-blur-xl border border-white rounded-[2rem] p-5 text-center shadow-sm">
                        <p className="text-3xl font-black text-amber-500">{avgRating}</p>
                        <p className="text-[10px] font-black uppercase text-lightneutral tracking-widest mt-1">Avg Rating</p>
                    </div>
                    <div className="bg-white/70 backdrop-blur-xl border border-white rounded-[2rem] p-5 text-center shadow-sm">
                        <p className="text-3xl font-black text-emerald-500">{positive}</p>
                        <p className="text-[10px] font-black uppercase text-lightneutral tracking-widest mt-1">Positive</p>
                    </div>
                    <div className="bg-white/70 backdrop-blur-xl border border-white rounded-[2rem] p-5 text-center shadow-sm">
                        <p className="text-3xl font-black text-rose-500">{critical}</p>
                        <p className="text-[10px] font-black uppercase text-lightneutral tracking-widest mt-1">Critical</p>
                    </div>
                </div>
            )}

            <div className="flex flex-col md:flex-row gap-4 bg-white/60 backdrop-blur-md p-4 rounded-[2rem] border border-white shadow-sm">
                <div className="flex-1 relative group">
                    <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-lightneutral group-focus-within:text-amber-500 transition-colors" />
                    <input
                        type="text"
                        placeholder="Search by Guest or Villa..."
                        className="w-full pl-12 pr-4 py-3 bg-white border border-gray-100 rounded-2xl focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all text-sm font-medium"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {isLoading ? (
                    <div className="col-span-full py-20 text-center font-bold text-lightneutral italic uppercase tracking-widest text-sm">Analyzing guest sentiment...</div>
                ) : filteredFeedback.length === 0 ? (
                    <div className="col-span-full py-20 text-center font-bold text-lightneutral italic uppercase tracking-widest text-sm">No feedback recorded yet.</div>
                ) : (
                    filteredFeedback.map((item) => (
                        <div key={item.id} className="bg-white/70 backdrop-blur-xl border border-white rounded-[2.5rem] p-6 shadow-sm hover:shadow-md transition-all group flex flex-col justify-between">
                            <div>
                                <div className="flex justify-between items-start mb-4">
                                    {renderStars(item.rating)}
                                    <span className={`px-2 py-0.5 rounded-full text-[8px] font-black uppercase border ${item.rating >= 4 ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-rose-50 text-rose-600 border-rose-100'}`}>
                                        {item.rating >= 4 ? 'POSITIVE' : 'CRITICAL'}
                                    </span>
                                </div>

                                <div className="space-y-3 mt-4">
                                    <div className="flex items-center gap-2 text-[10px] font-black uppercase text-lightneutral">
                                        <FiHome size={12} className="text-secondary" />
                                        <span>Villa: {item.villa_code}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-[10px] font-black uppercase text-lightneutral">
                                        <FiUser size={12} className="text-secondary" />
                                        <span>Guest: ...{item.guest_id ? item.guest_id.slice(-4) : 'Unknown'}</span>
                                    </div>
                                    {item.comment && (
                                        <div className="mt-3 p-3 bg-gray-50 rounded-xl border border-gray-100">
                                            <p className="text-[10px] font-black uppercase text-lightneutral mb-1">Guest Comment</p>
                                            <p className="text-xs text-neutral italic">"{item.comment}"</p>
                                        </div>
                                    )}
                                    <div className="flex items-center gap-2 text-[10px] font-black uppercase text-lightneutral">
                                        <FiMessageSquare size={12} className="text-secondary" />
                                        <span>{item.rating >= 4 ? 'Review prompt sent' : 'Manager notified'}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="mt-6 pt-4 border-t border-gray-50 flex items-center justify-between">
                                <span className="text-[10px] font-black text-lightneutral italic">{item.time}</span>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default FeedbackView;
