FROM node:20-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && mkdir -p /opt/java \
    && curl -fsSL "https://api.adoptium.net/v3/binary/latest/21/ga/linux/x64/jre/hotspot/normal/eclipse" \
       -o /tmp/jre.tar.gz \
    && tar -xzf /tmp/jre.tar.gz -C /opt/java --strip-components=1 \
    && rm /tmp/jre.tar.gz \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g firebase-tools

ENV JAVA_HOME=/opt/java
ENV PATH="$JAVA_HOME/bin:$PATH"

WORKDIR /firebase

CMD ["firebase", "emulators:start", "--only", "auth,firestore"]
