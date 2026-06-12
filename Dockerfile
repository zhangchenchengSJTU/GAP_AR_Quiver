FROM debian:bookworm-slim

ARG GAP_VERSION=latest
ARG GAP_PREFIX=/opt/gap

ENV DEBIAN_FRONTEND=noninteractive \
    GAP_ROOT=/opt/gap \
    LD_LIBRARY_PATH="/opt/gap/lib:${LD_LIBRARY_PATH}" \
    PATH="/opt/gap/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        build-essential \
        gfortran \
        make \
        cmake \
        autoconf \
        automake \
        libtool \
        m4 \
        pkg-config \
        git \
        perl \
        python3 \
        libgmp-dev \
        libreadline-dev \
        zlib1g-dev \
        libncurses-dev \
        libffi-dev \
        libssl-dev \
        libmpfr-dev \
        bzip2 \
        xz-utils \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    resolved_gap_version="${GAP_VERSION}"; \
    if [ "${resolved_gap_version}" = "latest" ]; then \
        resolved_gap_version="$(curl -fsSLI -o /dev/null -w '%{url_effective}' https://github.com/gap-system/gap/releases/latest | sed 's#.*/tag/v##')"; \
    fi; \
    curl -fsSL "https://github.com/gap-system/gap/releases/download/v${resolved_gap_version}/gap-${resolved_gap_version}.tar.gz" -o /tmp/gap.tar.gz; \
    mkdir -p /usr/local/src/gap; \
    tar -xzf /tmp/gap.tar.gz -C /usr/local/src/gap --strip-components=1; \
    rm /tmp/gap.tar.gz; \
    cd /usr/local/src/gap; \
    ./configure --prefix="${GAP_PREFIX}"; \
    make -j"$(nproc)"; \
    make bootstrap-pkg-full || make bootstrap-pkg-minimal || true; \
    make install; \
    echo "${GAP_PREFIX}/lib" > /etc/ld.so.conf.d/gap.conf; \
    ldconfig; \
    "${GAP_PREFIX}/bin/gap" -q -c 'Print("GAP ", GAPInfo.Version, "\\n"); QUIT;'

WORKDIR /workspace

CMD ["gap"]
