"""Sondas públicas: disponibilidade, falha e recuperação da dependência."""

from unittest.mock import Mock


def test_healthz_independe_do_firestore(cliente, monkeypatch):
    obter_banco = Mock(side_effect=RuntimeError("Banco indisponível"))
    monkeypatch.setattr("app.db.get_db", obter_banco)

    resposta = cliente.get("/healthz")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"
    obter_banco.assert_not_called()


def test_readyz_confere_firestore_saudavel(cliente, monkeypatch):
    banco = Mock()
    leitura = banco.collection.return_value.limit.return_value.get
    leitura.return_value = []
    monkeypatch.setattr("app.db.get_db", lambda: banco)

    resposta = cliente.get("/readyz")

    assert resposta.status_code == 200
    assert resposta.json() == {
        "status": "pronto",
        "dependencia": "firestore",
    }
    leitura.assert_called_once()


def test_readyz_falha_sem_expor_detalhes_e_recupera(cliente, monkeypatch):
    banco = Mock()
    leitura = banco.collection.return_value.limit.return_value.get
    leitura.side_effect = RuntimeError("detalhe-interno-confidencial")
    monkeypatch.setattr("app.db.get_db", lambda: banco)

    resposta = cliente.get("/readyz")

    assert resposta.status_code == 503
    assert resposta.json() == {
        "status": "indisponivel",
        "dependencia": "firestore",
    }
    assert "detalhe-interno-confidencial" not in resposta.text

    # A falha da dependência não derruba a disponibilidade do processo.
    assert cliente.get("/healthz").status_code == 200

    # Quando o banco volta, a prontidão se recupera.
    leitura.side_effect = None
    leitura.return_value = []

    recuperada = cliente.get("/readyz")
    assert recuperada.status_code == 200
    assert recuperada.json()["status"] == "pronto"
