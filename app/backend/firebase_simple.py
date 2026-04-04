# Firebase Admin SDK initialization - Simplified approach
firebase_admin_json = os.environ.get('FIREBASE_ADMIN_JSON')
firebase_app = None

print(f"🔍 Firebase Admin SDK initialization check:")
print(f"   FIREBASE_ADMIN_JSON exists: {bool(firebase_admin_json)}")

# Try individual environment variables first (simpler and more reliable)
try:
    firebase_type = os.environ.get('FIREBASE_TYPE', 'service_account')
    firebase_project_id = os.environ.get('FIREBASE_PROJECT_ID', 'xero-notes')
    firebase_private_key_id = os.environ.get('FIREBASE_PRIVATE_KEY_ID', '594bb7e380083a61a39556eed63eb9c0f25e441a')
    firebase_client_email = os.environ.get('FIREBASE_CLIENT_EMAIL', 'firebase-adminsdk-fbsvc@xero-notes.iam.gserviceaccount.com')
    firebase_client_id = os.environ.get('FIREBASE_CLIENT_ID', '100717736424180417094')
    firebase_auth_uri = os.environ.get('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth')
    firebase_token_uri = os.environ.get('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token')
    firebase_auth_provider = os.environ.get('FIREBASE_AUTH_PROVIDER', 'https://www.googleapis.com/oauth2/v1/certs')
    firebase_client_cert = os.environ.get('FIREBASE_CLIENT_CERT', 'https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40xero-notes.iam.gserviceaccount.com')
    firebase_universe = os.environ.get('FIREBASE_UNIVERSE', 'googleapis.com')
    
    # Get private key from individual env var or fallback to JSON
    firebase_private_key = os.environ.get('FIREBASE_PRIVATE_KEY')
    if not firebase_private_key and firebase_admin_json:
        # Try to extract from JSON if individual env var not set
        try:
            if firebase_admin_json and '-----BEGIN PRIVATE KEY-----' in firebase_admin_json:
                start = firebase_admin_json.find('-----BEGIN PRIVATE KEY-----')
                end = firebase_admin_json.find('-----END PRIVATE KEY-----', start)
                if start != -1 and end != -1:
                    private_key_section = firebase_admin_json[start:end + len('-----END PRIVATE KEY-----')]
                    firebase_private_key = private_key_section.replace('\\\\n', '\n').replace('\\n', '\n')
                    print("✅ Extracted private key from JSON")
        except Exception as e:
            print(f"❌ Failed to extract from JSON: {e}")
    
    if firebase_private_key:
        print("✅ Using individual environment variables")
        firebase_config = {
            "type": firebase_type,
            "project_id": firebase_project_id,
            "private_key_id": firebase_private_key_id,
            "private_key": firebase_private_key,
            "client_email": firebase_client_email,
            "client_id": firebase_client_id,
            "auth_uri": firebase_auth_uri,
            "token_uri": firebase_token_uri,
            "auth_provider_x509_cert_url": firebase_auth_provider,
            "client_x509_cert_url": firebase_client_cert,
            "universe_domain": firebase_universe
        }
    else:
        print("⚠️ No individual Firebase environment variables found")
        firebase_config = None
    
    if firebase_config:
        print(f"   Config keys: {list(firebase_config.keys())}")
        print(f"   Project ID: {firebase_config.get('project_id', 'NOT_FOUND')}")
        print(f"   Client email: {firebase_config.get('client_email', 'NOT_FOUND')}")
        
        # Check if app already exists
        try:
            firebase_app = firebase_admin.get_app()
            print("✅ Using existing Firebase app")
        except ValueError:
            # App doesn't exist, initialize it
            if firebase_config:
                cred = credentials.Certificate(firebase_config)
                firebase_app = firebase_admin.initialize_app(cred)
                print("✅ Firebase Admin SDK initialized from individual environment variables")
            else:
                print("❌ Firebase config is None, cannot initialize")
        
except Exception as e:
    print(f"❌ Firebase initialization failed: {e}")
    import traceback
    traceback.print_exc()
    firebase_app = None

# Additional debugging for Firebase initialization
print(f"🔍 Final Firebase app status: {firebase_app is not None}")
if firebase_app:
    print(f"🔍 Firebase app name: {firebase_app.name}")
else:
    print("🚨 Firebase app is None - this will cause authentication failures")
