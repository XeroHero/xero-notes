# Quick Start: Enable Google Authentication

## 🚀 Essential Steps (5 minutes)

### 1. Firebase Setup (3 min)

1. **Go to [Firebase Console](https://console.firebase.google.com/)**
   - Select your `xero-notes` project (or create one)

2. **Enable Google Sign-In**
   - Authentication → Sign-in method → Google → Enable
   - Add authorized domains: `localhost`, `xero-notes.vercel.app`

3. **Get Firebase Config** (already in your `.env`, but verify)
   - Project Settings → Your apps → Web app
   - Compare with your `.env` file

4. **Download Firebase Admin SDK Key** ⚠️ CRITICAL
   - Project Settings → Service accounts → Generate new private key
   - Save as `app/backend/firebase-admin.json`
   - **DO NOT COMMIT THIS FILE** (already in `.gitignore`)

### 2. Vercel Environment Variables (2 min)

1. **Go to [Vercel Dashboard](https://vercel.com/dashboard)**
   - Select `xero-notes` project

2. **Add Environment Variables** (Settings → Environment Variables):
   ```
   FIREBASE_ADMIN_JSON={paste entire firebase-admin.json content here}
   MONGO_URL=mongodb+srv://your-connection-string
   DB_NAME=xero_notes
   CORS_ORIGINS=https://xero-notes.vercel.app
   ```

3. **Redeploy**
   - Go to Deployments → Click on latest → Redeploy

### 3. Test It! (1 min)

1. Open your app: `https://xero-notes.vercel.app`
2. Click "Continue with Google"
3. Sign in with your Google account
4. Create a note
5. Open incognito window, sign in with different account
6. Verify you **don't** see the first note ✅

---

## 📋 File Checklist

Make sure these files exist:

- ✅ `src/lib/firebase.js` - Firebase config (created)
- ✅ `src/context/AuthContext.js` - Updated with Firebase auth (updated)
- ✅ `src/pages/LoginPage.js` - Google Sign-In button (updated)
- ✅ `app/backend/server.py` - Main backend with auth (updated)
- ✅ `app/backend/firebase_auth.py` - Firebase auth handler (created)
- ✅ `app/backend/firebase-admin.json` - **YOU MUST CREATE THIS** ⚠️
- ✅ `app/backend/migrate_data.py` - Data migration script (created)
- ✅ `.gitignore` - Updated to exclude firebase-admin.json (updated)

---

## 🔧 Local Development

```bash
# Terminal 1 - Backend
cd app/backend
python server.py

# Terminal 2 - Frontend
npm start
```

---

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "Firebase Admin SDK initialization failed" | Check `firebase-admin.json` exists in `app/backend/` |
| "Not authenticated" | Clear browser cookies, try again |
| Google popup closes immediately | Add domain to Firebase authorized domains |
| CORS errors | Update `CORS_ORIGINS` in Vercel environment variables |
| Can see other users' notes | Run migration script: `python app/backend/migrate_data.py` |

---

## 📖 Full Documentation

See `GOOGLE_AUTH_SETUP.md` for detailed instructions.

---

## ✅ What Changed

**Before:**
- ❌ Anyone could see all notes
- ❌ No user authentication
- ❌ Notes not isolated by user

**After:**
- ✅ Google Sign-In required
- ✅ Each user sees only their own notes
- ✅ Notes/folders filtered by `user_id`
- ✅ Share links still work publicly
- ✅ Sessions expire after 7 days
- ✅ Secure cookies with HttpOnly flag

---

## 🆘 Need Help?

1. Check `GOOGLE_AUTH_SETUP.md` for detailed guide
2. Run test suite: `python app/backend/test_auth.py`
3. Check browser console for errors
4. Verify Firebase config matches your project
