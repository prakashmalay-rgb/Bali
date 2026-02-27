import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';

const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : (import.meta.env.VITE_API_URL || 'https://bali-v92r.onrender.com');

const PassportSubmission = ({ userId, villaCode }) => {
    const [file, setFile] = useState(null);
    const [fullName, setFullName] = useState('');
    const [loading, setLoading] = useState(false);
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file || !fullName) {
            toast.error("Please provide your name and passport file.");
            return;
        }

        const formData = new FormData();
        formData.append('user_id', userId);
        formData.append('villa_code', villaCode || 'WEB_VILLA_01');
        formData.append('full_name', fullName);
        formData.append('file', file);

        setLoading(true);
        try {
            const response = await axios.post(`${API_BASE_URL}/passports/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                timeout: 30000
            });
            toast.success("✅ Passport uploaded securely!");
            setSubmitted(true);
            setFile(null);
            setFullName('');
        } catch (error) {
            console.error("Passport upload error:", error);
            const detail = error.response?.data?.detail || "Upload failed. Please try again.";
            toast.error(detail);
        } finally {
            setLoading(false);
        }
    };

    if (submitted) {
        return (
            <div className="passport-upload-card p-6 bg-white rounded-xl shadow-lg border border-green-200">
                <div className="text-center py-8">
                    <div className="text-5xl mb-4">✅</div>
                    <h3 className="text-xl font-semibold text-green-700 mb-2">Passport Submitted!</h3>
                    <p className="text-sm text-gray-500 mb-6">
                        Your passport has been securely uploaded and encrypted. The villa staff will verify it shortly.
                    </p>
                    <button
                        onClick={() => setSubmitted(false)}
                        className="text-blue-600 underline text-sm hover:text-blue-800 transition"
                    >
                        Submit another passport
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="passport-upload-card p-6 bg-white rounded-xl shadow-lg border border-gray-100">
            <h3 className="text-xl font-semibold mb-4 text-gray-800">🛂 Secure Passport Submission</h3>
            <p className="text-sm text-gray-500 mb-6 italic">
                Your document is encrypted and accessible only to authorized villa staff.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Full Name (as per Passport)</label>
                    <input
                        type="text"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        className="w-full p-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-blue-500 transition-all"
                        placeholder="John Doe"
                        required
                    />
                </div>

                <div className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
                    <input
                        type="file"
                        id="passport-file"
                        onChange={(e) => setFile(e.target.files[0])}
                        className="hidden"
                        accept=".jpg,.jpeg,.png,.pdf,.webp"
                    />
                    <label htmlFor="passport-file" className="cursor-pointer">
                        {file ? (
                            <span className="text-blue-600 font-medium">{file.name}</span>
                        ) : (
                            <span className="text-gray-400">Click to upload or drag & drop (PDF, JPG, PNG)</span>
                        )}
                    </label>
                </div>

                <button
                    disabled={loading}
                    className={`w-full p-4 rounded-lg text-white font-bold transition-all shadow-md ${loading ? 'bg-gray-400' : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:scale-[1.02]'
                        }`}
                >
                    {loading ? 'Encrypting & Uploading...' : 'Securely Submit Passport'}
                </button>
            </form>
        </div>
    );
};

export default PassportSubmission;
