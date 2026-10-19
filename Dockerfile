FROM python:3.11-slim-bookworm

LABEL maintainer="Chandan Pandey <thecnical@users.noreply.github.com>"
LABEL description="Radnex — Autonomous Web Security Reconnaissance and Coding Agent CLI"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV RADNEX_HOME=/root/.radnex

# Install system dependencies, Node.js and AntSeed P2P CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    tmux \
    ca-certificates \
    nodejs \
    npm \
    && (npm install -g @antseed/cli || true) \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy repo source
COPY . .

# Install dependencies and radnex
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    chmod +x install.sh setup.sh packaging/radnex

ENTRYPOINT ["radnex"]
CMD ["--mode", "cpss"]
