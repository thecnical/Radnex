FROM python:3.11-slim

LABEL maintainer="Chandan Pandey <thecnical@users.noreply.github.com>"
LABEL description="Radnex — Autonomous Web Security Reconnaissance and Coding Agent CLI"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV RADNEX_HOME=/root/.radnex

# Install essential system dependencies and Node.js for AntSeed P2P
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    tmux \
    ca-certificates \
    nodejs \
    npm \
    && npm install -g @antseed/cli \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source and install radnex
COPY . .
RUN pip install --no-cache-dir -e . && \
    chmod +x install.sh setup.sh packaging/radnex

ENTRYPOINT ["radnex"]
CMD ["--mode", "cpss"]
