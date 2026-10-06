import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface SettingsState {
  offlineMode: boolean;
  theme: "light" | "dark" | "system";
  refreshInterval: number; // seconds
  biometricEnabled: boolean;
}

const initialState: SettingsState = {
  offlineMode: false,
  theme: "system",
  refreshInterval: 30,
  biometricEnabled: true,
};

const settingsSlice = createSlice({
  name: "settings",
  initialState,
  reducers: {
    setOfflineMode: (state, action: PayloadAction<boolean>) => {
      state.offlineMode = action.payload;
    },
    setTheme: (state, action: PayloadAction<SettingsState["theme"]>) => {
      state.theme = action.payload;
    },
    setRefreshInterval: (state, action: PayloadAction<number>) => {
      state.refreshInterval = Math.max(5, action.payload);
    },
    setBiometricEnabled: (state, action: PayloadAction<boolean>) => {
      state.biometricEnabled = action.payload;
    },
  },
});

export const {
  setOfflineMode,
  setTheme,
  setRefreshInterval,
  setBiometricEnabled,
} = settingsSlice.actions;
export default settingsSlice.reducer;
