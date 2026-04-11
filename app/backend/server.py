from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timezone, timedelta
import os
import uuid
import json
import httpx
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB imports
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo import ASCENDING, DESCENDING
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False

# Firebase imports
try:
    import firebase_admin
    from firebase_admin import credentials, auth as firebase_auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI()

# Global variables
db = None
client = None
firebase_app = None
session_store = {}
notes_store = {}  # user_id -> list of notes
folders_store = {}  # user_id -> list of folders

# MongoDB connection - disabled for now
print(" MongoDB connection disabled - using memory storage")
db = None
client = None

# Firebase initialization
if FIREBASE_AVAILABLE:
    try:
        firebase_admin_json = os.environ.get('FIREBASE_ADMIN_JSON')
        if firebase_admin_json:
            firebase_config = json.loads(firebase_admin_json)
            cred = credentials.Certificate(firebase_config)
            firebase_app = firebase_admin.initialize_app(cred)
            print(" Firebase Admin SDK initialized")
        else:
            print(" FIREBASE_ADMIN_JSON not found")
            firebase_app = None
    except Exception as e:
        print(f" Firebase initialization failed: {e}")
        firebase_app = None
else:
    firebase_app = None

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy - allow necessary resources
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://www.gstatic.com https://apis.google.com https://vercel.live; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://*.firebaseio.com https://*.googleapis.com https://vercel.live; "
            "frame-src 'self' https://*.google.com; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Other security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"  # Less restrictive than DENY
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS (only in production)
        if os.environ.get("VERCEL_ENV") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

# Add security middleware after class definition
app.add_middleware(SecurityHeadersMiddleware)

# Data models
class User:
    def __init__(self, user_id: str, email: str, name: str = "", picture: str = "", created_at: str = ""):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.picture = picture
        self.created_at = created_at

# Session verification with database support
async def get_current_user(request: Request) -> User:
    session_token = request.cookies.get("session_token")
    print(f"get_current_user called - session_token: {session_token[:8] if session_token else 'None'}")
    print(f"All cookies: {dict(request.cookies)}")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
            print(f"Found token in Authorization header: {session_token[:8] if session_token else 'None'}")
    
    if not session_token:
        print("No session token found in cookies or headers")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # FIRST: Check memory sessions (primary for reliability)
    print(f"Available sessions in memory store: {list(session_store.keys())}")
    if session_token in session_store:
        session_data = session_store[session_token]
        print(f"Found session in memory store for user: {session_data.get('email', 'unknown')}")
        
        # Check if session is expired
        expires_at = session_data.get("expires_at")
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                # Session expired, remove it
                del session_store[session_token]
                print("Session expired and removed")
                raise HTTPException(status_code=401, detail="Session expired")
        
        # Return user from memory store
        print(f"Session valid, returning user: {session_data.get('email', 'unknown')}")
        return User(
            user_id=session_data["user_id"],
            email=session_data["email"],
            name=session_data.get("name", ""),
            picture=session_data.get("picture", ""),
            created_at=session_data.get("created_at", "")
        )
    else:
        print(f"Session token not found in memory store: {session_token}")
    
    # SECOND: Check database sessions (fallback)
    if db is not None:
        try:
            session_doc = await db.user_sessions.find_one({"session_token": session_token})
            if session_doc:
                # Check if session is expired
                expires_at = session_doc.get("expires_at")
                if expires_at:
                    if isinstance(expires_at, str):
                        expires_at = datetime.fromisoformat(expires_at)
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    if expires_at < datetime.now(timezone.utc):
                        # Session expired, remove it
                        await db.user_sessions.delete_one({"session_token": session_token})
                        raise HTTPException(status_code=401, detail="Session expired")
                    else:
                        # Session valid, find user data
                        user_doc = await db.users.find_one({"user_id": session_doc["user_id"]})
                        if user_doc:
                            return User(
                                user_id=user_doc["user_id"],
                                email=user_doc["email"],
                                name=user_doc.get("name", ""),
                                picture=user_doc.get("picture", ""),
                                created_at=user_doc.get("created_at", "")
                            )
        except Exception as e:
            print(f"Database session check failed: {e}")
    
    raise HTTPException(status_code=401, detail="Invalid session")

# Firebase login with database session storage
@app.post("/api/auth/firebase-login")
async def firebase_login(request: Request, response: Response):
    try:
        # Get request body
        body = await request.json()
        idToken = body.get("idToken")
        firebaseUser = body.get("firebaseUser", {})
        
        if not idToken:
            raise HTTPException(status_code=400, detail="Invalid request")
        
        # If Firebase Admin SDK is not available, use the firebaseUser data directly
        if not firebase_app:
            print(" Firebase Admin SDK not available, using client-side user data")
            
            # Create user data from client-side Firebase user
            user_id = f"user_{firebaseUser.get('uid', '')[:12]}"
            email = firebaseUser.get('email', '')
            name = firebaseUser.get('displayName', '')
            picture = firebaseUser.get('photoURL', '')
            
            # Create session token
            session_token = f"session_{uuid.uuid4().hex[:24]}"
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            
            # Store session in memory (fallback)
            session_store[session_token] = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Set session cookie
            print(f" Setting fallback session cookie: {session_token[:8]}...")
            response.set_cookie(
                key="session_token",
                value=session_token,
                expires=expires_at,
                httponly=False,  # Allow JavaScript access for debugging
                secure=True,  # Required for production HTTPS
                samesite="none",  # Less restrictive for cross-origin requests
                path="/"
            )
            print(f" Fallback session cookie set successfully")
            
            return {
                "user_id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        
        # Verify Firebase token (if Admin SDK is available)
        decoded_token = firebase_auth.verify_id_token(idToken)
        
        # Create user data
        user_id = f"user_{decoded_token['uid'][:12]}"
        email = decoded_token.get('email', '')
        name = decoded_token.get('name', '')
        picture = decoded_token.get('picture', '')
        
        # Create session token
        session_token = f"session_{uuid.uuid4().hex[:24]}"
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Store session in database
        if db is not None:
            try:
                session_doc = {
                    "user_id": user_id,
                    "session_token": session_token,
                    "expires_at": expires_at.isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Delete existing sessions for this user
                await db.user_sessions.delete_many({"user_id": user_id})
                # Insert new session
                await db.user_sessions.insert_one(session_doc)
                print(f" Firebase session created in database for: {email}")
            except Exception as session_error:
                print(f" Session creation failed, falling back to memory: {session_error}")
                # Fallback to memory storage
                session_store[session_token] = {
                    "user_id": user_id,
                    "email": email,
                    "name": name,
                    "picture": picture,
                    "expires_at": expires_at.isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
        else:
            # Fallback to memory storage
            session_store[session_token] = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            print(f"Session stored in memory store: {session_token[:8]}... for user: {email}")
        
        # Set session cookie
        print(f" Setting session cookie: {session_token[:8]}...")
        # Use less restrictive cookie settings for better compatibility
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=False,  # Allow JavaScript access for debugging
            secure=True,  # Required for production HTTPS
            samesite="none",  # Less restrictive for cross-origin requests
            path="/",
            max_age=7 * 24 * 60 * 60
        )
        print(f" Session cookie set successfully")
        
        return {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture
        }
        
    except Exception as e:
        print(f"Firebase login error: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

# Current user endpoint
@app.get("/api/auth/me")
async def get_current_user_endpoint(request: Request):
    try:
        # Get session token from cookie
        session_token = request.cookies.get("session_token")
        print(f"Looking for session token: {session_token[:8] if session_token else 'None'}")
        
        if not session_token:
            print("No session token found in cookie")
            raise HTTPException(status_code=401, detail="No session token provided")
        
        # Check memory store first (more reliable for session persistence)
        print(f"Available sessions in store: {list(session_store.keys())}")
        user_data = session_store.get(session_token)
        if user_data:
            print(f"Found session in memory store: {user_data.get('email', 'unknown')}")
            return {
                "user_id": user_data.get("user_id"),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "picture": user_data.get("picture"),
                "created_at": user_data.get("created_at")
            }
        else:
            print(f"Session not found in memory store for token: {session_token}")
        
        # Fallback to database if memory store fails
        if db is None:
            print("Database not available, no fallback possible")
            raise HTTPException(status_code=401, detail="No valid session found")
        
        # Try database lookup
        try:
            if db:
                session_doc = await db.user_sessions.find_one({"session_token": session_token})
                if session_doc:
                    print(f"Found session in database: {session_doc.get('user_id', 'unknown')}")
                    return {
                        "user_id": session_doc.get("user_id"),
                        "email": session_doc.get("email"),
                        "name": session_doc.get("name"),
                        "picture": session_doc.get("picture"),
                        "created_at": session_doc.get("created_at")
                    }
            else:
                print(f"Session not found in database")
                # Fallback to memory store
                user_data = session_store.get(session_token)
                if user_data:
                    print(f"Found session in memory store: {user_data.get('email', 'unknown')}")
                    return {
                        "user_id": user_data.get("user_id"),
                        "email": user_data.get("email"),
                        "name": user_data.get("name"),
                        "picture": user_data.get("picture"),
                        "created_at": user_data.get("created_at")
                    }
                else:
                    print("Session not found in memory store either")
                    raise HTTPException(status_code=401, detail="No valid session found")
                    
        except Exception as e:
            print(f"Session validation error: {e}")
            raise HTTPException(status_code=500, detail=f"Session validation failed: {str(e)}")
            
    except Exception as e:
        print(f"Unexpected error in session validation: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Logout endpoint
@app.post("/api/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        # Remove from database
        if db is not None:
            try:
                await db.user_sessions.delete_many({"session_token": session_token})
            except Exception as e:
                print(f"Database session deletion failed: {e}")
        
        # Remove from memory
        if session_token in session_store:
            del session_store[session_token]
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out"}

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected" if db else "disconnected",
        "firebase": "initialized" if firebase_app else "not initialized"
    }

# Folders endpoints
@app.get("/api/folders")
async def get_folders(request: Request):
    user = await get_current_user(request)
    # Return user's folders from memory storage
    user_folders = folders_store.get(user.user_id, [])
    return user_folders

@app.post("/api/folders")
async def create_folder(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    
    # Create new folder
    new_folder = {
        "id": f"folder_{uuid.uuid4().hex[:8]}", 
        "name": body.get("name", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user.user_id
    }
    
    # Store in memory
    if user.user_id not in folders_store:
        folders_store[user.user_id] = []
    folders_store[user.user_id].append(new_folder)
    
    return new_folder

# Notes endpoints
@app.get("/api/notes")
async def get_notes(request: Request):
    user = await get_current_user(request)
    # Return user's notes from memory storage
    user_notes = notes_store.get(user.user_id, [])
    return user_notes

@app.post("/api/notes")
async def create_note(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    
    # Create new note
    new_note = {
        "id": f"note_{uuid.uuid4().hex[:8]}", 
        "title": body.get("title", ""),
        "content": body.get("content", ""),
        "folder_id": body.get("folder_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user.user_id
    }
    
    # Store in memory
    if user.user_id not in notes_store:
        notes_store[user.user_id] = []
    notes_store[user.user_id].append(new_note)
    
    return new_note

@app.put("/api/notes/{note_id}")
async def update_note(note_id: str, request: Request):
    user = await get_current_user(request)
    body = await request.json()
    
    # Find and update the note
    user_notes = notes_store.get(user.user_id, [])
    for note in user_notes:
        if note["id"] == note_id:
            note["title"] = body.get("title", note["title"])
            note["content"] = body.get("content", note["content"])
            note["updated_at"] = datetime.now(timezone.utc).isoformat()
            return note
    
    raise HTTPException(status_code=404, detail="Note not found")

@app.delete("/api/folders/{folder_id}")
async def delete_folder(folder_id: str, request: Request):
    user = await get_current_user(request)
    
    # Find and delete the folder
    user_folders = folders_store.get(user.user_id, [])
    for i, folder in enumerate(user_folders):
        if folder["id"] == folder_id:
            del user_folders[i]
            return {"message": "Folder deleted"}
    
    raise HTTPException(status_code=404, detail="Folder not found")

@app.post("/api/notes/{note_id}/share")
async def share_note(note_id: str, request: Request):
    user = await get_current_user(request)
    # Generate share link logic here
    share_link = f"share_{uuid.uuid4().hex[:12]}"
    return {"share_link": share_link, "url": f"/shared/{share_link}"}

@app.get("/api/shared/{share_link}")
async def get_shared_note(share_link: str):
    # Get shared note logic here (no authentication required)
    return {
        "id": f"note_{uuid.uuid4().hex[:8]}",
        "title": "Shared Note",
        "content": "This is a shared note content",
        "share_link": share_link
    }

# Additional health check endpoints
@app.get("/api/health/db")
async def health_db():
    return {
        "status": "connected" if db else "disconnected",
        "type": "memory" if not db else "mongodb"
    }

@app.get("/api/health/firebase")
async def health_firebase():
    return {
        "status": "initialized" if firebase_app else "not initialized",
        "admin_sdk": firebase_app is not None
    }

@app.get("/api/health/env")
async def health_env():
    # Check multiple environment variables to detect production
    is_production = (
        os.environ.get("NODE_ENV") == "production" or
        os.environ.get("VERCEL_ENV") == "production" or
        os.environ.get("ENVIRONMENT") == "production"
    )
    
    return {
        "environment": "production" if is_production else "development",
        "platform": "Vercel" if is_production else "Local",
        "mongo_url_set": bool(os.environ.get("MONGO_URL")),
        "firebase_config_set": bool(os.environ.get("FIREBASE_ADMIN_JSON"))
    }

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shutdown handler
@app.on_event("shutdown")
async def shutdown_db_client():
    if client:
        client.close()

# Vercel handler
handler = app
