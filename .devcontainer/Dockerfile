# Imagen del taller "Asistentes de planta".
#
# Todo lo pesado se hornea aca: los paquetes de Python (~1.8 GB) y el modelo de
# embeddings (~2.1 GB). El alumno no descarga nada de eso — abre el Codespace y
# ya esta. Esa es la razon de existir de este archivo.
#
# Cada paso imprime un marcador ===> para que el "Creation Log" sea legible
# cuando algo falle.

FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

# El entorno virtual y el cache del modelo viven FUERA de /workspaces.
# Codespaces monta el repositorio clonado encima de /workspaces/<repo>, asi que
# cualquier cosa que dejemos ahi durante la construccion desaparece al arrancar.
# El `.venv` que espera el material del taller se crea como enlace simbolico a
# /opt/venv en `al-crear.sh`.
ENV VENV=/opt/venv \
    HF_HOME=/opt/cache-modelos \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

# ---------------------------------------------------------------------------
# 0. Los directorios, vacios y con dueño, ANTES de llenarlos
# ---------------------------------------------------------------------------
# Sin `chown -R` en ninguna parte, y es a proposito. Un chown recursivo sobre un
# venv de 1.8 GB no solo tarda minutos: en Docker reescribe cada archivo en una
# capa nueva, o sea que DUPLICA el tamaño de la imagen. Creando los directorios
# vacios con el dueño correcto y trabajando como `vscode` desde aqui, cada
# archivo nace ya con su dueño y no hay nada que corregir despues.
#
# OJO CON LOS PADRES. `mkdir -p a/b/c` crea `a` y `a/b` como root, y darle dueño
# solo a `a/b/c` no sirve: el usuario sigue sin poder escribir en los de arriba.
# El instalador de Claude Code guarda las versiones en ~/.local/share, asi que
# ~/.local, ~/.local/bin y ~/.local/share necesitan dueño los tres.
#
# Estos chown son sobre directorios VACIOS y sin -R: instantaneos, y no tienen
# nada que ver con el chown recursivo sobre 4 GB que hubo aca antes.
RUN set -eux; \
    echo "===> 0. directorios"; \
    mkdir -p "$VENV" "$HF_HOME" \
             /home/vscode/.local/bin /home/vscode/.local/share \
             /home/vscode/.claude; \
    chown vscode:vscode "$VENV" "$HF_HOME" \
                        /home/vscode/.local /home/vscode/.local/bin \
                        /home/vscode/.local/share /home/vscode/.claude

USER vscode
ENV PATH="/home/vscode/.local/bin:${PATH}"

# ---------------------------------------------------------------------------
# 1. Entorno virtual
# ---------------------------------------------------------------------------
# Se usa `python3`, no `python3.12`: la imagen base expone el interprete por ese
# nombre y no garantiza un alias con el numero de version. Igual se verifica que
# sea 3.12 y se falla en el acto si no lo es — una imagen construida sobre otra
# version arranca bien y revienta despues, que es peor.
RUN set -eux; \
    echo "===> 1. entorno virtual"; \
    python3 --version; \
    python3 -c 'import sys; assert sys.version_info[:2] == (3, 12), sys.version'; \
    python3 -m venv "$VENV"; \
    "$VENV/bin/pip" install --no-cache-dir --upgrade pip

# ---------------------------------------------------------------------------
# 2. PyTorch, solo-CPU
# ---------------------------------------------------------------------------
# `sentence-transformers` arrastra torch, y el torch por defecto de PyPI para
# Linux viene con todo el stack de CUDA: son varios gigabytes de bibliotecas de
# GPU que en un Codespace no tienen ninguna tarjeta que usar. Instalandolo
# primero desde el indice de solo-CPU, pip ya lo encuentra satisfecho y no lo
# reemplaza al resolver el requirements.
RUN set -eux; \
    echo "===> 2. torch (CPU)"; \
    "$VENV/bin/pip" install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu torch

# ---------------------------------------------------------------------------
# 3. El resto de los paquetes
# ---------------------------------------------------------------------------
COPY --chown=vscode:vscode referencia/requirements.txt /tmp/requirements.txt
RUN set -eux; \
    echo "===> 3. requirements.txt"; \
    "$VENV/bin/pip" install --no-cache-dir -r /tmp/requirements.txt; \
    rm /tmp/requirements.txt; \
    "$VENV/bin/python" -c 'import importlib.metadata as m; [m.version(p) for p in ("streamlit","chromadb","strands-agents","pandas")]; print("paquetes clave presentes")'

# ---------------------------------------------------------------------------
# 4. Modelo de busqueda por significado
# ---------------------------------------------------------------------------
COPY --chown=vscode:vscode .devcontainer/preparar-modelo.py /tmp/preparar-modelo.py
RUN set -eux; \
    echo "===> 4. modelo de embeddings"; \
    "$VENV/bin/python" /tmp/preparar-modelo.py; \
    rm /tmp/preparar-modelo.py

# ---------------------------------------------------------------------------
# 5. Claude Code
# ---------------------------------------------------------------------------
# Version FIJA, no "latest". Los quince alumnos tienen que estar en la misma
# version que probaste tu: si cada Codespace instala la ultima del dia, a media
# manana unos ven una interfaz y otros ven otra, y tus instrucciones dejan de
# coincidir con la pantalla.
#
# El `claude --version` de abajo no es decorativo: si la instalacion se cae a
# medias, la construccion tiene que fallar aqui y no despues.
RUN set -eux; \
    echo "===> 5. Claude Code"; \
    curl -fsSL https://claude.ai/install.sh | bash -s 2.1.144; \
    claude --version

# Sin auto-actualizacion en segundo plano, por la misma razon que el pin.
COPY --chown=vscode:vscode .devcontainer/claude-settings.json /home/vscode/.claude/settings.json

RUN echo "===> imagen del taller lista"
