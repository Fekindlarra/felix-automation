import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createStackNavigator } from "@react-navigation/stack";
import { Provider } from "react-redux";
import { StatusBar } from "expo-status-bar";
import store from "./store";
import AuthScreen from "./screens/AuthScreen";
import DashboardScreen from "./screens/DashboardScreen";
import useAuthState from "./hooks/useAuthState";

const Stack = createStackNavigator();

/**
 * FASE 15 Mobile App Root
 *
 * Track A: React Native + Expo + TypeScript
 * - Authentication (biometric + JWT)
 * - Redux state management
 * - Real-time dashboard via WebSocket
 * - Offline capability with AsyncStorage
 */
function RootNavigator() {
  const { isAuthenticated, isLoading } = useAuthState();

  if (isLoading) {
    return null; // Splash screen handled by Expo
  }

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        animationEnabled: true,
      }}
    >
      {!isAuthenticated ? (
        <Stack.Screen
          name="Auth"
          component={AuthScreen}
          options={{ animationEnabled: false }}
        />
      ) : (
        <Stack.Screen name="Dashboard" component={DashboardScreen} />
      )}
    </Stack.Navigator>
  );
}

export default function App() {
  return (
    <Provider store={store}>
      <StatusBar hidden={false} />
      <NavigationContainer>
        <RootNavigator />
      </NavigationContainer>
    </Provider>
  );
}
