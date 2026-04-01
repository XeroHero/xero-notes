# Google Authentication Setup Guide

This guide will help you set up Google Authentication for Xero Notes so that each user can only see their own notes.

## Overview

The authentication system uses:
- **Firebase Authentication** (Google Sign-In) on the frontend
- **Firebase Admin SDK** on the backend to verify tokens
- **MongoDB** to store user sessions and data
- **Session cookies** for authenticated API requests

## Step 1: Firebase Console Setup

### 1.1 Create a Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" or select your existing "xero-notes" project
3. Follow the setup wizard

### 1.2 Enable Google Sign-In
1. In Firebase Console, go to **Authentication** → **Sign-in method**
2. Click on **Google** and enable it
3. Add your authorized domains:
   - `localhost` (for development)
   - `xero-notes.vercel.app` (for production)
   - Any custom domain you're using
4. Save the configuration

### 1.3 Get Firebase Web App Configuration
1. Go to **Project Settings** (gear icon)
2. Scroll down to "Your apps" section
3. If you don't have a web app, click the web icon (</>) to create one
4. Copy the `firebaseConfig` object values
5. Update your `.env` file with these values (already configured in your `.env`)

### 1.4 Generate Firebase Admin SDK Private Key
1. Go to **Project Settings** → **Service accounts**
2. Click **Generate new private key**
3. Click **Generate key** to download the JSON file
4. Save it as `firebase-admin.json` in `app/backend/`
5. **IMPORTANT**: Never commit this file to Git (it's in `.gitignore`)

### 1.5 Set Environment Variable for Vercel
For production deployment, you need to set the Firebase Admin JSON as an environment variable:

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your `xero-notes` project
3. Go to **Settings** → **Environment Variables**
4. Add a new variable:
   - Name: `FIREBASE_ADMIN_JSON`
   - Value: Copy the **entire contents** of your `firebase-admin.json` file (as a JSON string)
5. Redeploy your application

## Step 2: MongoDB Setup

### 2.1 Update MongoDB Collections

Your MongoDB should have these collections:
- `users` - User accounts
- `user_sessions` - Active sessions
- `notes` - User notes (with `user_id` field for isolation)
- `folders` - User folders (with `user_id` field for isolation)

### 2.2 Indexes for Performance

Run these commands in MongoDB Compass or shell to add indexes:

```javascript
// Users collection
db.users.createIndex({ "firebase_uid": 1 }, { unique: true })
db.users.createIndex({ "email": 1 }, { unique: true })

// User sessions collection
db.user_sessions.createIndex({ "session_token": 1 }, { unique: true })
db.user_sessions.createIndex({ "user_id": 1 })
db.user_sessions.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 })

// Notes collection
db.notes.createIndex({ "user_id": 1, "created_at": -1 })
db.notes.createIndex({ "share_link": 1 })

// Folders collection
db.folders.createIndex({ "user_id": 1 })
```

## Step 3: Local Development Setup

### 3.1 Install Dependencies

```bash
# Frontend dependencies
npm install

# Backend dependencies (in app/backend/)
cd app/backend
pip install -r requirements.txt
```

### 3.2 Environment Variables

Make sure your `.env` file has:

```env
# Frontend (.env)
REACT_APP_FIREBASE_API_KEY=your_api_key
REACT_APP_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=xero-notes
REACT_APP_FIREBASE_STORAGE_BUCKET=xero-notes.firebasestorage.app
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
REACT_APP_FIREBASE_APP_ID=your_app_id
REACT_APP_FIREBASE_MEASUREMENT_ID=your_measurement_id

# Backend (app/backend/.env)
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=xero_notes
FIREBASE_ADMIN_JSON={"type":"service_account",...}  # Full JSON content
CORS_ORIGINS=http://localhost:3000
```

### 3.3 Run the Application

```bash
# Terminal 1 - Start backend
cd app/backend
python server.py

# Terminal 2 - Start frontend
npm start
```

## Step 4: Production Deployment

### 4.1 Vercel Environment Variables

Set these in Vercel Dashboard → Project Settings → Environment Variables:

```
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=xero_notes
FIREBASE_ADMIN_JSON={"type":"service_account",...}  # Full JSON as string
CORS_ORIGINS=https://xero-notes.vercel.app
```

### 4.2 Deploy

```bash
# Build and deploy
git push
# Vercel will automatically deploy
```

## Step 5: Testing

### 5.1 Test Google Sign-In
1. Open `http://localhost:3000` (or your production URL)
2. Click "Continue with Google"
3. Sign in with your Google account
4. You should be redirected to the dashboard

### 5.2 Test User Isolation
1. Open the app in an incognito window
2. Sign in with a **different** Google account
3. Create a note
4. Switch back to the first account
5. You should **NOT** see the note from the second account

### 5.3 Test Note Sharing
1. Create a note
2. Click the share button
3. Copy the share link
4. Open the link in an incognito window
5. You should see the shared note without authentication

## Security Features

✅ **User Isolation**: Each user can only see their own notes and folders
✅ **Token Verification**: Firebase tokens are verified on the backend
✅ **Session Management**: Sessions expire after 7 days
✅ **Secure Cookies**: HttpOnly, Secure, SameSite=None cookies
✅ **Share Links**: Public sharing via unique UUID links (no auth required for viewing shared notes)

## Troubleshooting

### "Firebase Admin SDK initialization failed"
- Make sure `firebase-admin.json` is in the correct location
- For Vercel, ensure `FIREBASE_ADMIN_JSON` environment variable is set

### "Not authenticated" errors
- Check that cookies are being sent with requests (credentials: "include")
- Verify session exists in MongoDB `user_sessions` collection
- Check session expiration date

### "CORS errors"
- Update `CORS_ORIGINS` in backend `.env` to include your frontend URL
- For production, use your actual domain (not localhost)

### Google Sign-In popup closes immediately
- Check that your domain is authorized in Firebase Console
- Verify Firebase config in `.env` matches your Firebase project

## Migration from Old System

If you have existing notes without `user_id` fields:

```javascript
// MongoDB script to add user_id to existing notes
db.notes.updateMany(
  { user_id: { $exists: false } },
  { $set: { user_id: "user_legacy" } }
)
```

## API Endpoints

### Authentication
- `POST /api/auth/firebase-login` - Login with Firebase token
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### Notes (Authenticated)
- `GET /api/notes` - Get user's notes
- `POST /api/notes` - Create note
- `GET /api/notes/:id` - Get specific note
- `PUT /api/notes/:id` - Update note
- `DELETE /api/notes/:id` - Delete note
- `POST /api/notes/:id/share` - Generate share link

### Public
- `GET /api/shared/:share_link` - View shared note (no auth required)

### Folders (Authenticated)
- `GET /api/folders` - Get user's folders
- `POST /api/folders` - Create folder
- `DELETE /api/folders/:id` - Delete folder
