#!/usr/bin/env node

console.log('🔥 Firebase Web Configuration Helper');
console.log('=====================================\n');

console.log('To get your Firebase web configuration:\n');

console.log('1. Go to Firebase Console: https://console.firebase.google.com/');
console.log('2. Select your "xero-notes" project');
console.log('3. Click the gear icon ⚙️ → Project Settings');
console.log('4. Scroll down to "Your apps" section');
console.log('5. Click the Web app (or create one if not exists)');
console.log('6. Copy the Firebase configuration object\n');

console.log('Your config should look like this:\n');
console.log('const firebaseConfig = {');
console.log('  apiKey: "AIzaSy..."');
console.log('  authDomain: "xero-notes.firebaseapp.com"');
console.log('  projectId: "xero-notes"');
console.log('  storageBucket: "xero-notes.appspot.com"');
console.log('  messagingSenderId: "123456789"');
console.log('  appId: "1:123456789:web:abcdef"');
console.log('  measurementId: "G-XXXXXXXXX"');
console.log('};\n');

console.log('📋 Add these as REACT_APP_ environment variables in Vercel:\n');

console.log('REACT_APP_FIREBASE_API_KEY=your_api_key_here');
console.log('REACT_APP_FIREBASE_AUTH_DOMAIN=xero-notes.firebaseapp.com');
console.log('REACT_APP_FIREBASE_PROJECT_ID=xero-notes');
console.log('REACT_APP_FIREBASE_STORAGE_BUCKET=xero-notes.appspot.com');
console.log('REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_sender_id');
console.log('REACT_APP_FIREBASE_APP_ID=your_app_id');
console.log('REACT_APP_FIREBASE_MEASUREMENT_ID=your_measurement_id\n');

console.log('🚀 Quick Setup Steps:');
console.log('1. Copy the FIREBASE_ADMIN_JSON from above (already generated)');
console.log('2. Get the REACT_APP_FIREBASE_* values from Firebase Console');
console.log('3. Add all environment variables to Vercel');
console.log('4. Add your Vercel domain to Firebase → Authentication → Settings → Authorized domains');
console.log('5. Deploy and test Google Sign-in!\n');

console.log('📁 Check firebase-admin-env.txt for the FIREBASE_ADMIN_JSON value');
