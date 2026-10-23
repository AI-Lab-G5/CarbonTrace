import yaml
from pathlib import Path

from app.main import app

spec = app.openapi()

# 1. servers — resolve no-empty-servers
spec["servers"] = [
    {"url": "http://localhost:3001", "description": "Desenvolvimento local"},
    {"url": "https://api.carbontrace.app", "description": "Produção"},
]

# 2. license — resolve o warning info-license
spec["info"]["license"] = {"name": "Proprietary"}

# 3. esquema de autenticação (Firebase ID token enviado como Bearer)
spec.setdefault("components", {}).setdefault("securitySchemes", {})["bearerAuth"] = {
    "type": "http",
    "scheme": "bearer",
    "bearerFormat": "JWT",
    "description": "Firebase ID token obtido no login do frontend.",
}

# 4. security na raiz — as 9 operações herdam, resolvendo security-defined
spec["security"] = [{"bearerAuth": []}]

# 5. /health é público: sobrescreve o herança com lista vazia
spec["paths"]["/health"]["get"]["security"] = []

# 6. 4XX documentados — opcional, elimina o warning operation-4xx-response
for path, item in spec["paths"].items():
    for method, operation in item.items():
        if method not in {"get", "post", "put", "patch", "delete"}:
            continue
        if path == "/health":
            continue
        responses = operation.setdefault("responses", {})
        responses.setdefault("401", {"description": "Token ausente, inválido ou expirado"})
        responses.setdefault("403", {"description": "Usuário sem acesso ao tenant solicitado"})

# 7. grava (mantendo o cabeçalho de aviso)
cabecalho = "# Nao editar a mao -- o contrato segue a implementacao.\n\n"
Path("docs/api/openapi.yaml").write_text(
    cabecalho + yaml.safe_dump(spec, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
