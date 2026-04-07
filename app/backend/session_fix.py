# Add this to your server.py file to fix session persistence
# This should be added after the existing session verification logic

async def check_database_session(session_token: str):
    """Check if session exists in database and return user data"""
    try:
        if db is None:
            return None
            
        # Find session in database
        session_doc = await db.user_sessions.find_one({"session_token": session_token})
        if not session_doc:
            return None
            
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
                return None
        
        # Find user data
        user_doc = await db.users.find_one({"user_id": session_doc["user_id"]})
        if not user_doc:
            return None
            
        return {
            "user_id": user_doc["user_id"],
            "email": user_doc["email"],
            "name": user_doc.get("name", ""),
            "picture": user_doc.get("picture", ""),
            "created_at": user_doc.get("created_at")
        }
    except Exception as e:
        print(f"Database session check failed: {e}")
        return None

# Replace the existing session verification in get_current_user_endpoint
# Add this at the beginning of the session check in /api/me endpoint:

# First check database (for persistent sessions)
db_user_data = await check_database_session(session_token)
if db_user_data:
    return db_user_data

# Then fall back to memory store (for temporary sessions)
if session_token in session_store:
    # ... existing memory store logic ...
