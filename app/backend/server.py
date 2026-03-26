
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection (for user sessions/auth)
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Firebase Admin SDK initialization
cred = credentials.Certificate(ROOT_DIR / 'firebase-admin.json')
firebase_app = firebase_admin.initialize_app(cred)
firestore_db = firestore.client()

app = FastAPI()
api_router = APIRouter(prefix=\"/api\")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Models
class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionData(BaseModel):
    session_id: str

class FolderCreate(BaseModel):
    name: str
    color: Optional[str] = \"#E06A4F\"

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None

class Folder(BaseModel):
    folder_id: str
    user_id: str
    name: str
    color: str
    created_at: str
    updated_at: str

class NoteCreate(BaseModel):
    title: str
    content: str = \"\"
    folder_id: Optional[str] = None
    is_shared: bool = False

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    folder_id: Optional[str] = None
    is_shared: Optional[bool] = None

class Note(BaseModel):
    note_id: str
    user_id: str
    title: str
    content: str
    folder_id: Optional[str]
    is_shared: bool
    share_link: Optional[str]
    created_at: str
    updated_at: str

class ShareNoteResponse(BaseModel):
    share_link: str

# Auth helper
async def get_current_user(request: Request) -> User:
    session_token = request.cookies.get(\"session_token\")

    if not session_token:
        auth_header = request.headers.get(\"Authorization\")
    if auth_header and auth_header.startswith(\"Bearer \"):
    session_token = auth_header.split(\" \")[1]

    if not session_token:
        raise HTTPException(status_code=401, detail=\"Not authenticated\")

    session_doc = await db.user_sessions.find_one({\"session_token\": session_token}, {\"_id\": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail=\"Invalid session\")

    expires_at = session_doc[\"expires_at\"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail=\"Session expired\")

    user_doc = await db.users.find_one({\"user_id\": session_doc[\"user_id\"]}, {\"_id\": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail=\"User not found\")

    if isinstance(user_doc.get(\"created_at\"), str):
    user_doc[\"created_at\"] = datetime.fromisoformat(user_doc[\"created_at\"])

    return User(**user_doc)

# Auth endpoints
@api_router.post(\"/auth/session\")
async def exchange_session(data: SessionData, response: Response):
    \"\"\"Exchange session_id for session_token via Emergent Auth\"\"\"
    try:
        async with httpx.AsyncClient() as http_client:
            resp = await http_client.get(
            \"https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data\",
            headers={\"X-Session-ID\": data.session_id}
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail=\"Invalid session_id\")

            auth_data = resp.json()
    except httpx.RequestError as e:
        logger.error(f\"Auth request failed: {e}\")
        raise HTTPException(status_code=500, detail=\"Authentication service unavailable\")

        existing_user = await db.users.find_one({\"email\": auth_data[\"email\"]}, {\"_id\": 0})

        if existing_user:
            user_id = existing_user[\"user_id\"]
        await db.users.update_one(
            {\"user_id\": user_id},
        {\"$set\": {\"name\": auth_data[\"name\"], \"picture\": auth_data.get(\"picture\")}}
        )
        else:
        user_id = f\"user_{uuid.uuid4().hex[:12]}\"
        user_doc = {
        \"user_id\": user_id,
        \"email\": auth_data[\"email\"],
        \"name\": auth_data[\"name\"],
        \"picture\": auth_data.get(\"picture\"),
        \"created_at\": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)

        # Create default folder in Firestore for new user
        default_folder = {
        \"folder_id\": f\"folder_{uuid.uuid4().hex[:12]}\",
        \"user_id\": user_id,
        \"name\": \"My Notes\",
        \"color\": \"#E06A4F\",
        \"created_at\": datetime.now(timezone.utc).isoformat(),
        \"updated_at\": datetime.now(timezone.utc).isoformat()
        }
        firestore_db.collection(\"folders\").document(default_folder[\"folder_id\"]).set(default_folder)

        session_token = auth_data[\"session_token\"]
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        session_doc = {
        \"user_id\": user_id,
        \"session_token\": session_token,
        \"expires_at\": expires_at.isoformat(),
        \"created_at\": datetime.now(timezone.utc).isoformat()
        }

        await db.user_sessions.delete_many({\"user_id\": user_id})
        await db.user_sessions.insert_one(session_doc)

        response.set_cookie(
            key=\"session_token\",
        value=session_token,
        httponly=True,
        secure=True,
        samesite=\"none\",
        path=\"/\",
        max_age=7 * 24 * 60 * 60
        )

        user_doc = await db.users.find_one({\"user_id\": user_id}, {\"_id\": 0})
    return user_doc

@api_router.get(\"/auth/me\")
async def get_me(user: User = Depends(get_current_user)):
    return user.model_dump()

@api_router.post(\"/auth/logout\")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get(\"session_token\")
    if session_token:
        await db.user_sessions.delete_many({\"session_token\": session_token})

    response.delete_cookie(key=\"session_token\", path=\"/\", samesite=\"none\", secure=True)
    return {\"message\": \"Logged out\"}

             # Folder endpoints (Firestore)
             @api_router.get(\"/folders\", response_model=List[Folder])
    async def get_folders(user: User = Depends(get_current_user)):
        folders_ref = firestore_db.collection(\"folders\")
        query = folders_ref.where(filter=FieldFilter(\"user_id\", \"==\", user.user_id))
        docs = query.stream()

        folders = []
        for doc in docs:
            folder_data = doc.to_dict()
        folders.append(folder_data)

        return folders

    @api_router.post(\"/folders\", response_model=Folder)
    async def create_folder(data: FolderCreate, user: User = Depends(get_current_user)):
        now = datetime.now(timezone.utc).isoformat()
        folder_id = f\"folder_{uuid.uuid4().hex[:12]}\"

        folder = {
        \"folder_id\": folder_id,
        \"user_id\": user.user_id,
        \"name\": data.name,
        \"color\": data.color or \"#E06A4F\",
        \"created_at\": now,
        \"updated_at\": now
        }

        firestore_db.collection(\"folders\").document(folder_id).set(folder)
        return folder

    @api_router.put(\"/folders/{folder_id}\", response_model=Folder)
    async def update_folder(folder_id: str, data: FolderUpdate, user: User = Depends(get_current_user)):
        folder_ref = firestore_db.collection(\"folders\").document(folder_id)
        folder_doc = folder_ref.get()

        if not folder_doc.exists:
            raise HTTPException(status_code=404, detail=\"Folder not found\")

        folder_data = folder_doc.to_dict()
        if folder_data.get(\"user_id\") != user.user_id:
        raise HTTPException(status_code=404, detail=\"Folder not found\")

        update_data = {\"updated_at\": datetime.now(timezone.utc).isoformat()}
        if data.name is not None:
            update_data[\"name\"] = data.name
        if data.color is not None:
            update_data[\"color\"] = data.color

        folder_ref.update(update_data)

        updated_doc = folder_ref.get()
        return updated_doc.to_dict()

    @api_router.delete(\"/folders/{folder_id}\")
    async def delete_folder(folder_id: str, user: User = Depends(get_current_user)):
        folder_ref = firestore_db.collection(\"folders\").document(folder_id)
        folder_doc = folder_ref.get()

        if not folder_doc.exists:
            raise HTTPException(status_code=404, detail=\"Folder not found\")

        folder_data = folder_doc.to_dict()
        if folder_data.get(\"user_id\") != user.user_id:
        raise HTTPException(status_code=404, detail=\"Folder not found\")

        # Move notes to no folder
        notes_ref = firestore_db.collection(\"notes\")
        notes_query = notes_ref.where(filter=FieldFilter(\"folder_id\", \"==\", folder_id))
        for note_doc in notes_query.stream():
            note_doc.reference.update({\"folder_id\": None})

        folder_ref.delete()
        return {\"message\": \"Folder deleted\"}

                 # Note endpoints (Firestore)
                 @api_router.get(\"/notes\", response_model=List[Note])
        async def get_notes(folder_id: Optional[str] = None, search: Optional[str] = None, user: User = Depends(get_current_user)):
            notes_ref = firestore_db.collection(\"notes\")
            query = notes_ref.where(filter=FieldFilter(\"user_id\", \"==\", user.user_id))

            if folder_id:
                query = query.where(filter=FieldFilter(\"folder_id\", \"==\", folder_id))

            docs = query.order_by(\"updated_at\", direction=firestore.Query.DESCENDING).stream()

            notes = []
            for doc in docs:
                note_data = doc.to_dict()
            # Client-side search filtering (Firestore doesn't support full-text search)
            if search:
                search_lower = search.lower()
                if search_lower not in note_data.get(\"title\", \"\").lower() and search_lower not in note_data.get(\"content\", \"\").lower():
            continue
            notes.append(note_data)

        return notes

    @api_router.get(\"/notes/{note_id}\", response_model=Note)
    async def get_note(note_id: str, user: User = Depends(get_current_user)):
        note_ref = firestore_db.collection(\"notes\").document(note_id)
        note_doc = note_ref.get()

        if not note_doc.exists:
            raise HTTPException(status_code=404, detail=\"Note not found\")

        note_data = note_doc.to_dict()
        if note_data.get(\"user_id\") != user.user_id:
        raise HTTPException(status_code=404, detail=\"Note not found\")

        return note_data

    @api_router.post(\"/notes\", response_model=Note)
    async def create_note(data: NoteCreate, user: User = Depends(get_current_user)):
        now = datetime.now(timezone.utc).isoformat()
        note_id = f\"note_{uuid.uuid4().hex[:12]}\"

        note = {
        \"note_id\": note_id,
        \"user_id\": user.user_id,
        \"title\": data.title,
        \"content\": data.content,
        \"folder_id\": data.folder_id,
        \"is_shared\": data.is_shared,
        \"share_link\": f\"share_{uuid.uuid4().hex[:16]}\" if data.is_shared else None,
        \"created_at\": now,
        \"updated_at\": now
        }

        firestore_db.collection(\"notes\").document(note_id).set(note)
        return note

    @api_router.put(\"/notes/{note_id}\", response_model=Note)
    async def update_note(note_id: str, data: NoteUpdate, user: User = Depends(get_current_user)):
        note_ref = firestore_db.collection(\"notes\").document(note_id)
        note_doc = note_ref.get()

        if not note_doc.exists:
            raise HTTPException(status_code=404, detail=\"Note not found\")

        note_data = note_doc.to_dict()
        if note_data.get(\"user_id\") != user.user_id:
        raise HTTPException(status_code=404, detail=\"Note not found\")

        update_data = {\"updated_at\": datetime.now(timezone.utc).isoformat()}
        if data.title is not None:
            update_data[\"title\"] = data.title
        if data.content is not None:
            update_data[\"content\"] = data.content
        if data.folder_id is not None:
            update_data[\"folder_id\"] = data.folder_id
        if data.is_shared is not None:
            update_data[\"is_shared\"] = data.is_shared
        if data.is_shared and not note_data.get(\"share_link\"):
        update_data[\"share_link\"] = f\"share_{uuid.uuid4().hex[:16]}\"

        note_ref.update(update_data)

        updated_doc = note_ref.get()
        return updated_doc.to_dict()

    @api_router.delete(\"/notes/{note_id}\")
    async def delete_note(note_id: str, user: User = Depends(get_current_user)):
        note_ref = firestore_db.collection(\"notes\").document(note_id)
        note_doc = note_ref.get()

        if not note_doc.exists:
            raise HTTPException(status_code=404, detail=\"Note not found\")

        note_data = note_doc.to_dict()
        if note_data.get(\"user_id\") != user.user_id:
        raise HTTPException(status_code=404, detail=\"Note not found\")

        note_ref.delete()
        return {\"message\": \"Note deleted\"}

                 @api_router.post(\"/notes/{note_id}/share\", response_model=ShareNoteResponse)
        async def share_note(note_id: str, user: User = Depends(get_current_user)):
            note_ref = firestore_db.collection(\"notes\").document(note_id)
            note_doc = note_ref.get()

            if not note_doc.exists:
                raise HTTPException(status_code=404, detail=\"Note not found\")

            note_data = note_doc.to_dict()
            if note_data.get(\"user_id\") != user.user_id:
            raise HTTPException(status_code=404, detail=\"Note not found\")

            share_link = note_data.get(\"share_link\") or f\"share_{uuid.uuid4().hex[:16]}\"
            note_ref.update({\"is_shared\": True, \"share_link\": share_link})

            return {\"share_link\": share_link}

                     # Public shared note endpoint (no auth required)
                     @api_router.get(\"/shared/{share_link}\")
            async def get_shared_note(share_link: str):
                notes_ref = firestore_db.collection(\"notes\")
                query = notes_ref.where(filter=FieldFilter(\"share_link\", \"==\", share_link)).where(filter=FieldFilter(\"is_shared\", \"==\", True))
                docs = list(query.stream())

                if not docs:
                    raise HTTPException(status_code=404, detail=\"Shared note not found\")

                note_data = docs[0].to_dict()

                # Get author info from MongoDB
                user_doc = await db.users.find_one({\"user_id\": note_data[\"user_id\"]}, {\"_id\": 0, \"name\": 1, \"picture\": 1})

                return {
                \"note\": note_data,
                \"author\": user_doc
                }

                # Health check
                @api_router.get(\"/health\")
                async def health():
                    return {\"status\": \"healthy\"}

                    app.include_router(api_router)

                    app.add_middleware(
                        CORSMiddleware,
                        allow_credentials=True,
                        allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
                        allow_methods=[\"*\"],
                    allow_headers=[\"*\"],
                    )

                    @app.on_event(\"shutdown\")
                    async def shutdown_db_client():
                        client.close()
                    "
                    Observation: Overwrite successful: /app/backend/server.py