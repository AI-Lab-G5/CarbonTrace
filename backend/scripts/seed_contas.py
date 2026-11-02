"""Cria as contas de demonstracao no Auth Emulator e vincula a empresa.

Uso (com o emulador no ar):

    FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099 python scripts/seed_contas.py

O CA-01 do CP2 pede que um integrante clone o repositorio e suba o
ambiente com "docker compose up" sem ajuste manual. So que um banco com
unidades e fatores, mas sem conta nenhuma no Auth, nao deixa ninguem
entrar: o login do frontend depende de um ID token, e o token depende de
um usuario existir. Este script fecha essa lacuna.

Nunca roda contra a nuvem: sem FIREBASE_AUTH_EMULATOR_HOST ele recusa.
Criar conta de teste em producao e o tipo de acidente que ninguem
percebe na hora.
"""

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Contas fixas, uma por empresa. A senha e publica de proposito: e dado
# sintetico de emulador local, documentado no README, e o ensaio do guia
# exige que qualquer integrante consiga entrar sem pedir segredo a
# ninguem. Nao existe caminho para estas contas fora do emulador.
SENHA_DEMO = "carbontrace-demo"

CONTAS_DEMO = [
    {
        "email": "demo-a@carbontrace.local",
        "nome": "Ana Demonstracao",
        "tenant_id": "empresa-a",
    },
    {
        "email": "demo-b@carbontrace.local",
        "nome": "Bruno Demonstracao",
        "tenant_id": "empresa-b",
    },
]


def _garantir_app() -> None:
    import firebase_admin

    if not firebase_admin._apps:
        firebase_admin.initialize_app()


def criar_ou_atualizar_conta(conta: dict) -> str:
    """Cria a conta se nao existir e devolve o uid.

    Idempotente: rodar o seed duas vezes nao duplica usuario nem quebra
    o "docker compose up" de quem ja subiu o ambiente antes.
    """
    from firebase_admin import auth

    try:
        usuario = auth.get_user_by_email(conta["email"])
        auth.update_user(
            usuario.uid,
            password=SENHA_DEMO,
            display_name=conta["nome"],
            email_verified=True,
        )
    except auth.UserNotFoundError:
        usuario = auth.create_user(
            email=conta["email"],
            password=SENHA_DEMO,
            display_name=conta["nome"],
            email_verified=True,
        )

    # A claim e o que o backend le para decidir o tenant. Sem ela o
    # funcionario autentica mas recebe 403 em toda rota de negocio.
    auth.set_custom_user_claims(
        usuario.uid,
        {"tenant_id": conta["tenant_id"], "papel": "funcionario"},
    )
    return usuario.uid


def main() -> int:
    if not os.environ.get("FIREBASE_AUTH_EMULATOR_HOST"):
        print("ERRO: defina FIREBASE_AUTH_EMULATOR_HOST antes de rodar o seed.")
        print("Este script nunca deve criar contas na nuvem.")
        return 1

    os.environ.setdefault("FIREBASE_PROJECT_ID", "demo-carbontrace")
    _garantir_app()

    for conta in CONTAS_DEMO:
        uid = criar_ou_atualizar_conta(conta)
        print(f"{conta['email']} -> {conta['tenant_id']} (uid {uid})")

    print("\nContas de demonstracao prontas.")
    print(f"Senha das duas contas: {SENHA_DEMO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
