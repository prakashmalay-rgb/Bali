import React, { useState } from 'react';
import axios from 'axios';
import { FiLock, FiCheck } from 'react-icons/fi';

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'https://bali-v92r.onrender.com');

const ChangePassword = () => {
    const [form, setForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (form.new_password !== form.confirm_password) {
            setError('New passwords do not match.');
            return;
        }
        if (form.new_password.length < 8) {
            setError('New password must be at least 8 characters.');
            return;
        }

        setIsLoading(true);
        try {
            const token = localStorage.getItem('easybali_token');
            await axios.post(
                `${API_BASE_URL}/admin/change-password`,
                { current_password: form.current_password, new_password: form.new_password },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setSuccess('Password updated successfully.');
            setForm({ current_password: '', new_password: '', confirm_password: '' });
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to update password. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="max-w-lg">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-neutral">Change Password</h1>
                <p className="text-sm text-lightneutral mt-1">Update your login passkey</p>
            </div>

            <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-8">
                <form onSubmit={handleSubmit} className="space-y-5">
                    {error && (
                        <div className="bg-danger/10 text-danger text-sm font-medium px-4 py-3 rounded-xl flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-danger flex-shrink-0" />
                            {error}
                        </div>
                    )}
                    {success && (
                        <div className="bg-emerald-50 text-emerald-600 text-sm font-medium px-4 py-3 rounded-xl flex items-center gap-2">
                            <FiCheck size={14} className="flex-shrink-0" />
                            {success}
                        </div>
                    )}

                    {[
                        { name: 'current_password', label: 'Current Password', placeholder: 'Enter current password' },
                        { name: 'new_password', label: 'New Password', placeholder: 'Min. 8 characters' },
                        { name: 'confirm_password', label: 'Confirm New Password', placeholder: 'Repeat new password' },
                    ].map(({ name, label, placeholder }) => (
                        <div key={name}>
                            <label className="block text-sm font-bold text-neutral mb-2 ml-1">{label}</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-lightneutral">
                                    <FiLock size={16} />
                                </div>
                                <input
                                    type="password"
                                    required
                                    placeholder={placeholder}
                                    value={form[name]}
                                    onChange={(e) => setForm({ ...form, [name]: e.target.value })}
                                    className="block w-full pl-10 pr-4 py-3.5 bg-gray-50/50 border border-gray-100 rounded-2xl text-darkgrey focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none text-sm"
                                />
                            </div>
                        </div>
                    ))}

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full mt-2 bg-gradient-to-r from-primary to-[#0B97EE] hover:from-[#0158c2] hover:to-primary text-white font-bold py-3.5 rounded-2xl transition-all shadow-blue-shadow transform hover:scale-[1.01] disabled:opacity-70 disabled:hover:scale-100"
                    >
                        {isLoading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
                        ) : (
                            'Update Password'
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChangePassword;
