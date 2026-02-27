import React, { useState, useRef } from 'react';
import axios from 'axios';
import { API_BASE_URL, warmUpServer, getUserFriendlyError } from '../../api/apiClient';

const PassportSubmission = ({ userId, villaCode }) => {
    const [file, setFile] = useState(null);
    const [fullName, setFullName] = useState('');
    const [loading, setLoading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [statusText, setStatusText] = useState('');
    const [submitted, setSubmitted] = useState(false);
    const [error, setError] = useState('');
    const fileRef = useRef(null);

    const handleFileChange = (e) => {
        const selected = e.target.files[0];
        if (!selected) return;

        const allowed = ['.jpg', '.jpeg', '.png', '.pdf', '.webp'];
        const ext = selected.name.substring(selected.name.lastIndexOf('.')).toLowerCase();
        if (!allowed.includes(ext)) {
            setError('Unsupported file type. Use JPG, PNG, PDF, or WEBP.');
            return;
        }
        if (selected.size > 10 * 1024 * 1024) {
            setError('File too large. Maximum 10MB.');
            return;
        }

        setFile(selected);
        setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!fullName.trim()) {
            setError('Please enter your full name as per passport.');
            return;
        }
        if (!file) {
            setError('Please select a passport file to upload.');
            return;
        }

        setLoading(true);
        setUploadProgress(0);
        setStatusText('Waking up secure server...');

        // Step 1: Warm up the server (handles Render cold-start)
        try {
            await warmUpServer();
        } catch {
            // Continue even if warmup fails — the actual request will retry
        }

        setStatusText('Encrypting & uploading...');

        const formData = new FormData();
        formData.append('user_id', userId || 'web_guest_' + Date.now());
        formData.append('villa_code', villaCode || 'WEB_VILLA_01');
        formData.append('full_name', fullName.trim());
        formData.append('file', file);

        // Step 2: Upload with retry
        const maxRetries = 3;
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                await axios.post(`${API_BASE_URL}/passports/upload`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                    timeout: 60000,
                    onUploadProgress: (progressEvent) => {
                        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        setUploadProgress(percent);
                    }
                });

                // SUCCESS
                setSubmitted(true);
                setLoading(false);
                return;
            } catch (err) {
                console.error(`Passport upload attempt ${attempt}/${maxRetries}:`, err);

                if (attempt < maxRetries) {
                    const isRetryable = !err.response || err.response.status >= 500;
                    if (isRetryable) {
                        setStatusText(`Server warming up... retrying (${attempt}/${maxRetries})`);
                        setUploadProgress(0);
                        await new Promise(r => setTimeout(r, 3000 * attempt));
                        continue;
                    }
                }

                // Final failure — show user-friendly message
                setError(getUserFriendlyError(err));
                setLoading(false);
                return;
            }
        }
    };

    const handleReset = () => {
        setSubmitted(false);
        setFile(null);
        setFullName('');
        setUploadProgress(0);
        setStatusText('');
        setError('');
        if (fileRef.current) fileRef.current.value = '';
    };

    /* ─── SUCCESS STATE ─── */
    if (submitted) {
        return (
            <div style={{
                padding: '32px 24px',
                background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
                borderRadius: '16px',
                border: '1px solid #bbf7d0',
                textAlign: 'center',
                maxWidth: '520px',
                margin: '0 auto'
            }}>
                <div style={{ fontSize: '56px', marginBottom: '12px' }}>✅</div>
                <h3 style={{
                    fontSize: '22px',
                    fontWeight: '700',
                    color: '#166534',
                    marginBottom: '8px'
                }}>Passport Submitted Successfully!</h3>
                <p style={{
                    fontSize: '14px',
                    color: '#4b5563',
                    lineHeight: '1.6',
                    marginBottom: '24px'
                }}>
                    <strong>{fullName}</strong>'s passport has been securely uploaded and encrypted.
                    The villa staff will verify it shortly.
                </p>
                <div style={{
                    background: 'white',
                    borderRadius: '12px',
                    padding: '16px',
                    marginBottom: '20px',
                    border: '1px solid #d1fae5',
                    textAlign: 'left',
                    fontSize: '13px',
                    color: '#374151'
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                        <span style={{ color: '#6b7280' }}>Status</span>
                        <span style={{
                            background: '#fef3c7', color: '#92400e',
                            padding: '2px 10px', borderRadius: '999px',
                            fontWeight: '600', fontSize: '12px'
                        }}>Pending Verification</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#6b7280' }}>Encryption</span>
                        <span style={{ fontWeight: '600', color: '#059669' }}>🔒 Secured</span>
                    </div>
                </div>
                <button onClick={handleReset} style={{
                    background: 'none', border: 'none', color: '#2563eb',
                    textDecoration: 'underline', cursor: 'pointer', fontSize: '14px', fontWeight: '500'
                }}>
                    Submit another passport
                </button>
            </div>
        );
    }

    /* ─── UPLOAD FORM ─── */
    return (
        <div style={{
            padding: '28px 24px',
            background: 'white',
            borderRadius: '16px',
            boxShadow: '0 4px 24px rgba(0,0,0,0.06)',
            border: '1px solid #f3f4f6',
            maxWidth: '520px',
            margin: '0 auto'
        }}>
            <h3 style={{
                fontSize: '20px', fontWeight: '700', color: '#1f2937',
                marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px'
            }}>
                🛂 Secure Passport Submission
            </h3>
            <p style={{
                fontSize: '13px', color: '#9ca3af', fontStyle: 'italic', marginBottom: '24px'
            }}>
                Your document is encrypted and accessible only to authorized villa staff.
            </p>

            <form onSubmit={handleSubmit}>
                {/* Full Name */}
                <div style={{ marginBottom: '16px' }}>
                    <label style={{
                        display: 'block', fontSize: '14px', fontWeight: '500',
                        color: '#374151', marginBottom: '6px'
                    }}>Full Name (as per Passport)</label>
                    <input
                        type="text"
                        value={fullName}
                        onChange={(e) => { setFullName(e.target.value); setError(''); }}
                        placeholder="John Doe"
                        required
                        disabled={loading}
                        style={{
                            width: '100%', padding: '12px 16px', borderRadius: '10px',
                            border: '1px solid #e5e7eb', fontSize: '15px', outline: 'none',
                            boxSizing: 'border-box'
                        }}
                    />
                </div>

                {/* File Upload */}
                <div style={{
                    border: `2px dashed ${file ? '#3b82f6' : '#d1d5db'}`,
                    borderRadius: '12px', padding: '24px 16px', textAlign: 'center',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    marginBottom: '16px', background: file ? '#eff6ff' : '#fafafa'
                }}
                    onClick={() => !loading && fileRef.current?.click()}
                >
                    <input
                        ref={fileRef} type="file"
                        onChange={handleFileChange}
                        style={{ display: 'none' }}
                        accept=".jpg,.jpeg,.png,.pdf,.webp"
                        disabled={loading}
                    />
                    {file ? (
                        <div>
                            <span style={{ fontSize: '24px' }}>📄</span>
                            <p style={{ color: '#2563eb', fontWeight: '600', fontSize: '14px', marginTop: '6px' }}>{file.name}</p>
                            <p style={{ color: '#9ca3af', fontSize: '12px', marginTop: '2px' }}>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                        </div>
                    ) : (
                        <div>
                            <span style={{ fontSize: '28px' }}>📁</span>
                            <p style={{ color: '#9ca3af', fontSize: '14px', marginTop: '6px' }}>Click to upload (PDF, JPG, PNG, WEBP — max 10MB)</p>
                        </div>
                    )}
                </div>

                {/* Error Message */}
                {error && (
                    <div style={{
                        background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '10px',
                        padding: '10px 14px', marginBottom: '16px', color: '#dc2626',
                        fontSize: '13px', fontWeight: '500'
                    }}>
                        ⚠️ {error}
                    </div>
                )}

                {/* Upload Progress */}
                {loading && (
                    <div style={{ marginBottom: '16px' }}>
                        <div style={{
                            display: 'flex', justifyContent: 'space-between',
                            fontSize: '13px', fontWeight: '600', color: '#4b5563', marginBottom: '6px'
                        }}>
                            <span>{statusText}</span>
                            <span>{uploadProgress}%</span>
                        </div>
                        <div style={{
                            width: '100%', height: '8px', background: '#e5e7eb',
                            borderRadius: '999px', overflow: 'hidden'
                        }}>
                            <div style={{
                                width: `${uploadProgress}%`, height: '100%',
                                background: 'linear-gradient(90deg, #3b82f6, #6366f1)',
                                borderRadius: '999px', transition: 'width 0.3s ease'
                            }} />
                        </div>
                    </div>
                )}

                {/* Submit Button */}
                <button
                    type="submit"
                    disabled={loading || !file || !fullName.trim()}
                    style={{
                        width: '100%', padding: '14px', borderRadius: '12px', border: 'none',
                        color: 'white', fontWeight: '700', fontSize: '15px',
                        cursor: (loading || !file || !fullName.trim()) ? 'not-allowed' : 'pointer',
                        background: (loading || !file || !fullName.trim())
                            ? '#9ca3af'
                            : 'linear-gradient(135deg, #2563eb, #4f46e5)',
                        boxShadow: (loading || !file || !fullName.trim())
                            ? 'none'
                            : '0 4px 14px rgba(37,99,235,0.3)',
                        transition: 'all 0.2s'
                    }}
                >
                    {loading ? `Uploading... ${uploadProgress}%` : '🔒 Securely Submit Passport'}
                </button>
            </form>
        </div>
    );
};

export default PassportSubmission;
