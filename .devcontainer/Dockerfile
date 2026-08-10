# Imagen del taller "Asistentes de planta".
#
# Todo lo pesado se hornea aca: los paquetes de Python (~1.8 GB) y el modelo de
# embeddings (~2.1 GB). El alumno no descarga nada de eso — abre el Codespace y
# ya esta. Esa es la razon de existir de este archivo.

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
# 1. Paquetes de Python
# ---------------------------------------------------------------------------
# torch se instala APARTE y desde el indice de solo-CPU, antes que el resto.
# `sentence-transformers` lo arrastra como dependencia, y el torch por defecto
# de PyPI para Linux viene con todo el stack de CUDA: son varios gigabytes de
# bibliotecas de GPU que en un Codespace no tienen ninguna maquina que usar.
# Instalandolo primero, pip ya lo encuentra satisfecho y no lo reemplaza.
RUN python3.12 -m venv "$VENV" \
 && "$VENV/bin/pip" install --no-cache-dir --upgrade pip \
 && "$VENV/bin/pip" install --no-cache-dir \
      --index-url https://download.pytorch.org/whl/cpu torch

COPY referencia/requirements.txt /tmp/requirements.txt
RUN "$VENV/bin/pip" install --no-cache-dir -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt

# ---------------------------------------------------------------------------
# 2. Modelo de busqueda por significado
# ---------------------------------------------------------------------------
COPY .devcontainer/preparar-modelo.py /tmp/preparar-modelo.py
RUN "$VENV/bin/python" /tmp/preparar-modelo.py \
 && rm /tmp/preparar-modelo.py

RUN chown -R vscode:vscode "$VENV" "$HF_HOME"

# ---------------------------------------------------------------------------
# 3. Claude Code
# ---------------------------------------------------------------------------
USER vscode
ENV PATH="/home/vscode/.local/bin:${PATH}"

# Version FIJA, no "latest". Los quince alumnos tienen que estar en la misma
# version que probaste tu: si cada Codespace instala la ultima del dia, a media
# manana unos ven una interfaz y otros ven otra, y tus instrucciones dejan de
# coincidir con la pantalla.
RUN curl -fsSL https://claude.ai/install.sh | bash -s 2.1.144

# Y por la misma razon, sin auto-actualizacion en segundo plano: Claude Code
# busca versiones nuevas al arrancar y se actualiza solo si no se le apaga.
RUN mkdir -p /home/vscode/.claude \
 && printf '%s\n' \
    '{' \
    '  "$schema": "https://json.schemastore.org/claude-code-settings.json",' \
    '  "env": {' \
    '    "DISABLE_AUTOUPDATER": "1"' \
    '  }' \
    '}' > /home/vscode/.claude/settings.json
