import { useEffect, useState, useCallback, useRef } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import { Analytics } from "@vercel/analytics/react";

// Firebase
import { initializeApp, getApps } from "firebase/app";
import { getFirestore, collection, onSnapshot, query, where, orderBy } from "firebase/firestore";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyAKnKY6jqNyGiRR7jQUNCdekaQWH3EqcMg",
  authDomain: "xero-notes.firebaseapp.com",
  projectId: "xero-notes",
  storageBucket: "xero-notes.firebasestorage.app",
  messagingSenderId: "1017234491738",
  appId: "1:1017234491738:web:fbdcafd6b4d2084f658b63",
  measurementId: "G-JB04JNKR3N"
};

// Initialize Firebase
const firebaseApp = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
const firestoreDb = getFirestore(firebaseApp);

// Components
import SimpleAuthDebug from "./components/SimpleAuthDebug";
import TestPage from "./components/TestPage";
import LoginPage from "./pages/LoginPage";
import Dashboard from "./pages/Dashboard";
import SharedNotePage from "./pages/SharedNotePage";

// Auth Context
import { AuthProvider, useAuth } from "./context/AuthContext";

// Auth Callback Component
const AuthCallback = () => {
  const navigate = useNavigate();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      const hash = window.location.hash;
      const sessionIdMatch = hash.match(/session_id=([^&]+)/);
      
      if (!sessionIdMatch) {
        navigate("/login");
        return;
      }

      const sessionId = sessionIdMatch[1];

      try {
        const response = await fetch(`${API}/auth/session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ session_id: sessionId }),
        });

        if (!response.ok) {
          throw new Error("Authentication failed");
        }

        const userData = await response.json();
        // Clear hash and navigate to dashboard with user data
        window.history.replaceState(null, "", window.location.pathname);
        navigate("/dashboard", { state: { user: userData }, replace: true });
      } catch (error) {
        console.error("Auth error:", error);
        toast.error("Authentication failed. Please try again.");
        navigate("/login");
      }
    };

    processAuth();
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F4F0EB]">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#E06A4F] mx-auto"></div>
        <p className="mt-4 text-[#78716C] font-body">Signing you in...</p>
      </div>
    </div>
  );
};

// Protected Route
const ProtectedRoute = ({ children }) => {
  const { user, loading, checkAuth } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // If user data was passed from AuthCallback, skip auth check
    if (location.state?.user) return;
    
    const verify = async () => {
      const isAuthenticated = await checkAuth();
      if (!isAuthenticated) {
        navigate("/login", { replace: true });
      }
    };
    verify();
  }, [checkAuth, navigate, location.state]);

  if (loading && !location.state?.user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F4F0EB]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#E06A4F]"></div>
      </div>
    );
  }

  return children;
};

// App Router
function AppRouter() {
  const location = useLocation();

  // CRITICAL: Check URL fragment synchronously for session_id
  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/test" element={<TestPage />} />
      <Route path="/simple-auth-debug" element={<SimpleAuthDebug />} />
      <Route path="/simple-dashboard" element={<Dashboard firestoreDb={firestoreDb} />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/shared/:shareLink" element={<SharedNotePage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard firestoreDb={firestoreDb} />
          </ProtectedRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Dashboard firestoreDb={firestoreDb} />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <AppRouter />
          <Toaster position="bottom-right" richColors />
        </AuthProvider>
      </BrowserRouter>
      <Analytics />
    </div>
  );
}

export default App;
export { API, firestoreDb };
