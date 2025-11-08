/**
 * Firebase Authentication Helper Functions
 */
import { signInWithPopup, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut, onAuthStateChanged } from "firebase/auth";
import { doc, setDoc, getDoc, updateDoc } from "firebase/firestore";
import { auth, db, googleProvider } from "./firebase-config.js";

/**
 * Sign in with Google
 */
export async function signInWithGoogle() {
    try {
        const result = await signInWithPopup(auth, googleProvider);
        const user = result.user;
        
        // Save user to Firestore
        await saveUserToFirestore(user);
        
        // Get custom token from backend
        const idToken = await user.getIdToken();
        const response = await fetch('/api/auth/firebase', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ idToken })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Store session token
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            return { success: true, user: data.user };
        } else {
            throw new Error(data.error || 'Authentication failed');
        }
    } catch (error) {
        console.error('Google sign-in error:', error);
        throw error;
    }
}

/**
 * Sign in with email and password
 */
export async function signInWithEmail(email, password) {
    try {
        const result = await signInWithEmailAndPassword(auth, email, password);
        const user = result.user;
        
        // Get custom token from backend
        const idToken = await user.getIdToken();
        const response = await fetch('/api/auth/firebase', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ idToken })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            return { success: true, user: data.user };
        } else {
            throw new Error(data.error || 'Authentication failed');
        }
    } catch (error) {
        console.error('Email sign-in error:', error);
        throw error;
    }
}

/**
 * Register with email and password
 */
export async function registerWithEmail(name, email, password) {
    try {
        const result = await createUserWithEmailAndPassword(auth, email, password);
        const user = result.user;
        
        // Update user profile with name
        await updateProfile(user, { displayName: name });
        
        // Save user to Firestore
        await saveUserToFirestore(user, { name });
        
        // Get custom token from backend
        const idToken = await user.getIdToken();
        const response = await fetch('/api/auth/firebase', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ idToken })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            return { success: true, user: data.user };
        } else {
            throw new Error(data.error || 'Registration failed');
        }
    } catch (error) {
        console.error('Registration error:', error);
        throw error;
    }
}

/**
 * Sign out
 */
export async function signOutUser() {
    try {
        await signOut(auth);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        return { success: true };
    } catch (error) {
        console.error('Sign out error:', error);
        throw error;
    }
}

/**
 * Save user to Firestore
 */
async function saveUserToFirestore(user, additionalData = {}) {
    try {
        const userRef = doc(db, 'users', user.uid);
        const userSnap = await getDoc(userRef);
        
        if (!userSnap.exists()) {
            await setDoc(userRef, {
                uid: user.uid,
                email: user.email,
                name: user.displayName || additionalData.name || user.email.split('@')[0],
                createdAt: new Date().toISOString(),
                ...additionalData
            });
        } else {
            // Update existing user
            await updateDoc(userRef, {
                email: user.email,
                name: user.displayName || additionalData.name || userSnap.data().name,
                lastLogin: new Date().toISOString()
            });
        }
    } catch (error) {
        console.error('Error saving user to Firestore:', error);
    }
}

/**
 * Get current user
 */
export function getCurrentFirebaseUser() {
    return auth.currentUser;
}

/**
 * Listen to auth state changes
 */
export function onAuthStateChange(callback) {
    return onAuthStateChanged(auth, callback);
}

