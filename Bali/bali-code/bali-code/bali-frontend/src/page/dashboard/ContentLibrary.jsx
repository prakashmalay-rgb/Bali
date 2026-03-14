import { useState, useEffect } from 'react';
import {
    FiPlus, FiSend, FiEdit2, FiTrash2, FiX, FiCheck,
    FiAlertCircle, FiMessageSquare, FiTag, FiClock
} from 'react-icons/fi';
import { API_BASE_URL, apiRequest } from '../../api/apiClient';
import axios from 'axios';

// ── constants ────────────────────────────────────────────────────────────────

const CONTENT_TYPES = [
    { value: 'announcement',    label: 'Announcement' },
    { value: 'promotion',       label: 'Promotion' },
    { value: 'notice',          label: 'Notice' },
    { value: 'travel_tip',      label: 'Travel Tip' },
    { value: 'welcome_message', label: 'Welcome Message' },
    { value: 'house_rules',     label: 'House Rules' },
    { value: 'privacy_notice',  label: 'Privacy Notice' },
];

const TYPE_COLORS = {
    announcement:    'bg-blue-50 text-blue-600 border-blue-100',
    promotion:       'bg-emerald-50 text-emerald-600 border-emerald-100',
    notice:          'bg-orange-50 text-orange-600 border-orange-100',
    travel_tip:      'bg-purple-50 text-purple-600 border-purple-100',
    welcome_message: 'bg-teal-50 text-teal-600 border-teal-100',
    house_rules:     'bg-gray-100 text-gray-600 border-gray-200',
    privacy_notice:  'bg-rose-50 text-rose-600 border-rose-100',
};

const typeLabel = (v) => CONTENT_TYPES.find(t => t.value === v)?.label ?? v;

// ── small helpers ─────────────────────────────────────────────────────────────

const authHeader = () => {
    const token = localStorage.getItem('easybali_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

const Toast = ({ msg, type, onClose }) => {
    useEffect(() => { const t = setTimeout(onClose, 3500); return () => clearTimeout(t); }, [onClose]);
    const base = type === 'error' ? 'bg-rose-50 border-rose-200 text-rose-700' : 'bg-emerald-50 border-emerald-200 text-emerald-700';
    return (
        <div className={`fixed bottom-6 right-6 z-[100] flex items-center gap-3 px-5 py-3 rounded-2xl border shadow-lg text-sm font-bold ${base}`}>
            {type === 'error' ? <FiAlertCircle /> : <FiCheck />}
            {msg}
            <button onClick={onClose} className="ml-2 opacity-60 hover:opacity-100"><FiX size={14} /></button>
        </div>
    );
};

// ── Edit / Create Modal ──────────────────────────────────────────────────────

const ContentModal = ({ item, onClose, onSaved }) => {
    const isNew = !item?.id;
    const [form, setForm] = useState({
        title: item?.title ?? '',
        type: item?.type ?? 'announcement',
        body: item?.body ?? '',
        tags: item?.tags?.join(', ') ?? '',
    });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    const handleSave = async () => {
        setError('');
        if (!form.title.trim()) return setError('Title is required.');
        if (!form.body.trim())  return setError('Message body is required.');
        setSaving(true);
        try {
            const payload = {
                title: form.title.trim(),
                type: form.type,
                body: form.body.trim(),
                tags: form.tags.split(',').map(t => t.trim()).filter(Boolean),
            };
            const url = isNew ? `${API_BASE_URL}/content` : `${API_BASE_URL}/content/${item.id}`;
            const method = isNew ? axios.post : axios.put;
            const res = await apiRequest(() => method(url, payload, { headers: authHeader() }));
            if (res.data.success) { onSaved(res.data.item); onClose(); }
            else setError(res.data.error || 'Failed to save.');
        } catch { setError('Request failed. Please try again.'); }
        finally { setSaving(false); }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
            <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" />
            <div className="relative w-full max-w-xl bg-white rounded-[2rem] shadow-2xl p-6 space-y-5" onClick={e => e.stopPropagation()}>
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-black text-neutral">{isNew ? 'New Content' : 'Edit Content'}</h2>
                    <button onClick={onClose} className="p-2 rounded-xl hover:bg-gray-100 text-lightneutral"><FiX /></button>
                </div>

                {error && <p className="text-sm font-bold text-rose-500 bg-rose-50 rounded-xl px-4 py-2">{error}</p>}

                <div className="space-y-4">
                    <div>
                        <label className="text-[11px] font-black uppercase tracking-widest text-lightneutral mb-1 block">Title</label>
                        <input
                            maxLength={200}
                            className="w-full px-4 py-3 bg-gray-50 border border-gray-100 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/20"
                            value={form.title}
                            onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                            placeholder="e.g. Villa Rules & Guidelines"
                        />
                    </div>

                    <div>
                        <label className="text-[11px] font-black uppercase tracking-widest text-lightneutral mb-1 block">Type</label>
                        <select
                            className="w-full px-4 py-3 bg-gray-50 border border-gray-100 rounded-xl text-sm font-bold text-neutral focus:outline-none focus:ring-2 focus:ring-primary/20"
                            value={form.type}
                            onChange={e => setForm(f => ({ ...f, type: e.target.value }))}
                        >
                            {CONTENT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                        </select>
                    </div>

                    <div>
                        <label className="text-[11px] font-black uppercase tracking-widest text-lightneutral mb-1 block">
                            Message Body
                            <span className="ml-2 normal-case font-medium text-gray-400">(WhatsApp markdown supported: *bold*, _italic_)</span>
                        </label>
                        <textarea
                            rows={8}
                            maxLength={4000}
                            className="w-full px-4 py-3 bg-gray-50 border border-gray-100 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none"
                            value={form.body}
                            onChange={e => setForm(f => ({ ...f, body: e.target.value }))}
                            placeholder="Write your message here..."
                        />
                        <p className="text-[10px] text-gray-400 text-right mt-1">{form.body.length}/4000</p>
                    </div>

                    <div>
                        <label className="text-[11px] font-black uppercase tracking-widest text-lightneutral mb-1 block">Tags <span className="font-medium normal-case">(comma-separated)</span></label>
                        <input
                            className="w-full px-4 py-3 bg-gray-50 border border-gray-100 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/20"
                            value={form.tags}
                            onChange={e => setForm(f => ({ ...f, tags: e.target.value }))}
                            placeholder="e.g. guest, arrival, important"
                        />
                    </div>
                </div>

                <div className="flex justify-end gap-3 pt-2">
                    <button onClick={onClose} className="px-5 py-2.5 rounded-xl border border-gray-200 text-sm font-bold text-neutral hover:bg-gray-50 transition-colors">Cancel</button>
                    <button onClick={handleSave} disabled={saving}
                        className="px-6 py-2.5 rounded-xl bg-primary text-white text-sm font-black hover:opacity-90 transition-opacity disabled:opacity-50">
                        {saving ? 'Saving...' : 'Save'}
                    </button>
                </div>
            </div>
        </div>
    );
};

// ── Send Modal ────────────────────────────────────────────────────────────────

const SendModal = ({ item, onClose, onSent }) => {
    const [channel, setChannel] = useState('whatsapp');
    const [target, setTarget] = useState('all');
    const [villaCode, setVillaCode] = useState('');
    const [customNumbers, setCustomNumbers] = useState('');
    const [sending, setSending] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');

    const handleSend = async () => {
        setError('');
        if (target === 'villa' && !villaCode.trim()) return setError('Please enter a villa code.');
        if (target === 'custom' && !customNumbers.trim()) return setError('Please enter at least one WhatsApp number.');

        const recipients = target === 'custom'
            ? customNumbers.split(/[\n,]+/).map(n => n.trim()).filter(Boolean)
            : undefined;

        if (target === 'custom') {
            const invalid = recipients.find(r => !/^\d+$/.test(r));
            if (invalid) return setError(`Invalid number format: "${invalid}" — digits only, no spaces or + sign.`);
        }

        setSending(true);
        try {
            const payload = { channel, target, ...(target === 'villa' ? { villa_code: villaCode.trim().toUpperCase() } : {}), ...(recipients ? { recipients } : {}) };
            const res = await apiRequest(() => axios.post(`${API_BASE_URL}/content/${item.id}/send`, payload, { headers: authHeader() }));
            if (res.data.success) { setResult(res.data); onSent(); }
            else setError(res.data.error || 'Send failed.');
        } catch { setError('Request failed. Please try again.'); }
        finally { setSending(false); }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
            <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" />
            <div className="relative w-full max-w-md bg-white rounded-[2rem] shadow-2xl p-6 space-y-5" onClick={e => e.stopPropagation()}>
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-[11px] font-black uppercase tracking-widest text-lightneutral">Send Message</p>
                        <h2 className="text-base font-black text-neutral">{item.title}</h2>
                    </div>
                    <button onClick={onClose} className="p-2 rounded-xl hover:bg-gray-100 text-lightneutral"><FiX /></button>
                </div>

                {result ? (
                    <div className="text-center py-4 space-y-2">
                        <div className="text-4xl">✅</div>
                        <p className="font-black text-neutral">Sent successfully</p>
                        <p className="text-sm text-lightneutral">{result.sent} sent · {result.failed} failed · {result.total_recipients} total recipients</p>
                        {result.note && <p className="text-xs text-orange-500 bg-orange-50 rounded-xl px-3 py-2">{result.note}</p>}
                        <button onClick={onClose} className="mt-4 px-6 py-2.5 rounded-xl bg-primary text-white text-sm font-black hover:opacity-90">Done</button>
                    </div>
                ) : (
                    <>
                        {error && <p className="text-sm font-bold text-rose-500 bg-rose-50 rounded-xl px-4 py-2">{error}</p>}

                        <div className="space-y-4">
                            {/* Channel */}
                            <div>
                                <label className="text-[11px] font-black uppercase tracking-widest text-lightneutral mb-2 block">Channel</label>
                                <div className="flex gap-2">
                                    {[['whatsapp', 'WhatsApp'], ['email', 'Email (soon)'], ['both', 'Both']].map(([v, l]) => (
                                        <button key={v}
                                            onClick={() => setChannel(v)}
                                            disabled={v === 'email' || v === 'both'}
                                            className={`flex-1 py-2 rounded-xl text-xs font-black border transition-colors
                                                ${channel === v ? 'bg-primary text-white border-primary' : 'bg-gray-50 text-lightneutral border-gray-100'}
                                                disabled:opacity-40 disabled:cursor-not-allowed`}>
                                            {l}
                                        </button>
                                    ))}
                                </div>
                                <p className="text-[10px] text-gray-400 mt-1">Email requires SMTP configuration — coming soon.</p>
                            </div>

                            {/* Target */}
                            <div>
                                <label className="text-[11px] font-black uppercase tracking-widest text-lightneutral mb-2 block">Recipients</label>
                                <div className="flex gap-2">
                                    {[['all', 'All Guests'], ['villa', 'By Villa'], ['custom', 'Custom']].map(([v, l]) => (
                                        <button key={v} onClick={() => setTarget(v)}
                                            className={`flex-1 py-2 rounded-xl text-xs font-black border transition-colors
                                                ${target === v ? 'bg-primary text-white border-primary' : 'bg-gray-50 text-lightneutral border-gray-100'}`}>
                                            {l}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {target === 'villa' && (
                                <div>
                                    <label className="text-[11px] font-black uppercase tracking-widest text-lightneutral mb-1 block">Villa Code</label>
                                    <input
                                        className="w-full px-4 py-3 bg-gray-50 border border-gray-100 rounded-xl text-sm font-bold uppercase focus:outline-none focus:ring-2 focus:ring-primary/20"
                                        value={villaCode}
                                        onChange={e => setVillaCode(e.target.value)}
                                        placeholder="e.g. V1"
                                    />
                                </div>
                            )}

                            {target === 'custom' && (
                                <div>
                                    <label className="text-[11px] font-black uppercase tracking-widest text-lightneutral mb-1 block">
                                        WhatsApp Numbers <span className="font-medium normal-case">(one per line, digits only)</span>
                                    </label>
                                    <textarea
                                        rows={4}
                                        className="w-full px-4 py-3 bg-gray-50 border border-gray-100 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none"
                                        value={customNumbers}
                                        onChange={e => setCustomNumbers(e.target.value)}
                                        placeholder={"628123456789\n628987654321"}
                                    />
                                </div>
                            )}
                        </div>

                        <div className="flex justify-end gap-3 pt-2">
                            <button onClick={onClose} className="px-5 py-2.5 rounded-xl border border-gray-200 text-sm font-bold text-neutral hover:bg-gray-50">Cancel</button>
                            <button onClick={handleSend} disabled={sending}
                                className="px-6 py-2.5 rounded-xl bg-primary text-white text-sm font-black hover:opacity-90 disabled:opacity-50 flex items-center gap-2">
                                <FiSend size={13} />
                                {sending ? 'Sending...' : 'Send Now'}
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

// ── Main Page ─────────────────────────────────────────────────────────────────

const ContentLibrary = () => {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [editItem, setEditItem] = useState(null);      // null = closed, {} = new, {...} = edit
    const [sendItem, setSendItem] = useState(null);
    const [deleteId, setDeleteId] = useState(null);
    const [toast, setToast] = useState(null);
    const [role, setRole] = useState('staff');

    useEffect(() => {
        const token = localStorage.getItem('easybali_token');
        if (token) {
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                setRole(payload.role || 'staff');
            } catch { /* ignore */ }
        }
        fetchItems();
    }, []);

    const fetchItems = async () => {
        setLoading(true);
        try {
            const res = await apiRequest(() => axios.get(`${API_BASE_URL}/content`, { headers: authHeader() }));
            if (res.data.success) setItems(res.data.items);
        } catch { /* ignore */ }
        finally { setLoading(false); }
    };

    const handleSaved = (saved) => {
        setItems(prev => {
            const idx = prev.findIndex(i => i.id === saved.id);
            return idx >= 0 ? prev.map(i => i.id === saved.id ? saved : i) : [saved, ...prev];
        });
        setToast({ msg: 'Content saved.', type: 'success' });
    };

    const handleDelete = async (id) => {
        try {
            const res = await apiRequest(() => axios.delete(`${API_BASE_URL}/content/${id}`, { headers: authHeader() }));
            if (res.data.success) {
                setItems(prev => prev.filter(i => i.id !== id));
                setToast({ msg: 'Deleted.', type: 'success' });
            } else {
                setToast({ msg: res.data.error || 'Delete failed.', type: 'error' });
            }
        } catch {
            setToast({ msg: 'Delete failed.', type: 'error' });
        }
        setDeleteId(null);
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-black text-neutral uppercase tracking-tight">Content <span className="text-primary">Library</span></h1>
                    <p className="text-sm font-medium text-lightneutral mt-1">Create and broadcast messages to guests via WhatsApp.</p>
                </div>
                <button
                    onClick={() => setEditItem({})}
                    className="inline-flex items-center gap-2 px-5 py-3 bg-primary text-white rounded-2xl text-sm font-black hover:opacity-90 transition-opacity shadow-sm">
                    <FiPlus /> New Content
                </button>
            </div>

            {/* Grid */}
            {loading ? (
                <div className="text-center py-20 text-sm font-bold text-lightneutral italic">Loading content library...</div>
            ) : items.length === 0 ? (
                <div className="text-center py-20 space-y-2">
                    <FiMessageSquare className="mx-auto text-3xl text-lightneutral" />
                    <p className="font-bold text-lightneutral">No content yet. Create your first message.</p>
                </div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {items.map(item => (
                        <div key={item.id} className="bg-white/70 backdrop-blur-xl border border-white rounded-[2rem] shadow-sm p-5 flex flex-col gap-3 hover:shadow-md transition-shadow">
                            {/* Type badge */}
                            <div className="flex items-center justify-between">
                                <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase border ${TYPE_COLORS[item.type] || 'bg-gray-50 text-gray-500 border-gray-100'}`}>
                                    {typeLabel(item.type)}
                                </span>
                                {item.send_history?.length > 0 && (
                                    <span className="text-[10px] font-bold text-lightneutral flex items-center gap-1">
                                        <FiSend size={10} /> Sent {item.send_history.length}x
                                    </span>
                                )}
                            </div>

                            {/* Title & body preview */}
                            <div className="flex-1">
                                <h3 className="font-black text-neutral text-sm leading-snug">{item.title}</h3>
                                <p className="text-xs text-lightneutral mt-1 line-clamp-3 leading-relaxed">{item.body}</p>
                            </div>

                            {/* Tags */}
                            {item.tags?.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                    {item.tags.map(tag => (
                                        <span key={tag} className="flex items-center gap-1 px-2 py-0.5 bg-gray-50 rounded-lg text-[10px] font-bold text-lightneutral">
                                            <FiTag size={9} /> {tag}
                                        </span>
                                    ))}
                                </div>
                            )}

                            {/* Timestamps */}
                            <p className="text-[10px] text-lightneutral flex items-center gap-1">
                                <FiClock size={10} />
                                Updated {item.updated_at ? new Date(item.updated_at).toLocaleDateString('en-GB') : '—'}
                            </p>

                            {/* Actions */}
                            <div className="flex gap-2 pt-1">
                                <button
                                    onClick={() => setSendItem(item)}
                                    className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-primary text-white text-xs font-black hover:opacity-90 transition-opacity">
                                    <FiSend size={11} /> Send
                                </button>
                                <button
                                    onClick={() => setEditItem(item)}
                                    className="p-2 rounded-xl border border-gray-100 hover:bg-gray-50 text-lightneutral transition-colors">
                                    <FiEdit2 size={14} />
                                </button>
                                {role === 'admin' && (
                                    <button
                                        onClick={() => setDeleteId(item.id)}
                                        className="p-2 rounded-xl border border-gray-100 hover:bg-rose-50 hover:text-rose-500 hover:border-rose-100 text-lightneutral transition-colors">
                                        <FiTrash2 size={14} />
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Modals */}
            {editItem !== null && (
                <ContentModal item={editItem?.id ? editItem : null} onClose={() => setEditItem(null)} onSaved={handleSaved} />
            )}
            {sendItem && (
                <SendModal item={sendItem} onClose={() => setSendItem(null)} onSent={() => { fetchItems(); setToast({ msg: 'Message sent!', type: 'success' }); }} />
            )}

            {/* Delete confirmation */}
            {deleteId && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={() => setDeleteId(null)}>
                    <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" />
                    <div className="relative bg-white rounded-[2rem] shadow-2xl p-6 w-full max-w-sm space-y-4" onClick={e => e.stopPropagation()}>
                        <h3 className="font-black text-neutral">Delete this content?</h3>
                        <p className="text-sm text-lightneutral">This action cannot be undone.</p>
                        <div className="flex gap-3">
                            <button onClick={() => setDeleteId(null)} className="flex-1 py-2.5 rounded-xl border border-gray-200 text-sm font-bold hover:bg-gray-50">Cancel</button>
                            <button onClick={() => handleDelete(deleteId)} className="flex-1 py-2.5 rounded-xl bg-rose-500 text-white text-sm font-black hover:opacity-90">Delete</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Toast */}
            {toast && <Toast msg={toast.msg} type={toast.type} onClose={() => setToast(null)} />}
        </div>
    );
};

export default ContentLibrary;
