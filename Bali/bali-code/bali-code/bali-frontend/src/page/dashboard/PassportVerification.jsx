import { useState, useEffect } from 'react';
import { API_BASE_URL, apiRequest, getUserFriendlyError } from '../../api/apiClient';
import axios from 'axios';
import { FiSearch, FiFileText, FiCheckCircle, FiClock, FiMaximize2, FiX, FiDownload, FiAlertCircle, FiSmartphone, FiMonitor } from 'react-icons/fi';

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

const RejectModal = ({ passport, onClose, onRejected }) => {
    const [reason, setReason] = useState('');
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    const handleReject = async () => {
        setSaving(true);
        setError('');
        try {
            const res = await apiRequest(() =>
                axios.put(`${API_BASE_URL}/dashboard-api/passports/${passport.id}/reject`, {
                    reason: reason || 'The document could not be verified. Please resubmit a clearer copy.'
                })
            );
            if (res.data.success) {
                onRejected(passport.id);
                onClose();
            } else {
                setError(res.data.error || 'Rejection failed');
            }
        } catch (e) {
            setError('Failed to reject passport');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
            <div className="bg-white rounded-[2rem] shadow-2xl w-full max-w-md p-8 space-y-6">
                <div className="flex justify-between items-start">
                    <div>
                        <h3 className="font-black text-neutral text-lg uppercase tracking-tight">Reject Submission</h3>
                        <p className="text-xs text-lightneutral mt-1">{passport.guest_name}</p>
                    </div>
                    <button onClick={onClose} className="p-2 bg-gray-100 hover:bg-rose-50 hover:text-rose-500 rounded-full transition-all"><FiX size={18} /></button>
                </div>
                <div>
                    <label className="text-[10px] font-black uppercase text-lightneutral tracking-widest block mb-1">Rejection Reason</label>
                    <textarea
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        rows={3}
                        placeholder="e.g. Document is blurry, please resubmit a clearer copy..."
                        className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm text-neutral focus:outline-none focus:ring-2 focus:ring-rose-500/20 resize-none"
                    />
                    <p className="text-[10px] text-lightneutral mt-1">This message will be sent to the guest via WhatsApp.</p>
                </div>
                {error && <p className="text-xs text-rose-500 font-bold">{error}</p>}
                <div className="flex justify-end gap-3">
                    <button onClick={onClose} className="px-5 py-2.5 rounded-xl font-bold text-sm text-darkgrey bg-gray-100 hover:bg-gray-200 transition">Cancel</button>
                    <button
                        onClick={handleReject}
                        disabled={saving}
                        className="px-6 py-2.5 rounded-xl font-black text-sm text-white bg-rose-500 hover:bg-rose-600 transition-all disabled:opacity-50"
                    >
                        {saving ? 'Rejecting...' : 'Reject & Notify Guest'}
                    </button>
                </div>
            </div>
        </div>
    );
};

const exportToCSV = (passports) => {
    const headers = ['ID', 'Guest Name', 'Villa Code', 'Source', 'Status', 'Uploaded At'];
    const rows = passports.map(p => [p.id, p.guest_name, p.villa_code, p.source || '', p.status, p.time]);
    const csv = [headers, ...rows].map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'passports_export.csv'; a.click();
    URL.revokeObjectURL(url);
};

const exportToExcel = (passports) => {
    const headers = ['ID', 'Guest Name', 'Villa Code', 'Source', 'Status', 'Uploaded At'];
    const rows = passports.map(p => [p.id, p.guest_name, p.villa_code, p.source || '', p.status, p.time]);
    const tableRows = rows.map(r => `<tr>${r.map(v => `<td>${String(v).replace(/</g, '&lt;')}</td>`).join('')}</tr>`).join('');
    const html = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel"><head><meta charset="UTF-8"></head><body><table><thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>${tableRows}</tbody></table></body></html>`;
    const blob = new Blob([html], { type: 'application/vnd.ms-excel' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'passports_export.xls'; a.click();
    URL.revokeObjectURL(url);
};

const PassportVerification = () => {
    const [passports, setPassports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedPassport, setSelectedPassport] = useState(null);
    const [rejectingPassport, setRejectingPassport] = useState(null);
    const [error, setError] = useState('');
    const [imgError, setImgError] = useState(false);

    useEffect(() => {
        const fetchPassports = async () => {
            try {
                const response = await apiRequest(() => axios.get(`${API_BASE_URL}/dashboard-api/passports`));
                if (response.data.success) {
                    setPassports(response.data.passports);
                }
            } catch (err) {
                console.error("Failed to fetch passports:", err);
                setError(getUserFriendlyError(err));
            } finally {
                setLoading(false);
            }
        };

        fetchPassports();
        const interval = setInterval(fetchPassports, 15000);
        return () => clearInterval(interval);
    }, []);

    const handleVerify = async (id) => {
        try {
            const response = await apiRequest(() => axios.put(`${API_BASE_URL}/dashboard-api/passports/${id}/verify`));
            if (response.data.success) {
                setPassports(prev => prev.map(p => p.id === id ? { ...p, status: 'verified' } : p));
                if (selectedPassport?.id === id) setSelectedPassport(prev => ({ ...prev, status: 'verified' }));
            } else {
                alert(response.data.error || 'Verification failed');
            }
        } catch (err) {
            alert(getUserFriendlyError(err));
        }
    };

    const handleRejected = (id) => {
        setPassports(prev => prev.map(p => p.id === id ? { ...p, status: 'rejected' } : p));
        if (selectedPassport?.id === id) setSelectedPassport(prev => ({ ...prev, status: 'rejected' }));
    };

    const filteredPassports = passports.filter(p =>
        p.guest_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.guest_id?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getStatusBadge = (status) => {
        switch (status) {
            case 'pending_verification':
                return (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase bg-orange-50 text-orange-600 border border-orange-100">
                        <FiClock className="w-3 h-3" /> Pending
                    </span>
                );
            case 'verified':
                return (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase bg-emerald-50 text-emerald-600 border border-emerald-100">
                        <FiCheckCircle className="w-3 h-3" /> Verified
                    </span>
                );
            case 'rejected':
                return (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase bg-rose-50 text-rose-600 border border-rose-100">
                        <FiAlertCircle className="w-3 h-3" /> Rejected
                    </span>
                );
            default:
                return (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase bg-gray-50 text-gray-500 border border-gray-100">
                        {status}
                    </span>
                );
        }
    };

    return (
        <div className="space-y-6">
            {rejectingPassport && (
                <RejectModal
                    passport={rejectingPassport}
                    onClose={() => setRejectingPassport(null)}
                    onRejected={handleRejected}
                />
            )}

            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-[#0B97EE] bg-clip-text text-transparent uppercase tracking-tight">
                        Passport Desk
                    </h1>
                    <p className="text-sm text-lightneutral mt-1 font-medium">Review and verify guest identities for compliance</p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => exportToCSV(filteredPassports)}
                        className="inline-flex items-center gap-2 px-4 py-2 text-xs font-black uppercase text-primary bg-primary/10 hover:bg-primary hover:text-white rounded-xl transition-all"
                    >
                        <FiDownload size={13} /> CSV
                    </button>
                    <button
                        onClick={() => exportToExcel(filteredPassports)}
                        className="inline-flex items-center gap-2 px-4 py-2 text-xs font-black uppercase text-emerald-600 bg-emerald-50 hover:bg-emerald-600 hover:text-white rounded-xl transition-all border border-emerald-100"
                    >
                        <FiDownload size={13} /> Excel
                    </button>
                </div>
            </div>

            {error && (
                <div className="p-4 bg-rose-50 border border-rose-100 rounded-2xl text-rose-600 font-medium">
                    {error}
                </div>
            )}

            <div className="bg-white/60 backdrop-blur-xl border border-white rounded-[2rem] shadow-sm overflow-hidden">
                <div className="p-4 border-b border-gray-100/30 flex justify-between items-center">
                    <div className="relative w-72">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-lightneutral">
                            <FiSearch />
                        </div>
                        <input
                            type="text"
                            className="block w-full pl-10 pr-4 py-2 bg-white/50 border border-gray-100 rounded-xl text-sm focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                            placeholder="Search by name or guest ID..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <span className="text-xs font-bold text-lightneutral">{filteredPassports.length} submission{filteredPassports.length !== 1 ? 's' : ''}</span>
                </div>

                <div className="overflow-x-auto p-2">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="text-[10px] font-bold text-lightneutral uppercase tracking-[0.2em] border-b border-gray-100/30">
                                <th className="px-6 py-4">Guest Identity</th>
                                <th className="px-6 py-4">Villa</th>
                                <th className="px-6 py-4">Source</th>
                                <th className="px-6 py-4">Uploaded At</th>
                                <th className="px-6 py-4 text-center">Security Status</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50/50">
                            {loading && passports.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="px-6 py-20 text-center">
                                        <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
                                        <p className="text-sm font-bold text-lightneutral">Decrypting secure files...</p>
                                    </td>
                                </tr>
                            ) : filteredPassports.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="px-6 py-20 text-center">
                                        <FiFileText className="w-12 h-12 text-gray-200 mx-auto mb-4" />
                                        <p className="text-darkgrey font-bold">No passport documents found</p>
                                        <p className="text-xs text-lightneutral mt-1">Guest submissions will appear here automatically.</p>
                                    </td>
                                </tr>
                            ) : (
                                filteredPassports.map((p) => (
                                    <tr key={p.id} className="hover:bg-white/80 transition-all group">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-black">
                                                    {p.guest_name?.charAt(0) || '?'}
                                                </div>
                                                <div>
                                                    <p className="text-sm font-black text-neutral uppercase">{p.guest_name}</p>
                                                    <p className="text-[10px] text-lightneutral font-bold tracking-tight">{p.guest_id?.slice(-8).toUpperCase()}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-xs font-bold text-darkgrey uppercase">{p.villa_code}</td>
                                        <td className="px-6 py-4"><SourceBadge source={p.source} /></td>
                                        <td className="px-6 py-4 text-xs font-semibold text-lightneutral">{p.time}</td>
                                        <td className="px-6 py-4 text-center">{getStatusBadge(p.status)}</td>
                                        <td className="px-6 py-4 text-right">
                                            <button
                                                onClick={() => { setSelectedPassport(p); setImgError(false); }}
                                                className="inline-flex items-center gap-2 px-3 py-2 text-xs font-black text-primary bg-primary/10 hover:bg-primary hover:text-white rounded-xl transition-all shadow-sm hover:scale-105"
                                            >
                                                <FiMaximize2 /> REVIEW
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Passport Lightbox Modal */}
            {selectedPassport && (
                <div
                    className="fixed inset-0 z-[100] flex items-center justify-center bg-darkgrey/90 backdrop-blur-md p-4 animate-fade-in"
                    onClick={(e) => { if (e.target.id === 'lightbox-bg') setSelectedPassport(null); }}
                    id="lightbox-bg"
                >
                    <div className="bg-white rounded-[2.5rem] shadow-2xl overflow-hidden max-w-4xl w-full flex flex-col max-h-[90vh]">
                        <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                            <div>
                                <div className="flex items-center gap-2 mb-1">
                                    <h3 className="font-black text-darkgrey text-xl uppercase tracking-tight">{selectedPassport.guest_name}</h3>
                                    <SourceBadge source={selectedPassport.source} />
                                </div>
                                <p className="text-xs font-bold text-lightneutral uppercase">
                                    Villa: {selectedPassport.villa_code} • ID: {selectedPassport.guest_id?.slice(-12)}
                                </p>
                            </div>
                            <button onClick={() => setSelectedPassport(null)} className="p-2 bg-gray-100 hover:bg-rose-50 hover:text-rose-500 rounded-full transition-all">
                                <FiX size={24} />
                            </button>
                        </div>

                        <div className="flex-1 overflow-auto bg-gray-50 p-8 flex items-center justify-center min-h-[400px]">
                            {!selectedPassport.passport_url || imgError ? (
                                <div className="text-center space-y-3">
                                    <FiFileText className="w-16 h-16 text-gray-300 mx-auto" />
                                    <p className="font-bold text-darkgrey">Document not available</p>
                                    <p className="text-xs text-lightneutral">The file could not be loaded. It may have been deleted or not yet uploaded.</p>
                                </div>
                            ) : selectedPassport.passport_url?.toLowerCase().split('?')[0].endsWith('.pdf') ? (
                                <iframe src={selectedPassport.passport_url} className="w-full h-[500px] rounded-2xl shadow-xl border-0" title="PDF Viewer" />
                            ) : (
                                <img
                                    src={selectedPassport.passport_url}
                                    alt="Document"
                                    className="max-w-full max-h-full object-contain rounded-2xl shadow-xl"
                                    onError={() => setImgError(true)}
                                />
                            )}
                        </div>

                        <div className="p-6 bg-white border-t border-gray-100 flex justify-end gap-3 flex-wrap">
                            <button onClick={() => setSelectedPassport(null)} className="px-6 py-3 rounded-2xl font-bold text-darkgrey bg-gray-100 hover:bg-gray-200 transition">CLOSE</button>

                            {selectedPassport.status === 'pending_verification' && (
                                <>
                                    <button
                                        onClick={() => { setSelectedPassport(null); setRejectingPassport(selectedPassport); }}
                                        className="px-6 py-3 rounded-2xl font-black text-white bg-rose-500 hover:bg-rose-600 transition-all"
                                    >
                                        REJECT
                                    </button>
                                    <button
                                        onClick={() => handleVerify(selectedPassport.id)}
                                        className="px-8 py-3 rounded-2xl font-black text-white bg-emerald-500 hover:bg-emerald-600 shadow-[0_10px_20px_rgba(16,185,129,0.2)] transition-all hover:scale-105 active:scale-95"
                                    >
                                        VERIFY & APPROVE
                                    </button>
                                </>
                            )}

                            <a
                                href={selectedPassport.passport_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl font-bold text-white bg-primary hover:bg-[#0B97EE] shadow-blue-shadow transition-all"
                            >
                                <FiDownload /> DOWNLOAD
                            </a>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PassportVerification;
