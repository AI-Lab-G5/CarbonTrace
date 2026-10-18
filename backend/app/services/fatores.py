"""Leitura dos fatores de emissao versionados.

Fatores sao globais (valem para todos os tenants) e imutaveis: uma versao
publicada nunca e editada. Corrigir um numero significa publicar uma versao
nova, nao sobrescrever a antiga. Sem isso, um relatorio emitido em marco
deixaria de bater consigo mesmo em dezembro.
"""

from functools import lru_cache

from app.db import colecao_global
from app.models import Fator, VersaoFatores


@lru_cache(maxsize=16)
def carregar_versao(versao: str) -> VersaoFatores | None:
    """Le uma versao do Firestore.

    O cache e seguro justamente porque a versao e imutavel: o conteudo
    de 'v1' hoje e o mesmo de daqui a um ano.
    """
    doc = colecao_global("fatores").document(versao).get()
    if not doc.exists:
        return None
    dados = doc.to_dict()
    return VersaoFatores(
        versao=versao,
        vigencia_inicio=dados["vigencia_inicio"],
        publicado_em=dados["publicado_em"],
        fatores=[Fator(**f) for f in dados["fatores"]],
    )


def listar_versoes() -> list[str]:
    return sorted(d.id for d in colecao_global("fatores").stream())


def versao_vigente(competencia: str) -> str:
    """Qual versao de fatores vale para uma competencia.

    Escolhe a versao mais recente cuja vigencia comecou ate a competencia
    informada. Um lancamento de 2025-03 usa os fatores de 2025, mesmo que
    seja digitado em 2026.
    """
    candidatas: list[tuple[str, str]] = []
    for doc in colecao_global("fatores").stream():
        inicio = doc.to_dict().get("vigencia_inicio", "")
        if inicio <= competencia:
            candidatas.append((inicio, doc.id))
    if not candidatas:
        raise RuntimeError(
            f"Nenhuma versao de fatores vigente para a competencia {competencia}. "
            "Rode o seed antes de lancar registros."
        )
    return max(candidatas)[1]


def buscar_fator(versao: str, fonte_id: str) -> Fator | None:
    conjunto = carregar_versao(versao)
    if conjunto is None:
        return None
    return next((f for f in conjunto.fatores if f.fonte_id == fonte_id), None)
