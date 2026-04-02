from fastapi import FastAPI
from datetime import datetime, timezone
import os

app = FastAPI()

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
        "env_vars": {
            "MONGO_URL_set": bool(os.environ.get('MONGO_URL')),
            "DB_NAME_set": bool(os.environ.get('DB_NAME')),
            "FIREBASE_ADMIN_JSON_set": bool(os.environ.get('FIREBASE_ADMIN_JSON'))
        }
    }

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/auth/test")
async def auth_test():
    return {"status": "ok", "message": "Auth test working"}

print("✅ Minimal server loaded successfully")
