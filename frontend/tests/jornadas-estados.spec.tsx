import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import type { User } from 'firebase/auth';
import { Jornadas } from '../src/components/Jornadas';
import { request } from '../src/api';

vi.mock('../src/api', () => ({ request: vi.fn() }));
const api = vi.mocked(request);
const conta = { uid: 'a', getIdToken: vi.fn().mockResolvedValue('token') } as unknown as User;
const vazio = { itens: [], proximo_cursor: null };
const loja = { id: 'u1', nome: 'Loja Centro', cidade: 'Brasilia', uf: 'DF' };
const eletricidade = { fonte_id: 'eletricidade', nome: 'Eletricidade', escopo: '2', unidade_base: 'kWh', unidades_aceitas: ['kWh', 'MWh'], kg_co2e_por_unidade: '0.0385', teto_mensal: '1000000', fonte_referencia: 'MCTI', status: 'preliminar' };

function comLoja(aoSalvar?: () => Promise<unknown>) {
  api.mockImplementation(async (path, _token, options) => {
    if (path.startsWith('/v1/unidades')) return { itens: [loja], proximo_cursor: null };
    if (path.startsWith('/v1/fontes')) return [eletricidade];
    if (path.startsWith('/v1/consumos') && options?.method === 'PUT') return aoSalvar ? aoSalvar() : Promise.reject(new Error('falha'));
    return vazio;
  });
}

async function preencherConsumo(competencia: string, quantidade: string, medida = 'kWh') {
  await screen.findByRole('option', { name: 'Loja Centro' });
  fireEvent.change(screen.getByLabelText('Loja'), { target: { value: 'u1' } });
  fireEvent.change(screen.getByLabelText('Competência'), { target: { value: competencia } });
  await screen.findByRole('option', { name: 'Eletricidade' });
  fireEvent.change(screen.getByLabelText('Fonte'), { target: { value: 'eletricidade' } });
  fireEvent.change(screen.getByLabelText('Quantidade'), { target: { value: quantidade } });
  fireEvent.change(screen.getByLabelText('Medida'), { target: { value: medida } });
}

beforeEach(() => { api.mockReset(); api.mockResolvedValue(vazio); });

describe('Estados da lista de unidades', () => {
  test('mostra "carregando" enquanto a API não responde e só depois "vazio"', async () => {
    let responder!: (valor: unknown) => void;
    api.mockImplementation(async path => path.startsWith('/v1/unidades') ? new Promise(r => { responder = r; }) : vazio);
    render(<Jornadas user={conta} expired={vi.fn()} />);
    expect(await screen.findByText(/Carregando unidades/)).toBeVisible();
    expect(screen.queryByText(/Nenhuma unidade encontrada/)).not.toBeInTheDocument();
    await waitFor(() => expect(responder).toBeDefined());
    responder(vazio);
    expect(await screen.findByText(/Nenhuma unidade encontrada/)).toBeVisible();
    expect(screen.queryByText(/Carregando unidades/)).not.toBeInTheDocument();
  });

  test('erro ao carregar unidades permite tentar novamente e recupera', async () => {
    let falhar = true;
    api.mockImplementation(async path => {
      if (path.startsWith('/v1/unidades')) { if (falhar) throw new Error('Serviço indisponível (HTTP 503). Tente novamente.'); return { itens: [loja], proximo_cursor: null }; }
      return vazio;
    });
    render(<Jornadas user={conta} expired={vi.fn()} />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Serviço indisponível');
    falhar = false;
    fireEvent.click(screen.getByRole('button', { name: 'Consultar novamente' }));
    expect(await screen.findByText(/Loja Centro — Brasilia\/DF/)).toBeVisible();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});

describe('Recusas da API aparecem na tela sem perder o que foi digitado', () => {
  test.each([
    ['acima do teto', '2025-10', '99999999', 'Quantidade 99999999 kWh acima do teto mensal de 1000000 kWh.'],
    ['mês no futuro', '2099-01', '10', 'Competencia 2099-01 esta no futuro.'],
  ])('%s', async (_nome, competencia, quantidade, detalhe) => {
    comLoja(() => Promise.reject(Object.assign(new Error(detalhe), { status: 422 })));
    render(<Jornadas user={conta} expired={vi.fn()} />);
    await preencherConsumo(competencia, quantidade);
    fireEvent.click(screen.getByRole('button', { name: 'Salvar consumo' }));
    const alerta = await screen.findByRole('alert');
    expect(alerta).toHaveTextContent(detalhe);
    expect(alerta).toHaveTextContent('⚠');
    expect(screen.getByLabelText('Quantidade')).toHaveValue(quantidade);
    expect(screen.getByLabelText('Quantidade')).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByLabelText('Quantidade').getAttribute('aria-describedby')).toContain('journey-error');
    expect(screen.getByRole('button', { name: 'Salvar consumo' })).toBeEnabled();
  });

  test('quantidade negativa ou com separador de milhar é recusada antes de chamar a API', async () => {
    comLoja();
    render(<Jornadas user={conta} expired={vi.fn()} />);
    for (const invalida of ['-1', '1.000,50', '']) {
      await preencherConsumo('2025-10', invalida);
      fireEvent.click(screen.getByRole('button', { name: 'Salvar consumo' }));
      expect(await screen.findByRole('alert')).toHaveTextContent(/decimal não negativa|Informe/);
    }
    expect(api.mock.calls.some(c => c[2]?.method === 'PUT')).toBe(false);
  });

  test('zero explícito é aceito e enviado como texto', async () => {
    comLoja(async () => ({ id: 'c1', unidade_id: 'u1', competencia: '2025-10', fonte_id: 'eletricidade', quantidade_informada: '0', unidade_informada: 'kWh', quantidade_convertida: '0', unidade_base: 'kWh', fator_versao: 'v1', fator_valor: '0.0385', emissao_kg_co2e: '0.000', escopo: '2' }));
    render(<Jornadas user={conta} expired={vi.fn()} />);
    await preencherConsumo('2025-10', '0');
    fireEvent.click(screen.getByRole('button', { name: 'Salvar consumo' }));
    await waitFor(() => expect(api.mock.calls.some(c => c[2]?.method === 'PUT')).toBe(true));
    const envio = api.mock.calls.find(c => c[2]?.method === 'PUT')!;
    expect(JSON.parse(String(envio[2]?.body)).quantidade).toBe('0');
  });
});

describe('Teclado nos formulários de jornada', () => {
  test('ordem de tabulação do cadastro de unidade ao registro de consumo, e envio com Enter', async () => {
    api.mockImplementation(async (path, _t, options) => {
      if (path.startsWith('/v1/unidades') && options?.method === 'POST') return { id: 'u2', ...JSON.parse(String(options.body)) };
      if (path.startsWith('/v1/unidades')) return { itens: [loja], proximo_cursor: null };
      if (path.startsWith('/v1/fontes')) return [eletricidade];
      return vazio;
    });
    const teclado = userEvent.setup();
    render(<Jornadas user={conta} expired={vi.fn()} />);
    await screen.findByRole('option', { name: 'Loja Centro' });
    const nome = screen.getByLabelText('Nome');
    nome.focus();
    await teclado.keyboard('Loja Norte');
    await teclado.tab(); expect(screen.getByLabelText('Cidade')).toHaveFocus();
    await teclado.keyboard('Goiania');
    await teclado.tab(); expect(screen.getByLabelText('UF')).toHaveFocus();
    await teclado.keyboard('go');
    await teclado.tab(); expect(screen.getByRole('button', { name: 'Cadastrar' })).toHaveFocus();
    await teclado.keyboard('{Enter}');
    expect(await screen.findByText(/Unidade cadastrada/)).toBeVisible();
    const envio = api.mock.calls.find(c => c[2]?.method === 'POST')!;
    expect(JSON.parse(String(envio[2]?.body))).toEqual({ nome: 'Loja Norte', cidade: 'Goiania', uf: 'GO' });

    // Do botão seguem, na ordem, todos os campos do registro de consumo.
    const ordem = ['Loja', 'Competência', 'Fonte', 'Quantidade', 'Medida'];
    await teclado.tab();
    for (const rotulo of ordem) {
      if (rotulo === 'Fonte') { fireEvent.change(screen.getByLabelText('Competência'), { target: { value: '2025-10' } }); await screen.findByRole('option', { name: 'Eletricidade' }); }
      expect(screen.getByLabelText(rotulo)).toHaveFocus();
      if (rotulo !== 'Medida') await teclado.tab();
    }
  });

  test('todo campo tem rótulo acessível e a mensagem de ajuda da quantidade é associada', async () => {
    render(<Jornadas user={conta} expired={vi.fn()} />);
    await screen.findByText(/Nenhuma unidade encontrada/);
    for (const rotulo of ['Nome', 'Cidade', 'UF', 'Loja', 'Competência', 'Fonte', 'Quantidade', 'Medida']) {
      expect(screen.getByLabelText(rotulo)).toBeInTheDocument();
    }
    expect(screen.getByLabelText('Quantidade').getAttribute('aria-describedby')).toContain('decimal-help');
  });
});