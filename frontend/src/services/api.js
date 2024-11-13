import axios from 'axios';

const API = axios.create({ baseURL: 'http://localhost:8000/api' });

// Automatically add JWT token for authenticated requests

API.interceptors.requests.use((req) => {
    const token = localStorage.getItem('token');
    if (token) {
        req.headers.Authorization = `Bearer ${token}`;
    }
    return req;
});

// API Calls
export const loginUser = (credentials) => API.post('/auth/login', credentials);
export const signupUser = (userData) => API.post('/auth/signup', userData);
export const getEvents = () => API.get('/events');
export const setEventAlert = (eventID, alertData) => API.post(`/events/${eventId}/alerts`, alertData);