"""Quem gravou e quando -- CA-01 da issue #35.

Todo registro de negocio carrega o UID de quem o criou e de quem o
alterou pela ultima vez, com as datas. Sem isso, um numero errado no
inventario e um numero sem dono: ninguem sabe a quem perguntar.

O UID vem sempre da claim do token verificado, nunca do corpo do
pedido. Se viesse do corpo, a autoria seria uma declaracao do cliente --
e um campo que o cliente escolhe nao prova nada. Por isso
`CAMPOS_DE_AUTORIA` existe: as rotas usam esse conjunto para descartar
qualquer tentativa de informar autoria na entrada.

Data em ISO 8601 UTC, segundo a segundo. Guardar como texto mantem a
mesma regra ja usada para numeros (ADR-009): o Firestore converteria um
timestamp para o seu proprio tipo, e a leitura de volta dependeria do
fuso de quem le.
"""

from __future__ import annotations

from datetime import UTC, datetime

CAMPOS_DE_AUTORIA = frozenset(
    {"criado_por_uid", "criado_em", "atualizado_por_uid", "atualizado_em"}
)


def agora() -> str:
    """Instante atual em ISO 8601 UTC, sem microssegundos.

    Microssegundo nenhum ajuda a auditar e so polui a tela. Segundo
    basta para ordenar e para responder "quando foi gravado".
    """
    return datetime.now(UTC).isoformat(timespec="seconds")


def marcar_criacao(dados: dict, uid: str) -> dict:
    """Carimba autoria de criacao num documento novo."""
    instante = agora()
    return {
        **dados,
        "criado_por_uid": uid,
        "criado_em": instante,
        "atualizado_por_uid": uid,
        "atualizado_em": instante,
    }


def marcar_atualizacao(dados: dict, uid: str, anterior: dict | None) -> dict:
    """Carimba a alteracao preservando quem criou.

    O ponto delicado: o lancamento e gravado com `set`, que substitui o
    documento inteiro. Sem trazer `criado_por_uid` e `criado_em` do
    documento anterior, a primeira correcao apagaria a autoria original
    e o registro passaria a parecer criado por quem corrigiu.

    Quando nao ha documento anterior, a alteracao e uma criacao.
    """
    if not anterior:
        return marcar_criacao(dados, uid)

    return {
        **dados,
        "criado_por_uid": anterior.get("criado_por_uid", uid),
        "criado_em": anterior.get("criado_em", agora()),
        "atualizado_por_uid": uid,
        "atualizado_em": agora(),
    }


def sem_autoria(dados: dict) -> dict:
    """Remove autoria vinda do cliente.

    Usado na entrada das rotas: o que o cliente mandar nesses campos e
    descartado antes de chegar ao banco.
    """
    return {k: v for k, v in dados.items() if k not in CAMPOS_DE_AUTORIA}
