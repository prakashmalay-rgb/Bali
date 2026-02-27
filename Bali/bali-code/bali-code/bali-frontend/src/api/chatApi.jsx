// src/api/chatApi.js
import axios from 'axios';
import { API_BASE_URL, apiRequest, getUserFriendlyError } from './apiClient';

export const chatAPI = {
  createPayment: async (userId, service, locationZone) => {
    return apiRequest(() =>
      axios.post(`${API_BASE_URL}/chatbot/create-booking-payment`, {
        ...service, user_id: userId, location_zone: locationZone
      }).then(r => r.data)
    );
  },

  sendMessage: async (chatType, userId, query) => {
    const language = localStorage.getItem('language') || 'EN';
    const villaCode = localStorage.getItem('current_villa_code') || 'WEB_VILLA_01';

    return apiRequest(() =>
      axios.post(
        `${API_BASE_URL}/chatbot/generate-response`,
        { query, chat_type: chatType, language, villa_code: villaCode },
        { params: { user_id: userId }, timeout: 30000 }
      ).then(r => r.data)
    );
  },

  uploadPassport: async (userId, file) => {
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('file', file);

    return apiRequest(() =>
      axios.post(`${API_BASE_URL}/chatbot/upload-passport`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000
      }).then(r => r.data)
    );
  },

  uploadAudio: async (audioBlob) => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'audio.webm');

    return apiRequest(() =>
      axios.post(`${API_BASE_URL}/chatbot/upload-audio`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000
      }).then(r => r.data)
    );
  },

  getUserId: () => {
    let userId = localStorage.getItem('userId');
    if (!userId) {
      userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('userId', userId);
    }
    return userId;
  },

  saveChatHistory: (userId, chatType, messages) => {
    const key = `chat_history_${chatType}_${userId}`;
    localStorage.setItem(key, JSON.stringify(messages));
  },

  loadChatHistory: (userId, chatType) => {
    const key = `chat_history_${chatType}_${userId}`;
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : [];
  }
};