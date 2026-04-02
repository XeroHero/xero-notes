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
          console.log(`Testing ${test.name} at ${test.url}`);
          const response = await fetch(test.url);
          console.log(`Response status: ${response.status}`);
          console.log(`Response headers:`, Object.fromEntries(response.headers.entries()));
          
          const text = await response.text();
          console.log(`Response text: ${text}`);
          
          let data;
          try {
            data = JSON.parse(text);
          } catch (e) {
            data = { rawResponse: text };
          }
          
          results[test.name] = {
            success: response.ok,
            data,
            status: response.status,
            headers: Object.fromEntries(response.headers.entries())
          };
        } catch (error) {
          console.error(`Error testing ${test.name}:`, error);
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
      <p style={{ fontSize: '12px', color: '#666', marginBottom: '20px' }}>
        Check browser console (F12) for detailed debugging information
      </p>
      {Object.entries(testResults).map(([testName, result]) => (
        <div key={testName} style={{ marginBottom: '15px', padding: '10px', backgroundColor: 'white', borderRadius: '4px' }}>
          <h4>{testName}</h4>
          <p><strong>Status:</strong> {result.status}</p>
          {result.headers && (
            <details style={{ marginBottom: '10px' }}>
              <summary><strong>Headers:</strong></summary>
              <pre style={{ fontSize: '10px', backgroundColor: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
                {JSON.stringify(result.headers, null, 2)}
              </pre>
            </details>
          )}
          {result.success ? (
            <div>
              <p style={{ color: 'green' }}>✅ Success!</p>
              <pre style={{ fontSize: '12px', backgroundColor: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
                {JSON.stringify(result.data, null, 2)}
              </pre>
            </div>
          ) : (
            <div>
              <p style={{ color: 'red' }}>❌ Error: {result.error}</p>
              {result.data && (
                <pre style={{ fontSize: '12px', backgroundColor: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
                  {JSON.stringify(result.data, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default AuthTest;
