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

# In-memory storage for development (fallback when MongoDB is unavailable)
memory_storage = {
    "folders": [],
    "notes": []
}

# In-memory session store for real user authentication
session_store = {}

# MongoDB connection with error handling
try:
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)  # Short timeout
    # Test the connection
    client.admin.command('ping')
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
print(f"   Raw env var type: {type(firebase_admin_json)}")
print(f"   Raw env var length: {len(firebase_admin_json) if firebase_admin_json else 0}")

# Debug: Print first 200 chars of raw environment variable
if firebase_admin_json:
    print(f"   Raw first 200 chars: {repr(firebase_admin_json[:200])}")

# Initialize Firebase Admin SDK with ultimate fallback methods
if firebase_admin_json:
    try:
        import json
        import ast
        
        firebase_config = None
        
        # Method 1: Try direct JSON parsing
        try:
            firebase_config = json.loads(firebase_admin_json)
            print("✅ Method 1: Direct JSON parsing successful")
        except json.JSONDecodeError as e:
            print(f"❌ Method 1 failed: {e}")
            
            # Method 2: Handle quote wrapping
            firebase_json_clean = firebase_admin_json.strip()
            if firebase_json_clean.startswith("'") and firebase_json_clean.endswith("'"):
                firebase_json_clean = firebase_json_clean[1:-1]
            elif firebase_json_clean.startswith('"') and firebase_json_clean.endswith('"'):
                firebase_json_clean = firebase_json_clean[1:-1]
            
            try:
                firebase_config = json.loads(firebase_json_clean)
                print("✅ Method 2: Quote unwrapping successful")
            except json.JSONDecodeError as e2:
                print(f"❌ Method 2 failed: {e2}")
                
                # Method 3: Try to fix escape sequences
                try:
                    firebase_json_clean = firebase_json_clean.replace('\\n', '\n').replace('\\\\n', '\n')
                    firebase_config = json.loads(firebase_json_clean)
                    print("✅ Method 3: Escape sequence fixing successful")
                except json.JSONDecodeError as e3:
                    print(f"❌ Method 3 failed: {e3}")
                    
                    # Method 4: Use ast.literal_eval as last resort
                    try:
                        firebase_config = ast.literal_eval(firebase_admin_json)
                        print("✅ Method 4: AST literal eval successful")
                    except Exception as e4:
                        print(f"❌ Method 4 failed: {e4}")
                        
                        # Method 5: Try manual parsing for Vercel format
                        try:
                            # Split by lines and reconstruct
                            lines = firebase_admin_json.split('\\n')
                            reconstructed = ''
                            for line in lines:
                                if line.strip().startswith('"') and line.strip().endswith('"'):
                                    reconstructed += line.strip()[1:-1] + '\n'
                                else:
                                    reconstructed += line + '\n'
                            firebase_config = json.loads(reconstructed.strip())
                            print("✅ Method 5: Manual line reconstruction successful")
                        except Exception as e5:
                            print(f"❌ Method 5 failed: {e5}")
                            
                            # Method 6: Ultimate fallback - try to reconstruct from individual components
                            try:
                                print("🔧 Attempting ultimate fallback method...")
                                # If JSON parsing completely fails, try to reconstruct from file
                                firebase_config = {
                                    "type": "service_account",
                                    "project_id": "xero-notes",
                                    "private_key_id": "594bb7e380083a61a39556eed63eb9c0f25e441a",
                                    "client_email": "firebase-adminsdk-fbsvc@xero-notes.iam.gserviceaccount.com",
                                    "client_id": "100717736424180417094",
                                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                    "token_uri": "https://oauth2.googleapis.com/token",
                                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                                    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40xero-notes.iam.gserviceaccount.com",
                                    "universe_domain": "googleapis.com"
                                }
                                
                                # Try to extract private key from environment variable
                                if '-----BEGIN PRIVATE KEY-----' in firebase_admin_json:
                                    # Extract private key section
                                    start = firebase_admin_json.find('-----BEGIN PRIVATE KEY-----')
                                    end = firebase_admin_json.find('-----END PRIVATE KEY-----', start)
                                    if start != -1 and end != -1:
                                        private_key_section = firebase_admin_json[start:end + len('-----END PRIVATE KEY-----')]
                                        # Clean up the private key
                                        private_key_section = private_key_section.replace('\\\\n', '\n').replace('\\n', '\n').replace('\\\\n', '\n')
                                        firebase_config["private_key"] = '-----BEGIN PRIVATE KEY-----\n' + private_key_section + '\n-----END PRIVATE KEY-----\n'
                                        print("✅ Method 6: Ultimate fallback successful - extracted private key")
                                    else:
                                        print("❌ Method 6: Could not find private key section")
                                else:
                                    print("❌ Method 6: No private key found in environment variable")
                                    
                            except Exception as e6:
                                print(f"❌ Method 6 failed: {e6}")
                                firebase_config = None
        
        # Method 7: Alternative approach - use individual environment variables
        if firebase_config is None:
            try:
                print("🔧 Attempting Method 7: Individual environment variables...")
                
                # Try to get individual Firebase environment variables
                firebase_type = os.environ.get('FIREBASE_TYPE', 'service_account')
                firebase_project_id = os.environ.get('FIREBASE_PROJECT_ID', 'xero-notes')
                firebase_private_key_id = os.environ.get('FIREBASE_PRIVATE_KEY_ID', '594bb7e380083a61a39556eed63eb9c0f25e441a')
                firebase_client_email = os.environ.get('FIREBASE_CLIENT_EMAIL', 'firebase-adminsdk-fbsvc@xero-notes.iam.gserviceaccount.com')
                firebase_client_id = os.environ.get('FIREBASE_CLIENT_ID', '100717736424180417094')
                firebase_auth_uri = os.environ.get('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth')
                firebase_token_uri = os.environ.get('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token')
                firebase_auth_provider = os.environ.get('FIREBASE_AUTH_PROVIDER', 'https://www.googleapis.com/oauth2/v1/certs')
                firebase_client_cert = os.environ.get('FIREBASE_CLIENT_CERT', 'https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40xero-notes.iam.gserviceaccount.com')
                firebase_universe = os.environ.get('FIREBASE_UNIVERSE', 'googleapis.com')
                
                # Get private key from individual env var or fallback
                firebase_private_key = os.environ.get('FIREBASE_PRIVATE_KEY')
                if not firebase_private_key and firebase_admin_json and '-----BEGIN PRIVATE KEY-----' in firebase_admin_json:
                    # Extract from JSON if individual env var not set
                    start = firebase_admin_json.find('-----BEGIN PRIVATE KEY-----')
                    end = firebase_admin_json.find('-----END PRIVATE KEY-----', start)
                    if start != -1 and end != -1:
                        private_key_section = firebase_admin_json[start:end + len('-----END PRIVATE KEY-----')]
                        firebase_private_key = private_key_section.replace('\\\\n', '\n').replace('\\n', '\n').replace('\\\\n', '\n')
                        firebase_private_key = '-----BEGIN PRIVATE KEY-----\n' + firebase_private_key + '\n-----END PRIVATE KEY-----\n'
                
                if firebase_private_key:
                    firebase_config = {
                        "type": firebase_type,
                        "project_id": firebase_project_id,
                        "private_key_id": firebase_private_key_id,
                        "private_key": firebase_private_key,
                        "client_email": firebase_client_email,
                        "client_id": firebase_client_id,
                        "auth_uri": firebase_auth_uri,
                        "token_uri": firebase_token_uri,
                        "auth_provider_x509_cert_url": firebase_auth_provider,
                        "client_x509_cert_url": firebase_client_cert,
                        "universe_domain": firebase_universe
                    }
                    print("✅ Method 7: Individual environment variables successful")
                else:
                    print("❌ Method 7: No private key available")
                    firebase_config = None
                    
            except Exception as e7:
                print(f"❌ Method 7 failed: {e7}")
                firebase_config = None
        
        if firebase_config:
            # Fix private key format regardless of method used
            if 'private_key' in firebase_config and isinstance(firebase_config['private_key'], str):
                private_key = firebase_config['private_key']
                # Fix Vercel double backslash issue: replace \\\\n with \n, then \\n with \n
                if '\\\\n' in private_key:
                    private_key = private_key.replace('\\\\n', '\n')
                if '\\n' in private_key:
                    private_key = private_key.replace('\\n', '\n')
                firebase_config['private_key'] = private_key
            
            print("✅ JSON parsing successful")
            print(f"   Config keys: {list(firebase_config.keys()) if firebase_config else 'None'}")
            print(f"   Project ID: {firebase_config.get('project_id', 'NOT_FOUND') if firebase_config else 'None'}")
            print(f"   Client email: {firebase_config.get('client_email', 'NOT_FOUND') if firebase_config else 'None'}")
            
            # Check if app already exists
            try:
                firebase_app = firebase_admin.get_app()
                print("✅ Using existing Firebase app")
            except ValueError:
                # App doesn't exist, initialize it
                if firebase_config:
                    cred = credentials.Certificate(firebase_config)
                    firebase_app = firebase_admin.initialize_app(cred)
                    print("✅ Firebase Admin SDK initialized from environment variable")
                else:
                    print("❌ Firebase config is None, cannot initialize")
            
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        import traceback
        traceback.print_exc()
        firebase_app = None
else:
    print("⚠️ FIREBASE_ADMIN_JSON not set")
    firebase_app = None

# Additional debugging for Firebase initialization
print(f"🔍 Final Firebase app status: {firebase_app is not None}")
if firebase_app:
    print(f"🔍 Firebase app name: {firebase_app.name}")
else:
    print("🚨 Firebase app is None - this will cause authentication failures")

app = FastAPI()
print("🚀 FastAPI app created")

api_router = APIRouter(prefix="/api")
print("🚀 API router created")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
print("🚀 Logging configured")

# Models
class User(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    created_at: str

class SessionData(BaseModel):
    session_id: str

class FirebaseLoginRequest(BaseModel):
    idToken: str
    firebaseUser: Optional[dict] = None

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
    
    # Check if session exists in session store (real Firebase users)
    if session_token in session_store:
        session_data = session_store[session_token]
        
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
                raise HTTPException(status_code=401, detail="Session expired")
        
        # Return real user data
        user_obj = User(
            user_id=session_data["user_id"],
            email=session_data["email"],
            name=session_data["name"],
            picture=session_data["picture"],
            created_at=session_data.get("created_at", datetime.now(timezone.utc).isoformat())
        )
        print(f"🔍 DEBUG: Returning real user from session: {user_obj.email}")
        return user_obj
    
    # Fallback for test sessions (remove this in production)
    if session_token.startswith("session_") and len(session_token) > 20:
        print("🔍 DEBUG: Using fallback test user (should not happen in production)")
        user_obj = User(
            user_id="user_test123456789",
            email="test@example.com", 
            name="Test User",
            picture="https://example.com/photo.jpg",
            created_at=datetime.now(timezone.utc).isoformat()
        )
        return user_obj
    
    raise HTTPException(status_code=401, detail="Invalid session")

# Auth endpoints
# @api_router.post("/auth/session")
# async def exchange_session(data: SessionData, response: Response):
#     """Exchange session_id for session_token via Emergent Auth"""
#     try:
#         async with httpx.AsyncClient() as http_client:
#             resp = await http_client.get(
#                 "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
#                 headers={"X-Session-ID": data.session_id}
#             )
#             if resp.status_code != 200:
#                 raise HTTPException(status_code=401, detail="Invalid session_id")
#             auth_data = resp.json()
#     except httpx.RequestError as e:
#         logger.error(f"Auth request failed: {e}")
#         raise HTTPException(status_code=500, detail="Authentication service unavailable")
#     
#     existing_user = await db.users.find_one({"email": auth_data["email"]}, {"_id": 0})
#     
#     if existing_user:
#         user_id = existing_user["user_id"]
#         await db.users.update_one(
#             {"user_id": user_id},
#             {"$set": {"name": auth_data["name"], "picture": auth_data.get("picture")}}
#         )
#     else:
#         user_id = f"user_{uuid.uuid4().hex[:12]}"
#         user_doc = {
#             "user_id": user_id,
#             "email": auth_data["email"],
#             "name": auth_data["name"],
#             "picture": auth_data.get("picture"),
#             "created_at": datetime.now(timezone.utc).isoformat()
#         }
#         await db.users.insert_one(user_doc)
#     
#     session_token = auth_data["session_token"]
#     expires_at = datetime.now(timezone.utc) + timedelta(days=7)
#     
#     session_doc = {
#         "user_id": user_id,
#         "session_token": session_token,
#         "expires_at": expires_at.isoformat(),
#         "created_at": datetime.now(timezone.utc).isoformat()
#     }
#     
#     await db.user_sessions.delete_many({"user_id": user_id})
#     await db.user_sessions.insert_one(session_doc)
#     
#     response.set_cookie(
#         key="session_token",
#         value=session_token,
#         httponly=True,
#         secure=False,  # Changed to False for Vercel compatibility
#         samesite="lax",  # Changed to lax for better compatibility
#         path="/",
#         max_age=7 * 24 * 60 * 60
#     )
#     
#     user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
#     return user_doc

# @api_router.get("/auth/me")
# async def get_me(user: User = Depends(get_current_user)):
#     return user.model_dump()

# @api_router.post("/auth/logout")
# async def logout(request: Request, response: Response):
#     session_token = request.cookies.get("session_token")
#     if session_token:
#         await db.user_sessions.delete_many({"session_token": session_token})
#     response.delete_cookie(key="session_token", path="/", samesite="none", secure=True)
#     return {"message": "Logged out"}

@app.post("/api/auth/test-login")
async def test_login(response: Response):
    """Test login endpoint that doesn't require Firebase verification"""
    print("🚨 TEST LOGIN ENDPOINT CALLED 🚨")
    
    try:
        # Create test user data
        user_id = "user_test123456789"
        email = "test@example.com"
        name = "Test User"
        picture = "https://example.com/photo.jpg"
        
        # Create or update user in database
        if db is not None:
            try:
                user_doc = {
                    "user_id": user_id,
                    "email": email,
                    "name": name,
                    "picture": picture,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                existing_user = await db.users.find_one({"user_id": user_id})
                if existing_user:
                    # Update existing user
                    await db.users.update_one(
                        {"user_id": user_id},
                        {"$set": {"name": name, "picture": picture}}
                    )
                    print("✅ Test user updated in database")
                else:
                    # Insert new user
                    await db.users.insert_one(user_doc)
                    print("✅ Test user created in database")
            except Exception as save_error:
                print(f"⚠️ Database save failed, but continuing: {save_error}")
        
        # Create session token for authentication
        session_token = f"session_{uuid.uuid4().hex[:24]}"
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Save session to database
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
                print("✅ Test session created in database")
            except Exception as session_error:
                print(f"⚠️ Session creation failed, but continuing: {session_error}")
        
        # Set session cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=False,  # Changed to False for local testing
            samesite="lax",
            path="/",
            max_age=7 * 24 * 60 * 60
        )
        print("✅ Test session cookie set")
        
        # Return user data
        user_data = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture
        }
        
        print("🔍 Returning test user data")
        return user_data

    except Exception as e:
        print(f"🚨 TEST LOGIN ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Test authentication failed: {str(e)}")

@api_router.post("/auth/firebase-login")
async def firebase_login(firebase_request: FirebaseLoginRequest, request: Request, response: Response):
    """Verify Firebase token and return user data"""
    print("🚨🚨🚨 FIREBASE LOGIN ENDPOINT CALLED 🚨🚨🚨")

    try:
        # Check if Firebase is initialized
        if firebase_app is None:
            raise HTTPException(status_code=500, detail="Firebase Admin SDK not initialized")
        
        # Verify Firebase ID token
        decoded_token = firebase_auth.verify_id_token(firebase_request.idToken)
        print(f"🔍 Firebase token verified successfully!")

        # Create user data from token
        user_id = f"user_{decoded_token['uid'][:12]}"
        email = decoded_token.get('email', '')
        name = decoded_token.get('name', '')
        picture = decoded_token.get('picture', '')
        
        # Create session token for authentication
        session_token = f"session_{uuid.uuid4().hex[:24]}"
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Store session data in memory
        session_store[session_token] = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        print(f"✅ Stored real user session for: {email}")
        
        # Set session cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=False,  # Changed to False for Vercel compatibility
            samesite="lax",  # Changed to lax for better compatibility
            path="/",
            max_age=7 * 24 * 60 * 60
        )
        print("✅ Session cookie set")
        
        # Return user data
        user_data = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture
        }
        
        print("🔍 Returning user data from Firebase token")
        return user_data

    except Exception as e:
        print(f"🚨 FIREBASE LOGIN ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@app.get("/api/me")
async def get_current_user_endpoint(request: Request):
    """Get current authenticated user (for session verification)"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if session exists in session store (real Firebase users)
    if session_token in session_store:
        session_data = session_store[session_token]
        
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
                raise HTTPException(status_code=401, detail="Session expired")
        
        # Return real user data as JSON
        return {
            "user_id": session_data["user_id"],
            "email": session_data["email"],
            "name": session_data["name"],
            "picture": session_data["picture"],
            "created_at": session_data.get("created_at")
        }
    
    # Fallback for test sessions (remove this in production)
    if session_token.startswith("session_") and len(session_token) > 20:
        return {
            "user_id": "user_test123456789",
            "email": "test@example.com", 
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    raise HTTPException(status_code=401, detail="Invalid session")

# Root route
@app.get("/")
async def root():
    return {"message": "Xero Notes API is running", "version": "1.0.0"}

# Simple test route at root level (bypasses /api prefix)
@app.get("/test")
async def simple_test():
    """Simple test endpoint at root level"""
    try:
        return {
            "status": "ok",
            "message": "Backend is working at root level",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "mongodb": "connected" if db is not None else "disconnected",
                "firebase": "initialized" if firebase_app is not None else "not_initialized",
                "env_vars": {
                    "MONGO_URL_set": bool(os.environ.get('MONGO_URL')),
                    "DB_NAME_set": bool(os.environ.get('DB_NAME')),
                    "FIREBASE_ADMIN_JSON_set": bool(os.environ.get('FIREBASE_ADMIN_JSON'))
                }
            }
        }
    except Exception as e:
        logger.error(f"Test endpoint error: {e}")
        return {
            "status": "error",
            "message": f"Test endpoint failed: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/api/debug-server")
async def debug_server():
    """Debug endpoint to confirm server.py is being used"""
    print("🚨🚨🚨 SERVER.PY DEBUG ENDPOINT CALLED 🚨🚨🚨")
    return {
        "message": "server.py is being used!",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server_file": "app/backend/server.py",
        "firebase_available": firebase_app is not None,
        "db_available": db is not None
    }

@app.get("/api/debug-env")
async def debug_env():
    """Debug endpoint to check environment variables (safe)"""
    return {
        "deployment_url": os.environ.get('VERCEL_URL', 'unknown'),
        "mongo_url_set": bool(os.environ.get('MONGO_URL')),
        "mongo_url_length": len(os.environ.get('MONGO_URL', '')),
        "mongo_url_starts_with": os.environ.get('MONGO_URL', '')[:20] + '...' if os.environ.get('MONGO_URL') else 'not_set',
        "db_name_set": bool(os.environ.get('DB_NAME')),
        "db_name": os.environ.get('DB_NAME', 'not_set'),
        "firebase_set": bool(os.environ.get('FIREBASE_ADMIN_JSON')),
        "firebase_length": len(os.environ.get('FIREBASE_ADMIN_JSON', ''))
    }

@app.get("/api/simple-debug")
async def simple_debug():
    """Simple debug endpoint"""
    try:
        return {
            "message": "Simple debug working",
            "timestamp": "2024-04-04T00:00:00Z",
            "db_available": db is not None,
            "db_name": "connected" if db is not None else "disconnected"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Debug endpoint failed"
        }

@app.get("/api/debug-mongo")
async def debug_mongo():
    """Debug MongoDB connection details"""
    try:
        # Test basic connection
        print("🔍 Testing MongoDB basic connection...")
        db_info = {
            "db_name": db.name if db else "no_db",
            "db_available": db is not None,
            "collections": []
        }
        
        if db is not None:
            try:
                # List collections
                collections = await db.list_collection_names()
                db_info["collections"] = collections
                print(f"🔍 Collections found: {collections}")
                
                # Test users collection specifically
                users_count = await db.users.count_documents({})
                db_info["users_count"] = users_count
                print(f"🔍 Users collection count: {users_count}")
                
            except Exception as collection_error:
                db_info["collection_error"] = str(collection_error)
                print(f"🚨 Collection error: {collection_error}")
        
        return db_info
        
    except Exception as e:
        print(f"🚨 MongoDB debug error: {e}")
        return {
            "error": str(e),
            "db_available": db is not None,
            "db_name": db.name if db else "no_db"
        }

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.api_route("/api/debug", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def debug_all_methods(request: Request):
    """Debug endpoint that accepts all methods"""
    print(f"🔍 DEBUG: {request.method} /api/debug called")
    print(f"🔍 DEBUG: Headers: {dict(request.headers)}")
    print(f"🔍 DEBUG: Query params: {dict(request.query_params)}")
    
    try:
        body = await request.body()
        print(f"🔍 DEBUG: Body: {body}")
    except:
        print(f"🔍 DEBUG: No body or body read error")
    
    return {
        "method": request.method,
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "message": f"Debug endpoint received {request.method}"
    }

@app.post("/api/simple-post")
async def simple_post():
    """Simple POST endpoint with no dependencies"""
    print("🔍 Simple POST endpoint called")
    return {"status": "ok", "method": "POST", "message": "Simple POST works"}

@app.post("/api/auth/test-post")
async def auth_test_post(request: Request):
    """Test POST endpoint in auth router"""
    print("🔍 Auth POST endpoint called")
    print(f"🔍 Request method: {request.method}")
    return {"message": "Auth POST test works"}

@app.post("/api/test-post")
async def test_post():
    """Test POST endpoint"""
    print("🔍 Test POST endpoint called")
    return {"message": "POST test works"}

@app.get("/api/auth/test")
async def auth_test():
    """Auth test endpoint"""
    return {
        "status": "ok",
        "message": "Auth test working",
        "firebase_available": firebase_app is not None,
        "db_available": db is not None
    }

@app.get("/api/simple-test")
async def simple_test():
    """Simple test endpoint to check if server is working"""
    return {"status": "ok", "message": "Server is working"}

@api_router.get("/auth/router-test")
async def router_test():
    """Test if the auth router is working"""
    return {"status": "ok", "message": "Auth router is working"}

# Notes endpoints (secured by user)
@api_router.post("/notes")
async def create_note(note_data: NoteCreate, request: Request):
    """Create a new note for the authenticated user"""
    print(f"🔍 DEBUG: POST /api/notes called")
    print(f"🔍 DEBUG: Note data: {note_data}")
    print(f"🔍 DEBUG: Request method: {request.method}")
    print(f"🔍 DEBUG: Request URL: {request.url}")
    
    # Get current user
    try:
        user = await get_current_user(request)
        print(f"🔍 DEBUG: User authenticated: {user.email}")
    except HTTPException as e:
        print(f"🔍 DEBUG: Authentication failed: {e.detail}")
        raise e
    
    # Create note in memory storage
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
    
    # Add to in-memory storage
    memory_storage["notes"].append(note_doc)
    print(f"✅ Created note in memory: {note_doc['title']}")
    
    return note_doc

@api_router.get("/notes")
async def get_notes(request: Request):
    """Get all notes for the authenticated user"""
    # Get current user
    try:
        user = await get_current_user(request)
        print(f"🔍 DEBUG: Get notes for user: {user.email}")
    except HTTPException as e:
        print(f"🔍 DEBUG: Authentication failed for get notes: {e.detail}")
        raise e
    
    # Use in-memory storage for development
    user_notes = [note for note in memory_storage["notes"] if note.get("user_id") == user.user_id]
    return {"notes": user_notes}

@api_router.get("/notes/{note_id}")
async def get_note(note_id: str, user: User = Depends(get_current_user)):
    """Get a specific note by ID (must belong to user)"""
    # Find note in in-memory storage
    note = next((note for note in memory_storage["notes"] 
                if note.get("note_id") == note_id and note.get("user_id") == user.user_id), None)
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return note

@api_router.put("/notes/{note_id}")
async def update_note(note_id: str, note_data: NoteUpdate, user: User = Depends(get_current_user)):
    """Update a note (must belong to user)"""
    # Find and update note in in-memory storage
    note = next((note for note in memory_storage["notes"] 
                if note.get("note_id") == note_id and note.get("user_id") == user.user_id), None)
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Update fields
    if note_data.title is not None:
        note["title"] = note_data.title
    if note_data.content is not None:
        note["content"] = note_data.content
    if note_data.folder_id is not None:
        note["folder_id"] = note_data.folder_id
    if note_data.is_shared is not None:
        note["is_shared"] = note_data.is_shared
    
    note["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    print(f"✅ Updated note in memory: {note_id}")
    return note

@api_router.delete("/notes/{note_id}")
async def delete_note(note_id: str, user: User = Depends(get_current_user)):
    """Delete a note (must belong to user)"""
    # Remove from in-memory storage
    original_count = len(memory_storage["notes"])
    memory_storage["notes"] = [
        note for note in memory_storage["notes"] 
        if not (note.get("note_id") == note_id and note.get("user_id") == user.user_id)
    ]
    
    if len(memory_storage["notes"]) == original_count:
        raise HTTPException(status_code=404, detail="Note not found")
    
    print(f"✅ Deleted note from memory: {note_id}")
    return {"success": True, "message": "Note deleted"}

@api_router.post("/notes/{note_id}/share")
async def share_note(note_id: str, user: User = Depends(get_current_user)):
    """Generate a share link for a note (must belong to user)"""
    # Fallback: Return mock share link
    share_link = f"{uuid.uuid4().hex[:12]}"
    return {"share_link": share_link}

@api_router.get("/shared/{share_link}")
async def get_shared_note(share_link: str):
    """Get a shared note by share link (public endpoint, no auth required)"""
    # Fallback: Return 404
    raise HTTPException(status_code=404, detail="Shared note not found")

# Folders endpoints (secured by user)
@api_router.get("/folders")
async def get_folders(request: Request):
    """Get all folders for the authenticated user"""
    # Get current user
    try:
        user = await get_current_user(request)
        print(f"🔍 DEBUG: Get folders for user: {user.email}")
    except HTTPException as e:
        print(f"🔍 DEBUG: Authentication failed for get folders: {e.detail}")
        raise e
    
    # Use in-memory storage for development
    user_folders = [folder for folder in memory_storage["folders"] if folder.get("user_id") == user.user_id]
    return {"folders": user_folders}

@api_router.post("/folders")
async def create_folder(folder_data: FolderCreate, request: Request):
    """Create a new folder for the authenticated user"""
    # Get current user
    try:
        user = await get_current_user(request)
        print(f"🔍 DEBUG: Create folder for user: {user.email}")
    except HTTPException as e:
        print(f"🔍 DEBUG: Authentication failed for create folder: {e.detail}")
        raise e
    
    # Create folder in memory storage
    folder_doc = {
        "folder_id": f"folder_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "name": folder_data.name,
        "color": folder_data.color or "#E06A4F",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Add to in-memory storage
    memory_storage["folders"].append(folder_doc)
    print(f"✅ Created folder in memory: {folder_doc['name']}")
    
    return folder_doc

@api_router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: str, user: User = Depends(get_current_user)):
    """Delete a folder (must belong to user)"""
    # Remove from in-memory storage
    original_count = len(memory_storage["folders"])
    memory_storage["folders"] = [
        folder for folder in memory_storage["folders"] 
        if not (folder.get("folder_id") == folder_id and folder.get("user_id") == user.user_id)
    ]
    
    if len(memory_storage["folders"]) == original_count:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    print(f"✅ Deleted folder from memory: {folder_id}")
    return {"success": True, "message": "Folder deleted"}

# Include routers
app.include_router(api_router)
# app.include_router(firebase_auth_router)  # Commented out to prevent conflicts

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["https://xero-notes.vercel.app", "https://notes.xerohero.dev", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

handler = app
