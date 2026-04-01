import { useState } from "react";
import { Button } from "../components/ui/button";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { signInWithGoogle } from "../lib/firebase";
import { toast } from "sonner";

const LoginPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { loginWithToken } = useAuth();

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    try {
      const { user, idToken } = await signInWithGoogle();
      
      // Send token to backend for session creation
      await loginWithToken(idToken, user);
      
      toast.success("Welcome back!");
      navigate("/dashboard");
    } catch (error) {
      console.error("Google login error:", error);
      toast.error(error.code === "auth/popup-closed-by-user" 
        ? "Sign-in cancelled" 
        : "Failed to sign in with Google");
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background Image */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1670893494981-cd78dcf87cf4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2OTV8MHwxfHNlYXJjaHwyfHxhYnN0cmFjdCUyMHNvZnQlMjBwYXBlciUyMHRleHR1cmUlMjBsaWdodHxlbnwwfHx8fDE3NzQ1MzY1NDJ8MA&ixlib=rb-4.1.0&q=85')`
        }}
      />

      {/* Glassmorphism Overlay */}
      <div className="absolute inset-0 bg-white/70 backdrop-blur-md" />

      {/* Content */}
      <div className="relative z-10 min-h-screen flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          {/* Logo & Title */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#E06A4F] mb-4 shadow-lg">
              <svg className="w-8 h-8 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <h1 className="font-heading text-4xl font-semibold tracking-tight text-[#1C1917] mb-2">
              Xero Notes
            </h1>
            <p className="text-[#78716C] font-body text-lg">
              Your thoughts, beautifully organized
            </p>
          </div>

          {/* Login Card */}
          <div
            className="bg-white/80 backdrop-blur-xl rounded-2xl p-8 shadow-xl border border-[#E7E5E4]"
            data-testid="login-card"
          >
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="font-heading text-xl font-medium text-[#1C1917] mb-2">
                  Welcome back
                </h2>
                <p className="text-[#78716C] font-body text-sm">
                  Sign in to access your notes from anywhere
                </p>
              </div>

              <Button
                onClick={handleGoogleLogin}
                disabled={isLoading}
                className="w-full h-12 bg-[#E06A4F] hover:bg-[#C95A41] text-white rounded-full font-body font-medium text-base transition-all duration-200 shadow-md hover:shadow-lg"
                data-testid="google-login-button"
              >
                {isLoading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                ) : (
                  <>
                    <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                      <path
                        fill="currentColor"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="currentColor"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="currentColor"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      />
                      <path
                        fill="currentColor"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      />
                    </svg>
                    Continue with Google
                  </>
                )}
              </Button>

              <div className="text-center text-xs text-[#A8A29E] font-body">
                By signing in, you agree to our Terms of Service and Privacy Policy
              </div>
            </div>
          </div>

          {/* Features */}
          <div className="mt-8 grid grid-cols-3 gap-4 text-center">
            <div className="p-3">
              <div className="text-[#E06A4F] mb-1">
                <svg className="w-6 h-6 mx-auto" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
                </svg>
              </div>
              <p className="text-xs text-[#78716C] font-body">Sync Everywhere</p>
            </div>
            <div className="p-3">
              <div className="text-[#E06A4F] mb-1">
                <svg className="w-6 h-6 mx-auto" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
                </svg>
              </div>
              <p className="text-xs text-[#78716C] font-body">Code Highlight</p>
            </div>
            <div className="p-3">
              <div className="text-[#E06A4F] mb-1">
                <svg className="w-6 h-6 mx-auto" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z" />
                </svg>
              </div>
              <p className="text-xs text-[#78716C] font-body">Share Notes</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
