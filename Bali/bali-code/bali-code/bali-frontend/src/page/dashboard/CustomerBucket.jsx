import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FiUser, FiCalendar, FiDollarSign, FiSearch, FiClock, FiChevronRight, FiX } from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';

const CustomerBucket = () => {
    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [selectedCustomer, setSelectedCustomer] = useState(null);
    const [history, setHistory] = useState([]);
    const [historyLoading, setHistoryLoading] = useState(false);

    const baseUrl = (import.meta.env.VITE_API_URL || 'https://bali-v92r.onrender.com');

    useEffect(() => {
        fetchCustomers();
    }, [startDate, endDate]);

    const fetchCustomers = async () => {
        setLoading(true);
        try {
            const params = {};
            if (startDate) params.start_date = startDate;
            if (endDate) params.end_date = endDate;

            const response = await axios.get(`${baseUrl}/dashboard-api/buckets/customers`, { params });
            if (response.data.success) {
                setCustomers(response.data.data);
            }
        } catch (error) {
            console.error('Error fetching customers:', error);
        }
        setLoading(false);
    };

    const fetchHistory = async (senderId) => {
        setHistoryLoading(true);
        setSelectedCustomer(senderId);
        try {
            const response = await axios.get(`${baseUrl}/dashboard-api/history/customer/${senderId}`);
            if (response.data.success) {
                setHistory(response.data.history);
            }
        } catch (error) {
            console.error('Error fetching history:', error);
        }
        setHistoryLoading(false);
    };

    const filteredCustomers = customers.filter(c =>
        c._id.toLowerCase().includes(searchTerm.toLowerCase())
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
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">Customer Intelligence</h1>
                    <p className="text-lightneutral mt-1">Track guest loyalty and lifetime value across all channels.</p>
                </div>

                <div className="flex flex-wrap items-center gap-4">
                    <div className="relative">
                        <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-lightneutral" />
                        <input
                            type="text"
                            placeholder="Search Guest ID..."
                            className="pl-10 pr-4 py-2.5 rounded-xl border border-gray-100 focus:ring-2 focus:ring-primary/20 outline-none transition-all w-64 bg-white/60"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <div className="flex items-center gap-2 bg-white/60 p-1 rounded-xl border border-gray-100">
                        <input
                            type="date"
                            className="bg-transparent border-none outline-none text-sm p-1.5"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                        />
                        <span className="text-gray-300">|</span>
                        <input
                            type="date"
                            className="bg-transparent border-none outline-none text-sm p-1.5"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                        />
                    </div>
                </div>
            </div>

            {/* Customer Table */}
            <div className="bg-white rounded-3xl border border-gray-100 shadow-xl overflow-hidden overflow-x-auto min-h-[500px]">
                <table className="w-full text-left">
                    <thead className="bg-secondarywhite/50 text-lightneutral text-xs uppercase tracking-wider">
                        <tr>
                            <th className="p-6 font-semibold">Guest Identifier</th>
                            <th className="p-6 font-semibold">Bookings</th>
                            <th className="p-6 font-semibold">Lifetime Spend</th>
                            <th className="p-6 font-semibold">Preferred Services</th>
                            <th className="p-6 font-semibold">Last Activity</th>
                            <th className="p-6 font-semibold"></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                        {loading ? (
                            [...Array(5)].map((_, i) => (
                                <tr key={i} className="animate-pulse">
                                    <td className="p-6"><div className="h-4 bg-gray-100 rounded w-24"></div></td>
                                    <td className="p-6"><div className="h-4 bg-gray-100 rounded w-12"></div></td>
                                    <td className="p-6"><div className="h-4 bg-gray-100 rounded w-32"></div></td>
                                    <td className="p-6"><div className="h-4 bg-gray-100 rounded w-40"></div></td>
                                    <td className="p-6"><div className="h-4 bg-gray-100 rounded w-24"></div></td>
                                    <td className="p-6"></td>
                                </tr>
                            ))
                        ) : filteredCustomers.length > 0 ? (
                            filteredCustomers.map((cust) => (
                                <tr
                                    key={cust._id}
                                    onClick={() => fetchHistory(cust._id)}
                                    className="hover:bg-primary/5 transition-colors cursor-pointer group"
                                >
                                    <td className="p-6 flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
                                            {cust._id.slice(-2)}
                                        </div>
                                        <span className="font-bold text-neutral">Guest {cust._id.slice(-6)}</span>
                                    </td>
                                    <td className="p-6">
                                        <span className="bg-blue-50 text-blue-600 px-2.5 py-1 rounded-lg text-sm font-semibold">
                                            {cust.total_bookings} requests
                                        </span>
                                    </td>
                                    <td className="p-6 font-bold text-neutral">
                                        {formatCurrency(cust.total_spent)}
                                    </td>
                                    <td className="p-6">
                                        <div className="flex flex-wrap gap-1">
                                            {cust.services.slice(0, 2).map((s, idx) => (
                                                <span key={idx} className="text-[10px] bg-gray-100 px-2 py-0.5 rounded-full text-grey uppercase font-medium">
                                                    {s}
                                                </span>
                                            ))}
                                            {cust.services.length > 2 && <span className="text-[10px] text-lightneutral">+{cust.services.length - 2} more</span>}
                                        </div>
                                    </td>
                                    <td className="p-6 text-sm text-lightneutral">
                                        {new Date(cust.last_booking).toLocaleDateString()}
                                    </td>
                                    <td className="p-6 text-right">
                                        <FiChevronRight className="inline-block text-gray-300 group-hover:text-primary transition-colors" />
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan="6" className="p-20 text-center text-lightneutral">
                                    <div className="flex flex-col items-center">
                                        <FiUser size={48} className="mb-4 opacity-20" />
                                        <p>No customers found matching your criteria.</p>
                                    </div>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* History Modal / Drawer */}
            <AnimatePresence>
                {selectedCustomer && (
                    <div className="fixed inset-0 z-[60] flex items-center justify-end">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setSelectedCustomer(null)}
                            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
                        />
                        <motion.div
                            initial={{ x: '100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '100%' }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="relative h-full w-full max-w-2xl bg-white shadow-2xl overflow-y-auto flex flex-col"
                        >
                            <div className="p-8 border-b sticky top-0 bg-white z-10 flex justify-between items-center">
                                <div>
                                    <h2 className="text-2xl font-bold text-neutral">Guest Activity History</h2>
                                    <p className="text-primary font-semibold">ID: {selectedCustomer}</p>
                                </div>
                                <button onClick={() => setSelectedCustomer(null)} className="p-2 hover:bg-gray-100 rounded-full">
                                    <FiX size={24} />
                                </button>
                            </div>

                            <div className="p-8 space-y-6">
                                {historyLoading ? (
                                    <div className="space-y-4">
                                        {[...Array(3)].map((_, i) => <div key={i} className="h-24 bg-gray-50 rounded-2xl animate-pulse"></div>)}
                                    </div>
                                ) : history.length > 0 ? (
                                    history.map((order) => (
                                        <div key={order._id} className="p-6 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:shadow-md transition-all">
                                            <div className="flex justify-between items-start mb-4">
                                                <div>
                                                    <span className="text-xs text-primary font-bold uppercase tracking-widest">{order.order_number}</span>
                                                    <h3 className="text-lg font-bold text-neutral">{order.service_name}</h3>
                                                </div>
                                                <span className={`px-3 py-1 rounded-full text-xs font-bold ${order.status === 'PAID' ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'
                                                    }`}>
                                                    {order.status}
                                                </span>
                                            </div>
                                            <div className="grid grid-cols-2 gap-4 text-sm">
                                                <div className="flex items-center gap-2 text-lightneutral">
                                                    <FiCalendar /> {order.date ? new Date(order.date).toLocaleDateString() : 'N/A'}
                                                </div>
                                                <div className="flex items-center gap-2 text-lightneutral">
                                                    <FiDollarSign /> {order.payment?.paid_amount ? formatCurrency(order.payment.paid_amount) : 'Unpaid'}
                                                </div>
                                                <div className="flex items-center gap-2 text-lightneutral">
                                                    <FiClock /> {order.time || 'N/A'}
                                                </div>
                                                <div className="text-lightneutral">
                                                    Villa: <span className="font-bold text-neutral">{order.villa_code || 'N/A'}</span>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <p className="text-center text-lightneutral py-10">No history found for this guest.</p>
                                )}
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default CustomerBucket;
