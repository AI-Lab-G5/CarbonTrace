from decimal import Decimal
import pytest

from tests.conftest import TENANT_A, TENANT_B

pytestmark = pytest.mark.precisa_banco


@pytest.mark.parametrize(
    "lancamentos, total_esperado, qtd_unidades_esperada",
    [
        # Cenário 0: nenhum lançamento no período
        ([], Decimal("0"), 0),
        # Cenário 1: único lançamento
        (
            [{"id": "c1", "unidade_id": "u1", "emissao_kg_co2e": "12.500"}],
            Decimal("12.500"),
            1,
        ),
        # Cenário 2: dois lançamentos na mesma unidade e período
        (
            [
                {"id": "c1", "unidade_id": "u1", "emissao_kg_co2e": "12.500"},
                {"id": "c2", "unidade_id": "u1", "emissao_kg_co2e": "7.250"},
            ],
            Decimal("19.750"),
            1,
        ),
        # Cenário N: múltiplos lançamentos distribuídos entre unidades
        (
            [
                {"id": "c1", "unidade_id": "u1", "emissao_kg_co2e": "10.125"},
                {"id": "c2", "unidade_id": "u1", "emissao_kg_co2e": "4.875"},
                {"id": "c3", "unidade_id": "u2", "emissao_kg_co2e": "3.500"},
                {"id": "c4", "unidade_id": "u2", "emissao_kg_co2e": "6.500"},
                {"id": "c5", "unidade_id": "u3", "emissao_kg_co2e": "5.000"},
            ],
            Decimal("30.000"),
            3,
        ),
    ],
)
def test_consolidado_agrega_todos_lancamentos_elegiveis(
    banco,
    como_funcionario,
    lancamentos,
    total_esperado,
    qtd_unidades_esperada,
):
    competencia = "2026-10"

    for uid, nome in [("u1", "Loja Centro"), ("u2", "Loja Norte"), ("u3", "Loja Sul")]:
        banco.collection("tenants").document(TENANT_A).collection("unidades").document(uid).set(
            {"nome": nome}
        )

    for item in lancamentos:
        banco.collection("tenants").document(TENANT_A).collection("consumos").document(item["id"]).set(
            {
                "competencia": competencia,
                **item,
            }
        )

    # Ruído de outro tenant e outra competência (não devem entrar na soma)
    banco.collection("tenants").document(TENANT_B).collection("consumos").document("outro-tenant").set(
        {
            "competencia": competencia,
            "unidade_id": "u1",
            "emissao_kg_co2e": "999.000",
        }
    )
    banco.collection("tenants").document(TENANT_A).collection("consumos").document("outra-comp").set(
        {
            "competencia": "2026-09",
            "unidade_id": "u1",
            "emissao_kg_co2e": "500.000",
        }
    )

    resp = como_funcionario.get(f"/v1/consolidado?competencia={competencia}")
    assert resp.status_code == 200
    body = resp.json()

    assert Decimal(str(body["total_kg_co2e"])) == total_esperado
    assert len(body["por_unidade"]) == qtd_unidades_esperada

    if len(lancamentos) == 5:
        por_uid = {linha["unidade_id"]: Decimal(str(linha["emissao_kg_co2e"])) for linha in body["por_unidade"]}
        assert por_uid["u1"] == Decimal("15.000")
        assert por_uid["u2"] == Decimal("10.000")
        assert por_uid["u3"] == Decimal("5.000")