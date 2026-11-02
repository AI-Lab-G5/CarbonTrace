"""Convites privados: transação reserva o convite e a associação antes das claims."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from firebase_admin import auth
from google.cloud import firestore

from app.db import get_db


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def criar_convite(email: str, tenant_id: str, horas: int = 24) -> str:
    if not email.strip() or "@" not in email or not tenant_id or "/" in tenant_id:
        raise ValueError("E-mail e empresa válidos são obrigatórios.")
    if not 1 <= horas <= 168:
        raise ValueError("Validade deve estar entre 1 e 168 horas.")
    token = secrets.token_urlsafe(32)
    get_db().collection("convites").document(digest(token)).create(
        {
            "email": email.strip().casefold(),
            "tenant_id": tenant_id,
            "papel": "funcionario",
            "expira_em": datetime.now(UTC) + timedelta(hours=horas),
            "criado_em": datetime.now(UTC),
            "uid": None,
        }
    )
    return token


def validar(convite, membro, claims, atuais, agora):
    uid = claims.get("uid") or claims.get("sub")
    if not uid:
        raise HTTPException(401, "Identidade inválida.")
    if not claims.get("email_verified") or not claims.get("email"):
        raise HTTPException(403, "Verifique seu e-mail antes de vincular a empresa.")
    if not convite or convite.get("email") != claims["email"].casefold():
        raise HTTPException(403, "Convite inválido para esta conta.")
    if convite.get("uid") and convite["uid"] != uid:
        raise HTTPException(409, "Convite já utilizado por outra conta.")
    # Retry do mesmo UID permanece recuperável mesmo depois do vencimento.
    if not convite.get("uid") and convite["expira_em"] <= agora:
        raise HTTPException(410, "Convite expirado. Solicite um novo à equipe.")
    tenant = convite["tenant_id"]
    for origem in (claims, atuais, membro or {}):
        if origem.get("tenant_id") and origem["tenant_id"] != tenant:
            raise HTTPException(409, "A conta já está vinculada a outra empresa.")
    if convite.get("papel") != "funcionario":
        raise HTTPException(403, "Convite inválido.")
    return uid, tenant


@firestore.transactional
def reservar(transaction, convite_ref, membro_ref, claims, atuais):
    convite = convite_ref.get(transaction=transaction).to_dict()
    membro = membro_ref.get(transaction=transaction).to_dict()
    uid, tenant = validar(convite, membro, claims, atuais, datetime.now(UTC))
    if not membro:
        transaction.create(
            membro_ref,
            {
                "tenant_id": tenant,
                "papel": "funcionario",
                "criado_em": datetime.now(UTC),
            },
        )
    if not convite.get("uid"):
        transaction.update(convite_ref, {"uid": uid, "resgatado_em": datetime.now(UTC)})
    return tenant


def resgatar(token: str, claims: dict) -> dict:
    uid = claims.get("uid") or claims.get("sub")
    if not uid:
        raise HTTPException(401, "Identidade inválida.")
    if not claims.get("email_verified"):
        raise HTTPException(403, "Verifique seu e-mail antes de vincular a empresa.")
    usuario = auth.get_user(uid)
    atuais = usuario.custom_claims or {}
    db = get_db()
    tenant = reservar(
        db.transaction(),
        db.collection("convites").document(digest(token)),
        db.collection("associacoes").document(uid),
        claims,
        atuais,
    )
    # Associação é durável. Se Auth falhar, repetir o POST reconcilia sem liberar o convite.
    try:
        atuais = auth.get_user(uid).custom_claims or {}
        if atuais.get("tenant_id") and atuais["tenant_id"] != tenant:
            raise HTTPException(409, "A conta já está vinculada a outra empresa.")
        auth.set_custom_user_claims(uid, {**atuais, "tenant_id": tenant, "papel": "funcionario"})
    except HTTPException:
        raise
    except Exception as erro:
        raise HTTPException(
            503, "Vínculo reservado. Tente novamente para concluir o acesso."
        ) from erro
    return {"tenant_id": tenant, "papel": "funcionario"}
