# @spec docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
FROM node:24-bookworm-slim@sha256:6042915a8b58012e6699f998ed96bca43ec9d8582447bdb68bc2445d0fafeb79
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund && npm cache clean --force
COPY --chown=node:node serverless.yml ./
COPY --chown=node:node src ./src
COPY --chown=node:node runner ./runner
COPY --chown=node:node tests ./tests
RUN mkdir -p /app/.state/data /app/.state/cache /reports && chown -R node:node /app/.state /reports
USER node
EXPOSE 8080
CMD ["node", "runner/server.cjs"]
