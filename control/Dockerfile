# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md | docs/PLATFORM_DEV.md
FROM node:24-bookworm-slim@sha256:6042915a8b58012e6699f998ed96bca43ec9d8582447bdb68bc2445d0fafeb79 AS console
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY web ./
RUN npm run build

FROM python:3.14-slim@sha256:af8a5aa14780025dbfbcfbc81bd8a91ebd87711dd5b0f48ed71090949dd7cb1d
WORKDIR /app
COPY control/requirements.txt ./
RUN python -m pip install --no-cache-dir --disable-pip-version-check --require-hashes -r requirements.txt
COPY control/app ./app
COPY control/migrations ./migrations
COPY --from=console /web/dist ./web
EXPOSE 18090
CMD ["python", "-B", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "18090", "--workers", "1", "--no-access-log", "--no-proxy-headers"]
