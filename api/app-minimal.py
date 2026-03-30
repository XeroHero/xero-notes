from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Pydantic model for login
class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/")
def home():
    return {"message": "Xero Notes API running", "version": "1.0.0"}

@app.get("/api/health")
def health():
    return {"status": "healthy", "message": "FastAPI working on Vercel!"}

@app.post("/api/auth/simple-login")
async def simple_login(login_data: LoginRequest):
    try:
        if login_data.username == 'lorenzo_mongo' and login_data.password == 'test123':
            return {
                "user_id": "user_test_123",
                "username": "lorenzo_mongo",
                "email": "lorenzo@test.com",
                "message": "Login successful"
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.get("/api/auth/google")
async def auth_google():
    # Return a mock session directly instead of redirecting
    return JSONResponse({
        "session_id": "mock_google_session_123",
        "redirect_url": "/#session_id=mock_google_session_123"
    })

@app.post("/api/auth/session")
async def auth_session(request):
    try:
        data = await request.json()
        session_id = data.get('session_id')
        
        # Mock validation - in real OAuth, you'd validate the session_id
        if session_id and session_id.startswith('mock_google_session'):
            return {
                "user_id": "user_test_123",
                "username": "lorenzo_mongo", 
                "email": "lorenzo@test.com"
            }
        else:
            return {"detail": "Invalid session"}
    except Exception as e:
        return {"detail": "Authentication failed"}

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

handler = app
