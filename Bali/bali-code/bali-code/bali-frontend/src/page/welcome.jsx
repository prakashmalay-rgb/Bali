import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Welcome = () => {
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        const queryParams = new URLSearchParams(location.search);
        const villaCode = queryParams.get('villa');

        if (villaCode) {
            // Save the villa code for RAG context
            localStorage.setItem('current_villa_code', villaCode);
            console.log(`[Welcome Flow] Initializing context for Villa: ${villaCode}`);

            // Generate or fetch user ID
            let userId = localStorage.getItem('userId');
            if (!userId) {
                userId = `guest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                localStorage.setItem('userId', userId);
            }

            // Generate initial bot greeting for the specific villa
            const initialBotMessage = {
                id: Date.now(),
                text: `Welcome to ${villaCode}! I am your EASY Bali AI Concierge. How can I make your stay perfect today?`,
                sender: "assistant",
                timestamp: new Date().toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit"
                })
            };

            // Transition directly into the active chatbot
            setTimeout(() => {
                navigate("/chatbot", {
                    state: {
                        chatType: 'general',
                        userId: userId,
                        activeTab: 'chat_tab',
                        initialBotMessage: initialBotMessage
                    }
                });
            }, 1000); // 1-second delay for a smooth "connecting" experience
        } else {
            // If no villa parameter is provided, just go home
            navigate("/");
        }
    }, [navigate, location]);

    return (
        <div className="min-h-screen bg-[#F4F7FB] flex flex-col items-center justify-center font-sans">
            <div className="w-16 h-16 border-4 border-primary/20 border-t-primary rounded-full animate-spin mb-6" />
            <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-[#0B97EE] bg-clip-text text-transparent mb-2">
                Connecting to your Villa...
            </h1>
            <p className="text-lightneutral text-sm font-medium">Please wait while we initialize your AI Concierge.</p>
        </div>
    );
};

export default Welcome;
