import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { AuthService } from '../services/AuthService';
import { useNavigate } from 'react-router-dom';
import api, { setOnTokenRefreshFailure } from '../services/api'; // Import api and setOnTokenRefreshFailure

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);
    const [accessToken, setAccessToken] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    const logout = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            await AuthService.logout(); // Call backend logout
            localStorage.removeItem('accessToken');
            setAccessToken(null);
            setIsAuthenticated(false);
            setUser(null);
            navigate('/login');
        } catch (err) {
            setError(err.message || 'Logout failed');
            console.error("Logout error:", err);
        } finally {
            setIsLoading(false);
        }
    }, [navigate]); // Add navigate to dependency array

    useEffect(() => {
        setOnTokenRefreshFailure(logout); // Set the logout function as the callback
    }, [logout]);

    useEffect(() => {
        const checkAuthStatus = async () => {
            try {
                const storedAccessToken = localStorage.getItem('accessToken');
                if (storedAccessToken) {
                    setAccessToken(storedAccessToken);
                    // Attempt to fetch user info to validate the token
                    try {
                        const userInfo = await AuthService.getCurrentUser();
                        setUser(userInfo);
                        setIsAuthenticated(true);
                    } catch (fetchError) {
                        console.error("Failed to fetch user info with stored token:", fetchError);
                        logout(); // If token is invalid, log out
                    }
                }
            } catch (err) {
                console.error("Authentication check failed:", err);
                localStorage.removeItem('accessToken');
                setIsAuthenticated(false);
                setUser(null);
            } finally {
                setIsLoading(false);
            }
        };
        checkAuthStatus();
    }, [logout]); // Add logout to dependency array

    const login = async (email, password) => {
        setIsLoading(true);
        setError(null);
        try {
            const { access_token } = await AuthService.login(email, password);
            localStorage.setItem('accessToken', access_token);
            setAccessToken(access_token);
            setIsAuthenticated(true);
            const userInfo = await AuthService.getCurrentUser(); // Fetch user info after login
            setUser(userInfo);
            navigate('/dashboard'); // Redirect to dashboard or home page
        } catch (err) {
            setError(err.message || 'Login failed');
            setIsAuthenticated(false);
            setUser(null);
            console.error("Login error:", err);
            throw err; // Re-throw to allow component to handle
        } finally {
            setIsLoading(false);
        }
    };

    const register = async (email, password, display_name) => {
        setIsLoading(true);
        setError(null);
        try {
            await AuthService.register(email, password, display_name);
            navigate('/login?registered=true');
        } catch (err) {
            setError(err.message || 'Registration failed');
            console.error("Registration error:", err);
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    const value = {
        isAuthenticated,
        user,
        accessToken,
        isLoading,
        error,
        login,
        register,
        logout,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
