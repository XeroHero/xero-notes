import { useState } from "react";
import { Button } from "../components/ui/button";
import { signInWithGoogle } from "../lib/firebase";
import { toast } from "sonner";

const SuccessTest = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSuccessTest = async () => {
    setIsLoading(true);
    setResult(null);
    
    try {
      console.log("🔥 Testing authentication success handling...");
      
      // Step 1: Get Google auth
      const { user, idToken } = await signInWithGoogle();
      console.log("✅ Google auth successful");
      
      // Step 2: Backend auth
      const response = await fetch('/api/auth/firebase-login', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ idToken, firebaseUser: user }),
      });
      
      const userData = await response.json();
      console.log("✅ Backend auth successful");
      
      // Step 3: Handle success WITHOUT any complex operations
      setResult({
        success: true,
        message: "🎉 Complete authentication flow successful!",
        userData: userData,
        timestamp: new Date().toISOString()
      });
      
      toast.success("🎉 Authentication test completed successfully!");
      
      // Don't navigate, don't update state, just show success
      console.log("🏁 Test completed - no navigation or state updates");
      
    } catch (error) {
      console.error("❌ Test failed:", error);
      setResult({
        success: false,
        error: error.message,
        timestamp: new Date().toISOString()
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
      border: '2px solid #f59e0b', 
      borderRadius: '8px',
      backgroundColor: '#fffbeb'
    }}>
      <h3>🏁 Success Handler Test</h3>
      <p style={{ fontSize: '14px', color: '#666', marginBottom: '15px' }}>
        Tests the complete authentication flow without navigation or complex state updates
      </p>
      
      <Button 
        onClick={handleSuccessTest} 
        disabled={isLoading}
        style={{ marginBottom: '20px' }}
      >
        {isLoading ? "Testing..." : "Test Success Flow"}
      </Button>
      
      {result && (
        <div style={{ padding: '15px', backgroundColor: 'white', borderRadius: '4px' }}>
          <h4>Results:</h4>
          {result.success ? (
            <div style={{ color: '#059669' }}>
              <p>✅ {result.message}</p>
              <p><strong>Time:</strong> {result.timestamp}</p>
              <details style={{ marginTop: '10px' }}>
                <summary><strong>User Data (click to expand)</strong></summary>
                <pre style={{ fontSize: '12px', backgroundColor: '#f5f5f5', padding: '8px', borderRadius: '4px', marginTop: '8px' }}>
                  {JSON.stringify(result.userData, null, 2)}
                </pre>
              </details>
            </div>
          ) : (
            <div style={{ color: '#dc2626' }}>
              <p>❌ Test failed</p>
              <p><strong>Error:</strong> {result.error}</p>
              <p><strong>Time:</strong> {result.timestamp}</p>
            </div>
          )}
        </div>
      )}
      
      <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
        This test bypasses all navigation and complex state management
      </p>
    </div>
  );
};

export default SuccessTest;
