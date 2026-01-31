import api from './api';

export const AuthService = {
    async register(email, password, display_name) {
        try {
            const response = await api.post('/auth/register', { email, password, display_name });
            return response.data;
        } catch (error) {
            console.error('Registration error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Registration failed');
        }
    },

    async login(email, password) {
        try {
            const response = await api.post('/auth/login', { email, password });
            // The backend sets an httpOnly refresh token cookie, so we only get the access token here
            return response.data; // Should contain { access_token: "...", token_type: "bearer" }
        } catch (error) {
            console.error('Login error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Login failed');
        }
    },

    async logout() {
        try {
            const response = await api.post('/auth/logout');
            return response.data;
        } catch (error) {
            console.error('Logout error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Logout failed');
        }
    },

    // This method will be used by the API interceptor for token refresh
    async refreshToken() {
        try {
            const response = await api.post('/auth/refresh');
            return response.data.access_token; // Should return new access token
        } catch (error) {
            console.error('Token refresh error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Could not refresh token');
        }
    },

    async getCurrentUser() {
        try {
            const response = await api.get('/auth/me');
            return response.data;
        } catch (error) {
            console.error('Get current user error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Could not fetch user info');
        }
    }
};
