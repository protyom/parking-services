FROM protyom/parking-monitoring:os

WORKDIR /app/
COPY pyproject.toml /app/

RUN uv pip install --system --no-cache-dir -e ".[django]" && \
    uv pip install --system --no-cache-dir uwsgi && \
    uv cache clean
