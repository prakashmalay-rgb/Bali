import { useState, useEffect } from 'react';
import { FiAlertCircle, FiSearch, FiFilter, FiUser, FiHome, FiPaperclip, FiX, FiDownload, FiMessageSquare, FiSmartphone, FiMonitor } from 'react-icons/fi';
import { API_BASE_URL, apiRequest } from '../../api/apiClient';
import axios from 'axios';

const STATUS_OPTIONS = ['open', 'in_progress', 'resolved', 'closed'];

const getStatusStyle = (status) => {
    switch ((status || '').toLowerCase()) {
        case 'completed':
        case 'resolved': return 'bg-emerald-50 text-emerald-600 border-emerald-100';
        case 'closed': return 'bg-gray-50 text-gray-500 border-gray-100';
        case 'pending':
        case 'open': return 'bg-rose-50 text-rose-600 border-rose-100';
        case 'in_progress': return 'bg-blue-50 text-primary border-blue-100';
        default: return 'bg-gray-50 text-lightneutral border-gray-100';
    }
};

const SourceBadge = ({ source }) => {
    if (source === 'whatsapp') {
        return (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-black uppercase bg-green-50 text-green-600 border border-green-100">
                <FiSmartphone size={9} /> WhatsApp
            </span>
        );
    }
    return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-black uppercase bg-indigo-50 text-indigo-600 border border-indigo-100">
            <FiMonitor size={9} /> Web
        </span>
    );
};

const ManageModal = ({ issue, onClose, onUpdated }) => {
    const [status, setStatus] = useState(issue.status);
    const [note, setNote] = useState('');
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    const handleSave = async () => {
        setSaving(true);
        setError('');
        try {
            const res = await apiRequest(() =>
                axios.patch(`${API_BASE_URL}/dashboard-api/issues/${issue.id}/status`, { status, note })
            );
            if (res.data.success) {
                onUpdated(issue.id, status);
                onClose();
            } else {
                setError(res.data.error || 'Update failed');
            }
        } catch (e) {
            setError('Failed to update issue status');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
            <div className="bg-white rounded-[2rem] shadow-2xl w-full max-w-lg p-8 space-y-6">
                <div className="flex justify-between items-start">
                    <div>
                        <h3 className="font-black text-neutral text-xl uppercase tracking-tight">Manage Issue</h3>
                        <p className="text-xs text-lightneutral mt-1">Villa: {issue.villa_code} • ID: ...{(issue.id || '').slice(-6)}</p>
                    </div>
                    <button onClick={onClose} className="p-2 bg-gray-100 hover:bg-rose-50 hover:text-rose-500 rounded-full transition-all"><FiX size={18} /></button>
                </div>

                <div className="p-4 bg-gray-50 rounded-2xl text-sm text-neutral leading-relaxed border border-gray-100">
                    {issue.description || 'No description provided.'}
                </div>

                {issue.history && issue.history.length > 0 && (
                    <div>
                        <p className="text-[10px] font-black uppercase text-lightneutral mb-2 tracking-widest">History</p>
                        <div className="space-y-2 max-h-32 overflow-y-auto pr-1">
                            {issue.history.map((h, i) => (
                                <div key={i} className="flex items-start gap-3 text-xs">
                                    <span className={`mt-0.5 px-2 py-0.5 rounded-full text-[9px] font-black uppercase border ${getStatusStyle(h.status)}`}>{h.status}</span>
                                    <span className="text-lightneutral">{h.note}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {issue.media_url && (
                    <div>
                        <p className="text-[10px] font-black uppercase text-lightneutral mb-2 tracking-widest">Attached Media</p>
                        <div className="bg-gray-50 rounded-2xl p-2 border border-gray-100 flex items-center justify-center">
                            {issue.media_type === 'voice_note' || issue.media_url.includes('.ogg') || issue.media_url.includes('.mp3') || issue.media_url.includes('.wav') ? (
                                <audio controls className="w-full">
                                    <source src={issue.media_url} type="audio/ogg" />
                                    Your browser does not support the audio element.
                                </audio>
                            ) : issue.media_type === 'video' || issue.media_url.includes('.mp4') ? (
                                <video controls className="max-h-64 rounded-xl">
                                    <source src={issue.media_url} type="video/mp4" />
                                    Your browser does not support the video element.
                                </video>
                            ) : (
                                <a href={issue.media_url} target="_blank" rel="noreferrer" title="Click to view full size">
                                    <img src={issue.media_url} alt="Issue Attachment" className="max-h-48 rounded-xl object-contain shadow-sm cursor-zoom-in hover:opacity-90 transition-opacity" />
                                </a>
                            )}
                        </div>
                    </div>
                )}

                <div className="space-y-3">
                    <div>
                        <label className="text-[10px] font-black uppercase text-lightneutral tracking-widest block mb-1">Update Status</label>
                        <select
                            value={status}
                            onChange={(e) => setStatus(e.target.value)}
                            className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm font-bold text-neutral focus:outline-none focus:ring-2 focus:ring-primary/20"
                        >
                            {STATUS_OPTIONS.map(s => (
                                <option key={s} value={s}>{s.replace('_', ' ').toUpperCase()}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="text-[10px] font-black uppercase text-lightneutral tracking-widest block mb-1">Note (optional)</label>
                        <textarea
                            value={note}
                            onChange={(e) => setNote(e.target.value)}
                            rows={2}
                            placeholder="Add a note about this status change..."
                            className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm text-neutral focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none"
                        />
                    </div>
                </div>

                {error && <p className="text-xs text-rose-500 font-bold">{error}</p>}

                <div className="flex justify-end gap-3">
                    <button onClick={onClose} className="px-5 py-2.5 rounded-xl font-bold text-sm text-darkgrey bg-gray-100 hover:bg-gray-200 transition">Cancel</button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="px-6 py-2.5 rounded-xl font-black text-sm text-white bg-primary hover:bg-[#0B97EE] transition-all disabled:opacity-50"
                    >
                        {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                </div>
            </div>
        </div>
    );
};

const exportToCSV = (issues) => {
    const headers = ['ID', 'Villa Code', 'Guest ID', 'Description', 'Priority', 'Status', 'Source', 'Has Media', 'Timestamp'];
    const rows = issues.map(i => [
        i.id, i.villa_code, i.guest_id || '', i.description || '', i.priority || '', i.status, i.source || '', i.media_url ? 'Yes' : 'No', i.time
    ]);
    const csv = [headers, ...rows].map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'issues_export.csv'; a.click();
    URL.revokeObjectURL(url);
};

const exportToExcel = (issues) => {
    // Build a simple HTML table that Excel can open directly
    const headers = ['ID', 'Villa Code', 'Guest ID', 'Description', 'Priority', 'Status', 'Source', 'Has Media', 'Timestamp'];
    const rows = issues.map(i => [
        i.id, i.villa_code, i.guest_id || '', i.description || '', i.priority || '', i.status, i.source || '', i.media_url ? 'Yes' : 'No', i.time
    ]);
    const tableRows = rows.map(r => `<tr>${r.map(v => `<td>${String(v).replace(/</g, '&lt;')}</td>`).join('')}</tr>`).join('');
    const html = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel"><head><meta charset="UTF-8"></head><body><table><thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>${tableRows}</tbody></table></body></html>`;
    const blob = new Blob([html], { type: 'application/vnd.ms-excel' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'issues_export.xls'; a.click();
    URL.revokeObjectURL(url);
};

const IssuesView = () => {
    const [issues, setIssues] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('ALL');
    const [managingIssue, setManagingIssue] = useState(null);

    useEffect(() => {
        fetchIssues();
    }, [filterStatus]);

    const fetchIssues = async () => {
        setIsLoading(true);
        try {
            const response = await apiRequest(() => axios.get(`${API_BASE_URL}/dashboard-api/issues`));
            if (response.data.success) {
                let data = response.data.issues;
                if (filterStatus !== 'ALL') {
                    data = data.filter(i => i.status.toUpperCase() === filterStatus || i.status.toLowerCase() === filterStatus.toLowerCase());
                }
                setIssues(data);
            }
        } catch (error) {
            console.error('Failed to fetch issues');
        } finally {
            setIsLoading(false);
        }
    };

    const handleStatusUpdated = (issueId, newStatus) => {
        setIssues(prev => prev.map(i => i.id === issueId ? { ...i, status: newStatus } : i));
    };

    const filteredIssues = issues.filter(i =>
        i.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        i.guest_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        i.villa_code?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="space-y-6">
            {managingIssue && (
                <ManageModal
                    issue={managingIssue}
                    onClose={() => setManagingIssue(null)}
                    onUpdated={handleStatusUpdated}
                />
            )}

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-black text-neutral uppercase tracking-tight">Technical <span className="text-rose-500">Issues</span></h1>
                    <p className="text-sm font-medium text-lightneutral mt-1">Maintenance requests and guest reports that need attention.</p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => exportToCSV(filteredIssues)}
                        className="inline-flex items-center gap-2 px-4 py-2 text-xs font-black uppercase text-primary bg-primary/10 hover:bg-primary hover:text-white rounded-xl transition-all"
                    >
                        <FiDownload size={13} /> CSV
                    </button>
                    <button
                        onClick={() => exportToExcel(filteredIssues)}
                        className="inline-flex items-center gap-2 px-4 py-2 text-xs font-black uppercase text-emerald-600 bg-emerald-50 hover:bg-emerald-600 hover:text-white rounded-xl transition-all border border-emerald-100"
                    >
                        <FiDownload size={13} /> Excel
                    </button>
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
                        <option value="open">OPEN</option>
                        <option value="in_progress">IN PROGRESS</option>
                        <option value="resolved">RESOLVED</option>
                        <option value="closed">CLOSED</option>
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
                        <div
                            key={issue.id}
                            onClick={() => setManagingIssue(issue)}
                            className="bg-white/70 backdrop-blur-xl border border-white rounded-[2.5rem] p-6 shadow-sm hover:shadow-md transition-all group flex flex-col justify-between cursor-pointer"
                        >
                            <div>
                                <div className="flex justify-between items-start mb-3">
                                    <span className={`px-3 py-1 rounded-full text-[9px] font-black uppercase border ${getStatusStyle(issue.status)}`}>
                                        {issue.status}
                                    </span>
                                    <div className="flex items-center gap-1.5">
                                        <SourceBadge source={issue.source} />
                                        {issue.media_type !== 'text' && issue.media_url && (
                                            <div className="p-1.5 bg-primary/5 rounded-lg text-primary" title="Image attachment">
                                                <FiPaperclip size={12} />
                                            </div>
                                        )}
                                    </div>
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
                                    {issue.priority && (
                                        <div className="flex items-center gap-2 text-[10px] font-black uppercase text-lightneutral">
                                            <FiAlertCircle size={12} className="text-secondary" />
                                            <span>Priority: {issue.priority}</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="mt-6 pt-4 border-t border-gray-50 flex items-center justify-between">
                                <span className="text-[10px] font-black text-lightneutral italic">{issue.time}</span>
                                <div className="flex gap-3">
                                    {issue.media_url && (
                                        <a
                                            href={issue.media_url}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="text-[10px] font-black text-rose-500 hover:underline uppercase tracking-widest flex items-center gap-1"
                                        >
                                            <FiPaperclip size={10} /> Media
                                        </a>
                                    )}
                                    <button
                                        onClick={() => setManagingIssue(issue)}
                                        className="text-[10px] font-black text-primary hover:underline uppercase tracking-widest flex items-center gap-1"
                                    >
                                        <FiMessageSquare size={10} /> Manage
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
