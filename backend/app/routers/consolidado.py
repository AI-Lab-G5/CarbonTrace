"""Consolidacao da rede numa competencia.

Entra no CP2 como leitura de apoio a J3. Dashboard, ranking e outliers
ficam fora por decisao do CA-07.
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from google.cloud.firestore_v1.base_query import FieldFilter

from app.auth import Identidade, funcionario_atual
from app.db import colecao_do_tenant
from app.dominio.calculo import mediana, somar
from app.dominio.numeros import para_decimal
from app.models import Consolidado, LinhaConsolidado

router = APIRouter(prefix="/v1/consolidado", tags=["consolidado"])


@router.get("", response_model=Consolidado)
def obter(
    competencia: str = Query(description="Mes de referencia, formato AAAA-MM"),
    identidade: Identidade = Depends(funcionario_atual),
) -> Consolidado:
    consumos = (
        colecao_do_tenant(identidade.tenant_id, "consumos")
        .where(filter=FieldFilter("competencia", "==", competencia))
        .stream()
    )

    por_unidade: dict[str, Decimal] = {}
    for doc in consumos:
        dados = doc.to_dict()
        unidade_id = dados["unidade_id"]
        emissao = para_decimal(dados["emissao_kg_co2e"], campo="emissao_kg_co2e")
        por_unidade[unidade_id] = por_unidade.get(unidade_id, Decimal(0)) + emissao

    valores = list(por_unidade.values())

    nomes = {
        d.id: d.to_dict().get("nome", d.id)
        for d in colecao_do_tenant(identidade.tenant_id, "unidades").stream()
    }

    linhas = [
        LinhaConsolidado(
            unidade_id=uid,
            unidade_nome=nomes.get(uid, uid),
            emissao_kg_co2e=valor,
        )
        for uid, valor in sorted(por_unidade.items(), key=lambda par: -par[1])
    ]

    return Consolidado(
        competencia=competencia,
        total_kg_co2e=somar(valores),
        mediana_kg_co2e=mediana(valores),
        por_unidade=linhas,
    )
