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
      console.log("🔐 loginWithToken called with:", { 
        idToken: idToken.substring(0, 20) + "...", 
        email: firebaseUser.email 
      });
      
      const response = await fetch(`${API}/auth/firebase-login`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        credentials: "include",
        body: JSON.stringify({ idToken, firebaseUser }),
      });

      console.log("📡 Backend response status:", response.status);
      console.log("📡 Backend response headers:", Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.log("❌ Backend error response:", errorText);
        console.log("❌ Response status:", response.status);
        console.log("❌ Response headers:", Object.fromEntries(response.headers.entries()));
        throw new Error(`Backend login failed: ${response.status} ${response.statusText}`);
      }

      const userData = await response.json();
      console.log("📋 User data received:", userData);
      console.log("📋 User data type:", typeof userData);
      console.log("📋 User data keys:", userData ? Object.keys(userData) : "null");

      // Check if userData has any function properties that shouldn't be there
      if (userData && typeof userData === 'object') {
        for (const [key, value] of Object.entries(userData)) {
          if (typeof value === 'function') {
            console.log(`⚠️ Found function property: ${key} =`, value);
          }
        }
      }

      console.log("👤 Setting user state...");
      setUser(userData);
      console.log("✅ User state set successfully");
      
      setLoading(false);
      return userData;
    } catch (error) {
      console.error("❌ Login with token error:", error);
      setLoading(false);
      throw error;
    }
  }, []);

  useEffect(() => {
    // Listen to Firebase auth state changes
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      console.log("🔥 Firebase auth state changed:", firebaseUser?.email || "null");
      
      if (firebaseUser) {
        // User is signed in, get ID token and authenticate with backend
        try {
          const idToken = await firebaseUser.getIdToken();
          console.log("🔐 Got ID token, attempting backend login...");
          
          // Only login if we're not already in the process of logging in
          if (!user || user.email !== firebaseUser.email) {
            await loginWithToken(idToken, {
              uid: firebaseUser.uid,
              email: firebaseUser.email,
              displayName: firebaseUser.displayName,
              photoURL: firebaseUser.photoURL,
            });
            console.log("✅ Backend login completed via auth state listener");
          } else {
            console.log("ℹ️ User already logged in, skipping duplicate login");
          }
        } catch (error) {
          console.error("❌ Auth state change error:", error);
          setUser(null);
          setLoading(false);
        }
      } else {
        // User is signed out
        console.log("👋 User signed out");
        setUser(null);
        setLoading(false);
      }
    });

    return () => unsubscribe();
  }, [loginWithToken, user]);

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
