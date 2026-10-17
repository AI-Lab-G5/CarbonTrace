"""Carrega os fatores de emissao e dados de exemplo no emulador.

Uso (com o emulador no ar):

    FIRESTORE_EMULATOR_HOST=127.0.0.1:8080 python scripts/seed.py

Nao roda contra a nuvem por engano: se FIRESTORE_EMULATOR_HOST nao estiver
definido, o script recusa. A protecao existe porque gravar dados de teste
em producao e o tipo de acidente que ninguem percebe na hora.
"""

import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

# Rodar "python scripts/seed.py" poe /app/scripts no sys.path, e nao /app --
# entao o pacote "app" nao seria encontrado. Inserir a raiz do backend
# resolve sem exigir que a pessoa lembre de usar "python -m".
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _achar_fatores() -> Path:
    """Localiza o dataset de fatores.

    Dentro do container o backend e a raiz (/app) e a pasta docs/ e montada
    em /docs; fora dele, docs/ fica um nivel acima do backend. Procurar nos
    dois lugares evita um caminho que so funciona em um dos ambientes.
    """
    candidatos = [
        Path("/docs/dados/fatores-v1.json"),
        BACKEND.parent / "docs" / "dados" / "fatores-v1.json",
        BACKEND / "docs" / "dados" / "fatores-v1.json",
    ]
    for caminho in candidatos:
        if caminho.exists():
            return caminho
    raise FileNotFoundError(
        "fatores-v1.json nao encontrado. Procurei em:\n  "
        + "\n  ".join(str(c) for c in candidatos)
    )

UNIDADES_EXEMPLO = [
    {"nome": "Loja Asa Norte", "cidade": "Brasilia", "uf": "DF"},
    {"nome": "Loja Taguatinga", "cidade": "Taguatinga", "uf": "DF"},
    {"nome": "Centro de Distribuicao", "cidade": "Goiania", "uf": "GO"},
]


def main() -> int:
    if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
        print("ERRO: defina FIRESTORE_EMULATOR_HOST antes de rodar o seed.")
        print("Este script nunca deve gravar na nuvem.")
        return 1

    os.environ.setdefault("FIREBASE_PROJECT_ID", "demo-carbontrace")

    from app.db import colecao_do_tenant, colecao_global

    conjunto = json.loads(_achar_fatores().read_text(encoding="utf-8"))
    versao = conjunto["versao"]
    colecao_global("fatores").document(versao).set(
        {
            "vigencia_inicio": conjunto["vigencia_inicio"],
            "publicado_em": conjunto["publicado_em"],
            "fatores": conjunto["fatores"],
        }
    )
    print(f"Fatores {versao}: {len(conjunto['fatores'])} fontes carregadas.")

    # Duas empresas de proposito: com uma so, o isolamento entre tenants
    # nunca seria exercitado em desenvolvimento.
    for tenant in ("empresa-a", "empresa-b"):
        for unidade in UNIDADES_EXEMPLO:
            colecao_do_tenant(tenant, "unidades").add(unidade)
        print(f"{tenant}: {len(UNIDADES_EXEMPLO)} unidades criadas.")

    print("\nSeed concluido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
