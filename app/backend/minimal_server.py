from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
import os
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import uuid

app = FastAPI()

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

@app.post("/api/auth/firebase-login")
async def firebase_login(request: FirebaseLoginRequest):
    """Test Firebase login endpoint"""
    try:
        print(f"🔐 Firebase login attempt for user: {request.firebaseUser.email}")
        print(f"📋 Request data: uid={request.firebaseUser.uid}, email={request.firebaseUser.email}")
        
        if not firebase_app:
            print("❌ Firebase Admin SDK not initialized")
            return {
                "error": "Firebase Admin SDK not properly initialized",
                "details": "Check FIREBASE_ADMIN_JSON environment variable",
                "env_vars_set": {
                    "FIREBASE_ADMIN_JSON": bool(os.environ.get('FIREBASE_ADMIN_JSON')),
                    "MONGO_URL": bool(os.environ.get('MONGO_URL')),
                    "DB_NAME": bool(os.environ.get('DB_NAME'))
                }
            }
        
        print("✅ Firebase app is available, attempting token verification...")
        
        # Verify the Firebase token
        try:
            decoded_token = firebase_auth.verify_id_token(request.idToken)
            print(f"✅ Token verified successfully: {decoded_token.get('uid')}")
        except Exception as token_error:
            print(f"❌ Token verification failed: {token_error}")
            return {
                "error": "Token verification failed",
                "details": str(token_error),
                "token_preview": request.idToken[:20] + "..." if request.idToken else "null"
            }
        
        # Ensure the token UID matches the provided user UID
        if decoded_token.get('uid') != request.firebaseUser.uid:
            print(f"❌ Token UID mismatch: {decoded_token.get('uid')} != {request.firebaseUser.uid}")
            return {
                "error": "Token UID mismatch",
                "details": f"Token UID: {decoded_token.get('uid')}, User UID: {request.firebaseUser.uid}"
            }
        
        print(f"✅ Login successful for user: {request.firebaseUser.email}")
        
        return {
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": request.firebaseUser.email,
            "name": request.firebaseUser.displayName,
            "picture": request.firebaseUser.photoURL,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "debug": {
                "token_uid": decoded_token.get('uid'),
                "user_uid": request.firebaseUser.uid,
                "firebase_initialized": firebase_app is not None
            }
        }
        
    except Exception as e:
        print(f"❌ Firebase login error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": "Authentication failed",
            "details": str(e),
            "traceback": traceback.format_exc()
        }

print("✅ Minimal server with Firebase auth loaded successfully")
