import { useEffect, useState } from 'react';
import './App.css';

interface HealthResponse {
  status: string;
  servico: string;
  modo_auth?: string;
  emulador?: boolean;
}

type ApiStatus =
  | { state: 'loading' }
  | { state: 'success'; httpStatus: number; data: HealthResponse }
  | { state: 'error'; message: string };

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export default function App() {
  const [status, setStatus] = useState<ApiStatus>({ state: 'loading' });
  const [retryKey, setRetryKey] = useState<number>(0);

  useEffect(() => {
    let ignore = false;
    const controller = new AbortController();

    fetch(`${API_BASE_URL}/health`, {
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
        if (!ignore) {
          setStatus({
            state: 'success',
            httpStatus: response.status,
            data,
          });
        }
      })
      .catch((err: unknown) => {
        if (ignore) return;
        const errorMessage =
          err instanceof Error
            ? err.message
            : 'Não foi possível estabelecer conexão com o backend.';
        setStatus({
          state: 'error',
          message: errorMessage,
        });
      });

    return () => {
      ignore = true;
      controller.abort();
    };
  }, [retryKey]);

  const handleRetry = () => {
    setStatus({ state: 'loading' });
    setRetryKey((prev) => prev + 1);
  };

  return (
    <div className="container">
      <header className="header">
        <h1>CarbonTrace</h1>
        <p className="description">
          Plataforma para inventário e gestão de emissões de gases de efeito estufa (GEE).
        </p>
      </header>

      <main>
        <section
          className="card"
          aria-labelledby="api-status-heading"
          aria-live="polite"
        >
          <div className="card-header">
            <h2 id="api-status-heading">Status da API</h2>
            <span className={`badge badge-${status.state}`} aria-hidden="true">
              {status.state === 'loading' && 'Carregando'}
              {status.state === 'success' && 'Online'}
              {status.state === 'error' && 'Indisponível'}
            </span>
          </div>

          {status.state === 'loading' && (
            <div className="status-content">
              <div className="spinner" role="status" aria-label="Carregando status da API" />
              <p>Consultando integridade do backend...</p>
            </div>
          )}

          {status.state === 'success' && (
            <div className="status-content">
              <p className="success-header">
                <strong>Status HTTP:</strong> {status.httpStatus} OK
              </p>
              <dl className="details-list">
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
                    <dt>Modo de Autenticação:</dt>
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
            <div className="status-content">
              <p className="error-message">
                <strong>Erro de conexão:</strong> {status.message}
              </p>
              <button
                type="button"
                className="btn-retry"
                onClick={handleRetry}
              >
                Tentar novamente
              </button>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
