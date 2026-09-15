# Mantra2 — self-contained mutation toolchain.
#
# Everything the tool needs lives in this image:
#   * Python 3.11
#   * PyVerilog 1.2.1 (+ the bundled compatibility patch, applied at build time)
#   * Icarus Verilog (iverilog + vvp) for preprocessing and the default
#     simulation backend
#
# Synopsys VCS is commercial and cannot be bundled. Mount your own licence and
# toolchain if you need `--backend vcs`.
FROM python:3.11-slim

# Docker forwards the host proxy (HTTP_PROXY/HTTPS_PROXY) into the build
# context. A socks5 proxy breaks apt/pip, so neutralise it. The container still
# reaches the network directly through Docker's NAT.
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG http_proxy
ARG https_proxy
ARG ALL_PROXY
ARG all_proxy
ENV HTTP_PROXY="" HTTPS_PROXY="" http_proxy="" https_proxy="" ALL_PROXY="" all_proxy=""

# Build essentials are not needed at runtime, only for pip wheels that ship
# without manylinux binaries. We drop them again afterwards to keep the layer
# small.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        iverilog \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# A dedicated user so the container never runs as root by default.
RUN useradd --create-home --uid 1000 mantra

WORKDIR /opt/mantra2
COPY --chown=mantra:mantra . /opt/mantra2

# Install the package (this pulls pyverilog==1.2.1) and immediately apply the
# bundled PyVerilog patch, so the image is usable the moment it starts.
RUN python -m pip install --no-cache-dir "/opt/mantra2[mutation]" \
    && mantra2 setup-pyverilog --yes

# /data is the conventional mount point for the project you want to mutate.
WORKDIR /data

USER mantra

ENTRYPOINT ["mantra2"]
CMD ["--help"]
