import { useRef, useState } from 'react';
import { GoogleAuthProvider, linkWithPopup, reload, sendEmailVerification, type User } from 'firebase/auth';
import { request } from '@/api';
import { authError } from '@/utils/authError';
import { GoogleButton } from '@/components/GoogleButton';
import { FormFeedback } from '@/components/FormFeedback';

export function Onboarding({ user, refresh }: { user: User; refresh: () => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const lock = useRef(false);
  async function run(action: () => Promise<void>) {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError(''); setMessage('');
    try { await action(); } catch (err) { setError(err instanceof Error && !('code' in err) ? err.message : authError(err)); }
    finally { lock.current = false; setBusy(false); }
  }
  return <section className="wrap card auth-card"><h1>Concluir acesso à empresa</h1>
    <p>Sua conta existe. Para acessar as lojas, confirme seu e-mail e use o convite enviado pela equipe.</p>
    {!user.emailVerified ? <><p role="status">✉ Verificação de e-mail pendente. Confira sua caixa de entrada.</p>
      <button className="btn" disabled={busy} onClick={() => { void run(async () => { await sendEmailVerification(user); setMessage('Verificação enviada. Confira sua caixa de entrada.'); }); }}>Reenviar verificação</button></> : <>
      <p role="status">✓ E-mail verificado. Aguardando vínculo autorizado.</p>
      <form onSubmit={event => { event.preventDefault(); const data = new FormData(event.currentTarget); void run(async () => {
        await request('/v1/onboarding/resgate', await user.getIdToken(), { method: 'POST', body: JSON.stringify({ convite: String(data.get('convite')).trim() }) });
        await refresh();
      }); }}><label>Convite da empresa<input name="convite" type="password" autoComplete="off" required minLength={32} maxLength={256} disabled={busy} /></label>
      <div className="auth-actions"><button className="btn" disabled={busy}>Vincular empresa</button></div></form>
      <p className="nota">Sem convite? Solicite à equipe responsável pela sua empresa.</p>
    </>}
    <div className="auth-actions"><button className="btn ghost" disabled={busy} onClick={() => { void run(async () => { await reload(user); await refresh(); setMessage('Situação atualizada.'); }); }}>Já verifiquei / Atualizar acesso</button></div>
    {busy && <p role="status">Conferindo acesso…</p>}{message && <p role="status">✓ {message}</p>}<FormFeedback message={error} focus/>
  </section>;
}

export function LinkGoogle({ user }: { user: User }) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const lock = useRef(false);
  if (user.providerData.some(provider => provider.providerId === 'google.com')) return null;
  return <><GoogleButton disabled={busy} onClick={() => {
    if (lock.current) return;
    lock.current = true; setBusy(true); setMessage('');
    void linkWithPopup(user, new GoogleAuthProvider()).then(() => setMessage('✓ Google vinculado à sua conta.')).catch(err => setMessage(`⚠ ${authError(err)}`)).finally(() => { lock.current = false; setBusy(false); });
  }}>Vincular Google</GoogleButton>{message && <p role="status">{message}</p>}</>;
}
