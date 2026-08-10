# 02 · Entorno, dependencias y configuración

## El entorno

Python **3.12** exacto. En macOS con Homebrew: `brew install python@3.12`.

> **Si `brew install` aborta**, no es un problema de la fórmula. En instalaciones
> viejas de Homebrew hay directorios de `/usr/local` que quedaron de root y
> cualquier instalación se detiene con «The following directories are not
> writable by your user». Se arregla una sola vez con el `chown` que el propio
> mensaje sugiere, y **pide contraseña** — o sea que no lo puede hacer un agente
> de código por su cuenta.
>
> Si no hay forma de instalar por brew, cualquier Python 3.12 sirve como base del
> entorno: `conda create -n <nombre> python=3.12` y después
> `<ruta>/bin/python -m venv .venv`. Lo que **no** se negocia es que el `venv`
> exista y que todo corra dentro de él.

```bash
# macOS / Linux
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

```powershell
# Windows
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
```

**Todo el stack va dentro de ese entorno, completo.** Nada contra el Python del
sistema y nada «que ya estaba instalado»: la aplicación tiene que arrancar en una
máquina limpia siguiendo solo el README. Las rutas de cada sistema y la comprobación
que falla si el entorno no está activo están en `19-verificacion-y-ejecucion.md`.

En el resto de estos prompts los comandos se escriben con la ruta de macOS
(`.venv/bin/…`) por brevedad; en Windows el equivalente es `.venv\Scripts\…`.

Copia `replica/referencia/requirements.txt` a la raíz **tal cual**. Las versiones
están fijadas y verificadas juntas; no las resuelvas por tu cuenta ni uses rangos.

## El proveedor del modelo: dos caminos, un modelo

El sistema soporta los dos y el resto del código no nota la diferencia. Se elige con
`PROVEEDOR_LLM` en el `.env`.

```python
def crear_modelo():
    if CONFIG.proveedor == "anthropic":
        from strands.models.anthropic import AnthropicModel
        llave = os.getenv("ANTHROPIC_API_KEY")
        if not llave:
            raise RuntimeError(
                "PROVEEDOR_LLM=anthropic pero no hay ANTHROPIC_API_KEY en el "
                "entorno. Ponla en el .env (que está en .gitignore) o expórtala."
            )
        return AnthropicModel(
            client_args={"api_key": llave},
            model_id=CONFIG.modelo_anthropic,   # claude-sonnet-5, SIN prefijo
            max_tokens=MAX_TOKENS,
        )
    return BedrockModel(
        model_id=CONFIG.modelo_bedrock,          # anthropic.claude-sonnet-5, CON prefijo
        region_name=CONFIG.region_aws,
        max_tokens=MAX_TOKENS,
    )
```

### `MAX_TOKENS = 16_384`, y no 4 096

Esto se descubrió en producción. Con 4 096 el chat funciona bien, pero el reporte
—que pide cuatro secciones sobre las cifras de seis gráficas— se corta a mitad de
frase con `MaxTokensReachedException`. **No es la ventana de contexto sino el tope
de escritura**, así que la solución es subir el tope y no recortar el encargo.

## La configuración

Un módulo `src/config.py` con un dataclass congelado que lee **todo** del entorno.
Ni un solo valor de negocio escrito en el código.

```python
proveedor          = os.getenv("PROVEEDOR_LLM", "bedrock").strip().lower()
modelo_bedrock     = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-sonnet-5")
modelo_anthropic   = os.getenv("ANTHROPIC_MODEL_ID", "claude-sonnet-5")
region_aws         = os.getenv("AWS_REGION", "us-east-1")
modelo_embeddings  = os.getenv("MODELO_EMBEDDINGS", "intfloat/multilingual-e5-base")

# Agente 1 — desperdicio
precio_resina_usd_kg = float(os.getenv("PRECIO_RESINA_USD_KG", "1.85"))
tolerancia_peso_g    = float(os.getenv("TOLERANCIA_PESO_G", "0.15"))
umbral_deriva_g_dia  = float(os.getenv("UMBRAL_DERIVA_G_DIA", "0.01"))
min_turnos_lote      = int(os.getenv("MIN_TURNOS_LOTE", "10"))
umbral_z_anomalia    = float(os.getenv("UMBRAL_Z_ANOMALIA", "3.5"))

# Agente 2 — paradas
costo_hora_paro_cop    = float(os.getenv("COSTO_HORA_PARO_COP", "2000000"))
prob_exito_preventivo  = float(os.getenv("PROB_EXITO_PREVENTIVO", "0.60"))
min_ocurrencias_patron = int(os.getenv("MIN_OCURRENCIAS_PATRON", "3"))
```

Ningún nombre de planta, ninguna fecha y ningún resultado viven acá.

## El `.env`

`replica/.env` ya viene listo — cópialo a la raíz del proyecto. `replica/.env.example`
es el que se comparte, con marcadores de posición y un comentario por variable
explicando qué cambia si la tocas.

`.gitignore` debe incluir, como mínimo:

```
.venv/
.env
__pycache__/
*.pyc
.chroma/
```

## Trampa de Streamlit: los módulos quedan cacheados

Streamlit no recarga un módulo ya importado que esté en `sys.modules`. Si editas
`src/config.py` con la app corriendo, el proceso sigue usando la versión vieja y
aparecen errores del tipo `AttributeError: 'Config' object has no attribute 'x'`
aunque el campo esté bien escrito en disco.

**Cuando cambies un módulo de configuración o de datos, reinicia el proceso.** No
pierdas media hora buscando un bug que no existe.

## Ruido en la consola que no es tuyo

El vigilante de archivos de Streamlit recorre los módulos importados para saber
cuáles recargar, y al hurgar en `transformers` tropieza con sus importaciones
perezosas de `torchvision` —que no está instalado y no hace falta—. Son **cientos
de trazas al arrancar** que no son errores de la aplicación pero se leen exactamente
como si lo fueran, y en un taller eso cuesta media hora de preguntas.

Se registran como advertencia, así que se callan sin perder la recarga automática:

```toml
[logger]
level = "error"
```

## Verificación de esta fase

```bash
.venv/bin/python -c "
import importlib.metadata as md
for p in ('strands-agents', 'pandas', 'streamlit', 'chromadb',
          'sentence-transformers', 'vl-convert-python'):
    print(f'  {p:22} {md.version(p)}')
print('dependencias ok')
"
.venv/bin/python -c "from src.config import CONFIG; print(CONFIG.proveedor, CONFIG.modelo_anthropic)"
```

Las dos tienen que imprimir sin traza. Pega la salida.

> **Por qué se pregunta por metadatos y no con `import`.** La versión obvia de
> esta comprobación era `import strands, pandas, …, sentence_transformers, …`, y
> **falla en macOS con procesador Intel**: ahí `import sentence_transformers`
> arrastra un PyTorch que no puede hablar con NumPy 2 (ver `07-semantica.md`) y
> escupe una traza de cuarenta líneas.
>
> Quien corre la verificación oficial, ve eso y concluye que instaló mal — cuando
> el entorno está perfecto y la aplicación arranca sin problema. Preguntar si el
> paquete **está instalado** es lo que esta comprobación quiere saber; que además
> se pueda importar es otra cosa, y en esa plataforma no se cumple ni hace falta.
