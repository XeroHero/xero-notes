# Vercel Environment Variables Setup for Google Authentication

## Required Environment Variables

### Firebase Configuration
You'll need these from your Firebase project settings:

```bash
# Frontend (React) Environment Variables
REACT_APP_FIREBASE_API_KEY=your_firebase_api_key
REACT_APP_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your-project-id
REACT_APP_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
REACT_APP_FIREBASE_APP_ID=your_app_id
REACT_APP_FIREBASE_MEASUREMENT_ID=your_measurement_id

# Backend (Python) Environment Variables
FIREBASE_ADMIN_JSON=your_firebase_admin_sdk_json
MONGO_URL=your_mongodb_connection_string
DB_NAME=xero_notes
```

## Step-by-Step Setup

### 1. Firebase Project Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing one
3. Enable Authentication → Google Sign-in
4. Add your web app to get Firebase config

### 2. Get Firebase Web Config

In Firebase Console → Project Settings → General → Your apps → Web app:

```json
{
  "apiKey": "your-api-key",
  "authDomain": "your-project-id.firebaseapp.com",
  "projectId": "your-project-id",
  "storageBucket": "your-project-id.appspot.com",
  "messagingSenderId": "123456789",
  "appId": "1:123456789:web:abcdef",
  "measurementId": "G-XXXXXXXXX"
}
```

### 3. Get Firebase Admin SDK

In Firebase Console → Project Settings → Service accounts → Generate new private key:

Download the JSON file and copy its contents.

### 4. MongoDB Setup

1. Create a free MongoDB Atlas account
2. Create a cluster
3. Get connection string

### 5. Vercel Environment Variables

Go to your Vercel project → Settings → Environment Variables and add:

#### Frontend Variables (REACT_APP_*):
```
REACT_APP_FIREBASE_API_KEY=AIzaSy...your-api-key
REACT_APP_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your-project-id
REACT_APP_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=123456789
REACT_APP_FIREBASE_APP_ID=1:123456789:web:abcdef
REACT_APP_FIREBASE_MEASUREMENT_ID=G-XXXXXXXXX
```

#### Backend Variables:
```
FIREBASE_ADMIN_JSON={"type":"service_account","project_id":"your-project-id","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=xero_notes
```

### 6. Firebase Auth Domain Configuration

In Firebase Console → Authentication → Settings → Authorized domains, add:
- `localhost` (for development)
- `your-vercel-domain.vercel.app` (for production)
- `your-custom-domain.com` (if using custom domain)

### 7. Deploy to Vercel

1. Push your changes to GitHub
2. Vercel will automatically deploy
3. Environment variables will be applied

## Testing

1. Go to your deployed app
2. Click "Continue with Google"
3. Should redirect to Google sign-in
4. After sign-in, should redirect back to your dashboard

## Troubleshooting

### Common Issues:

1. **"Firebase project not initialized"**
   - Check FIREBASE_ADMIN_JSON is properly formatted
   - Ensure no newlines in the JSON string

2. **"Unauthorized domain"**
   - Add your Vercel domain to Firebase authorized domains

3. **"Token verification failed"**
   - Check Firebase project ID matches between frontend and backend

4. **CORS issues**
   - Backend already has CORS middleware configured

### Debug Mode:

Add this to your Vercel environment variables to see more logs:
```
PYTHONPATH=/app
```

## Local Development

Create a `.env.local` file in your project root:

```bash
# Frontend variables
REACT_APP_FIREBASE_API_KEY=your_local_api_key
REACT_APP_FIREBASE_AUTH_DOMAIN=localhost
REACT_APP_FIREBASE_PROJECT_ID=your-project-id
REACT_APP_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=123456789
REACT_APP_FIREBASE_APP_ID=1:123456789:web:abcdef
REACT_APP_FIREBASE_MEASUREMENT_ID=G-XXXXXXXXX

# Backend variables
FIREBASE_ADMIN_JSON=@./firebase-admin.json
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=xero_notes
```

Note: Use `@./firebase-admin.json` to load from file in local development.
