/**
 * Universal API Client for EASY Bali
 * - Auto-detects local vs production environment
 * - Warms up Render backend on first request (handles cold starts)
 * - Retries failed requests with exponential backoff
 * - Sanitizes error messages — NEVER exposes raw server errors to users
 */
import axios from 'axios';

// ─── GUARD RAIL ─────────────────────────────────────────────────────────────
// If VITE_API_URL is missing the app will call the wrong URL and payment links
// will silently fail. This error is intentionally loud.
if (!import.meta.env.VITE_API_URL) {
    console.error(
        '%c⛔ VITE_API_URL is not set! Payment links & all API calls will FAIL.',
        'color:red;font-size:16px;font-weight:bold;',
        '\nCreate bali-frontend/.env with:\n  VITE_API_URL=http://localhost:8000'
    );
}

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://bali-v92r.onrender.com';

let _serverAwake = false;

/**
 * Wake up the Render backend if it's cold-sleeping.
 * Pings the health endpoint and waits for a response.
 */
export async function warmUpServer() {
    if (_serverAwake) return true;
    try {
        await axios.get(`${API_BASE_URL}/`, { timeout: 15000 });
        _serverAwake = true;
        return true;
    } catch {
        // Server might be waking up — we'll retry later
        return false;
    }
}

/**
 * Safe error extractor — never exposes raw server internals.
 */
export function getUserFriendlyError(error) {
    if (!error.response) {
        // Network error / timeout / CORS
        return 'Server is starting up. Please wait a moment and try again.';
    }
    const status = error.response.status;
    const detail = error.response?.data?.detail;

    // TEMPORARY: Expose exact raw backend error for debugging the 500 issue
    if (detail) {
        return `Backend Error: ${detail}`;
    }

    if (status === 422) return 'Please check your input and try again.';
    if (status === 413) return 'File is too large. Maximum allowed is 10MB.';
    if (status === 400) return detail || 'Invalid request. Please check your input.';
    if (status >= 500) return 'Server is experiencing temporary issues. Please try again in a moment.';
    return 'Something went wrong. Please try again.';
}

/**
 * Makes an API request with automatic retry and server warmup.
 * @param {Function} requestFn - A function that returns an axios promise
 * @param {Object} options - { maxRetries, onRetry }
 */
export async function apiRequest(requestFn, options = {}) {
    const { maxRetries = 3, onRetry } = options;

    // Warm up the server before the first real request
    if (!_serverAwake) {
        await warmUpServer();
    }

    let lastError;
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return await requestFn();
        } catch (error) {
            lastError = error;
            const isNetworkError = !error.response;
            const isServerError = error.response?.status >= 500;

            if ((isNetworkError || isServerError) && attempt < maxRetries) {
                const delay = Math.min(2000 * attempt, 6000); // 2s, 4s, 6s
                if (onRetry) onRetry(attempt, maxRetries);
                await new Promise(r => setTimeout(r, delay));
                _serverAwake = false; // Force re-warmup on next attempt
                continue;
            }
            break;
        }
    }
    throw lastError;
}
