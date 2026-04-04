const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy API requests to the backend
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8001',
      changeOrigin: true,
    })
  );

  // Proxy test endpoint to backend
  app.use(
    '/test',
    createProxyMiddleware({
      target: 'http://localhost:8001',
      changeOrigin: true,
    })
  );
};
