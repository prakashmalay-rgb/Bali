import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useVoiceToText } from '../../hooks/useVoiceToText';

const IssueReporting = ({ userId, villaCode }) => {
    const [description, setDescription] = useState('');
    const [priority, setPriority] = useState('medium');
    const [image, setImage] = useState(null);
    const [loading, setLoading] = useState(false);
    
    const { isListening, toggleListening } = useVoiceToText(
        (transcript) => setDescription(transcript),
        () => { } // no auto-send for form
    );

    const handleSubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('user_id', userId);
        formData.append('villa_code', villaCode);
        formData.append('description', description);
        formData.append('priority', priority);
        if (image) formData.append('image', image);

        setLoading(true);
        try {
            await axios.post(`${import.meta.env.VITE_API_URL}/issues/submit`, formData);
            toast.success("Maintenance request sent to villa staff.");
            setDescription('');
            setImage(null);
        } catch (error) {
            toast.error("Failed to submit request.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="issue-report-card p-6 bg-white rounded-xl shadow-lg border border-gray-100">
            <h3 className="text-xl font-semibold mb-4 text-gray-800">🛠️ Report an Issue</h3>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <div className="flex justify-between items-center mb-1">
                        <label className="block text-sm font-medium text-gray-700 font-black uppercase tracking-widest text-[10px]">Description</label>
                        <button
                            type="button"
                            onClick={toggleListening}
                            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase transition-all shadow-sm ${isListening ? 'bg-rose-500 text-white animate-pulse' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                        >
                            {isListening ? (
                                <>🛑 STOP</>
                            ) : (
                                <>🎤 Voice Note</>
                            )}
                        </button>
                    </div>
                    <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        className="w-full p-4 rounded-xl border border-gray-200 min-h-[120px] text-sm focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 outline-none transition-all"
                        placeholder="Leaking AC, broken light bulb, etc."
                        required
                    />
                </div>

                <div className="flex gap-4">
                    <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 font-black uppercase tracking-widest text-[10px] mb-1">Priority</label>
                        <select
                            value={priority}
                            onChange={(e) => setPriority(e.target.value)}
                            className="w-full p-3 rounded-xl border border-gray-200 text-sm font-bold focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 outline-none"
                        >
                            <option value="low">Low (General)</option>
                            <option value="medium">Medium (Annoying)</option>
                            <option value="high">High (Urgent)</option>
                            <option value="urgent">Critical (Safety/Water/Electric)</option>
                        </select>
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 font-black uppercase tracking-widest text-[10px] mb-1">Attachment (Optional)</label>
                    <div className="mt-1 flex items-center gap-4 p-4 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                        <input
                            type="file"
                            onChange={(e) => setImage(e.target.files[0])}
                            className="text-xs text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-black file:uppercase file:bg-white file:text-neutral file:shadow-sm hover:file:bg-gray-100"
                            accept="image/*"
                        />
                    </div>
                </div>

                <button
                    disabled={loading}
                    className={`w-full p-4 rounded-lg text-white font-bold transition-all shadow-md ${loading ? 'bg-gray-400' : 'bg-gradient-to-r from-red-500 to-orange-500 hover:scale-[1.02]'
                        }`}
                >
                    {loading ? 'Submitting...' : 'Send Maintenance Request'}
                </button>
            </form>
        </div>
    );
};

export default IssueReporting;
