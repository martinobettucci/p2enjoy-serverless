# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
FROM node:24-bookworm-slim@sha256:6042915a8b58012e6699f998ed96bca43ec9d8582447bdb68bc2445d0fafeb79 AS runtime
WORKDIR /runtime
COPY runtime/*.mjs ./
USER 0:0
ENTRYPOINT ["node", "/runtime/validate-supervisor.mjs"]

FROM runtime AS qualification
WORKDIR /fixtures
COPY qualification/package.json qualification/package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY qualification/artifacts ./
