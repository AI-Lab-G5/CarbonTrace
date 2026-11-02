import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Onboarding, LinkGoogle } from '../src/components/Onboarding';
import { GoogleAuthProvider, linkWithPopup, reload, sendEmailVerification, type User } from 'firebase/auth';
import { request } from '../src/api';

vi.mock('../src/auth', () => ({ auth: {}, authMode: 'emulator' }));

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

vi.mock('firebase/auth', () => ({
  GoogleAuthProvider: vi.fn(),
  linkWithPopup: vi.fn(),
  reload: vi.fn().mockResolvedValue(undefined),
  sendEmailVerification: vi.fn().mockResolvedValue(undefined),
}));

describe('Componente Onboarding', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('exibe aviso de verificação de e-mail pendente quando não verificado', async () => {
    const fakeUser = {
      uid: 'u-pendente',
      email: 'pendente@empresa.com',
      emailVerified: false,
      providerData: [{ providerId: 'password' }],
      getIdToken: vi.fn(),
    } as unknown as User;

    const refreshMock = vi.fn().mockResolvedValue(undefined);
    render(<Onboarding user={fakeUser} refresh={refreshMock} />);

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Concluir acesso à empresa');
    expect(screen.getByText(/Verificação de e-mail pendente/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reenviar verificação' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Já verifiquei \/ Atualizar acesso/i })).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Já verifiquei \/ Atualizar acesso/i }));
    await waitFor(() => {
      expect(reload).toHaveBeenCalledWith(fakeUser);
      expect(refreshMock).toHaveBeenCalledTimes(1);
    });
  });

  it('permite reenviar verificação de e-mail com feedback visual', async () => {
    vi.mocked(sendEmailVerification).mockResolvedValueOnce(undefined);
    const fakeUser = {
      uid: 'u-pendente',
      email: 'pendente@empresa.com',
      emailVerified: false,
      providerData: [{ providerId: 'password' }],
      getIdToken: vi.fn(),
    } as unknown as User;

    const user = userEvent.setup();
    render(<Onboarding user={fakeUser} refresh={vi.fn().mockResolvedValue(undefined)} />);

    await user.click(screen.getByRole('button', { name: 'Reenviar verificação' }));
    await waitFor(() => {
      expect(sendEmailVerification).toHaveBeenCalledWith(fakeUser);
      expect(screen.getByText(/Verificação enviada. Confira sua caixa de entrada./i)).toBeInTheDocument();
    });
  });

  it('exibe campo de código de convite quando o e-mail está verificado', async () => {
    const fakeUser = {
      uid: 'u-verificado',
      email: 'verificado@empresa.com',
      emailVerified: true,
      providerData: [{ providerId: 'password' }],
      getIdToken: vi.fn().mockResolvedValue('token-id-firebase-123'),
    } as unknown as User;

    vi.mocked(request).mockResolvedValueOnce({ tenant_id: 'empresa-a', papel: 'funcionario' });
    const refreshMock = vi.fn().mockResolvedValue(undefined);

    const user = userEvent.setup();
    render(<Onboarding user={fakeUser} refresh={refreshMock} />);

    expect(screen.getByText(/E-mail verificado. Aguardando vínculo autorizado./i)).toBeInTheDocument();
    const inputConvite = screen.getByLabelText('Convite da empresa');
    const botaoVincular = screen.getByRole('button', { name: 'Vincular empresa' });

    const tokenValido = 'convite-seguro-token-com-mais-de-32-chars-xyz';
    await user.type(inputConvite, tokenValido);
    await user.click(botaoVincular);

    await waitFor(() => {
      expect(fakeUser.getIdToken).toHaveBeenCalled();
      expect(request).toHaveBeenCalledWith(
        '/v1/onboarding/resgate',
        'token-id-firebase-123',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ convite: tokenValido }),
        }),
      );
      expect(refreshMock).toHaveBeenCalledTimes(1);
    });
  });

  it('usuário verificado (inclusive via Google) tem acesso ao campo de convite', () => {
    const fakeUserGoogle = {
      uid: 'u-google',
      email: 'google@empresa.com',
      emailVerified: true,
      providerData: [{ providerId: 'google.com' }],
      getIdToken: vi.fn(),
    } as unknown as User;

    render(<Onboarding user={fakeUserGoogle} refresh={vi.fn().mockResolvedValue(undefined)} />);

    expect(screen.getByLabelText('Convite da empresa')).toBeInTheDocument();
    expect(screen.queryByText(/Verificação de e-mail pendente/i)).not.toBeInTheDocument();
  });
});

describe('Componente LinkGoogle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('não renderiza botão se a conta já possui o provedor Google', () => {
    const fakeUser = {
      uid: 'u-com-google',
      providerData: [{ providerId: 'google.com' }],
    } as unknown as User;

    const { container } = render(<LinkGoogle user={fakeUser} />);
    expect(container.firstChild).toBeNull();
  });

  it('permite vincular conta Google e chama linkWithPopup', async () => {
    vi.mocked(linkWithPopup).mockResolvedValueOnce({} as unknown as never);
    const fakeUser = {
      uid: 'u-senha',
      providerData: [{ providerId: 'password' }],
    } as unknown as User;

    const user = userEvent.setup();
    render(<LinkGoogle user={fakeUser} />);

    const btn = screen.getByRole('button', { name: 'Vincular Google' });
    await user.click(btn);

    expect(linkWithPopup).toHaveBeenCalledWith(fakeUser, expect.any(GoogleAuthProvider));
    expect(await screen.findByText(/Google vinculado à sua conta/i)).toBeInTheDocument();
  });

  it('trata erro de credencial já em uso em outra conta', async () => {
    vi.mocked(linkWithPopup).mockRejectedValueOnce({ code: 'auth/credential-already-in-use' });
    const fakeUser = {
      uid: 'u-senha',
      providerData: [{ providerId: 'password' }],
    } as unknown as User;

    const user = userEvent.setup();
    render(<LinkGoogle user={fakeUser} />);

    await user.click(screen.getByRole('button', { name: 'Vincular Google' }));
    expect(await screen.findByText(/Este Google já pertence a outra conta/i)).toBeInTheDocument();
  });
});
