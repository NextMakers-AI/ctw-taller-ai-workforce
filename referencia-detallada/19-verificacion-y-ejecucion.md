# 19 · Ejecución local, verificación final y entrega

## Cómo se corre, en Windows y en macOS

La aplicación **siempre corre dentro de un entorno virtual de Python**, nunca contra
el Python del sistema: así las versiones fijadas valen y nada de lo que instale este
proyecto rompe otro.

Lo único que cambia entre sistemas operativos es **la ruta del ejecutable dentro del
entorno**: `Scripts\` en Windows, `bin/` en macOS y Linux.

### macOS / Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python -m src.generar_datos
python -m src.verificar_datos
streamlit run app.py
```

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

python -m src.generar_datos
python -m src.verificar_datos
streamlit run app.py
```

> Si PowerShell bloquea el script de activación, se habilita una sola vez con
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`. Es la
> pregunta número uno en un taller con máquinas Windows.

**Sin activar el entorno** también funciona, llamando al ejecutable por su ruta —útil
para un script o para el propio agente de código:

| | macOS / Linux | Windows |
|---|---|---|
| Python | `.venv/bin/python` | `.venv\Scripts\python.exe` |
| pip | `.venv/bin/pip` | `.venv\Scripts\pip.exe` |
| Streamlit | `.venv/bin/streamlit` | `.venv\Scripts\streamlit.exe` |

### Comprueba que de verdad estás en el entorno, con el stack completo

Antes de dar nada por instalado. Si esto falla, todo lo demás miente:

```bash
# macOS/Linux: .venv/bin/python   ·   Windows: .venv\Scripts\python.exe
.venv/bin/python -c "
import sys, importlib.metadata as md
assert sys.prefix != sys.base_prefix, 'NO estás en el entorno virtual'
print(f'entorno: {sys.prefix}')
print(f'python : {sys.version.split()[0]}')
faltan = []
for paquete in ('strands-agents', 'anthropic', 'boto3', 'pandas', 'numpy',
                'statsmodels', 'scipy', 'sentence-transformers', 'chromadb',
                'streamlit', 'altair', 'vl-convert-python', 'python-dotenv'):
    try:
        print(f'  {paquete:22} {md.version(paquete)}')
    except md.PackageNotFoundError:
        faltan.append(paquete)
assert not faltan, f'faltan en el entorno: {faltan}'
print('stack completo dentro del entorno virtual')
"
```

Tiene que imprimir **las trece líneas de versión** y terminar en `stack completo`.

Dos fallos típicos que esta comprobación atrapa:

- `sys.prefix == sys.base_prefix` → estás corriendo el Python del sistema. Los
  paquetes que veas instalados son globales, y en otra máquina no van a estar.
- Un paquete falta pero la app «funciona» → estaba instalado globalmente y el
  entorno lo está tomando prestado. En una máquina limpia se rompe.

### La URL que hay que abrir

Al arrancar, Streamlit imprime esto y normalmente abre el navegador solo:

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

**La dirección que hay que poner en el navegador es:**

```
http://localhost:8501
```

Tres cosas que hay que decirle a quien lo corre:

- Si el puerto 8501 está ocupado, Streamlit toma el siguiente (8502, 8503…). **Lee la
  URL que imprime**, no la asumas. Para fijarlo: `streamlit run app.py --server.port 8501`.
- La **Network URL** sirve para abrirla desde otro equipo de la misma red —útil para
  proyectar desde otra máquina en el taller—. No la uses en una red pública: la
  aplicación no tiene autenticación, por diseño.
- Para que **no** abra el navegador solo (por ejemplo al correrla desde un script),
  el `config.toml` ya trae `headless = true`.

Cuando termines de construir, **imprime la URL en el mensaje final** en vez de dar
por hecho que la persona la vio pasar en la consola.

---

## Verificación final y entrega

## Las tres verificaciones

Córrelas y **pega la salida real**. No las declares hechas.

```bash
.venv/bin/python -m src.verificar_datos          # ✓ Los 7 patrones son detectables
.venv/bin/python -m src.paras.verificar_datos    # ✓ Los patrones verificables … · 2 aviso(s)
.venv/bin/python -m pruebas.test_calculos        # ✓ Los cálculos recuperan los 7 patrones
```

Los **2 avisos** del segundo son correctos y esperados: son las dos promesas del plan
que los datos no sostienen. No los hagas desaparecer tocando el generador.

## Comprobación de la interfaz

Con la app corriendo, para **cada agente** y en **cada modo** (claro y oscuro):

| # | Qué | Cómo se ve que está bien |
|---|---|---|
| 1 | Las cuatro pestañas abren | Sin excepción en pantalla |
| 2 | Contraste | Ningún texto blanco sobre blanco, tampoco en hover |
| 3 | Filtros | Cambiar de asistente y volver: siguen puestos |
| 4 | Recarga | F5 en Paradas/Tablero deja donde estaba |
| 5 | Sugerencias | Al hacer clic, lanzan la pregunta |
| 6 | Chat | Sin scroll horizontal; el texto dentro de su burbuja |
| 7 | Alto del chat | No encoge al empezar a responder |
| 8 | Reporte | Descarga, 6 SVG, sin CDN, una hoja por gráfica |
| 9 | Consola | Cero trazas al arrancar |

## Lo que se entrega

### `README.md` en español, con arranque en cuatro comandos

```bash
# 1 · entorno y dependencias
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
# 2 · configuración
cp .env.example .env      # y pon tu ANTHROPIC_API_KEY
# 3 · datos + verificación de los dos agentes
.venv/bin/python -m src.generar_datos && .venv/bin/python -m src.verificar_datos
# 4 · la aplicación
.venv/bin/streamlit run app.py
```

El README tiene que incluir, además del arranque:

- **Las cinco lecciones** con la trampa de cada una
- **El hallazgo de la fecha del turno** del agente 2
- **Las dos promesas que los datos no sostienen**, dichas como avisos
- **Por qué `pypdf` y el troceado no aplican** — explicado, no omitido
- **Por qué los embeddings solo tocan el texto libre**
- **La corrección de Sonnet 4 → Sonnet 5** y la diferencia de identificador entre
  Bedrock y la Claude API

### `preguntas_ejemplo.md`

Cuatro preguntas **con las respuestas reales que dieron al ejecutarlas**. No
inventadas, no editadas para que se vean mejor. Si una respuesta salió floja, esa es
información: o el prompt o una herramienta necesitan trabajo.

Ninguna pregunta lleva fecha escrita a mano.

### Archivos de proyecto

`requirements.txt` con versiones fijadas, `.env.example` comentado, `.gitignore`.

## Autocrítica antes de entregar

Repasa esta lista y **reporta lo que no cumplas** en vez de dejarlo pasar:

- [ ] ¿Hay algún `groupby` fuera de los módulos de cálculo?
- [ ] ¿Hay alguna cifra de negocio escrita a mano en el código?
- [ ] ¿Hay alguna fecha o nombre de planta escrito a mano?
- [ ] ¿El bloque de trazabilidad lo arma el código, y suma por unión de conjuntos?
- [ ] ¿Los pies de los gráficos se recalculan del dato, o hay prosa que afirma algo
      que dejaría de ser cierto con otro archivo?
- [ ] ¿Los embeddings tocan algún número?
- [ ] ¿Todos los textos están en español neutro, sin voseo?
- [ ] ¿La paleta se verificó con criterios medibles, o se eligió de vista?
- [ ] ¿Hay algún `var(--x, ...)` de CSS esperando una variable que Streamlit no expone?
- [ ] ¿Algún fallo del modelo puede tumbar la interfaz o el reporte?

## Lo que NO hay que hacer

- **No inventes que verificaste.** Si no corriste el comando, dilo.
- **No hagas desaparecer un aviso tocando el generador.** Que el verificador diga
  «esto no está» es el verificador funcionando.
- **No agregues dependencias** fuera de las fijadas, salvo que algo del enunciado lo
  exija; si lo haces, fíjala y explica por qué en el README.
- **No reemplaces una cifra que no cuadra por una que sí.** Las tres cifras
  equivocadas que se encontraron construyendo esto salieron de *leer* la salida de
  las pruebas: costo de deriva mal escalado, línea base de 5 turnos, y un promedio de
  cavidades hermanas que se incluía a sí mismo.
