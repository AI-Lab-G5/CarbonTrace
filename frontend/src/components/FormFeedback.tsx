import { useEffect, useRef } from 'react';

export function FormFeedback({ message, focus = false, retry, retryLabel = 'Tentar novamente', disabled = false }: {
  message: string;
  focus?: boolean;
  retry?: () => void;
  retryLabel?: string;
  disabled?: boolean;
}) {
  const notice = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!message || !focus) return;
    const field = notice.current?.closest('form')?.querySelector<HTMLElement>('[aria-invalid="true"]');
    (field || notice.current)?.focus();
  }, [message, focus]);
  if (!message) return null;
  return <div ref={notice} role="alert" tabIndex={-1} className="error-box form-feedback">
    <p>{message}</p>
    {retry && <button type="button" className="btn ghost" disabled={disabled} onClick={retry}>{retryLabel}</button>}
  </div>;
}
