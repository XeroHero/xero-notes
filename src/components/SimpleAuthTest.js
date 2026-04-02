import { useState } from "react";
import { Button } from "../components/ui/button";
import { signInWithGoogle } from "../lib/firebase";
import { toast } from "sonner";

const SimpleAuthTest = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleDirectTest = async () => {
    setIsLoading(true);
    setResult(null);
    
    try {
      console.log("🔥 Step 1: Getting Google sign-in...");
      const { user, idToken } = await signInWithGoogle();
      console.log("✅ Step 1: Got Google user and token", { user: user.email });
      
      console.log("🔐 Step 2: Testing direct backend call...");
      const response = await fetch('/api/auth/firebase-login', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ idToken, firebaseUser: user }),
      });
      
      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}: ${response.statusText}`);
      }
      
      const userData = await response.json();
      console.log("✅ Step 2: Backend authentication successful", userData);
      
      setResult({
        success: true,
        userData,
        message: "Authentication working perfectly!"
      });
      
      toast.success("Direct authentication test successful!");
      
    } catch (error) {
      console.error("❌ Direct test failed:", error);
      
      setResult({
        success: false,
        error: error.message,
        message: "Test failed"
      });
      
      toast.error(`Test failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ 
      padding: '20px', 
      margin: '20px', 
      border: '2px solid #10b981', 
      borderRadius: '8px',
      backgroundColor: '#f0fdf4'
    }}>
      <h3>🧪 Direct Backend Test (No AuthContext)</h3>
      <p style={{ fontSize: '14px', color: '#666', marginBottom: '15px' }}>
        Tests the backend authentication directly without AuthContext interference
      </p>
      
      <Button 
        onClick={handleDirectTest} 
        disabled={isLoading}
        style={{ marginBottom: '20px' }}
      >
        {isLoading ? "Testing..." : "Test Direct Backend Call"}
      </Button>
      
      {result && (
        <div style={{ padding: '15px', backgroundColor: 'white', borderRadius: '4px' }}>
          <h4>Results:</h4>
          {result.success ? (
            <div style={{ color: 'green' }}>
              <p>✅ {result.message}</p>
              <pre style={{ fontSize: '12px', backgroundColor: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
                {JSON.stringify(result.userData, null, 2)}
              </pre>
            </div>
          ) : (
            <div style={{ color: 'red' }}>
              <p>❌ {result.message}</p>
              <p><strong>Error:</strong> {result.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SimpleAuthTest;
