
Action: file_editor create /app/frontend/src/context/AuthContext.js --file-text "import { createContext, useContext, useState, useCallback, useEffect } from \"react\";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    // CRITICAL: If returning from OAuth callback, skip the /me check.
    // AuthCallback will exchange the session_id and establish the session first.
    if (window.location.hash?.includes(\"session_id=\")) {
      setLoading(false);
      return false;
    }

    try {
      const response = await fetch(`${API}/auth/me`, {
        credentials: \"include\",
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
        method: \"POST\",
        credentials: \"include\",
      });
    } catch (error) {
      console.error(\"Logout error:\", error);
    }
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
    throw new Error(\"useAuth must be used within an AuthProvider\");
  }
  return context;
};
"
Observation: Create successful: /app/frontend/src/context/AuthContext.js