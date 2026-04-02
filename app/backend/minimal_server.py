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

try:
    if firebase_admin_json:
        import json
        firebase_config = json.loads(firebase_admin_json)
        cred = credentials.Certificate(firebase_config)
        firebase_app = firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK initialized from environment variable")
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
        print(f"Firebase login attempt for user: {request.firebaseUser.email}")
        
        if not firebase_app:
            print("❌ Firebase Admin SDK not initialized")
            raise HTTPException(status_code=500, detail="Firebase Admin SDK not properly initialized")
        
        # Verify the Firebase token
        try:
            decoded_token = firebase_auth.verify_id_token(request.idToken)
            print(f"Token verified successfully: {decoded_token.get('uid')}")
        except Exception as token_error:
            print(f"Token verification failed: {token_error}")
            raise HTTPException(status_code=401, detail=f"Token verification failed: {str(token_error)}")
        
        # Ensure the token UID matches the provided user UID
        if decoded_token.get('uid') != request.firebaseUser.uid:
            raise HTTPException(status_code=401, detail="Token UID mismatch")
        
        print(f"Login successful for user: {request.firebaseUser.email}")
        
        return {
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": request.firebaseUser.email,
            "name": request.firebaseUser.displayName,
            "picture": request.firebaseUser.photoURL,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Firebase login error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

print("✅ Minimal server with Firebase auth loaded successfully")
