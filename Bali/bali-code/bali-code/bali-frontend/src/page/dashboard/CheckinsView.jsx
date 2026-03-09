import React, { useState, useEffect } from 'react';
import { FiMapPin, FiClock, FiSearch, FiHome, FiCheckCircle } from 'react-icons/fi';
import { API_BASE_URL, apiRequest } from '../../api/apiClient';
import axios from 'axios';

const CheckinsView = () => {
    const [checkins, setCheckins] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchCheckins();
    }, []);

    const fetchCheckins = async () => {
        setIsLoading(true);
        try {
            const response = await apiRequest(() => axios.get(`${API_BASE_URL}/dashboard-api/checkins`));
            if (response.data.success) {
                setCheckins(response.data.checkins);
            }
        } catch (error) {
            console.error('Failed to fetch checkins');
        } finally {
            setIsLoading(false);
        }
    };

    const filteredCheckins = checkins.filter(c =>
        c.villa_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.villa_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.guest_id?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-black text-neutral uppercase tracking-tight">Check-in <span className="text-primary">Logs</span></h1>
                    <p className="text-sm font-medium text-lightneutral mt-1">Real-time tracking of guest arrivals and active villa sessions.</p>
                </div>
            </div>

            <div className="flex flex-col md:flex-row gap-4 bg-white/60 backdrop-blur-md p-4 rounded-[2rem] border border-white shadow-sm">
                <div className="flex-1 relative group">
                    <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-lightneutral group-focus-within:text-primary transition-colors" />
                    <input
                        type="text"
                        placeholder="Search by Villa Name or Guest..."
                        className="w-full pl-12 pr-4 py-3 bg-white border border-gray-100 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm font-medium"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <div className="bg-white/70 backdrop-blur-xl border border-white rounded-[2.5rem] shadow-sm overflow-hidden">
                <div className="overflow-x-auto p-2">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="text-[10px] font-black text-lightneutral uppercase tracking-[0.2em] border-b border-gray-100/30">
                                <th className="px-6 py-5">Villa / Location</th>
                                <th className="px-6 py-5">Guest Reference</th>
                                <th className="px-6 py-5">Arrival Time</th>
                                <th className="px-6 py-5">Est. Departure</th>
                                <th className="px-6 py-5 text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50/50">
                            {isLoading ? (
                                <tr><td colSpan="5" className="py-20 text-center font-bold text-lightneutral italic uppercase">Syncing arrival data...</td></tr>
                            ) : filteredCheckins.length === 0 ? (
                                <tr><td colSpan="5" className="py-20 text-center font-bold text-lightneutral italic uppercase">No check-in logs recorded.</td></tr>
                            ) : (
                                filteredCheckins.map((c) => (
                                    <tr key={c.id} className="hover:bg-white/80 transition-all group">
                                        <td className="px-6 py-5">
                                            <div className="flex items-center gap-3">
                                                <div className="p-3 rounded-2xl bg-primary/10 text-primary">
                                                    <FiMapPin size={18} />
                                                </div>
                                                <div>
                                                    <p className="font-black text-neutral uppercase">{c.villa_name}</p>
                                                    <p className="text-[10px] font-bold text-lightneutral tracking-[0.1em]">{c.villa_code}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-5 font-bold text-darkgrey uppercase tracking-widest text-xs">
                                            {c.guest_id ? `CUSTOMER_${c.guest_id.slice(-6)}` : 'UNKNOWN'}
                                        </td>
                                        <td className="px-6 py-5">
                                            <div className="flex items-center gap-1.5 text-xs font-bold text-neutral">
                                                <FiClock className="text-lightneutral" />
                                                {c.time}
                                            </div>
                                        </td>
                                        <td className="px-6 py-5">
                                            <div className="flex items-center gap-1.5 text-xs font-bold text-rose-500">
                                                <FiClock className="text-lightneutral" />
                                                {c.checkout_time}
                                            </div>
                                        </td>
                                        <td className="px-6 py-5 text-right">
                                            <span className={`px-4 py-1.5 rounded-full text-[9px] font-black uppercase flex items-center gap-1 justify-center ml-auto w-fit border
                                                ${c.status === 'active' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-gray-50 text-lightneutral border-gray-100'}
                                            `}>
                                                <FiCheckCircle />
                                                {c.status}
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

export default CheckinsView;
