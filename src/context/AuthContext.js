import { createContext, useContext, useState, useCallback, useEffect } from "react";
import { auth } from "../lib/firebase";
import { onAuthStateChanged } from "firebase/auth";

// API Configuration
const API = process.env.NODE_ENV === 'production' 
  ? '/api'  // Vercel serverless functions
  : '/api';  // Local development proxy

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  console.log("AuthContext initialized");

  const checkAuth = useCallback(async () => {
    console.log("checkAuth called");
    
    // First check if we already have a user in state
    if (user) {
      console.log("User already in state, authenticated:", user.email);
      return true;
    }

    // Check for session_id in URL hash first (Emergent OAuth flow)
    if (window.location.hash?.includes("session_id=")) {
      setLoading(false);
      return false;
    }

    // Wait for Firebase auth state to be ready
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // Check if there's a session cookie (for returning users)
    console.log("Checking for session cookie...");
    
    const cookies = document.cookie.split(';').map(cookie => cookie.trim());
    console.log("All cookies:", cookies);
    const sessionCookie = cookies.find(cookie => cookie.startsWith('session_token='));
    console.log("Session cookie found:", !!sessionCookie);
    
    if (!sessionCookie) {
      console.log("No session cookie found, user not authenticated");
      setLoading(false);
      return false;
    }

    console.log("Session cookie found, validating...");
    
    // Add delay to ensure cookies are available
    await new Promise(resolve => setTimeout(resolve, 100));
    
    try {
      const response = await fetch(`${API}/auth/me`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json"
        }
      });

      if (response.ok) {
        const userData = await response.json();
        console.log("User data from /auth/me:", userData);
        setUser(userData);
        setLoading(false);
        return true;
      }
    } catch (error) {
      console.log("Session validation failed:", error.message);
    }

    // Firebase auth state listener will handle this for new logins
    setLoading(false);
    return false;
  }, []);

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
    console.log("setUserData called with:", userData);
    setUser(userData);
    setLoading(false);
  }, []);

  const loginWithToken = useCallback(async (idToken, firebaseUser) => {
    console.log("loginWithToken called with:", { idToken: idToken?.substring(0, 10) + "...", email: firebaseUser?.email });
    try {
      const response = await fetch(`${API}/auth/firebase-login`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        credentials: "include",
        body: JSON.stringify({ idToken, firebaseUser }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.log("Login failed:", response.status, errorText);
        throw new Error(`Backend login failed: ${response.status} ${response.statusText}`);
      }

      const userData = await response.json();
      console.log("Login successful, user data:", userData);
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
    console.log("useEffect called");
    // Listen to Firebase auth state changes
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      console.log("Firebase auth state changed:", firebaseUser ? `User: ${firebaseUser.email}` : "No user");
      
      if (firebaseUser) {
        // User is signed in, get ID token and authenticate with backend
        try {
          const idToken = await firebaseUser.getIdToken();
          console.log("Got ID token, calling loginWithToken");
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
        // User is signed out - check if we have a valid session cookie
        console.log("User signed out, checking session...");
        await checkAuth();
      }
    });

    return () => unsubscribe();
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, checkAuth, logout, loginWithToken, setUserData }}>
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
