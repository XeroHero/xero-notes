from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    try:
        return {"message": "Xero Notes API is running", "version": "1.0.0"}
    except Exception as e:
        logger.error(f"Error in home endpoint: {e}")
        return {"error": str(e)}

@app.get("/api/health")
def health():
    try:
        return {"status": "healthy", "message": "Vercel Python API working!"}
    except Exception as e:
        logger.error(f"Error in health endpoint: {e}")
        return {"error": str(e)}

@app.post("/api/auth/simple-login")
async def simple_login(request):
    try:
        logger.info("Login endpoint called")
        data = await request.json()
        username = data.get('username')
        password = data.get('password')
        
        logger.info(f"Login attempt for user: {username}")
        
        # Hardcoded test user
        if username == 'lorenzo_mongo' and password == 'test123':
            logger.info("Login successful")
            return {
                "user_id": "user_test_123",
                "username": "lorenzo_mongo", 
                "email": "lorenzo@test.com",
                "message": "Login successful"
            }
        else:
            logger.warning(f"Login failed for user: {username}")
            return {"detail": "Invalid username or password"}
            
    except Exception as e:
        logger.error(f"Error in simple_login: {e}")
        return {"detail": f"Internal server error: {str(e)}"}

# For Vercel, we need to expose the app
handler = app
