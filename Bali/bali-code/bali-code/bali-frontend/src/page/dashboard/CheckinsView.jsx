import { useState, useEffect } from 'react';
import {
    FiMapPin, FiClock, FiSearch, FiCheckCircle, FiPlus, FiX, FiCalendar, FiTrash2, FiUser
} from 'react-icons/fi';
import { API_BASE_URL, apiRequest } from '../../api/apiClient';
import axios from 'axios';

const authHeader = () => {
    const t = localStorage.getItem('easybali_token');
    return t ? { Authorization: `Bearer ${t}` } : {};
};

// ── Pre-register form modal ───────────────────────────────────────────────────

const RegisterArrivalModal = ({ onClose, onSaved }) => {
    const [form, setForm] = useState({
        guest_name: '', sender_id: '', villa_code: '',
        checkin_date: '', checkout_date: '', eta: ''
    });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    const handleSave = async () => {
        setError('');
        if (!form.sender_id.trim()) return setError('WhatsApp number is required.');
        if (!/^\d+$/.test(form.sender_id.trim())) return setError('WhatsApp number must be digits only (e.g. 628123456789).');
        if (!form.villa_code.trim()) return setError('Villa code is required.');
        if (!form.checkin_date) return setError('Check-in date is required.');
        setSaving(true);
        try {
            const res = await apiRequest(() =>
                axios.post(`${API_BASE_URL}/dashboard-api/arrivals/expected`, form, { headers: authHeader() })
            );
            if (res.data.success) { onSaved(res.data.arrival); onClose(); }
            else setError(res.data.error || 'Failed to save.');
        } catch { setError('Request failed.'); }
        finally { setSaving(false); }
    };

    const Field = ({ label, ...props }) => (
        <div>
            <label className="text-[10px] font-black uppercase tracking-widest text-lightneutral mb-1 block">{label}</label>
            <input className="w-full px-4 py-3 bg-gray-50 border border-gray-100 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/20" {...props} />
        </div>
    );

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
            <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" />
            <div className="relative w-full max-w-md bg-white rounded-[2rem] shadow-2xl p-6 space-y-4" onClick={e => e.stopPropagation()}>
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-black text-neutral">Pre-Register Guest</h2>
                    <button onClick={onClose} className="p-2 rounded-xl hover:bg-gray-100 text-lightneutral"><FiX /></button>
                </div>
                {error && <p className="text-sm font-bold text-rose-500 bg-rose-50 rounded-xl px-4 py-2">{error}</p>}
                <div className="space-y-3">
                    <Field label="Guest Name (optional)" value={form.guest_name} onChange={e => setForm(f => ({ ...f, guest_name: e.target.value }))} placeholder="e.g. John Smith" />
                    <Field label="WhatsApp Number *" value={form.sender_id} onChange={e => setForm(f => ({ ...f, sender_id: e.target.value }))} placeholder="e.g. 628123456789" />
                    <Field label="Villa Code *" value={form.villa_code} onChange={e => setForm(f => ({ ...f, villa_code: e.target.value.toUpperCase() }))} placeholder="e.g. V1" />
                    <div className="grid grid-cols-2 gap-3">
                        <Field label="Check-in Date *" type="date" value={form.checkin_date} onChange={e => setForm(f => ({ ...f, checkin_date: e.target.value }))} />
                        <Field label="Checkout Date" type="date" value={form.checkout_date} onChange={e => setForm(f => ({ ...f, checkout_date: e.target.value }))} />
                    </div>
                    <Field label="ETA (optional)" value={form.eta} onChange={e => setForm(f => ({ ...f, eta: e.target.value }))} placeholder="e.g. 3 PM" />
                </div>
                <p className="text-[10px] text-lightneutral">A pre-arrival WhatsApp will be sent 24–48 h before check-in date.</p>
                <div className="flex justify-end gap-3 pt-1">
                    <button onClick={onClose} className="px-5 py-2.5 rounded-xl border border-gray-200 text-sm font-bold hover:bg-gray-50">Cancel</button>
                    <button onClick={handleSave} disabled={saving}
                        className="px-6 py-2.5 rounded-xl bg-primary text-white text-sm font-black hover:opacity-90 disabled:opacity-50">
                        {saving ? 'Saving...' : 'Register'}
                    </button>
                </div>
            </div>
        </div>
    );
};

// ── Main view ─────────────────────────────────────────────────────────────────

const CheckinsView = () => {
    const [tab, setTab] = useState('active');          // 'active' | 'expected'
    const [checkins, setCheckins] = useState([]);
    const [expected, setExpected] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [showRegister, setShowRegister] = useState(false);

    useEffect(() => {
        fetchCheckins();
        fetchExpected();
    }, []);

    const fetchCheckins = async () => {
        setIsLoading(true);
        try {
            const res = await apiRequest(() => axios.get(`${API_BASE_URL}/dashboard-api/checkins`));
            if (res.data.success) setCheckins(res.data.checkins);
        } catch { /* ignore */ }
        finally { setIsLoading(false); }
    };

    const fetchExpected = async () => {
        try {
            const res = await apiRequest(() =>
                axios.get(`${API_BASE_URL}/dashboard-api/arrivals/expected`, { headers: authHeader() })
            );
            if (res.data.success) setExpected(res.data.arrivals);
        } catch { /* ignore */ }
    };

    const handleDelete = async (id) => {
        try {
            await apiRequest(() =>
                axios.delete(`${API_BASE_URL}/dashboard-api/arrivals/expected/${id}`, { headers: authHeader() })
            );
            setExpected(prev => prev.filter(e => e.id !== id));
        } catch { /* ignore */ }
    };

    const filteredCheckins = checkins.filter(c =>
        c.villa_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.villa_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.guest_id?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const filteredExpected = expected.filter(e =>
        e.villa_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.guest_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.sender_id?.includes(searchTerm)
    );

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-black text-neutral uppercase tracking-tight">Villa <span className="text-primary">Arrivals</span></h1>
                    <p className="text-sm font-medium text-lightneutral mt-1">Track active check-ins and pre-register expected guests.</p>
                </div>
                <button
                    onClick={() => setShowRegister(true)}
                    className="inline-flex items-center gap-2 px-5 py-3 bg-primary text-white rounded-2xl text-sm font-black hover:opacity-90 transition-opacity shadow-sm">
                    <FiPlus /> Pre-Register Guest
                </button>
            </div>

            {/* Tabs + Search */}
            <div className="flex flex-col md:flex-row gap-4 bg-white/60 backdrop-blur-md p-4 rounded-[2rem] border border-white shadow-sm">
                <div className="flex gap-2">
                    {[['active', 'Active Check-ins'], ['expected', 'Expected Arrivals']].map(([v, l]) => (
                        <button key={v} onClick={() => setTab(v)}
                            className={`px-4 py-2 rounded-xl text-xs font-black border transition-colors
                                ${tab === v ? 'bg-primary text-white border-primary' : 'bg-white text-lightneutral border-gray-100 hover:border-primary/30'}`}>
                            {l}
                            {v === 'expected' && expected.length > 0 && (
                                <span className="ml-1.5 px-1.5 py-0.5 bg-white/20 rounded-full text-[10px]">{expected.length}</span>
                            )}
                        </button>
                    ))}
                </div>
                <div className="flex-1 relative group">
                    <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-lightneutral group-focus-within:text-primary transition-colors" />
                    <input
                        type="text"
                        placeholder="Search by Villa or Guest..."
                        className="w-full pl-12 pr-4 py-3 bg-white border border-gray-100 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm font-medium"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            {/* Active Check-ins table */}
            {tab === 'active' && (
                <div className="bg-white/70 backdrop-blur-xl border border-white rounded-[2.5rem] shadow-sm overflow-hidden">
                    <div className="overflow-x-auto p-2">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="text-[10px] font-black text-lightneutral uppercase tracking-[0.2em] border-b border-gray-100/30">
                                    <th className="px-6 py-5">Villa / Location</th>
                                    <th className="px-6 py-5">Guest Reference</th>
                                    <th className="px-6 py-5">Arrival Time</th>
                                    <th className="px-6 py-5">Est. Departure</th>
                                    <th className="px-6 py-5 text-right">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50/50">
                                {isLoading ? (
                                    <tr><td colSpan="5" className="py-20 text-center font-bold text-lightneutral italic uppercase">Syncing arrival data...</td></tr>
                                ) : filteredCheckins.length === 0 ? (
                                    <tr><td colSpan="5" className="py-20 text-center font-bold text-lightneutral italic uppercase">No check-in logs recorded.</td></tr>
                                ) : filteredCheckins.map((c) => (
                                    <tr key={c.id} className="hover:bg-white/80 transition-all">
                                        <td className="px-6 py-5">
                                            <div className="flex items-center gap-3">
                                                <div className="p-3 rounded-2xl bg-primary/10 text-primary"><FiMapPin size={18} /></div>
                                                <div>
                                                    <p className="font-black text-neutral uppercase">{c.villa_name}</p>
                                                    <p className="text-[10px] font-bold text-lightneutral tracking-[0.1em]">{c.villa_code}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-5 font-bold text-darkgrey uppercase tracking-widest text-xs">
                                            {c.guest_id ? `CUSTOMER_${c.guest_id.slice(-6)}` : 'UNKNOWN'}
                                        </td>
                                        <td className="px-6 py-5">
                                            <div className="flex items-center gap-1.5 text-xs font-bold text-neutral">
                                                <FiClock className="text-lightneutral" />{c.time}
                                            </div>
                                        </td>
                                        <td className="px-6 py-5">
                                            <div className="flex items-center gap-1.5 text-xs font-bold text-rose-500">
                                                <FiClock className="text-lightneutral" />{c.checkout_time}
                                            </div>
                                        </td>
                                        <td className="px-6 py-5 text-right">
                                            <span className={`px-4 py-1.5 rounded-full text-[9px] font-black uppercase inline-flex items-center gap-1 border
                                                ${c.status === 'active' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-gray-50 text-lightneutral border-gray-100'}`}>
                                                <FiCheckCircle />{c.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Expected Arrivals table */}
            {tab === 'expected' && (
                <div className="bg-white/70 backdrop-blur-xl border border-white rounded-[2.5rem] shadow-sm overflow-hidden">
                    <div className="overflow-x-auto p-2">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="text-[10px] font-black text-lightneutral uppercase tracking-[0.2em] border-b border-gray-100/30">
                                    <th className="px-6 py-5">Guest</th>
                                    <th className="px-6 py-5">Villa</th>
                                    <th className="px-6 py-5">Check-in Date</th>
                                    <th className="px-6 py-5">Checkout Date</th>
                                    <th className="px-6 py-5">ETA</th>
                                    <th className="px-6 py-5 text-right">Pre-Arrival</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50/50">
                                {filteredExpected.length === 0 ? (
                                    <tr>
                                        <td colSpan="6" className="py-20 text-center">
                                            <FiCalendar className="mx-auto text-2xl text-lightneutral mb-2" />
                                            <p className="font-bold text-lightneutral text-sm">No expected arrivals. Use "Pre-Register Guest" to add one.</p>
                                        </td>
                                    </tr>
                                ) : filteredExpected.map((e) => (
                                    <tr key={e.id} className="hover:bg-white/80 transition-all">
                                        <td className="px-6 py-5">
                                            <div className="flex items-center gap-3">
                                                <div className="p-2 rounded-xl bg-primary/5 text-primary"><FiUser size={14} /></div>
                                                <div>
                                                    <p className="font-black text-neutral text-sm">{e.guest_name || 'Unknown Guest'}</p>
                                                    <p className="text-[10px] font-bold text-lightneutral">...{e.sender_id?.slice(-6)}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-5 font-bold text-lightneutral tracking-widest text-sm">{e.villa_code}</td>
                                        <td className="px-6 py-5 text-sm font-bold text-neutral">
                                            {e.checkin_date ? new Date(e.checkin_date).toLocaleDateString('en-GB') : '—'}
                                        </td>
                                        <td className="px-6 py-5 text-sm font-bold text-lightneutral">
                                            {e.checkout_date ? new Date(e.checkout_date).toLocaleDateString('en-GB') : '—'}
                                        </td>
                                        <td className="px-6 py-5">
                                            {e.eta
                                                ? <span className="px-2 py-1 bg-emerald-50 text-emerald-600 border border-emerald-100 rounded-lg text-xs font-black">{e.eta}</span>
                                                : <span className="text-xs text-lightneutral italic">Awaiting reply</span>
                                            }
                                        </td>
                                        <td className="px-6 py-5 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                {e.pre_arrival_sent
                                                    ? <span className="px-3 py-1 bg-blue-50 text-blue-600 border border-blue-100 rounded-full text-[9px] font-black">SENT</span>
                                                    : <span className="px-3 py-1 bg-orange-50 text-orange-500 border border-orange-100 rounded-full text-[9px] font-black">PENDING</span>
                                                }
                                                <button onClick={() => handleDelete(e.id)}
                                                    className="p-1.5 rounded-lg hover:bg-rose-50 hover:text-rose-500 text-lightneutral transition-colors">
                                                    <FiTrash2 size={13} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {showRegister && (
                <RegisterArrivalModal
                    onClose={() => setShowRegister(false)}
                    onSaved={(arrival) => { setExpected(prev => [arrival, ...prev]); setTab('expected'); }}
                />
            )}
        </div>
    );
};

export default CheckinsView;
