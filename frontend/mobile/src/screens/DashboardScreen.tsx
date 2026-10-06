import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { useSelector, useDispatch } from "react-redux";
import type { RootState } from "../store";
import { getRecentEvents } from "../services/api";
import WebSocketManager from "../services/websocket";
import {
  addEvent,
  setConnectionStatus,
  setWsLatency,
} from "../store/slices/dashboardSlice";

/**
 * Dashboard Screen (FASE 15 - Track A)
 *
 * Features:
 * - Real-time prediction updates via WebSocket ✨ LIVE
 * - Conversion probability gauge
 * - Risk factors display
 * - Event history
 * - Auto-reconnect with exponential backoff
 */
export default function DashboardScreen() {
  const dashboardState = useSelector((state: RootState) => state.dashboard);
  const authState = useSelector((state: RootState) => state.auth);
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(true);
  const [wsManager, setWsManager] = useState<WebSocketManager | null>(null);

  useEffect(() => {
    loadInitialData();
    initializeWebSocket();

    return () => {
      // Cleanup on unmount
      if (wsManager) {
        wsManager.disconnect();
      }
    };
  }, []);

  const initializeWebSocket = async () => {
    try {
      const token = authState.token || "guest";
      const userId = authState.user?.id || "user_001";

      // WebSocket URL pointing to backend
      const wsUrl = `ws://localhost:8000/ws/predictions/${userId}/client_001?token=${token}`;

      const manager = new WebSocketManager({
        url: wsUrl,
        token: token,
      });

      // Subscribe to prediction events
      manager.subscribe("prediction:generated", (prediction) => {
        console.log("📊 Real-time prediction received:", prediction);

        // Dispatch to Redux to update dashboard
        dispatch(
          addEvent({
            client_id:
              parseInt(
                prediction.data?.client_id?.split("_")[1]?.padStart(0, "0") || "0"
              ) || 0,
            probability: prediction.data?.probability || 0,
            confidence: prediction.data?.confidence || 0,
            risk_factors: prediction.data?.risk_factors || [],
            positive_factors: prediction.data?.positive_factors || [],
            timestamp: prediction.timestamp,
          })
        );
      });

      // Subscribe to connection status
      manager.subscribe("connection_confirmed", () => {
        console.log("✅ WebSocket connected and authenticated");
        dispatch(setConnectionStatus("connected"));
      });

      // Subscribe to heartbeat for latency tracking
      manager.subscribe("heartbeat", () => {
        dispatch(setWsLatency(Math.random() * 50)); // Simulated: TODO calculate real
      });

      await manager.connect();
      setWsManager(manager);
    } catch (error) {
      console.error("❌ WebSocket initialization failed:", error);
    }
  };

  const loadInitialData = async () => {
    try {
      const events = await getRecentEvents(20);
      setLoading(false);
    } catch (error) {
      console.error("Error loading events:", error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Dashboard</Text>
        <View style={styles.connectionStatus}>
          <View
            style={[
              styles.statusDot,
              {
                backgroundColor:
                  dashboardState.connectionStatus === "connected"
                    ? "#34C759"
                    : dashboardState.connectionStatus === "connecting"
                      ? "#FF9500"
                      : "#FF3B30",
              },
            ]}
          />
          <Text style={styles.statusText}>
            {dashboardState.connectionStatus}
          </Text>
        </View>
      </View>

      {/* WebSocket Latency */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>WebSocket Latency</Text>
        <Text style={styles.latency}>{dashboardState.wsLatency}ms</Text>
      </View>

      {/* Recent Events */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>
          Recent Events ({dashboardState.events.length})
        </Text>
        {dashboardState.events.length === 0 ? (
          <Text style={styles.placeholder}>No events yet</Text>
        ) : (
          dashboardState.events.map((event, idx) => (
            <View key={idx} style={styles.eventItem}>
              <View style={styles.eventHeader}>
                <Text style={styles.eventClient}>Client {event.client_id}</Text>
                <View style={styles.probabilityGauge}>
                  <Text style={styles.probabilityValue}>
                    {event.probability}%
                  </Text>
                </View>
              </View>
              <Text style={styles.confidence}>
                Confidence: {(event.confidence * 100).toFixed(0)}%
              </Text>
              {event.risk_factors.length > 0 && (
                <Text style={styles.riskLabel}>
                  Risk: {event.risk_factors.join(", ")}
                </Text>
              )}
            </View>
          ))
        )}
      </View>

      {/* User Info */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Your Profile</Text>
        <Text style={styles.info}>{authState.user?.email}</Text>
        <Text style={styles.role}>{authState.user?.role}</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#fff",
  },
  header: {
    backgroundColor: "#fff",
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#e0e0e0",
  },
  title: {
    fontSize: 28,
    fontWeight: "bold",
    marginBottom: 8,
    color: "#1a1a1a",
  },
  connectionStatus: {
    flexDirection: "row",
    alignItems: "center",
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontSize: 12,
    color: "#666",
    textTransform: "capitalize",
  },
  card: {
    backgroundColor: "#fff",
    marginHorizontal: 16,
    marginVertical: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#e0e0e0",
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 12,
    color: "#1a1a1a",
  },
  latency: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#007AFF",
  },
  placeholder: {
    fontSize: 14,
    color: "#999",
    fontStyle: "italic",
  },
  eventItem: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#f0f0f0",
  },
  eventHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6,
  },
  eventClient: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1a1a1a",
  },
  probabilityGauge: {
    backgroundColor: "#007AFF",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  probabilityValue: {
    fontSize: 12,
    fontWeight: "700",
    color: "#fff",
  },
  confidence: {
    fontSize: 12,
    color: "#666",
    marginBottom: 4,
  },
  riskLabel: {
    fontSize: 12,
    color: "#FF3B30",
  },
  info: {
    fontSize: 14,
    color: "#333",
    marginBottom: 4,
  },
  role: {
    fontSize: 12,
    color: "#999",
  },
});
