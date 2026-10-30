# syntax=docker/dockerfile:1
ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}
WORKDIR /app
COPY requirements.txt .
# optional build secret 'ca' = extra CA bundle for TLS-intercepting proxies (not needed normally)
RUN --mount=type=secret,id=ca,required=false \
    if [ -f /run/secrets/ca ]; then export PIP_CERT=/run/secrets/ca; fi; \
    pip install --no-cache-dir -r requirements.txt
COPY ordering ./ordering
# keys and data live in volumes, never in the image
VOLUME ["/app/keys", "/app/data"]
ENTRYPOINT ["python", "-m", "ordering"]
CMD ["run"]
