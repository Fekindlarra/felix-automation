import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./slices/authSlice";
import dashboardReducer from "./slices/dashboardSlice";
import settingsReducer from "./slices/settingsSlice";

/**
 * Redux Store Configuration
 *
 * Slices:
 * - auth: JWT token, user info, authentication state
 * - dashboard: Real-time prediction data, WebSocket events
 * - settings: App preferences, offline mode
 */
const store = configureStore({
  reducer: {
    auth: authReducer,
    dashboard: dashboardReducer,
    settings: settingsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ["dashboard/setEvents"],
        ignoredPaths: ["dashboard.events"],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;
