"""Validação integrada de J4, exclusivamente nos emuladores."""

import json
import os
from decimal import Decimal
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

import firebase_admin
from firebase_admin import auth
from google.auth.credentials import AnonymousCredentials
from google.cloud import firestore

PROJETO = "demo-carbontrace"
API = "http://127.0.0.1:8000"

# Conferir o destino antes de criar qualquer dado.
assert os.environ.get("FIREBASE_PROJECT_ID") == PROJETO
assert os.environ.get("FIRESTORE_EMULATOR_HOST") == "firebase-emulator:8080"
assert os.environ.get("FIREBASE_AUTH_EMULATOR_HOST") == "firebase-emulator:9099"

firebase_admin.initialize_app(options={"projectId": PROJETO})
db = firestore.Client(
    project=PROJETO,
    credentials=AnonymousCredentials(),
)
execucao = uuid4().hex[:12]


def requisitar(metodo, url, dados=None, token=None, esperado=200):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    pedido = Request(
        url,
        data=json.dumps(dados).encode() if dados is not None else None,
        headers=headers,
        method=metodo,
    )
    try:
        with urlopen(pedido, timeout=30) as resposta:
            codigo = resposta.status
            corpo = resposta.read()
    except HTTPError as erro:
        codigo = erro.code
        corpo = erro.read()

    try:
        resultado = json.loads(corpo)
    except json.JSONDecodeError:
        raise AssertionError(
            f"{metodo} {url}: HTTP {codigo}; "
            f"resposta não JSON: {corpo.decode('utf-8', errors='replace')[:500]}"
        ) from None

    assert codigo == esperado, (
        f"{metodo} {url}: esperado {esperado}, "
        f"recebido {codigo}: {resultado}"
    )
    return resultado


def conta(letra):
    tenant = f"qa-j4-{execucao}-{letra}"
    email = f"{tenant}@example.test"
    senha = "qa-j4-somente-emulador"
    usuario = auth.create_user(
        email=email, password=senha, email_verified=True
    )
    auth.set_custom_user_claims(
        usuario.uid,
        {"tenant_id": tenant, "papel": "funcionario"},
    )
    login = requisitar(
        "POST",
        "http://firebase-emulator:9099/identitytoolkit.googleapis.com/"
        "v1/accounts:signInWithPassword?key=teste-local",
        {"email": email, "password": senha, "returnSecureToken": True},
    )
    return tenant, login["idToken"]


def api(token, metodo, caminho, dados=None, esperado=200):
    return requisitar(metodo, API + caminho, dados, token, esperado)


def preparar(tenant, mes, valores):
    raiz = db.collection("tenants").document(tenant)
    for numero, valor in enumerate(valores, start=1):
        unidade = f"u{numero}"
        raiz.collection("unidades").document(unidade).set({
            "nome": f"Loja QA {numero}",
            "cidade": "Cidade de teste",
            "uf": "DF" if numero < 3 else "GO",
            "ativa": True,
        })
        raiz.collection("consumos").document(f"{mes}_{unidade}").set({
            "unidade_id": unidade,
            "competencia": mes,
            "fonte_id": "eletricidade" if numero < 3 else "diesel",
            "escopo": "2" if numero < 3 else "1",
            "emissao_kg_co2e": valor,
        })


def gerar(token, mes, esperado=201):
    return api(
        token, "POST", "/v1/snapshots",
        {"competencia": mes}, esperado,
    )


def comparacao(token, snapshot):
    return api(
        token, "GET",
        f"/v1/snapshots/{snapshot['id']}/comparacao",
    )


saude = requisitar("GET", API + "/healthz")
assert saude["emulador"] is True
assert requisitar("GET", API + "/readyz")["status"] == "pronto"

tenant_a, token_a = conta("a")
tenant_b, token_b = conta("b")

preparar(tenant_a, "2026-01", ["100.000", "100.000", "200.000"])
preparar(tenant_a, "2026-02", ["50.000", "100.000", "150.000"])

# Uma consulta não pode gerar o snapshot.
api(token_a, "GET", "/v1/agregados?competencia=2026-01", esperado=404)
colecao = db.collection("tenants").document(tenant_a).collection("snapshots")
assert list(colecao.stream()) == []

janeiro = gerar(token_a, "2026-01")["snapshot"]
assert Decimal(janeiro["total_kg_co2e"]) == Decimal("400")
assert janeiro["unidades_no_total"] == 3
regioes = {
    r["regiao"]: Decimal(r["emissao_kg_co2e"])
    for r in janeiro["por_regiao"]
}
assert regioes == {"DF": Decimal("200"), "GO": Decimal("200")}
assert sum(Decimal(e["emissao_kg_co2e"]) for e in janeiro["por_escopo"]) == 400

comparado = comparacao(token_a, janeiro)
assert comparado["disponivel"] is True
assert Decimal(comparado["mediana_kg_co2e"]) == 100
print("PASSOU: 100/100/200; total 400; regiões 200/200; mediana 100.")

# Percorrer páginas de uma unidade sem alterar os totais.
caminho = f"/v1/snapshots/{janeiro['id']}/unidades"
assert api(token_a, "GET", caminho)["limite"] == 20
linhas = []
cursor = None
for _ in range(10):
    parametros = {"limite": 1}
    if cursor:
        parametros["cursor"] = cursor
    pagina = api(token_a, "GET", caminho + "?" + urlencode(parametros))
    linhas.extend(pagina["itens"])
    cursor = pagina["proximo_cursor"]
    if not cursor:
        break
assert cursor is None
assert len(linhas) == 3
assert len({linha["unidade_id"] for linha in linhas}) == 3
assert sum(
        Decimal(linha["emissao_kg_co2e"]) for linha in linhas
        ) == 400

filtrado = api(token_a, "GET", caminho + "?regiao=GO")
assert len(filtrado["itens"]) == 1
assert Decimal(filtrado["itens"][0]["emissao_kg_co2e"]) == 200
api(token_a, "GET", caminho + "?limite=101", esperado=422)
print("PASSOU: paginação, filtro regional e limite máximo.")

fevereiro = gerar(token_a, "2026-02")["snapshot"]
assert Decimal(fevereiro["total_kg_co2e"]) == 300
comparado = comparacao(token_a, fevereiro)
assert comparado["disponivel"] is True
assert all(linha["alerta"] is False for linha in comparado["linhas"])
assert Decimal(api(
    token_a, "GET", "/v1/agregados?competencia=2026-01"
)["total_kg_co2e"]) == 400
print("PASSOU: meses independentes e ±50% exato sem alerta.")

# A empresa B não pode ler snapshots ou agregados da A.
api(token_b, "GET", f"/v1/snapshots/{janeiro['id']}", esperado=404)
api(token_b, "GET", "/v1/agregados?competencia=2026-01", esperado=404)
assert api(token_b, "GET", "/v1/snapshots")["itens"] == []

preparar(tenant_b, "2026-01", ["999.000"])
snapshot_b = gerar(token_b, "2026-01")["snapshot"]
assert Decimal(snapshot_b["total_kg_co2e"]) == 999
assert Decimal(api(
    token_a, "GET", f"/v1/snapshots/{janeiro['id']}"
)["total_kg_co2e"]) == 400
print("PASSOU: isolamento de snapshots e agregados entre empresas.")

repetido = gerar(token_a, "2026-01", esperado=200)
assert repetido["criado"] is False
assert repetido["snapshot"]["id"] == janeiro["id"]

db.collection("tenants").document(tenant_a).collection("consumos").document(
    "2026-01_u1"
).update({"emissao_kg_co2e": "101.000"})

novo = gerar(token_a, "2026-01")["snapshot"]
assert novo["versao"] == janeiro["versao"] + 1
assert Decimal(novo["total_kg_co2e"]) == 401
antigo = api(token_a, "GET", f"/v1/snapshots/{janeiro['id']}")
assert antigo == janeiro
print("PASSOU: reenvio sem duplicação e snapshot anterior preservado.")

for mes, valores, total in [
    ("2026-03", ["0.000", "0.000", "0.000"], "0"),
    ("2026-04", ["100.000", "100.000"], "200"),
    ("2026-05", ["0.101", "0.202", "0.303"], "0.606"),
]:
    preparar(tenant_a, mes, valores)
    snapshot = gerar(token_a, mes)["snapshot"]
    assert Decimal(snapshot["total_kg_co2e"]) == Decimal(total)
    comparado = comparacao(token_a, snapshot)
    if mes != "2026-05":
        assert comparado["disponivel"] is False
        assert comparado["motivo"]
    else:
        assert Decimal(comparado["mediana_kg_co2e"]) == Decimal("0.202")
print("PASSOU: mediana zero, menos de 3 elegíveis e frações exatas.")

# Mesmo um desvio pouco acima de 50% deve alertar.
preparar(tenant_a, "2026-06", ["49.999", "100.000", "150.001"])
snapshot = gerar(token_a, "2026-06")["snapshot"]
comparado = comparacao(token_a, snapshot)
alertas = {
    linha["unidade_id"]: linha["alerta"]
    for linha in comparado["linhas"]
}
assert alertas == {"u1": True, "u2": False, "u3": True}, (
    f"Desvios de ±50,001% devem alertar. Recebido: {alertas}"
)
print("PASSOU: desvios estritamente maiores que 50%.")
print("VALIDAÇÃO J4 CONCLUÍDA.")
db.close()
