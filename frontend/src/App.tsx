import { useCallback, useEffect, useRef, useState } from 'react';
import { onAuthStateChanged, signOut, type User } from 'firebase/auth';
import { auth, authConfigError } from '@/auth';
import { ApiError, request } from '@/api';
import { Topbar } from '@/components/Topbar';
import { Footer } from '@/components/Footer';
import { ApiStatus } from '@/components/ApiStatus';
import { Login } from '@/components/Login';
import { Onboarding, LinkGoogle } from '@/components/Onboarding';
import { Jornadas } from '@/components/Jornadas';
import './App.css';

type Session = { user: User | null; phase: 'restoring' | 'visitor' | 'pending' | 'authorized' | 'error'; error?: string };
export default function App() {
  const [session, setSession] = useState<Session>({user:null,phase:'restoring'});
  const [message, setMessage] = useState('');
  const generation = useRef(0);
  const check = useCallback(async (user: User | null, force = false) => {
    const current = ++generation.current;
    setSession({user,phase:user ? 'restoring' : 'visitor'});
    if (!user) return;
    try {
      const result = await user.getIdTokenResult(force);
      if (current !== generation.current) return;
      if (!result.claims.tenant_id || result.claims.papel !== 'funcionario') {
        setSession({user,phase:'pending'}); return;
      }
      await request('/v1/onboarding/acesso', result.token);
      if (current === generation.current) setSession({user,phase:'authorized'});
    } catch (err) {
      if (current !== generation.current) return;
      if (err instanceof ApiError && err.status === 401) {
        setMessage('Sessão expirada. Entre novamente.'); await signOut(auth);
      } else setSession({user,phase:'error',error:err instanceof Error ? err.message : 'Não foi possível conferir o acesso. Tente novamente.'});
    }
  }, []);
  useEffect(() => {
    if (authConfigError) return;
    const gen = generation;
    const unsubscribe = onAuthStateChanged(auth, user => { void check(user); });
    return () => { gen.current++; unsubscribe(); };
  }, [check]);
  const expired = useCallback(() => { generation.current++; setSession({user:null,phase:'visitor'}); setMessage('Sessão expirada. Entre novamente.'); void signOut(auth); }, []);
  const {user,phase} = session;
  return <div className="app-container"><Topbar /><main>
    {message && <p className="wrap" role="status">⚠ {message}</p>}
    {authConfigError ? <p className="wrap error-box" role="alert">⚠ {authConfigError}</p> : <>
      {user && <div className="wrap"><p>{user.email}</p><div className="auth-actions"><button className="btn ghost" onClick={() => {
        generation.current++; setSession({user,phase:'restoring'});
        void signOut(auth).then(() => { setSession({user:null,phase:'visitor'}); setMessage('Você saiu da aplicação.'); }).catch(() => setSession({user,phase:'error',error:'Não foi possível sair. Tente novamente.'}));
      }}>Sair</button><LinkGoogle key={user.uid} user={user}/></div></div>}
      {phase === 'restoring' && <p className="wrap" role="status">◌ Restaurando sessão…</p>}
      {phase === 'visitor' && <Login/>}
      {phase === 'pending' && user && <Onboarding key={user.uid} user={user} refresh={() => check(user,true)}/>}
      {phase === 'authorized' && user && <Jornadas key={user.uid} user={user} expired={expired}/>}
      {phase === 'error' && <section className="wrap card"><p role="alert">⚠ {session.error}</p><button className="btn" onClick={() => { void check(user,true); }}>Tentar novamente</button></section>}
    </>}
    <ApiStatus />
  </main><Footer /></div>;
}
