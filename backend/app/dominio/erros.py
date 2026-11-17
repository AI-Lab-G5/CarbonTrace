"""Erros do dominio.

Cada um carrega os dados que a mensagem ao usuario precisa. A rota
traduz para HTTP; o dominio nao sabe o que e um codigo de status.
"""


class ErroDeDominio(Exception):
    """Base dos erros de regra de negocio."""

    def mensagem(self) -> str:
        raise NotImplementedError


class QuantidadeInvalida(ErroDeDominio):
    """Quantidade fora do que o dominio aceita."""

    def __init__(self, motivo: str) -> None:
        self.motivo = motivo
        super().__init__(motivo)

    def mensagem(self) -> str:
        return self.motivo


class QuantidadeAcimaDoTeto(ErroDeDominio):
    """Quantidade acima do teto plausivel da fonte.

    O teto existe para pegar erro de digitacao -- um zero a mais em
    100000 passa despercebido num relatorio e so aparece na auditoria.
    """

    def __init__(self, quantidade, teto, unidade: str) -> None:
        self.quantidade = quantidade
        self.teto = teto
        self.unidade = unidade
        super().__init__(self.mensagem())

    def mensagem(self) -> str:
        return (
            f"Quantidade {self.quantidade} {self.unidade} acima do teto de "
            f"{self.teto} {self.unidade} para esta fonte. Confira se a unidade "
            "e o valor estao corretos."
        )


class UnidadeIncompativel(ErroDeDominio):
    """Unidade informada nao converte para a unidade do fator."""

    def __init__(
        self,
        unidade_informada: str,
        unidade_base: str,
        aceitas: list[str],
    ) -> None:
        self.unidade_informada = unidade_informada
        self.unidade_base = unidade_base
        self.aceitas = aceitas
        super().__init__(self.mensagem())

    def mensagem(self) -> str:
        return (
            f"Unidade {self.unidade_informada!r} nao serve para esta fonte. "
            f"Aceitas: {', '.join(self.aceitas)}."
        )


class FatorNaoEncontrado(ErroDeDominio):
    """Nao existe fator publicado para a fonte na competencia pedida."""

    def __init__(self, fonte_id: str, competencia: str) -> None:
        self.fonte_id = fonte_id
        self.competencia = competencia
        super().__init__(self.mensagem())

    def mensagem(self) -> str:
        return (
            f"Nao ha fator vigente para a fonte {self.fonte_id!r} na "
            f"competencia {self.competencia}."
        )


class CompetenciaInvalida(ErroDeDominio):
    """Competencia fora do formato ou do intervalo aceito."""

    def __init__(self, motivo: str) -> None:
        self.motivo = motivo
        super().__init__(motivo)

    def mensagem(self) -> str:
        return self.motivo
