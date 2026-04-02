import { useState, useEffect } from "react";

const API = "/api";

const AuthTest = () => {
  const [testResult, setTestResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const testBackend = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API}/auth/test`);
        const data = await response.json();
        setTestResult({
          success: true,
          data,
          status: response.status
        });
      } catch (error) {
        setTestResult({
          success: false,
          error: error.message,
          status: 'Error'
        });
      } finally {
        setLoading(false);
      }
    };

    testBackend();
  }, []);

  if (loading) {
    return <div>Testing backend connection...</div>;
  }

  return (
    <div style={{ 
      padding: '20px', 
      margin: '20px', 
      border: '1px solid #ccc', 
      borderRadius: '8px',
      backgroundColor: '#f9f9f9'
    }}>
      <h3>Backend Connection Test</h3>
      {testResult ? (
        <div>
          <p><strong>Status:</strong> {testResult.status}</p>
          {testResult.success ? (
            <div>
              <p style={{ color: 'green' }}>✅ Backend is accessible!</p>
              <pre>{JSON.stringify(testResult.data, null, 2)}</pre>
            </div>
          ) : (
            <p style={{ color: 'red' }}>❌ Error: {testResult.error}</p>
          )}
        </div>
      ) : null}
    </div>
  );
};

export default AuthTest;
