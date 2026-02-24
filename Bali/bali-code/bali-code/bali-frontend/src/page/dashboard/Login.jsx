import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FiLock, FiUser, FiArrowRight } from 'react-icons/fi';

const API_BASE_URL = 'https://easy-bali.onrender.com';

const Login = () => {
    const [credentials, setCredentials] = useState({ username: '', password: '' });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            const response = await axios.post(`${API_BASE_URL}/admin/login`, credentials);

            if (response.data.access_token) {
                // Store JWT token
                localStorage.setItem('easybali_token', response.data.access_token);
                // Redirect to dashboard securely
                navigate('/dashboard');
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to authenticate. Please check your credentials.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#F4F7FB] flex items-center justify-center relative overflow-hidden font-sans">
            {/* Background design accents */}
            <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-gradient-to-tr from-primary/20 to-[#0B97EE]/5 blur-3xl" />
            <div className="absolute bottom-[-10%] right-[-5%] w-[600px] h-[600px] rounded-full bg-gradient-to-bl from-primary/10 to-transparent blur-3xl" />

            <div className="w-full max-w-md px-6 relative z-10 animate-fade-in">

                {/* Brand Header */}
                <div className="text-center mb-10">
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-[#0B97EE] bg-clip-text text-transparent tracking-tight">
                        EASY<span className="text-neutral">Bali</span>
                    </h1>
                    <p className="text-sm font-semibold text-lightneutral mt-2 tracking-widest uppercase">
                        Host Authentication
                    </p>
                </div>

                {/* Login Glass Card */}
                <div className="bg-white/80 backdrop-blur-xl border border-white p-8 rounded-[2rem] shadow-[0_20px_40px_rgba(0,0,0,0.04)]">

                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <div className="bg-danger/10 text-danger text-sm font-medium px-4 py-3 rounded-xl flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-danger flex-shrink-0" />
                                {error}
                            </div>
                        )}

                        <div>
                            <label className="block text-sm font-bold text-neutral mb-2 ml-1">Admin ID</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-lightneutral">
                                    <FiUser size={18} />
                                </div>
                                <input
                                    type="text"
                                    required
                                    className="block w-full pl-11 pr-4 py-3.5 bg-gray-50/50 border border-gray-100 rounded-2xl text-darkgrey focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
                                    placeholder="Enter your username"
                                    value={credentials.username}
                                    onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-bold text-neutral mb-2 ml-1">Passkey</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-lightneutral">
                                    <FiLock size={18} />
                                </div>
                                <input
                                    type="password"
                                    required
                                    className="block w-full pl-11 pr-4 py-3.5 bg-gray-50/50 border border-gray-100 rounded-2xl text-darkgrey focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none"
                                    placeholder="••••••••"
                                    value={credentials.password}
                                    onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full relative group mt-8 bg-gradient-to-r from-primary to-[#0B97EE] hover:from-[#0158c2] hover:to-primary text-white font-bold py-4 rounded-2xl transition-all shadow-blue-shadow transform hover:scale-[1.02] flex items-center justify-center gap-2 disabled:opacity-70 disabled:hover:scale-100"
                        >
                            {isLoading ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    <span>Access Portal</span>
                                    <FiArrowRight className="group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>
                </div>

                <p className="text-center text-xs text-lightneutral mt-8 font-medium">
                    Secured by EASY Bali Systems © 2026
                </p>
            </div>
        </div>
    );
};

export default Login;
