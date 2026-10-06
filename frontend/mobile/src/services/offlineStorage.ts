import AsyncStorage from "@react-native-async-storage/async-storage";

/**
 * Offline Storage Manager
 *
 * Caches:
 * - User authentication data
 * - Recent predictions and events
 * - UI state
 * - Pending sync queue
 */

const CACHE_KEYS = {
  AUTH_TOKEN: "@felix:auth_token",
  AUTH_USER: "@felix:auth_user",
  EVENTS: "@felix:events",
  PREDICTIONS: "@felix:predictions",
  LAST_SYNC: "@felix:last_sync",
  SYNC_QUEUE: "@felix:sync_queue",
};

export const setAuthCache = async (token: string, user: any) => {
  try {
    await AsyncStorage.multiSet([
      [CACHE_KEYS.AUTH_TOKEN, token],
      [CACHE_KEYS.AUTH_USER, JSON.stringify(user)],
    ]);
  } catch (error) {
    console.error("Error caching auth:", error);
  }
};

export const getAuthCache = async () => {
  try {
    const [token, userJson] = await AsyncStorage.multiGet([
      CACHE_KEYS.AUTH_TOKEN,
      CACHE_KEYS.AUTH_USER,
    ]);
    return {
      token: token[1],
      user: userJson[1] ? JSON.parse(userJson[1]) : null,
    };
  } catch (error) {
    console.error("Error retrieving auth:", error);
    return { token: null, user: null };
  }
};

export const cacheEvents = async (events: any[]) => {
  try {
    await AsyncStorage.setItem(
      CACHE_KEYS.EVENTS,
      JSON.stringify(events.slice(0, 100)),
    );
    await AsyncStorage.setItem(CACHE_KEYS.LAST_SYNC, new Date().toISOString());
  } catch (error) {
    console.error("Error caching events:", error);
  }
};

export const getCachedEvents = async () => {
  try {
    const data = await AsyncStorage.getItem(CACHE_KEYS.EVENTS);
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error("Error retrieving cached events:", error);
    return [];
  }
};

export const clearCache = async () => {
  try {
    await AsyncStorage.multiRemove(Object.values(CACHE_KEYS));
  } catch (error) {
    console.error("Error clearing cache:", error);
  }
};
