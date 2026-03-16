import React, { useState, useEffect } from 'react';
import { FiHome, FiWifi, FiFileText, FiLink, FiSave, FiAlertCircle, FiSettings, FiPlus, FiTrash2 } from 'react-icons/fi';
import { API_BASE_URL, apiRequest } from '../../api/apiClient';
import axios from 'axios';

const VillaProfile = () => {
    const [profile, setProfile] = useState({
        villa_code: '',
        manager_phone: '',
        wifi_name: '',
        wifi_password: '',
        house_rules: '',
        orientation_link: '',
        review_link: '',
        maps_link: '',
        docs: []
    });
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [statusMsg, setStatusMsg] = useState({ type: '', text: '' });
    const [userData, setUserData] = useState(null);
    const [villaList, setVillaList] = useState([]);
    const [selectedVilla, setSelectedVilla] = useState('');

    useEffect(() => {
        const storedUser = localStorage.getItem('user_data');
        if (storedUser) {
            const user = JSON.parse(storedUser);
            setUserData(user);
            initVillas(user);
        }
    }, []);

    const initVillas = async (user) => {
        const isAdmin = user.villa_codes?.includes('*');
        if (isAdmin) {
            try {
                const res = await apiRequest(() => axios.get(`${API_BASE_URL}/dashboard-api/villa/list`));
                if (res.data.success && res.data.villas.length > 0) {
                    setVillaList(res.data.villas);
                    const firstCode = res.data.villas[0].villa_code;
                    setSelectedVilla(firstCode);
                    fetchProfile(firstCode);
                } else {
                    setIsLoading(false);
                }
            } catch (error) {
                console.error('Failed to fetch villa list:', error);
                setIsLoading(false);
            }
        } else {
            const code = user.villa_codes?.[0] || '';
            setSelectedVilla(code);
            fetchProfile(code);
        }
    };

    const fetchProfile = async (villaCode) => {
        setIsLoading(true);
        try {
            const queryParam = villaCode ? `?code=${villaCode}` : '';
            const response = await apiRequest(() => axios.get(`${API_BASE_URL}/dashboard-api/villa/profile${queryParam}`));
            if (response.data.success) {
                setProfile(response.data.profile);
            }
        } catch (error) {
            console.error('Failed to fetch profile:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleVillaChange = (code) => {
        setSelectedVilla(code);
        fetchProfile(code);
    };

    const handleSave = async () => {
        setIsSaving(true);
        setStatusMsg({ type: '', text: '' });
        try {
            const response = await apiRequest(() => axios.post(`${API_BASE_URL}/dashboard-api/villa/profile`, profile));
            if (response.data.success) {
                setStatusMsg({ type: 'success', text: '✅ Profile updated successfully!' });
            } else {
                setStatusMsg({ type: 'error', text: `❌ ${response.data.error}` });
            }
        } catch (error) {
            setStatusMsg({ type: 'error', text: '❌ Failed to save profile. Please check your connection.' });
        } finally {
            setIsSaving(false);
            setTimeout(() => setStatusMsg({ type: '', text: '' }), 3000);
        }
    };

    const addDocLink = () => {
        const title = prompt("Document Title (e.g., Appliance Guide, Digital Orientation):");
        const url = prompt("URL link (e.g., Google Drive or Video link):");
        if (title && url) {
            setProfile(prev => ({
                ...prev,
                docs: [...prev.docs, { title, url }]
            }));
        }
    };

    const removeDoc = (index) => {
        setProfile(prev => ({
            ...prev,
            docs: prev.docs.filter((_, i) => i !== index)
        }));
    };

    if (isLoading) return <div className="py-20 text-center font-black italic text-lightneutral">SYNCHRONIZING SECURE VILLA DATA...</div>;

    return (
        <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-4xl font-black text-neutral uppercase tracking-tighter italic">Property <span className="text-primary underline decoration-4 decoration-primary/20">Profile</span></h1>
                    <p className="text-sm font-medium text-lightneutral mt-1">Configure property-specific information for AI context and guest orientation.</p>
                    {villaList.length > 1 && (
                        <select
                            value={selectedVilla}
                            onChange={(e) => handleVillaChange(e.target.value)}
                            className="mt-3 bg-white border border-gray-200 rounded-2xl px-4 py-2 font-bold text-sm text-neutral focus:ring-4 focus:ring-primary/10 outline-none"
                        >
                            {villaList.map((v) => (
                                <option key={v.villa_code} value={v.villa_code}>
                                    {v.name ? `${v.name} (${v.villa_code})` : v.villa_code}
                                </option>
                            ))}
                        </select>
                    )}
                </div>
                <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="bg-neutral text-white px-8 py-4 rounded-2xl font-black text-sm uppercase tracking-widest hover:bg-primary transition-all flex items-center gap-2 shadow-xl hover:shadow-primary/20 disabled:opacity-50"
                >
                    <FiSave /> {isSaving ? 'Synching...' : 'Commit Changes'}
                </button>
            </div>

            {statusMsg.text && (
                <div className={`p-4 rounded-2xl font-bold text-sm flex items-center gap-3 border shadow-sm transition-all
                    ${statusMsg.type === 'success' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-rose-50 text-rose-600 border-rose-100'}`}
                >
                    <FiAlertCircle /> {statusMsg.text}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Left: Basic Info */}
                <div className="bg-white/70 backdrop-blur-xl border border-white rounded-[2.5rem] p-8 shadow-sm space-y-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-3 bg-primary/10 rounded-2xl text-primary"><FiWifi size={24} /></div>
                        <h2 className="text-xl font-black text-neutral uppercase tracking-tight">Connectivity & <span className="text-primary">Wi-Fi</span></h2>
                    </div>

                    <div className="space-y-4">
                        <div>
                            <label className="text-[10px] font-black text-lightneutral uppercase tracking-widest block mb-2 px-1">Manager WhatsApp (Global Format)</label>
                            <input
                                type="text"
                                className="w-full bg-secondarywhite/30 border border-gray-100 rounded-2xl px-5 py-4 font-bold text-neutral focus:ring-4 focus:ring-primary/10 outline-none transition-all"
                                placeholder="e.g., 628123456789"
                                value={profile.manager_phone}
                                onChange={(e) => setProfile({ ...profile, manager_phone: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="text-[10px] font-black text-lightneutral uppercase tracking-widest block mb-2 px-1">Network Name (SSID)</label>
                            <input
                                type="text"
                                className="w-full bg-secondarywhite/30 border border-gray-100 rounded-2xl px-5 py-4 font-bold text-neutral focus:ring-4 focus:ring-primary/10 outline-none transition-all"
                                placeholder="e.g., EasyBali_VILLA_01"
                                value={profile.wifi_name}
                                onChange={(e) => setProfile({ ...profile, wifi_name: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="text-[10px] font-black text-lightneutral uppercase tracking-widest block mb-2 px-1">Network Password</label>
                            <input
                                type="text"
                                className="w-full bg-secondarywhite/30 border border-gray-100 rounded-2xl px-5 py-4 font-bold text-neutral focus:ring-4 focus:ring-primary/10 outline-none transition-all"
                                placeholder="e.g., bali2026"
                                value={profile.wifi_password}
                                onChange={(e) => setProfile({ ...profile, wifi_password: e.target.value })}
                            />
                        </div>
                    </div>

                    <div className="pt-8 border-t border-gray-50 flex items-center gap-3">
                        <div className="p-3 bg-secondary/10 rounded-2xl text-secondary"><FiLink size={24} /></div>
                        <h2 className="text-xl font-black text-neutral uppercase tracking-tight">Digital <span className="text-secondary">Orientation</span></h2>
                    </div>
                    <div>
                        <label className="text-[10px] font-black text-lightneutral uppercase tracking-widest block mb-2 px-1">Video / Interactive Link</label>
                        <input
                            type="text"
                            className="w-full bg-secondarywhite/30 border border-gray-100 rounded-2xl px-5 py-4 font-bold text-neutral focus:ring-4 focus:ring-secondary/10 outline-none transition-all"
                            placeholder="e.g., YouTube Link or Matterport Tour URL"
                            value={profile.orientation_link}
                            onChange={(e) => setProfile({ ...profile, orientation_link: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="text-[10px] font-black text-lightneutral uppercase tracking-widest block mb-2 px-1">Review Link (Google / Airbnb / TripAdvisor)</label>
                        <input
                            type="text"
                            className="w-full bg-secondarywhite/30 border border-gray-100 rounded-2xl px-5 py-4 font-bold text-neutral focus:ring-4 focus:ring-secondary/10 outline-none transition-all"
                            placeholder="e.g., https://g.page/r/your-villa/review"
                            value={profile.review_link}
                            onChange={(e) => setProfile({ ...profile, review_link: e.target.value })}
                        />
                        <p className="text-[10px] text-lightneutral mt-1 px-1">Sent to guests who rate 4★ or 5★ after checkout.</p>
                    </div>
                    <div>
                        <label className="text-[10px] font-black text-lightneutral uppercase tracking-widest block mb-2 px-1">Directions Link (Google Maps)</label>
                        <input
                            type="text"
                            className="w-full bg-secondarywhite/30 border border-gray-100 rounded-2xl px-5 py-4 font-bold text-neutral focus:ring-4 focus:ring-secondary/10 outline-none transition-all"
                            placeholder="e.g., https://maps.google.com/?q=your+villa"
                            value={profile.maps_link}
                            onChange={(e) => setProfile({ ...profile, maps_link: e.target.value })}
                        />
                        <p className="text-[10px] text-lightneutral mt-1 px-1">Included in the pre-arrival welcome message to help guests find the villa.</p>
                    </div>
                </div>

                {/* Right: Rules & Docs */}
                <div className="bg-white/70 backdrop-blur-xl border border-white rounded-[2.5rem] p-8 shadow-sm space-y-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-3 bg-neutral/10 rounded-2xl text-neutral"><FiFileText size={24} /></div>
                        <h2 className="text-xl font-black text-neutral uppercase tracking-tight">House <span className="text-neutral/60">Rules</span></h2>
                    </div>

                    <textarea
                        className="w-full h-48 bg-secondarywhite/30 border border-gray-100 rounded-2xl px-5 py-4 font-bold text-neutral focus:ring-4 focus:ring-neutral/10 outline-none transition-all resize-none"
                        placeholder="Define property specific rules (smoking, neighbors, trash, pet policy)..."
                        value={profile.house_rules}
                        onChange={(e) => setProfile({ ...profile, house_rules: e.target.value })}
                    ></textarea>

                    <div className="pt-8 border-t border-gray-50 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-primary/10 rounded-2xl text-primary"><FiSettings size={24} /></div>
                            <h2 className="text-xl font-black text-neutral uppercase tracking-tight">Guides & <span className="text-primary">Docs</span></h2>
                        </div>
                        <button onClick={addDocLink} className="p-3 bg-primary text-white rounded-xl hover:scale-105 transition-transform">
                            <FiPlus />
                        </button>
                    </div>

                    <div className="space-y-3">
                        {profile.docs.length === 0 ? (
                            <p className="text-xs font-bold text-lightneutral italic text-center py-4 bg-gray-50/50 rounded-2xl border border-dashed border-gray-200">No documents linked yet. Add guides for appliances etc.</p>
                        ) : (
                            profile.docs.map((doc, idx) => (
                                <div key={idx} className="flex items-center justify-between p-4 bg-white border border-gray-100 rounded-2xl group shadow-sm">
                                    <div className="flex items-center gap-3">
                                        <div className="w-2 h-2 rounded-full bg-primary" />
                                        <p className="font-bold text-sm text-neutral">{doc.title}</p>
                                    </div>
                                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <a href={doc.url} target="_blank" rel="noreferrer" className="p-2 text-primary hover:bg-primary/10 rounded-lg">
                                            <FiLink size={14} />
                                        </a>
                                        <button onClick={() => removeDoc(idx)} className="p-2 text-rose-500 hover:bg-rose-50 rounded-lg">
                                            <FiTrash2 size={14} />
                                        </button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            <div className="bg-neutral p-8 rounded-[3rem] text-white flex flex-col md:flex-row items-center gap-8 shadow-2xl overflow-hidden relative">
                <div className="absolute top-0 right-0 w-64 h-64 bg-primary/20 blur-[100px] -mr-32 -mt-32 rounded-full" />
                <div className="relative z-10 text-center md:text-left">
                    <h3 className="text-2xl font-black uppercase tracking-tight italic">Global Sync <span className="text-primary decoration-primary decoration-4 underline underline-offset-8">Enabled</span></h3>
                    <p className="text-gray-300 mt-2 font-medium max-w-xl">Changes saved here are instantly accessible to the AI Virtual Concierge. Your guests will receive these details upon arrival confirmation and in their welcome pack.</p>
                </div>
                <div className="bg-white/10 backdrop-blur-md px-8 py-6 rounded-3xl border border-white/10">
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-primary mb-2">Current Active Villa</p>
                    <p className="text-3xl font-black tracking-tighter italic">{profile.villa_code || 'ALL_VILLAS'}</p>
                </div>
            </div>
        </div>
    );
};

export default VillaProfile;
