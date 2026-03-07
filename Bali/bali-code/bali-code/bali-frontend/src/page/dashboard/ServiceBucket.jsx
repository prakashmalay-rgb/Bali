import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FiActivity, FiStar, FiTrendingUp, FiSearch, FiBox, FiChevronRight } from 'react-icons/fi';

const ServiceBucket = () => {
    const [services, setServices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const baseUrl = (import.meta.env.VITE_API_URL || 'https://bali-v92r.onrender.com');

    useEffect(() => {
        fetchServices();
    }, [startDate, endDate]);

    const fetchServices = async () => {
        setLoading(true);
        try {
            const params = {};
            if (startDate) params.start_date = startDate;
            if (endDate) params.end_date = endDate;

            const response = await axios.get(`${baseUrl}/dashboard-api/buckets/services`, { params });
            if (response.data.success) {
                setServices(response.data.data);
            }
        } catch (error) {
            console.error('Error fetching services:', error);
        }
        setLoading(false);
    };

    const formatCurrency = (val) => {
        return new Intl.NumberFormat('id-ID', {
            style: 'currency',
            currency: 'IDR',
            minimumFractionDigits: 0
        }).format(val);
    };

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 bg-white/40 backdrop-blur-md p-6 rounded-3xl border border-white/20 shadow-sm">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-[#ED8612] to-orange-400 bg-clip-text text-transparent">Service Analytics</h1>
                    <p className="text-lightneutral mt-1">Discover peak demand and highest grossing service categories.</p>
                </div>

                <div className="flex items-center gap-2 bg-white/60 p-1 rounded-xl border border-gray-100">
                    <input type="date" className="bg-transparent border-none outline-none text-sm p-1.5" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
                    <span className="text-gray-300">|</span>
                    <input type="date" className="bg-transparent border-none outline-none text-sm p-1.5" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
                </div>
            </div>

            {/* Top Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {services.slice(0, 3).map((s, i) => (
                    <div key={i} className="p-6 rounded-3xl bg-white border border-gray-100 shadow-sm relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:scale-125 transition-transform">
                            <FiStar size={80} className="text-[#ED8612]" />
                        </div>
                        <p className="text-[10px] font-black uppercase text-orange-500 tracking-widest">{i === 0 ? '👑 Best Seller' : `Rank #${i + 1}`}</p>
                        <h3 className="text-xl font-bold text-neutral mt-1 truncate uppercase">{s._id}</h3>
                        <div className="mt-4 flex justify-between items-end">
                            <div>
                                <p className="text-2xl font-black text-neutral">{s.popularity}</p>
                                <p className="text-xs text-lightneutral">Total Bookings</p>
                            </div>
                            <div className="text-right">
                                <p className="text-lg font-bold text-[#ED8612]">{formatCurrency(s.revenue)}</p>
                                <p className="text-xs text-lightneutral">Revenue Generated</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Table */}
            <div className="bg-white rounded-3xl border border-gray-100 shadow-xl overflow-hidden overflow-x-auto">
                <table className="w-full text-left">
                    <thead className="bg-secondarywhite/50 text-lightneutral text-xs uppercase tracking-wider">
                        <tr>
                            <th className="p-6 font-semibold">Service Name</th>
                            <th className="p-6 font-semibold">Demand Level</th>
                            <th className="p-6 font-semibold">Avg. Booking Value</th>
                            <th className="p-6 font-semibold">Gross Revenue</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {services.map((s) => (
                            <tr key={s._id} className="hover:bg-orange-50/50 transition-colors">
                                <td className="p-6 font-bold text-neutral uppercase">{s._id}</td>
                                <td className="p-6">
                                    <div className="flex items-center gap-3">
                                        <span className="text-sm font-bold text-neutral">{s.popularity}</span>
                                        <div className="flex-1 max-w-[100px] h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                            <div className="h-full bg-orange-500" style={{ width: `${(s.popularity / services[0].popularity * 100)}%` }}></div>
                                        </div>
                                    </div>
                                </td>
                                <td className="p-6 text-darkgrey">{formatCurrency(s.avg_price)}</td>
                                <td className="p-6 font-bold text-[#ED8612]">{formatCurrency(s.revenue)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ServiceBucket;
