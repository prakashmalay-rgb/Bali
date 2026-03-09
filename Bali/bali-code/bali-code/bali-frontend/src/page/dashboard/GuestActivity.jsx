import React, { useState, useEffect } from 'react';
import { API_BASE_URL, apiRequest, getUserFriendlyError } from '../../api/apiClient';
import axios from 'axios';
import { FiClock, FiCheck, FiInfo, FiSearch, FiFilter, FiUser, FiMessageSquare, FiAlertCircle } from 'react-icons/fi';

const GuestActivity = () => {
    const [activities, setActivities] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('all');
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchActivity = async () => {
            try {
                const response = await apiRequest(() => axios.get(`${API_BASE_URL}/dashboard-api/activity`));
                if (response.data.success) {
                    setActivities(response.data.activity);
                }
            } catch (err) {
                console.error("Failed to fetch guest activity:", err);
                setError(getUserFriendlyError(err));
            } finally {
                setIsLoading(false);
            }
        };

        fetchActivity();
    }, []);

    // Helper functions for UI
    const getStatusStyles = (status, type) => {
        if (type === 'issue' && status === 'pending') return 'bg-rose-50 text-rose-600 border-rose-100';

        switch (status) {
            case 'completed':
                return 'bg-emerald-50 text-emerald-600 border-emerald-100';
            case 'pending':
                return 'bg-amber-50 text-amber-600 border-amber-100';
            default:
                return 'bg-blue-50 text-primary border-blue-100';
        }
    };

    const getIcon = (type, status) => {
        switch (type) {
            case 'order':
                return status === 'completed' ? <FiCheck className="w-4 h-4" /> : <FiClock className="w-4 h-4" />;
            case 'inquiry':
                return <FiMessageSquare className="w-4 h-4" />;
            case 'issue':
                return <FiAlertCircle className="w-4 h-4" />;
            default:
                return <FiInfo className="w-4 h-4" />;
        }
    };

    // Filter Logic
    const filteredActivities = activities.filter(act => {
        const matchesSearch =
            act.guest_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            act.service.toLowerCase().includes(searchTerm.toLowerCase()) ||
            act.action.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = filterStatus === 'all' || act.status === filterStatus;
        return matchesSearch && matchesStatus;
    });

    return (
        <div className="space-y-6">

            {/* Header & Controls */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-[#0B97EE] bg-clip-text text-transparent uppercase tracking-tight">Guest Activity</h1>
                    <p className="text-sm text-lightneutral mt-1 font-medium">Unified timeline of bookings, inquiries, and maintenance issues</p>
                </div>

                <div className="flex w-full md:w-auto gap-3">
                    <div className="relative flex-1 md:w-64">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-lightneutral">
                            <FiSearch />
                        </div>
                        <input
                            type="text"
                            className="block w-full pl-10 pr-4 py-2 bg-white/70 backdrop-blur-md border border-gray-100 rounded-xl text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                            placeholder="Search guests or events..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>

                    <div className="relative">
                        <select
                            className="appearance-none pl-4 pr-10 py-2 bg-white/70 backdrop-blur-md border border-gray-100 rounded-xl text-sm focus:ring-2 focus:ring-primary/20 outline-none transition-all cursor-pointer font-bold text-darkgrey"
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                        >
                            <option value="all">All Events</option>
                            <option value="pending">Pending</option>
                            <option value="completed">Completed</option>
                            <option value="resolved">Updates</option>
                        </select>
                        <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-lightneutral">
                            <FiFilter className="w-4 h-4" />
                        </div>
                    </div>
                </div>
            </div>

            {error && (
                <div className="p-4 bg-rose-50 border border-rose-100 rounded-2xl text-rose-600 text-sm font-medium flex items-center gap-3">
                    <FiAlertCircle />
                    {error}
                </div>
            )}

            {/* Main Activity Board (Glassmorphism) */}
            <div className="bg-white/60 backdrop-blur-xl border border-white rounded-[2rem] shadow-sm overflow-hidden">
                <div className="overflow-x-auto p-2">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-gray-100/30">
                                <th className="py-4 px-6 text-[10px] font-bold text-lightneutral uppercase tracking-[0.2em]">Guest info</th>
                                <th className="py-4 px-6 text-[10px] font-bold text-lightneutral uppercase tracking-[0.2em]">Action / Event</th>
                                <th className="py-4 px-6 text-[10px] font-bold text-lightneutral uppercase tracking-[0.2em]">Details</th>
                                <th className="py-4 px-6 text-[10px] font-bold text-lightneutral uppercase tracking-[0.2em] text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50/50">
                            {isLoading ? (
                                <tr>
                                    <td colSpan="4" className="py-20 text-center">
                                        <div className="inline-block w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
                                        <p className="text-sm font-bold text-lightneutral mt-4 italic tracking-wide">Syncing real-time guest interactions...</p>
                                    </td>
                                </tr>
                            ) : filteredActivities.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="py-20 text-center">
                                        <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-300">
                                            <FiSearch size={24} />
                                        </div>
                                        <p className="text-sm font-bold text-darkgrey">No activity matches your filters.</p>
                                        <p className="text-xs text-lightneutral mt-1">Try broadening your search.</p>
                                    </td>
                                </tr>
                            ) : (
                                filteredActivities.map((act) => (
                                    <tr key={act.id} className="hover:bg-white/80 transition-all group cursor-pointer border-l-4 border-l-transparent hover:border-l-primary">
                                        <td className="py-4 px-6">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary/10 to-primary/5 border border-primary/10 flex items-center justify-center text-primary font-black shadow-sm group-hover:scale-110 transition-transform">
                                                    {act.guest_name.charAt(act.guest_name.length - 1)}
                                                </div>
                                                <div>
                                                    <p className="text-sm font-black text-neutral group-hover:text-primary transition-colors tracking-tight">{act.guest_name}</p>
                                                    <p className="text-[10px] font-bold text-lightneutral mt-0.5 opacity-70 uppercase">{act.time}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="py-4 px-6">
                                            <div className="flex items-center gap-2">
                                                <span className={`p-1.5 rounded-lg ${act.type === 'issue' ? 'bg-rose-100 text-rose-500' : 'bg-blue-100 text-blue-500'}`}>
                                                    {getIcon(act.type, act.status)}
                                                </span>
                                                <p className="text-sm font-bold text-darkgrey">{act.action}</p>
                                            </div>
                                        </td>
                                        <td className="py-4 px-6">
                                            <p className="text-xs font-semibold text-neutral line-clamp-1">{act.service}</p>
                                            {act.amount > 0 && (
                                                <p className="text-xs font-black text-emerald-500 mt-1">
                                                    IDR {act.amount.toLocaleString('id-ID')}
                                                </p>
                                            )}
                                        </td>
                                        <td className="py-4 px-6 text-right">
                                            <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-black uppercase border ${getStatusStyles(act.status, act.type)} shadow-sm`}>
                                                <span className="capitalize">{act.status}</span>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
    );
};

export default GuestActivity;
