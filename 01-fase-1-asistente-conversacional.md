# Fase 1 · Asistente conversacional con trazabilidad

> **Cómo se usa.** Pega este archivo entero como primer mensaje en tu agente de
> código, en la carpeta del taller. Antes, haz lo de `00-preparacion-del-entorno.md`.

## Cómo trabajar conmigo

**No sé programar.** Trabaja de forma autónoma y no me pidas decisiones técnicas.

- Háblame en **español sencillo**, sin jerga y sin trazas de error.
- Si algo falla, **diagnostícalo y arréglalo tú**. Después cuéntame en una frase
  qué pasó y qué hiciste; no me muestres el error para que lo interprete yo.
- Si de verdad necesitas algo de mí, pídeme **una sola cosa a la vez**, con
  instrucciones exactas de dónde y qué escribir.
- **No inventes que verificaste algo.** Cuando este archivo diga «verifica X»,
  ejecuta el comando y mira la salida real. Si falla, arréglalo y vuelve a
  correrlo.
- Al terminar, dime en pocas frases **qué construiste y qué puedo probar yo**,
  con el comando exacto o lo que tengo que mirar en pantalla.

---

Vas a construir un asistente que responde preguntas sobre los datos de una planta
de empaques plásticos que **no tiene SCADA**: todo entra a mano, en archivos que
alguien llena al cierre de cada turno.

**En esta fase hay interfaz, pero solo el chat.** Nada de gráficos, nada de
filtros, nada de tablero: una sola pantalla donde se pregunta y se ve al agente
consultar los datos. Todo eso llega en la fase 2, y llega sobre esto.

El chat es el deliverable, pero **el guion de consola se construye igual y se
prueba primero**. Es un diagnóstico, no un adorno: si algo se rompe en la consola,
el problema es del agente; si se rompe solo en el navegador, es de la interfaz.
Buscar en el sitio equivocado cuesta media hora que no tenemos.

**Al terminar** vas a poder abrir `http://localhost:8501`, preguntarle, y ver en
vivo qué herramienta consulta para cada cifra y sobre cuántas filas se paró.

---

## Las reglas que no se negocian

Si rompes una de estas, el resultado no es esta aplicación.

1. **Todo va en español neutro** — el código, los comentarios, los nombres de
   variable y los mensajes. Nada de voseo («pregunta», no «preguntá»). Los nombres
   de función son en español: `calcular_desperdicio`, no `calculate_waste`.

2. **Toda cifra que el asistente diga sale de una herramienta.** El modelo no suma,
   no promedia, no estima, no extrapola. Si falta un dato, llama a otra
   herramienta; si no hay herramienta, dice que no lo sabe.

3. **El bloque de trazabilidad lo arma el código, no el modelo.** Y las filas se
   cuentan por **unión de conjuntos**: si tres herramientas consultan las mismas
   28.000 filas, el bloque dice 28.000, no 84.000.

4. **Ningún número del negocio va escrito a mano en el código.** Ni fechas, ni
   umbrales, ni nombres de planta. Todo sale de los datos o del `.env`.

5. **Nunca inventes que verificaste algo.** Cuando este archivo dice «verifica X»,
   corre el comando y muestra la salida real. Si falla, arréglalo y vuelve a
   correrlo; no lo declares hecho.

---

## El stack, sin sustituciones

Ya está instalado (ver `00-preparacion-del-entorno.md`). Las versiones están fijadas en
`referencia/requirements.txt`: **no las resuelvas por tu cuenta**.

| Qué | Cuál |
|---|---|
| Lenguaje | Python 3.12 en `venv` |
| Agente | `strands-agents==1.50.2` — el decorador `@tool` saca el esquema del docstring |
| Modelo | **Claude Sonnet 5** |
| Cálculo | `pandas`, `numpy`, `statsmodels`, `scipy` |

### El modelo: Sonnet 4 está deprecado

Si algún material dice **Claude Sonnet 4**, está desactualizado: ese modelo está
deprecado y su fecha de retiro ya pasó, así que algo construido sobre él deja de
funcionar solo, sin que nadie toque una línea.

El identificador **no se escribe igual según por dónde se llegue**:

- Claude API directa → `claude-sonnet-5` (**sin** prefijo)
- Amazon Bedrock → `anthropic.claude-sonnet-5` (el prefijo `anthropic.` es de Bedrock)

A los modelos Claude recientes **no** se les pasa `temperature` ni `top_p`: los
rechazan.

**`MAX_TOKENS = 16_384`, y no 4.096.** Con 4.096 el chat funciona bien, pero más
adelante el reporte —que pide cuatro secciones sobre las cifras de seis gráficas—
se corta a mitad de frase con `MaxTokensReachedException`. No es la ventana de
contexto sino el **tope de escritura**, así que la solución es subir el tope y no
recortar el encargo.

---

## Los datos

Están en `datos/`, ya generados. **No escribas un generador**: los cinco CSV
llegan de la planta como llegan.

El esquema completo está en `referencia/esquema-de-datos.md` — **léelo antes de
escribir `carga.py`**. En esta fase solo se usan los tres del asistente de
desperdicio: `muestras_qc.csv`, `produccion_turno.csv`, `eventos_operacion.csv`.

Léelos siempre con **`encoding="utf-8-sig"`**, nunca `utf-8`: salen de Excel y
traen BOM, que sin eso se pega a la primera columna y la vuelve ilegible.

---

# Las cinco lecciones

Son el corazón de todo esto. **Cada una es una trampa en la que un análisis
ingenuo cae**, y el sistema tiene que estar construido para no caer.

## 1 · El desperdicio son DOS cosas que no se solapan

- **Scrap pesado**: lo que la planta ya mide, va a la báscula de rechazos.
- **Gramaje exceso**: material regalado *dentro de producto conforme*. La pieza
  pesa más que su objetivo, pasa la inspección y **se despacha**. No aparece en
  ningún reporte de scrap de la planta: es invisible para el sistema actual.

Se calcula `delta_medio × unidades_conformes`, **desglosado por línea y por SKU**
— nunca un promedio global, porque cada SKU tiene su propio peso objetivo y
promediar gramos de piezas de 3 g con piezas de 96 g no significa nada.

Solo cuentan las muestras con `veredicto == "conforme"`, y el delta se recorta en
cero (`.clip(lower=0)`): una pieza que pesa *menos* del objetivo no es un ahorro
que compense a otra que pesa de más, es otro problema.

**Repórtalos separados y sumados**, y di explícitamente que el segundo es
invisible para el sistema actual.

## 2 · Deriva y desviación sistemática se corrigen distinto

- **Deriva**: la máquina se desgasta, el peso sube con el tiempo → **mantenimiento**.
- **Setpoint desviado**: está calibrada en el número equivocado desde el
  principio, pero estable → **un ajuste**.

Recomendar lo contrario hace perder tiempo y plata.

Cómo se distinguen: **regresión sobre las medias diarias**, ponderada por el
número de muestras de cada día (`statsmodels.WLS`). Un día con 4 muestras no puede
pesar lo mismo que uno con 300. Se clasifica **por la pendiente**, no por el
promedio.

> **La trampa, y es la más fácil de pisar:** el setpoint se juzga por el
> **intercepto** de la regresión, no por la media de la serie. Una línea con
> deriva tiene una media alta *porque derivó*, y si la juzgas por la media la
> clasificas como setpoint desviado — que es exactamente el error que la lección
> quiere evitar.

> **Segunda trampa, aritmética.** El costo mensual proyectado de la deriva:
>
> ```python
> costo = (pendiente * 30) * (unidades_por_dia * 30) / 1000 * precio
> ```
>
> Los dos factores tienen que estar en la **misma unidad de tiempo**. Multiplicar
> los gramos de un mes por las unidades de un solo día da una cifra ~30 veces más
> chica — tan pequeña que nadie actuaría sobre ella.

## 3 · Un lote de resina sin muestra suficiente no es evidencia

Exige un mínimo de turnos (10 por defecto, configurable en el `.env`). Los lotes
que no llegan **se devuelven igual, con su `n` visible**. No se esconden: mostrar
por qué se descartaron enseña más que omitirlos.

Si el asistente menciona un lote, dice en cuántos turnos se basa. Los descartados
se pueden mencionar como pendientes de confirmar, **nunca como culpables**.

Usa `scipy.stats.ttest_ind` para decir si la diferencia es significativa. Un lote
puede tener el peor promedio y aun así no serlo.

## 4 · Una cavidad solo existe junto a su molde

La cavidad 3 del molde A y la cavidad 3 del molde B no tienen nada que ver.
Agrupar por número de cavidad sin el molde mezcla piezas de máquinas distintas.

Cuando se compara por cavidad, se agrupa por **molde + cavidad** y se devuelve una
advertencia diciéndolo. El número accionable es `exceso_vs_hermanas_g`: cuánto
pesa de más una cavidad **contra sus hermanas del mismo molde**.

> **La trampa aritmética:** al calcular el promedio de las hermanas hay que
> **excluir la cavidad que se está evaluando** — `(suma - propia) / (cuenta - 1)`.
> Incluirla diluye su propia desviación y el exceso sale más chico de lo que es.

## 5 · Las categorías de desperdicio se solapan

Un mismo turno puede tener cambio de color **y** paro no programado. Los
porcentajes **no suman 100 %** y jamás deben presentarse como una partición ni
como una torta.

Cada cifra es el **exceso sobre una línea base**, y la línea base son los turnos
sin transiciones.

> **La trampa está en el DENOMINADOR, y es silenciosa.** El porcentaje de cada
> categoría se mide contra el exceso de **toda la planta** sobre la línea base.
> Dividir entre la suma de las categorías —que es lo que sale natural— da 100 %
> exacto **por construcción**: la advertencia no se dispara nunca, los porcentajes
> parecen una partición prolija, y la lección desaparece sin que nada falle ni
> ninguna prueba se ponga roja.
>
> Devuelve las dos cifras con nombres distintos: `pct_del_exceso_de_planta` y
> `pct_de_lo_atribuido`. Las dos se usan más adelante.

---

# Qué construir en esta fase

```
.env                        (ya lo copiaste)
requirements.txt            copia de referencia/requirements.txt
.gitignore                  .venv/  .env  __pycache__/  .chroma/
app.py                      La interfaz: SOLO el chat.
.streamlit/config.toml      Copia de referencia/config.toml, tal cual.
assets/                     Ya está: el logo y el favicon.
src/
  config.py                 Parámetros desde el entorno. Cero cifras de negocio.
  carga.py                  Datos (dataclass congelado), preparar_*, filtrar, traza.
  calculos.py               LA ÚNICA FUENTE DE CIFRAS.
  trazabilidad.py           Registro de filas tocadas, por unión de conjuntos.
  herramientas.py           Las 7 @tool.
  agente.py                 Modelo, prompt del sistema, puente de streaming.
  estilo.py                 Tokens y hoja de estilos. Todavía sin paleta de gráficos.
  preguntar.py              Las mismas preguntas, por consola. Es el diagnóstico.
pruebas/test_calculos.py    Comprobaciones sobre los cálculos.
```

**Lo que NO se construye acá, a propósito:** gráficos, tablero, filtros, supuestos
en la barra lateral y el registro de agentes. Todo eso es la fase 2. Si te
descubres dibujando una barra, te saliste del encargo.

## `src/config.py`

Un dataclass **congelado** que lee todo del entorno. Ni un solo valor de negocio
escrito en el código:

```python
proveedor            = os.getenv("PROVEEDOR_LLM", "bedrock").strip().lower()
modelo_bedrock       = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-sonnet-5")
modelo_anthropic     = os.getenv("ANTHROPIC_MODEL_ID", "claude-sonnet-5")
region_aws           = os.getenv("AWS_REGION", "us-east-1")
modelo_embeddings    = os.getenv("MODELO_EMBEDDINGS", "intfloat/multilingual-e5-base")

precio_resina_usd_kg = float(os.getenv("PRECIO_RESINA_USD_KG", "1.85"))
tolerancia_peso_g    = float(os.getenv("TOLERANCIA_PESO_G", "0.15"))
umbral_deriva_g_dia  = float(os.getenv("UMBRAL_DERIVA_G_DIA", "0.01"))
min_turnos_lote      = int(os.getenv("MIN_TURNOS_LOTE", "10"))
umbral_z_anomalia    = float(os.getenv("UMBRAL_Z_ANOMALIA", "3.5"))
```

**Ningún nombre de planta, ninguna fecha y ningún resultado viven acá.**

## `src/carga.py`

`Datos` es un **dataclass congelado** con los tres marcos ya tipados. Sus métodos:

- `desde_marcos(marcos)` — construye desde diccionarios de DataFrame. Es lo que
  después permitirá mezclar archivos cargados con los de disco.
- `cargar()` — desde los CSV.
- `filtrar(**filtros)` — devuelve otro `Datos`, **recortando los tres archivos de
  forma coherente**. Es fácil que un filtro recorte las muestras y no la
  producción, y de ahí salen cocientes absurdos: los kilos de toda la planta
  divididos entre las piezas de una sola línea.
- `validar()` — mensajes accionables, no trazas.
- `marcos()` — vuelve a diccionarios.
- `traza(*fuentes)` — **devuelve los índices de las filas tocadas, no el conteo.**

Lo último importa: el registro de trazabilidad tiene que poder *unir* lo que
tocaron varias herramientas sin contar dos veces las mismas filas. Con conteos eso
es imposible; con conjuntos de índices es trivial. Por eso `filtrar()` **no
reindexa**: los índices originales son los que viajan.

Deriva acá, a nivel de fila y no como agregado: el `delta_g` de cada pieza contra
su objetivo, el `pct_scrap` de cada turno, y una etiqueta compuesta de molde +
cavidad que haga imposible agrupar por cavidad a secas.

El **nombre de la planta sale de la columna `planta`**, nunca del código.

## `src/calculos.py` — la única fuente de cifras

De acá sale **toda** cifra que la aplicación muestre o diga. Nadie más suma.

Cada función devuelve un **diccionario**, no un DataFrame. Las claves que empiezan
por `_` son para el código —series, mapas, índices de trazabilidad— y se filtran
antes de mandarle nada al modelo.

| Función | Lección |
|---|---|
| `calcular_desperdicio(datos, precio_usd_kg)` | 1 |
| `analizar_deriva(datos, precio_usd_kg)` | 2 |
| `rankear_lotes_resina(datos, min_turnos)` | 3 |
| `comparar_dimension(datos, dimension)` | 4 — `linea`, `sku`, `turno`, `molde`, `cavidad` |
| `atribuir_categorias(datos, precio_usd_kg)` | 5 |
| `detectar_turnos_anomalos(datos, umbral_z)` | el turno fuera de norma |

Y funciones de apoyo que ya vas a necesitar en la fase 2:
`distribucion_delta_peso`, `serie_costo_acumulado`, `mapa_linea_turno`,
`pareto_desperdicio`.

### `detectar_turnos_anomalos` usa z **robusto**

Mediana y MAD × 1.4826, **no** media y desviación estándar. El turno que buscamos
es tan extremo que *arrastra* la media y la desviación clásicas, y termina
escondiéndose a sí mismo. La mediana no se mueve.

### La regla de la salida

Toda función que haga un supuesto o tenga una limitación devuelve una de estas
claves: `advertencia`, `aviso`, `nota_metodo`, `nota_conservadora`. El prompt del
agente le ordena incorporarlas.

**Son las salvedades que hacen que la cifra aguante una pregunta incómoda.** Una
respuesta que da un número sin decir sobre qué se paró se cae en la primera
repregunta.

> **Dos funciones que miden lo mismo tienen que cuadrar, y hay que comprobarlo.**
> `serie_costo_acumulado` y `calcular_desperdicio` son funciones **distintas** que
> miden lo mismo: el final de la curva tiene que ser el total.
>
> Que la curva **reutilice** el delta por línea+SKU que ya calculó
> `calcular_desperdicio` en vez de rehacerlo, y que ese delta viaje **sin
> redondear** en una clave `_`. Sumar las cifras ya redondeadas de cada
> combinación desplaza el total y aparece una diferencia. Deja un `assert`: la
> diferencia tiene que ser 0,00.

## `src/trazabilidad.py`

```python
class Registro:
    def anotar(self, herramienta, traza):
        # UNIÓN DE CONJUNTOS de índices, no suma de conteos
        for fuente, indices in (traza.get("filas") or {}).items():
            self._filas.setdefault(fuente, set()).update(int(i) for i in indices)
```

**Esto es lo que evita el número inflado.** Sumando conteos diría el triple, y
quien conozca el archivo sabría que es mentira — y a partir de ahí no cree nada
más.

El bloque en markdown **lo arma el código** y se pega al final de la respuesta:

```
---
**Trazabilidad** *(generada por el código, no por el modelo)*
Rango consultado: **2026-02-08 → 2026-08-06**
Filas analizadas: **29.373** — 1.137 cierres · 28.236 muestras
Precio de resina aplicado: **1.85 USD/kg**
Herramientas ejecutadas: `calcular_desperdicio`, `atribuir_categorias`
```

`limpiar_para_modelo(resultado)` quita las claves con `_` antes de mandar nada al
modelo: son series y arreglos de índices que gastarían miles de tokens y además lo
tentarían a sumar a mano justo lo que las herramientas ya sumaron bien.

### Quién limpia el registro, y cuándo

El registro es **de una respuesta, no de la sesión**:

- **`configurar()` lo limpia**, y por eso vive a nivel de módulo y no dentro del
  contexto: así se puede consultar antes de configurar nada.
- **Cada pregunta reconfigura.** Si `configurar()` se llama una sola vez al
  arrancar, el bloque de la cuarta pregunta lista las herramientas y las filas de
  las **cuatro**. Es exactamente el número inflado que este bloque viene a evitar.

## `src/herramientas.py` — las siete

Con el decorador `@tool` de `strands`, que **saca el esquema del docstring y de
las anotaciones de tipo**. El docstring no es documentación: es la interfaz que el
modelo lee para decidir cuándo llamarla. Escríbelo pensando en eso.

| Herramienta | Para qué |
|---|---|
| `calcular_desperdicio` | Las dos mitades, separadas y sumadas |
| `analizar_deriva` | Deriva vs setpoint desviado, con su clasificación |
| `rankear_lotes_resina` | Lotes con evidencia + descartados con su `n` |
| `atribuir_categorias` | Exceso sobre línea base, con aviso de solapamiento |
| `comparar_dimension` | Línea, SKU, turno, molde, cavidad (con su molde) |
| `detectar_turnos_anomalos` | Z robusto |
| `buscar_notas_similares` | Marcador por ahora: devuelve un aviso de que aún no existe |

La séptima se construye completa en la fase 3. Déjala declarada y devolviendo
un aviso honesto —«el índice semántico no está disponible»— para que el agente
sepa que existe y no invente su contenido.

Todas devuelven `dict`, todas anotan la traza, y ninguna calcula: cada una llama a
`calculos.py`.

El modelo **no elige el recorte de datos ni el precio**: eso lo fija `configurar()`
desde fuera, y las herramientas reciben siempre la vista ya preparada.

## `src/agente.py`

### El modelo: dos caminos, uno solo de código

```python
def crear_modelo():
    if CONFIG.proveedor == "anthropic":
        from strands.models.anthropic import AnthropicModel
        llave = os.getenv("ANTHROPIC_API_KEY")
        if not llave:
            raise RuntimeError(
                "PROVEEDOR_LLM=anthropic pero no hay ANTHROPIC_API_KEY en el "
                "entorno. Ponla en el .env (que está en .gitignore)."
            )
        return AnthropicModel(
            client_args={"api_key": llave},
            model_id=CONFIG.modelo_anthropic,   # claude-sonnet-5, SIN prefijo
            max_tokens=MAX_TOKENS,
        )
    from strands.models import BedrockModel
    return BedrockModel(
        model_id=CONFIG.modelo_bedrock,          # anthropic.claude-sonnet-5, CON prefijo
        region_name=CONFIG.region_aws,
        max_tokens=MAX_TOKENS,
    )
```

### `callback_handler=None` no es opcional

```python
Agent(model=..., tools=..., system_prompt=..., callback_handler=None)
```

Por omisión `Agent` instala un manejador que va imprimiendo la respuesta a stdout
por su cuenta. Como el texto se consume por `stream_async`, dejarlo activo hace
que cada trozo salga **dos veces** y en consola se vea como una respuesta
entrelazada consigo misma.

### El prompt del sistema

**No contiene ni una cifra.** Lo único concreto que lleva es el inventario de la
planta —qué líneas, qué SKU con su peso objetivo, qué turnos, qué rango de
fechas— y eso se deriva de los CSV al arrancar.

Un número en el prompt es un número que nadie puede auditar y que el modelo
repetirá con total seguridad cuando los datos ya hayan cambiado.

Estructura:

1. **Quién eres** — analista de desperdicio, responde en español, con la precisión
   de quien sabe que cualquiera en la sala puede pedirle verificar la cifra.
2. **La planta**, derivada de los datos.
3. **La regla que no se negocia** — toda cifra sale de una herramienta.
4. **Cómo interpretar lo que devuelven las herramientas** — las cinco lecciones,
   escritas como instrucciones de lectura.
5. **Cómo escribir** — primero la respuesta directa en una o dos frases, después
   la evidencia con las cifras tal como vienen, al final qué hacer distinguiendo
   ajuste de mantenimiento.
6. **Prohibición explícita de escribir el bloque de trazabilidad**: lo agrega el
   código. Un bloque de auditoría redactado por el modelo tendría exactamente el
   problema que viene a resolver.

### El puente de streaming async → sync

`stream_async` es asíncrono y ni la consola ni Streamlit lo son. Un hilo aparte
con una `queue.Queue` y un centinela de fin. **Se escribe una sola vez y lo usan
los dos**: la consola y el chat consumen exactamente el mismo generador.

Formas de evento verificadas contra el código de `strands`:

- texto → `{"data": "trozo de texto"}`
- herramienta → `{"current_tool_use": {"toolUseId": ..., "name": ...}}`

`current_tool_use` **se repite en cada delta** mientras se arman los argumentos.
Emítelo una sola vez por invocación, recordando el último `toolUseId` visto.

Emite dos clases de evento: `{"tipo": "herramienta"}` y `{"tipo": "texto"}`. Ver
al agente consultar los datos es lo que deja claro que no está improvisando.

## `src/preguntar.py` — el diagnóstico, y se hace primero

Corre las preguntas por consola, imprimiendo qué herramienta se ejecuta y, al
final, el bloque de trazabilidad.

**Constrúyelo y córrelo antes de tocar la interfaz.** Es lo que separa un
problema del agente de un problema de Streamlit, y no se borra después: queda
como la forma rápida de probar el agente sin abrir el navegador.

Las cuatro preguntas de ejemplo **no llevan fechas escritas a mano**. El rango de
los datos es el que es, y una pregunta con la fecha adentro se rompe el día que
los archivos cambien. En vez de «el 18 de junio», se pregunta «cuál fue el peor
turno del período» — que además es la demostración que importa.

1. «¿Cuánto material estamos desperdiciando y de qué tipo es? Separa lo que la
   planta ya mide de lo que no.» → lección 1
2. «¿Qué líneas hay que recalibrar y cuáles necesitan mantenimiento? No me las
   mezcles.» → lección 2
3. «¿Hay algún lote de resina que se comporte peor que los demás?» → lección 3
4. «¿Cuál fue el peor turno del período y qué pasó ahí?» → el turno fuera de norma

## `pruebas/test_calculos.py`

Sin framework: un guion que imprime `[PASA]`/`[FALLA]` y sale con código distinto
de cero si algo falla.

**No comprueban que el código corra: comprueban que recupere los patrones que hay
en los datos.** Es la diferencia entre una prueba que se siente bien y una que
sirve. Al menos:

- Las dos mitades del desperdicio existen, se suman sin solaparse, y el desglose
  por línea+SKU reconstruye el total.
- Solo se cuentan muestras conformes, y ningún delta medio es negativo.
- Se detecta la línea que **deriva** y la que tiene el **setpoint desviado**.
- **El setpoint se juzga por el intercepto, no por la media**: comprueba que la
  línea con deriva tiene la media más alta y *aun así* no se clasifica como
  setpoint desviado. Esta es la prueba que más enseña.
- El costo de la deriva está escalado a un mes completo.
- Los lotes con evidencia superan el mínimo; los descartados vienen con su `n`.
- Los porcentajes de categoría **pasan del 100 %** y hay advertencia.
- El promedio de las cavidades hermanas **excluye** a la propia.
- El z robusto encuentra el turno más extremo.
- `filtrar()` recorta los **tres** archivos de forma coherente.

**Si una prueba falla, lee la cifra que imprime antes de tocar nada.**

---

# La interfaz de esta fase: solo el chat

Con la consola en verde, recién ahora se dibuja. Son tres piezas: el sistema
visual mínimo, el armazón de la página y la pantalla de chat propiamente dicha.

**Nada de gráficos, nada de filtros, nada de pestañas.** El tablero no es que se
deje para después por falta de tiempo: es que un chat que ya responde bien y dice
de dónde saca cada cifra **ya es una aplicación honesta**, y conviene verla
funcionar antes de agregarle superficie.

## `src/estilo.py` — lo mínimo del sistema visual

### Qué es y qué no es

shadcn/ui **no se puede instalar** en Streamlit: es un catálogo de componentes
React sobre Tailwind, y Tailwind resuelve sus clases en tiempo de build.

Lo portable —y de donde viene el aspecto— son sus **tokens**: la escala neutra
`zinc`, borde de 1 px en vez de sombra, radios de 0.5rem, tipografía Inter. Esos
tokens van en `.streamlit/config.toml`, que es tema **nativo**: cópialo de
`referencia/config.toml` tal cual. El CSS a mano se reserva para lo poco que el
tema nativo no alcanza.

> Ese archivo trae también una paleta de gráficos. Déjala ahí y no la toques: se
> usa en la fase 2, cuando haya algo que pintar.

### La trampa que condiciona todo este archivo

**Streamlit 1.61 no expone NINGUNA variable CSS.** Sus estilos son CSS-en-JS con
los valores ya interpolados, así que cualquier `var(--algo, #reserva)` que
escribas usa **siempre** el valor de reserva.

Consecuencia real: en modo oscuro toda la interfaz usaba los colores claros y
había cajas con **texto blanco sobre fondo blanco**. La hoja de estilos tiene que
ser una **función de Python que recibe el modo** e interpola los hex reales:

```python
def css(modo_oscuro: bool) -> str:
    t = tokens(modo_oscuro)
    return f"""<style> ... background: {t['fondo']}; ... </style>"""
```

El modo activo se guarda como **estado de módulo** en `estilo.py`, para que nadie
tenga que pasarlo por parámetro. Eso asume **un proceso por persona**, que es
exactamente la restricción de este taller. Escríbelo en el comentario.

**Quién decide el modo: el `.env`, no el sistema operativo.** La variable `TEMA`
(`oscuro` | `claro` | `auto`) lo fija, y **por defecto es `oscuro`**. Con `auto`
—que es lo que hace Streamlit si lo dejas solo— la misma aplicación se vería
clara en un computador y oscura en otro, y proyectada en una sala eso no se puede
elegir en el momento.

> **Y no basta con la hoja de estilos propia.** Los controles nativos de
> Streamlit los pinta `.streamlit/config.toml`, que no lee el `.env`. Ahí el
> juego de colores oscuro va en el `[theme]` de nivel superior y **no se define
> ninguna variante**: definir `[theme.dark]` y `[theme.light]` es justamente lo
> que hace que Streamlit siga la preferencia del sistema operativo, y
> `base = "dark"` no alcanza para forzarlo porque los colores explícitos del
> nivel superior le ganan a la base.

### `key=` es el único ancla CSS estable

Streamlit publica `key="x"` como clase `st-key-x`. El alto, el borde y el resto
los pone en clases generadas (`st-emotion-cache-*`) que **cambian entre
versiones**. **Nunca apuntes a `st-emotion-cache-*`.** Si necesitas estilar un
contenedor, dale un `key` aunque no necesites su estado.

### Los tokens

```python
CLARO = {
  "fondo": "#FFFFFF", "superficie": "#FFFFFF", "muted": "#F4F4F5",
  "borde": "#E4E4E7", "texto": "#09090B", "texto_suave": "#71717A",
  "primario": "#EB652B", "sobre_primario": "#1C0A02",
}
OSCURO = {
  "fondo": "#09090B", "superficie": "#09090B", "muted": "#18181B",
  "borde": "#27272A", "texto": "#FAFAFA", "texto_suave": "#A1A1AA",
  "primario": "#EB652B", "sobre_primario": "#1C0A02",
}
```

En la fase 2 este diccionario crece con los tokens que solo usan los
gráficos (`grilla`, `neutral_serie`) y con las dos paletas verificadas.

### La marca manda sobre el color; la accesibilidad manda sobre la marca

El naranja **#EB652B** es el del logo, **medido** sobre la imagen: son el 66 % de
sus píxeles opacos. Sirve en los dos modos porque su luminosidad OKLCH (L = 0,666)
cae dentro de las dos bandas permitidas.

**La tinta encima no es blanca.** Blanco sobre ese naranja da 3,27:1, insuficiente
para texto. El casi negro cálido #1C0A02 da 5,88:1. Por eso los botones primarios
y la pastilla de la pregunta llevan **letra oscura**: no es una preferencia
estética.

Los enlaces tampoco usan el naranja del logo tal cual: `#C13D00` en claro
(5,34:1) y `#FA7A48` en oscuro (7,52:1).

### Los patrones de componente que hay que reproducir

| Componente shadcn | Cómo se ve acá |
|---|---|
| **Card** | Borde de 1 px, radio 0.5rem, **sin sombra**. La caja del chat y la ficha de la planta |
| **SidebarGroupLabel** | Versalitas: 0.6875rem, peso 600, `letter-spacing: 0.06em`, mayúsculas, tinta suave |
| **Muted surface** | La barra lateral un tono por debajo del lienzo |
| **Badge** | Las sugerencias del chat: borde 1 px, radio 999px, 0.78rem |
| **Button** | Primario = naranja con **letra oscura**. Terciario = sin borde, solo tinta |
| **Separator** | 1 px. Debe verse **también con la barra lateral cerrada** |
| **Avatar** | El del asistente: círculo de 1.75rem, borde 1 px, ícono en **tinta de texto**, no en el gris del borde |

## `app.py` — el armazón

Una sola pantalla. En la barra lateral, **solo la ficha de la planta**: nombre,
período y cuántas filas tiene cada archivo. Todo eso sale de los datos, nunca
escrito a mano — el nombre de la planta se lee de la columna `planta`.

**Sin título de página encima del chat.** No aporta nada y empuja el contenido
hacia abajo.

El logo va con `st.logo("assets/next-makers-log.png", size="medium")`, que lo
coloca arriba de la barra lateral por sí solo. El favicon es `assets/favicon.png`
—la marca recortada, no el logotipo: a 32 px un logotipo con texto no es legible.

### Caché

Streamlit reejecuta el script entero en cada interacción. Sin caché, cada mensaje
volvería a leer los CSV desde cero.

- `@st.cache_data` para los archivos
- `@st.cache_resource` para el objeto de datos y el agente

Los parámetros que no son *hashables* llevan `_` delante del nombre para que
Streamlit los ignore al calcular la clave: `def _agente(clave, _datos)`.

> **Trampa que cuesta media hora: los módulos quedan cacheados.** Streamlit no
> recarga un módulo ya importado que esté en `sys.modules`. Si editas `estilo.py`
> con la app corriendo, el proceso sigue usando la versión vieja y tu CSS nuevo
> **no aparece**, aunque el archivo en disco esté bien. **Cuando cambies un módulo
> de estilo o de configuración, reinicia el proceso.**

### Iconos: Material Symbols, nunca unicode

```python
st.button("Limpiar conversacion", type="tertiary", icon=":material/delete_sweep:")
```

Un emoji o un carácter unicode se dibuja con la fuente del sistema: se ve distinto
en macOS, Windows y Linux, cambia de ancho y rompe la alineación. Solo se
resuelven en **etiquetas de widget**, no dentro de HTML crudo: un `:material/mail:`
dentro de un `<a>` escrito con `unsafe_allow_html=True` sale como texto literal.

---

# La pantalla de chat

Es donde el taller se juega su credibilidad: acá se ve al agente consultar los
datos en vivo.

## El problema de partida

`st.chat_input` **suelto se ancla al pie de la ventana, pero dentro de un
contenedor se dibuja en línea**. En la fase 2 esta pantalla va a vivir dentro
de una pestaña, y ahí el campo de entrada termina **arriba** de los mensajes. Se
construye desde ya con la estructura que aguanta las dos situaciones.

## La estructura, de fuera hacia adentro

Todo dentro de **una sola caja con borde**, para que se lea como un componente:

```python
with st.container(border=True, key="caja_chat"):
    # 1. barra de acciones (solo si ya hay conversación)
    # 2. transcripción, con su propio scroll
    # 3. sugerencias (solo si NO hay conversación)
    # 4. st.chat_input
```

La caja tiene **alto fijo** —`height: calc(100vh - 118px) !important`— y la
transcripción es lo elástico (`flex: 1 1 auto`), de modo que el campo de entrada
siempre toque el pie.

> **El alto es FIJO, jamás adaptativo.** Hacer que dependa de si hay conversación
> encoge la caja **justo cuando el agente empieza a responder**, que es el peor
> momento posible para mover el layout.

> **Streamlit envuelve cada contenedor en un `stLayoutWrapper` y al envoltorio es
> al que le pone el alto.** Estirar solo el bloque de adentro no sirve: hay que
> soltar los dos, y además fijarles `flex: 0 0 auto`, porque si no el
> `flex-shrink` los encoge de vuelta al tamaño del contenido.
> ```css
> [data-testid="stLayoutWrapper"]:has(> .st-key-caja_chat) {
>   height: calc(100vh - 118px) !important; flex: 0 0 auto !important;
> }
> .st-key-caja_chat [data-testid="stLayoutWrapper"]:has(> .st-key-transcripcion) {
>   flex: 1 1 auto !important; height: auto !important; min-height: 0 !important;
> }
> ```

### Dos cosas de Streamlit que rompen esta estructura

**1. Un `st.container()` vacío NO llega al DOM.** Sin conversación, el contenedor
de la transcripción no existe, la caja se queda sin su elemento elástico y el campo
de entrada sube al tope. Métele un hueco de 1 px cuando no hay mensajes:

```python
if not st.session_state[clave_chat]:
    st.markdown('<div class="hueco-transcripcion"></div>', unsafe_allow_html=True)
```

**2. `st.chat_input` se estira dentro de un contenedor flex.** No basta con fijar
el `flex` de su contenedor: sus divisiones internas llevan `flex: 1 1 0%` y
arrastran el `textarea` hasta ~170 px, o sea seis líneas vacías.

```css
.st-key-caja_chat [data-testid="stChatInput"] > div,
.st-key-caja_chat [data-testid="stChatInput"] > div > div { flex: 0 0 auto !important; }
.st-key-caja_chat [data-testid="stChatInputTextArea"] {
  height: auto !important; min-height: 1.5rem !important; max-height: 7.5rem !important;
}
```

El `max-height` no es defensivo: es el comportamiento correcto de un chat.

## Los mensajes: patrón asimétrico

`st.chat_message` dibuja avatar y texto plano, sin burbujas: no lee como una
conversación.

- **La pregunta**: pastilla a la derecha, fondo del primario, radio
  `1rem 1rem 0.25rem 1rem`, ancho máximo 70 %, avatar del usuario oculto.
- **La respuesta**: texto corrido con su avatar a la izquierda. Meterla en burbuja
  sería un error — son reportes largos, con listas, tablas y bloques de código.

### Cuatro defectos de render y su causa

**1. El texto se sale del fondo de color.** Streamlit le pone a
`stMarkdownContainer` un **margen inferior negativo de 15 px** para compensar el
margen de los párrafos. Al quitarle el margen al párrafo de la pastilla, esa
compensación se queda sin contraparte. **Donde anules el margen del párrafo, anula
también el negativo del contenedor.**

**2. La pastilla sale centrada** aunque la fila tenga `justify-content: flex-end`.
Se resuelve con `margin-left: auto; margin-right: 0` sobre el contenido, que no
depende de quién gane la regla de la fila.

**3. Desborde horizontal de ~34 px** — exactamente el ancho del avatar más su
separación. El ancho se reparte **distinto según el rol**: la respuesta encoge
(`flex: 1 1 0; min-width: 0`) para hacerle sitio al avatar; la pregunta mide lo
que mide su texto (`flex: 0 0 auto`).

**4. El ícono del asistente casi no se ve**: iba en el gris del borde. Va con la
tinta del texto.

### Nada de scroll horizontal

Las palabras largas se parten donde toque —un id de lote no tiene espacios— y lo
que de verdad no se puede partir hace **su propio scroll adentro**:
`overflow-wrap: anywhere` en párrafos y celdas, `overflow-x: auto` en `pre` y
tablas.

Tipografía: 14 px de base (no los 15 de Streamlit), interlínea 1.65, y **títulos
discretos** — una respuesta trae subtítulos, y a 24 px compiten con la interfaz.

## Las sugerencias

Las cuatro preguntas de ejemplo —las mismas de `preguntar.py`—, **dentro de la
caja** y **se lanzan al hacer clic**: una lista para copiar y pegar obliga a un
paso que no aporta nada.

```python
pendiente = st.session_state.pop(clave_pendiente, None)   # POP, y ANTES de dibujar
```

El `pop` antes de dibujar es lo que evita que **el mismo clic se procese dos
veces**.

Van como pastillas compactas en fila (`st.container(horizontal=True)`), no en
rejilla: una rejilla reservaba media caja para cuatro botones y le robaba el
espacio a la conversación. Solo se muestran cuando no hay conversación.

## El streaming y el estado en vivo

```python
with transcripcion, st.chat_message("assistant"):
    estado = st.status("Pensando…", expanded=True)
    def flujo():
        for ev in iterar_respuesta(agente, pregunta):
            if ev["tipo"] == "herramienta":
                estado.write(f":material/build: `{ev['nombre']}`")
                estado.update(label=f"Ejecutando {ev['nombre']}…")
            else:
                yield ev["texto"]
    texto = st.write_stream(flujo())
```

Es el mismo puente de streaming que ya usa la consola: `stream_async` es
asíncrono y ni la consola ni Streamlit lo son. **Ver qué herramienta se ejecuta
mientras corre es medio taller**: es lo que deja claro que el agente no está
improvisando.

Al final, el **bloque de trazabilidad**, que lo arma el código. Y `configurar()`
se llama **una vez por pregunta**, igual que en la consola: si se llamara una sola
vez al arrancar, el bloque de la cuarta pregunta listaría las filas de las cuatro.

## Un fallo del modelo no puede tumbar la interfaz

El texto se acumula **fuera** del `try`, y el error se guarda en su propia
variable —Python borra el nombre de `except ... as exc` al salir del bloque:

```python
fallo, texto = None, ""
try:
    texto = st.write_stream(flujo())
except Exception as exc:
    fallo = exc
```

**Caso especial `already processing`:** el agente vive en `cache_resource` y
sobrevive a un F5. Si alguien recarga mientras el modelo escribe, la petición
vieja sigue en curso y la nueva choca. No es culpa de quien preguntó: descarta el
agente trabado (`_agente.clear()`) y reintenta **una vez**, en silencio.

El mensaje de error dice, siempre, que **los datos y los cálculos no dependen del
modelo**: las cifras son las mismas y se pueden volver a pedir.

---

## Verificación de esta fase

Primero por consola, que es donde se diagnostica. Corre esto y **pega la salida
real**:

```bash
.venv/bin/python -m pruebas.test_calculos
.venv/bin/python -m src.preguntar "¿Cuánto material estamos desperdiciando y de qué tipo es?"
```

Lo que tiene que verse:

1. Las comprobaciones **todas en verde**.
2. El agente llamando herramientas, una línea por invocación.
3. El bloque de trazabilidad al final.
4. **Las filas analizadas no superan el total de filas de los archivos.** Si lo
   superan, estás sumando conteos en vez de unir conjuntos: `muestras_qc.csv` tiene
   28.236 filas y `produccion_turno.csv` 1.137, así que ningún bloque puede decir
   más de 33.303 en total.

Después la interfaz:

```bash
.venv/bin/streamlit run app.py --server.port 8501
```

Con la app corriendo:

1. **Abre en modo oscuro**, sin importar cómo esté configurado el sistema
   operativo. Sin excepción en pantalla y **cero trazas en consola al arrancar**.
2. **La caja del chat llega al pie de la ventana** y su alto **no cambia** cuando
   el agente empieza a responder.
3. Clic en una sugerencia → la pregunta se lanza sola y aparecen los dos mensajes.
4. La pastilla de la pregunta va **a la derecha** y el texto queda **dentro** del
   fondo de color.
5. Una respuesta larga con tablas **no produce scroll horizontal**.
6. Se ve el nombre de la herramienta mientras corre, y el bloque de trazabilidad
   al final — **el mismo que imprimió la consola, con las mismas cifras**.
7. Ningún texto oscuro sobre fondo oscuro ni blanco sobre blanco, tampoco al
   pasar el mouse sobre un botón.
8. Pon `TEMA=claro` en el `.env` y comprueba que la hoja de estilos propia
   cambia. **Los controles nativos NO van a cambiar**: eso confirma que el tema
   vive en dos sitios y que hay que tocar los dos. Vuelve a dejarlo en `oscuro`.

Y para jugar antes de seguir: cambia `PRECIO_RESINA_USD_KG` en el `.env`, reinicia
la app, vuelve a preguntar, y mira cómo cambia la cifra en dólares y no la de
kilos.
