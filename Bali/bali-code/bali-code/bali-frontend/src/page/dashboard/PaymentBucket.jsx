import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FiDollarSign, FiPieChart, FiArrowRight } from 'react-icons/fi';
import { motion } from 'framer-motion';
import { API_BASE_URL, apiRequest } from '../../api/apiClient';

const PaymentBucket = () => {
    const [payments, setPayments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [fetchError, setFetchError] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    useEffect(() => {
        fetchPayments();
    }, [startDate, endDate]);

    const fetchPayments = async () => {
        setLoading(true);
        setFetchError('');
        try {
            const params = {};
            if (startDate) params.start_date = startDate;
            if (endDate) params.end_date = endDate;

            const response = await apiRequest(() => axios.get(`${API_BASE_URL}/dashboard-api/buckets/payments`, { params }));
            if (response.data.success) {
                setPayments(response.data.data);
            } else {
                setFetchError(response.data.error || 'Failed to load payments.');
            }
        } catch (error) {
            console.error('Error fetching payments:', error);
            setFetchError('Could not reach server. Please try again.');
        }
        setLoading(false);
    };

    const formatCurrency = (val) => {
        return new Intl.NumberFormat('id-ID', {
            style: 'currency',
            currency: 'IDR',
            minimumFractionDigits: 0
        }).format(val || 0);
    };

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 bg-white/40 backdrop-blur-md p-6 rounded-3xl border border-white/20 shadow-sm">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-[#B710F6] to-purple-400 bg-clip-text text-transparent">Financial Audits</h1>
                    <p className="text-lightneutral mt-1">Real-time split payment distributions and revenue logs.</p>
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

            {/* Split Breakdown Explained Card */}
            <div className="bg-gradient-to-r from-purple-50 to-white p-6 rounded-3xl border border-purple-100 flex items-center gap-6">
                <div className="p-4 bg-purple-100 rounded-2xl text-purple-600">
                    <FiPieChart size={32} />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-neutral">Xendit Split Distribution Architecture</h3>
                    <p className="text-sm text-lightneutral">
                        Payments are automatically split at source: **ServiceProvider Share**, **Villa Commission**, and **Easy-Bali Profit**.
                    </p>
                </div>
            </div>

            {/* Error state */}
            {fetchError && (
                <div className="p-4 bg-rose-50 border border-rose-100 rounded-2xl text-rose-600 text-sm font-bold">
                    {fetchError}
                </div>
            )}

            {/* Payments List */}
            <div className="grid grid-cols-1 gap-6">
                {loading ? (
                    [0, 1, 2].map((i) => <div key={i} className="h-32 bg-gray-50 rounded-3xl animate-pulse" />)
                ) : payments.length > 0 ? (
                    payments.map((p, idx) => (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.05 }}
                            key={p.order_id}
                            className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm hover:shadow-md transition-all group"
                        >
                            <div className="flex flex-col lg:flex-row justify-between gap-6">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-xs font-bold text-purple-600 bg-purple-50 px-2.5 py-1 rounded-lg uppercase">{p.order_id}</span>
                                        <span className="text-xs text-lightneutral">{new Date(p.time).toLocaleString()}</span>
                                    </div>
                                    <h3 className="text-xl font-bold text-neutral group-hover:text-purple-600 transition-colors uppercase">{p.service}</h3>
                                    <p className="text-2xl font-black text-neutral mt-2">{formatCurrency(p.total_paid)}</p>
                                </div>

                                <div className="flex-1 bg-gray-50/50 rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
                                    <div className="text-center">
                                        <p className="text-[10px] text-lightneutral font-bold uppercase">Provider Share</p>
                                        <p className="font-bold text-neutral">{formatCurrency(p.splits?.sp_share)}</p>
                                    </div>
                                    <FiArrowRight className="hidden md:block text-gray-300" />
                                    <div className="text-center">
                                        <p className="text-[10px] text-lightneutral font-bold uppercase">Villa Share</p>
                                        <p className="font-bold text-neutral">{formatCurrency(p.splits?.villa_share)}</p>
                                    </div>
                                    <FiArrowRight className="hidden md:block text-gray-300" />
                                    <div className="text-center">
                                        <p className="text-[10px] text-lightneutral font-bold uppercase">EB Profit</p>
                                        <p className="font-bold text-purple-600">{formatCurrency(p.splits?.eb_share)}</p>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))
                ) : (
                    <div className="text-center py-20 bg-white rounded-3xl border border-dashed border-gray-200">
                        <FiDollarSign className="mx-auto text-gray-200 mb-4" size={48} />
                        <p className="text-lightneutral">No paid transactions found in this period.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PaymentBucket;
