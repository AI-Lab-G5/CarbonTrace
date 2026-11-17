import { useEffect, useRef, useState } from 'react';
import { createUserWithEmailAndPassword, GoogleAuthProvider, sendEmailVerification, sendPasswordResetEmail, signInWithEmailAndPassword, signInWithPopup, updateProfile, validatePassword } from 'firebase/auth';
import { auth, authMode } from '@/auth';
import { authError } from '@/utils/authError';
import { PasswordField } from '@/components/PasswordField';
import { GoogleButton } from '@/components/GoogleButton';
import { FormFeedback } from '@/components/FormFeedback';
import { fieldErrors, FormValidationError, type FieldErrors } from '@/utils/validation';

export function Login({ initialMode = 'login' }: { initialMode?: 'login' | 'signup' }) {
  const [mode, setMode] = useState<'login' | 'signup' | 'reset'>(initialMode);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [invalidFields, setInvalidFields] = useState<FieldErrors>({});
  const [attempt, setAttempt] = useState(0);
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
    locked.current = true; setAttempt(value => value + 1); setBusy(true); setError(''); setMessage('');
    try { await action(); } catch (err) { setInvalidFields(fieldErrors(err)); setError(err instanceof FormValidationError ? err.message : authError(err)); }
    finally { locked.current = false; setBusy(false); }
  }
  function change(next: typeof mode) {
    setMode(next); setError(''); setMessage(''); setInvalidFields({});
  }
  return <section className="wrap card auth-card"><h1>{mode === 'signup' ? 'Criar conta' : mode === 'reset' ? 'Recuperar acesso' : 'Entrar no CarbonTrace'}</h1>
    <p>Use sua conta individual. O acesso às lojas depende de um convite da sua empresa.</p>
    {authMode === 'emulator' && <p className="nota">Ambiente local de demonstração. O acesso Google aqui é simulado.</p>}
    <form key={mode} onChange={event => {
      if (!(event.target instanceof HTMLInputElement)) return;
      const name = event.target.name;
      setInvalidFields(current => { const next = { ...current }; delete next[name]; return next; });
    }} onSubmit={event => {
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
        if (!name) throw new FormValidationError({ name: 'Informe seu nome.' });
        if (password !== data.get('confirmation')) throw new FormValidationError({ confirmation: 'A confirmação deve ser igual à senha.' });
        const policy = await validatePassword(auth, password);
        if (!policy.isValid) throw new FormValidationError({ password: 'A senha não atende à política do projeto. Use ao menos 6 caracteres e confira as exigências da equipe.' });
        const result = await createUserWithEmailAndPassword(auth, email, password);
        await updateProfile(result.user, { displayName: name });
        await sendEmailVerification(result.user);
      });
    }}><fieldset className="journey-fields" disabled={busy}><div className="grid">
      {mode === 'signup' && <div className="form-field"><label htmlFor="signup-name">Nome</label><input id="signup-name" ref={first} name="name" autoComplete="name" required maxLength={120} aria-invalid={Boolean(invalidFields.name) || undefined} aria-describedby={invalidFields.name ? 'signup-name-error' : undefined}/>{invalidFields.name && <small id="signup-name-error" className="field-error">{invalidFields.name}</small>}</div>}
      <label>E-mail<input ref={mode === 'signup' ? undefined : first} name="email" type="email" autoComplete={mode === 'signup' ? 'email' : 'username'} required /></label>
      {mode !== 'reset' && <PasswordField label="Senha" name="password" autoComplete={mode === 'signup' ? 'new-password' : 'current-password'} describedBy={mode === 'signup' ? 'password-help' : undefined} error={invalidFields.password}/>}
      {mode === 'signup' && <PasswordField label="Confirmar senha" name="confirmation" autoComplete="new-password" error={invalidFields.confirmation}/>}
    </div>
    {mode === 'signup' && <p id="password-help" className="nota">Use ao menos 6 caracteres. A política da empresa pode exigir letras, números e símbolos adicionais.</p>}
    <FormFeedback key={attempt} message={error} focus/>
    <div className="auth-actions"><button className="btn">{busy ? 'Aguarde…' : mode === 'signup' ? 'Criar conta' : mode === 'reset' ? 'Enviar instruções' : 'Entrar'}</button></div>
    </fieldset></form>
    <div className="auth-actions">
      <button className="btn ghost" disabled={busy} onClick={() => change(mode === 'login' ? 'signup' : 'login')}>{mode === 'login' ? 'Criar conta' : 'Voltar para entrar'}</button>
      {mode === 'login' && <button className="btn ghost" disabled={busy} onClick={() => change('reset')}>Esqueci minha senha</button>}
    </div>
    {mode !== 'reset' && <GoogleButton disabled={busy} onClick={() => { void run(() => signInWithPopup(auth, new GoogleAuthProvider())); }}>Entrar com Google</GoogleButton>}
    {message && <p role="status">✓ {message}</p>}
  </section>;
}
