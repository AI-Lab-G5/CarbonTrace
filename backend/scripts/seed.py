"""Carrega o catalogo de fatores e dados de exemplo no emulador.

Uso (com o emulador no ar):

    FIRESTORE_EMULATOR_HOST=127.0.0.1:8080 python scripts/seed.py

Nao roda contra a nuvem por engano: sem FIRESTORE_EMULATOR_HOST o script
recusa. Gravar dado de teste em producao e o tipo de acidente que ninguem
percebe na hora.

Publicar versao de fatores e operacao administrativa, feita por aqui --
nao ha tela nem rota para isso, e o CA-01 dispensa de proposito.
"""

import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

VERSOES = ["fatores-v1.json", "fatores-v2.json"]

UNIDADES_EXEMPLO = [
    {"nome": "Loja Asa Norte", "cidade": "Brasilia", "uf": "DF"},
    {"nome": "Loja Taguatinga", "cidade": "Taguatinga", "uf": "DF"},
    {"nome": "Centro de Distribuicao", "cidade": "Goiania", "uf": "GO"},
]


def _pasta_dados() -> Path:
    """Localiza docs/dados.

    No container o backend e a raiz e docs/ esta montada em /docs; fora
    dele, docs/ fica um nivel acima. Procurar nos dois evita um caminho
    que so funciona em um dos ambientes.
    """
    candidatos = [
        Path("/docs/dados"),
        BACKEND.parent / "docs" / "dados",
        BACKEND / "docs" / "dados",
    ]
    for caminho in candidatos:
        if caminho.is_dir():
            return caminho
    raise FileNotFoundError(
        "Pasta docs/dados nao encontrada. Procurei em:\n  "
        + "\n  ".join(str(c) for c in candidatos)
    )


def main() -> int:
    if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
        print("ERRO: defina FIRESTORE_EMULATOR_HOST antes de rodar o seed.")
        print("Este script nunca deve gravar na nuvem.")
        return 1

    os.environ.setdefault("FIREBASE_PROJECT_ID", "demo-carbontrace")

    from app.db import colecao_do_tenant, colecao_global

    pasta = _pasta_dados()

    for arquivo in VERSOES:
        conjunto = json.loads((pasta / arquivo).read_text(encoding="utf-8"))
        versao = conjunto["versao"]
        colecao_global("fatores").document(versao).set(
            {
                "vigencia_inicio": conjunto["vigencia_inicio"],
                "vigencia_fim": conjunto.get("vigencia_fim"),
                "publicado_em": conjunto["publicado_em"],
                "status": conjunto["status"],
                "fatores": conjunto["fatores"],
            }
        )
        fontes = ", ".join(f["fonte_id"] for f in conjunto["fatores"])
        print(f"Fatores {versao} (vigencia {conjunto['vigencia_inicio']}): {fontes}")

    # Duas empresas de proposito: com uma so, o isolamento entre tenants
    # nunca seria exercitado em desenvolvimento.
    for tenant in ("empresa-a", "empresa-b"):
        existentes = list(colecao_do_tenant(tenant, "unidades").limit(1).stream())
        if existentes:
            print(f"{tenant}: ja tem unidades, nada a fazer.")
            continue
        for unidade in UNIDADES_EXEMPLO:
            colecao_do_tenant(tenant, "unidades").add(unidade)
        print(f"{tenant}: {len(UNIDADES_EXEMPLO)} unidades criadas.")

    print("\nSeed concluido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
