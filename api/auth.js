module.exports = async (req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  // Handle different routes
  const { url, method } = req;
  
  if (method === 'OPTIONS') {
    res.status(200).end();
    return;
  }
  
  if (url === '/api/auth/simple-login' && method === 'POST') {
    try {
      const body = JSON.parse(req.body);
      const { username, password } = body;
      
      // Hardcoded test user
      if (username === 'lorenzo_mongo' && password === 'test123') {
        res.status(200).json({
          user_id: 'user_test_123',
          username: 'lorenzo_mongo',
          email: 'lorenzo@test.com',
          message: 'Login successful'
        });
      } else {
        res.status(401).json({ detail: 'Invalid username or password' });
      }
    } catch (error) {
      res.status(500).json({ detail: 'Internal server error' });
    }
  }
  
  // Simple health check
  if (url === '/api/health') {
    res.status(200).json({ status: 'healthy', message: 'Node.js serverless working!' });
  }
  
  // Default response
  res.status(404).json({ detail: 'Endpoint not found' });
};
