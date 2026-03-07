import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FiHome, FiTrendingUp, FiCheckCircle, FiSearch, FiChevronRight, FiX, FiActivity, FiDollarSign } from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';

const VillaBucket = () => {
    const [villas, setVillas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [selectedVilla, setSelectedVilla] = useState(null);
    const [history, setHistory] = useState([]);
    const [historyLoading, setHistoryLoading] = useState(false);

    const baseUrl = (import.meta.env.VITE_API_URL || 'https://bali-v92r.onrender.com');

    useEffect(() => {
        fetchVillas();
    }, [startDate, endDate]);

    const fetchVillas = async () => {
        setLoading(true);
        try {
            const params = {};
            if (startDate) params.start_date = startDate;
            if (endDate) params.end_date = endDate;

            const response = await axios.get(`${baseUrl}/dashboard-api/buckets/villas`, { params });
            if (response.data.success) {
                setVillas(response.data.data);
            }
        } catch (error) {
            console.error('Error fetching villas:', error);
        }
        setLoading(false);
    };

    const fetchHistory = async (villaCode) => {
        setHistoryLoading(true);
        setSelectedVilla(villaCode);
        try {
            const response = await axios.get(`${baseUrl}/dashboard-api/history/villa/${villaCode}`);
            if (response.data.success) {
                setHistory(response.data.history);
            }
        } catch (error) {
            console.error('Error fetching history:', error);
        }
        setHistoryLoading(false);
    };

    const filteredVillas = villas.filter(v =>
        (v._id || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    const formatCurrency = (val) => {
        return new Intl.NumberFormat('id-ID', {
            style: 'currency',
            currency: 'IDR',
            minimumFractionDigits: 0
        }).format(val);
    };

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Header + Filters */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 bg-white/40 backdrop-blur-md p-6 rounded-3xl border border-white/20 shadow-sm">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-[#0C5B22] to-green-400 bg-clip-text text-transparent">Villa Performance</h1>
                    <p className="text-lightneutral mt-1">Analyze booking conversion rates per property and zone.</p>
                </div>

                <div className="flex flex-wrap items-center gap-4">
                    <div className="relative">
                        <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-lightneutral" />
                        <input
                            type="text"
                            placeholder="Search Villa Code..."
                            className="pl-10 pr-4 py-2.5 rounded-xl border border-gray-100 focus:ring-2 focus:ring-green-500/20 outline-none transition-all w-64 bg-white/60"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-6 rounded-3xl bg-gradient-to-br from-[#0C5B22] to-green-700 text-white shadow-lg">
                    <p className="text-green-100 text-sm font-semibold uppercase tracking-wider">Top Performing Villa</p>
                    <h2 className="text-3xl font-bold mt-2">{villas[0]?._id || 'N/A'}</h2>
                    <p className="mt-4 text-green-100 text-sm">Revenue: {formatCurrency(villas[0]?.total_revenue || 0)}</p>
                </div>
                <div className="p-6 rounded-3xl bg-white border border-gray-100 shadow-sm">
                    <p className="text-lightneutral text-sm font-semibold uppercase tracking-wider">Avg. Requests / Villa</p>
                    <h2 className="text-3xl font-bold mt-2 text-neutral">
                        {villas.length ? (villas.reduce((acc, v) => acc + v.total_requests, 0) / villas.length).toFixed(1) : 0}
                    </h2>
                </div>
                <div className="p-6 rounded-3xl bg-white border border-gray-100 shadow-sm">
                    <p className="text-lightneutral text-sm font-semibold uppercase tracking-wider">Total Active Villas</p>
                    <h2 className="text-3xl font-bold mt-2 text-neutral">{villas.length}</h2>
                </div>
            </div>

            {/* Villa Table */}
            <div className="bg-white rounded-3xl border border-gray-100 shadow-xl overflow-hidden overflow-x-auto">
                <table className="w-full text-left">
                    <thead className="bg-secondarywhite/50 text-lightneutral text-xs uppercase tracking-wider">
                        <tr>
                            <th className="p-6 font-semibold">Villa Code</th>
                            <th className="p-6 font-semibold">Total Requests</th>
                            <th className="p-6 font-semibold">Paid Bookings</th>
                            <th className="p-6 font-semibold">Conversion Rate</th>
                            <th className="p-6 font-semibold">Total Revenue</th>
                            <th className="p-6 font-semibold"></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {loading ? (
                            [...Array(5)].map((_, i) => (
                                <tr key={i} className="animate-pulse">
                                    <td colSpan="6" className="p-6"><div className="h-6 bg-gray-50 rounded w-full"></div></td>
                                </tr>
                            ))
                        ) : filteredVillas.map((villa) => (
                            <tr
                                key={villa._id}
                                onClick={() => fetchHistory(villa._id)}
                                className="hover:bg-green-50 transition-colors cursor-pointer group"
                            >
                                <td className="p-6">
                                    <span className="font-bold text-neutral">{villa._id || 'UNASSIGNED'}</span>
                                </td>
                                <td className="p-6 text-darkgrey font-medium">{villa.total_requests}</td>
                                <td className="p-6">
                                    <div className="flex items-center gap-2">
                                        <FiCheckCircle className="text-green-500" />
                                        <span className="font-bold text-neutral">{villa.confirmed_requests}</span>
                                    </div>
                                </td>
                                <td className="p-6">
                                    <div className="w-full max-w-[100px] h-2 bg-gray-100 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-green-500 rounded-full"
                                            style={{ width: `${(villa.confirmed_requests / villa.total_requests * 100) || 0}%` }}
                                        ></div>
                                    </div>
                                    <span className="text-[10px] text-lightneutral font-bold mt-1 block">
                                        {((villa.confirmed_requests / villa.total_requests * 100) || 0).toFixed(1)}%
                                    </span>
                                </td>
                                <td className="p-6 font-bold text-[#0C5B22]">{formatCurrency(villa.total_revenue)}</td>
                                <td className="p-6 text-right">
                                    <FiChevronRight className="inline-block text-gray-300 group-hover:text-green-600 transition-colors" />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* History Drill-down Modal */}
            <AnimatePresence>
                {selectedVilla && (
                    <div className="fixed inset-0 z-[60] flex items-center justify-end">
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setSelectedVilla(null)} className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
                        <motion.div initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }} className="relative h-full w-full max-w-2xl bg-white shadow-2xl overflow-y-auto flex flex-col" >
                            <div className="p-8 border-b sticky top-0 bg-white z-10 flex justify-between items-center">
                                <div>
                                    <h2 className="text-2xl font-bold text-neutral">Villa Booking Log</h2>
                                    <p className="text-[#0C5B22] font-semibold">Code: {selectedVilla}</p>
                                </div>
                                <button onClick={() => setSelectedVilla(null)} className="p-2 hover:bg-gray-100 rounded-full"><FiX size={24} /></button>
                            </div>
                            <div className="p-8 space-y-4">
                                {historyLoading ? <p>Loading history...</p> : history.map(h => (
                                    <div key={h._id} className="p-5 rounded-2xl border border-gray-100 bg-gray-50 flex justify-between items-center">
                                        <div>
                                            <p className="text-xs text-lightneutral font-bold">{h.order_number}</p>
                                            <p className="font-bold text-neutral">{h.service_name}</p>
                                            <p className="text-xs text-darkgrey mt-1">{new Date(h.created_at).toLocaleString()}</p>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-bold text-neutral">{h.payment?.paid_amount ? formatCurrency(h.payment.paid_amount) : 'IDR -'}</p>
                                            <span className={`text-[10px] uppercase font-black px-2 py-0.5 rounded-full ${h.status === 'PAID' ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'}`}>
                                                {h.status}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default VillaBucket;
