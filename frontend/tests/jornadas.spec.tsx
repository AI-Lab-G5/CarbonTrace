import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';
import type { User } from 'firebase/auth';
import { Jornadas } from '../src/components/Jornadas';
import { request } from '../src/api';
import { MemoryRouter, Route, Routes } from 'react-router';
import { UnidadesPage } from '../src/pages/UnidadesPage';
import { ConsumosPage } from '../src/pages/ConsumosPage';
vi.mock('../src/api', () => ({ request: vi.fn() }));
const api = vi.mocked(request);
const user = { uid: 'a', getIdToken: vi.fn().mockResolvedValue('token') } as unknown as User;
const empty = { itens: [], proximo_cursor: null };
beforeEach(() => { api.mockReset(); api.mockResolvedValue(empty); });
function renderJornadas(path = '/unidades', expired = vi.fn()) {
 return render(<MemoryRouter initialEntries={[path]}><Routes><Route element={<Jornadas user={user} expired={expired}/>}><Route path="/unidades" element={<UnidadesPage/>}/><Route path="/consumos" element={<ConsumosPage/>}/></Route></Routes></MemoryRouter>);
}
test('lista vazia possui instrução e campos rotulados', async () => {
 renderJornadas();
 expect(await screen.findByText(/Nenhuma unidade encontrada/)).toBeVisible();
 for (const label of ['Nome','Cidade','UF']) expect(screen.getByLabelText(label)).toBeVisible();
 fireEvent.click(screen.getByRole('link', {name: /Consumos/}));
 for (const label of ['Loja','Competência']) expect(screen.getByLabelText(label)).toBeVisible();
 expect(screen.queryByLabelText('Fonte')).not.toBeInTheDocument();
 expect(screen.getByRole('button',{name:'Salvar consumo'})).toBeDisabled();
});
test('cadastro envia dados normalizados e confirma sucesso', async () => {
 renderJornadas();
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
 renderJornadas('/unidades', expired);
 await waitFor(() => expect(expired).toHaveBeenCalled());
 expect(screen.getByRole('button',{name:'Consultar novamente'})).toBeVisible();
});
test('catálogo distingue carregamento de vazio', async () => {
 renderJornadas('/consumos');
 await screen.findByText(/Cadastre uma unidade para registrar/);
 let resolve!: (value: unknown) => void;
 api.mockImplementation(async path => path.startsWith('/v1/fontes') ? new Promise(r => {resolve=r;}) : empty);
 fireEvent.change(screen.getByLabelText('Competência'),{target:{value:'2025-10'}});
 expect(screen.getByText(/Carregando fontes/)).toBeVisible();
 await waitFor(() => expect(resolve).toBeDefined()); resolve([]);
 expect(await screen.findByText(/Nenhuma fonte disponível/)).toBeVisible();
});

test('mudar competência preserva páginas de lojas carregadas', async () => {
 api.mockImplementation(async path => path.startsWith('/v1/unidades') ? {itens:[{id:'u',nome:'Loja',cidade:'X',uf:'DF'}],proximo_cursor:null} : path.startsWith('/v1/fontes') ? [] : empty);
 renderJornadas('/consumos');
 await screen.findByRole('option',{name:'Loja'});
 const before=api.mock.calls.filter(c=>c[0].startsWith('/v1/unidades')).length;
 fireEvent.change(screen.getByLabelText('Competência'),{target:{value:'2025-10'}});
 await screen.findByText(/Nenhuma fonte disponível/);
 expect(api.mock.calls.filter(c=>c[0].startsWith('/v1/unidades'))).toHaveLength(before);
});

const unitFixture = { id: 'u', nome: 'Loja Centro', cidade: 'Brasília', uf: 'DF' };
const factorFixture = { fonte_id: 'eletricidade', nome: 'Eletricidade', unidades_aceitas: ['kWh', 'MWh'], unidade_base: 'kWh', kg_co2e_por_unidade: '0.0385', teto_mensal: '999999', fonte_referencia: 'Referência original', status: 'preliminar' };
const recordFixture = { id: 'c', unidade_id: 'u', competencia: '2025-10', fonte_id: 'eletricidade', quantidade_informada: '1.5', unidade_informada: 'MWh', quantidade_convertida: '1500', unidade_base: 'kWh', fator_versao: 'v1', fator_valor: '0.0385', emissao_kg_co2e: '57.750', escopo: '2' };
function mockJourney(duplicate = false) {
 api.mockImplementation(async (path, _token, options) => {
  if (path.startsWith('/v1/unidades')) return { itens: [unitFixture], proximo_cursor: null };
  if (path.startsWith('/v1/fontes/versoes')) return { versao: 'v1', fatores: [factorFixture] };
  if (path.startsWith('/v1/fontes?')) return [factorFixture];
  if (options?.method === 'PUT' || path.startsWith('/v1/consumos/c')) return recordFixture;
  return { itens: duplicate ? [recordFixture] : [], proximo_cursor: null };
 });
}
async function fillConsumption() {
 await screen.findByRole('option', { name: 'Loja Centro' });
 fireEvent.change(screen.getByLabelText('Loja'), { target: { value: 'u' } });
 fireEvent.change(screen.getByLabelText('Competência'), { target: { value: '2025-10' } });
 await screen.findByRole('option', { name: 'Eletricidade' });
 fireEvent.change(screen.getByLabelText('Fonte'), { target: { value: 'eletricidade' } });
 fireEvent.change(screen.getByLabelText('Quantidade'), { target: { value: '1,5' } });
 fireEvent.change(screen.getByLabelText('Medida'), { target: { value: 'MWh' } });
}

test('trocar de rota preserva filtros e rascunho sem consultar lojas novamente', async () => {
 mockJourney(); renderJornadas('/consumos'); await fillConsumption();
 const before = api.mock.calls.filter(c => c[0].startsWith('/v1/unidades')).length;
 fireEvent.click(screen.getByRole('link', { name: /Unidades/ }));
 expect(screen.queryByLabelText('Quantidade')).not.toBeInTheDocument();
 fireEvent.click(screen.getByRole('link', { name: /Consumos/ }));
 expect(screen.getByLabelText('Loja')).toHaveValue('u');
 expect(screen.getByLabelText('Competência')).toHaveValue('2025-10');
 expect(screen.getByLabelText('Fonte')).toHaveValue('eletricidade');
 expect(screen.getByLabelText('Quantidade')).toHaveValue('1,5');
 expect(screen.getByLabelText('Medida')).toHaveValue('MWh');
 expect(api.mock.calls.filter(c => c[0].startsWith('/v1/unidades'))).toHaveLength(before);
});

test('salva decimal pela API, consulta fator versionado e reproduz cálculo original', async () => {
 mockJourney(); renderJornadas('/consumos'); await fillConsumption();
 fireEvent.click(screen.getByRole('button', { name: 'Salvar consumo' }));
 expect(await screen.findByText('✓ Consumo salvo e consultado pela API.')).toBeVisible();
 expect(api).toHaveBeenCalledWith('/v1/consumos', 'token', expect.objectContaining({ method: 'PUT', body: JSON.stringify({ unidade_id: 'u', competencia: '2025-10', fonte_id: 'eletricidade', quantidade: '1.5', unidade_medida: 'MWh' }) }));
 expect(screen.getByRole('region', { name: 'Resultado salvo' })).toHaveTextContent('57,750 kgCO₂e');
 expect(api).toHaveBeenCalledWith('/v1/fontes/versoes/v1', 'token', undefined);
 fireEvent.click(screen.getByRole('button', { name: 'Conferir cálculo original' }));
 expect(await screen.findByText(/Reprodução concluída/)).toBeVisible();
 expect(api).toHaveBeenCalledWith('/v1/consumos/c/recalculo', 'token', { method: 'POST' });
});

test('consumo duplicado mostra resultado original e não grava novamente', async () => {
 mockJourney(true); renderJornadas('/consumos'); await fillConsumption();
 fireEvent.click(screen.getByRole('button', { name: 'Salvar consumo' }));
 expect(await screen.findByRole('alert')).toHaveTextContent('Este consumo já existe');
 expect(screen.getByRole('region', { name: 'Resultado salvo' })).toHaveTextContent('57,750');
 expect(api.mock.calls.some(c => c[2]?.method === 'PUT')).toBe(false);
});
