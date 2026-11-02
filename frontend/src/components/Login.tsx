import { useEffect, useRef, useState } from 'react';
import { createUserWithEmailAndPassword, GoogleAuthProvider, sendEmailVerification, sendPasswordResetEmail, signInWithEmailAndPassword, signInWithPopup, updateProfile, validatePassword } from 'firebase/auth';
import { auth, authMode } from '@/auth';
import { authError } from '@/utils/authError';

export function Login() {
  const [mode, setMode] = useState<'login' | 'signup' | 'reset'>('login');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const locked = useRef(false);
  const first = useRef<HTMLInputElement>(null);
  const previousMode = useRef(mode);
  useEffect(() => {
    if (previousMode.current !== mode) {
      first.current?.focus();
      previousMode.current = mode;
    }
  }, [mode]);
  async function run(action: () => Promise<unknown>) {
    if (locked.current) return;
    locked.current = true; setBusy(true); setError(''); setMessage('');
    try { await action(); } catch (err) { setError(authError(err)); }
    finally { locked.current = false; setBusy(false); }
  }
  function change(next: typeof mode) {
    setMode(next); setError(''); setMessage('');
  }
  return <section className="wrap card auth-card"><h1>{mode === 'signup' ? 'Criar conta' : mode === 'reset' ? 'Recuperar acesso' : 'Entrar no CarbonTrace'}</h1>
    <p>Use sua conta individual. O acesso às lojas depende de um convite da sua empresa.</p>
    {authMode === 'emulator' && <p className="nota">Ambiente local de demonstração. O acesso Google aqui é simulado.</p>}
    <form key={mode} onSubmit={event => {
      event.preventDefault(); const data = new FormData(event.currentTarget);
      const email = String(data.get('email')).trim(); const password = String(data.get('password') || '');
      void run(async () => {
        if (mode === 'reset') {
          try { await sendPasswordResetEmail(auth, email); }
          catch (err) { if ((err as {code?: string}).code !== 'auth/user-not-found') throw err; }
          setMessage('Se houver uma conta elegível, você receberá instruções para recuperar o acesso.'); return;
        }
        if (mode === 'login') { await signInWithEmailAndPassword(auth, email, password); return; }
        const name = String(data.get('name')).trim();
        if (!name) { setError('Informe seu nome.'); return; }
        if (password !== data.get('confirmation')) { setError('A confirmação deve ser igual à senha.'); return; }
        const policy = await validatePassword(auth, password);
        if (!policy.isValid) { setError('A senha não atende à política do projeto. Use ao menos 6 caracteres e confira as exigências da equipe.'); return; }
        const result = await createUserWithEmailAndPassword(auth, email, password);
        await updateProfile(result.user, { displayName: name });
        await sendEmailVerification(result.user);
      });
    }}><fieldset className="journey-fields" disabled={busy}><div className="grid">
      {mode === 'signup' && <label>Nome<input ref={first} name="name" autoComplete="name" required maxLength={120} /></label>}
      <label>E-mail<input ref={mode === 'signup' ? undefined : first} name="email" type="email" autoComplete={mode === 'signup' ? 'email' : 'username'} required /></label>
      {mode !== 'reset' && <><label>Senha<input name="password" type="password" autoComplete={mode === 'signup' ? 'new-password' : 'current-password'} required aria-describedby={mode === 'signup' ? 'password-help' : undefined} /></label>
      {mode === 'signup' && <label>Confirmar senha<input name="confirmation" type="password" autoComplete="new-password" required /></label>}</>}
    </div>
    {mode === 'signup' && <p id="password-help" className="nota">Use ao menos 6 caracteres. A política da empresa pode exigir letras, números e símbolos adicionais.</p>}
    <div className="auth-actions"><button className="btn">{busy ? '◌ Aguarde…' : mode === 'signup' ? 'Criar conta' : mode === 'reset' ? 'Enviar instruções' : 'Entrar'}</button></div>
    </fieldset></form>
    <div className="auth-actions">
      <button className="btn ghost" disabled={busy} onClick={() => change(mode === 'login' ? 'signup' : 'login')}>{mode === 'login' ? 'Criar conta' : 'Voltar para entrar'}</button>
      {mode === 'login' && <button className="btn ghost" disabled={busy} onClick={() => change('reset')}>Esqueci minha senha</button>}
    </div>
    {mode !== 'reset' && <button className="google-button" disabled={busy} onClick={() => { void run(() => signInWithPopup(auth, new GoogleAuthProvider())); }}>Entrar com Google</button>}
    {error && <p role="alert" className="error-box">⚠ {error}</p>}
    {message && <p role="status">✓ {message}</p>}
  </section>;
}
