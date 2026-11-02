export function authError(error: unknown): string {
  const code = (error as { code?: string })?.code;
  const messages: Record<string, string> = {
    'auth/popup-closed-by-user': 'A janela do Google foi fechada. Você pode tentar novamente.',
    'auth/popup-blocked': 'O navegador bloqueou a janela. Permita popups para este site e tente novamente.',
    'auth/cancelled-popup-request': 'Já existe uma solicitação de login. Conclua a janela aberta.',
    'auth/network-request-failed': 'Sem conexão. Confira sua rede e tente novamente.',
    'auth/unauthorized-domain': 'Este endereço ainda não foi autorizado para login. Avise a equipe.',
    'auth/operation-not-allowed': 'Este método de acesso ainda não foi habilitado. Avise a equipe.',
    'auth/account-exists-with-different-credential': 'Entre pelo método original da sua conta. Depois use Vincular Google na sessão autenticada.',
    'auth/credential-already-in-use': 'Este Google já pertence a outra conta. Entre nessa conta ou procure a equipe.',
    'auth/provider-already-linked': 'O Google já está vinculado a esta conta.',
    'auth/email-already-in-use': 'Não foi possível criar a conta. Tente entrar ou recuperar o acesso.',
    'auth/weak-password': 'A senha não atende à política do projeto. Use uma senha mais forte.',
    'auth/too-many-requests': 'Muitas tentativas. Aguarde um pouco antes de tentar novamente.',
    'auth/requires-recent-login': 'Entre novamente antes de concluir esta operação.',
  };
  return (code && messages[code]) || 'Não foi possível entrar ou concluir a operação. Confira seus dados e tente novamente.';
}
