import { useState, useEffect, useRef } from "react";
import { chatAPI } from "../api/chatApi";
import { getSubMenu } from "../components/services/api";

export const useChatLogic = (chatType, userId, t, navigate, setActiveTab, setMessages, messages) => {
    const [isConnected, setIsConnected] = useState(false);
    const [apiLoading, setApiLoading] = useState(false);
    const [loadingItem, setLoadingItem] = useState(null);

    const socketRef = useRef(null);
    const autoCloseTimeoutRef = useRef(null);
    const initialMessageProcessed = useRef(false);
    const isCleaningUp = useRef(false);

    const getCurrentTime = () => {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    };

    const apiBasedChats = [
        'what-to-do',
        'currency-converter',
        'plan-my-trip',
        'things-to-do-in-bali',
        'general',
        'voice-translator',
        'passport-submission'
    ];

    // Logic to handle auto-starting chats
    useEffect(() => {
        if (
            chatType &&
            userId &&
            apiBasedChats.includes(chatType) &&
            !apiLoading &&
            !initialMessageProcessed.current
        ) {
            if (messages.length === 1 && messages[0].sender === 'user') {
                initialMessageProcessed.current = true;
                sendMessageToAPI(messages[0].text);
            } else if (messages.length === 0) {
                initialMessageProcessed.current = true;
                sendMessageToAPI("Hi");
            }
        }
    }, [chatType, userId, messages.length, apiLoading]);

    const sendMessageToAPI = async (userMessage) => {
        try {
            setApiLoading(true);
            const response = await chatAPI.sendMessage(chatType, userId, userMessage);
            const botMessage = {
                id: Date.now(),
                text: response.response,
                sender: "bot",
                timestamp: getCurrentTime(),
            };
            setMessages((prev) => [...prev, botMessage]);
        } catch (error) {
            console.error("❌ Error sending message:", error);
            const errorMessage = {
                id: Date.now(),
                text: error.response?.data?.detail || t("process_error"),
                sender: "bot",
                timestamp: getCurrentTime(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setApiLoading(false);
        }
    };

    const handleMenuClick = (itemId, activeTab) => {
        if (itemId === activeTab && chatType && !['order_services', 'local_guide', 'recommendations', 'discounts_promotions'].includes(itemId)) return;

        const idToEnglish = {
            'order_services': 'Order Services',
            'local_guide': 'Local Guide',
            'recommendations': 'Recommendations',
            'discounts_promotions': 'Discount & Promotions',
            'currency_converter': 'Currency Converter',
            'what_to_do': 'What To Do Today?',
            'plan_my_trip': 'Plan My Trip!',
            'voice_translator': 'Voice Translator',
            'passport_submission': 'Passport Submission'
        };

        const categoryMenus = ['order_services', 'local_guide', 'recommendations', 'discounts_promotions'];
        if (categoryMenus.includes(itemId)) {
            navigate('/categories', {
                state: { mainMenu: idToEnglish[itemId] || itemId }
            });
            return;
        }

        const chatMap = {
            'currency_converter': 'currency-converter',
            'what_to_do': 'what-to-do',
            'plan_my_trip': 'plan-my-trip',
            'voice_translator': 'voice-translator',
            'passport_submission': 'passport-submission'
        };

        const newChatType = chatMap[itemId];
        if (newChatType) {
            setActiveTab(itemId);
            initialMessageProcessed.current = false;
            // Load history
            const storedMessages = chatAPI.loadChatHistory(userId, newChatType);
            setMessages(storedMessages);
            return newChatType; // Component should update its chatType state
        }
        return null;
    };

    return {
        isConnected,
        apiLoading,
        loadingItem,
        setLoadingItem,
        sendMessageToAPI,
        handleMenuClick,
        getCurrentTime,
        socketRef,
        apiBasedChats
    };
};
