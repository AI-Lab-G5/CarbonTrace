import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';
import type { User } from 'firebase/auth';
import { Jornadas } from '../src/components/Jornadas';
import { request } from '../src/api';
vi.mock('../src/api', () => ({ request: vi.fn() }));
const api = vi.mocked(request);
const user = { uid: 'a', getIdToken: vi.fn().mockResolvedValue('token') } as unknown as User;
const empty = { itens: [], proximo_cursor: null };
beforeEach(() => { api.mockReset(); api.mockResolvedValue(empty); });
test('lista vazia possui instrução e campos rotulados', async () => {
 render(<Jornadas user={user} expired={vi.fn()} />);
 expect(await screen.findByText(/Nenhuma unidade encontrada/)).toBeVisible();
 for (const label of ['Nome','Cidade','UF','Loja','Competência','Fonte','Quantidade','Medida']) expect(screen.getByLabelText(label)).toBeVisible();
 expect(screen.getByRole('button',{name:'Salvar consumo'})).toBeDisabled();
});
test('cadastro envia dados normalizados e confirma sucesso', async () => {
 render(<Jornadas user={user} expired={vi.fn()} />);
 await screen.findByText(/Nenhuma unidade encontrada/);
 api.mockImplementation(async (_path, _token, options) => options?.method === 'POST' ? { id:'u', ...JSON.parse(String(options.body)) } : empty);
 fireEvent.change(screen.getByLabelText('Nome'),{target:{value:' Loja Centro '}});
 fireEvent.change(screen.getByLabelText('Cidade'),{target:{value:' Brasilia '}});
 fireEvent.change(screen.getByLabelText('UF'),{target:{value:'df'}});
 fireEvent.click(screen.getByRole('button',{name:'Cadastrar'}));
 expect(await screen.findByText(/Unidade cadastrada/)).toBeVisible();
 expect(api).toHaveBeenCalledWith('/v1/unidades','token',expect.objectContaining({body:JSON.stringify({nome:'Loja Centro',cidade:'Brasilia',uf:'DF'})}));
});
test('401 encerra sessão e erro permite consultar novamente', async () => {
 const expired=vi.fn(); api.mockRejectedValue(Object.assign(new Error('Sessão expirada'),{status:401}));
 render(<Jornadas user={user} expired={expired} />);
 await waitFor(() => expect(expired).toHaveBeenCalled());
 expect(screen.getByRole('button',{name:'Consultar novamente'})).toBeVisible();
});
test('catálogo distingue carregamento de vazio', async () => {
 render(<Jornadas user={user} expired={vi.fn()} />);
 await screen.findByText(/Nenhuma unidade encontrada/);
 let resolve!: (value: unknown) => void;
 api.mockImplementation(async path => path.startsWith('/v1/fontes') ? new Promise(r => {resolve=r;}) : empty);
 fireEvent.change(screen.getByLabelText('Competência'),{target:{value:'2025-10'}});
 expect(screen.getByText(/Carregando fontes/)).toBeVisible();
 await waitFor(() => expect(resolve).toBeDefined()); resolve([]);
 expect(await screen.findByText(/Nenhuma fonte disponível/)).toBeVisible();
});

test('mudar competência preserva páginas de lojas carregadas', async () => {
 api.mockImplementation(async path => path.startsWith('/v1/unidades') ? {itens:[{id:'u',nome:'Loja',cidade:'X',uf:'DF'}],proximo_cursor:null} : path.startsWith('/v1/fontes') ? [] : empty);
 render(<Jornadas user={user} expired={vi.fn()} />);
 await screen.findByRole('option',{name:'Loja'});
 const before=api.mock.calls.filter(c=>c[0].startsWith('/v1/unidades')).length;
 fireEvent.change(screen.getByLabelText('Competência'),{target:{value:'2025-10'}});
 await screen.findByText(/Nenhuma fonte disponível/);
 expect(api.mock.calls.filter(c=>c[0].startsWith('/v1/unidades'))).toHaveLength(before);
});
