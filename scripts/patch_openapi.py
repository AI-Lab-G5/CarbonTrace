"""Pós-processa docs/api/openapi.yaml para satisfazer o lint do Redocly."""
from pathlib import Path

import yaml

SPEC = Path("docs/api/openapi.yaml")
METODOS = {"get", "post", "put", "patch", "delete", "options", "head"}
ROTAS_PUBLICAS = {"/health"}

spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))

# 1. servers -> resolve no-empty-servers
spec["servers"] = [
    {"url": "http://localhost:3001", "description": "Desenvolvimento local"},
    {"url": "https://api.carbontrace.app", "description": "Produção"},
]

# 2. license -> resolve o warning info-license
spec.setdefault("info", {})["license"] = {"name": "Proprietary"}

# 3. esquema de autenticação
spec.setdefault("components", {}).setdefault("securitySchemes", {})["bearerAuth"] = {
    "type": "http",
    "scheme": "bearer",
    "bearerFormat": "JWT",
    "description": "Firebase ID token obtido no login do frontend.",
}

# 4. security na raiz -> as 9 operações herdam, resolve security-defined
spec["security"] = [{"bearerAuth": []}]

for rota, item in spec.get("paths", {}).items():
    for metodo, operacao in item.items():
        if metodo not in METODOS:
            continue
        if rota in ROTAS_PUBLICAS:
            operacao["security"] = []  # exceção explícita: rota pública
            continue
        respostas = operacao.setdefault("responses", {})
        respostas.setdefault("401", {"description": "Token ausente, inválido ou expirado"})
        respostas.setdefault("403", {"description": "Usuário sem acesso ao tenant"})

CABECALHO = "# Nao editar a mao -- o contrato segue a implementacao.\n\n"
SPEC.write_text(
    CABECALHO + yaml.safe_dump(spec, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
print(f"OK: {SPEC} normalizado")
