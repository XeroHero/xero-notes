from fastapi import APIRouter, HTTPException, Request, Response, Depends
from pydantic import BaseModel
from typing import Optional
import os
from datetime import datetime, timezone, timedelta
import uuid
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
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

# Firebase Admin SDK initialization
firebase_admin_json = os.environ.get('FIREBASE_ADMIN_JSON')
if firebase_admin_json:
    # Use environment variable (Vercel deployment)
    import json
    try:
        # Try to parse as JSON string
        firebase_config = json.loads(firebase_admin_json)
        cred = credentials.Certificate(firebase_config)
        print("Firebase Admin SDK initialized from environment variable")
    except json.JSONDecodeError as e:
        print(f"Failed to parse FIREBASE_ADMIN_JSON: {e}")
        # Try treating it as a file path
        try:
            cred = credentials.Certificate(firebase_admin_json)
            print("Firebase Admin SDK initialized from file path")
        except Exception as file_error:
            print(f"Also failed to load as file: {file_error}")
            raise
else:
    # Use file (local development)
    cred = credentials.Certificate(ROOT_DIR / 'firebase-admin.json')
    print("Firebase Admin SDK initialized from local file")

try:
    firebase_app = firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK initialized successfully")
except Exception as e:
    print(f"Firebase initialization error: {e}")
    # Create a default app if one already exists
    try:
        firebase_app = firebase_admin.get_app()
        print("Using existing Firebase app")
    except:
        firebase_app = None

# Firebase auth router
firebase_auth_router = APIRouter(prefix="/api/auth")

# Models
class FirebaseUser(BaseModel):
    uid: str
    email: str
    displayName: Optional[str] = None
    photoURL: Optional[str] = None

class FirebaseLoginRequest(BaseModel):
    idToken: str
    firebaseUser: FirebaseUser

class User(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    created_at: str

# Helper function to verify Firebase token
async def verify_firebase_token(id_token: str):
    """Verify Firebase ID token and return decoded token"""
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def get_or_create_user(firebase_user: FirebaseUser) -> User:
    """Get existing user or create new one in MongoDB"""
    # Check if user exists by Firebase UID
    existing_user = await db.users.find_one({"firebase_uid": firebase_user.uid}, {"_id": 0})
    
    if existing_user:
        # Update user info
        await db.users.update_one(
            {"firebase_uid": firebase_user.uid},
            {"$set": {
                "email": firebase_user.email,
                "name": firebase_user.displayName,
                "picture": firebase_user.photoURL,
                "last_login": datetime.now(timezone.utc).isoformat()
            }}
        )
        return User(**existing_user)
    
    # Create new user
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "firebase_uid": firebase_user.uid,
        "email": firebase_user.email,
        "name": firebase_user.displayName,
        "picture": firebase_user.photoURL,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    # Create default folder for new user
    default_folder = {
        "folder_id": f"folder_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "name": "My Notes",
        "color": "#E06A4F",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.folders.insert_one(default_folder)
    
    return User(**user_doc)

@firebase_auth_router.post("/firebase-login")
async def firebase_login(request: FirebaseLoginRequest, response: Response):
    """Verify Firebase token and create session"""
    try:
        print(f"Firebase login attempt for user: {request.firebaseUser.email}")
        
        # Verify the Firebase token
        try:
            decoded_token = await verify_firebase_token(request.idToken)
            print(f"Token verified successfully: {decoded_token.get('uid')}")
        except Exception as token_error:
            print(f"Token verification failed: {token_error}")
            raise HTTPException(status_code=401, detail=f"Token verification failed: {str(token_error)}")
        
        # Ensure the token UID matches the provided user UID
        if decoded_token.get('uid') != request.firebaseUser.uid:
            raise HTTPException(status_code=401, detail="Token UID mismatch")
        
        # Get or create user in database
        user = await get_or_create_user(request.firebaseUser)
        print(f"User retrieved/created: {user.user_id}")
        
        # Create session token
        session_token = f"session_{uuid.uuid4().hex[:24]}"
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Store session in MongoDB
        session_doc = {
            "user_id": user.user_id,
            "firebase_uid": request.firebaseUser.uid,
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Remove old sessions for this user
        await db.user_sessions.delete_many({"user_id": user.user_id})
        await db.user_sessions.insert_one(session_doc)
        
        # Set session cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7 * 24 * 60 * 60
        )
        
        print(f"Login successful for user: {user.email}")
        
        return {
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "created_at": user.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Firebase login error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@firebase_auth_router.get("/me")
async def get_current_user(request: Request):
    """Get current authenticated user"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get session from database
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check if session is expired
    expires_at = session_doc.get("expires_at")
    if expires_at:
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expired")
    
    # Get user from database
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Remove sensitive fields
    user_doc.pop("firebase_uid", None)
    
    return user_doc

@firebase_auth_router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout user and invalidate session"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/", samesite="none", secure=True)
    return {"message": "Logged out successfully"}
