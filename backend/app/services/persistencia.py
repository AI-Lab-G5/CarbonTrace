"""Traducao entre o dominio e o documento gravado no Firestore.

Todo numero vai para o banco como texto. O Firestore armazena numero
como double de 64 bits -- gravar Decimal ali o converteria em float e
jogaria fora a exatidao que o dominio inteiro preserva.

Isolar a conversao aqui mantem rota e dominio livres desse detalhe.
"""

from app.dominio.calculo import Resultado
from app.dominio.numeros import como_texto, para_decimal
from app.models import Consumo, ConsumoEntrada


def documento_de_consumo(entrada: ConsumoEntrada, resultado: Resultado) -> dict:
    """Monta o documento a gravar.

    Guarda a versao e o valor do fator junto do resultado. E a redundancia
    que permite recalcular sem depender de o catalogo continuar igual.
    """
    return {
        "unidade_id": entrada.unidade_id,
        "competencia": entrada.competencia,
        "fonte_id": entrada.fonte_id,
        "quantidade_informada": como_texto(resultado.quantidade_informada),
        "unidade_informada": resultado.unidade_informada,
        "quantidade_convertida": como_texto(resultado.quantidade_convertida),
        "unidade_base": resultado.unidade_base,
        "fator_versao": resultado.fator_versao,
        "fator_valor": como_texto(resultado.fator_valor),
        "emissao_kg_co2e": como_texto(resultado.emissao_kg_co2e),
        "escopo": resultado.escopo,
    }


def consumo_de_documento(doc_id: str, dados: dict) -> Consumo:
    """Le o documento de volta, com os numeros em Decimal."""
    return Consumo(
        id=doc_id,
        unidade_id=dados["unidade_id"],
        competencia=dados["competencia"],
        fonte_id=dados["fonte_id"],
        quantidade_informada=para_decimal(
            dados["quantidade_informada"], campo="quantidade_informada"
        ),
        unidade_informada=dados["unidade_informada"],
        quantidade_convertida=para_decimal(
            dados["quantidade_convertida"], campo="quantidade_convertida"
        ),
        unidade_base=dados["unidade_base"],
        fator_versao=dados["fator_versao"],
        fator_valor=para_decimal(dados["fator_valor"], campo="fator_valor"),
        emissao_kg_co2e=para_decimal(
            dados["emissao_kg_co2e"], campo="emissao_kg_co2e"
        ),
        escopo=dados["escopo"],
    )


def resultado_de_consumo(consumo: Consumo) -> Resultado:
    """Reconstroi o resultado do dominio a partir do que foi gravado.

    Usado pelo recalculo: o dominio so sabe lidar com Resultado, e o
    que vem do banco e um Consumo.
    """
    return Resultado(
        quantidade_informada=consumo.quantidade_informada,
        unidade_informada=consumo.unidade_informada,
        quantidade_convertida=consumo.quantidade_convertida,
        unidade_base=consumo.unidade_base,
        fator_versao=consumo.fator_versao,
        fator_valor=consumo.fator_valor,
        emissao_kg_co2e=consumo.emissao_kg_co2e,
        escopo=consumo.escopo,
    )
