import { useEffect, useRef, useState } from 'react';

export interface HealthResponse {
  status: string;
  servico: string;
  modo_auth?: string;
  emulador?: boolean;
}

export type ApiStatusState =
  | { state: 'loading' }
  | { state: 'success'; httpStatus: number; data: HealthResponse }
  | { state: 'error'; message: string };

interface ApiStatusProps {
  apiBaseUrl?: string;
  onStatusChange?: (status: ApiStatusState) => void;
}

export function ApiStatus({ apiBaseUrl = '/api', onStatusChange }: ApiStatusProps) {
  const [status, setStatus] = useState<ApiStatusState>({ state: 'loading' });
  const [retryKey, setRetryKey] = useState<number>(0);

  const onStatusChangeRef = useRef(onStatusChange);
  useEffect(() => {
    onStatusChangeRef.current = onStatusChange;
  }, [onStatusChange]);

  useEffect(() => {
    let ignore = false;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);

    fetch(`${apiBaseUrl}/healthz`, {
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
      },
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Falha na resposta: HTTP ${response.status} ${response.statusText}`);
        }
        const data = (await response.json()) as HealthResponse;
        const readiness = await fetch(`${apiBaseUrl}/readyz`, { signal: controller.signal });
        if (!readiness.ok) throw new Error('API responde, mas o banco ainda não está pronto. Tente novamente.');
        if (!ignore) {
          const nextState: ApiStatusState = {
            state: 'success',
            httpStatus: response.status,
            data,
          };
          setStatus(nextState);
          onStatusChangeRef.current?.(nextState);
        }
      })
      .catch((err: unknown) => {
        if (ignore) return;
        const errorMessage =
          controller.signal.aborted
            ? 'A API demorou para responder. Tente novamente.'
            : err instanceof Error
            ? err.message
            : 'Não foi possível estabelecer conexão com o backend.';
        const nextState: ApiStatusState = {
          state: 'error',
          message: errorMessage,
        };
        setStatus(nextState);
        onStatusChangeRef.current?.(nextState);
      }).finally(() => clearTimeout(timeout));

    return () => {
      clearTimeout(timeout);
      ignore = true;
      controller.abort();
    };
  }, [apiBaseUrl, retryKey]);

  const handleRetry = () => {
    const nextState: ApiStatusState = { state: 'loading' };
    setStatus(nextState);
    onStatusChangeRef.current?.(nextState);
    setRetryKey((prev) => prev + 1);
  };

  return (
    <details id="status-api" className="wrap card api-status-panel" open={status.state === 'error' || undefined}>
      <summary className="card-header-status">
        <h2>Conexão com a plataforma</h2>
        <span className={`badge badge-${status.state}`} aria-live="polite">
          {status.state === 'loading' && '◌ Carregando'}
          {status.state === 'success' && 'Pronta'}
          {status.state === 'error' && '⚠ Indisponível'}
        </span>
      </summary>

      {status.state === 'loading' && (
        <div className="status-box" role="status" aria-label="Consultando integridade do backend">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span className="spinner" />
            <p style={{ margin: 0 }}>Consultando integridade do backend (/api/healthz)...</p>
          </div>
        </div>
      )}

      {status.state === 'success' && (
        <div className="status-box">
          <p style={{ margin: '0 0 0.5rem', color: 'var(--accent)' }}>
            <strong>HTTP {status.httpStatus} OK</strong> — Conectado com sucesso
          </p>
          <dl className="details-grid">
            <div>
              <dt>Serviço:</dt>
              <dd>{status.data.servico}</dd>
            </div>
            <div>
              <dt>Status:</dt>
              <dd>{status.data.status}</dd>
            </div>
            {status.data.modo_auth && (
              <div>
                <dt>Autenticação:</dt>
                <dd>{status.data.modo_auth}</dd>
              </div>
            )}
            {typeof status.data.emulador === 'boolean' && (
              <div>
                <dt>Emulador Firebase:</dt>
                <dd>{status.data.emulador ? 'Ativo' : 'Inativo'}</dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {status.state === 'error' && (
        <div className="status-box">
          <div className="error-box">
            <strong>Erro de conexão:</strong> {status.message}
          </div>
          <button
            type="button"
            className="btn"
            style={{ marginTop: '0.85rem' }}
            onClick={handleRetry}
          >
            Tentar novamente
          </button>
        </div>
      )}
    </details>
  );
}
