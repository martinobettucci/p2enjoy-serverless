# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#outil-et-manifeste
FROM python:3.14-slim@sha256:af8a5aa14780025dbfbcfbc81bd8a91ebd87711dd5b0f48ed71090949dd7cb1d AS cli
WORKDIR /app
COPY adapter/requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir --disable-pip-version-check --require-hashes -r requirements.txt
COPY adapter/*.py ./adapter/
ENTRYPOINT ["python", "-B", "-m", "adapter"]

FROM cli AS qualification
COPY e2e/adapter.py e2e/adapter-deploy-public.py ./e2e/
COPY qualification/serverless.platform.yml qualification/package.json ./qualification/
COPY qualification/src ./qualification/src/
ENTRYPOINT ["python", "-B", "/app/e2e/adapter.py"]
