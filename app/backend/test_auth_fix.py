#!/usr/bin/env python3

import requests
import json

# Test the login endpoints
def test_authentication():
    # Test the test login endpoint (no Firebase required)
    url = "http://127.0.0.1:8001/api/auth/test-login"
    
    try:
        print("=== Testing Test Login Endpoint ===")
        response = requests.post(url, json={})
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Cookies: {response.cookies}")
        print(f"Response: {response.json()}")
        
        # Test if we can access protected endpoints with the session cookie
        session_cookie = response.cookies.get("session_token")
        if session_cookie:
            print(f"\n=== Testing Protected Endpoints with Session Cookie: {session_cookie[:20]}... ===")
            cookies = {"session_token": session_cookie}
            
            # Test folders endpoint
            print("\n--- Testing /api/folders ---")
            folders_response = requests.get("http://127.0.0.1:8001/api/folders", cookies=cookies)
            print(f"Folders endpoint status: {folders_response.status_code}")
            print(f"Folders response: {folders_response.json()}")
            
            # Test notes endpoint
            print("\n--- Testing /api/notes ---")
            notes_response = requests.get("http://127.0.0.1:8001/api/notes", cookies=cookies)
            print(f"Notes endpoint status: {notes_response.status_code}")
            print(f"Notes response: {notes_response.json()}")
            
            # Test creating a folder
            print("\n--- Testing POST /api/folders ---")
            create_folder_response = requests.post(
                "http://127.0.0.1:8001/api/folders", 
                cookies=cookies,
                json={"name": "Test Folder", "color": "#E06A4F"}
            )
            print(f"Create folder status: {create_folder_response.status_code}")
            print(f"Create folder response: {create_folder_response.json()}")
            
            # Test creating a note
            print("\n--- Testing POST /api/notes ---")
            create_note_response = requests.post(
                "http://127.0.0.1:8001/api/notes", 
                cookies=cookies,
                json={"title": "Test Note", "content": "Test content", "is_shared": False}
            )
            print(f"Create note status: {create_note_response.status_code}")
            print(f"Create note response: {create_note_response.json()}")
            
        else:
            print("No session cookie set!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_authentication()
