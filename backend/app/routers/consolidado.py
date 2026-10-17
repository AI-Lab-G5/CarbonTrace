"""Consolidacao da rede em uma competencia."""

from fastapi import APIRouter, Depends, Query

from app.auth import Identidade, identidade_atual
from app.db import colecao_do_tenant
from app.models import Consolidado, LinhaConsolidado
from app.services.calculo import consolidar

router = APIRouter(prefix="/v1/consolidado", tags=["consolidado"])


@router.get("", response_model=Consolidado)
def obter(
    competencia: str = Query(description="Mes de referencia, no formato AAAA-MM"),
    identidade: Identidade = Depends(identidade_atual),
) -> Consolidado:
    registros = (
        colecao_do_tenant(identidade.tenant_id, "registros")
        .where("competencia", "==", competencia)
        .stream()
    )

    por_unidade: dict[str, float] = {}
    for doc in registros:
        dados = doc.to_dict()
        unidade_id = dados["unidade_id"]
        por_unidade[unidade_id] = por_unidade.get(unidade_id, 0.0) + dados["emissao_kg_co2e"]

    total, mediana = consolidar(por_unidade)

    nomes = {
        d.id: d.to_dict().get("nome", d.id)
        for d in colecao_do_tenant(identidade.tenant_id, "unidades").stream()
    }

    linhas = [
        LinhaConsolidado(
            unidade_id=uid,
            unidade_nome=nomes.get(uid, uid),
            emissao_kg_co2e=round(valor, 6),
        )
        for uid, valor in sorted(por_unidade.items(), key=lambda par: -par[1])
    ]

    return Consolidado(
        competencia=competencia,
        total_kg_co2e=total,
        mediana_kg_co2e=mediana,
        por_unidade=linhas,
    )
