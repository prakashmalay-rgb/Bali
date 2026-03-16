import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { FiLock, FiArrowRight } from 'react-icons/fi';

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'https://bali-v92r.onrender.com');

const ResetPassword = () => {
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [token, setToken] = useState(null);
    
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        const queryParams = new URLSearchParams(location.search);
        const resetToken = queryParams.get('token');
        if (resetToken) {
            setToken(resetToken);
        } else {
            setError('Invalid or missing reset token.');
        }
    }, [location]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }
        
        if (!token) {
            setError("Cannot reset password without a valid token.");
            return;
        }

        setIsLoading(true);
        setError('');
        setSuccess('');

        try {
            const response = await axios.post(`${API_BASE_URL}/admin/reset-password`, { 
                token: token,
                new_password: password
            });

            if (response.data.status === 'success') {
                setSuccess("Password successfully reset! You will be redirected to the login page momentarily.");
                setTimeout(() => {
                    navigate('/admin/login');
                }, 3000);
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to reset password. The link might be expired.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#F4F7FB] flex items-center justify-center relative overflow-hidden font-sans">
            <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-gradient-to-tr from-primary/20 to-[#0B97EE]/5 blur-3xl" />
            <div className="absolute bottom-[-10%] right-[-5%] w-[600px] h-[600px] rounded-full bg-gradient-to-bl from-primary/10 to-transparent blur-3xl" />

            <div className="w-full max-w-md px-6 relative z-10 animate-fade-in">
                <div className="text-center mb-10">
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-[#0B97EE] bg-clip-text text-transparent tracking-tight">
                        EASY<span className="text-neutral">Bali</span>
                    </h1>
                    <p className="text-sm font-semibold text-lightneutral mt-2 tracking-widest uppercase">
                        Reset Password
                    </p>
                </div>

                <div className="bg-white/80 backdrop-blur-xl border border-white p-8 rounded-[2rem] shadow-[0_20px_40px_rgba(0,0,0,0.04)]">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <div className="bg-danger/10 text-danger text-sm font-medium px-4 py-3 rounded-xl flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-danger flex-shrink-0" />
                                {error}
                            </div>
                        )}
                        
                        {success && (
                            <div className="bg-emerald-50 text-emerald-600 text-sm font-medium px-4 py-3 rounded-xl flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0" />
                                {success}
                            </div>
                        )}

                        <div>
                            <label className="block text-sm font-bold text-neutral mb-2 ml-1">New Password</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-lightneutral">
                                    <FiLock size={18} />
                                </div>
                                <input
                                    type="password"
                                    required
                                    className="block w-full pl-11 pr-4 py-3.5 bg-gray-50/50 border border-gray-100 rounded-2xl text-darkgrey focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    disabled={!token || success}
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-bold text-neutral mb-2 ml-1">Confirm Password</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-lightneutral">
                                    <FiLock size={18} />
                                </div>
                                <input
                                    type="password"
                                    required
                                    className="block w-full pl-11 pr-4 py-3.5 bg-gray-50/50 border border-gray-100 rounded-2xl text-darkgrey focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
                                    placeholder="••••••••"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    disabled={!token || success}
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading || !token || success}
                            className="w-full relative group mt-8 bg-gradient-to-r from-primary to-[#0B97EE] hover:from-[#0158c2] hover:to-primary text-white font-bold py-4 rounded-2xl transition-all shadow-blue-shadow transform hover:scale-[1.02] flex items-center justify-center gap-2 disabled:opacity-70 disabled:hover:scale-100"
                        >
                            {isLoading ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    <span>Reset Password</span>
                                    <FiArrowRight className="group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>
                    
                    <div className="mt-6 text-center">
                        <button 
                            type="button" 
                            onClick={() => navigate('/admin/login')}
                            className="text-sm font-bold text-lightneutral hover:text-neutral transition-colors bg-transparent border-none cursor-pointer"
                        >
                            Back to Login
                        </button>
                    </div>
                </div>

                <p className="text-center text-xs text-lightneutral mt-8 font-medium">
                    Secured by EASY Bali Systems © 2026
                </p>
            </div>
        </div>
    );
};

export default ResetPassword;
