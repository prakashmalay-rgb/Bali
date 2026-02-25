import React, { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import bottomRightPng from "../../assets/images/right-bottom.png";
import topLeftPng from "../../assets/images/top-left.png";
import { getSubMenu } from '../services/api';
import { chatAPI } from "../../api/chatApi"
import { useVoiceToText } from "../../hooks/useVoiceToText";
import { useLanguage } from "../../context/LanguageContext";

const Chat = () => {
  const { language, toggleLanguage, t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("order_services");
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [socket, setSocket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [inputMessage, setInputMessage] = useState("");
  const [loadingItem, setLoadingItem] = useState(null);
  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);
  const [chatType, setChatType] = useState(null);
  const [userId, setUserId] = useState(null);
  const [apiLoading, setApiLoading] = useState(false);

  const { isListening, toggleListening } = useVoiceToText(
    (transcript) => setInputMessage(transcript),
    (finalTranscript) => handleAutoSend(finalTranscript)
  );

  const handleAutoSend = (text) => {
    if (!text.trim()) return;

    // We use a small timeout to ensure state has updated or we just pass the text directly
    // to a new version of handleSendClick that can accept a direct message.
    handleSendClick(text);
  };

  // ✅ NEW: Refs to prevent re-renders and duplicate connections
  const initialMessageProcessed = useRef(false);
  const hasInitialized = useRef(false);
  const isCleaningUp = useRef(false);

  // ✅ NEW: Timeout ref for 120 second auto-close
  const autoCloseTimeoutRef = useRef(null);

  const getCurrentTime = () => {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  // ✅ NEW: Helper functions for WebSocket message persistence
  const saveWebSocketMessages = (sessionId, messages) => {
    try {
      localStorage.setItem(`websocket_chat_${sessionId}`, JSON.stringify(messages));
      console.log("💾 Saved WebSocket messages to localStorage");
    } catch (error) {
      console.error("❌ Error saving WebSocket messages:", error);
    }
  };

  const loadWebSocketMessages = (sessionId) => {
    try {
      const savedMessages = localStorage.getItem(`websocket_chat_${sessionId}`);
      if (savedMessages) {
        const parsedMessages = JSON.parse(savedMessages);
        console.log("📂 Loaded WebSocket messages from localStorage:", parsedMessages.length);
        return parsedMessages;
      }
    } catch (error) {
      console.error("❌ Error loading WebSocket messages:", error);
    }
    return [];
  };

  const clearWebSocketMessages = (sessionId) => {
    try {
      localStorage.removeItem(`websocket_chat_${sessionId}`);
      console.log("🧹 Cleared WebSocket messages from localStorage");
    } catch (error) {
      console.error("❌ Error clearing WebSocket messages:", error);
    }
  };

  // ✅ NEW: Function to close WebSocket gracefully
  const closeWebSocketConnection = (reason = "Manual close") => {
    console.log(`🔌 Closing WebSocket connection: ${reason}`);

    // Clear auto-close timeout
    if (autoCloseTimeoutRef.current) {
      clearTimeout(autoCloseTimeoutRef.current);
      autoCloseTimeoutRef.current = null;
    }

    // Close the socket
    if (socketRef.current) {
      const state = socketRef.current.readyState;
      if (state === WebSocket.OPEN || state === WebSocket.CONNECTING) {
        socketRef.current.close(1000, reason);
      }
      socketRef.current = null;
    }
    setIsConnected(false);
  };

  // ✅ NEW: Start 120-second auto-close timer
  const startAutoCloseTimer = () => {
    // Clear any existing timeout
    if (autoCloseTimeoutRef.current) {
      clearTimeout(autoCloseTimeoutRef.current);
    }

    // Set new 120-second timeout
    autoCloseTimeoutRef.current = setTimeout(() => {
      console.log("⏰ 120 seconds elapsed - auto-closing WebSocket connection");
      closeWebSocketConnection("Auto-close after 120 seconds");
    }, 120000); // 120 seconds = 120000 milliseconds

    console.log("⏱️ Started 120-second auto-close timer");
  };

  const handleMenuClick = (itemId) => {
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
        state: {
          mainMenu: idToEnglish[itemId] || itemId
        }
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
      const currentUserId = chatAPI.getUserId();

      // Reset state for new chat type
      initialMessageProcessed.current = false;
      setChatType(newChatType);
      setUserId(currentUserId);

      // Load history or clear
      const storedMessages = chatAPI.loadChatHistory(currentUserId, newChatType);
      setMessages(storedMessages);
    }
  };

  // ✅ FIXED: Initialize only once on mount
  useEffect(() => {
    // Prevent multiple initializations
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    console.log("=== CHATBOT COMPONENT - RECEIVED VALUES ===");
    console.log("Location state:", location.state);
    console.log("Location key:", location.key);

    initialMessageProcessed.current = false;

    if (location.state?.chatType && location.state?.userId) {
      const currentChatType = location.state.chatType;
      const currentUserId = location.state.userId;

      console.log(`Initializing ${currentChatType} chat for user ${currentUserId}`);
      setChatType(currentChatType);
      setUserId(currentUserId);
      setActiveTab(location.state?.activeTab || "chat_tab");

      if (location.state?.initialBotMessage) {
        const botMsg = location.state.initialBotMessage;
        console.log("🤖 Starting with bot message:", botMsg.text);
        setMessages([botMsg]);
        initialMessageProcessed.current = true;
      }
      else if (location.state?.initialMessage) {
        const initialMsg = location.state.initialMessage;
        console.log("📩 New message from Hero:", initialMsg.text);
        setMessages([initialMsg]);
        initialMessageProcessed.current = false;
      }
      else {
        const storedMessages = chatAPI.loadChatHistory(currentUserId, currentChatType);

        if (storedMessages && storedMessages.length > 0) {
          setMessages(storedMessages);
          console.log("📂 Loaded chat history:", storedMessages.length, "messages");
          initialMessageProcessed.current = true;
        } else {
          setMessages([]);
          console.log("🆕 Starting empty chat");
        }
      }
    }
    // ✅ UPDATED: WebSocket-based order chat with persistence
    else if (location.state?.message && location.state?.sessionId) {
      console.log("📦 WebSocket order chat initialization");
      setChatType('order-service');

      const sessionId = location.state.sessionId;

      // ✅ Load existing WebSocket messages from localStorage
      const savedMessages = loadWebSocketMessages(sessionId);

      if (savedMessages.length > 0) {
        console.log("📂 Restored previous WebSocket chat:", savedMessages.length, "messages");
        setMessages(savedMessages);
      } else {
        const initialMessage = {
          id: Date.now(),
          text: location.state.message,
          sender: "bot",
          timestamp: getCurrentTime(),
        };
        setMessages([initialMessage]);
      }
    } else {
      console.log("No initial state provided");
    }
    console.log("===============================================");
  }, []); // ✅ Empty dependency array - only run once

  // ✅ Auto-send initial message for API-based chats
  useEffect(() => {
    const apiBasedChats = ['what-to-do', 'currency-converter', 'plan-my-trip', 'things-to-do-in-bali', 'general', 'voice-translator', 'passport-submission'];

    if (
      chatType &&
      userId &&
      apiBasedChats.includes(chatType) &&
      !apiLoading &&
      !initialMessageProcessed.current
    ) {
      if (messages.length === 1 && messages[0].sender === 'user') {
        console.log('🚀 Auto-sending initial message to API:', messages[0].text);
        initialMessageProcessed.current = true;
        sendMessageToAPI(messages[0].text);
      } else if (messages.length === 0) {
        console.log('🚀 Auto-starting chat with Hi');
        initialMessageProcessed.current = true;
        sendMessageToAPI("Hi");
      }
    }
  }, [chatType, userId, messages.length, apiLoading]);

  // ✅ Save messages to localStorage for API-based chats
  useEffect(() => {
    const apiBasedChats = ['what-to-do', 'currency-converter', 'plan-my-trip', 'things-to-do-in-bali', 'general', 'voice-translator', 'passport-submission'];
    if (apiBasedChats.includes(chatType) && userId && messages.length > 0) {
      chatAPI.saveChatHistory(userId, chatType, messages);
      console.log("💾 Saved messages to localStorage");
    }
  }, [messages, userId, chatType]);

  // ✅ NEW: Save WebSocket messages to localStorage whenever they change
  useEffect(() => {
    const sessionId = location.state?.sessionId;
    if (chatType === 'order-service' && sessionId && messages.length > 0) {
      saveWebSocketMessages(sessionId, messages);
    }
  }, [messages, chatType, location.state?.sessionId]);

  // ✅ FIXED: WebSocket connection logic
  useEffect(() => {
    const sessionId = location.state?.sessionId;
    const apiBasedChats = ['what-to-do', 'currency-converter', 'plan-my-trip', 'things-to-do-in-bali', 'general', 'voice-translator', 'passport-submission'];

    // Wait for chatType to be set
    if (!chatType) {
      console.log("⏳ Waiting for chat type to be set...");
      return;
    }

    // Only connect WebSocket for order services
    if (sessionId && !apiBasedChats.includes(chatType)) {
      console.log("=== ESTABLISHING WEBSOCKET CONNECTION ===");
      console.log("Session ID:", sessionId);
      console.log("Chat Type:", chatType);

      let ws = null;
      isCleaningUp.current = false;

      const baseUrl = import.meta.env.VITE_BASE_URL;
      if (!baseUrl) {
        console.error("❌ VITE_BASE_URL is not defined in environment variables");
        return;
      }
      const wsUrl = baseUrl.replace(/^http/, 'ws') + `/ws/${sessionId}`;

      console.log("🔗 WebSocket URL:", wsUrl);

      const connectWebSocket = () => {
        if (isCleaningUp.current) {
          console.log("⚠️ Component is cleaning up, skipping connection");
          return;
        }

        try {
          console.log("🔌 Attempting WebSocket connection...");
          ws = new WebSocket(wsUrl);

          ws.onopen = () => {
            if (isCleaningUp.current) return;
            console.log("✅ WebSocket connected successfully");
            setIsConnected(true);

            // ✅ NEW: Start 120-second auto-close timer
            startAutoCloseTimer();
          };

          ws.onmessage = (event) => {
            if (isCleaningUp.current) return;
            console.log("📨 Received WebSocket message:", event.data);

            try {
              const data = JSON.parse(event.data);

              // ✅ NEW: Handle "destroy" type message
              if (data.type === "destroy") {
                console.log("🛑 Received destroy message - closing connection");
                closeWebSocketConnection("Destroy message received");

                // Optional: Clear saved messages when destroy is received
                clearWebSocketMessages(sessionId);
                return;
              }

              const newMessage = {
                id: Date.now(),
                text: data.message || data.text || JSON.stringify(data),
                sender: "bot",
                timestamp: getCurrentTime(),
                type: data.type || "text", // ✅ Store message type
              };
              setMessages((prev) => [...prev, newMessage]);

              // ✅ NEW: Reset the 120-second timer on each message
              startAutoCloseTimer();

            } catch (e) {
              console.error("Error parsing message:", e);
              const newMessage = {
                id: Date.now(),
                text: event.data,
                sender: "bot",
                timestamp: getCurrentTime(),
              };
              setMessages((prev) => [...prev, newMessage]);
            }
          };

          ws.onerror = (error) => {
            if (isCleaningUp.current) return;
            console.error("❌ WebSocket error:", error);
            console.error("WebSocket readyState:", ws?.readyState);
            setIsConnected(false);
          };

          ws.onclose = (event) => {
            if (isCleaningUp.current) return;
            console.log("❌ WebSocket closed:", {
              code: event.code,
              reason: event.reason,
              wasClean: event.wasClean
            });
            setIsConnected(false);

            // ✅ Clear the auto-close timeout when connection closes
            if (autoCloseTimeoutRef.current) {
              clearTimeout(autoCloseTimeoutRef.current);
              autoCloseTimeoutRef.current = null;
            }

            // Auto-reconnect for abnormal closures
            if (event.code !== 1000 && event.code !== 1001 && !isCleaningUp.current) {
              console.log("🔄 Attempting to reconnect in 3 seconds...");
              setTimeout(() => {
                if (!isCleaningUp.current && sessionId) {
                  connectWebSocket();
                }
              }, 3000);
            }
          };

          socketRef.current = ws;
          setSocket(ws);

        } catch (error) {
          console.error("❌ Failed to create WebSocket connection:", error);
          setIsConnected(false);
        }
      };

      connectWebSocket();

      // ✅ Cleanup function
      return () => {
        isCleaningUp.current = true;
        console.log("🧹 Cleaning up WebSocket connection");

        // Clear auto-close timeout
        if (autoCloseTimeoutRef.current) {
          clearTimeout(autoCloseTimeoutRef.current);
          autoCloseTimeoutRef.current = null;
        }

        if (socketRef.current) {
          const state = socketRef.current.readyState;
          if (state === WebSocket.OPEN || state === WebSocket.CONNECTING) {
            socketRef.current.close(1000, "Component unmounting");
          }
          socketRef.current = null;
        }
        setIsConnected(false);
      };
    } else {
      if (!sessionId) {
        console.log("ℹ️ No session ID found, skipping WebSocket");
      } else if (apiBasedChats.includes(chatType)) {
        console.log("ℹ️ API-based chat, skipping WebSocket");
      }
    }
  }, [chatType]); // ✅ Only depend on chatType

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      setApiLoading(true);
      console.log(`📤 Uploading passport image for user ${userId}`);

      // Add optimistic user message for the file
      const userFileMessage = {
        id: Date.now(),
        text: `📸 Uploaded: ${file.name}`,
        sender: "user",
        timestamp: getCurrentTime(),
      };
      setMessages((prev) => [...prev, userFileMessage]);

      // Call API
      const response = await chatAPI.uploadPassport(userId, file);

      const botMessage = {
        id: Date.now() + 1,
        text: response.response,
        sender: "bot",
        timestamp: getCurrentTime(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("❌ Error uploading passport:", error);

      const errorMessage = {
        id: Date.now() + 1,
        text: error.response?.data?.detail || t("upload_error"),
        sender: "bot",
        timestamp: getCurrentTime(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setApiLoading(false);
      event.target.value = null; // reset input
    }
  };

  // ✅ Function to send message to API
  const sendMessageToAPI = async (userMessage) => {
    try {
      setApiLoading(true);
      console.log(`📤 Sending message to ${chatType} endpoint for user ${userId}`);

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

  // ✅ FIXED: Handle send click for both WebSocket and API
  const handleSendClick = (messageOverride) => {
    const textToSend = typeof messageOverride === 'string' ? messageOverride : inputMessage;

    if (!textToSend.trim()) return;

    const newUserMessage = {
      id: Date.now(),
      text: textToSend,
      sender: "user",
      timestamp: getCurrentTime(),
    };

    setMessages((prev) => [...prev, newUserMessage]);

    const apiBasedChats = ['what-to-do', 'currency-converter', 'plan-my-trip', 'things-to-do-in-bali', 'general', 'voice-translator', 'passport-submission'];

    if (apiBasedChats.includes(chatType) && userId) {
      // API-based chat
      console.log("📤 Sending via API");
      sendMessageToAPI(textToSend);
    } else if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      // WebSocket-based chat (Order Services)
      try {
        const payload = JSON.stringify({
          message: textToSend,
          timestamp: getCurrentTime(),
          type: "user_message"
        });
        socketRef.current.send(payload);
        console.log("✅ Sent message via WebSocket:", textToSend);

        // ✅ NEW: Reset the 120-second timer when user sends a message
        startAutoCloseTimer();

      } catch (error) {
        console.error("❌ Error sending WebSocket message:", error);
        const errorMessage = {
          id: Date.now(),
          text: t("connection_error"),
          sender: "bot",
          timestamp: getCurrentTime(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } else {
      console.warn("⚠️ No active connection available");
      const warningMessage = {
        id: Date.now(),
        text: t("connection_error"),
        sender: "bot",
        timestamp: getCurrentTime(),
      };
      setMessages((prev) => [...prev, warningMessage]);
    }

    setInputMessage("");
  };

  const handleServiceSelect = (service) => {
    const confirmMsg = `CONFIRM_BOOKING|${JSON.stringify({
      id: service.id,
      title: service.title,
      price: service.price
    })}`;

    const userMsg = {
      id: Date.now(),
      text: `${t("booking_intent_msg")} ${service.title}`,
      sender: "user",
      timestamp: getCurrentTime(),
    };

    setMessages(prev => [...prev, userMsg]);

    // Then show confirmation
    setTimeout(() => {
      const botMsg = {
        id: Date.now() + 1,
        text: confirmMsg,
        sender: "bot",
        timestamp: getCurrentTime(),
      };
      setMessages(prev => [...prev, botMsg]);
    }, 500);
  };

  const handleConfirmBooking = async (service) => {
    setApiLoading(true);
    try {
      // Add "Confirmed" message from user
      const userMsg = {
        id: Date.now(),
        text: t("confirm_user_msg"),
        sender: "user",
        timestamp: getCurrentTime(),
      };
      setMessages(prev => [...prev, userMsg]);

      // Call API to generate Xendit link
      const response = await chatAPI.createPayment(userId, service);

      const botMsg = {
        id: Date.now() + 1,
        text: response.response,
        sender: "bot",
        timestamp: getCurrentTime(),
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error("Error confirming booking:", err);
      const errorMsg = {
        id: Date.now() + 1,
        text: t("generate_payment_error"),
        sender: "bot",
        timestamp: getCurrentTime(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setApiLoading(false);
    }
  };

  const handleCancelSelection = () => {
    const userMsg = {
      id: Date.now(),
      text: "Cancel selection",
      sender: "user",
      timestamp: getCurrentTime(),
    };
    setMessages(prev => [...prev, userMsg]);

    setTimeout(() => {
      const botMsg = {
        id: Date.now() + 1,
        text: t("selection_cancelled"),
        sender: "bot",
        timestamp: getCurrentTime(),
      };
      setMessages(prev => [...prev, botMsg]);
    }, 500);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSendClick();
    }
  };

  const renderBotMessage = (text) => {
    if (!text || typeof text !== "string") {
      return <span>{t("no_message_error")}</span>;
    }

    // Handle structured services data
    if (text.startsWith("SERVICES_DATA|")) {
      try {
        const data = JSON.parse(text.split("|")[1]);
        return (
          <div className="services-table-container mt-2">
            <p className="mb-3 text-white font-medium">{data.message}</p>
            <div className="overflow-x-auto rounded-xl border border-white/20">
              <table className="min-w-full bg-[#FF8000] text-white text-sm">
                <thead>
                  <tr className="bg-white/10">
                    <th className="px-4 py-2 text-left">{t("service_col")}</th>
                    <th className="px-4 py-2 text-left">{t("price_col")}</th>
                    <th className="px-4 py-2 text-center">{t("action_col")}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.options.map((opt, i) => (
                    <tr key={i} className="border-t border-white/10 hover:bg-white/5 transition-colors">
                      <td className="px-4 py-3">
                        <div className="font-bold">{opt.title}</div>
                        <div className="text-xs text-white/70 line-clamp-1">{opt.description}</div>
                      </td>
                      <td className="px-4 py-3 font-mono">{opt.price}</td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => handleServiceSelect(opt)}
                          className="bg-white text-orange-600 px-3 py-1 rounded-full text-xs font-bold hover:bg-orange-600 hover:text-white transition shadow-sm"
                        >
                          {t("book_btn")}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      } catch (e) {
        console.error("Error parsing services data:", e);
      }
    }

    // Handle Confirmation data
    if (text.startsWith("CONFIRM_BOOKING|")) {
      try {
        const data = JSON.parse(text.split("|")[1]);
        return (
          <div className="confirmation-container mt-2">
            <p className="mb-4 text-white font-medium">
              {t("confirm_booking_desc_prefix")} **{data.title}** {t("confirm_booking_desc_mid")} **IDR {data.price}**.
              {t("confirm_booking_desc_suffix")}
            </p>
            <div className="flex gap-4">
              <button
                onClick={() => handleConfirmBooking(data)}
                className="bg-green-500 text-white px-6 py-2 rounded-full font-bold hover:bg-green-600 transition shadow-md"
              >
                {t("confirm_booking_title")}
              </button>
              <button
                onClick={() => handleCancelSelection()}
                className="bg-red-500 text-white px-6 py-2 rounded-full font-bold hover:bg-red-600 transition shadow-md"
              >
                {t("cancel_btn")}
              </button>
            </div>
          </div>
        );
      } catch (e) {
        console.error("Error parsing confirmation data:", e);
      }
    }

    // Convert escaped newlines to real line breaks
    text = text.replace(/\\n/g, "\n");

    // Split message parts by markdown tokens
    const regex =
      /(\*\*\*[^\*]+\*\*\*|\*\*[^\*]+\*\*|\^\^[^\^]+\^\^|\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|\n)/gi;

    const parts = text.split(regex).filter(Boolean);

    return parts.map((part, index) => {
      if (part === "\n") return <br key={index} />;

      // Bold + large
      if (part.startsWith("***") && part.endsWith("***")) {
        return (
          <span key={index} className="font-bold text-lg">
            {part.slice(3, -3)}
          </span>
        );
      }

      // Bold
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <span key={index} className="font-bold">
            {part.slice(2, -2)}
          </span>
        );
      }

      // Large
      if (part.startsWith("^^") && part.endsWith("^^")) {
        return (
          <span key={index} className="text-lg">
            {part.slice(2, -2)}
          </span>
        );
      }

      // ✅ Handle Markdown-style links
      const linkMatch = part.match(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/i);
      if (linkMatch) {
        const url = linkMatch[2];
        const isPaymentLink = /(xendit|stripe|paypal|checkout|paystack)/i.test(url);
        const isInvoiceLink = /(invoice|receipt|pdf|\.pdf)/i.test(url);

        if (isPaymentLink) {
          return (
            <a
              key={index}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-2 bg-white text-orange-600 font-semibold px-4 py-2 rounded-2xl shadow-md border border-white hover:bg-orange-600 hover:text-white transition"
            >
              💳 {t("pay_now")}
            </a>
          );
        }
        if (isInvoiceLink) {
          return (
            <a
              key={index}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-2 bg-white text-orange-600 font-semibold px-4 py-2 rounded-2xl shadow-md border border-white hover:bg-orange-600 hover:text-white transition"
            >
              📄 {t("download_invoice")}
            </a>
          );
        }

        // For normal links
        return (
          <a
            key={index}
            href={url}
            className="underline text-blue-200"
            target="_blank"
            rel="noopener noreferrer"
          >
            {linkMatch[1]}
          </a>
        );
      }

      // ❌ Skip plain leftover "link" text from Markdown
      if (part.trim() === "link" || part.match(/https?:\/\/[^\s]+/)) {
        return null;
      }

      return <span key={index}>{part}</span>;
    });
  };





  const menuItems = [
    { id: "chat_tab", name: t("chat_tab"), icon: "/chat-icons/today.svg" },
    { id: "order_services", name: t("order_services"), icon: "/chat-icons/order.svg" },
    { id: "local_guide", name: t("local_guide"), icon: "/chat-icons/guide.svg" },
    { id: "voice_translator", name: t("voice_translator"), icon: "/chat-icons/translator.svg" },
    { id: "currency_converter", name: t("currency_converter"), icon: "/chat-icons/currency.svg" },
    { id: "what_to_do", name: t("what_to_do"), icon: "/chat-icons/today.svg" },
    { id: "plan_my_trip", name: t("plan_my_trip"), icon: "/chat-icons/trip.svg" },
    { id: "recommendations", name: t("recommendations"), icon: "/chat-icons/recommend.svg" },
    { id: "discounts_promotions", name: t("discounts_promotions"), icon: "/chat-icons/discount.svg" },
    { id: "passport_submission", name: t("passport_submission"), icon: "/chat-icons/passport.svg" },
  ];

  return (
    <div className="chat relative flex gap-5 p-2 md:p-2 min-h-screen">
      <img
        src={topLeftPng}
        alt="Top Left Icon"
        className="absolute top-[10px] left-[0px] sm:left-[150px] md:left-[270px] w-[350px] sm:w-[200px] md:w-[450px] opacity-60 z-0"
      />
      <img
        src={bottomRightPng}
        alt="Bottom Right Icon"
        className="absolute bottom-0 right-0 w-[390px] sm:w-[250px] md:w-[450px] opacity-60 z-0"
      />
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
      <div
        className={`asidebar flex flex-col gap-10 items-center w-[320px] bg-[#DEDEDE] rounded-[30px] p-5 transition-transform duration-300 ease-in-out
        ${isMobileMenuOpen ? "translate-x-0" : "translate-x-full"}
        md:translate-x-0 md:static fixed top-2 right-2 bottom-2 z-50 md:z-auto
      `}
      >
        <div className="flex justify-between items-center w-full md:justify-center">
          <img
            src="/assets/balilogo.svg"
            alt="Logo"
            className="w-[136px] h-9 cursor-pointer"
            onClick={() => navigate('/')}
          />
          <button
            className="md:hidden p-2"
            onClick={() => setIsMobileMenuOpen(false)}
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div className="flex flex-col w-full">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleMenuClick(item.id)}
              className={`text-[16px] flex items-center justify-start gap-3 font-medium w-full px-4 py-5 rounded-[50px] transition hover:bg-[#FF8000] hover:text-white group shadow-none ${loadingItem === item.id
                ? "opacity-50 cursor-not-allowed"
                : ""
                } ${activeTab === item.id
                  ? "bg-[#FF8000] text-white"
                  : ""
                }`}
              disabled={loadingItem === item.id}
              aria-disabled={loadingItem === item.id}
            >
              <img
                src={item.icon}
                alt={item.name}
                className={`w-5 h-5 transition group-hover:filter group-hover:invert group-hover:brightness-0 ${loadingItem === item.id ? "animate-spin" : ""
                  } ${activeTab === item.id
                    ? "filter invert brightness-0"
                    : ""
                  }`}
              />
              {loadingItem === item.id ? t("loading") : item.name}
            </button>
          ))}
        </div>
      </div>
      <div className="right w-full flex flex-col justify-between relative z-10">
        <div className="header shadow-md flex justify-between items-center w-full h-[84px] lg:h-[97px] p-5 rounded-[50px] bg-white mb-5">
          <div className="flex items-center gap-4">
            <button
              className="md:hidden p-2"
              onClick={() => setIsMobileMenuOpen(true)}
            >
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            </button>
            <h5 className="font-bold text-[18px] md:text-[24px] md:px-6">
              {t("chat_placeholder")}
            </h5>
          </div>
          <div
            className="flex justify-center items-center size-12 md:size-16 rounded-full border-[1px] border-solid border-black cursor-pointer hover:bg-black hover:text-white transition-all"
            onClick={toggleLanguage}
          >
            <h6 className="font-semibold text-sm md:text-base">{language}</h6>
          </div>
        </div>
        <div className="flex flex-col h-[calc(100vh-245px)] overflow-hidden gap-10">
          <div className="messages-container flex-1 overflow-y-auto px-5 z-10">
            <div className="flex flex-col gap-5">
              {messages.map((message) => (
                message.sender === "bot" ? (
                  <div key={message.id} className="flex items-end gap-2">
                    <div className="w-10 h-10 rounded-full bg-[#FF8000] flex items-center justify-center flex-shrink-0">
                      <img
                        src="/assets/ai-chat-icon.png"
                        alt=""
                        className="w-10 h-10"
                      />
                    </div>
                    <div className="flex flex-col bg-[#FF8000] px-7 py-4 rounded-[25px] rounded-bl-none break-words max-w-[85%]">
                      <p className="text-white font-medium leading-relaxed" style={{ whiteSpace: 'pre-line' }}>
                        {renderBotMessage(message.text)}
                      </p>
                      <p className="text-white text-end font-bold text-sm mt-0">
                        {message.timestamp}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div
                    key={message.id}
                    className="flex items-end gap-2 justify-end z-11"
                  >
                    <div className="flex flex-col bg-white px-8 py-4 rounded-[25px] rounded-br-none shadow-md break-words max-w-[85%]">
                      <p className="text-black font-medium">{message.text}</p>
                      <p className="text-gray-500 text-end font-bold text-sm mt-2">
                        {message.timestamp}
                      </p>
                    </div>
                  </div>
                )
              ))}
              {apiLoading && (
                <div className="flex items-end gap-2">
                  <div className="w-10 h-10 rounded-full bg-[#FF8000] flex items-center justify-center flex-shrink-0">
                    <img
                      src="/assets/ai-chat-icon.png"
                      alt=""
                      className="w-10 h-10"
                    />
                  </div>
                  <div className="flex flex-col bg-[#FF8000] px-7 py-4 rounded-[25px] rounded-bl-none">
                    <div className="flex gap-2">
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        </div>
        <div className="px-[10px]">
          <div className="rounded-full bg-white shadow-lg flex px-[20px] sm:px-[40px] py-[20px] items-center justify-between h-[85px] mb-[20px] border-class">
            {chatType === 'passport-submission' && (
              <>
                <input
                  type="file"
                  accept="image/*"
                  id="passport-upload"
                  className="hidden"
                  onChange={handleFileChange}
                />
                <label htmlFor="passport-upload" className={`cursor-pointer mr-3 ${apiLoading ? 'opacity-50 cursor-not-allowed' : ''}`}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-500 hover:text-orange-500 transition">
                    <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                  </svg>
                </label>
              </>
            )}
            <input
              type="text"
              placeholder={t("chat_placeholder")}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={apiLoading}
              className="w-[90%] py-4 sm:py-6 rounded-[50px] text-[#333] text-[16px] sm:text-[18px] placeholder:text-[#8e8e8e] disabled:opacity-50 outline-none"
            />
            <div className="flex items-center gap-4">
              <img
                src="/assets/mic.svg"
                alt="Voice Search"
                onClick={toggleListening}
                className={`cursor-pointer transition-all duration-300 ${isListening ? 'scale-150 mic-glow filter invert sepia(100%) saturate(10000%) hue-rotate(0deg) brightness(100%) contrast(100%)' : ''}`}
              />
              <img
                src="/assets/chat-btn.svg"
                alt=""
                onClick={handleSendClick}
                className={`w-[35px] h-[35px] sm:w-[50px] sm:h-[50px] ${apiLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
                  }`}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;