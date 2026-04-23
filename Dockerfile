# ===== builder step =====
FROM python:3.9.13-buster AS builder

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBCONF_NOWARNINGS=yes
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Paris

# System layer
RUN apt update && apt install -y \
    emacs \
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
    pip install -r requirements-dev.txt && playwright install && \
    apt-get update && apt-get install libnss3 libnspr4 libdrm2 libgbm1 -y

COPY package.json /install/
COPY collaborator_evaluation/package.json /install/collaborator_evaluation/
RUN . $NVM_DIR/nvm.sh && cd /install && yarn install
RUN . $NVM_DIR/nvm.sh && cd /install/collaborator_evaluation && yarn install
# Source layer
COPY . .
RUN ln -s /install/node_modules node_modules
RUN ln -s /install/collaborator_evaluation/node_modules collaborator_evaluation/node_modules

# Compiling translations and assets
RUN . $NVM_DIR/nvm.sh && make I18N:compile PYTHON=python && yarn build

