# syntax=docker/dockerfile:1
FROM ghcr.io/paperclipai/paperclip@sha256:de762433b50d56ed9180fef96a13fa236b37856c5c7a7718e8f19afe3d1e8670 AS paperclip-upstream
FROM python:3.14-slim-trixie@sha256:f85c5697265c178cc6887276c55fe16cf3d14ca35c3df6a5eab3b360534a55d2 AS runtime
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    pip install --no-cache-dir uv==0.12.3 \
    && apt-get update && apt-get install -y --no-install-recommends tini gosu git curl ripgrep jq libreoffice-calc \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 node && useradd --uid 1000 --gid 1000 --home-dir /paperclip node
WORKDIR /opt/hermes
# Source checkout is required by Hermes; wheels are intentionally unsupported upstream.
RUN --mount=type=bind,source=vendor/hermes-agent,target=/source-hermes \
    --mount=type=secret,id=proxy_ca \
    cp -a /source-hermes/. /opt/hermes/ \
    && if [ -f /run/secrets/proxy_ca ]; then export SSL_CERT_FILE=/run/secrets/proxy_ca; fi; \
    UV_PROJECT_ENVIRONMENT=/opt/hermes/.venv uv sync --frozen --no-dev --python /usr/local/bin/python3 \
    && rm -rf /root/.cache/uv
WORKDIR /opt/ares
RUN --mount=type=bind,source=.,target=/source-ares \
    --mount=type=secret,id=proxy_ca \
    cp /source-ares/pyproject.toml /source-ares/uv.lock /opt/ares/ \
    && cp -a /source-ares/src /source-ares/config /source-ares/agents /source-ares/skills /source-ares/templates /source-ares/docs /opt/ares/ \
    && cp -a /source-ares/vendor/paperclip/skills /opt/ares/upstream-paperclip-skills \
    && cp /source-ares/docker/entrypoint.sh /usr/local/bin/ares-entrypoint \
    && cp /source-ares/docker/hermes-launcher.sh /usr/local/bin/ares-hermes \
    && if [ -f /run/secrets/proxy_ca ]; then export SSL_CERT_FILE=/run/secrets/proxy_ca; fi; \
    uv sync --frozen --no-dev --no-editable --python /usr/local/bin/python3 \
    && rm -rf /root/.cache/uv \
    && chmod 755 /usr/local/bin/ares-entrypoint /usr/local/bin/ares-hermes \
    && ln -s /opt/ares/.venv/bin/ares /usr/local/bin/ares \
    && mkdir -p /data /paperclip && chown node:node /data /paperclip
# Keep upstream compiled code and Node; omit unrelated provider CLIs from its 5GB image.
RUN --mount=from=paperclip-upstream,source=/,target=/upstream \
    cp -a /upstream/app /app \
    && cp /upstream/usr/local/bin/node /usr/local/bin/node \
    && chmod -R a+rX /opt/ares /opt/hermes /app \
    && chown -R node:node /app
ENV PATH="/opt/ares/.venv/bin:/opt/hermes/.venv/bin:${PATH}" \
    ARES_ROOT=/opt/ares ARES_DATA=/data \
    HERMES_HOME=/data/hermes HERMES_PYTHON=/opt/hermes/.venv/bin/python \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/paperclip
WORKDIR /app
ENTRYPOINT ["tini", "--", "/usr/local/bin/ares-entrypoint"]
CMD ["node", "--import", "/app/server/node_modules/tsx/dist/loader.mjs", "/app/server/dist/index.js"]
