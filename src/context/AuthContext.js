import { createContext, useContext, useState, useCallback, useEffect } from "react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    // Check for session_id in URL hash first
    if (window.location.hash?.includes("session_id=")) {
      setLoading(false);
      return false;
    }

    // Check localStorage for user data (from simplified login)
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setUser(userData);
        setLoading(false);
        return true;
      } catch (error) {
        console.error("Error parsing stored user data:", error);
        localStorage.removeItem("user");
      }
    }

    // Fall back to API check
    try {
      const response = await fetch(`${API}/auth/me`, {
        credentials: "include",
      });

      if (!response.ok) {
        setUser(null);
        setLoading(false);
        return false;
      }

      const userData = await response.json();
      setUser(userData);
      setLoading(false);
      return true;
    } catch (error) {
      setUser(null);
      setLoading(false);
      return false;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await fetch(`${API}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch (error) {
      console.error("Logout error:", error);
    }
    // Clear localStorage and state
    localStorage.removeItem("user");
    setUser(null);
  }, []);

  const setUserData = useCallback((userData) => {
    setUser(userData);
    setLoading(false);
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

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
