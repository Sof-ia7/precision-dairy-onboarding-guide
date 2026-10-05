# Processing container (Container 1): runs Chapter 3 -> Chapter 4 -> PostgreSQL load.
#
# Build (anywhere):
#   podman build -t precision-dairy-pipeline:dev .
# Build on campus/VPN through the Geddes Docker Hub cache (avoids Docker Hub rate limits):
#   podman build --build-arg BASE=geddes-registry.rcac.purdue.edu/docker-hub-cache/library/python:3.11-slim \
#     -t precision-dairy-pipeline:dev .

ARG BASE=python:3.11-slim

# ---- builder: install dependencies into a virtualenv ----
FROM ${BASE} AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ---- runtime: copy the virtualenv and the scripts only ----
FROM ${BASE} AS runtime
LABEL org.opencontainers.image.title="precision-dairy-pipeline" \
      org.opencontainers.image.description="Purdue Precision Dairy: PASDE data -> herd & feed tables -> PostgreSQL for Grafana"

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY src/ /app/

# Non-root user (Kubernetes clusters commonly forbid root containers).
# Mount points: /data (read-only inputs) and /outputs (CSV backups).
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin app \
 && mkdir -p /data /outputs/chapter3 /outputs/chapter4 \
 && chown -R app:app /outputs
USER 10001

CMD ["python", "/app/run_all.py"]
