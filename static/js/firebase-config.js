/**
 * Firebase Configuration
 */
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDGTGU6WcGclC9GOQMIPYlG0_xU_K1Yn-c",
  authDomain: "codemind-372a6.firebaseapp.com",
  projectId: "codemind-372a6",
  storageBucket: "codemind-372a6.firebasestorage.app",
  messagingSenderId: "753260539371",
  appId: "1:753260539371:web:c467fc5cbc5e558b5efdae",
  measurementId: "G-639TCFB0S4"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase services
const auth = getAuth(app);
const db = getFirestore(app);
const analytics = typeof window !== 'undefined' ? getAnalytics(app) : null;
const googleProvider = new GoogleAuthProvider();

// Google OAuth Client ID
const GOOGLE_CLIENT_ID = "24978387197-r0s4p2l6ee62eigqi1fdddehlp5hnb0b.apps.googleusercontent.com";

// Export for use in other files
if (typeof window !== 'undefined') {
    window.firebaseApp = app;
    window.firebaseAuth = auth;
    window.firebaseDb = db;
    window.firebaseAnalytics = analytics;
    window.googleProvider = googleProvider;
    window.GOOGLE_CLIENT_ID = GOOGLE_CLIENT_ID;
}

export { app, auth, db, analytics, googleProvider, GOOGLE_CLIENT_ID };

