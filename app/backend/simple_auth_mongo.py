from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import hashlib
import uuid
from datetime import datetime, timezone
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Simple auth with MongoDB
simple_auth_router = APIRouter(prefix="/api/auth")

# Models
class SimpleUserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class SimpleUserLogin(BaseModel):
    username: str
    password: str

class SimpleUser(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None
    created_at: str

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

async def get_user_by_username(username: str) -> Optional[dict]:
    return await db.simple_users.find_one({'username': username})

async def create_user(username: str, password: str, email: Optional[str] = None) -> str:
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "username": username,
        "password_hash": hash_password(password),
        "email": email,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.simple_users.insert_one(user_doc)
    return user_id

# Auth endpoints
@simple_auth_router.post("/simple-signup")
async def simple_signup(user_data: SimpleUserCreate):
    # Check if user already exists in MongoDB
    existing_user = await get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create new user in MongoDB
    user_id = await create_user(user_data.username, user_data.password, user_data.email)
    
    return {"message": "User created successfully", "user_id": user_id}

@simple_auth_router.post("/simple-login")
async def simple_login(login_data: SimpleUserLogin):
    # Find user in MongoDB
    user = await get_user_by_username(login_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Verify password
    if user["password_hash"] != hash_password(login_data.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Return user info (in real app, you'd create a session token)
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "email": user.get("email"),
        "message": "Login successful"
    }

@simple_auth_router.get("/simple-me")
async def simple_me(username: str):
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "email": user.get("email"),
        "created_at": user["created_at"]
    }
