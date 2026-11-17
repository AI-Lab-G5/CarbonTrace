"""Admin local: gera segredo uma única vez, em arquivo privado, nunca em logs."""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.convites import criar_convite  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--empresa", required=True)
    parser.add_argument("--horas", type=int, default=24)
    parser.add_argument("--saida", required=True, help="Arquivo privado fora do repositório")
    args = parser.parse_args()
    if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
        parser.error("Este script é restrito ao emulador local.")
    destino = Path(args.saida).resolve()
    if destino.is_relative_to(Path(__file__).resolve().parents[2]):
        parser.error("Use um arquivo fora do repositório.")
    # Não sobrescreve arquivos; permissões POSIX restritas no container.
    fd = os.open(destino, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as arquivo:
        arquivo.write(criar_convite(args.email, args.empresa, args.horas))
    print("Convite salvo no arquivo privado informado. Compartilhe apenas com o destinatário.")


if __name__ == "__main__":
    main()
