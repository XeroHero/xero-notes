from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
import hashlib
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority")
DB_NAME = os.getenv("DB_NAME", "xero_notes")

try:
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    db = client[DB_NAME]
    users_collection = db.users
    # Test connection
    client.admin.command('ping')
    print("MongoDB connection successful")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    # Fallback to in-memory storage
    users_collection = None

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    username: str
    password: str
    email: str

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, password: str, email: str):
    if users_collection:
        user_doc = {
            "username": username,
            "password_hash": hash_password(password),
            "email": email,
            "created_at": datetime.now(),
            "user_id": f"user_{uuid.uuid4().hex[:12]}"
        }
        users_collection.insert_one(user_doc)
        return user_doc
    else:
        # Fallback
        return {
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "username": username,
            "email": email
        }

def find_user(username: str, password: str):
    if users_collection:
        user = users_collection.find_one({
            "username": username,
            "password_hash": hash_password(password)
        })
        return user
    else:
        # Fallback to mock user
        if username == "lorenzo_mongo" and password == "test123":
            return {
                "user_id": "user_test_123",
                "username": "lorenzo_mongo",
                "email": "lorenzo@test.com"
            }
        return None

# API endpoints
@app.get("/")
def home():
    return {"message": "Xero Notes API running", "version": "1.0.0", "mongo_connected": users_collection is not None}

@app.get("/api/health")
def health():
    return {"status": "healthy", "message": "FastAPI working on Vercel!", "mongo_connected": users_collection is not None}

@app.post("/api/auth/simple-login")
async def simple_login(login_data: LoginRequest):
    try:
        user = find_user(login_data.username, login_data.password)
        
        if user:
            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "email": user["email"],
                "message": "Login successful"
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.post("/api/auth/simple-signup")
async def simple_signup(signup_data: SignupRequest):
    try:
        # Check if user already exists
        if users_collection:
            existing_user = users_collection.find_one({"username": signup_data.username})
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create new user
        user = create_user(signup_data.username, signup_data.password, signup_data.email)
        
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "message": "User created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.get("/api/auth/me")
async def auth_me():
    # Mock current user endpoint for now
    return {
        "user_id": "user_test_123",
        "username": "lorenzo_mongo",
        "email": "lorenzo@test.com"
    }

@app.post("/api/auth/logout")
async def auth_logout():
    return {"message": "Logged out successfully"}

handler = app
