import React, { useState, useEffect } from 'react';
import { FiTrendingUp, FiUsers, FiDollarSign, FiActivity, FiMessageSquare, FiArrowRight } from 'react-icons/fi';
import { API_BASE_URL, apiRequest, getUserFriendlyError } from '../../api/apiClient';
import axios from 'axios';
import { Link } from 'react-router-dom';

const DashboardMain = () => {
    const [stats, setStats] = useState({
        activeGuests: 0,
        totalBookings: 0,
        revenue: 0,
        pendingInquiries: 0,
        reportedIssues: 0
    });

    const [recentActivity, setRecentActivity] = useState([]);
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('easybali_token');
        if (token) {
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                setUser({
                    email: payload.email,
                    role: payload.role || 'staff',
                    villa_code: payload.villa_code
                });
            } catch (err) {
                console.error("Token parse error");
            }
        }

        const fetchDashboardData = async () => {
            try {
                const response = await apiRequest(() => axios.get(`${API_BASE_URL}/dashboard-api/stats`));
                if (response.data.success) {
                    setStats(response.data.stats);
                    setRecentActivity(response.data.recentActivity);
                }
            } catch (error) {
                console.error('Stats fetch failed');
            } finally {
                setIsLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    const formatIDR = (num) => {
        return new Intl.NumberFormat('id-ID', {
            style: 'currency',
            currency: 'IDR',
            minimumFractionDigits: 0
        }).format(num);
    };

    const StatCard = ({ icon, title, value, colorClass }) => (
        <div className="p-6 rounded-[2rem] bg-white/70 backdrop-blur-md border border-white shadow-sm hover:shadow-md transition-all group overflow-hidden relative">
            <div className={`absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 rounded-full opacity-10 ${colorClass}`} />
            <div className="flex items-center justify-between mb-4">
                <div className={`p-3.5 rounded-2xl ${colorClass}`}>
                    {icon}
                </div>
            </div>
            <div>
                <h3 className="text-lightneutral text-[10px] font-black uppercase tracking-[0.2em]">{title}</h3>
                <p className="text-2xl font-black text-neutral mt-1 group-hover:scale-105 transition-transform origin-left">{value}</p>
            </div>
        </div>
    );

    return (
        <div className="space-y-8">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-black text-neutral tracking-tight uppercase">
                        Dashboard <span className="text-primary">Overview</span>
                    </h1>
                    <p className="text-sm font-medium text-lightneutral mt-1 tracking-tight">
                        Logged in as <span className="text-darkgrey font-bold">{user?.email || 'Administrator'}</span>
                        {user?.villa_code && user.villa_code !== '*' && ` • Villa: ${user.villa_code}`}
                    </p>
                </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    icon={<FiUsers size={20} className="text-primary" />}
                    title="Active Guests"
                    value={stats.activeGuests}
                    colorClass="bg-primary/20"
                />
                <StatCard
                    icon={<FiActivity size={20} className="text-emerald-500" />}
                    title="Villa Bookings"
                    value={stats.totalBookings}
                    colorClass="bg-emerald-500/20"
                />
                <StatCard
                    icon={<FiDollarSign size={20} className="text-violet-500" />}
                    title="Gross Revenue"
                    value={formatIDR(stats.revenue)}
                    colorClass="bg-violet-500/20"
                />
                <StatCard
                    icon={<FiMessageSquare size={20} className="text-orange-500" />}
                    title="Open Requests"
                    value={stats.pendingInquiries}
                    colorClass="bg-orange-500/20"
                />
            </div>

            {/* Quick Activity View */}
            <div className="bg-white/60 backdrop-blur-xl border border-white rounded-[2.5rem] shadow-sm overflow-hidden mt-8">
                <div className="p-6 border-b border-gray-100/30 flex justify-between items-center">
                    <div>
                        <h2 className="text-lg font-black text-neutral uppercase tracking-tight">Recent Interactions</h2>
                        <p className="text-[10px] font-bold text-lightneutral mt-0.5 uppercase tracking-widest">Real-time guest events</p>
                    </div>
                    <Link to="/dashboard/guests" className="text-xs font-black text-primary hover:underline flex items-center gap-1 group">
                        VIEW FULL TIMELINE <FiArrowRight className="group-hover:translate-x-1 transition-transform" />
                    </Link>
                </div>
                <div className="overflow-x-auto p-2">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="text-[10px] font-black text-lightneutral uppercase tracking-[0.2em] border-b border-gray-100/20">
                                <th className="px-6 py-4">Guest</th>
                                <th className="px-6 py-4">Interaction</th>
                                <th className="px-6 py-4">Time</th>
                                <th className="px-6 py-4 text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50/50">
                            {isLoading ? (
                                <tr>
                                    <td colSpan="4" className="py-12 text-center text-sm font-bold text-lightneutral italic">Syncing metrics...</td>
                                </tr>
                            ) : recentActivity.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="py-12 text-center text-sm font-bold text-lightneutral italic">No recent activity detected.</td>
                                </tr>
                            ) : (
                                recentActivity.map((act) => (
                                    <tr key={act.id} className="hover:bg-white/80 transition-all group border-l-4 border-l-transparent hover:border-l-primary">
                                        <td className="px-6 py-4 font-black text-darkgrey text-sm">
                                            {act.guest}
                                        </td>
                                        <td className="px-6 py-4 text-sm font-semibold text-neutral">
                                            {act.action}
                                        </td>
                                        <td className="px-6 py-4 text-xs font-bold text-lightneutral uppercase">
                                            {act.time}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase border
                                                ${act.status === 'confirmed' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' :
                                                    act.status === 'pending' ? 'bg-orange-50 text-orange-600 border-orange-100' :
                                                        'bg-blue-50 text-primary border-blue-100'}`}
                                            >
                                                {act.status}
                                            </span>
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

export default DashboardMain;
