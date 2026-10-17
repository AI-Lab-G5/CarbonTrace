"""Configuracao lida do ambiente. Nenhum segredo fica no codigo."""

import os


class Settings:
    """Configuracao da aplicacao.

    Os valores vem do ambiente. O .env.example documenta cada um;
    o .env real nunca e versionado.
    """

    def __init__(self) -> None:
        self.project_id: str = os.environ.get("FIREBASE_PROJECT_ID", "demo-carbontrace")
        self.firestore_emulator_host: str | None = os.environ.get("FIRESTORE_EMULATOR_HOST")
        self.auth_emulator_host: str | None = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST")

        # "emulator" aceita um cabecalho de identidade sem assinatura, para
        # desenvolvimento local. "firebase" exige um ID token valido.
        # Qualquer valor diferente de "emulator" e tratado como "firebase".
        self.auth_mode: str = os.environ.get("AUTH_MODE", "emulator")

        self.cors_origins: list[str] = [
            origem.strip()
            for origem in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
            if origem.strip()
        ]

    @property
    def usando_emulador(self) -> bool:
        return self.firestore_emulator_host is not None


settings = Settings()
