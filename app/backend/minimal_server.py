from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
import os
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import uuid
from typing import Optional

app = FastAPI()

# Models
class Note(BaseModel):
    title: str
    content: str = ""

class Folder(BaseModel):
    name: str
    color: str = "#E06A4F"
    created_at: str = ""
    updated_at: str = ""

class User(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    created_at: str

# Mock data storage (since we don't have MongoDB in minimal server)
mock_users = {}
mock_folders = {}
mock_notes = {}

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
        firebase_app = firebase_admin.get_app()
        print("✅ Using existing Firebase app")
    except:
        firebase_app = None
        print("❌ Firebase Admin SDK not available")

# Models
class FirebaseUser(BaseModel):
    uid: str
    email: str
    displayName: str = None
    photoURL: str = None

class FirebaseLoginRequest(BaseModel):
    idToken: str
    firebaseUser: FirebaseUser

@app.get("/")
async def root():
    return {"message": "Xero Notes API is running", "version": "1.0.0"}

@app.get("/test")
async def simple_test():
    """Simple test endpoint at root level"""
    return {
        "status": "ok",
        "message": "Backend is working at root level",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "firebase": "initialized" if firebase_app else "not_initialized",
            "env_vars": {
                "MONGO_URL_set": bool(os.environ.get('MONGO_URL')),
                "DB_NAME_set": bool(os.environ.get('DB_NAME')),
                "FIREBASE_ADMIN_JSON_set": bool(os.environ.get('FIREBASE_ADMIN_JSON'))
            }
        }
    }

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/auth/test")
async def auth_test():
    return {
        "status": "ok", 
        "message": "Auth test working",
        "firebase_available": firebase_app is not None
    }

# Firebase login endpoint removed - using server.py instead
# This was causing routing conflicts with the main server

@app.get("/api/me")
async def get_current_user():
    """Get current authenticated user (for session verification)"""
    return {
        "user_id": "test_user_123",
        "email": "test@example.com", 
        "name": "Test User",
        "message": "Mock user endpoint working"
    }

# Add missing endpoints for dashboard
@app.get("/api/folders")
async def get_folders():
    """Get all folders for the authenticated user"""
    return {
        "folders": list(mock_folders.values()),
        "message": "Mock folders endpoint working"
    }

@app.get("/api/notes")
async def get_notes():
    """Get all notes for the authenticated user"""
    return {
        "notes": list(mock_notes.values()),
        "message": "Mock notes endpoint working"
    }

print("✅ Minimal server with Firebase auth loaded successfully")
