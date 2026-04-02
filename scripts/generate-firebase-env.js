#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Read the Firebase admin JSON file
const firebaseAdminPath = path.join(__dirname, '../app/backend/firebase-admin.json');

if (!fs.existsSync(firebaseAdminPath)) {
  console.error('❌ firebase-admin.json not found at:', firebaseAdminPath);
  console.log('Please download it from Firebase Console → Project Settings → Service accounts');
  process.exit(1);
}

try {
  const firebaseConfig = fs.readFileSync(firebaseAdminPath, 'utf8');
  const config = JSON.parse(firebaseConfig);
  
  // Convert to single line JSON for environment variable
  const envValue = JSON.stringify(config);
  
  console.log('✅ Firebase Admin SDK configuration loaded');
  console.log('\n📋 Add this to your Vercel Environment Variables:');
  console.log('\nFIREBASE_ADMIN_JSON=' + envValue);
  console.log('\n💡 Copy the entire line above and paste it into Vercel → Settings → Environment Variables');
  
  // Also write to a file for easy copying
  fs.writeFileSync(path.join(__dirname, '../firebase-admin-env.txt'), 'FIREBASE_ADMIN_JSON=' + envValue);
  console.log('📁 Also saved to firebase-admin-env.txt for easy copying');
  
} catch (error) {
  console.error('❌ Error reading firebase-admin.json:', error.message);
  process.exit(1);
}
