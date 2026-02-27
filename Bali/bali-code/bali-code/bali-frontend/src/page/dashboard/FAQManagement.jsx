import React, { useState, useEffect } from 'react';
import { FiPlus, FiTrash2, FiBook } from 'react-icons/fi';
import axios from 'axios';

const FAQManagement = () => {
    const [faqs, setFaqs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [formData, setFormData] = useState({
        question: '',
        answer: ''
    });
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

    const fetchFaqs = async () => {
        if (!user || (!user.villa_code && user.role !== 'admin')) return;

        // For admin to view a specific villa, they'd theoretically have a selector. 
        // For now, we assume admin is checking WEB_VILLA_01 or we rely on the staff's bound villa.
        const targetVilla = user.villa_code || 'WEB_VILLA_01';

        try {
            const res = await axios.get(`${baseUrl}/faq-admin/list/${targetVilla}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setFaqs(res.data.faqs);
            setLoading(false);
        } catch (err) {
            console.error('Error fetching FAQs:', err);
            setErrorMsg('Failed to load FAQs.');
            setLoading(false);
        }
    };

    useEffect(() => {
        if (user) {
            fetchFaqs();
        }
    }, [user, token]);

    const handleCreate = async (e) => {
        e.preventDefault();
        setErrorMsg('');
        setSuccessMsg('');
        setIsSubmitting(true);

        const targetVilla = user.villa_code || 'WEB_VILLA_01';

        try {
            await axios.post(`${baseUrl}/faq-admin/add`, {
                villa_code: targetVilla,
                question: formData.question,
                answer: formData.answer
            }, {
                headers: { Authorization: `Bearer ${token}` }
            });

            setSuccessMsg('Successfully injected FAQ into AI Memory.');
            setFormData({ question: '', answer: '' });
            fetchFaqs();
        } catch (err) {
            setErrorMsg(err.response?.data?.detail || 'Failed to create FAQ rule.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure you want to delete this FAQ from the AI memory?")) return;

        const targetVilla = user.villa_code || 'WEB_VILLA_01';
        try {
            await axios.delete(`${baseUrl}/faq-admin/delete/${id}?villa_code=${targetVilla}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            fetchFaqs();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to delete FAQ');
        }
    };

    return (
        <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-8 animate-fade-in pb-20 lg:pb-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl md:text-3xl font-bold text-neutral">AI Memory Rules</h1>
                    <p className="text-lightneutral">Teach the assistant specific House Rules to your Villa (e.g., WiFi, Trash pickup, Codes).</p>
                </div>
            </div>

            {errorMsg && <div className="p-4 bg-red-50 text-red-600 rounded-lg">{errorMsg}</div>}
            {successMsg && <div className="p-4 bg-green-50 text-green-600 rounded-lg">{successMsg}</div>}

            {/* Create FAQ Card */}
            <div className="bg-white rounded-xl shadow-sm border border-[#E2E8F0] overflow-hidden">
                <div className="px-6 py-4 border-b border-[#E2E8F0] bg-gray-50 flex items-center gap-2">
                    <FiBook className="text-gray-500" />
                    <h3 className="font-semibold text-gray-800">Add New AI Rule</h3>
                </div>
                <div className="p-6 bg-primary/5">
                    <form onSubmit={handleCreate} className="space-y-4">
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">Trigger Question or Topic</label>
                            <input
                                required type="text" placeholder="e.g. What is the WiFi password?"
                                className="w-full p-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
                                value={formData.question} onChange={e => setFormData({ ...formData, question: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-1">The Assistant's Direct Answer</label>
                            <textarea
                                required rows="3" placeholder="e.g. The WiFi network is 'BaliVilla1' and the password is 'sunnybali2024'."
                                className="w-full p-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
                                value={formData.answer} onChange={e => setFormData({ ...formData, answer: e.target.value })}
                            ></textarea>
                            <p className="text-xs text-gray-500 mt-1">This text will be instantly encoded into semantic vectors inside Pinecone and prioritized when guests ask anything related.</p>
                        </div>
                        <div className="flex justify-end">
                            <button type="submit" disabled={isSubmitting} className="max-w-xs w-full p-3 bg-primary hover:bg-[#0B97EE] transition-colors text-white rounded-lg font-medium flex justify-center items-center gap-2 shadow-sm">
                                <FiPlus /> {isSubmitting ? 'Encoding into AI Model...' : 'Inject into AI'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            {/* Existing FAQs */}
            <div className="bg-white rounded-xl shadow-sm border border-[#E2E8F0] overflow-hidden">
                <div className="px-6 py-4 border-b border-[#E2E8F0] bg-gray-50 flex items-center justify-between">
                    <h3 className="font-semibold text-gray-800">Active AI Memory Blocks</h3>
                </div>
                <div className="p-6">
                    {loading ? (
                        <div className="text-center py-8 text-gray-500">Loading AI memory index...</div>
                    ) : faqs.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">No custom rules have been added for your villa yet.</div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {faqs.map((faq) => (
                                <div key={faq.id} className="p-4 border rounded-lg hover:shadow-md transition-shadow bg-gray-50 group">
                                    <div className="flex justify-between items-start gap-4">
                                        <div className="space-y-2">
                                            <h4 className="font-bold text-gray-900 leading-snug">{faq.question}</h4>
                                            <p className="text-sm text-gray-600 bg-white p-2 rounded border border-gray-100 italic">{faq.answer}</p>
                                        </div>
                                        <button
                                            onClick={() => handleDelete(faq.id)}
                                            className="text-gray-400 hover:text-red-600 transition-colors p-1"
                                            title="Delete permanently"
                                        >
                                            <FiTrash2 className="text-lg" />
                                        </button>
                                    </div>
                                    <div className="mt-3 text-[10px] text-gray-400 font-mono">
                                        Vector ID: {faq.pinecone_id}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default FAQManagement;
