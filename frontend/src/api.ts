export class ApiError extends Error {
  status: number;
  fields: Record<string, string>;
  constructor(status: number, message: string, fields: Record<string, string> = {}) { super(message); this.status = status; this.fields = fields; }
}
export async function request<T>(path: string, token: string, options: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const cancel = () => controller.abort();
  if (options.signal?.aborted) controller.abort();
  options.signal?.addEventListener('abort', cancel, { once: true });
  let timedOut = false;
  const timeout = setTimeout(() => { timedOut = true; controller.abort(); }, 15000);
  const writing = options.method && !['GET', 'HEAD'].includes(options.method.toUpperCase());
  try {
    let response: Response;
    try {
      response = await fetch(`${import.meta.env.VITE_API_BASE_URL || '/api'}${path}`, {
        ...options, signal: controller.signal, headers: { Accept: 'application/json', 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...options.headers },
      });
    } catch (error) {
      if (timedOut) throw new ApiError(0, writing ? 'A operação demorou para responder. Consulte os registros antes de tentar salvar novamente.' : 'A consulta demorou para responder. Confira sua conexão e tente novamente.');
      if (error instanceof DOMException && error.name === 'AbortError') throw error;
      throw new ApiError(0, writing ? 'Não foi possível conectar à API. Se estava salvando, consulte os registros antes de tentar novamente.' : 'Não foi possível carregar os dados. Confira sua conexão e tente novamente.');
    }
    const data: unknown = await response.json().catch(error => {
      if (controller.signal.aborted) throw error;
      return null;
    });
    if (!response.ok) {
      let detail = '';
      const fields: Record<string, string> = {};
      if (data && typeof data === 'object' && 'detail' in data) {
        const value = data.detail;
        if (typeof value === 'string') detail = value;
        else if (Array.isArray(value)) detail = value.flatMap(item => {
          if (!item || typeof item !== 'object') return [];
          const key = Array.isArray(item.loc) ? item.loc.slice(1).join('.') : '';
          const message = typeof item.msg === 'string' ? item.msg : 'Confira o valor informado.';
          if (key) fields[key] = message;
          return [`${key || 'Campo'}: ${message}`];
        }).join('; ');
      }
      const fallback: Record<number, string> = { 401: 'Sessão expirada. Entre novamente.', 403: 'Sua conta não tem acesso a esta operação.', 404: 'Registro não encontrado.', 409: 'Já existe um registro para estes dados.', 422: 'Confira os campos informados.', 429: 'Muitas solicitações. Aguarde um pouco antes de tentar novamente.' };
      throw new ApiError(response.status, response.status === 401 ? fallback[401] : detail || fallback[response.status] || 'O serviço está indisponível no momento. Tente novamente em instantes.', fields);
    }
    if (data === null) throw new ApiError(502, 'A API retornou uma resposta inválida. Consulte novamente antes de reenviar dados.');
    return data as T;
  } catch (error) {
    if (timedOut && !(error instanceof ApiError)) throw new ApiError(0, writing ? 'A operação demorou para responder. Consulte os registros antes de tentar salvar novamente.' : 'A consulta demorou para responder. Confira sua conexão e tente novamente.');
    throw error;
  } finally {
    clearTimeout(timeout);
    options.signal?.removeEventListener('abort', cancel);
  }
}
