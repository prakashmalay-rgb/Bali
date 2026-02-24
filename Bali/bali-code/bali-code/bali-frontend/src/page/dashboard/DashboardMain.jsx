import React, { useState, useEffect } from 'react';
import { FiTrendingUp, FiUsers, FiDollarSign, FiActivity } from 'react-icons/fi';
import axios from 'axios';

const DashboardMain = () => {
    const [stats, setStats] = useState({
        activeGuests: 0,
        totalBookings: 0,
        revenue: 0,
        pendingInquiries: 0
    });

    const [recentActivity, setRecentActivity] = useState([]);

    useEffect(() => {
        const fetchDashboardStats = async () => {
            try {
                const baseUrl = 'https://bali-v92r.onrender.com';
                const response = await axios.get(`${baseUrl}/dashboard-api/stats`);
                const { stats, recentActivity } = response.data;

                if (stats) setStats(stats);
                if (recentActivity) setRecentActivity(recentActivity);
            } catch (error) {
                console.error('Failed to fetch dashboard stats:', error);
                // Fallback for visual demonstration if backend breaks
                setStats({
                    activeGuests: 12,
                    totalBookings: 48,
                    revenue: 14500000,
                    pendingInquiries: 3
                });
                setRecentActivity([
                    { id: 1, guest: 'System', action: 'Could not connect to database', time: 'Just now', status: 'error' }
                ]);
            }
        };

        fetchDashboardStats();
    }, []);

    const formatIDR = (num) => {
        return new Intl.NumberFormat('id-ID', {
            style: 'currency',
            currency: 'IDR',
            minimumFractionDigits: 0
        }).format(num);
    };

    const StatCard = ({ icon, title, value, trend, colorClass }) => (
        <div className={`p-6 rounded-3xl bg-white border border-gray-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-all duration-300 transform hover:-translate-y-1`}>
            <div className="flex items-center justify-between">
                <div className={`p-4 rounded-2xl ${colorClass}`}>
                    {icon}
                </div>
                <div className="flex items-center gap-1 text-sm font-semibold text-green-500 bg-green-50 px-2.5 py-1 rounded-full">
                    <FiTrendingUp />
                    {trend}
                </div>
            </div>
            <div className="mt-6">
                <h3 className="text-lightneutral text-sm font-semibold uppercase tracking-wider">{title}</h3>
                <p className="text-3xl font-bold text-neutral mt-1">{value}</p>
            </div>
        </div>
    );

    return (
        <div className="space-y-8 fade-in">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-neutral tracking-tight">Welcome back, Admin 👋</h1>
                    <p className="text-lightneutral mt-1">Here is what is happening across your villas today.</p>
                </div>
                <button className="bg-primary hover:bg-[#0B97EE] text-white px-6 py-2.5 rounded-xl font-semibold shadow-blue-shadow transition-all transform hover:scale-[1.02]">
                    Download Report
                </button>
            </div>

            {/* Primary Metric Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    icon={<FiUsers size={24} className="text-primary" />}
                    title="Active Guests"
                    value={stats.activeGuests}
                    trend="+12%"
                    colorClass="bg-primary/10"
                />
                <StatCard
                    icon={<FiActivity size={24} className="text-[#0C5B22]" />}
                    title="Service Bookings"
                    value={stats.totalBookings}
                    trend="+5%"
                    colorClass="bg-[#0C5B22]/10"
                />
                <StatCard
                    icon={<FiDollarSign size={24} className="text-[#B710F6]" />}
                    title="Villa Revenue"
                    value={formatIDR(stats.revenue)}
                    trend="+18%"
                    colorClass="bg-[#B710F6]/10"
                />
                <StatCard
                    icon={<FiMessageSquare size={24} className="text-[#ED8612]" />}
                    title="Pending Chats"
                    value={stats.pendingInquiries}
                    trend="-2%"
                    colorClass="bg-[#ED8612]/10"
                />
            </div>

            {/* Recent Activity Table Container */}
            <div className="bg-white rounded-3xl border border-gray-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                    <h2 className="text-lg font-bold text-neutral">Live Guest Activity</h2>
                    <button className="text-primary text-sm font-semibold hover:underline">View All</button>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-secondarywhite/50 text-lightneutral text-xs uppercase tracking-wider">
                                <th className="p-5 font-semibold">Guest</th>
                                <th className="p-5 font-semibold">Action</th>
                                <th className="p-5 font-semibold">Time</th>
                                <th className="p-5 font-semibold">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {recentActivity.map((activity) => (
                                <tr key={activity.id} className="hover:bg-light transition-colors group">
                                    <td className="p-5 font-medium text-neutral flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-gray-200 to-gray-300"></div>
                                        {activity.guest}
                                    </td>
                                    <td className="p-5 text-darkgrey">{activity.action}</td>
                                    <td className="p-5 text-lightneutral whitespace-nowrap">{activity.time}</td>
                                    <td className="p-5 capitalize">
                                        <span className={`px-3 py-1 rounded-full text-xs font-semibold
                      ${activity.status === 'confirmed' ? 'bg-green-100 text-[#0C5B22]' :
                                                activity.status === 'pending' ? 'bg-orange-100 text-[#ED8612]' :
                                                    'bg-blue-100 text-primary'}`}
                                        >
                                            {activity.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default DashboardMain;
