# 06 · El agente, sus herramientas y la trazabilidad

## Las siete herramientas

Con el decorador `@tool` de `strands`, que **saca el esquema del docstring y de las
anotaciones de tipo**. El docstring no es documentación: es la interfaz que el
modelo lee para decidir cuándo llamarla. Escríbelo pensando en eso.

| Herramienta | Para qué |
|---|---|
| `calcular_desperdicio` | Las dos mitades, separadas y sumadas |
| `analizar_deriva` | Deriva vs setpoint desviado, con su clasificación |
| `rankear_lotes_resina` | Lotes con evidencia + descartados con su `n` |
| `atribuir_categorias` | Exceso sobre línea base, con aviso de solapamiento |
| `comparar_dimension` | Línea, SKU, molde, cavidad (con su molde) |
| `detectar_turnos_anomalos` | Z robusto |
| `buscar_notas_similares` | **Solo texto libre.** Nunca cuenta nada |

Todas devuelven `dict`. Todas anotan en el registro de trazabilidad las filas que
tocaron.

## El prompt del sistema

**No contiene ni una cifra.** Lo único concreto que lleva es el inventario de la
planta —qué líneas, qué SKU, qué turnos, qué rango de fechas— y eso se deriva de los
CSV al arrancar.

Un número en el prompt es un número que nadie puede auditar y que el modelo repetirá
con total seguridad cuando los datos ya hayan cambiado.

Estructura:

1. **Quién eres** — analista de desperdicio, responde en español, con la precisión
   de alguien que sabe que cualquiera en la sala puede pedirle verificar la cifra.
2. **La planta**, derivada de los datos.
3. **La regla que no se negocia** — toda cifra sale de una herramienta.
4. **Cómo interpretar lo que devuelven las herramientas** — las cinco lecciones,
   escritas como instrucciones de lectura, más: `buscar_notas_similares` no cuenta
   nada, sirve para «¿ha pasado esto antes?».
5. **Cómo escribir** — primero la respuesta directa en una o dos frases, después la
   evidencia con las cifras tal como vienen, al final qué hacer distinguiendo ajuste
   de mantenimiento.
6. **Prohibición explícita de escribir el bloque de trazabilidad**: lo agrega el
   código. Un bloque de auditoría redactado por el modelo tendría exactamente el
   problema que viene a resolver.

## `callback_handler=None` no es opcional

```python
Agent(model=..., tools=..., system_prompt=..., callback_handler=None)
```

Por omisión `Agent` instala un manejador que va imprimiendo la respuesta a stdout
por su cuenta. Como el texto se consume por `stream_async`, dejarlo activo hace que
cada trozo salga **dos veces** y en consola se vea como una respuesta entrelazada
consigo misma.

## El puente de streaming async → sync

Streamlit corre sincrónico y `stream_async` es asíncrono. Un hilo aparte con una
`queue.Queue` y un centinela de fin:

```python
_FIN = object()

def iterar_respuesta(agente, pregunta):
    cola = queue.Queue()
    def correr():
        async def bombear():
            async for evento in agente.stream_async(pregunta):
                cola.put(evento)
        try: asyncio.run(bombear())
        except BaseException as exc: cola.put(exc)   # se relanza en el hilo principal
        finally: cola.put(_FIN)
    threading.Thread(target=correr, daemon=True).start()
    ...
```

Formas de evento verificadas contra el código de `strands`:

- texto → `{"data": "trozo de texto"}`
- herramienta → `{"current_tool_use": {"toolUseId": ..., "name": ...}}`

`current_tool_use` **se repite en cada delta** mientras se arman los argumentos.
Emítelo una sola vez por invocación, recordando el último `toolUseId` visto.

Emite dos clases de evento: `{"tipo": "herramienta"}` y `{"tipo": "texto"}`. Ver al
agente consultar los datos es lo que deja claro que no está improvisando — es medio
taller.

## La trazabilidad

```python
class Registro:
    def anotar(self, herramienta, traza):
        # UNIÓN DE CONJUNTOS de índices, no suma de conteos
        for fuente, indices in traza.get("filas", {}).items():
            self._filas.setdefault(fuente, set()).update(int(i) for i in indices)
```

**Esto es lo que evita el número inflado.** Si tres herramientas consultan las mismas
26 000 filas, el bloque dice 26 000. Sumando conteos diría 78 000, y quien conozca
el archivo sabría que es mentira — y a partir de ahí no cree nada más.

El bloque en markdown lo arma el código y se pega al final de la respuesta:

```
---
**Trazabilidad** *(generada por el código, no por el modelo)*
Rango consultado: **2026-02-08 → 2026-08-06**
Filas analizadas: **29,151** — 3,194 eventos · 25,395 muestras · 562 cierres
Precio de resina aplicado: **1.85 USD/kg**
Herramientas ejecutadas: `detectar_turnos_anomalos`, `buscar_notas_similares`
```

### Quién limpia el registro, y cuándo

El registro es **de una respuesta, no de la sesión**, y eso hay que dejarlo
escrito porque de ahí salen dos bugs que no fallan:

- **`configurar()` lo limpia**, y por eso vive a nivel de módulo y no dentro del
  contexto: así se puede consultar antes de configurar nada y el bloque nunca
  depende del orden en que se llamen las cosas.
- **Cada pregunta reconfigura.** La interfaz lo hace sola porque Streamlit
  reejecuta el script entero, pero el guion de consola de `preguntar.py` no: si
  `configurar()` se llama una sola vez al arrancar, el bloque de la cuarta
  pregunta lista las herramientas y las filas de las **cuatro**. Es exactamente
  el número inflado que este bloque viene a evitar, y encima queda impreso en el
  archivo de preguntas de ejemplo que se entrega.
- **El reporte anota a mano, y por eso el orden importa** (ver `16-reporte.md`):
  anotar y después configurar deja el bloque en blanco.

`limpiar_para_modelo(resultado)` quita las claves con `_` antes de mandar nada al
modelo: son series y arreglos de índices que gastarían miles de tokens y además lo
tentarían a sumar a mano justo lo que las herramientas ya sumaron bien.

## Una respuesta de punta a punta, sin interfaz

`src/preguntar.py` corre las preguntas por consola. Sirve para probar el agente
antes de tener interfaz, que es el orden correcto: **si algo se rompe ahí, el
problema es del agente; si se rompe solo en Streamlit, es de la interfaz.**

Las cuatro preguntas de ejemplo **no llevan fechas escritas a mano**. El rango de
los datos se deriva del día en que se generaron, así que una pregunta con la fecha
dentro se rompe sola en cuanto alguien vuelve a correr el generador. En vez de «el
18 de junio», se pregunta «cuál fue el peor turno del período» — que además es la
demostración que importa.

## Verificación de esta fase

```bash
.venv/bin/python -m src.preguntar "¿Cuánto material estamos desperdiciando y de qué tipo es?"
```

Tiene que verse el agente llamando herramientas y, al final, el bloque de
trazabilidad. Comprueba a mano que **las filas analizadas no superen el total de
filas de los archivos**: si lo superan, estás sumando conteos en vez de unir
conjuntos.
