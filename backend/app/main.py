"""CarbonTrace API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import consolidado, consumos, fontes, health, unidades

app = FastAPI(
    title="CarbonTrace API",
    version="0.2.0",
    description=(
        "Inventario de emissoes de GEE para redes de varejo e franquias.\n\n"
        "Quantidades e fatores trafegam como texto, nao como numero decimal: "
        "o calculo e feito em Decimal do inicio ao fim para que dois recalculos "
        "do mesmo periodo devolvam exatamente o mesmo resultado.\n\n"
        "Todo dado de cliente vive sob /tenants/{tenantId}/ e o tenant vem das "
        "claims do ID token, nunca de parametro do cliente. Apenas /healthz e "
        "/readyz sao publicas."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(unidades.router)
app.include_router(fontes.router)
app.include_router(consumos.router)
app.include_router(consolidado.router)
