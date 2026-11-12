FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends nginx openssl && rm -rf /var/lib/apt/lists/*
COPY --from=frontend /usr/local/bin/node /usr/local/bin/node
WORKDIR /app
COPY backend/requirements.lock.txt /app/backend/requirements.lock.txt
RUN pip install --no-cache-dir -r backend/requirements.lock.txt
COPY backend/ /app/backend/
COPY data/ /app/data/
COPY --from=frontend /build /app/frontend
COPY deploy/ /app/deploy/
ENV PYTHONDONTWRITEBYTECODE=1 NEXT_TELEMETRY_DISABLED=1 GATEKEEPER_DATA_DIR=/var/data
EXPOSE 10000
CMD ["bash", "/app/deploy/start.sh"]
