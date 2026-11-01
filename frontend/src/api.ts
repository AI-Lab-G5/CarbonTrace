export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) { super(message); this.status = status; }
}
export async function request<T>(path: string, token: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${import.meta.env.VITE_API_BASE_URL || '/api'}${path}`, {
      ...options, headers: { Accept: 'application/json', 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...options.headers },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new ApiError(0, 'Não foi possível conectar à API. Se estava salvando, consulte os registros antes de tentar novamente.');
  }
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    let detail = '';
    if (data && typeof data === 'object' && 'detail' in data) {
      const value = data.detail;
      if (typeof value === 'string') detail = value;
      else if (Array.isArray(value)) detail = value.map((item: { loc?: string[]; msg?: string }) => `${item.loc?.slice(1).join('.') || 'Campo'}: ${item.msg || 'Inválido'}`).join('; ');
    }
    const fallback: Record<number, string> = { 401: 'Sessão expirada. Entre novamente.', 403: 'Sua conta não tem acesso a esta operação.', 404: 'Registro não encontrado.', 409: 'Já existe um registro para estes dados.', 422: 'Confira os campos informados.' };
    throw new ApiError(response.status, response.status === 401 ? fallback[401] : detail || fallback[response.status] || `Serviço indisponível (HTTP ${response.status}). Tente novamente.`);
  }
  if (data === null) throw new ApiError(502, 'A API retornou uma resposta inválida. Consulte novamente antes de reenviar dados.');
  return data as T;
}
