import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Login } from '../src/components/Login';
import {
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signInWithPopup,
  updateProfile,
  validatePassword,
} from 'firebase/auth';

vi.mock('../src/auth', () => ({ auth: { languageCode: 'pt-BR' }, authMode: 'emulator' }));

vi.mock('firebase/auth', () => {
  return {
    createUserWithEmailAndPassword: vi.fn(),
    GoogleAuthProvider: vi.fn(),
    sendEmailVerification: vi.fn(),
    sendPasswordResetEmail: vi.fn(),
    signInWithEmailAndPassword: vi.fn(),
    signInWithPopup: vi.fn(),
    updateProfile: vi.fn(),
    validatePassword: vi.fn().mockResolvedValue({ isValid: true }),
  };
});

describe('Componente Login', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(validatePassword).mockResolvedValue({ isValid: true } as unknown as { isValid: boolean });
  });

  it('login funciona com teclado e mantém erro compreensível', async () => {
    vi.mocked(signInWithEmailAndPassword).mockRejectedValueOnce(new Error('offline'));
    const user = userEvent.setup();
    render(<Login />);

    await user.tab();
    expect(screen.getByLabelText('E-mail')).toHaveFocus();
    await user.keyboard('funcionario@example.test');
    await user.tab();
    expect(screen.getByLabelText('Senha')).toHaveFocus();
    await user.keyboard('senha-temporaria');
    await user.tab();
    expect(screen.getByRole('button', { name: 'Entrar' })).toHaveFocus();
    await user.keyboard('{Enter}');

    expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível entrar');
    expect(signInWithEmailAndPassword).toHaveBeenCalledTimes(1);
    expect(signInWithEmailAndPassword).toHaveBeenCalledWith(
      expect.anything(),
      'funcionario@example.test',
      'senha-temporaria',
    );
  });

  it('alterna para Criar conta com foco no primeiro campo e labels corretos', async () => {
    const user = userEvent.setup();
    render(<Login />);

    const btnCriarConta = screen.getByRole('button', { name: 'Criar conta' });
    await user.click(btnCriarConta);

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Criar conta');
    expect(screen.getByLabelText('Nome')).toBeInTheDocument();
    expect(screen.getByLabelText('E-mail')).toBeInTheDocument();
    expect(screen.getByLabelText('Senha')).toBeInTheDocument();
    expect(screen.getByLabelText('Confirmar senha')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByLabelText('Nome')).toHaveFocus();
    });
  });

  it('recusa cadastro se o nome estiver em branco', async () => {
    const user = userEvent.setup();
    render(<Login />);
    await user.click(screen.getByRole('button', { name: 'Criar conta' }));

    await user.type(screen.getByLabelText('Nome'), '   ');
    await user.type(screen.getByLabelText('E-mail'), 'novo@empresa.com');
    await user.type(screen.getByLabelText('Senha'), 'SenhaForte123!');
    await user.type(screen.getByLabelText('Confirmar senha'), 'SenhaForte123!');
    await user.click(screen.getByRole('button', { name: 'Criar conta' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Informe seu nome.');
    expect(createUserWithEmailAndPassword).not.toHaveBeenCalled();
  });

  it('recusa cadastro se confirmação de senha for diferente', async () => {
    const user = userEvent.setup();
    render(<Login />);
    await user.click(screen.getByRole('button', { name: 'Criar conta' }));

    await user.type(screen.getByLabelText('Nome'), 'Ana Silva');
    await user.type(screen.getByLabelText('E-mail'), 'ana@empresa.com');
    await user.type(screen.getByLabelText('Senha'), 'SenhaForte123!');
    await user.type(screen.getByLabelText('Confirmar senha'), 'SenhaDiferente456');
    await user.click(screen.getByRole('button', { name: 'Criar conta' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('A confirmação deve ser igual à senha.');
    expect(createUserWithEmailAndPassword).not.toHaveBeenCalled();
  });

  it('valida política de senha e rejeita senha fraca', async () => {
    vi.mocked(validatePassword).mockResolvedValueOnce({ isValid: false } as unknown as { isValid: boolean });
    const user = userEvent.setup();
    render(<Login />);
    await user.click(screen.getByRole('button', { name: 'Criar conta' }));

    await user.type(screen.getByLabelText('Nome'), 'Ana Silva');
    await user.type(screen.getByLabelText('E-mail'), 'ana@empresa.com');
    await user.type(screen.getByLabelText('Senha'), '123');
    await user.type(screen.getByLabelText('Confirmar senha'), '123');
    await user.click(screen.getByRole('button', { name: 'Criar conta' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('A senha não atende à política do projeto.');
    expect(createUserWithEmailAndPassword).not.toHaveBeenCalled();
  });

  it('preserva espaços de senhas sem remoção silenciosa', async () => {
    const fakeUser = { uid: 'u-123' };
    vi.mocked(createUserWithEmailAndPassword).mockResolvedValueOnce({ user: fakeUser } as unknown as { user: typeof fakeUser });
    vi.mocked(updateProfile).mockResolvedValueOnce(undefined);
    vi.mocked(sendEmailVerification).mockResolvedValueOnce(undefined);

    const user = userEvent.setup();
    render(<Login />);
    await user.click(screen.getByRole('button', { name: 'Criar conta' }));

    await user.type(screen.getByLabelText('Nome'), 'Carlos Santos');
    await user.type(screen.getByLabelText('E-mail'), 'carlos@empresa.com');
    // Senha com espaços intencionais no início e meio
    await user.type(screen.getByLabelText('Senha'), ' Senha Com Espaco ');
    await user.type(screen.getByLabelText('Confirmar senha'), ' Senha Com Espaco ');
    await user.click(screen.getByRole('button', { name: 'Criar conta' }));

    await waitFor(() => {
      expect(createUserWithEmailAndPassword).toHaveBeenCalledWith(
        expect.anything(),
        'carlos@empresa.com',
        ' Senha Com Espaco ',
      );
      expect(updateProfile).toHaveBeenCalledWith(fakeUser, { displayName: 'Carlos Santos' });
      expect(sendEmailVerification).toHaveBeenCalledWith(fakeUser);
    });
  });

  it('permite alternar visibilidade das senhas com botão acessível', async () => {
    const user = userEvent.setup();
    render(<Login />);

    const campoSenha = screen.getByLabelText('Senha');
    expect(campoSenha).toHaveAttribute('type', 'password');

    const toggle = screen.getByRole('button', { name: 'Mostrar senhas' });
    expect(toggle).toHaveAttribute('aria-pressed', 'false');

    await user.click(toggle);
    expect(campoSenha).toHaveAttribute('type', 'text');
    expect(toggle).toHaveAttribute('aria-pressed', 'true');
    expect(toggle).toHaveTextContent('Ocultar senhas');

    await user.click(toggle);
    expect(campoSenha).toHaveAttribute('type', 'password');
    expect(toggle).toHaveAttribute('aria-pressed', 'false');
  });

  it('solicita recuperação de senha e exibe mensagem que evita enumeração', async () => {
    vi.mocked(sendPasswordResetEmail).mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    render(<Login />);

    await user.click(screen.getByRole('button', { name: 'Esqueci minha senha' }));
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Recuperar acesso');

    await user.type(screen.getByLabelText('E-mail'), 'desconhecido@empresa.com');
    await user.click(screen.getByRole('button', { name: 'Enviar instruções' }));

    await waitFor(() => {
      expect(sendPasswordResetEmail).toHaveBeenCalledWith(expect.anything(), 'desconhecido@empresa.com');
      expect(screen.getByRole('status')).toHaveTextContent(
        'Se houver uma conta elegível, você receberá instruções para recuperar o acesso.',
      );
    });
  });

  it('inicia login com Google via popup com provider correto', async () => {
    vi.mocked(signInWithPopup).mockResolvedValueOnce({} as unknown as { user: object });
    const user = userEvent.setup();
    render(<Login />);

    const googleBtn = screen.getByRole('button', { name: 'Entrar com Google' });
    await user.click(googleBtn);

    expect(signInWithPopup).toHaveBeenCalledTimes(1);
    expect(signInWithPopup).toHaveBeenCalledWith(expect.anything(), expect.any(GoogleAuthProvider));
  });

  it('trata fechamento voluntário do popup sem erro técnico alarmante', async () => {
    vi.mocked(signInWithPopup).mockRejectedValueOnce({ code: 'auth/popup-closed-by-user' });
    const user = userEvent.setup();
    render(<Login />);

    await user.click(screen.getByRole('button', { name: 'Entrar com Google' }));

    const alerta = await screen.findByRole('alert');
    expect(alerta).toHaveTextContent('A janela do Google foi fechada. Você pode tentar novamente.');
    expect(alerta).not.toHaveTextContent('auth/');
  });

  it('trata popup bloqueado pelo navegador com mensagem acionável', async () => {
    vi.mocked(signInWithPopup).mockRejectedValueOnce({ code: 'auth/popup-blocked' });
    const user = userEvent.setup();
    render(<Login />);

    await user.click(screen.getByRole('button', { name: 'Entrar com Google' }));

    const alerta = await screen.findByRole('alert');
    expect(alerta).toHaveTextContent('O navegador bloqueou a janela. Permita popups para este site e tente novamente.');
  });

  it('trata erro de e-mail já existente sem expor detalhes indevidos', async () => {
    vi.mocked(createUserWithEmailAndPassword).mockRejectedValueOnce({ code: 'auth/email-already-in-use' });
    const user = userEvent.setup();
    render(<Login />);
    await user.click(screen.getByRole('button', { name: 'Criar conta' }));

    await user.type(screen.getByLabelText('Nome'), 'Joao');
    await user.type(screen.getByLabelText('E-mail'), 'repetido@empresa.com');
    await user.type(screen.getByLabelText('Senha'), 'senha1234');
    await user.type(screen.getByLabelText('Confirmar senha'), 'senha1234');
    await user.click(screen.getByRole('button', { name: 'Criar conta' }));

    const alerta = await screen.findByRole('alert');
    expect(alerta).toHaveTextContent('Não foi possível criar a conta. Tente entrar ou recuperar o acesso.');
  });
});
