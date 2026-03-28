import React from 'react';

const TestPage = () => {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>Xero Notes - Test Page</h1>
      <p>If you can see this page, the frontend is working!</p>
      <p>Backend URL: {process.env.REACT_APP_BACKEND_URL}</p>
      <p>Current time: {new Date().toLocaleString()}</p>
    </div>
  );
};

export default TestPage;
