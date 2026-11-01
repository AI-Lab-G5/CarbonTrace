import { initializeApp } from 'firebase/app';
import { connectAuthEmulator, getAuth } from 'firebase/auth';

const projectId = import.meta.env.VITE_FIREBASE_PROJECT_ID || 'demo-carbontrace';
const app = initializeApp({ projectId, apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'demo-carbontrace-key', authDomain: `${projectId}.firebaseapp.com` });
export const auth = getAuth(app);
// Esta entrega é local. O endereço deve ser acessível pelo navegador.
connectAuthEmulator(auth, import.meta.env.VITE_AUTH_EMULATOR_URL || 'http://127.0.0.1:9099');
