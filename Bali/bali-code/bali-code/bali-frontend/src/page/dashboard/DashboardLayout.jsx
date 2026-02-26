import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
    FiHome,
    FiMessageSquare,
    FiLogOut,
    FiMenu,
    FiX,
    FiUser,
    FiFileText
} from 'react-icons/fi';

const DashboardLayout = () => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [user, setUser] = useState(null);
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        const token = localStorage.getItem('easybali_token');
        if (token) {
            try {
                const payloadStr = atob(token.split('.')[1]);
                const payload = JSON.parse(payloadStr);
                setUser({
                    email: payload.email,
                    role: payload.role || 'staff',
                    villa_code: payload.villa_code
                });
            } catch (err) {
                console.error("Failed to parse token", err);
            }
        }
    }, []);

    const handleLogout = () => {
        // Clear tokens
        localStorage.removeItem('easybali_token');
        navigate('/admin/login');
    };

    let navItems = [
        { path: '/dashboard', icon: <FiHome className="text-xl" />, label: 'Overview', roles: ['admin', 'staff', 'read_only'] },
        { path: '/dashboard/guests', icon: <FiUser className="text-xl" />, label: 'Guest Activity', roles: ['admin', 'staff', 'read_only'] },
        { path: '/dashboard/chats', icon: <FiMessageSquare className="text-xl" />, label: 'Concierge Chats', roles: ['admin', 'staff'] },
        { path: '/dashboard/passports', icon: <FiFileText className="text-xl" />, label: 'Passports', roles: ['admin'] },
    ];

    if (user) {
        navItems = navItems.filter(item => item.roles.includes(user.role));
    }

    return (
        <div className="flex h-screen bg-[#F7F8F9] font-sans overflow-hidden">

            {/* Mobile Sidebar Overlay */}
            {isSidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden backdrop-blur-sm transition-opacity"
                    onClick={() => setIsSidebarOpen(false)}
                />
            )}

            {/* Sidebar - Glassmorphism Design */}
            <aside
                className={`fixed lg:static top-0 left-0 h-full w-72 bg-white/70 backdrop-blur-xl border-r border-white/40 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] z-50 transform transition-transform duration-300 ease-in-out ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
                    } flex flex-col`}
            >
                <div className="p-8 flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold bg-gradient-to-r from-primary to-[#0B97EE] bg-clip-text text-transparent tracking-tight">
                            EASY<span className="text-neutral">Bali</span>
                        </h2>
                        <p className="text-xs text-lightneutral uppercase tracking-wider font-semibold mt-1">Host Portal</p>
                    </div>
                    <button
                        className="lg:hidden p-2 text-darkgrey hover:bg-light rounded-full transition-colors"
                        onClick={() => setIsSidebarOpen(false)}
                    >
                        <FiX size={24} />
                    </button>
                </div>

                <nav className="flex-1 px-4 py-6 space-y-2">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path || (item.path !== '/dashboard' && location.pathname.startsWith(item.path));
                        return (
                            <button
                                key={item.label}
                                onClick={() => {
                                    navigate(item.path);
                                    setIsSidebarOpen(false);
                                }}
                                className={`w-full flex items-center gap-4 px-4 py-3.5 rounded-2xl transition-all duration-300 font-medium ${isActive
                                    ? 'bg-primary text-white shadow-blue-shadow transform scale-[1.02]'
                                    : 'text-grey hover:bg-primary/10 hover:text-primary hover:scale-[1.02]'
                                    }`}
                            >
                                {item.icon}
                                {item.label}
                            </button>
                        );
                    })}
                </nav>

                <div className="p-6 border-t border-gray-100/50">
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-4 px-4 py-3 text-lightneutral hover:text-danger hover:bg-danger/10 rounded-2xl transition-all font-medium"
                    >
                        <FiLogOut className="text-xl" />
                        Sign Out
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col min-w-0 bg-secondarywhite relative">
                {/* Top Header */}
                <header className="h-20 bg-white/60 backdrop-blur-lg border-b border-white shadow-sm flex items-center px-6 sticky top-0 z-30 justify-between">
                    <button
                        className="lg:hidden p-2.5 bg-white text-darkgrey rounded-xl shadow-sm hover:shadow-md transition-shadow"
                        onClick={() => setIsSidebarOpen(true)}
                    >
                        <FiMenu size={20} />
                    </button>

                    <div className="flex-1 flex justify-end items-center gap-6">
                        <div className="flex items-center gap-3 bg-white py-2 px-4 rounded-full shadow-sm border border-gray-100">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-primary to-[#0B97EE] flex items-center justify-center text-white font-bold text-sm uppercase">
                                {user?.email ? user.email.charAt(0) : 'U'}
                            </div>
                            <div className="hidden md:block">
                                <p className="text-sm font-bold text-neutral truncate max-w-[150px]">{user?.email || 'User'}</p>
                                <p className="text-xs text-lightneutral capitalize">
                                    {user ? user.role.replace('_', ' ') : 'Role'}
                                    {user?.villa_code ? ` • ${user.villa_code}` : ''}
                                </p>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Scrollable Content */}
                <div className="flex-1 overflow-auto p-4 md:p-8">
                    <div className="max-w-7xl mx-auto animate-fade-in">
                        <Outlet />
                    </div>
                </div>
            </main>
        </div>
    );
};

export default DashboardLayout;