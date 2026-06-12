FROM ubuntu:24.04

ARG GAP_VERSION=4.15.1

ENV DEBIAN_FRONTEND=noninteractive
ENV GAP_HOME=/opt/gap-${GAP_VERSION}
ENV PATH="${GAP_HOME}/bin:${PATH}"

RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    bzip2 \
    build-essential \
    m4 \
    perl \
    python3 \
    libgmp-dev \
    zlib1g-dev \
    libreadline-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN wget "https://github.com/gap-system/gap/releases/download/v${GAP_VERSION}/gap-${GAP_VERSION}.tar.gz" \
    && tar -xzf "gap-${GAP_VERSION}.tar.gz" \
    && rm "gap-${GAP_VERSION}.tar.gz"

WORKDIR ${GAP_HOME}

RUN ./configure --with-gmp=system \
    && make -j"$(nproc)" \
    && mkdir -p ${GAP_HOME}/bin \
    && ln -sf ${GAP_HOME}/gap ${GAP_HOME}/bin/gap

RUN useradd -ms /bin/bash gap \
    && chown -R gap:gap ${GAP_HOME}

USER gap
WORKDIR /home/gap/workspace

CMD ["gap"]
