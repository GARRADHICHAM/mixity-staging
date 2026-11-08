# ===== builder step =====
FROM python:3.10.14-bullseye AS builder

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBCONF_NOWARNINGS=yes
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Paris

# Debian Bullseye is EOL: its packages now live on archive.debian.org
RUN for f in /etc/apt/sources.list /etc/apt/sources.list.d/*; do [ -f "$f" ] && \
    sed -i 's|deb.debian.org|archive.debian.org|g; s|security.debian.org|archive.debian.org|g; /^deb.* bullseye-updates/d; s| bullseye-updates||' "$f"; done || true; \
    echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99archive

# System layer
RUN apt update && apt install -y --no-install-recommends \
    emacs-nox \
    ca-certificates \
    curl \
    wget \
    make \
    gettext \
    libgraphviz-dev \
    netcat
# Javascript dependencies layer
ENV NVM_DIR="/root/.nvm"
ENV NODE_VERSION 20.11.0
RUN ["mkdir", "/install"]
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.2/install.sh | bash && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION --latest-npm && npm install -g yarn
ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH      $NVM_DIR/v$NODE_VERSION/bin:$PATH

# Install wkhtmltopdf
RUN apt-get update && apt-get install -y wkhtmltopdf

# Python dependencies layer
COPY requirements.txt requirements-dev.txt /app/
RUN pwd && ls -la && pip install --upgrade pip && \
    pip install -r requirements-dev.txt && playwright install chromium && \
    apt-get update && apt-get install -y --no-install-recommends libnss3 libnspr4 libdrm2 libgbm1 && rm -rf /var/lib/apt/lists/* /root/.cache/pip

COPY package.json /install/
COPY collaborator_evaluation/package.json /install/collaborator_evaluation/
RUN . $NVM_DIR/nvm.sh && cd /install && yarn install && yarn cache clean
RUN . $NVM_DIR/nvm.sh && cd /install/collaborator_evaluation && yarn install && yarn cache clean
# Source layer
COPY . .
RUN ln -s /install/node_modules node_modules
RUN ln -s /install/collaborator_evaluation/node_modules collaborator_evaluation/node_modules

# Compiling translations and assets
RUN . $NVM_DIR/nvm.sh && make I18N:compile PYTHON=python && yarn build

