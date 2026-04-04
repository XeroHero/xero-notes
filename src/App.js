import { useEffect, useState, useCallback, useRef } from "react";
import "./App.css";
import { HashRouter as Router, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import { Analytics } from "@vercel/analytics/react";

const API = "/api";  // Use relative URL to avoid CORS issues

// Components
import SimpleAuthDebug from "./components/SimpleAuthDebug";
import SimpleDashboard from "./components/SimpleDashboard";
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
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // If user data was passed from AuthCallback, skip auth check
    if (location.state?.user) {
      setIsChecking(false);
      return;
    }
    
    // Quick check - if user already exists, no need to verify
    if (user) {
      setIsChecking(false);
      return;
    }
    
    const verify = async () => {
      const isAuthenticated = await checkAuth();
      if (!isAuthenticated) {
        navigate("/login", { replace: true });
      }
      setIsChecking(false);
    };
    verify();
  }, [user, checkAuth, navigate, location.state]);

  // Show loading while checking authentication or if auth context is loading
  if ((loading || isChecking) && !location.state?.user && !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F4F0EB]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#E06A4F] mx-auto"></div>
          <p className="mt-4 text-[#78716C] font-body">Checking authentication...</p>
        </div>
      </div>
    );
  }

  // If we have user data from state or auth context, render children
  if (location.state?.user || user) {
    return children;
  }

  // This should not be reached due to the redirect above, but as a fallback
  return null;
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
      <Route path="/simple-dashboard" element={<SimpleDashboard />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/shared/:shareLink" element={<SharedNotePage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      {/* Catch all route for 404 handling */}
      <Route path="*" element={
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <h1>404 - Page Not Found</h1>
          <p>The page you're looking for doesn't exist.</p>
          <button 
            onClick={() => window.location.href = '/'}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#E06A4F',
              color: 'white',
              border: 'none',
              borderRadius: '0.25rem',
              cursor: 'pointer'
            }}
          >
            Go Home
          </button>
        </div>
      } />
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <Router>
        <AuthProvider>
          <AppRouter />
          <Toaster position="bottom-right" richColors />
        </AuthProvider>
      </Router>
      <Analytics />
    </div>
  );
}

export default App;
export { API };
