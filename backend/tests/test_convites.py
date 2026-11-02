from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.services.convites import validar


def dados():
    return (
        {
            "email": "ana@example.test",
            "tenant_id": "a",
            "papel": "funcionario",
            "expira_em": datetime.now(UTC) + timedelta(hours=1),
            "uid": None,
        },
        {"uid": "ana", "email": "ana@example.test", "email_verified": True},
    )


@pytest.mark.parametrize(
    "cenario,status",
    [
        ("invalido", 403),
        ("expirado", 410),
        ("email", 403),
        ("nao_verificado", 403),
        ("uid_ausente", 401),
        ("outro_uid", 409),
        ("outra_empresa", 409),
        ("claim_conflitante", 409),
        ("papel", 403),
    ],
)
def test_recusas(cenario, status):
    convite, claims = dados()
    membro = None
    atuais = {}
    if cenario == "invalido":
        convite = None
    elif cenario == "expirado":
        convite["expira_em"] = datetime.now(UTC) - timedelta(seconds=1)
    elif cenario == "email":
        claims["email"] = "outra@example.test"
    elif cenario == "nao_verificado":
        claims["email_verified"] = False
    elif cenario == "uid_ausente":
        del claims["uid"]
    elif cenario == "outro_uid":
        convite["uid"] = "outro"
    elif cenario == "outra_empresa":
        membro = {"tenant_id": "b"}
    elif cenario == "claim_conflitante":
        atuais = {"tenant_id": "b"}
    elif cenario == "papel":
        convite["papel"] = "admin"
    with pytest.raises(HTTPException) as erro:
        validar(convite, membro, claims, atuais, datetime.now(UTC))
    assert erro.value.status_code == status


def test_retry_mesmo_uid_apos_expiracao():
    convite, claims = dados()
    convite.update(uid="ana", expira_em=datetime.now(UTC) - timedelta(days=1))
    assert validar(convite, {"tenant_id": "a"}, claims, {}, datetime.now(UTC)) == ("ana", "a")


def test_falha_claims_preserva_reserva_e_retry_reconcilia(monkeypatch):
    from app.services import convites

    _, claims = dados()
    reserva = Mock(return_value="a")
    monkeypatch.setattr(convites, "reservar", reserva)
    monkeypatch.setattr(convites, "get_db", Mock())
    monkeypatch.setattr(
        convites.auth, "get_user", Mock(return_value=Mock(custom_claims={"extra": 1}))
    )
    aplicar = Mock(side_effect=[RuntimeError("offline"), None])
    monkeypatch.setattr(convites.auth, "set_custom_user_claims", aplicar)
    with pytest.raises(HTTPException) as erro:
        convites.resgatar("segredo", claims)
    assert erro.value.status_code == 503
    assert convites.resgatar("segredo", claims)["tenant_id"] == "a"
    aplicar.assert_called_with("ana", {"extra": 1, "tenant_id": "a", "papel": "funcionario"})
    assert reserva.call_count == 2


def test_onboarding_requer_token(cliente):
    assert cliente.post("/v1/onboarding/resgate", json={"convite": "x" * 43}).status_code == 401


def test_acesso_sem_empresa_bloqueado(sem_empresa):
    for rota in ["/v1/onboarding/acesso", "/v1/unidades", "/v1/consumos"]:
        assert sem_empresa.get(rota).status_code == 403
