import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FiClock, FiCheck, FiInfo, FiSearch, FiFilter } from 'react-icons/fi';

const API_BASE_URL = 'https://easy-bali.onrender.com';

const GuestActivity = () => {
    const [activities, setActivities] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('all');

    useEffect(() => {
        const fetchActivity = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/dashboard-api/activity`);
                if (response.data.success) {
                    setActivities(response.data.activity);
                }
            } catch (error) {
                console.error("Failed to fetch guest activity:", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchActivity();
    }, []);

    // Helper functions for UI
    const getStatusStyles = (status) => {
        switch (status) {
            case 'completed':
                return 'bg-emerald-50 text-emerald-600 border-emerald-100';
            case 'pending':
                return 'bg-amber-50 text-amber-600 border-amber-100';
            default:
                return 'bg-blue-50 text-primary border-blue-100';
        }
    };

    const getIcon = (iconType) => {
        switch (iconType) {
            case 'payment':
                return <FiCheck className="w-4 h-4" />;
            case 'request':
                return <FiClock className="w-4 h-4" />;
            default:
                return <FiInfo className="w-4 h-4" />;
        }
    };

    // Filter Logic
    const filteredActivities = activities.filter(act => {
        const matchesSearch = act.guest_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            act.service.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = filterStatus === 'all' || act.status === filterStatus;
        return matchesSearch && matchesStatus;
    });

    return (
        <div className="space-y-6">

            {/* Header & Controls */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-[#0B97EE] bg-clip-text text-transparent">Guest Activity</h1>
                    <p className="text-sm text-lightneutral mt-1">Live tracking of all guest service requests and payments</p>
                </div>

                <div className="flex w-full md:w-auto gap-3">
                    <div className="relative flex-1 md:w-64">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-lightneutral">
                            <FiSearch />
                        </div>
                        <input
                            type="text"
                            className="block w-full pl-10 pr-4 py-2 bg-white/70 backdrop-blur-md border border-gray-100 rounded-xl text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                            placeholder="Search guests or services..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>

                    <div className="relative">
                        <select
                            className="appearance-none pl-4 pr-10 py-2 bg-white/70 backdrop-blur-md border border-gray-100 rounded-xl text-sm focus:ring-2 focus:ring-primary/20 outline-none transition-all cursor-pointer font-medium text-darkgrey"
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                        >
                            <option value="all">All Status</option>
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

            {/* Main Activity Board (Glassmorphism) */}
            <div className="bg-white/60 backdrop-blur-xl border border-white rounded-[2rem] shadow-sm overflow-hidden">
                <div className="overflow-x-auto p-2">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-gray-100/50">
                                <th className="py-4 px-6 text-xs font-semibold text-lightneutral uppercase tracking-wider">Guest info</th>
                                <th className="py-4 px-6 text-xs font-semibold text-lightneutral uppercase tracking-wider">Action</th>
                                <th className="py-4 px-6 text-xs font-semibold text-lightneutral uppercase tracking-wider">Order / Amount</th>
                                <th className="py-4 px-6 text-xs font-semibold text-lightneutral uppercase tracking-wider text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50/50">
                            {isLoading ? (
                                <tr>
                                    <td colSpan="4" className="py-20 text-center">
                                        <div className="inline-block w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
                                        <p className="text-sm font-medium text-lightneutral mt-4">Syncing live activity stream...</p>
                                    </td>
                                </tr>
                            ) : filteredActivities.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="py-20 text-center">
                                        <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-300">
                                            <FiSearch size={24} />
                                        </div>
                                        <p className="text-sm font-medium text-darkgrey">No activity found.</p>
                                        <p className="text-xs text-lightneutral mt-1">Try adjusting your filters.</p>
                                    </td>
                                </tr>
                            ) : (
                                filteredActivities.map((act) => (
                                    <tr key={act.id} className="hover:bg-white/80 transition-colors group cursor-pointer">
                                        <td className="py-4 px-6">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary/10 to-primary/5 border border-primary/10 flex items-center justify-center text-primary font-bold shadow-sm">
                                                    {act.guest_name.charAt(0)}{act.guest_name.slice(-1)}
                                                </div>
                                                <div>
                                                    <p className="text-sm font-bold text-neutral group-hover:text-primary transition-colors">{act.guest_name}</p>
                                                    <p className="text-xs text-lightneutral mt-0.5">{act.time}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="py-4 px-6">
                                            <p className="text-sm font-medium text-darkgrey">{act.action}</p>
                                            <p className="text-xs text-lightneutral mt-0.5">{act.service}</p>
                                        </td>
                                        <td className="py-4 px-6">
                                            <p className="text-sm font-medium text-neutral">{act.order_number}</p>
                                            <p className="text-xs font-bold text-darkgrey mt-0.5">
                                                IDR {act.amount.toLocaleString('id-ID')}
                                            </p>
                                        </td>
                                        <td className="py-4 px-6 text-right">
                                            <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold border ${getStatusStyles(act.status)} shadow-sm`}>
                                                {getIcon(act.icon)}
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
