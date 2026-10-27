"""Firestore em memoria, para os testes de ponta a ponta rodarem sempre.

Por que existe
--------------
Os testes de fluxo e de isolamento precisam de dado gravado: "barrar o
acesso ao consumo da empresa A" so prova alguma coisa se o consumo
existir. Ate aqui eles dependiam do emulador, e eram pulados quando ele
nao estava no ar -- ou seja, nunca rodavam na pipeline. Teste que so
roda na maquina de quem escreveu nao protege ninguem.

Este dublê implementa o pedaco estreito da API do Firestore que a
aplicacao realmente usa, e nada alem: colecao, documento, set, get,
stream, where com igualdade, add e limit. Com ele, o mesmo arquivo de
teste roda nos dois modos -- contra o emulador quando
FIRESTORE_EMULATOR_HOST esta definido, contra memoria quando nao.

O que ele NAO prova
-------------------
Regras de seguranca do Firestore, indices compostos, transacoes,
concorrencia e o comportamento real de tipos na serializacao. Isso
continua sendo trabalho do emulador, na issue #24 do QA. O que o dublê
garante e que a nossa logica -- caminho por tenant, idempotencia pela
chave natural, Decimal indo e voltando como texto -- esta exercitada em
toda execucao da suite.

Deliberadamente guarda os valores como foram passados, sem converter
nada: se algum dia alguem gravar um float, o teste de serializacao
enxerga o float, e nao uma versao higienizada dele.
"""

from __future__ import annotations

import copy
import uuid
from collections.abc import Iterator
from typing import Any


class _Snapshot:
    """Equivalente de DocumentSnapshot, so com o que as rotas leem."""

    def __init__(self, doc_id: str, dados: dict[str, Any] | None) -> None:
        self.id = doc_id
        self._dados = dados

    @property
    def exists(self) -> bool:
        return self._dados is not None

    def to_dict(self) -> dict[str, Any] | None:
        # Copia: quem le nao deve conseguir alterar o "banco" sem gravar.
        return copy.deepcopy(self._dados) if self._dados is not None else None


class _DocumentRef:
    def __init__(self, banco: _Banco, caminho: str, doc_id: str) -> None:
        self._banco = banco
        self._caminho = caminho
        self.id = doc_id

    def set(self, dados: dict[str, Any]) -> None:
        self._banco.gravar(self._caminho, self.id, dados)

    def get(self) -> _Snapshot:
        return _Snapshot(self.id, self._banco.ler(self._caminho, self.id))

    def delete(self) -> None:
        self._banco.apagar(self._caminho, self.id)

    def collection(self, nome: str) -> _Collection:
        return _Collection(self._banco, f"{self._caminho}/{self.id}/{nome}")


class _Query:
    """Consulta acumulativa: cada where devolve uma nova, como no SDK."""

    def __init__(
        self,
        banco: _Banco,
        caminho: str,
        filtros: list[tuple[str, str, Any]] | None = None,
        limite: int | None = None,
        depois_de: str | None = None,
    ) -> None:
        self._banco = banco
        self._caminho = caminho
        self._filtros = filtros or []
        self._limite = limite
        self._depois_de = depois_de

    def _derivada(self, **mudancas) -> _Query:
        base = {
            "filtros": self._filtros,
            "limite": self._limite,
            "depois_de": self._depois_de,
        }
        return _Query(self._banco, self._caminho, **{**base, **mudancas})

    def where(self, filter: Any = None, **_: Any) -> _Query:  # noqa: A002
        """So igualdade: e o unico operador que a aplicacao usa hoje.

        Qualquer outro levanta, em vez de silenciosamente nao filtrar --
        um filtro ignorado faria um teste de isolamento passar por
        engano, que e exatamente o erro mais caro aqui.
        """
        if filter is None:
            raise TypeError("Use where(filter=FieldFilter(...)).")
        if filter.op_string != "==":
            raise NotImplementedError(
                f"O duble so implementa '==', nao '{filter.op_string}'. "
                "Se a aplicacao passou a usar outro operador, estenda aqui."
            )
        novos = [*self._filtros, (filter.field_path, "==", filter.value)]
        return self._derivada(filtros=novos)

    def limit(self, quantidade: int) -> _Query:
        return self._derivada(limite=quantidade)

    def order_by(self, campo: str) -> _Query:
        """Só por '__name__'.

        O duble ja devolve tudo ordenado por id, entao ordenar por id e
        um no-op. Qualquer outro campo levanta, em vez de devolver uma
        ordem errada que o teste aceitaria sem perceber.
        """
        if campo != "__name__":
            raise NotImplementedError(
                f"O duble so ordena por '__name__', nao por '{campo}'."
            )
        return self._derivada()

    def start_after(self, ancora: _Snapshot) -> _Query:
        return self._derivada(depois_de=ancora.id)

    def stream(self) -> Iterator[_Snapshot]:
        achados = []
        for doc_id, dados in sorted(self._banco.colecao(self._caminho).items()):
            if self._depois_de is not None and doc_id <= self._depois_de:
                continue
            if all(dados.get(campo) == valor for campo, _, valor in self._filtros):
                achados.append(_Snapshot(doc_id, dados))
        if self._limite is not None:
            achados = achados[: self._limite]
        return iter(achados)


class _Collection(_Query):
    def __init__(self, banco: _Banco, caminho: str) -> None:
        super().__init__(banco, caminho)

    def document(self, doc_id: str | None = None) -> _DocumentRef:
        return _DocumentRef(self._banco, self._caminho, doc_id or uuid.uuid4().hex)

    def add(self, dados: dict[str, Any]) -> tuple[None, _DocumentRef]:
        ref = self.document()
        ref.set(dados)
        return (None, ref)


class _Banco:
    """Armazenamento: caminho da colecao -> id do documento -> dados."""

    def __init__(self) -> None:
        self._dados: dict[str, dict[str, dict[str, Any]]] = {}

    def colecao(self, caminho: str) -> dict[str, dict[str, Any]]:
        return self._dados.setdefault(caminho, {})

    def gravar(self, caminho: str, doc_id: str, dados: dict[str, Any]) -> None:
        self.colecao(caminho)[doc_id] = copy.deepcopy(dados)

    def ler(self, caminho: str, doc_id: str) -> dict[str, Any] | None:
        return self.colecao(caminho).get(doc_id)

    def apagar(self, caminho: str, doc_id: str) -> None:
        self.colecao(caminho).pop(doc_id, None)


class ClienteFake:
    """Substituto de firestore.Client."""

    def __init__(self) -> None:
        self._banco = _Banco()

    def collection(self, nome: str) -> _Collection:
        return _Collection(self._banco, nome)
