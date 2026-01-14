# Dockerfile para Shortsmaker Worker

FROM python:3.11-slim

# Metadados
LABEL maintainer="your-email@example.com"
LABEL description="Shortsmaker Worker - Async video processing worker"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app/ .

# Criar usuário não-root
RUN useradd -m -u 1000 worker && \
    chown -R worker:worker /app

# Mudar para usuário não-root
USER worker

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "from infra.config.settings import get_settings; get_settings()" || exit 1

# Comando de execução
CMD ["python", "main.py"]
