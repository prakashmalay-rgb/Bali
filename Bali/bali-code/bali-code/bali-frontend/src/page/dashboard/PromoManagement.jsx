import React, { useState, useEffect } from 'react';
import { FiPlus, FiCheckCircle, FiXCircle, FiPercent, FiDollarSign } from 'react-icons/fi';
import axios from 'axios';

const PromoManagement = () => {
    const [promos, setPromos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [formData, setFormData] = useState({
        code: '',
        type: 'percentage',
        value: '',
        usage_limit: '',
        expiry: ''
    });
    const [errorMsg, setErrorMsg] = useState('');
    const [successMsg, setSuccessMsg] = useState('');

    const token = localStorage.getItem('easybali_token');
    const baseUrl = (import.meta.env.VITE_API_URL || 'https://bali-v92r.onrender.com');

    const fetchPromos = async () => {
        try {
            const res = await axios.get(`${baseUrl}/promos/list`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setPromos(res.data.promos);
            setLoading(false);
        } catch (err) {
            console.error('Error fetching promos:', err);
            setErrorMsg('Failed to load promo codes.');
            setLoading(false);
        }
    };

    useEffect(() => {
        if (token) fetchPromos();
    }, [token]);

    const handleCreate = async (e) => {
        e.preventDefault();
        setErrorMsg('');
        setSuccessMsg('');
        setIsSubmitting(true);

        try {
            const payload = {
                code: formData.code.toUpperCase(),
                type: formData.type,
                value: parseFloat(formData.value)
            };
            if (formData.usage_limit) payload.usage_limit = parseInt(formData.usage_limit);
            if (formData.expiry) payload.expiry = new Date(formData.expiry).toISOString();

            await axios.post(`${baseUrl}/promos/create`, payload, {
                headers: { Authorization: `Bearer ${token}` }
            });

            setSuccessMsg(`Promo Code ${payload.code} created successfully!`);
            setFormData({ code: '', type: 'percentage', value: '', usage_limit: '', expiry: '' });
            fetchPromos();
        } catch (err) {
            setErrorMsg(err.response?.data?.detail || 'Failed to create promo code.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleToggle = async (code) => {
        try {
            await axios.put(`${baseUrl}/promos/${code}/toggle`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
            fetchPromos(); // Refresh list to get new active status
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to toggle status');
        }
    };

    return (
        <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-8 animate-fade-in pb-20 lg:pb-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl md:text-3xl font-bold text-neutral">Promo Codes</h1>
                    <p className="text-lightneutral">Create and manage discount codes for the Chatbot and Bookings.</p>
                </div>
            </div>

            {errorMsg && <div className="p-4 bg-red-50 text-red-600 rounded-lg">{errorMsg}</div>}
            {successMsg && <div className="p-4 bg-green-50 text-green-600 rounded-lg">{successMsg}</div>}

            {/* Create Promo Card */}
            <div className="bg-white rounded-xl shadow-sm border border-[#E2E8F0] overflow-hidden">
                <div className="px-6 py-4 border-b border-[#E2E8F0] bg-gray-50 flex items-center justify-between">
                    <h3 className="font-semibold text-gray-800">Create New Promo</h3>
                </div>
                <div className="p-6">
                    <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Code</label>
                            <input
                                required type="text" placeholder="SUMMER20"
                                className="w-full p-2 border rounded focus:ring-2 focus:ring-primary"
                                value={formData.code} onChange={e => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                            <select
                                className="w-full p-2 border rounded focus:ring-2 focus:ring-primary"
                                value={formData.type} onChange={e => setFormData({ ...formData, type: e.target.value })}
                            >
                                <option value="percentage">Percentage (%)</option>
                                <option value="fixed">Fixed Rate (IDR)</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Value</label>
                            <div className="relative">
                                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                                    {formData.type === 'percentage' ? <FiPercent /> : <FiDollarSign />}
                                </span>
                                <input
                                    required type="number" min="1" step="any" placeholder={formData.type === 'fixed' ? '500000' : '20'}
                                    className="w-full pl-8 p-2 border rounded focus:ring-2 focus:ring-primary"
                                    value={formData.value} onChange={e => setFormData({ ...formData, value: e.target.value })}
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Usage Limit (Optional)</label>
                            <input
                                type="number" min="1" placeholder="Unlimited"
                                className="w-full p-2 border rounded focus:ring-2 focus:ring-primary"
                                value={formData.usage_limit} onChange={e => setFormData({ ...formData, usage_limit: e.target.value })}
                            />
                        </div>
                        <div className="w-full">
                            <button type="submit" disabled={isSubmitting} className="w-full p-2.5 bg-primary hover:bg-[#0B97EE] transition-colors text-white rounded font-medium flex justify-center items-center gap-2 shadow-sm">
                                <FiPlus /> {isSubmitting ? 'Creating...' : 'Create Promo'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            {/* Promo List */}
            <div className="bg-white rounded-xl shadow-sm border border-[#E2E8F0] overflow-hidden">
                <div className="px-6 py-4 border-b border-[#E2E8F0] bg-gray-50 flex items-center justify-between">
                    <h3 className="font-semibold text-gray-800">Active & Historical Codes</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-gray-600">
                        <thead className="bg-gray-50 text-gray-700 border-b">
                            <tr>
                                <th className="px-6 py-3 font-medium">Promo Code</th>
                                <th className="px-6 py-3 font-medium">Type</th>
                                <th className="px-6 py-3 font-medium">Value</th>
                                <th className="px-6 py-3 font-medium">Usage</th>
                                <th className="px-6 py-3 font-medium">Status</th>
                                <th className="px-6 py-3 font-medium text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {loading ? (
                                <tr><td colSpan="6" className="text-center py-8">Loading promos...</td></tr>
                            ) : promos.length === 0 ? (
                                <tr><td colSpan="6" className="text-center py-8 text-gray-500">No promo codes existing.</td></tr>
                            ) : promos.map((promo) => (
                                <tr key={promo.id} className="hover:bg-gray-50/50">
                                    <td className="px-6 py-4 font-bold text-gray-900">{promo.code}</td>
                                    <td className="px-6 py-4 capitalize">{promo.type}</td>
                                    <td className="px-6 py-4 ">{promo.type === 'percentage' ? `${promo.value}%` : `IDR ${promo.value.toLocaleString()}`}</td>
                                    <td className="px-6 py-4">
                                        {promo.current_usage} {promo.usage_limit ? `/ ${promo.usage_limit}` : 'uses'}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded text-xs font-semibold flex items-center gap-1 w-max ${promo.active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                            {promo.active ? <FiCheckCircle /> : <FiXCircle />}
                                            {promo.active ? 'Active' : 'Disabled'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button
                                            onClick={() => handleToggle(promo.code)}
                                            className="text-sm font-medium text-primary hover:text-[#0B97EE] underline"
                                        >
                                            {promo.active ? 'Deactivate' : 'Enable'}
                                        </button>
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

export default PromoManagement;
