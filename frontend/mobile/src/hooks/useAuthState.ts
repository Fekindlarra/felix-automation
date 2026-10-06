import { useEffect } from "react";
import { useAppDispatch, useAppSelector, RootState } from "./index";
import { restoreAuth, setLoading } from "../store/slices/authSlice";
import { getAuthCache } from "../services/offlineStorage";

/**
 * Hook: Restore auth state from AsyncStorage on app startup
 */
export default function useAuthState() {
  const dispatch = useAppDispatch();
  const { isAuthenticated, isLoading } = useAppSelector(
    (state: RootState) => state.auth,
  );

  useEffect(() => {
    restoreAuthState();
  }, []);

  const restoreAuthState = async () => {
    try {
      const { token, user } = await getAuthCache();
      if (token && user) {
        dispatch(restoreAuth({ token, user }));
      } else {
        dispatch(setLoading(false));
      }
    } catch (error) {
      console.error("Error restoring auth:", error);
      dispatch(setLoading(false));
    }
  };

  return { isAuthenticated, isLoading };
}
