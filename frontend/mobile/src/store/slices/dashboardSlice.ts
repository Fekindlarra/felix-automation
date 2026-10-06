import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface PredictionEvent {
  client_id: number;
  probability: number;
  confidence: number;
  risk_factors: string[];
  positive_factors: string[];
  timestamp: string;
}

interface DashboardState {
  events: PredictionEvent[];
  connectionStatus: "connected" | "disconnected" | "connecting";
  lastUpdate: string | null;
  wsLatency: number;
}

const initialState: DashboardState = {
  events: [],
  connectionStatus: "disconnected",
  lastUpdate: null,
  wsLatency: 0,
};

const dashboardSlice = createSlice({
  name: "dashboard",
  initialState,
  reducers: {
    addEvent: (state, action: PayloadAction<PredictionEvent>) => {
      state.events.unshift(action.payload);
      state.lastUpdate = new Date().toISOString();
      // Keep only last 50 events in memory
      if (state.events.length > 50) {
        state.events.pop();
      }
    },
    setConnectionStatus: (
      state,
      action: PayloadAction<DashboardState["connectionStatus"]>,
    ) => {
      state.connectionStatus = action.payload;
    },
    setWsLatency: (state, action: PayloadAction<number>) => {
      state.wsLatency = action.payload;
    },
    clearEvents: (state) => {
      state.events = [];
    },
  },
});

export const { addEvent, setConnectionStatus, setWsLatency, clearEvents } =
  dashboardSlice.actions;
export default dashboardSlice.reducer;
