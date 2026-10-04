import axios from 'axios';
import { supabase } from './supabase';

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'https://finmate-backend-bjq1.onrender.com',
});

// Automatically inject Supabase JWT token into outgoing FastAPI requests
API.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default API;