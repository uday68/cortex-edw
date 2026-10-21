# Hardened, lightweight Python 3.12 container for Cortex EDW
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim AS runner

WORKDIR /app

# Run as non-root user UID 10001
RUN useradd -u 10001 -m cortexuser
USER cortexuser

COPY --from=builder /root/.local /home/cortexuser/.local
ENV PATH=/home/cortexuser/.local/bin:$PATH
ENV PYTHONPATH=/app

COPY --chown=cortexuser:cortexuser . .

EXPOSE 8000 8501

CMD ["sh", "-c", "uvicorn cortex.api.server:app --host 0.0.0.0 --port 8000 & streamlit run cortex/ui/dashboard.py --server.port 8501 --server.address 0.0.0.0"]
