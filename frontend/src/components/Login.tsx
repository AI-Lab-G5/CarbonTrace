import { useState } from 'react';
import { signInWithEmailAndPassword } from 'firebase/auth';
import { auth } from '@/auth';

export function Login() {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  return <section className="wrap card"><h1>Entrar no CarbonTrace</h1><p>Ambiente local de demonstração. Use sua conta individual de teste preparada pela equipe.</p>
    <form onSubmit={async event => {
      event.preventDefault(); const data = new FormData(event.currentTarget); setBusy(true); setError('');
      try { await signInWithEmailAndPassword(auth, String(data.get('email')).trim(), String(data.get('password'))); }
      catch { setError('Não foi possível entrar. Confira seus dados e a disponibilidade/configuração do emulador com a equipe.'); }
      finally { setBusy(false); }
    }}><div className="grid"><label>E-mail<input name="email" type="email" autoComplete="username" required /></label>
      <label>Senha<input name="password" type="password" autoComplete="current-password" required /></label></div>
      <button className="btn" disabled={busy}>{busy ? '◌ Entrando…' : 'Entrar'}</button>
      {error && <p role="alert" className="error-box">⚠ {error} Tente novamente.</p>}
    </form></section>;
}
