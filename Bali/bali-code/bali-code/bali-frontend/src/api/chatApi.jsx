// src/services/chatApi.js
import axios from 'axios';

const API_BASE_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://bali-v92r.onrender.com';

export const chatAPI = {
  createPayment: async (userId, service) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/chatbot/create-booking-payment`,
        { ...service, user_id: userId }
      );
      return response.data;
    } catch (error) {
      console.error("Error creating payment:", error);
      throw error;
    }
  },
  // Send message to specific chat endpoint
  sendMessage: async (chatType, userId, query) => {
    const endpoints = {
      'what-to-do': 'what-to-do/chat',
      'currency-converter': 'currency-converter/chat',
      'plan-my-trip': 'plan-my-trip/chat',
      'voice-translator': 'language_lesson/chat',
      'passport-submission': 'chatbot/generate-response',
      'general': 'chatbot/generate-response',
      'things-to-do-in-bali': "things-to-do-in-bali/chat"
    };

    const endpoint = endpoints[chatType] || endpoints.general;

    try {
      const response = await axios.post(
        `${API_BASE_URL}/${endpoint}`,
        { query, chat_type: chatType },
        { params: { user_id: userId } }
      );
      return response.data;
    } catch (error) {
      console.error(`Error in ${chatType} chat:`, error);
      throw error;
    }
  },

  // Upload Passport
  uploadPassport: async (userId, file) => {
    try {
      const formData = new FormData();
      formData.append('user_id', userId);
      formData.append('file', file);

      const response = await axios.post(
        `${API_BASE_URL}/chatbot/upload-passport`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error uploading passport:', error);
      throw error;
    }
  },

  // Get or create user ID
  getUserId: () => {
    let userId = localStorage.getItem('userId');
    if (!userId) {
      userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('userId', userId);
    }
    return userId;
  },

  // Save chat history
  saveChatHistory: (userId, chatType, messages) => {
    const key = `chat_history_${chatType}_${userId}`;
    localStorage.setItem(key, JSON.stringify(messages));
  },

  // Load chat history
  loadChatHistory: (userId, chatType) => {
    const key = `chat_history_${chatType}_${userId}`;
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : [];
  }
};