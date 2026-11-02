import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../src/App';
import { onAuthStateChanged, signOut, type User } from 'firebase/auth';
import { ApiError, request } from '../src/api';

vi.mock('../src/auth', () => ({
  auth: {},
  authMode: 'emulator',
  authConfigError: '',
}));

vi.mock('firebase/auth', () => ({
  onAuthStateChanged: vi.fn(),
  signOut: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('../src/api', () => ({
  request: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
}));

// Mock Jornadas e Onboarding para manter o teste focado nas transições do App
vi.mock('../src/components/Jornadas', () => ({
  Jornadas: ({ user }: { user: User }) => <div data-testid="jornadas-view">Jornadas para {user.email}</div>,
}));

vi.mock('../src/components/Onboarding', () => ({
  Onboarding: ({ user }: { user: User }) => <div data-testid="onboarding-view">Onboarding para {user.email}</div>,
  LinkGoogle: () => <button>Mock Vincular Google</button>,
}));

vi.mock('../src/components/Login', () => ({
  Login: () => <div data-testid="login-view">Tela de Login</div>,
}));

vi.mock('../src/components/ApiStatus', () => ({
  ApiStatus: () => null,
}));

describe('App - Máquina de Estados da Sessão e Acesso', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.replaceState(null, '', '/');
  });

  it('inicia na fase de restauração de sessão', () => {
    vi.mocked(onAuthStateChanged).mockImplementation(() => () => {});
    render(<App />);
    expect(screen.getByRole('status')).toHaveTextContent('Restaurando sessão');
  });

  it('muda para visitante quando não há usuário logado', async () => {
    vi.mocked(onAuthStateChanged).mockImplementation((_auth, callback) => {
      (callback as (u: User | null) => void)(null);
      return () => {};
    });

    render(<App />);
    await waitFor(() => {
      expect(screen.getByTestId('login-view')).toBeInTheDocument();
    });
  });

  it('redireciona usuário sem custom claims de empresa para Onboarding', async () => {
    const fakeUser = {
      uid: 'user-sem-empresa',
      email: 'novo@empresa.com',
      getIdTokenResult: vi.fn().mockResolvedValue({
        token: 'fake-token',
        claims: {}, // sem tenant_id nem papel
      }),
    } as unknown as User;

    vi.mocked(onAuthStateChanged).mockImplementation((_auth, callback) => {
      (callback as (u: User | null) => void)(fakeUser);
      return () => {};
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('onboarding-view')).toBeInTheDocument();
      expect(screen.queryByTestId('jornadas-view')).not.toBeInTheDocument();
    });
  });

  it('libera jornadas quando usuário tem tenant_id, papel e API confirma', async () => {
    const fakeUser = {
      uid: 'user-autorizado',
      email: 'autorizado@empresa.com',
      getIdTokenResult: vi.fn().mockResolvedValue({
        token: 'fake-token-autorizado',
        claims: { tenant_id: 'empresa-a', papel: 'funcionario' },
      }),
    } as unknown as User;

    vi.mocked(request).mockResolvedValueOnce({ tenant_id: 'empresa-a', papel: 'funcionario' });

    vi.mocked(onAuthStateChanged).mockImplementation((_auth, callback) => {
      (callback as (u: User | null) => void)(fakeUser);
      return () => {};
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('jornadas-view')).toBeInTheDocument();
      expect(request).toHaveBeenCalledWith('/v1/onboarding/acesso', 'fake-token-autorizado');
    });
  });

  it('ao clicar em Sair, desconecta no Firebase e exibe mensagem amigável', async () => {
    const fakeUser = {
      uid: 'user-sair',
      email: 'sair@empresa.com',
      getIdTokenResult: vi.fn().mockResolvedValue({
        token: 'fake-token',
        claims: { tenant_id: 'empresa-a', papel: 'funcionario' },
      }),
    } as unknown as User;

    vi.mocked(request).mockResolvedValueOnce({ tenant_id: 'empresa-a', papel: 'funcionario' });

    vi.mocked(onAuthStateChanged).mockImplementation((_auth, callback) => {
      (callback as (u: User | null) => void)(fakeUser);
      return () => {};
    });

    const user = userEvent.setup();
    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Sair' })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: 'Sair' }));

    await waitFor(() => {
      expect(signOut).toHaveBeenCalled();
      expect(screen.getByRole('status')).toHaveTextContent('Você saiu da aplicação.');
      expect(screen.getByTestId('login-view')).toBeInTheDocument();
    });
  });

  it('ao receber 401 da API, expira sessão e desconecta', async () => {
    const fakeUser = {
      uid: 'user-expirado',
      email: 'expirado@empresa.com',
      getIdTokenResult: vi.fn().mockResolvedValue({
        token: 'token-expirado',
        claims: { tenant_id: 'empresa-a', papel: 'funcionario' },
      }),
    } as unknown as User;

    vi.mocked(request).mockRejectedValueOnce(new ApiError(401, 'Token expirado'));

    vi.mocked(onAuthStateChanged).mockImplementation((_auth, callback) => {
      (callback as (u: User | null) => void)(fakeUser);
      return () => {};
    });

    render(<App />);

    await waitFor(() => {
      expect(signOut).toHaveBeenCalled();
      expect(screen.getByText(/Sessão expirada. Entre novamente./i)).toBeInTheDocument();
    });
  });

  it('preserva o destino protegido durante login e só libera após confirmar acesso', async () => {
    window.history.replaceState(null, '', '/consumos');
    let authChanged!: (u: User | null) => void;
    vi.mocked(onAuthStateChanged).mockImplementation((_auth, callback) => {
      authChanged = callback as (u: User | null) => void;
      authChanged(null);
      return () => {};
    });
    render(<App/>);
    await screen.findByTestId('login-view');
    expect(window.location.pathname).toBe('/entrar');
    expect(screen.queryByTestId('jornadas-view')).not.toBeInTheDocument();
    const fakeUser = { uid: 'direct', getIdTokenResult: vi.fn().mockResolvedValue({ token: 'token', claims: { tenant_id: 'a', papel: 'funcionario' } }) } as unknown as User;
    vi.mocked(request).mockResolvedValueOnce({});
    const { act } = await import('@testing-library/react');
    await act(async () => authChanged(fakeUser));
    await screen.findByTestId('jornadas-view');
    expect(window.location.pathname).toBe('/consumos');
  });

  it('mostra recuperação para endereço desconhecido', async () => {
    window.history.replaceState(null, '', '/inexistente');
    vi.mocked(onAuthStateChanged).mockImplementation((_auth, callback) => {
      (callback as (u: User | null) => void)(null);
      return () => {};
    });
    render(<App/>);
    expect(await screen.findByRole('heading', { name: 'Página não encontrada' })).toBeVisible();
    expect(screen.getByRole('link', { name: 'Voltar ao início' })).toHaveAttribute('href', '/');
  });
});
