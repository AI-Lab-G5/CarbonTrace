import { initializeApp } from 'firebase/app';
import { connectAuthEmulator, getAuth } from 'firebase/auth';

export const authMode = import.meta.env.VITE_AUTH_MODE || 'emulator';
const real = authMode === 'firebase';
const projectId = import.meta.env.VITE_FIREBASE_PROJECT_ID || (real ? '' : 'demo-carbontrace');
export const authConfigError = !['firebase', 'emulator'].includes(authMode)
  ? 'Configure VITE_AUTH_MODE como emulator ou firebase e refaça o build.'
  : real && (!projectId || projectId.startsWith('demo-') || !import.meta.env.VITE_FIREBASE_API_KEY || !import.meta.env.VITE_FIREBASE_AUTH_DOMAIN)
    ? 'Configure projeto, API key e authDomain do Firebase Web e refaça o build.' : '';
const app = initializeApp({
  projectId: projectId || 'invalid-configuration',
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || (real ? 'invalid-configuration' : 'demo-carbontrace-key'),
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || `${projectId}.firebaseapp.com`,
});
export const auth = getAuth(app);
auth.languageCode = 'pt-BR';
if (authMode === 'emulator') {
  connectAuthEmulator(auth, import.meta.env.VITE_AUTH_EMULATOR_URL || 'http://127.0.0.1:9099', { disableWarnings: true });
}
