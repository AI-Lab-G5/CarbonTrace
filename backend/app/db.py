"""Cliente do Firestore.

Quando FIRESTORE_EMULATOR_HOST esta definido, a biblioteca do Google
conecta no emulador automaticamente e nao exige credencial nenhuma.
E por isso que o desenvolvimento local nao gasta cota nem precisa de
chave de conta de servico.
"""

from functools import lru_cache

from google.cloud import firestore

from app.config import settings


@lru_cache(maxsize=1)
def get_db() -> firestore.Client:
    """Devolve o cliente do Firestore, criado uma unica vez."""
    return firestore.Client(project=settings.project_id)


def colecao_do_tenant(tenant_id: str, nome: str):
    """Caminho de uma colecao dentro do escopo de um tenant.

    Todo dado de cliente mora sob /tenants/{tenantId}/. Nenhuma consulta
    da aplicacao le a raiz de uma colecao global de dados de cliente --
    e esse o alicerce do isolamento entre empresas.
    """
    return get_db().collection("tenants").document(tenant_id).collection(nome)


def colecao_global(nome: str):
    """Colecao global, compartilhada e somente leitura para os tenants.

    Hoje so os fatores de emissao, que sao publicos e versionados.
    """
    return get_db().collection(nome)
