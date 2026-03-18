import { useState, useEffect } from 'react';
import { API_BASE_URL, apiRequest, getUserFriendlyError } from '../../api/apiClient';
import axios from 'axios';
import { FiClock, FiCheck, FiInfo, FiSearch, FiFilter, FiMessageSquare, FiAlertCircle, FiX, FiMapPin, FiPhone, FiTag, FiUser } from 'react-icons/fi';

// ── Detail slide-over panel ───────────────────────────────────────────────────

const DetailPanel = ({ act, onClose }) => {
    const [detail, setDetail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [fetchError, setFetchError] = useState('');

    useEffect(() => {
        const load = async () => {
            try {
                const res = await apiRequest(() =>
                    axios.get(`${API_BASE_URL}/dashboard-api/activity/${act.type}/${act.id}`)
                );
                if (res.data.success) setDetail(res.data.data);
                else setFetchError(res.data.error || 'Failed to load details.');
            } catch {
                setFetchError('Could not load details.');
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [act.id, act.type]);

    const Row = ({ icon, label, value }) => value ? (
        <div className="flex gap-3 items-start">
            <span className="mt-0.5 text-lightneutral flex-shrink-0">{icon}</span>
            <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-lightneutral">{label}</p>
                <p className="text-sm font-medium text-neutral mt-0.5 break-words">{value}</p>
            </div>
        </div>
    ) : null;

    const renderContent = () => {
        if (loading) return <p className="text-sm text-lightneutral italic">Loading...</p>;
        if (fetchError) return <p className="text-sm text-rose-500">{fetchError}</p>;
        if (!detail) return null;

        if (act.type === 'issue') return (
            <div className="space-y-4">
                <Row icon={<FiUser />} label="Customer ID" value={detail.customer_id} />
                <Row icon={<FiAlertCircle />} label="Description" value={detail.description} />
                <Row icon={<FiMapPin />} label="Villa" value={detail.villa_code} />
                <Row icon={<FiPhone />} label="Guest Number" value={detail.sender_id} />
                <Row icon={<FiTag />} label="Category" value={detail.category} />
                <Row icon={<FiClock />} label="Reported" value={detail.timestamp ? new Date(detail.timestamp).toLocaleString() : null} />
                {detail.photo_url && (
                    <div>
                        <p className="text-[10px] font-black uppercase tracking-widest text-lightneutral mb-2">Photo</p>
                        <img src={detail.photo_url} alt="Issue" className="rounded-2xl w-full object-cover max-h-48 border border-gray-100" />
                    </div>
                )}
            </div>
        );

        if (act.type === 'inquiry') return (
            <div className="space-y-4">
                <Row icon={<FiUser />} label="Customer ID" value={detail.customer_id} />
                <Row icon={<FiMessageSquare />} label="Guest Query" value={detail.query} />
                <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-lightneutral mb-1">AI Response</p>
                    <p className="text-sm text-neutral bg-gray-50 rounded-2xl p-3 leading-relaxed">{detail.response}</p>
                </div>
                <Row icon={<FiMapPin />} label="Villa" value={detail.villa_code} />
                <Row icon={<FiPhone />} label="Guest Number" value={detail.sender_id} />
                <Row icon={<FiTag />} label="Intent" value={detail.intent} />
                <Row icon={<FiClock />} label="Time" value={detail.timestamp ? new Date(detail.timestamp).toLocaleString() : null} />
            </div>
        );

        if (act.type === 'order') return (
            <div className="space-y-4">
                <Row icon={<FiUser />} label="Customer ID" value={detail.customer_id} />
                <Row icon={<FiTag />} label="Service" value={detail.service_name} />
                <Row icon={<FiMapPin />} label="Villa" value={detail.villa_code} />
                <Row icon={<FiPhone />} label="Guest Number" value={detail.sender_id} />
                <Row icon={<FiTag />} label="Status" value={detail.status} />
                {detail.payment?.paid_amount > 0 && (
                    <Row icon={<FiInfo />} label="Amount Paid" value={`IDR ${Number(detail.payment.paid_amount).toLocaleString('id-ID')}`} />
                )}
                <Row icon={<FiClock />} label="Created" value={detail.created_at ? new Date(detail.created_at).toLocaleString() : null} />
                <Row icon={<FiClock />} label="Updated" value={detail.updated_at ? new Date(detail.updated_at).toLocaleString() : null} />
            </div>
        );

        return null;
    };

    const typeLabel = { issue: 'Maintenance Issue', inquiry: 'AI Inquiry', order: 'Service Order' };
    const typeBg = { issue: 'bg-rose-50 text-rose-600', inquiry: 'bg-blue-50 text-blue-600', order: 'bg-emerald-50 text-emerald-600' };

    return (
        <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
            <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" />
            <div
                className="relative w-full max-w-md h-full bg-white shadow-2xl overflow-y-auto"
                onClick={e => e.stopPropagation()}
            >
                <div className="p-6 space-y-5">
                    {/* Header */}
                    <div className="flex items-start justify-between gap-3">
                        <div>
                            <span className={`text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full ${typeBg[act.type] || 'bg-gray-50 text-gray-500'}`}>
                                {typeLabel[act.type] || act.type}
                            </span>
                            <h2 className="text-lg font-black text-neutral mt-2">{act.guest_name}</h2>
                            {act.customer_id && (
                                <p className="text-xs font-bold text-primary/70 flex items-center gap-1 mt-0.5">
                                    <FiUser size={11} /> {act.customer_id}
                                </p>
                            )}
                            <p className="text-xs text-lightneutral mt-0.5">{act.time}</p>
                        </div>
                        <button onClick={onClose} className="p-2 rounded-xl hover:bg-gray-100 text-lightneutral flex-shrink-0">
                            <FiX size={18} />
                        </button>
                    </div>

                    <hr className="border-gray-100" />

                    {/* Detail content */}
                    {renderContent()}
                </div>
            </div>
        </div>
    );
};

// ── Main component ────────────────────────────────────────────────────────────

const GuestActivity = () => {
    const [activities, setActivities] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('all');
    const [error, setError] = useState('');
    const [selectedAct, setSelectedAct] = useState(null);

    useEffect(() => {
        const fetchActivity = async () => {
            try {
                const response = await apiRequest(() => axios.get(`${API_BASE_URL}/dashboard-api/activity`));
                if (response.data.success) {
                    setActivities(response.data.activity);
                }
            } catch (err) {
                console.error("Failed to fetch guest activity:", err);
                setError(getUserFriendlyError(err));
            } finally {
                setIsLoading(false);
            }
        };

        fetchActivity();
    }, []);

    const getStatusStyles = (status, type) => {
        if (type === 'issue' && status === 'pending') return 'bg-rose-50 text-rose-600 border-rose-100';
        switch (status) {
            case 'completed': return 'bg-emerald-50 text-emerald-600 border-emerald-100';
            case 'pending': return 'bg-amber-50 text-amber-600 border-amber-100';
            default: return 'bg-blue-50 text-primary border-blue-100';
        }
    };

    const getIcon = (type, status) => {
        switch (type) {
            case 'order': return status === 'completed' ? <FiCheck className="w-4 h-4" /> : <FiClock className="w-4 h-4" />;
            case 'inquiry': return <FiMessageSquare className="w-4 h-4" />;
            case 'issue': return <FiAlertCircle className="w-4 h-4" />;
            default: return <FiInfo className="w-4 h-4" />;
        }
    };

    const filteredActivities = activities.filter(act => {
        const matchesSearch =
            act.guest_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            act.service.toLowerCase().includes(searchTerm.toLowerCase()) ||
            act.action.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = filterStatus === 'all' || act.status === filterStatus;
        return matchesSearch && matchesStatus;
    });

    return (
        <div className="space-y-6">

            {/* Header & Controls */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-[#0B97EE] bg-clip-text text-transparent uppercase tracking-tight">Guest Activity</h1>
                    <p className="text-sm text-lightneutral mt-1 font-medium">Unified timeline of bookings, inquiries, and maintenance issues</p>
                </div>

                <div className="flex w-full md:w-auto gap-3">
                    <div className="relative flex-1 md:w-64">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-lightneutral">
                            <FiSearch />
                        </div>
                        <input
                            type="text"
                            className="block w-full pl-10 pr-4 py-2 bg-white/70 backdrop-blur-md border border-gray-100 rounded-xl text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                            placeholder="Search guests or events..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>

                    <div className="relative">
                        <select
                            className="appearance-none pl-4 pr-10 py-2 bg-white/70 backdrop-blur-md border border-gray-100 rounded-xl text-sm focus:ring-2 focus:ring-primary/20 outline-none transition-all cursor-pointer font-bold text-darkgrey"
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                        >
                            <option value="all">All Events</option>
                            <option value="pending">Pending</option>
                            <option value="completed">Completed</option>
                            <option value="resolved">Updates</option>
                        </select>
                        <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-lightneutral">
                            <FiFilter className="w-4 h-4" />
                        </div>
                    </div>
                </div>
            </div>

            {error && (
                <div className="p-4 bg-rose-50 border border-rose-100 rounded-2xl text-rose-600 text-sm font-medium flex items-center gap-3">
                    <FiAlertCircle />
                    {error}
                </div>
            )}

            {/* Main Activity Board */}
            <div className="bg-white/60 backdrop-blur-xl border border-white rounded-[2rem] shadow-sm overflow-hidden">
                <div className="overflow-x-auto p-2">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-gray-100/30">
                                <th className="py-4 px-6 text-[10px] font-bold text-lightneutral uppercase tracking-[0.2em]">Guest info</th>
                                <th className="py-4 px-6 text-[10px] font-bold text-lightneutral uppercase tracking-[0.2em]">Action / Event</th>
                                <th className="py-4 px-6 text-[10px] font-bold text-lightneutral uppercase tracking-[0.2em]">Details</th>
                                <th className="py-4 px-6 text-[10px] font-bold text-lightneutral uppercase tracking-[0.2em] text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50/50">
                            {isLoading ? (
                                <tr>
                                    <td colSpan="4" className="py-20 text-center">
                                        <div className="inline-block w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
                                        <p className="text-sm font-bold text-lightneutral mt-4 italic tracking-wide">Syncing real-time guest interactions...</p>
                                    </td>
                                </tr>
                            ) : filteredActivities.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="py-20 text-center">
                                        <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-300">
                                            <FiSearch size={24} />
                                        </div>
                                        <p className="text-sm font-bold text-darkgrey">No activity matches your filters.</p>
                                        <p className="text-xs text-lightneutral mt-1">Try broadening your search.</p>
                                    </td>
                                </tr>
                            ) : (
                                filteredActivities.map((act) => (
                                    <tr
                                        key={act.id}
                                        onClick={() => setSelectedAct(act)}
                                        className="hover:bg-white/80 transition-all group cursor-pointer border-l-4 border-l-transparent hover:border-l-primary"
                                    >
                                        <td className="py-4 px-6">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary/10 to-primary/5 border border-primary/10 flex items-center justify-center text-primary font-black shadow-sm group-hover:scale-110 transition-transform">
                                                    {act.guest_name.charAt(act.guest_name.length - 1)}
                                                </div>
                                                <div>
                                                    <p className="text-sm font-black text-neutral group-hover:text-primary transition-colors tracking-tight">{act.guest_name}</p>
                                                    {act.customer_id && (
                                                        <p className="text-[10px] font-bold text-primary/70 mt-0.5 flex items-center gap-1">
                                                            <FiUser size={9} />
                                                            {act.customer_id}
                                                        </p>
                                                    )}
                                                    <p className="text-[10px] font-bold text-lightneutral mt-0.5 opacity-70 uppercase">{act.time}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="py-4 px-6">
                                            <div className="flex items-center gap-2">
                                                <span className={`p-1.5 rounded-lg ${act.type === 'issue' ? 'bg-rose-100 text-rose-500' : 'bg-blue-100 text-blue-500'}`}>
                                                    {getIcon(act.type, act.status)}
                                                </span>
                                                <p className="text-sm font-bold text-darkgrey">{act.action}</p>
                                            </div>
                                        </td>
                                        <td className="py-4 px-6">
                                            <p className="text-xs font-semibold text-neutral line-clamp-1">{act.service}</p>
                                            {act.amount > 0 && (
                                                <p className="text-xs font-black text-emerald-500 mt-1">
                                                    IDR {act.amount.toLocaleString('id-ID')}
                                                </p>
                                            )}
                                        </td>
                                        <td className="py-4 px-6 text-right">
                                            <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-black uppercase border ${getStatusStyles(act.status, act.type)} shadow-sm`}>
                                                <span className="capitalize">{act.status}</span>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {selectedAct && (
                <DetailPanel act={selectedAct} onClose={() => setSelectedAct(null)} />
            )}

        </div>
    );
};

export default GuestActivity;
