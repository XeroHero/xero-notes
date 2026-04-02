from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import logging
from pathlib import Path
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

# Import auth routers
# from app.backend.firebase_auth import firebase_auth_router  # Commented out to prevent conflicts

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection with error handling
try:
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    print("✅ MongoDB connected successfully")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    # Set fallback values to prevent crashes
    mongo_url = None
    client = None
    db = None

# Firebase Admin SDK initialization
firebase_admin_json = os.environ.get('FIREBASE_ADMIN_JSON')
firebase_app = None

print(f"🔍 Firebase Admin SDK initialization check:")
print(f"   FIREBASE_ADMIN_JSON exists: {bool(firebase_admin_json)}")
if firebase_admin_json:
    print(f"   JSON length: {len(firebase_admin_json)}")
    print(f"   First 100 chars: {firebase_admin_json[:100]}")

try:
    if firebase_admin_json:
        import json
        try:
            firebase_config = json.loads(firebase_admin_json)
            print("✅ JSON parsing successful")
            print(f"   Config keys: {list(firebase_config.keys())}")
            print(f"   Project ID: {firebase_config.get('project_id', 'NOT_FOUND')}")
            print(f"   Client email: {firebase_config.get('client_email', 'NOT_FOUND')}")
            
            cred = credentials.Certificate(firebase_config)
            firebase_app = firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin SDK initialized from environment variable")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"   First 200 chars: {firebase_admin_json[:200]}")
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ FIREBASE_ADMIN_JSON not set")
except Exception as e:
    print(f"❌ Firebase initialization error: {e}")
    try:
        # Try to get existing app first
        firebase_app = firebase_admin.get_app()
        if firebase_app:
            print("✅ Using existing Firebase app")
        else:
            # If no existing app, try to initialize
            if firebase_admin_json:
                import json
                firebase_config = json.loads(firebase_admin_json)
                cred = credentials.Certificate(firebase_config)
                firebase_app = firebase_admin.initialize_app(cred)
                print("✅ Firebase Admin SDK initialized from environment variable")
            else:
                print("⚠️ No Firebase config available")
    except:
        firebase_app = None
        print("❌ Firebase Admin SDK not available")

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Models
class User(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    created_at: str

class SessionData(BaseModel):
    session_id: str

class FolderCreate(BaseModel):
    name: str
    color: Optional[str] = "#E06A4F"

class NoteCreate(BaseModel):
    title: str
    content: str = ""
    folder_id: Optional[str] = None
    is_shared: bool = False

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    folder_id: Optional[str] = None
    is_shared: Optional[bool] = None

# Auth helper - Get current authenticated user
async def get_current_user(request: Request) -> User:
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    expires_at = session_doc.get("expires_at")
    if expires_at:
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expired")
    
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    if isinstance(user_doc.get("created_at"), str):
        user_doc["created_at"] = datetime.fromisoformat(user_doc["created_at"])
    
    return User(**user_doc)

# Auth endpoints
@api_router.post("/auth/session")
async def exchange_session(data: SessionData, response: Response):
    """Exchange session_id for session_token via Emergent Auth"""
    try:
        async with httpx.AsyncClient() as http_client:
            resp = await http_client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": data.session_id}
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session_id")
            auth_data = resp.json()
    except httpx.RequestError as e:
        logger.error(f"Auth request failed: {e}")
        raise HTTPException(status_code=500, detail="Authentication service unavailable")
    
    existing_user = await db.users.find_one({"email": auth_data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": auth_data["name"], "picture": auth_data.get("picture")}}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": auth_data["email"],
            "name": auth_data["name"],
            "picture": auth_data.get("picture"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
    
    session_token = auth_data["session_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session_doc = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.user_sessions.insert_one(session_doc)
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,  # Changed to False for Vercel compatibility
        samesite="lax",  # Changed to lax for better compatibility
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user_doc

@api_router.get("/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    return user.model_dump()

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    response.delete_cookie(key="session_token", path="/", samesite="none", secure=True)
    return {"message": "Logged out"}

@app.get("/api/me")
async def get_current_user():
    """Get current authenticated user (for session verification)"""
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

# Root route
@app.get("/")
async def root():
    return {"message": "Xero Notes API is running", "version": "1.0.0"}

# Simple test route at root level (bypasses /api prefix)
@app.get("/test")
async def simple_test():
    """Simple test endpoint at root level"""
    return {
        "status": "ok",
        "message": "Backend is working at root level",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "mongodb": "connected" if db else "disconnected",
            "firebase": "initialized" if firebase_app else "not_initialized"
        }
    }

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

# Notes endpoints (secured by user)
@api_router.post("/notes")
async def create_note(note_data: NoteCreate, request: Request, user: User = Depends(get_current_user)):
    """Create a new note for the authenticated user"""
    print(f"🔍 DEBUG: POST /api/notes called")
    print(f"🔍 DEBUG: User: {user}")
    print(f"🔍 DEBUG: Note data: {note_data}")
    try:
        note_doc = {
            "note_id": f"note_{uuid.uuid4().hex[:12]}",
            "user_id": user.user_id,
            "title": note_data.title,
            "content": note_data.content,
            "folder_id": note_data.folder_id,
            "is_shared": note_data.is_shared,
            "share_link": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notes.insert_one(note_doc)
        return note_doc
    except Exception as e:
        logger.error(f"Create note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/notes")
async def get_notes(user: User = Depends(get_current_user)):
    """Get all notes for the authenticated user"""
    try:
        notes_cursor = db.notes.find({"user_id": user.user_id})
        notes = []
        async for note in notes_cursor:
            note["_id"] = str(note["_id"])
            notes.append(note)
        return {"notes": notes}
    except Exception as e:
        logger.error(f"Get notes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/notes/{note_id}")
async def get_note(note_id: str, user: User = Depends(get_current_user)):
    """Get a specific note by ID (must belong to user)"""
    try:
        note = await db.notes.find_one({"note_id": note_id, "user_id": user.user_id})
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        note["_id"] = str(note["_id"])
        return note
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/notes/{note_id}")
async def update_note(note_id: str, note_data: NoteUpdate, user: User = Depends(get_current_user)):
    """Update a note (must belong to user)"""
    try:
        update_data = {}
        if note_data.title is not None:
            update_data["title"] = note_data.title
        if note_data.content is not None:
            update_data["content"] = note_data.content
        if note_data.folder_id is not None:
            update_data["folder_id"] = note_data.folder_id
        if note_data.is_shared is not None:
            update_data["is_shared"] = note_data.is_shared
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await db.notes.update_one(
            {"note_id": note_id, "user_id": user.user_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Note not found")
        
        updated_note = await db.notes.find_one({"note_id": note_id, "user_id": user.user_id})
        updated_note["_id"] = str(updated_note["_id"])
        return updated_note
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/notes/{note_id}")
async def delete_note(note_id: str, user: User = Depends(get_current_user)):
    """Delete a note (must belong to user)"""
    try:
        result = await db.notes.delete_one({"note_id": note_id, "user_id": user.user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"success": True, "message": "Note deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/notes/{note_id}/share")
async def share_note(note_id: str, user: User = Depends(get_current_user)):
    """Generate a share link for a note (must belong to user)"""
    try:
        note = await db.notes.find_one({"note_id": note_id, "user_id": user.user_id})
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        share_link = f"{uuid.uuid4().hex[:12]}"
        
        await db.notes.update_one(
            {"note_id": note_id, "user_id": user.user_id},
            {
                "$set": {
                    "is_shared": True,
                    "share_link": share_link,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {"share_link": share_link}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Share note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/shared/{share_link}")
async def get_shared_note(share_link: str):
    """Get a shared note by share link (public endpoint, no auth required)"""
    try:
        note = await db.notes.find_one({"share_link": share_link, "is_shared": True})
        if not note:
            raise HTTPException(status_code=404, detail="Shared note not found")
        
        note["_id"] = str(note["_id"])
        
        # Get author information
        user_doc = await db.users.find_one({"user_id": note["user_id"]}, {"_id": 0})
        author = {
            "name": user_doc.get("name", "Xero Notes User") if user_doc else "Xero Notes User",
            "picture": user_doc.get("picture") if user_doc else None
        }
        
        return {"note": note, "author": author}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get shared note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Folders endpoints (secured by user)
@api_router.get("/folders")
async def get_folders(user: User = Depends(get_current_user)):
    """Get all folders for the authenticated user"""
    try:
        folders_cursor = db.folders.find({"user_id": user.user_id})
        folders = []
        async for folder in folders_cursor:
            folder["_id"] = str(folder["_id"])
            folders.append(folder)
        return {"folders": folders}
    except Exception as e:
        logger.error(f"Get folders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/folders")
async def create_folder(folder_data: FolderCreate, user: User = Depends(get_current_user)):
    """Create a new folder for the authenticated user"""
    try:
        folder_doc = {
            "folder_id": f"folder_{uuid.uuid4().hex[:12]}",
            "user_id": user.user_id,
            "name": folder_data.name,
            "color": folder_data.color or "#E06A4F",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.folders.insert_one(folder_doc)
        return folder_doc
    except Exception as e:
        logger.error(f"Create folder error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: str, user: User = Depends(get_current_user)):
    """Delete a folder (must belong to user)"""
    try:
        result = await db.folders.delete_one({"folder_id": folder_id, "user_id": user.user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Folder not found")
        return {"success": True, "message": "Folder deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete folder error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include routers
app.include_router(api_router)
# app.include_router(firebase_auth_router)  # Commented out to prevent conflicts

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

handler = app
