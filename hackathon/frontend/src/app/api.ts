const API_BASE_URL = typeof window !== 'undefined'
    ? (window.location.origin.includes('localhost') ? 'http://localhost:8000' : '')
    : 'http://backend:8000';

interface FetchProps {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
    body?: any;
    isFormData?: boolean;
}

export async function apiRequest(endpoint: string, { method = 'GET', body, isFormData = false }: FetchProps = {}) {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

    const headers: Record<string, string> = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    if (!isFormData) {
        headers['Content-Type'] = 'application/json';
    }

    let finalBody = body;
    if (body && !isFormData) {
        finalBody = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method,
        headers,
        body: finalBody
    });

    if (!response.ok) {
        let errorMsg = 'An unexpected error occurred';
        try {
            const errJson = await response.json();
            errorMsg = errJson.detail || errJson.error || errorMsg;
        } catch (e) {
            // Empty
        }
        throw new Error(errorMsg);
    }

    return response.json();
}
