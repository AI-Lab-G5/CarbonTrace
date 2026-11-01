import { afterEach, expect, test, vi } from 'vitest';
import { request } from '../src/api';
afterEach(() => vi.unstubAllGlobals());
test('envia token e quantidade textual sem repetir escrita', async () => {
 const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: 'a' })));
 vi.stubGlobal('fetch', fetcher);
 await request('/v1/consumos', 'token', { method: 'PUT', body: JSON.stringify({ quantidade: '0' }) });
 expect(fetcher).toHaveBeenCalledTimes(1);
 expect(fetcher.mock.calls[0][1].headers.Authorization).toBe('Bearer token');
 expect(JSON.parse(fetcher.mock.calls[0][1].body).quantidade).toBe('0');
});
test('expõe erro de campo da API', async () => {
 vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: [{loc:['body','quantidade'],msg:'Inválida'}] }), {status:422})));
 await expect(request('/v1/consumos','t')).rejects.toThrow('quantidade: Inválida');
});
test('resposta sem JSON e sessão expirada são compreensíveis', async () => {
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response('no',{status:401})));
 await expect(request('/v1/unidades','t')).rejects.toThrow('Sessão expirada');
});
test('preserva cancelamento e não repete falha de rede', async () => {
 const fetcher = vi.fn().mockRejectedValue(new DOMException('cancelado','AbortError')); vi.stubGlobal('fetch', fetcher);
 await expect(request('/v1/unidades','t')).rejects.toHaveProperty('name','AbortError');
 fetcher.mockRejectedValue(new TypeError('network'));
 await expect(request('/v1/consumos','t',{method:'PUT'})).rejects.toThrow('consulte os registros');
 expect(fetcher).toHaveBeenCalledTimes(2);
});
