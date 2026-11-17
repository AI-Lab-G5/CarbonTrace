"""CA-03 / CA-04: prova de deny-all das Security Rules no emulador.

O que este teste prova, e por que ele existe separado da suite do backend:

O backend tem 182 testes que exercitam a autorizacao da **API**. Nenhum
deles toca nas Security Rules do Firestore, porque a API usa o Admin SDK,
que ignora as Rules por definicao. Isso deixa um buraco: se alguem
chamar o Firestore direto do navegador, quem responde e a Rule, e ninguem
nunca a testou.

Este arquivo fecha esse buraco. Ele fala com o Firestore pelo mesmo
caminho que um cliente falaria -- REST, com e sem token -- e exige 403
nos dois casos. Depois prova que o Admin SDK continua funcionando, porque
deny-all mal feito quebraria a API inteira.

Como rodar (com o emulador no ar):

    python -m pytest qa/test_deny_all.py -v

Sem emulador os testes pulam sozinhos, para nao quebrar quem so quer
rodar a suite do backend.
"""

import os

import httpx
import pytest

PROJETO = os.environ.get("FIREBASE_PROJECT_ID", "demo-carbontrace")
FIRESTORE = os.environ.get("FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")
AUTH = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST", "127.0.0.1:9099")

# Caminho de dado real de cliente. Se a Rule for deny-all de verdade, o
# cliente nem chega a saber se este documento existe.
ALVO = "tenants/empresa-a/unidades"
DOC = "tenants/empresa-a/unidades/documento-de-teste"

# Contas criadas por backend/scripts/seed_contas.py.
CONTA_A = ("demo-a@carbontrace.local", "carbontrace-demo")
CONTA_B = ("demo-b@carbontrace.local", "carbontrace-demo")


def _base_firestore() -> str:
    return f"http://{FIRESTORE}/v1/projects/{PROJETO}/databases/(default)/documents"


def _emulador_no_ar() -> bool:
    """Sonda barata: o emulador responde?

    Sem isso, o teste falharia com erro de conexao em toda maquina que
    nao subiu o Compose, e "quebrado" viraria o estado normal da suite.
    """
    try:
        httpx.get(f"http://{FIRESTORE}/", timeout=2.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _emulador_no_ar(),
    reason="Emulador do Firestore nao esta no ar (suba com docker compose up).",
)


def _token(email: str, senha: str) -> str:
    """Pega um ID token real do Auth Emulator.

    Token de verdade, e nao um dicionario de claims: a Rule le
    request.auth, que o emulador monta a partir da assinatura do token.
    Um dicionario forjado nao passaria por esse caminho.
    """
    resposta = httpx.post(
        f"http://{AUTH}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
        params={"key": "fake-api-key"},
        json={"email": email, "password": senha, "returnSecureToken": True},
        timeout=10.0,
    )
    resposta.raise_for_status()
    return resposta.json()["idToken"]


def _headers(token: str | None) -> dict:
    return {"Authorization": f"Bearer {token}"} if token else {}


# --------------------------------------------------------------------
# Cliente anonimo: sem token nenhum
# --------------------------------------------------------------------


def test_anonimo_nao_le():
    resposta = httpx.get(f"{_base_firestore()}/{ALVO}", headers=_headers(None), timeout=10.0)
    assert resposta.status_code == 403, (
        f"Anonimo leu {ALVO} (status {resposta.status_code}). "
        "A Rule deveria negar tudo para quem nao esta autenticado."
    )


def test_anonimo_nao_escreve():
    resposta = httpx.patch(
        f"{_base_firestore()}/{DOC}",
        headers=_headers(None),
        json={"fields": {"nome": {"stringValue": "invasao"}}},
        timeout=10.0,
    )
    assert resposta.status_code == 403, (
        f"Anonimo escreveu em {DOC} (status {resposta.status_code})."
    )


def test_anonimo_nao_apaga():
    resposta = httpx.delete(f"{_base_firestore()}/{DOC}", headers=_headers(None), timeout=10.0)
    assert resposta.status_code == 403


# --------------------------------------------------------------------
# Cliente autenticado de verdade -- o caso que mais importa
# --------------------------------------------------------------------


@pytest.fixture(scope="module")
def token_valido() -> str:
    return _token(*CONTA_A)


def test_usuario_autenticado_nao_le(token_valido):
    """Mesmo com token legitimo e da empresa certa, o cliente nao le.

    Este e o coracao do deny-all: nao basta barrar desconhecido. O
    funcionario autenticado da empresa A tambem nao pode falar direto
    com o banco -- todo acesso passa pela API, que tem autorizacao
    propria e auditavel.
    """
    resposta = httpx.get(
        f"{_base_firestore()}/{ALVO}", headers=_headers(token_valido), timeout=10.0
    )
    assert resposta.status_code == 403, (
        f"Funcionario autenticado leu {ALVO} direto (status {resposta.status_code}). "
        "Deny-all exige que nem ele leia sem passar pela API."
    )


def test_usuario_autenticado_nao_escreve(token_valido):
    resposta = httpx.patch(
        f"{_base_firestore()}/{DOC}",
        headers=_headers(token_valido),
        json={"fields": {"nome": {"stringValue": "invasao"}}},
        timeout=10.0,
    )
    assert resposta.status_code == 403, (
        f"Funcionario autenticado escreveu em {DOC} direto (status {resposta.status_code})."
    )


def test_usuario_de_outra_empresa_tambem_nao_le():
    """Empresa B tentando ler empresa A -- negado antes mesmo do tenant."""
    token = _token(*CONTA_B)
    resposta = httpx.get(f"{_base_firestore()}/{ALVO}", headers=_headers(token), timeout=10.0)
    assert resposta.status_code == 403


def test_autenticado_nao_le_fatores_direto(token_valido):
    """Fatores tambem sao serve-so-pela-API.

    A versao anterior da Rule permitia leitura publica de /fatores. O
    frontend nao le fatores direto (usa GET /v1/fontes), entao manter a
    porta aberta seria superficie de ataque sem contrapartida.
    """
    resposta = httpx.get(
        f"{_base_firestore()}/fatores/v1", headers=_headers(token_valido), timeout=10.0
    )
    assert resposta.status_code == 403


# --------------------------------------------------------------------
# A API continua funcionando (Admin SDK ignora Rules)
# --------------------------------------------------------------------


def test_admin_sdk_continua_lendo_e_escrevendo():
    """A segunda camada nao pode derrubar a primeira.

    Se as Rules barrarem o Admin SDK, a API inteira para. Este teste
    existe para provar que nao barram.
    """
    from google.cloud import firestore

    db = firestore.Client(project=PROJETO)
    ref = db.collection("tenants").document("empresa-a").collection("unidades").document(
        "sonda-admin-sdk"
    )
    ref.set({"nome": "Sonda", "origem": "qa-deny-all"})
    assert ref.get().exists
    ref.delete()


def test_api_responde_com_dado_semeado(token_valido):
    """Ponta a ponta: token real -> API -> Firestore.

    Prova que negar o cliente direto nao atrapalhou a jornada real.
    """
    try:
        resposta = httpx.get(
            "http://127.0.0.1:8000/v1/unidades",
            headers=_headers(token_valido),
            timeout=10.0,
        )
    except httpx.HTTPError:
        # Sem a API no ar nao ha o que provar aqui. O job de CI sobe so o
        # emulador; a API e exercitada pelos 182 testes do backend.
        pytest.skip("API nao esta no ar (suba com docker compose up).")
    assert resposta.status_code == 200, resposta.text
