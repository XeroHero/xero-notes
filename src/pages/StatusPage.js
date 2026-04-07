import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { CheckCircle, XCircle, AlertCircle, Database, Server, Globe, Users, Clock } from "lucide-react";

const API = "/api";

const StatusPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [status, setStatus] = useState({
    loading: true,
    checks: {}
  });

  useEffect(() => {
    const runHealthChecks = async () => {
      const checks = {};

      // 1. Database Connection Check
      try {
        const response = await fetch(`${API}/health/db`, {
          method: "GET",
          credentials: "include"
        });
        const data = await response.json();
        checks.database = {
          status: response.ok ? 'healthy' : 'unhealthy',
          message: data.message || (response.ok ? 'Connected' : 'Failed to connect'),
          details: data.details || null,
          responseTime: data.response_time || null
        };
      } catch (error) {
        checks.database = {
          status: 'unhealthy',
          message: 'Connection failed',
          details: error.message
        };
      }

      // 2. API Status Check
      try {
        const startTime = Date.now();
        const response = await fetch(`${API}/health`, {
          method: "GET",
          credentials: "include"
        });
        const endTime = Date.now();
        const data = await response.json();
        checks.api = {
          status: response.ok ? 'healthy' : 'unhealthy',
          message: data.status || 'API responding',
          responseTime: endTime - startTime,
          version: data.version || null,
          uptime: data.uptime || null
        };
      } catch (error) {
        checks.api = {
          status: 'unhealthy',
          message: 'API not responding',
          details: error.message
        };
      }

      // 3. Authentication Check
      try {
        const response = await fetch(`${API}/auth/me`, {
          method: "GET",
          credentials: "include"
        });
        if (response.ok) {
          const userData = await response.json();
          checks.auth = {
            status: 'healthy',
            message: 'Authentication working',
            user: userData.email || 'Authenticated user',
            userId: userData.user_id || null
          };
        } else {
          checks.auth = {
            status: 'warning',
            message: 'Not authenticated',
            details: 'User not logged in'
          };
        }
      } catch (error) {
        checks.auth = {
          status: 'unhealthy',
          message: 'Auth system error',
          details: error.message
        };
      }

      // 4. Firebase Check
      try {
        const response = await fetch(`${API}/health/firebase`, {
          method: "GET",
          credentials: "include"
        });
        const data = await response.json();
        checks.firebase = {
          status: response.ok ? 'healthy' : 'unhealthy',
          message: data.message || (response.ok ? 'Firebase connected' : 'Firebase error'),
          details: data.details || null
        };
      } catch (error) {
        checks.firebase = {
          status: 'unhealthy',
          message: 'Firebase check failed',
          details: error.message
        };
      }

      // 5. Environment Check
      try {
        const response = await fetch(`${API}/health/env`, {
          method: "GET",
          credentials: "include"
        });
        const data = await response.json();
        checks.environment = {
          status: response.ok ? 'healthy' : 'warning',
          message: data.environment || 'Environment loaded',
          platform: data.platform || 'Unknown',
          nodeVersion: data.node_version || null,
          deployment: data.deployment || null
        };
      } catch (error) {
        checks.environment = {
          status: 'warning',
          message: 'Environment check failed',
          details: error.message
        };
      }

      setStatus({
        loading: false,
        checks
      });
    };

    runHealthChecks();
    // Refresh status every 30 seconds
    const interval = setInterval(runHealthChecks, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'unhealthy':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      healthy: 'bg-green-100 text-green-800 border-green-200',
      warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      unhealthy: 'bg-red-100 text-red-800 border-red-200'
    };
    return (
      <Badge className={variants[status] || 'bg-gray-100 text-gray-800 border-gray-200'}>
        {status?.toUpperCase() || 'UNKNOWN'}
      </Badge>
    );
  };

  const overallStatus = () => {
    const values = Object.values(status.checks);
    if (values.length === 0) return 'loading';
    if (values.some(check => check.status === 'unhealthy')) return 'unhealthy';
    if (values.some(check => check.status === 'warning')) return 'warning';
    return 'healthy';
  };

  if (status.loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Running health checks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">System Status</h1>
              <p className="text-gray-600">Monitor the health and performance of Xero Notes</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                {getStatusIcon(overallStatus())}
                <span className="text-sm font-medium">
                  {overallStatus()?.toUpperCase() || 'UNKNOWN'}
                </span>
              </div>
              <Button onClick={() => navigate(-1)} variant="outline">
                Back
              </Button>
            </div>
          </div>
          <div className="text-sm text-gray-500">
            Last updated: {new Date().toLocaleString()} (Auto-refresh every 30s)
          </div>
        </div>

        {/* Status Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {/* Database Status */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Database className="h-4 w-4" />
                Database
              </CardTitle>
              {getStatusBadge(status.checks.database?.status)}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{status.checks.database?.message}</div>
              {status.checks.database?.responseTime && (
                <p className="text-xs text-muted-foreground">
                  Response time: {status.checks.database.responseTime}ms
                </p>
              )}
              {status.checks.database?.details && (
                <p className="text-xs text-muted-foreground mt-1">
                  {status.checks.database.details}
                </p>
              )}
            </CardContent>
          </Card>

          {/* API Status */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Server className="h-4 w-4" />
                API Server
              </CardTitle>
              {getStatusBadge(status.checks.api?.status)}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{status.checks.api?.message}</div>
              {status.checks.api?.responseTime && (
                <p className="text-xs text-muted-foreground">
                  Response time: {status.checks.api.responseTime}ms
                </p>
              )}
              {status.checks.api?.uptime && (
                <p className="text-xs text-muted-foreground">
                  Uptime: {Math.floor(status.checks.api.uptime / 3600)}h
                </p>
              )}
              {status.checks.api?.version && (
                <p className="text-xs text-muted-foreground">
                  Version: {status.checks.api.version}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Authentication Status */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Users className="h-4 w-4" />
                Authentication
              </CardTitle>
              {getStatusBadge(status.checks.auth?.status)}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{status.checks.auth?.message}</div>
              {status.checks.auth?.user && (
                <p className="text-xs text-muted-foreground">
                  User: {status.checks.auth.user}
                </p>
              )}
              {status.checks.auth?.details && (
                <p className="text-xs text-muted-foreground">
                  {status.checks.auth.details}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Firebase Status */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Globe className="h-4 w-4" />
                Firebase
              </CardTitle>
              {getStatusBadge(status.checks.firebase?.status)}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{status.checks.firebase?.message}</div>
              {status.checks.firebase?.details && (
                <p className="text-xs text-muted-foreground">
                  {status.checks.firebase.details}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Environment Status */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Environment
              </CardTitle>
              {getStatusBadge(status.checks.environment?.status)}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{status.checks.environment?.message}</div>
              {status.checks.environment?.platform && (
                <p className="text-xs text-muted-foreground">
                  Platform: {status.checks.environment.platform}
                </p>
              )}
              {status.checks.environment?.deployment && (
                <p className="text-xs text-muted-foreground">
                  Deployment: {status.checks.environment.deployment}
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* API Endpoints */}
        <Card>
          <CardHeader>
            <CardTitle>Available API Endpoints</CardTitle>
            <CardDescription>
              List of all available API endpoints for developers and debugging
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Authentication Endpoints */}
              <div>
                <h4 className="font-semibold text-sm mb-2 text-blue-600">Authentication</h4>
                <ul className="space-y-1 text-xs">
                  <li><code className="bg-gray-100 px-1 rounded">POST /auth/firebase-login</code></li>
                  <li><code className="bg-gray-100 px-1 rounded">GET /auth/me</code></li>
                  <li><code className="bg-gray-100 px-1 rounded">POST /auth/logout</code></li>
                </ul>
              </div>

              {/* Notes Endpoints */}
              <div>
                <h4 className="font-semibold text-sm mb-2 text-green-600">Notes</h4>
                <ul className="space-y-1 text-xs">
                  <li><code className="bg-gray-100 px-1 rounded">GET /api/notes</code></li>
                  <li><code className="bg-gray-100 px-1 rounded">POST /api/notes</code></li>
                  <li><code className="bg-gray-100 px-1 rounded">GET /api/notes/:id</code></li>
                  <li><code className="bg-gray-100 px-1 rounded">PUT /api/notes/:id</code></li>
                  <li><code className="bg-gray-100 px-1 rounded">DELETE /api/notes/:id</code></li>
                  <li><code className="bg-gray-100 px-1 rounded">POST /api/notes/:id/share</code></li>
                </ul>
              </div>

              {/* Folders Endpoints */}
              <div>
                <h4 className="font-semibold text-sm mb-2 text-purple-600">Folders</h4>
                <ul className="space-y-1 text-xs">
                  <li><code className="bg-gray-100 px-1 rounded">GET /api/folders</code></li>
                  <li><code className="bg-gray-100 px-1 rounded">POST /api/folders</code></li>
                  <li><code className="bg-gray-100 px-1 rounded">DELETE /api/folders/:id</code></li>
                </ul>
              </div>

              {/* Shared Notes */}
              <div>
                <h4 className="font-semibold text-sm mb-2 text-orange-600">Shared Notes</h4>
                <ul className="space-y-1 text-xs">
                  <li><code className="bg-gray-100 px-1 rounded">GET /api/shared/:link</code></li>
                </ul>
              </div>

              {/* Health Check Endpoints */}
              <div>
                <h4 className="font-semibold text-sm mb-2 text-red-600">Health Checks</h4>
                <ul className="space-y-1 text-xs">
                  <li><code className="bg-gray-100 px-1 rounded">GET /api/health</code></li>
                  <li><code className="bg-gray-100 px-1 rounded">GET /api/health/db</code></li>
                  <li><code className="bg-gray-100 px-1 rounded">GET /api/health/firebase</code></li>
                  <li><code className="bg-gray-100 px-1 rounded">GET /api/health/env</code></li>
                </ul>
              </div>

              {/* Debug Endpoints */}
              <div>
                <h4 className="font-semibold text-sm mb-2 text-gray-600">Debug</h4>
                <ul className="space-y-1 text-xs">
                  <li><code className="bg-gray-100 px-1 rounded">GET /api/debug/env</code></li>
                  <li><code className="bg-gray-100 px-1 rounded">GET /api/debug/headers</code></li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StatusPage;
