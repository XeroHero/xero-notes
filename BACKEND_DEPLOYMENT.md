# Backend Deployment Guide (Separate Vercel Project)

## Overview

The frontend is deployed on Vercel, and the backend will be deployed as a separate Vercel project using the Python
runtime.

## Step 1: Create Separate Backend Repository

1. **Create new GitHub repository** for the backend (e.g., `xero-notes-backend`)

2. **Move backend code** to new repository:
   ```bash
   # In your current xero-notes project
   cd app/backend
   # Copy all files to the new repository
   ```

3. **Backend repository structure**:
   ```
   xero-notes-backend/
   ├── server.py
   ├── requirements.txt
   ├── vercel.json
   ├── firebase-admin.json
   ├── .env
   └── api/ (if you have API routes)
   ```

## Step 2: Deploy Backend to Vercel

1. **Go to [Vercel Dashboard](https://vercel.com/dashboard)**
2. **Add New Project**
3. **Import the backend repository**
4. **Configure Environment Variables**:
    - `MONGODB_URI`: Your MongoDB connection string
    - `DB_NAME`: xero_notes
    - `FIREBASE_ADMIN_JSON`: Paste entire firebase-admin.json content
    - `CORS_ORIGINS`: https://xero-notes.vercel.app,http://localhost:3000

5. **Deploy** - Vercel will detect Python and deploy accordingly

6. **Get Backend URL** - Vercel will provide a URL like `https://xero-notes-backend.vercel.app`

## Step 3: Update Frontend Vercel Environment Variables

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select `xero-notes` project (frontend)
3. Go to Settings → Environment Variables
4. Add: `REACT_APP_BACKEND_URL` = `your-backend-vercel-url`
5. Redeploy the frontend

## Step 4: Clean Up Current Project

Remove backend files from the current repository:

```bash
rm -rf app/backend
```

## Step 5: Local Development

For local development:

```bash
# Terminal 1 - Backend (from separate repo)
cd xero-notes-backend
python server.py

# Terminal 2 - Frontend (from current repo)
# Create .env file with:
REACT_APP_BACKEND_URL=http://localhost:8000
npm start
```

## Verification

After deployment:

1. Visit your frontend Vercel URL
2. Try logging in with Google
3. Verify notes are created and saved
4. Check browser console for any API errors

## Troubleshooting

- **CORS Errors**: Ensure `CORS_ORIGINS` includes your frontend Vercel domain
- **Connection Refused**: Verify backend Vercel project is deployed and accessible
- **MongoDB Errors**: Check `MONGODB_URI` is correct and MongoDB Atlas allows connections
- **Firebase Errors**: Verify `FIREBASE_ADMIN_JSON` is properly formatted in backend Vercel project

## Benefits

- Both projects on Vercel
- Free tier available for both
- No external service dependencies
- Easy deployment and management
