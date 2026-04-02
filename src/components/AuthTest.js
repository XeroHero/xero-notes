import { useState, useEffect } from "react";

const AuthTest = () => {
  const [testResults, setTestResults] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const testEndpoints = async () => {
      const tests = [
        { name: "Root Test", url: "/test" },
        { name: "API Health", url: "/api/health" },
        { name: "Auth Test", url: "/api/auth/test" }
      ];

      const results = {};

      for (const test of tests) {
        try {
          const response = await fetch(test.url);
          const data = await response.json();
          results[test.name] = {
            success: true,
            data,
            status: response.status
          };
        } catch (error) {
          results[test.name] = {
            success: false,
            error: error.message,
            status: 'Error'
          };
        }
      }

      setTestResults(results);
      setLoading(false);
    };

    testEndpoints();
  }, []);

  if (loading) {
    return <div>Testing backend connections...</div>;
  }

  return (
    <div style={{ 
      padding: '20px', 
      margin: '20px', 
      border: '1px solid #ccc', 
      borderRadius: '8px',
      backgroundColor: '#f9f9f9'
    }}>
      <h3>Backend Connection Tests</h3>
      {Object.entries(testResults).map(([testName, result]) => (
        <div key={testName} style={{ marginBottom: '15px', padding: '10px', backgroundColor: 'white', borderRadius: '4px' }}>
          <h4>{testName}</h4>
          <p><strong>Status:</strong> {result.status}</p>
          {result.success ? (
            <div>
              <p style={{ color: 'green' }}>✅ Success!</p>
              <pre style={{ fontSize: '12px', backgroundColor: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
                {JSON.stringify(result.data, null, 2)}
              </pre>
            </div>
          ) : (
            <p style={{ color: 'red' }}>❌ Error: {result.error}</p>
          )}
        </div>
      ))}
    </div>
  );
};

export default AuthTest;
