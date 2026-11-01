import { useCallback, useEffect, useState } from 'react';
import { onAuthStateChanged, signOut, type User } from 'firebase/auth';
import { auth } from '@/auth';
import { Topbar } from '@/components/Topbar';
import { Footer } from '@/components/Footer';
import { ApiStatus } from '@/components/ApiStatus';
import { Login } from '@/components/Login';
import { Jornadas } from '@/components/Jornadas';
import './App.css';

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [message, setMessage] = useState('');
  useEffect(() => onAuthStateChanged(auth, next => { setUser(next); setReady(true); }), []);
  const expired = useCallback(() => { setUser(null); setMessage('Sessão expirada. Entre novamente.'); void signOut(auth); }, []);
  return <div className="app-container"><Topbar /><main>
    {message && <p className="wrap" role="status">⚠ {message}</p>}
    {!ready ? <p className="wrap" role="status">◌ Restaurando sessão…</p> : user ? <>
      <div className="wrap"><p>{user.email}</p><button className="btn ghost" onClick={() => { void signOut(auth).then(() => { setUser(null); setMessage('Você saiu da aplicação.'); }).catch(() => setMessage('Não foi possível sair. Tente novamente.')); }}>Sair</button></div>
      <Jornadas key={user.uid} user={user} expired={expired} />
    </> : <Login />}
    <ApiStatus />
  </main><Footer /></div>;
}
