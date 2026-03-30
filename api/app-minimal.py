from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Xero Notes API running", "version": "1.0.0"}

@app.get("/api/health")
def health():
    return {"status": "healthy", "message": "FastAPI working on Vercel!"}

@app.post("/api/auth/simple-login")
async def simple_login(request):
    try:
        data = await request.json()
        username = data.get('username')
        password = data.get('password')
        
        if username == 'lorenzo_mongo' and password == 'test123':
            return {
                "user_id": "user_test_123",
                "username": "lorenzo_mongo",
                "email": "lorenzo@test.com",
                "message": "Login successful"
            }
        else:
            return {"detail": "Invalid username or password"}
    except:
        return {"detail": "Internal server error"}

@app.post("/api/auth/session")
async def auth_session(request):
    # Mock OAuth session handling
    return {
        "user_id": "user_test_123",
        "username": "lorenzo_mongo",
        "email": "lorenzo@test.com"
    }

@app.get("/api/auth/me")
async def auth_me():
    # Mock current user endpoint
    return {
        "user_id": "user_test_123",
        "username": "lorenzo_mongo",
        "email": "lorenzo@test.com"
    }

@app.post("/api/auth/logout")
async def auth_logout():
    # Mock logout endpoint
    return {"message": "Logged out successfully"}

@app.get("/api/auth/google")
async def auth_google():
    # Mock Google OAuth redirect
    return RedirectResponse(url="/#session_id=mock_google_session_123")

handler = app
