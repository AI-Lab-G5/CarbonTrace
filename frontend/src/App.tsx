import { useCallback, useEffect, useRef, useState } from 'react';
import { onAuthStateChanged, signOut, type User } from 'firebase/auth';
import { BrowserRouter, Link, Navigate, Outlet, Route, Routes, useLocation } from 'react-router';
import { auth, authConfigError } from '@/auth';
import { ApiError, request } from '@/api';
import { Topbar } from '@/components/Topbar';
import { Footer } from '@/components/Footer';
import { ApiStatus } from '@/components/ApiStatus';
import { AuthPage } from '@/pages/AuthPage';
import { HomePage } from '@/pages/HomePage';
import { Onboarding, LinkGoogle } from '@/components/Onboarding';
import { Jornadas } from '@/components/Jornadas';
import { UnidadesPage } from '@/pages/UnidadesPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { ConsumosPage } from '@/pages/ConsumosPage';
import { clearDrafts } from '@/utils/drafts';
import './App.css';
import './workspace.css';
import './landing.css';

type Session = { user: User | null; phase: 'restoring' | 'visitor' | 'pending' | 'authorized' | 'error'; error?: string };
export default function App() {
  return <BrowserRouter><AppContent /></BrowserRouter>;
}

function AppContent() {
  const location = useLocation();
  const [session, setSession] = useState<Session>({user:null,phase:'restoring'});
  const [message, setMessage] = useState('');
  const generation = useRef(0);
  const activeUid = useRef<string | null>(null);
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
        clearDrafts(user.uid);
        setMessage('Sessão expirada. Entre novamente.'); await signOut(auth);
      } else setSession({user,phase:'error',error:err instanceof Error ? err.message : 'Não foi possível conferir o acesso. Tente novamente.'});
    }
  }, []);
  useEffect(() => {
    if (authConfigError) return;
    const gen = generation;
    const unsubscribe = onAuthStateChanged(auth, user => {
      if (activeUid.current && activeUid.current !== user?.uid) clearDrafts(activeUid.current);
      activeUid.current = user?.uid || null;
      void check(user);
    });
    return () => { gen.current++; unsubscribe(); };
  }, [check]);
  const expired = useCallback(() => { if (activeUid.current) clearDrafts(activeUid.current); generation.current++; setSession({user:null,phase:'visitor'}); setMessage('Sessão expirada. Entre novamente.'); void signOut(auth); }, []);
  const {user,phase} = session;
  const isHome = location.pathname === '/';
  const requested = (location.state as { from?: string } | null)?.from;
  const destination = ['/consumos', '/dashboard'].includes(requested || '') ? requested! : '/unidades';
  const protectedContent = phase === 'authorized' && user
    ? <Jornadas key={user.uid} user={user} expired={expired}/>
    : <Navigate to={phase === 'pending' ? '/acesso' : '/entrar'} replace state={{ from: location.pathname }} />;
  const accessContent = authConfigError
    ? <p className="wrap error-box" role="alert">⚠ {authConfigError}</p>
    : phase === 'restoring'
      ? <p className="wrap session-loading" role="status"><span className="spinner" aria-hidden="true"/> Restaurando sessão…</p>
      : phase === 'error'
        ? <section className="wrap card"><p role="alert">⚠ {session.error}</p><button className="btn" onClick={() => { void check(user,true); }}>Tentar novamente</button></section>
        : <Outlet/>;
  useEffect(() => {
    const titles: Record<string, string> = { '/': 'Conheça o impacto. Transforme o futuro.', '/entrar': 'Entrar', '/acesso': 'Concluir acesso', '/unidades': 'Unidades', '/consumos': 'Consumos', '/dashboard': 'Dashboard' };
    document.title = `${titles[location.pathname] || 'Página não encontrada'} | CarbonTrace`;
    if (location.hash) {
      const section = document.getElementById(location.hash.slice(1));
      section?.focus({ preventScroll: true });
      section?.scrollIntoView?.({ block: 'start' });
      return;
    }
    document.getElementById('main-content')?.focus();
  }, [location.pathname, location.hash]);
  return <div className="app-container"><a className="skip-link" href="#main-content">Ir para o conteúdo</a><Topbar authorized={phase === 'authorized'} /><main id="main-content" tabIndex={-1}>
    {message && <p className="wrap" role="status">⚠ {message}</p>}
    {user && !isHome && <div className="wrap session-bar"><span className="session-email">{user.email}</span><div className="auth-actions"><LinkGoogle key={user.uid} user={user}/><button className="btn ghost" onClick={() => {
        generation.current++; setSession({user,phase:'restoring'});
        void signOut(auth).then(() => { clearDrafts(user.uid); setSession({user:null,phase:'visitor'}); setMessage('Você saiu da aplicação.'); }).catch(() => setSession({user,phase:'error',error:'Não foi possível sair. Tente novamente.'}));
      }}>Sair</button></div></div>}
    <Routes>
      <Route path="/" element={<HomePage authorized={phase === 'authorized'}/>}/>
      <Route element={accessContent}>
        <Route path="/entrar" element={phase === 'visitor' ? <AuthPage/> : <Navigate to={phase === 'pending' ? '/acesso' : destination} replace state={location.state}/>}/>
        <Route path="/acesso" element={phase === 'pending' && user ? <div className="route-enter"><Onboarding key={user.uid} user={user} refresh={() => check(user,true)}/></div> : <Navigate to={phase === 'visitor' ? '/entrar' : destination} replace state={location.state}/>}/>
        <Route element={protectedContent}>
          <Route path="/unidades" element={<UnidadesPage/>}/>
          <Route path="/consumos" element={<ConsumosPage/>}/>
          <Route path="/dashboard" element={<DashboardPage/>}/>
        </Route>
      </Route>
      <Route path="*" element={<section className="wrap card route-enter"><h1>Página não encontrada</h1><p>Este endereço não está disponível no CarbonTrace.</p><Link className="btn" to="/">Voltar ao início</Link></section>}/>
    </Routes>
    {!isHome && <ApiStatus />}
  </main><Footer compact={!isHome}/></div>;
}
