import { createContext, useContext, useState, useCallback, useEffect } from "react";
import { auth } from "../lib/firebase";
import { onAuthStateChanged } from "firebase/auth";

const API = "/api";  // Use relative URL to call same-domain backend

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    // Check for session_id in URL hash first (Emergent OAuth flow)
    if (window.location.hash?.includes("session_id=")) {
      setLoading(false);
      return false;
    }

    // Firebase auth state listener will handle this
    setLoading(false);
    return !!user;
  }, [user]);

  const logout = useCallback(async () => {
    try {
      // Logout from Firebase
      await fetch(`${API}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch (error) {
      console.error("Logout error:", error);
    }
    // Clear state
    setUser(null);
  }, []);

  const setUserData = useCallback((userData) => {
    setUser(userData);
    setLoading(false);
  }, []);

  const loginWithToken = useCallback(async (idToken, firebaseUser) => {
    try {
      const response = await fetch(`${API}/auth/firebase-login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ idToken, firebaseUser }),
      });

      if (!response.ok) {
        throw new Error("Backend login failed");
      }

      const userData = await response.json();
      setUser(userData);
      setLoading(false);
      return userData;
    } catch (error) {
      console.error("Login with token error:", error);
      setLoading(false);
      throw error;
    }
  }, []);

  useEffect(() => {
    // Listen to Firebase auth state changes
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        // User is signed in, get ID token and authenticate with backend
        try {
          const idToken = await firebaseUser.getIdToken();
          await loginWithToken(idToken, {
            uid: firebaseUser.uid,
            email: firebaseUser.email,
            displayName: firebaseUser.displayName,
            photoURL: firebaseUser.photoURL,
          });
        } catch (error) {
          console.error("Auth state change error:", error);
          setUser(null);
          setLoading(false);
        }
      } else {
        // User is signed out
        setUser(null);
        setLoading(false);
      }
    });

    return () => unsubscribe();
  }, [loginWithToken]);

  return (
    <AuthContext.Provider value={{ user, loading, checkAuth, logout, setUserData }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
