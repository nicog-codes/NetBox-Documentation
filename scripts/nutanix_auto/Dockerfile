FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-requests python3-lxml python3-pil \
    ca-certificates libvisio-tools librsvg2-bin \
    && rm -rf /var/lib/apt/lists/*
COPY pipeline.py /app/pipeline.py
COPY import_nutanix_elevation_images.py /app/import_nutanix_elevation_images.py
WORKDIR /app
ENTRYPOINT ["python3", "/app/pipeline.py"]
