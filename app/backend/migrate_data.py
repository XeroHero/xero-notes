"""
Migration script to add user_id to existing notes and folders
Run this once to secure existing data
"""

from pymongo import MongoClient
from dotenv import load_dotenv
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
MONGO_URI = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def migrate_notes():
    """Add user_id to notes that don't have it"""
    print("Migrating notes...")
    
    # Find notes without user_id
    notes_without_user = db.notes.find({"user_id": {"$exists": False}})
    notes_list = list(notes_without_user)
    
    if not notes_list:
        print("✓ All notes already have user_id")
        return
    
    print(f"Found {len(notes_list)} notes without user_id")
    
    # For now, assign them to a legacy user
    # In production, you might want a different strategy
    legacy_user_id = "user_legacy_001"
    
    result = db.notes.update_many(
        {"user_id": {"$exists": False}},
        {"$set": {"user_id": legacy_user_id}}
    )
    
    print(f"✓ Updated {result.modified_count} notes with user_id: {legacy_user_id}")

def migrate_folders():
    """Add user_id to folders that don't have it"""
    print("\nMigrating folders...")
    
    folders_without_user = db.folders.find({"user_id": {"$exists": False}})
    folders_list = list(folders_without_user)
    
    if not folders_list:
        print("✓ All folders already have user_id")
        return
    
    print(f"Found {len(folders_list)} folders without user_id")
    
    legacy_user_id = "user_legacy_001"
    
    result = db.folders.update_many(
        {"user_id": {"$exists": False}},
        {"$set": {"user_id": legacy_user_id}}
    )
    
    print(f"✓ Updated {result.modified_count} folders with user_id: {legacy_user_id}")

def create_indexes():
    """Create indexes for better performance"""
    print("\nCreating indexes...")
    
    # Users indexes
    db.users.create_index("firebase_uid", unique=True)
    db.users.create_index("email", unique=True)
    print("✓ Users indexes created")
    
    # Sessions indexes
    db.user_sessions.create_index("session_token", unique=True)
    db.user_sessions.create_index("user_id")
    db.user_sessions.create_index("expires_at", expireAfterSeconds=0)
    print("✓ Sessions indexes created")
    
    # Notes indexes
    db.notes.create_index([("user_id", 1), ("created_at", -1)])
    db.notes.create_index("share_link")
    print("✓ Notes indexes created")
    
    # Folders indexes
    db.folders.create_index("user_id")
    print("✓ Folders indexes created")

def verify_migration():
    """Verify the migration was successful"""
    print("\nVerifying migration...")
    
    # Check notes
    notes_count = db.notes.count_documents({})
    notes_with_user = db.notes.count_documents({"user_id": {"$exists": True}})
    print(f"Notes: {notes_with_user}/{notes_count} have user_id")
    
    # Check folders
    folders_count = db.folders.count_documents({})
    folders_with_user = db.folders.count_documents({"user_id": {"$exists": True}})
    print(f"Folders: {folders_with_user}/{folders_count} have user_id")
    
    if notes_count == notes_with_user and folders_count == folders_with_user:
        print("\n✓ Migration completed successfully!")
    else:
        print("\n⚠ Some documents may still need migration")

if __name__ == "__main__":
    print("=" * 50)
    print("Xero Notes Database Migration")
    print("=" * 50)
    
    try:
        migrate_notes()
        migrate_folders()
        create_indexes()
        verify_migration()
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        raise
    finally:
        client.close()
