FROM mcr.microsoft.com/devcontainers/python:3.11

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    vim \
    inetutils-ping \
    telnet \
    curl \
    gcc \
    python3-dev \
    python3-venv && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

# Install project requirements globally in the container
COPY app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
