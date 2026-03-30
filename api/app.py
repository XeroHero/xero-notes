from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Xero Notes API is running", "version": "1.0.0"}

@app.get("/api/health")
def health():
    return {"status": "healthy", "message": "Vercel Python API working!"}

@app.post("/api/auth/simple-login")
async def simple_login(request):
    import json
    data = await request.json()
    username = data.get('username')
    password = data.get('password')
    
    # Hardcoded test user
    if username == 'lorenzo_mongo' and password == 'test123':
        return {
            "user_id": "user_test_123",
            "username": "lorenzo_mongo", 
            "email": "lorenzo@test.com",
            "message": "Login successful"
        }
    else:
        return {"detail": "Invalid username or password"}

# For Vercel, we need to expose the app
handler = app
