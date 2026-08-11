# Imagen del taller "Asistentes de planta".
#
# Hornea Python 3.12, los paquetes del proyecto y Claude Code, para que el alumno
# no descargue ni instale nada: abre el Codespace y ya esta.
#
# Cada paso imprime un marcador ===> para que el "Creation Log" sea legible
# cuando algo falle.

FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

# El entorno virtual vive FUERA de /workspaces. Codespaces monta el repositorio
# clonado encima de /workspaces/<repo>, asi que cualquier cosa que dejemos ahi
# durante la construccion desaparece al arrancar. El `.venv` que espera el
# material del taller se crea como enlace simbolico a /opt/venv en `al-crear.sh`.
ENV VENV=/opt/venv \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

# ---------------------------------------------------------------------------
# 0. Los directorios, vacios y con dueño, ANTES de llenarlos
# ---------------------------------------------------------------------------
# OJO CON LOS PADRES. `mkdir -p a/b/c` crea `a` y `a/b` como root, y darle dueño
# solo a `a/b/c` no sirve: el usuario sigue sin poder escribir en los de arriba.
# El instalador de Claude Code guarda las versiones en ~/.local/share, asi que
# ~/.local, ~/.local/bin y ~/.local/share necesitan dueño los tres.
#
# Estos chown son sobre directorios VACIOS y sin -R: instantaneos. Un chown
# recursivo sobre un venv ya lleno no solo tarda minutos, en Docker reescribe
# cada archivo en una capa nueva y DUPLICA el tamaño de la imagen.
RUN set -eux; \
    echo "===> 0. directorios"; \
    mkdir -p "$VENV" \
             /home/vscode/.local/bin /home/vscode/.local/share \
             /home/vscode/.claude; \
    chown vscode:vscode "$VENV" \
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
# 2. Los paquetes del proyecto
# ---------------------------------------------------------------------------
# Trece paquetes, todos con rueda para Linux, sin nada que compilar. Antes aca
# habia un paso extra para instalar torch desde el indice de solo-CPU: el
# proyecto ya no lleva embeddings, asi que ni torch ni el modelo de 2 GB entran
# a la imagen. Ver la seccion "Por que esto NO lleva embeddings" de la fase 3.
COPY --chown=vscode:vscode referencia/requirements.txt /tmp/requirements.txt
RUN set -eux; \
    echo "===> 2. requirements.txt"; \
    "$VENV/bin/pip" install --no-cache-dir -r /tmp/requirements.txt; \
    rm /tmp/requirements.txt; \
    "$VENV/bin/python" -c 'import importlib.metadata as m; [m.version(p) for p in ("streamlit","strands-agents","pandas","altair","fpdf2")]; print("paquetes clave presentes")'

# ---------------------------------------------------------------------------
# 3. Claude Code
# ---------------------------------------------------------------------------
# Version FIJA, no "latest". Los quince alumnos tienen que estar en la misma
# version que probaste tu: si cada Codespace instala la ultima del dia, a media
# manana unos ven una interfaz y otros ven otra, y tus instrucciones dejan de
# coincidir con la pantalla.
#
# El `claude --version` de abajo no es decorativo: si la instalacion se cae a
# medias, la construccion tiene que fallar aqui y no despues.
RUN set -eux; \
    echo "===> 3. Claude Code"; \
    curl -fsSL https://claude.ai/install.sh | bash -s 2.1.227; \
    claude --version

# Modelo, modo de permisos y auto-actualizacion, fijados para los quince.
COPY --chown=vscode:vscode .devcontainer/claude-settings.json /home/vscode/.claude/settings.json

RUN echo "===> imagen del taller lista"
