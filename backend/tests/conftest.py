"""Fixtures compartilhadas.

Duas substituicoes acontecem aqui, cada uma por um motivo diferente.

A verificacao do ID token e substituida em todos os testes. Isso e
deliberado: conferir assinatura e validade e codigo do Firebase, ja
testado por eles. O que precisamos provar e a nossa autorizacao -- que o
tenant vem da claim e nao do cliente, que papel errado e barrado, que
token expirado nao passa. Substituindo o verificador, cada um desses
casos vira um teste deterministico, sem emitir token real nem depender
de rede.

O Firestore e substituido apenas nos testes marcados com
@pytest.mark.precisa_banco, por um duble em memoria (duble_firestore.py)
criado do zero a cada teste. Antes esses testes dependiam do emulador e
eram pulados sem ele -- ou seja, nunca rodavam na pipeline. O duble nao
substitui o emulador: regras de seguranca, indices e transacoes
continuam sendo verificados la, na issue #24 do QA. Ele garante que o
caminho HTTP -> dominio -> persistencia -> HTTP esteja exercitado em
toda execucao da suite.
"""

import json
from pathlib import Path
from typing import Annotated

import pytest
from fastapi import Header, HTTPException, status
from fastapi.testclient import TestClient

from app.auth import claims_do_token
from app.main import app
from tests.duble_firestore import ClienteFake

TENANT_A = "empresa-a"
TENANT_B = "empresa-b"

PASTA_DADOS = Path(__file__).resolve().parents[2] / "docs" / "dados"
VERSOES_DE_FATORES = ["fatores-v1.json", "fatores-v2.json"]


def claims(
    uid: str = "ana",
    tenant_id: str = TENANT_A,
    papel: str = "funcionario",
    email: str = "ana@empresa-a.exemplo",
) -> dict:
    """Claims equivalentes as que o Firebase devolveria."""
    return {"uid": uid, "tenant_id": tenant_id, "papel": papel, "email": email}


def _publicar_fatores(cliente: ClienteFake) -> None:
    """Carrega o catalogo real, o mesmo que o seed grava no emulador.

    Ler o arquivo de verdade em vez de inventar fatores no teste e o que
    faz 1500 kWh x 0,0385 = 57,750 significar alguma coisa: o numero
    conferido a mao e o numero que a aplicacao publica.
    """
    for arquivo in VERSOES_DE_FATORES:
        conjunto = json.loads((PASTA_DADOS / arquivo).read_text(encoding="utf-8"))
        cliente.collection("fatores").document(conjunto["versao"]).set(
            {
                "vigencia_inicio": conjunto["vigencia_inicio"],
                "vigencia_fim": conjunto.get("vigencia_fim"),
                "publicado_em": conjunto["publicado_em"],
                "status": conjunto["status"],
                "fatores": conjunto["fatores"],
            }
        )


@pytest.fixture(autouse=True)
def banco(request, monkeypatch):
    """Banco limpo para cada teste marcado com precisa_banco.

    Autouse para rodar antes das fixtures de cliente -- o TestClient
    precisa encontrar o banco ja no lugar. Nos demais testes nao faz
    nada, de modo que 'sem banco' continue significando sem banco.
    """
    if request.node.get_closest_marker("precisa_banco") is None:
        yield None
        return

    from app.services.fatores import carregar_versao

    cliente = ClienteFake()
    _publicar_fatores(cliente)
    monkeypatch.setattr("app.db.get_db", lambda: cliente)

    # O cache de versoes e seguro em producao (versao publicada e
    # imutavel), mas entre testes guardaria o catalogo do banco anterior.
    carregar_versao.cache_clear()
    yield cliente
    carregar_versao.cache_clear()


# --------------------------------------------------------------------
# Quem esta chamando
# --------------------------------------------------------------------
#
# A identidade vai num cabecalho de teste, e nao numa substituicao
# global por fixture. A diferenca importa: um teste de isolamento usa
# dois clientes ao mesmo tempo -- a empresa A grava, a B tenta ler. Com
# uma substituicao global, a segunda fixture sobrescreve a primeira e os
# dois clientes viram a mesma pessoa; o teste passa sem provar nada, que
# e a pior maneira de um teste de seguranca falhar.

CABECALHO_PERSONA = "X-Teste-Persona"

PERSONAS: dict[str, dict] = {
    "funcionario-a": claims(),
    "funcionario-b": claims(
        uid="bruno", tenant_id=TENANT_B, email="bruno@empresa-b.exemplo"
    ),
    "papel-errado": claims(papel="auditor_externo"),
    "sem-empresa": {"uid": "novo", "papel": "funcionario"},
}


def _claims_de_teste(
    persona: Annotated[str | None, Header(alias=CABECALHO_PERSONA)] = None,
) -> dict:
    """Substituta de claims_do_token: a persona faz o papel do ID token."""
    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization: Bearer <id_token> e obrigatorio.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if persona == "token-expirado":
        # O que o SDK do Firebase faz quando o token passou da validade.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado. Entre novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return PERSONAS[persona]


@pytest.fixture(autouse=True)
def _verificador_de_token():
    app.dependency_overrides[claims_do_token] = _claims_de_teste
    yield
    app.dependency_overrides.clear()


def _cliente_como(persona: str | None, **kwargs) -> TestClient:
    cabecalhos = {CABECALHO_PERSONA: persona} if persona else {}
    return TestClient(app, headers=cabecalhos, **kwargs)


@pytest.fixture
def cliente() -> TestClient:
    """Cliente sem autenticacao: exercita o caminho de token ausente."""
    with _cliente_como(None) as c:
        yield c


@pytest.fixture
def como_funcionario() -> TestClient:
    """Cliente autenticado como funcionario da empresa A."""
    with _cliente_como("funcionario-a") as c:
        yield c


@pytest.fixture
def como_outra_empresa() -> TestClient:
    """Funcionario legitimo, mas da empresa B."""
    with _cliente_como("funcionario-b") as c:
        yield c


@pytest.fixture
def com_papel_errado() -> TestClient:
    """Token valido, papel que nao existe no sistema."""
    with _cliente_como("papel-errado") as c:
        yield c


@pytest.fixture
def com_token_expirado() -> TestClient:
    with _cliente_como("token-expirado") as c:
        yield c


@pytest.fixture
def sem_empresa() -> TestClient:
    """Usuario autenticado que ainda nao foi vinculado a uma empresa."""
    with _cliente_como("sem-empresa") as c:
        yield c


@pytest.fixture
def como_funcionario_sem_banco() -> TestClient:
    """Autenticado, mas sem Firestore por tras.

    Serve aos testes que provam que a entrada passou da validacao: eles
    so precisam saber que a resposta nao foi 422. Sem banco, o handler
    morre depois -- e com raise_server_exceptions=False isso vira 500 em
    vez de estourar no teste.

    Vale a pena existir: sem ele, um validador exageradamente restritivo
    recusaria tudo e todos os testes negativos continuariam verdes.
    """
    with _cliente_como("funcionario-a", raise_server_exceptions=False) as c:
        yield c
