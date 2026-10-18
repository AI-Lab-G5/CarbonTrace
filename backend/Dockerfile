FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# requirements.txt vem antes do codigo para aproveitar o cache de camadas:
# alterar um arquivo .py nao refaz a instalacao das dependencias.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuario sem privilegios ja no ambiente de desenvolvimento. Nao custa nada
# agora e evita a descoberta tardia de que algo so funcionava como root.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# 0.0.0.0 e obrigatorio: dentro do container, 127.0.0.1 so responde a ele
# mesmo e a porta publicada no host nao alcanca nada.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
