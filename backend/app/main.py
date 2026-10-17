"""CarbonTrace API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import consolidado, fatores, health, registros, unidades

app = FastAPI(
    title="CarbonTrace API",
    version="0.1.0",
    description=(
        "Inventario de emissoes de GEE para redes de varejo e franquias. "
        "Todo dado de cliente vive sob /tenants/{tenantId}/ e o tenant vem "
        "da identidade do chamador, nunca de parametro do cliente."
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
app.include_router(registros.router)
app.include_router(fatores.router)
app.include_router(consolidado.router)
