# SESSION PERSISTENCE FIX
# 
# The issue: Sessions are stored in memory (session_store) instead of database
# This causes sessions to be lost on refresh/restart
#
# SOLUTION: Update the session verification in server.py
#
# 1. FIND this section around line 581 in server.py:
#    # Check if session exists in session store (real Firebase users)
#    if session_token in session_store:
#
# 2. REPLACE the entire session verification section with this:

async def get_current_user_endpoint(request: Request):
    """Get current authenticated user (for session verification)"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # FIRST: Check database sessions (persistent)
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
                    else:
                        # Session valid, find user data
                        user_doc = await db.users.find_one({"user_id": session_doc["user_id"]})
                        if user_doc:
                            return {
                                "user_id": user_doc["user_id"],
                                "email": user_doc["email"],
                                "name": user_doc.get("name", ""),
                                "picture": user_doc.get("picture", ""),
                                "created_at": user_doc.get("created_at")
                            }
        except Exception as e:
            print(f"Database session check failed: {e}")
    
    # SECOND: Check memory sessions (fallback)
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

#
# 3. ALSO UPDATE the Firebase login section around line 530 to save to database:
#
# REPLACE:
#     # Store session data in memory
#     session_store[session_token] = { ... }
#
# WITH:
#     # Store session data in database
#     if db is not None:
#         try:
#             session_doc = {
#                 "user_id": user_id,
#                 "session_token": session_token,
#                 "expires_at": expires_at.isoformat(),
#                 "created_at": datetime.now(timezone.utc).isoformat()
#             }
#             
#             # Delete existing sessions for this user
#             await db.user_sessions.delete_many({"user_id": user_id})
#             # Insert new session
#             await db.user_sessions.insert_one(session_doc)
#             print(f" Firebase session created in database for: {email}")
#         except Exception as session_error:
#             print(f" Session creation failed, falling back to memory: {session_error}")
#             # Fallback to memory storage if database fails
#             session_store[session_token] = {
#                 "user_id": user_id,
#                 "email": email,
#                 "name": name,
#                 "picture": picture,
#                 "expires_at": expires_at.isoformat(),
#                 "created_at": datetime.now(timezone.utc).isoformat()
#             }
#     else:
#         # Fallback to memory storage if no database
#         session_store[session_token] = {
#             "user_id": user_id,
#             "email": email,
#             "name": name,
#             "picture": picture,
#             "expires_at": expires_at.isoformat(),
#             "created_at": datetime.now(timezone.utc).isoformat()
#         }
