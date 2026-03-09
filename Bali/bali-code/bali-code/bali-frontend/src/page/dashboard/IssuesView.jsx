import React, { useState, useEffect } from 'react';
import { FiAlertCircle, FiSearch, FiFilter, FiCheckCircle, FiClock, FiUser, FiHome, FiPaperclip } from 'react-icons/fi';
import { API_BASE_URL, apiRequest } from '../../api/apiClient';
import axios from 'axios';

const IssuesView = () => {
    const [issues, setIssues] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('ALL');

    useEffect(() => {
        fetchIssues();
    }, [filterStatus]);

    const fetchIssues = async () => {
        setIsLoading(true);
        try {
            const response = await apiRequest(() => axios.get(`${API_BASE_URL}/dashboard-api/issues`));
            if (response.data.success) {
                // Front-end filter since backend returns recent for now
                let data = response.data.issues;
                if (filterStatus !== 'ALL') {
                    data = data.filter(i => i.status.toUpperCase() === filterStatus);
                }
                setIssues(data);
            }
        } catch (error) {
            console.error('Failed to fetch issues');
        } finally {
            setIsLoading(false);
        }
    };

    const filteredIssues = issues.filter(i =>
        i.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        i.guest_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        i.villa_code?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getStatusStyle = (status) => {
        switch (status.toLowerCase()) {
            case 'completed':
            case 'resolved': return 'bg-emerald-50 text-emerald-600 border-emerald-100';
            case 'pending':
            case 'open': return 'bg-rose-50 text-rose-600 border-rose-100';
            case 'in_progress': return 'bg-blue-50 text-primary border-blue-100';
            default: return 'bg-gray-50 text-lightneutral border-gray-100';
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-black text-neutral uppercase tracking-tight">Technical <span className="text-rose-500">Issues</span></h1>
                    <p className="text-sm font-medium text-lightneutral mt-1">Maintenance requests and guest reports that need attention.</p>
                </div>
            </div>

            <div className="flex flex-col md:flex-row gap-4 bg-white/60 backdrop-blur-md p-4 rounded-[2rem] border border-white shadow-sm">
                <div className="flex-1 relative group">
                    <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-lightneutral group-focus-within:text-rose-500 transition-colors" />
                    <input
                        type="text"
                        placeholder="Search by Description, Guest, or Villa..."
                        className="w-full pl-12 pr-4 py-3 bg-white border border-gray-100 rounded-2xl focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 transition-all text-sm font-medium"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="flex items-center gap-2">
                    <FiFilter className="text-lightneutral ml-2" />
                    <select
                        className="bg-white border border-gray-100 rounded-2xl px-4 py-3 text-sm font-bold text-neutral focus:outline-none focus:ring-2 focus:ring-rose-500/20"
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                    >
                        <option value="ALL">ALL STATUS</option>
                        <option value="OPEN">OPEN / PENDING</option>
                        <option value="COMPLETED">RESOLVED</option>
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {isLoading ? (
                    <div className="col-span-full py-20 text-center font-bold text-lightneutral italic uppercase tracking-widest">Scanning logs...</div>
                ) : filteredIssues.length === 0 ? (
                    <div className="col-span-full py-20 text-center font-bold text-lightneutral italic uppercase tracking-widest">No active issues found.</div>
                ) : (
                    filteredIssues.map((issue) => (
                        <div key={issue.id} className="bg-white/70 backdrop-blur-xl border border-white rounded-[2.5rem] p-6 shadow-sm hover:shadow-md transition-all group flex flex-col justify-between">
                            <div>
                                <div className="flex justify-between items-start mb-4">
                                    <span className={`px-3 py-1 rounded-full text-[9px] font-black uppercase border
                                        ${getStatusStyle(issue.status)}`}
                                    >
                                        {issue.status}
                                    </span>
                                    {issue.media_type !== 'text' && (
                                        <div className="p-2 bg-primary/5 rounded-lg text-primary" title="Image attachment available">
                                            <FiPaperclip size={14} />
                                        </div>
                                    )}
                                </div>
                                <h3 className="font-bold text-neutral leading-relaxed mb-4 group-hover:text-primary transition-colors">
                                    {issue.description || 'No description provided.'}
                                </h3>

                                <div className="space-y-2">
                                    <div className="flex items-center gap-2 text-[10px] font-black uppercase text-lightneutral">
                                        <FiHome size={12} className="text-secondary" />
                                        <span>Villa: {issue.villa_code}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-[10px] font-black uppercase text-lightneutral">
                                        <FiUser size={12} className="text-secondary" />
                                        <span>Guest: {issue.guest_id ? `...${issue.guest_id.slice(-4)}` : 'UNKNOWN'}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="mt-6 pt-4 border-t border-gray-50 flex items-center justify-between">
                                <span className="text-[10px] font-black text-lightneutral italic">{issue.time}</span>
                                <div className="flex gap-4">
                                    {issue.media_url && (
                                        <a
                                            href={issue.media_url}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="text-[10px] font-black text-rose-500 hover:underline uppercase tracking-widest flex items-center gap-1"
                                        >
                                            <FiPaperclip size={10} /> View Media
                                        </a>
                                    )}
                                    <button className="text-[10px] font-black text-primary hover:underline uppercase tracking-widest">
                                        Manage →
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default IssuesView;
