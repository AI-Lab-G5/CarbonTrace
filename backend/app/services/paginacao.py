"""Paginacao por cursor das listagens.

Nenhuma rota de lista devolve um numero ilimitado de documentos. Uma
rede com duas dezenas de lojas e dois anos de historico passa de dez mil
lancamentos; sem limite, a primeira chamada paga a leitura de todos eles
no Firestore e entrega ao navegador um JSON que ele nao consegue montar.

Por cursor e nao por numero de pagina
-------------------------------------
"Pagina 3" pressupoe que o conjunto nao muda entre uma chamada e outra.
Ele muda: alguem lanca um consumo enquanto outra pessoa navega, e a
partir dali toda pagina seguinte repete ou pula um item. O cursor marca
*onde parou*, nao *quantos pulou*, e por isso nao sofre disso. E e
tambem o que o Firestore faz bem: offset cobra a leitura dos documentos
que ele descarta.
"""

from fastapi import HTTPException, status

LIMITE_PADRAO = 50
LIMITE_MAXIMO = 200


def fatiar(colecao, consulta, cursor: str | None, limite: int):
    """Devolve (documentos da pagina, cursor da proxima ou None).

    `colecao` e a colecao base, usada para resolver o cursor; `consulta`
    e ela ja com os filtros aplicados. Sao parametros separados porque
    o cursor e um documento, e nao um documento filtrado.
    """
    consulta = consulta.order_by("__name__").limit(limite + 1)

    if cursor:
        ancora = colecao.document(cursor).get()
        if not ancora.exists:
            # Cursor de um documento apagado, ou de outra empresa. Nos
            # dois casos continuar daria uma pagina silenciosamente
            # errada; melhor dizer que o cursor nao serve.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cursor invalido ou expirado. Recomece a listagem.",
            )
        consulta = consulta.start_after(ancora)

    # Um a mais do que o pedido: e assim que se sabe se ha proxima
    # pagina sem devolver um cursor que leva a uma pagina vazia.
    documentos = list(consulta.stream())
    tem_proxima = len(documentos) > limite
    documentos = documentos[:limite]

    proximo = documentos[-1].id if (tem_proxima and documentos) else None
    return documentos, proximo
