import { useState } from "react";
import { Button } from "../components/ui/button";
import { signInWithGoogle } from "../lib/firebase";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";

const GoogleAuthTest = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const { loginWithToken } = useAuth();

  const handleTestLogin = async () => {
    setIsLoading(true);
    setResult(null);
    
    try {
      console.log("🔥 Step 1: Getting Google sign-in...");
      const { user, idToken } = await signInWithGoogle();
      console.log("✅ Step 1: Got Google user and token", { user: user.email, idToken: idToken.substring(0, 20) + "..." });
      
      console.log("🔐 Step 2: Sending token to backend...");
      const userData = await loginWithToken(idToken, user);
      console.log("✅ Step 2: Backend authentication successful", userData);
      
      setResult({
        success: true,
        user: userData,
        steps: {
          googleSignIn: "✅ Success",
          backendAuth: "✅ Success"
        }
      });
      
      toast.success("Google authentication test successful!");
      
    } catch (error) {
      console.error("❌ Authentication test failed:", error);
      
      setResult({
        success: false,
        error: error.message,
        steps: {
          googleSignIn: error.message.includes("Google") ? "❌ Failed" : "✅ Success",
          backendAuth: error.message.includes("Backend") ? "❌ Failed" : "✅ Success"
        }
      });
      
      toast.error(`Authentication test failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ 
      padding: '20px', 
      margin: '20px', 
      border: '2px solid #4285f4', 
      borderRadius: '8px',
      backgroundColor: '#f8f9fa'
    }}>
      <h3>🔥 Google Authentication Test</h3>
      
      <Button 
        onClick={handleTestLogin} 
        disabled={isLoading}
        style={{ marginBottom: '20px' }}
      >
        {isLoading ? "Testing..." : "Test Google Login"}
      </Button>
      
      {result && (
        <div style={{ padding: '15px', backgroundColor: 'white', borderRadius: '4px' }}>
          <h4>Test Results:</h4>
          <div style={{ marginBottom: '10px' }}>
            <strong>Google Sign-In:</strong> {result.steps.googleSignIn}
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>Backend Auth:</strong> {result.steps.backendAuth}
          </div>
          
          {result.success ? (
            <div style={{ color: 'green' }}>
              <p>✅ Overall: Success!</p>
              <pre style={{ fontSize: '12px', backgroundColor: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
                {JSON.stringify(result.user, null, 2)}
              </pre>
            </div>
          ) : (
            <div style={{ color: 'red' }}>
              <p>❌ Overall: Failed</p>
              <p><strong>Error:</strong> {result.error}</p>
            </div>
          )}
        </div>
      )}
      
      <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
        Check browser console (F12) for detailed step-by-step debugging
      </p>
    </div>
  );
};

export default GoogleAuthTest;
