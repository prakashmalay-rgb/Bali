import React, { useState, useEffect } from 'react';
import { FiRotateCcw, FiCheck, FiX, FiAlertCircle } from 'react-icons/fi';
import { API_BASE_URL, apiRequest } from '../../api/apiClient';
import axios from 'axios';

const STATUS_STYLES = {
    pending:  'bg-amber-50 text-amber-700 border-amber-200',
    approved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    rejected: 'bg-rose-50 text-rose-700 border-rose-200',
    failed:   'bg-gray-100 text-gray-500 border-gray-200',
};

const RefundsView = () => {
    const [refunds, setRefunds] = useState([]);
    const [loading, setLoading] = useState(true);
    const [toast, setToast] = useState({ type: '', text: '' });
    const [showRequestModal, setShowRequestModal] = useState(false);
    const [showRejectModal, setShowRejectModal] = useState(null); // holds refund id
    const [form, setForm] = useState({ order_number: '', reason: '' });
    const [rejectNote, setRejectNote] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const showToast = (type, text) => {
        setToast({ type, text });
        setTimeout(() => setToast({ type: '', text: '' }), 4000);
    };

    const fetchRefunds = async () => {
        setLoading(true);
        try {
            const res = await apiRequest(() => axios.get(`${API_BASE_URL}/dashboard-api/refunds`));
            setRefunds(res.data.refunds || []);
        } catch {
            showToast('error', 'Failed to load refunds');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchRefunds(); }, []);

    const handleRequest = async () => {
        if (!form.order_number.trim() || !form.reason.trim()) {
            showToast('error', 'Order number and reason are required');
            return;
        }
        setSubmitting(true);
        try {
            await apiRequest(() => axios.post(`${API_BASE_URL}/dashboard-api/refunds`, form));
            showToast('success', 'Refund request submitted — awaiting admin approval');
            setShowRequestModal(false);
            setForm({ order_number: '', reason: '' });
            fetchRefunds();
        } catch (e) {
            showToast('error', e.response?.data?.detail || 'Failed to submit refund request');
        } finally {
            setSubmitting(false);
        }
    };

    const handleApprove = async (id) => {
        setSubmitting(true);
        try {
            await apiRequest(() => axios.post(`${API_BASE_URL}/dashboard-api/refunds/${id}/approve`));
            showToast('success', 'Refund approved and processed via Xendit');
            fetchRefunds();
        } catch (e) {
            showToast('error', e.response?.data?.detail || 'Failed to approve refund');
        } finally {
            setSubmitting(false);
        }
    };

    const handleReject = async () => {
        setSubmitting(true);
        try {
            await apiRequest(() => axios.post(`${API_BASE_URL}/dashboard-api/refunds/${showRejectModal}/reject`, { note: rejectNote }));
            showToast('success', 'Refund request rejected');
            setShowRejectModal(null);
            setRejectNote('');
            fetchRefunds();
        } catch (e) {
            showToast('error', e.response?.data?.detail || 'Failed to reject refund');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">
            {/* Header */}
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-4xl font-black text-neutral uppercase tracking-tighter italic">
                        Refund <span className="text-primary underline decoration-4 decoration-primary/20">Requests</span>
                    </h1>
                    <p className="text-sm font-medium text-lightneutral mt-1">
                        Review and process guest refunds. Admin approval required before Xendit processes the payout.
                    </p>
                </div>
                <button
                    onClick={() => setShowRequestModal(true)}
                    className="bg-neutral text-white px-6 py-3 rounded-2xl font-black text-sm uppercase tracking-widest hover:bg-primary transition-all flex items-center gap-2 shadow-xl"
                >
                    <FiRotateCcw /> New Request
                </button>
            </div>

            {/* Toast */}
            {toast.text && (
                <div className={`p-4 rounded-2xl font-bold text-sm flex items-center gap-3 border shadow-sm
                    ${toast.type === 'success' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-rose-50 text-rose-600 border-rose-100'}`}>
                    <FiAlertCircle /> {toast.text}
                </div>
            )}

            {/* Table */}
            <div className="bg-white/70 backdrop-blur-xl border border-white rounded-[2.5rem] shadow-sm overflow-hidden">
                {loading ? (
                    <div className="py-20 text-center font-black italic text-lightneutral">LOADING REFUND DATA...</div>
                ) : refunds.length === 0 ? (
                    <div className="py-20 text-center text-lightneutral font-bold">No refund requests yet.</div>
                ) : (
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-gray-100 text-[10px] font-black text-lightneutral uppercase tracking-widest">
                                <th className="text-left px-6 py-4">Order</th>
                                <th className="text-left px-6 py-4">Service</th>
                                <th className="text-left px-6 py-4">Amount</th>
                                <th className="text-left px-6 py-4">Reason</th>
                                <th className="text-left px-6 py-4">Status</th>
                                <th className="text-left px-6 py-4">Requested By</th>
                                <th className="text-left px-6 py-4">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {refunds.map((r) => (
                                <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                                    <td className="px-6 py-4 font-bold text-neutral">{r.order_number}</td>
                                    <td className="px-6 py-4 text-neutral">{r.service_name}</td>
                                    <td className="px-6 py-4 font-bold text-neutral">
                                        IDR {(r.paid_amount || 0).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 text-lightneutral max-w-[180px] truncate" title={r.reason}>{r.reason}</td>
                                    <td className="px-6 py-4">
                                        <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase border ${STATUS_STYLES[r.status] || STATUS_STYLES.failed}`}>
                                            {r.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-lightneutral text-xs">{r.requested_by}</td>
                                    <td className="px-6 py-4">
                                        {r.status === 'pending' && (
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={() => handleApprove(r.id)}
                                                    disabled={submitting}
                                                    className="p-2 bg-emerald-100 text-emerald-700 rounded-xl hover:bg-emerald-200 transition-colors disabled:opacity-50"
                                                    title="Approve & Process Refund"
                                                >
                                                    <FiCheck size={14} />
                                                </button>
                                                <button
                                                    onClick={() => setShowRejectModal(r.id)}
                                                    disabled={submitting}
                                                    className="p-2 bg-rose-100 text-rose-600 rounded-xl hover:bg-rose-200 transition-colors disabled:opacity-50"
                                                    title="Reject"
                                                >
                                                    <FiX size={14} />
                                                </button>
                                            </div>
                                        )}
                                        {r.status === 'approved' && (
                                            <span className="text-[10px] text-emerald-600 font-bold">Xendit ID: {r.xendit_refund_id || '—'}</span>
                                        )}
                                        {r.status === 'rejected' && r.rejection_note && (
                                            <span className="text-[10px] text-rose-500" title={r.rejection_note}>Note: {r.rejection_note.slice(0, 30)}{r.rejection_note.length > 30 ? '…' : ''}</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* New Request Modal */}
            {showRequestModal && (
                <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-[2.5rem] p-8 w-full max-w-md shadow-2xl space-y-5">
                        <h2 className="text-2xl font-black text-neutral uppercase tracking-tight">New Refund Request</h2>
                        <div>
                            <label className="text-[10px] font-black text-lightneutral uppercase tracking-widest block mb-2">Order Number</label>
                            <input
                                className="w-full border border-gray-200 rounded-2xl px-4 py-3 font-bold text-neutral focus:ring-4 focus:ring-primary/10 outline-none"
                                placeholder="e.g., EB-20260315-001"
                                value={form.order_number}
                                onChange={(e) => setForm({ ...form, order_number: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="text-[10px] font-black text-lightneutral uppercase tracking-widest block mb-2">Reason</label>
                            <textarea
                                rows={3}
                                className="w-full border border-gray-200 rounded-2xl px-4 py-3 font-bold text-neutral focus:ring-4 focus:ring-primary/10 outline-none resize-none"
                                placeholder="SP cancellation, guest complaint, duplicate charge..."
                                value={form.reason}
                                onChange={(e) => setForm({ ...form, reason: e.target.value })}
                            />
                        </div>
                        <div className="flex gap-3 pt-2">
                            <button onClick={() => setShowRequestModal(false)} className="flex-1 border border-gray-200 text-neutral font-black rounded-2xl py-3 hover:bg-gray-50 transition-colors">Cancel</button>
                            <button onClick={handleRequest} disabled={submitting} className="flex-1 bg-neutral text-white font-black rounded-2xl py-3 hover:bg-primary transition-colors disabled:opacity-50">
                                {submitting ? 'Submitting...' : 'Submit Request'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Reject Modal */}
            {showRejectModal && (
                <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-[2.5rem] p-8 w-full max-w-md shadow-2xl space-y-5">
                        <h2 className="text-2xl font-black text-neutral uppercase tracking-tight">Reject Refund</h2>
                        <div>
                            <label className="text-[10px] font-black text-lightneutral uppercase tracking-widest block mb-2">Rejection Note (optional)</label>
                            <textarea
                                rows={3}
                                className="w-full border border-gray-200 rounded-2xl px-4 py-3 font-bold text-neutral focus:ring-4 focus:ring-primary/10 outline-none resize-none"
                                placeholder="Reason for rejection..."
                                value={rejectNote}
                                onChange={(e) => setRejectNote(e.target.value)}
                            />
                        </div>
                        <div className="flex gap-3 pt-2">
                            <button onClick={() => setShowRejectModal(null)} className="flex-1 border border-gray-200 text-neutral font-black rounded-2xl py-3 hover:bg-gray-50 transition-colors">Cancel</button>
                            <button onClick={handleReject} disabled={submitting} className="flex-1 bg-rose-500 text-white font-black rounded-2xl py-3 hover:bg-rose-600 transition-colors disabled:opacity-50">
                                {submitting ? 'Rejecting...' : 'Confirm Reject'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default RefundsView;
