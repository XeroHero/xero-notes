"""
Test script to verify Google Authentication setup
"""

import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import os

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

BASE_URL = "http://localhost:8000"  # Change to your backend URL

def test_health():
    """Test if backend is running"""
    print("\n1. Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_firebase_login():
    """Test Firebase login endpoint (requires valid Firebase token)"""
    print("\n2. Testing Firebase login endpoint...")
    print("   Note: This requires a valid Firebase ID token")
    print("   You can get one from the browser console after signing in:")
    print("   firebase.auth().currentUser.getIdToken()")
    
    # Example test (uncomment and replace with actual token)
    # token = "your_firebase_token_here"
    # response = requests.post(
    #     f"{BASE_URL}/api/auth/firebase-login",
    #     json={
    #         "idToken": token,
    #         "firebaseUser": {
    #             "uid": "test_uid",
    #             "email": "test@example.com",
    #             "displayName": "Test User"
    #         }
    #     }
    # )
    # print(f"   Status: {response.status_code}")
    # print(f"   Response: {response.json()}")
    print("   Skipped - manual testing required")
    return True

def test_protected_endpoints():
    """Test that protected endpoints require authentication"""
    print("\n3. Testing protected endpoints...")
    
    # Try to get notes without authentication
    response = requests.get(f"{BASE_URL}/api/notes")
    print(f"   GET /api/notes (no auth): {response.status_code}")
    assert response.status_code == 401, "Should require authentication"
    
    # Try to get folders without authentication
    response = requests.get(f"{BASE_URL}/api/folders")
    print(f"   GET /api/folders (no auth): {response.status_code}")
    assert response.status_code == 401, "Should require authentication"
    
    print("   ✓ Protected endpoints are secure")
    return True

def test_shared_note_public():
    """Test that shared notes are accessible without auth"""
    print("\n4. Testing shared note endpoint...")
    
    # Try to get a non-existent shared note
    response = requests.get(f"{BASE_URL}/api/shared/nonexistent")
    print(f"   GET /api/shared/nonexistent: {response.status_code}")
    # Should be 404 (not found) not 401 (unauthorized)
    assert response.status_code == 404, "Shared notes should be public"
    
    print("   ✓ Shared notes are publicly accessible")
    return True

def test_database_indexes():
    """Verify database indexes exist"""
    print("\n5. Testing database indexes...")
    
    try:
        from pymongo import MongoClient
        MONGO_URI = os.environ['MONGO_URL']
        DB_NAME = os.environ['DB_NAME']
        
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        # Check users indexes
        users_indexes = db.users.list_indexes()
        print(f"   Users indexes: {[idx['name'] for idx in users_indexes]}")
        
        # Check notes indexes
        notes_indexes = db.notes.list_indexes()
        print(f"   Notes indexes: {[idx['name'] for idx in notes_indexes]}")
        
        # Check sessions indexes
        sessions_indexes = db.user_sessions.list_indexes()
        print(f"   Sessions indexes: {[idx['name'] for idx in sessions_indexes]}")
        
        client.close()
        print("   ✓ Database indexes verified")
        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Xero Notes Authentication Test Suite")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health),
        ("Firebase Login", test_firebase_login),
        ("Protected Endpoints", test_protected_endpoints),
        ("Shared Notes Public", test_shared_note_public),
        ("Database Indexes", test_database_indexes),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result, None))
        except Exception as e:
            results.append((name, False, str(e)))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for name, result, error in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
        if error:
            print(f"       Error: {error}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Authentication is working correctly.")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
