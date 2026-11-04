import { useId, useState } from 'react';

export function PasswordField({ label, name, autoComplete, describedBy, error }: {
  label: string;
  name: string;
  autoComplete: string;
  describedBy?: string;
  error?: string;
}) {
  const id = useId();
  const [visible, setVisible] = useState(false);
  const subject = name === 'confirmation' ? 'confirmação de senha' : 'senha';
  const action = `${visible ? 'Ocultar' : 'Mostrar'} ${subject}`;
  return <div className="password-field">
    <label htmlFor={id}>{label}</label>
    <div className="password-input">
      <input id={id} name={name} type={visible ? 'text' : 'password'} autoComplete={autoComplete} required aria-invalid={Boolean(error) || undefined} aria-describedby={[describedBy, error ? `${id}-error` : ''].filter(Boolean).join(' ') || undefined}/>
      <button type="button" className="password-toggle" aria-label={action} title={action} aria-pressed={visible} aria-controls={id} onClick={() => setVisible(!visible)}>
        <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/>
          <circle cx="12" cy="12" r="3"/>
          {visible && <path d="m3 3 18 18"/>}
        </svg>
      </button>
    </div>
    {error && <small id={`${id}-error`} className="field-error">{error}</small>}
  </div>;
}
