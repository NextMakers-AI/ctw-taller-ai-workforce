#!/usr/bin/env bash
# Se ejecuta una vez, al crear el Codespace, despues de montar el repositorio.
#
# Lo pesado ya esta dentro de la imagen. Aca solo queda conectar el ambiente
# horneado con la carpeta del taller, y avisarle al alumno si algo falta.

set -euo pipefail

VENV_REAL=/opt/venv

echo
echo "Preparando la carpeta del taller..."

# ---------------------------------------------------------------------------
# .venv -> /opt/venv
# ---------------------------------------------------------------------------
# Todo el material del taller dice `.venv/bin/python`. El entorno real vive en
# /opt para sobrevivir al montaje del repositorio, asi que aca se tiende el
# puente. Sin esto, cada comando del taller falla con "no such file".
if [ ! -e .venv ]; then
  ln -s "$VENV_REAL" .venv
  echo "  .venv enlazado al entorno de la imagen"
fi

# ---------------------------------------------------------------------------
# Comprobaciones que le importan al alumno
# ---------------------------------------------------------------------------
problemas=0

version_python=$(.venv/bin/python -V 2>&1)
echo "  ${version_python}"

if [ -f .env ] && grep -q '^ANTHROPIC_API_KEY=sk-ant-' .env 2>/dev/null; then
  echo "  Llave de API: configurada en .env"
elif [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo "  Llave de API: tomada del ambiente"
else
  echo "  Llave de API: FALTA — mira el paso 2 de 00-preparacion-del-entorno.md"
  problemas=$((problemas + 1))
fi

csv=$(find datos -maxdepth 1 -name '*.csv' 2>/dev/null | wc -l | tr -d ' ')
if [ "$csv" -eq 5 ]; then
  echo "  Datos: los cinco CSV estan"
else
  echo "  Datos: se esperaban 5 archivos CSV y hay ${csv}"
  problemas=$((problemas + 1))
fi

echo
if [ "$problemas" -eq 0 ]; then
  echo "Ambiente listo. Abre 01-fase-1-asistente-conversacional.md para empezar."
else
  echo "Ambiente casi listo: hay ${problemas} cosa(s) por resolver, arriba."
fi
echo
