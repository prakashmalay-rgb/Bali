import React, { useState, useEffect } from 'react';
import { FiCheckCircle, FiXCircle, FiSave, FiMessageSquare } from 'react-icons/fi';
import axios from 'axios';

const MessageAutomations = () => {
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');
    const [successMsg, setSuccessMsg] = useState('');
    const [user, setUser] = useState(null);

    const token = localStorage.getItem('easybali_token');
    const baseUrl = (import.meta.env.VITE_API_URL || 'https://bali-v92r.onrender.com');

    useEffect(() => {
        if (token) {
            try {
                const payloadStr = atob(token.split('.')[1]);
                const payload = JSON.parse(payloadStr);
                setUser(payload);
            } catch (err) {
                console.error("Failed to parse token", err);
            }
        }
    }, [token]);

    const fetchTemplates = async () => {
        if (!user || (!user.villa_code && user.role !== 'admin')) return;

        const targetVilla = user.villa_code || 'WEB_VILLA_01';

        try {
            const res = await axios.get(`${baseUrl}/automation-admin/list/${targetVilla}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setTemplates(res.data.templates);
            setLoading(false);
        } catch (err) {
            console.error('Error fetching templates:', err);
            setErrorMsg('Failed to load message templates.');
            setLoading(false);
        }
    };

    useEffect(() => {
        if (user) {
            fetchTemplates();
        }
    }, [user, token]);

    const handleUpdate = async (type, newContent, newStatus) => {
        setErrorMsg('');
        setSuccessMsg('');
        setSaving(true);
        const targetVilla = user.villa_code || 'WEB_VILLA_01';

        try {
            await axios.put(`${baseUrl}/automation-admin/update/${targetVilla}/${type}`, {
                content: newContent,
                is_active: newStatus
            }, {
                headers: { Authorization: `Bearer ${token}` }
            });

            setSuccessMsg(`Automation '${type}' saved successfully.`);
            fetchTemplates();
        } catch (err) {
            setErrorMsg(err.response?.data?.detail || 'Failed to update automation template.');
        } finally {
            setSaving(false);
        }
    };

    const handleContentChange = (id, text) => {
        setTemplates(prev => prev.map(t => t.id === id ? { ...t, content: text } : t));
    };

    const triggerInfo = {
        "welcome": "Sent to WhatsApp exactly 1 hour after booking confirmation or pending Check-In today.",
        "pre_checkout": "Sent 18 hours before registered Check-Out date.",
        "post_checkout": "Sent 6 hours after Check-Out sequence is complete."
    };

    const formatTypeName = (type) => {
        return type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    };

    return (
        <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-8 animate-fade-in pb-20 lg:pb-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl md:text-3xl font-bold text-neutral">The Butler (Automated Messaging)</h1>
                    <p className="text-lightneutral">Schedule and customize proactive WhatsApp messages to your guests before and after their stay.</p>
                </div>
            </div>

            {errorMsg && <div className="p-4 bg-red-50 text-red-600 rounded-lg">{errorMsg}</div>}
            {successMsg && <div className="p-4 bg-green-50 text-green-600 rounded-lg">{successMsg}</div>}

            <div className="space-y-6">
                {loading ? (
                    <div className="text-center py-10 text-gray-500">Loading automation triggers...</div>
                ) : (
                    templates.map((tpl) => (
                        <div key={tpl.id} className="bg-white rounded-xl shadow-sm border border-[#E2E8F0] overflow-hidden">
                            <div className="px-6 py-4 border-b border-[#E2E8F0] bg-gray-50 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <FiMessageSquare className="text-primary" />
                                    <h3 className="font-bold text-gray-800">{formatTypeName(tpl.type)} Sequence</h3>
                                </div>
                                <label className="flex items-center cursor-pointer relative">
                                    <input
                                        type="checkbox"
                                        className="sr-only"
                                        checked={tpl.is_active}
                                        onChange={(e) => handleUpdate(tpl.type, tpl.content, e.target.checked)}
                                    />
                                    <div className={`w-11 h-6 rounded-full transition-colors ${tpl.is_active ? 'bg-green-500' : 'bg-gray-300'}`}>
                                        <div className={`w-5 h-5 bg-white rounded-full mt-0.5 shadow transform transition-transform ${tpl.is_active ? 'translate-x-5' : 'translate-x-0.5'}`}></div>
                                    </div>
                                    <span className="ml-3 text-sm font-medium text-gray-700">
                                        {tpl.is_active ? 'Active' : 'Disabled'}
                                    </span>
                                </label>
                            </div>

                            <div className="p-6 space-y-4">
                                <div>
                                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Trigger Condition</div>
                                    <div className="bg-primary/10 text-primary p-3 rounded-md text-sm">
                                        {triggerInfo[tpl.type] || "Scheduled background event."}
                                    </div>
                                </div>

                                <div>
                                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">WhatsApp Message Template</div>
                                    <textarea
                                        rows="4"
                                        className="w-full p-4 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary disabled:bg-gray-100 disabled:text-gray-500"
                                        value={tpl.content}
                                        onChange={(e) => handleContentChange(tpl.id, e.target.value)}
                                        disabled={!tpl.is_active}
                                    ></textarea>
                                    <p className="text-xs text-gray-500 mt-2 italic">Variables available: &#123;name&#125; (Guest's Name)</p>
                                </div>

                                <div className="flex justify-end pt-2">
                                    <button
                                        onClick={() => handleUpdate(tpl.type, tpl.content, tpl.is_active)}
                                        disabled={saving || !tpl.is_active}
                                        className="px-4 py-2 bg-primary hover:bg-[#0B97EE] text-white rounded font-medium flex items-center gap-2 disabled:opacity-50 transition-colors"
                                    >
                                        <FiSave /> Save Changes
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

export default MessageAutomations;
