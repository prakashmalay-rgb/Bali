import React, { useState, useEffect } from 'react';
import { FiSearch, FiFilter, FiCalendar, FiDollarSign, FiCheckCircle, FiClock, FiXCircle } from 'react-icons/fi';
import { API_BASE_URL, apiRequest } from '../../api/apiClient';
import axios from 'axios';

const BookingsView = () => {
    const [bookings, setBookings] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('ALL');

    useEffect(() => {
        fetchBookings();
    }, [filterStatus]);

    const fetchBookings = async () => {
        setIsLoading(true);
        try {
            let url = `${API_BASE_URL}/dashboard-api/bookings`;
            if (filterStatus !== 'ALL') {
                url += `?status=${filterStatus}`;
            }
            const response = await apiRequest(() => axios.get(url));
            if (response.data.success) {
                setBookings(response.data.bookings);
            }
        } catch (error) {
            console.error('Failed to fetch bookings');
        } finally {
            setIsLoading(false);
        }
    };

    const filteredBookings = bookings.filter(b =>
        b.order_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        b.guest_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        b.service?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getStatusStyle = (status) => {
        switch (status) {
            case 'PAID': return 'bg-emerald-50 text-emerald-600 border-emerald-100';
            case 'PENDING': return 'bg-orange-50 text-orange-600 border-orange-100';
            case 'CANCELLED': return 'bg-rose-50 text-rose-600 border-rose-100';
            default: return 'bg-blue-50 text-primary border-blue-100';
        }
    };

    const formatIDR = (num) => {
        return new Intl.NumberFormat('id-ID', {
            style: 'currency',
            currency: 'IDR',
            minimumFractionDigits: 0
        }).format(num);
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-black text-neutral uppercase tracking-tight">Service <span className="text-primary">Bookings</span></h1>
                    <p className="text-sm font-medium text-lightneutral mt-1">Manage all service requests and orders across villas.</p>
                </div>
            </div>

            {/* Filters bar */}
            <div className="flex flex-col md:flex-row gap-4 bg-white/60 backdrop-blur-md p-4 rounded-[2rem] border border-white shadow-sm">
                <div className="flex-1 relative group">
                    <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-lightneutral group-focus-within:text-primary transition-colors" />
                    <input
                        type="text"
                        placeholder="Search by Order ID, Guest, or Service..."
                        className="w-full pl-12 pr-4 py-3 bg-white border border-gray-100 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm font-medium"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="flex items-center gap-2">
                    <FiFilter className="text-lightneutral ml-2" />
                    <select
                        className="bg-white border border-gray-100 rounded-2xl px-4 py-3 text-sm font-bold text-neutral focus:outline-none focus:ring-2 focus:ring-primary/20"
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                    >
                        <option value="ALL">ALL STATUS</option>
                        <option value="PAID">PAID</option>
                        <option value="PENDING">PENDING</option>
                        <option value="CANCELLED">CANCELLED</option>
                    </select>
                </div>
            </div>

            {/* Table Container */}
            <div className="bg-white/70 backdrop-blur-xl border border-white rounded-[2.5rem] shadow-sm overflow-hidden text-sm">
                <div className="overflow-x-auto p-2">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="text-[10px] font-black text-lightneutral uppercase tracking-[0.2em] border-b border-gray-100/30">
                                <th className="px-6 py-5">Order Reference</th>
                                <th className="px-6 py-5">Guest</th>
                                <th className="px-6 py-5">Service</th>
                                <th className="px-6 py-5">Villa</th>
                                <th className="px-6 py-5">Amount</th>
                                <th className="px-6 py-5 text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50/50">
                            {isLoading ? (
                                <tr><td colSpan="6" className="py-20 text-center font-bold text-lightneutral italic">Retrieving secure records...</td></tr>
                            ) : filteredBookings.length === 0 ? (
                                <tr><td colSpan="6" className="py-20 text-center font-bold text-lightneutral italic">No matching bookings found.</td></tr>
                            ) : (
                                filteredBookings.map((b) => (
                                    <tr key={b.id} className="hover:bg-white/80 transition-all group border-l-4 border-l-transparent hover:border-l-primary">
                                        <td className="px-6 py-5">
                                            <div className="flex items-center gap-2">
                                                <div className="p-2 rounded-xl bg-primary/5 text-primary">
                                                    <FiCalendar />
                                                </div>
                                                <div>
                                                    <p className="font-black text-neutral tracking-tight underline decoration-primary/20 decoration-2 underline-offset-4">{b.order_number}</p>
                                                    <p className="text-[9px] font-black text-lightneutral uppercase mt-0.5">{b.time}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-5 font-bold text-darkgrey uppercase tracking-tighter">
                                            {b.guest_id ? `...${b.guest_id.slice(-6)}` : 'UNKNOWN'}
                                        </td>
                                        <td className="px-6 py-5">
                                            <p className="font-black text-neutral">{b.service}</p>
                                        </td>
                                        <td className="px-6 py-5 font-bold text-lightneutral tracking-widest">
                                            {b.villa}
                                        </td>
                                        <td className="px-6 py-5 font-black text-neutral">
                                            {formatIDR(b.amount)}
                                        </td>
                                        <td className="px-6 py-5 text-right">
                                            <span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase border flex items-center gap-1.5 justify-center ml-auto w-fit
                                                ${getStatusStyle(b.status)}`}
                                            >
                                                {b.status === 'PAID' && <FiCheckCircle />}
                                                {b.status === 'PENDING' && <FiClock />}
                                                {b.status === 'CANCELLED' && <FiXCircle />}
                                                {b.status}
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

export default BookingsView;
