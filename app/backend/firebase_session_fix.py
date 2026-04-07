# Firebase login section with proper database session storage
# Replace lines around 558-590 in server.py with this:

        # Store session data in database
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
                # Fallback to memory storage if database fails
                session_store[session_token] = {
                    "user_id": user_id,
                    "email": email,
                    "name": name,
                    "picture": picture,
                    "expires_at": expires_at.isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
        else:
            # Fallback to memory storage if no database
            session_store[session_token] = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        print(f" Session stored for: {email}")
