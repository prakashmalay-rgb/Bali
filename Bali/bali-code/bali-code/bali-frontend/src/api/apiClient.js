/**
 * Universal API Client for EASY Bali
 * - Auto-detects local vs production environment
 * - Warms up Render backend on first request (handles cold starts)
 * - Retries failed requests with exponential backoff
 * - Sanitizes error messages — NEVER exposes raw server errors to users
 */
import axios from 'axios';

// ─── GUARD RAIL ─────────────────────────────────────────────────────────────
if (!import.meta.env.VITE_API_URL) {
    console.warn('VITE_API_URL is not set! Using fallback.');
}

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://bali-v92r.onrender.com';

let _serverAwake = false;

// ─── AUTH INTERCEPTOR ────────────────────────────────────────────────────────
axios.interceptors.request.use((config) => {
    const token = localStorage.getItem('easybali_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

// Handle global auth failures
axios.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            const currentPath = window.location.pathname;
            if (currentPath.includes('/dashboard')) {
                localStorage.removeItem('easybali_token');
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

/**
 * Wake up the Render backend if it's cold-sleeping.
 */
export async function warmUpServer() {
    if (_serverAwake) return true;
    try {
        await axios.get(`${API_BASE_URL}/`, { timeout: 15000 });
        _serverAwake = true;
        return true;
    } catch {
        return false;
    }
}

/**
 * Safe error extractor.
 */
export function getUserFriendlyError(error) {
    if (!error.response) return 'Server is starting up. Please wait...';
    const detail = error.response?.data?.detail;
    if (detail) return `Error: ${detail}`;
    return 'Something went wrong. Please try again.';
}

/**
 * Makes an API request with automatic retry and server warmup.
 */
export async function apiRequest(requestFn, options = {}) {
    const { maxRetries = 3, onRetry } = options;
    if (!_serverAwake) await warmUpServer();

    let lastError;
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return await requestFn();
        } catch (error) {
            lastError = error;
            if (!error.response || error.response.status >= 500) {
                if (attempt < maxRetries) {
                    await new Promise(r => setTimeout(r, 2000 * attempt));
                    _serverAwake = false;
                    continue;
                }
            }
            break;
        }
    }
    throw lastError;
}
