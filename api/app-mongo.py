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
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global OPTIONS handler for CORS preflight
@app.options("/{path:path}")
async def global_options(path: str):
    return JSONResponse(
        content={"success": True},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority")
DB_NAME = os.getenv("DB_NAME", "xero_notes")
COLLECTION_NAME = "xero_notes"  # Your collection name

try:
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    db = client[DB_NAME]
    users_collection = db[COLLECTION_NAME]
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
    if users_collection is not None:
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
    if users_collection is not None:
        print("Querying MongoDB...")
        user = users_collection.find_one({
            "username": username,
            "password_hash": hash_password(password)
        })
        if user:
            print(f"Found user in MongoDB: {user}")
            return user
        else:
            print("User not found in MongoDB, checking fallback...")
            # Fallback to mock user
            if username == "lorenzo_mongo" and password == "test123":
                print("Returning mock user")
                return {
                    "user_id": "user_test_123",
                    "username": "lorenzo_mongo",
                    "email": "lorenzo@test.com"
                }
            print("Mock user not found")
            return None
    else:
        print("Using fallback mock user logic")
        # Fallback to mock user
        if username == "lorenzo_mongo" and password == "test123":
            print("Returning mock user")
            return {
                "user_id": "user_test_123",
                "username": "lorenzo_mongo",
                "email": "lorenzo@test.com"
            }
        print("Mock user not found")
        return None

# API endpoints
@app.get("/")
def home():
    return {"message": "Xero Notes API running", "version": "1.0.0", "mongo_connected": users_collection is not None}

@app.get("/api/health")
def health():
    return {"status": "healthy", "message": "FastAPI working on Vercel!", "mongo_connected": users_collection is not None}

@app.post("/api/auth/simple-login")
async def simple_login(request: Request):
    try:
        # Parse request manually first to debug
        body = await request.body()
        print(f"Raw body: {body}")
        
        data = await request.json()
        print(f"Parsed data: {data}")
        
        # Now validate with Pydantic
        login_data = LoginRequest(**data)
        print(f"Validated data: {login_data}")
        
        print("About to call find_user...")
        user = find_user(login_data.username, login_data.password)
        print(f"find_user returned: {user}")
        
        if user:
            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "email": user["email"],
                "message": "Login successful"
            }
        else:
            print("User not found, returning 401")
            raise HTTPException(status_code=401, detail="Invalid username or password")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")  # Debug log
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")

@app.post("/api/auth/test")
async def test_login(request: Request):
    # Debug endpoint to see what's being received
    try:
        body = await request.body()
        data = await request.json()
        return {
            "received_body": str(body),
            "received_data": data,
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

@app.post("/api/auth/simple-signup")
async def simple_signup(signup_data: SignupRequest):
    try:
        # Check if user already exists
        if users_collection is not None:
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

# Notes endpoints
@app.post("/api/notes")
async def create_note(request: Request):
    try:
        data = await request.json()
        title = data.get('title', '')
        content = data.get('content', '')
        user_id = data.get('user_id', 'user_test_123')
        folder_id = data.get('folder_id', None)
        is_shared = data.get('is_shared', False)
        
        if users_collection is not None:
            notes_collection = db.notes
            note_doc = {
                "title": title,
                "content": content,
                "user_id": user_id,
                "folder_id": folder_id,
                "is_shared": is_shared,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "note_id": f"note_{uuid.uuid4().hex[:12]}"
            }
            notes_collection.insert_one(note_doc)
            # Convert ObjectId to string for JSON serialization
            note_doc["_id"] = str(note_doc["_id"])
            return note_doc
        else:
            # Fallback - return mock note
            note_id = f"note_{uuid.uuid4().hex[:12]}"
            return {
                "_id": note_id,
                "note_id": note_id,
                "title": title,
                "content": content,
                "user_id": user_id,
                "folder_id": folder_id,
                "is_shared": is_shared
            }
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.get("/api/notes")
async def get_notes():
    try:
        if users_collection is not None:
            notes_collection = db.notes
            notes = list(notes_collection.find({"user_id": "user_test_123"}))
            # Convert ObjectId to string for JSON serialization
            for note in notes:
                note["_id"] = str(note["_id"])
            return {"notes": notes}
        else:
            # Fallback - return empty notes
            return {"notes": []}
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.put("/api/notes/{note_id}")
async def update_note(note_id: str, request: Request):
    try:
        data = await request.json()
        
        if users_collection is not None:
            notes_collection = db.notes
            # Build update dict with only provided fields
            update_data = {}
            if 'title' in data:
                update_data['title'] = data['title']
            if 'content' in data:
                update_data['content'] = data['content']
            if 'folder_id' in data:
                update_data['folder_id'] = data['folder_id']
            if 'is_shared' in data:
                update_data['is_shared'] = data['is_shared']
            update_data['updated_at'] = datetime.now()
            
            result = notes_collection.update_one(
                {"note_id": note_id},
                {"$set": update_data}
            )
            if result.modified_count > 0 or result.matched_count > 0:
                # Return the updated note
                updated_note = notes_collection.find_one({"note_id": note_id})
                if updated_note:
                    updated_note["_id"] = str(updated_note["_id"])
                    return updated_note
                raise HTTPException(status_code=404, detail="Note not found")
            else:
                raise HTTPException(status_code=404, detail="Note not found")
        else:
            # Fallback - return mock updated note
            return {
                "note_id": note_id,
                "title": data.get('title', ''),
                "content": data.get('content', ''),
                "updated_at": datetime.now().isoformat()
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: str):
    try:
        if users_collection is not None:
            notes_collection = db.notes
            result = notes_collection.delete_one({"note_id": note_id})
            if result.deleted_count > 0:
                return {"success": True, "message": "Note deleted"}
            else:
                raise HTTPException(status_code=404, detail="Note not found")
        else:
            # Fallback - just return success
            return {"success": True, "message": "Note deleted (mock)"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.get("/api/notes/{note_id}")
async def get_note(note_id: str):
    try:
        if users_collection is not None:
            notes_collection = db.notes
            note = notes_collection.find_one({"note_id": note_id})
            if note:
                note["_id"] = str(note["_id"])
                return {"note": note}
            else:
                raise HTTPException(status_code=404, detail="Note not found")
        else:
            # Fallback - return mock note
            return {"note": {"note_id": note_id, "title": "Mock Note", "content": "Mock content"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

# Folders endpoints
@app.get("/api/folders")
async def get_folders():
    try:
        if users_collection is not None:
            folders_collection = db.folders
            folders = list(folders_collection.find({"user_id": "user_test_123"}))
            # Convert ObjectId to string for JSON serialization
            for folder in folders:
                folder["_id"] = str(folder["_id"])
            return {"folders": folders}
        else:
            # Fallback - return empty folders
            return {"folders": []}
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.post("/api/folders")
async def create_folder(request: Request):
    try:
        data = await request.json()
        name = data.get('name', '')
        user_id = data.get('user_id', 'user_test_123')
        
        if users_collection is not None:
            folders_collection = db.folders
            folder_doc = {
                "name": name,
                "user_id": user_id,
                "created_at": datetime.now(),
                "folder_id": f"folder_{uuid.uuid4().hex[:12]}"
            }
            folders_collection.insert_one(folder_doc)
            return {"success": True, "folder_id": folder_doc["folder_id"]}
        else:
            # Fallback - just return success
            return {"success": True, "folder_id": f"folder_{uuid.uuid4().hex[:12]}"}
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.delete("/api/folders/{folder_id}")
async def delete_folder(folder_id: str):
    try:
        if users_collection is not None:
            folders_collection = db.folders
            result = folders_collection.delete_one({"folder_id": folder_id})
            if result.deleted_count > 0:
                return {"success": True, "message": "Folder deleted"}
            else:
                raise HTTPException(status_code=404, detail="Folder not found")
        else:
            # Fallback - just return success
            return {"success": True, "message": "Folder deleted (mock)"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

handler = app
