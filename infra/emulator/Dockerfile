# Emulator Suite do Firebase em container.
#
# Containerizar em vez de pedir instalacao local resolve o requisito do
# Checkpoint 1: "um integrante clona o repositorio num computador limpo e
# tudo sobe". Sem isso, cada pessoa precisaria instalar Node, a CLI do
# Firebase e um JDK na mao -- e o emulador do Firestore roda em Java.

FROM node:20-alpine

RUN apk add --no-cache openjdk17-jre-headless bash netcat-openbsd \
    && npm install -g firebase-tools@13

WORKDIR /srv

EXPOSE 4000 8080 9099

CMD ["firebase", "emulators:start", \
     "--project", "demo-carbontrace", \
     "--import", "/srv/data", \
     "--export-on-exit", "/srv/data"]
