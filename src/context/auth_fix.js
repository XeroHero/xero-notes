// Enhanced session persistence for AuthContext.js
// Replace the existing useEffect with this improved version

useEffect(() => {
  // Listen to Firebase auth state changes
  const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
    if (firebaseUser) {
      // User is signed in, get ID token and authenticate with backend
      try {
        const idToken = await firebaseUser.getIdToken();
        
        // Only login if we're not already in the process of logging in
        if (!user || user.email !== firebaseUser.email) {
          await loginWithToken(idToken, {
            uid: firebaseUser.uid,
            email: firebaseUser.email,
            displayName: firebaseUser.displayName,
            photoURL: firebaseUser.photoURL,
          });
        }
      } catch (error) {
        console.error("Auth state change error:", error);
        setUser(null);
        setLoading(false);
      }
    } else {
      // User is signed out - check for existing session
      const checkExistingSession = async () => {
        try {
          // First try to get current user from backend
          const response = await fetch(`${API}/auth/me`, {
            method: "GET",
            credentials: "include",
            headers: {
              "Content-Type": "application/json"
            }
          });

          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
            setLoading(false);
            return true; // Session found
          }
        } catch (error) {
          // Session check failed
        }
        
        // No session found, clear user state
        setUser(null);
        setLoading(false);
        return false;
      };

      // Only check session if we don't already have a user
      if (!user) {
        await checkExistingSession();
      } else {
        setLoading(false);
      }
    }
  });

  return () => unsubscribe();
}, [user, loginWithToken]);
