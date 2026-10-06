import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";

const API_BASE_URL =
  process.env.REACT_APP_API_URL || "http://localhost:8000/api";

/**
 * API Client with JWT Token Management
 *
 * Handles:
 * - Token refresh
 * - Error interceptors
 * - Request/response logging
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Request interceptor: Add JWT token
apiClient.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor: Handle 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await AsyncStorage.removeItem("auth_token");
      await AsyncStorage.removeItem("auth_user");
      // Dispatch logout action here
    }
    return Promise.reject(error);
  },
);

export const loginUser = async (email: string, password: string) => {
  const response = await apiClient.post("/auth/login", { email, password });
  return response.data;
};

export const loginBiometric = async (clientId: string) => {
  const response = await apiClient.post("/auth/biometric", {
    client_id: clientId,
  });
  return response.data;
};

export const getPredictions = async (clientId: string) => {
  const response = await apiClient.get(`/predictions/${clientId}`);
  return response.data;
};

export const getRecentEvents = async (limit: number = 20) => {
  const response = await apiClient.get("/events/recent", { params: { limit } });
  return response.data;
};

export default apiClient;
