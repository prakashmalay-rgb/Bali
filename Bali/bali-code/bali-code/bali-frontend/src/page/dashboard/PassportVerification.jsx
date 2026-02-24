import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FiSearch, FiFileText, FiCheckCircle, FiClock, FiMaximize2, FiX } from 'react-icons/fi';

const API_BASE_URL = 'https://bali-v92r.onrender.com';

const PassportVerification = () => {
    const [passports, setPassports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedPassport, setSelectedPassport] = useState(null);

    useEffect(() => {
        const fetchPassports = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/dashboard-api/passports`);
                if (response.data.success) {
                    setPassports(response.data.passports);
                }
            } catch (error) {
                console.error("Failed to fetch passports:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchPassports();
        const interval = setInterval(fetchPassports, 10000); // Live poll every 10s
        return () => clearInterval(interval);
    }, []);

    const filteredPassports = passports.filter(p =>
        p.guest_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.guest_id.includes(searchTerm)
    );

    const getStatusBadge = (status) => {
        switch (status) {
            case 'pending_verification':
                return (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-orange-50 text-orange-600 border border-orange-100">
                        <FiClock className="w-3.5 h-3.5" />
                        Pending
                    </span>
                );
            case 'verified':
                return (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-600 border border-emerald-100">
                        <FiCheckCircle className="w-3.5 h-3.5" />
                        Verified
                    </span>
                );
            default:
                return (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-gray-50 text-gray-600 border border-gray-100">
                        {status}
                    </span>
                );
        }
    };

    return (
        <div className="flex flex-col space-y-6 font-sans">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-[#0B97EE] bg-clip-text text-transparent">
                        Passport Submissions
                    </h1>
                    <p className="text-sm text-lightneutral mt-1">Review guest passports explicitly submitted via the Concierge upload flow</p>
                </div>
            </div>

            <div className="bg-white/60 backdrop-blur-xl border border-white rounded-[2rem] shadow-sm overflow-hidden">
                <div className="p-6 border-b border-gray-100/50 flex justify-between items-center bg-white/50">
                    <div className="relative w-72">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-lightneutral">
                            <FiSearch />
                        </div>
                        <input
                            type="text"
                            className="block w-full pl-10 pr-4 py-2 bg-white border border-gray-100 rounded-xl text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                            placeholder="Search by Guest Name or ID..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-lightneutral uppercase bg-gray-50/50 border-b border-gray-100/50">
                            <tr>
                                <th className="px-6 py-4 font-semibold">Guest</th>
                                <th className="px-6 py-4 font-semibold">Submission Time</th>
                                <th className="px-6 py-4 font-semibold">Status</th>
                                <th className="px-6 py-4 font-semibold text-right">Review</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50/50">
                            {loading && passports.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="px-6 py-12 text-center text-lightneutral">
                                        <div className="w-6 h-6 border-2 border-primary/20 border-t-primary rounded-full animate-spin mx-auto mb-3"></div>
                                        Fetching secure database...
                                    </td>
                                </tr>
                            ) : filteredPassports.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="px-6 py-12 text-center">
                                        <FiFileText className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                                        <p className="text-darkgrey font-medium">No passport submissions found</p>
                                    </td>
                                </tr>
                            ) : (
                                filteredPassports.map((passport) => (
                                    <tr key={passport.id} className="hover:bg-white/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary/10 to-transparent border border-primary/10 flex items-center justify-center text-primary font-bold">
                                                    {passport.guest_name.charAt(6)}
                                                </div>
                                                <div>
                                                    <p className="font-bold text-neutral">{passport.guest_name}</p>
                                                    <p className="text-[10px] text-lightneutral font-medium">{passport.guest_id.slice(0, 16)}...</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-lightneutral font-medium">
                                            {passport.time}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {getStatusBadge(passport.status)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right">
                                            <button
                                                onClick={() => setSelectedPassport(passport)}
                                                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-primary bg-primary/10 hover:bg-primary hover:text-white rounded-xl transition-colors"
                                            >
                                                <FiMaximize2 /> View Document
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Passport Modal Lightbox */}
            {selectedPassport && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in" onClick={(e) => {
                    if (e.target.id === 'lightbox-bg') setSelectedPassport(null);
                }} id="lightbox-bg">
                    <div className="bg-white rounded-[2rem] shadow-2xl overflow-hidden max-w-4xl w-full flex flex-col max-h-[90vh]">
                        <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                            <div>
                                <h3 className="font-bold text-darkgrey text-lg">{selectedPassport.guest_name}'s Passport</h3>
                                <p className="text-xs text-lightneutral">Submitted on {selectedPassport.time}</p>
                            </div>
                            <button onClick={() => setSelectedPassport(null)} className="p-2 bg-gray-200 hover:bg-red-100 hover:text-red-500 rounded-full transition-colors">
                                <FiX size={20} />
                            </button>
                        </div>
                        <div className="flex-1 overflow-auto bg-[#e5e5e5] p-6 flex items-center justify-center min-h-[400px]">
                            {/* Assuming S3 returns image formats mostly */}
                            <img src={selectedPassport.passport_url} alt="Passport Scan" className="max-w-full max-h-full object-contain rounded-xl shadow-lg" />
                        </div>
                        <div className="p-4 bg-white border-t border-gray-100 flex justify-end gap-3">
                            <button onClick={() => setSelectedPassport(null)} className="px-6 py-2.5 rounded-xl font-semibold text-gray-600 bg-gray-100 hover:bg-gray-200 transition">Close</button>
                            <a href={selectedPassport.passport_url} target="_blank" rel="noopener noreferrer" className="px-6 py-2.5 rounded-xl font-semibold text-white bg-primary hover:bg-[#ff8000] shadow-blue-shadow transition">Download Origin</a>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PassportVerification;
