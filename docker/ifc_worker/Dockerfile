# Pinned linux/arm64 official Python 3.12.16 slim Debian bookworm image.
# Manifest digest inspected 2026-11-07; never substitute mutable python:latest.
FROM docker.io/library/python:3.12-slim-bookworm@sha256:df540bfd30bd380e89a349611ce42aa67bcb542d58c047706616eb6ba2f86a1b
LABEL org.opencontainers.image.title="bim-markup-bench isolated IFC4X3 worker" \
      org.opencontainers.image.description="Experimental native IFC Python 3.12 worker with pinned hashed wheel dependencies; no live model provider or GT scorer" \
      org.opencontainers.image.version="0.1.0"
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONNOUSERSITE=1 \
    PIP_NO_CACHE_DIR=1     OPENBLAS_NUM_THREADS=1     OMP_NUM_THREADS=1     MKL_NUM_THREADS=1     NUMEXPR_NUM_THREADS=1
WORKDIR /opt/ifc_worker
COPY docker/ifc_worker/requirements.lock /opt/ifc_worker/requirements.lock
RUN python -m pip install --disable-pip-version-check --no-cache-dir \
    --require-hashes --only-binary=:all: -r /opt/ifc_worker/requirements.lock \
    && python -c "import ifcopenshell,numpy,shapely; assert ifcopenshell.version == '0.8.4.post1'"
COPY docker/ifc_worker/trusted_probe.py /opt/ifc_worker/trusted_probe.py
COPY docker/ifc_worker/run_candidate.py /opt/ifc_worker/run_candidate.py
USER 65534:65534
ENTRYPOINT ["/usr/local/bin/python3"]
CMD ["/opt/ifc_worker/trusted_probe.py"]
