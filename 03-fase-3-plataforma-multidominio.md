# Fase 3 · Plataforma multidominio y reportería

> **Cómo se usa.** Pega este archivo entero en el mismo agente de código, sobre lo
> que construiste en las fases 1 y 2.

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

Ya tienes una aplicación completa de un asistente. Ahora vas a comprobar si el
contrato del registro sirve de verdad: **agregar un segundo asistente de un
dominio completamente distinto sin tocar `app.py`.**

Y de paso, las dos piezas que convierten la demostración en algo entregable: la
búsqueda semántica sobre el texto libre y un reporte que se puede mandar por
correo.

**El orden importa.** Si se acaba el tiempo, lo que falte tiene que ser lo menos
valioso:

1. **La búsqueda semántica** — completa la séptima herramienta que dejaste marcada.
2. **El segundo asistente** — el momento que justifica todo el contrato.
3. **Las dos pestañas que faltan** — Datos y Generar reporte.

---

# 1 · La búsqueda semántica

## Para qué sirve, y para qué no

**Solo para el texto libre.** Un supervisor escribe «arranque con molde tibio»,
otro «la máquina salió fría», otro «primeras cajas con rebaba» — tres textos sin
una palabra en común y el mismo problema. Eso es lo único que un embedding resuelve
y una consulta con `LIKE` no.

**Nunca para números.** Un embedding de «4.084 kg» no significa nada; ese número se
suma, no se busca por parecido. **Escríbelo en el código y en el README**, porque
es la confusión más común al meter una base vectorial en un proyecto de datos.

La herramienta `buscar_notas_similares` **no cuenta nada**. Sirve para «¿ha pasado
esto antes?» y para mostrar que varias personas reportaron lo mismo con palabras
distintas. Si alguien pregunta *cuánto*, la respuesta viene de una función de
cálculo.

Las únicas columnas que se indexan son las de texto libre: `nota_supervisor` y
`descripcion` en el asistente de desperdicio, `comentario_operario` y
`descripcion` en el de paradas.

## El modelo y sus prefijos asimétricos

`intfloat/multilingual-e5-base` **exige prefijos distintos** para lo que se indexa
y para lo que se consulta, y sin ellos la calidad se degrada de forma
**silenciosa** — no falla, simplemente devuelve peores vecinos:

- lo que se indexa lleva `passage: `
- lo que se consulta lleva `query: `

`chromadb` expone exactamente el gancho que hace falta:

```python
class FuncionE5(EmbeddingFunction):
    def __call__(self, input):        # indexado
        return motor().codificar([f"passage: {t}" for t in input])
    def embed_query(self, input):     # consulta
        return motor().codificar([f"query: {t}" for t in input])
```

Ese gancho de dos métodos es el que hace falta; una sola función para ambos lados
desperdicia la mitad de lo que el modelo sabe hacer. `chromadb` 1.5 además pide
que la clase implemente `name()`, `get_config()` y `build_from_config()`.

## Se embebe por texto distinto, no por fila

Si 40 turnos comparten la nota «sin novedad», eso es **un** vector, no 40. Embeber
por fila multiplica el costo y llena los resultados de duplicados.

Guarda junto a cada texto las filas donde aparece, para poder devolver cuántas
veces se escribió algo parecido — que es dato, aunque el conteo no venga del
modelo.

## En macOS Intel el camino normal NO existe

Y no es algo que se arregle configurando. PyPI publica `torch` **hasta 2.2.2** para
`macosx x86_64` —PyTorch dejó de compilar para esa plataforma— y ese binario está
construido contra NumPy 1.x, mientras que este stack fija `numpy==2.5.1` porque
`pandas 3` lo exige. Cualquier llamada a `encode` termina en «RuntimeError: Numpy
is not available».

La salida fácil sería degradar la búsqueda semántica. No se hace: es el único
patrón que justifica los embeddings en todo el proyecto. Se usa **el mismo modelo
por otro camino** — e5 publica su exportación a ONNX en su propio repositorio
(`onnx/model.onnx` y `onnx/tokenizer.json`), y `onnxruntime` y `tokenizers` ya
están en el entorno.

Los dos motores tienen que hacer **exactamente lo mismo**: los mismos prefijos,
*mean pooling* sobre la máscara de atención y normalización L2. Si no, los vectores
del índice y los de la consulta no viven en el mismo espacio.

```python
@functools.lru_cache(maxsize=1)
def motor():
    try:
        # El intento fallido escupe cientos de líneas por stderr que se leen como
        # errores de la aplicación sin serlo. Se silencian, y el motivo queda
        # guardado en el motor de respaldo por si hay que mostrarlo.
        with warnings.catch_warnings(), contextlib.redirect_stderr(io.StringIO()):
            warnings.simplefilter("ignore")
            return _MotorTorch()
    except Exception as error:
        return _MotorOnnx(motivo=str(error))
```

**`sentence_transformers` no se importa a nivel de módulo en ninguna parte**, solo
dentro de ese `try`. Un import arriba del archivo tumbaría la aplicación entera en
esas máquinas.

El modelo se carga una sola vez con `functools.lru_cache`: pesa más de un gigabyte
y los dos asistentes lo comparten.

## El módulo es genérico desde el principio

No sabe de desperdicio ni de paradas: recibe qué columnas de qué marcos llevan
texto.

```python
recopilar_textos(marcos, columnas)
construir_indice(marcos, columnas, coleccion, forzar=False)
buscar_notas(buscador, marcos, consulta, k, campos_ejemplo)
```

## El índice no puede tumbar la aplicación

Si `chromadb` o el modelo fallan, **el resto tiene que seguir funcionando**: el
tablero y las seis herramientas de cálculo no dependen de esto. Captura la
excepción, guarda el mensaje y muéstralo como advertencia en la barra lateral.
Nada de una traza en pantalla completa por una pieza opcional.

Ahora completa `buscar_notas_similares`, que en la fase 1 quedó devolviendo un
aviso.

**Compruébalo así:**

```bash
.venv/bin/python -m src.preguntar "¿Ha pasado antes algo parecido a un arranque con el molde frío?"
```

La respuesta debe traer notas con palabras **distintas** a las de la pregunta. Si
solo trae coincidencias literales, revisa que los prefijos estén puestos y en el
lado correcto.

---

# 2 · El segundo asistente: paradas no planeadas

## Por qué existe

Para probar que la abstracción sirve. Es **deliberadamente distinto** del primero:
minutos en vez de gramos, máquinas en vez de SKU, COP/hora en vez de USD/kg, y una
partición real de causas en vez de categorías que se solapan.

Si los dos fueran parecidos, la abstracción no probaría nada. **`app.py` no se
toca**: si te ves editándolo, algo del contrato quedó corto y hay que arreglar el
contrato, no la interfaz.

Sus fuentes son `downtime_log.csv` y `mantenimiento_historico.csv` (ver
`referencia/esquema-de-datos.md`). Va en `src/paras/`, con la misma estructura:
`carga.py`, `calculos.py`, `herramientas.py`, `graficos.py`, `agente.py`,
`preguntar.py`.

## El hallazgo que define este agente

**La fecha del turno no es la fecha del calendario.**

El turno de noche va de 22:00 a 05:59 y pertenece al día en que empezó. Una parada
a las 02:00 del sábado es del turno de noche del **viernes**.

```python
madrugada_de_turno_noche = (p["turno"] == "noche") & (hora < 6)
p["fecha_turno"] = p["fecha"] - pd.to_timedelta(
    madrugada_de_turno_noche.astype(int), unit="D")
```

Sin esta derivación de tres líneas, el patrón fuerte del dataset **aparece partido
entre dos columnas contiguas del mapa y se lee como ruido**. Con la fecha del
turno queda en una sola celda y la prueba estadística lo confirma.

Es la lección de este agente: **una derivación de tres líneas es la diferencia
entre encontrar el patrón y no verlo.** El mapa día × turno tiene que ir sobre
`fecha_turno`, y el filtro de fechas también.

## Clasificar causas cuando falta el código de falla

Una de cada cuatro filas trae el código vacío y solo el comentario del operario.

**El vocabulario se construye desde el propio dataset, no desde la intuición.** Se
cruzan las palabras del comentario con la `categoria_falla` de las filas que sí la
tienen, y se ve qué categoría le corresponde de verdad a cada palabra.

> El caso que lo enseña: **«tolva» parece materia prima.** En este dataset, todas
> las filas que la mencionan y además traen categoría son **operativas**.
> Corregirlo por el dato y no por la intuición baja mucho las filas sin clasificar.

Cada palabra aporta **una unidad de evidencia repartida según cómo se reparte de
verdad** en el archivo. Descartar las palabras repartidas —quedarse solo con las
que apuntan a una sola categoría— parece más limpio, pero deja fuera justamente
las que vuelven ambiguo a un comentario, y entonces la marca de ambigüedad no se
activa nunca.

Marca cada fila con `categoria_origen` (código o comentario) y `comentario_ambiguo`,
y **reporta en el pie del gráfico qué porcentaje se infirió del comentario**. Es
una medida de calidad del dato que quien lee tiene derecho a ver.

## Las nueve herramientas

`resumen_de_paras`, `rankear_causas`, `detectar_patron_recurrente`,
`comparar_lineas`, `analizar_microparos`, `cuantificar_ahorro`,
`generar_reporte_handoff`, `consultar_maquina`, `buscar_comentarios_similares`.

Cuatro decisiones de método que hay que respetar:

**`detectar_patron_recurrente` compara contra la actividad de la planta**, no
contra un promedio plano. Si la planta corre menos los domingos, tener menos
paradas el domingo no es un hallazgo. Usa `scipy.stats.binomtest` contra la
actividad real de esa celda día × turno. La exposición hay que aproximarla —el
archivo no trae el calendario de operación— y **eso se dice en `nota_metodo`**.

**`comparar_lineas` compara perfil, no volumen.** Una línea que corre el doble
tiene el doble de paradas y eso no dice nada. Devuelve horas **por día** y número
de máquinas, y el pie lo advierte.

**`analizar_microparos` devuelve un dato honesto e incómodo.** Microparada = menos
de 5 minutos. La clave `si_fuera_una_causa_ocuparia_el_puesto` responde *«si
juntáramos todas las microparadas en una sola causa, ¿en qué puesto del Pareto
quedaría?»* — que es la pregunta que importa y evita exagerarlas. Son muchísimas en
cantidad y pocas en horas: contarlas por cantidad las hace parecer el problema
principal cuando no lo son.

**`cuantificar_ahorro` solo cuenta patrones confirmados**, solo el exceso sobre la
tasa esperada, y **penaliza la probabilidad de éxito si ya se intentaron
preventivos** sobre esa máquina: si el preventivo ya se hizo y el problema sigue,
la probabilidad de que funcione esta vez es menor.

## Los seis gráficos

Pareto (con curva acumulada), torta de causas, horas por línea, evolución semanal,
mapa día × turno sobre `fecha_turno`, y top de máquinas.

### El Pareto lleva curva acumulada acá y no en el otro agente

**No es una inconsistencia, y hay que escribirlo en el código:**

- En **paradas** las causas son una partición real —cada parada pertenece a
  exactamente una categoría— así que el acumulado suma 100 % y el 80/20 se lee.
- En **desperdicio** las categorías se solapan, y una curva acumulada contra el
  total afirmaría algo falso.

### Color

Este tablero usa la escala **monocromática cálida**, no la categórica de seis
tonos: seis colores saturados en un tablero de marca naranja se leen chillones.

Como esa escala **no identifica por leyenda** con más de tres categorías, los dos
gráficos que la usan con seis llevan **etiquetas directas**:

- **Torta**: nombre y porcentaje sobre cada gajo con peso suficiente. El color
  armoniza; el nombre identifica. Es lo que hace legítima una torta monocromática.
- **Área apilada**: es el mejor caso de la rampa —bandas contiguas que se comparan
  contra su vecina— y conserva la leyenda.
- **Top de máquinas**: colorea por línea, y son tres, así que los pasos se reparten
  a lo ancho y ahí el color sí identifica solo.

**«Indeterminada» va en gris**: significa «no sabemos qué pasó», no es una causa
más.

## Registrarlo

Escribe su `AgenteDef` y agrégalo al diccionario `AGENTES`. **Eso es todo lo que
debería hacer falta.** Sus métricas: horas de paro, costo, paradas registradas y
porcentaje de microparadas. Su supuesto: el costo de paro en COP/hora. Sus filtros:
rango de fechas, línea, máquina, turno y categoría de falla.

**Comprueba el hallazgo:**

```bash
.venv/bin/python -c "
from src.paras import carga, calculos
d = carga.cargar()
r = calculos.distribucion_turno(d, 2_000_000)
print(r['_mapa'].sort_values('horas', ascending=False).head(3))
"
```

La celda más alta tiene que ser **una sola** combinación día × turno. Si el pico
aparece repartido entre dos días contiguos, `fecha_turno` no se está aplicando.

---

# 3 · Las dos pestañas que faltan

## La pestaña Datos

Es la pieza que convierte una demostración en una herramienta: sin ella, el
asistente solo sabe hablar del archivo que le tocó.

**Nada de esto se escribe a mano por agente.** Cada fuente ya declara sus campos en
el registro (fase 2), y de esa declaración salen solos el validador de CSV, el
formulario de captura y la lista de columnas esperadas.

> **Regla de oro, y dila en la interfaz, arriba de todo:** los cambios valen **para
> esta sesión**. El tablero y el chat los ven de inmediato, porque los dos leen del
> mismo objeto de datos. **Los archivos en disco no se tocan.** Quien carga un
> archivo en una sala llena necesita saber que no está sobrescribiendo nada.

Un `expander` por fuente, con el estado real en el título, y dentro dos
sub-pestañas: **Cargar un archivo** y **Agregar un registro**.

### Cargar un CSV

**Se dicen las columnas esperadas ANTES de pedir el archivo.** Sin eso, la gente
sube el archivo, falla, y no sabe qué arreglar.

Lectura con `pd.read_csv(archivo, encoding="utf-8-sig")`. Si falla, el mensaje no
es una traza: «No pude leer el archivo: … Revisa que sea un CSV separado por comas
y guardado en UTF-8».

**Validación con mensajes accionables**, no stacktraces. Tienen que decir qué
columna y qué tan mal está:

> ✗ `duracion_min` no es numérica en el 40 % de las filas
> ✗ Faltan columnas obligatorias: `linea`, `turno`

y no `ValueError: could not convert string to float`. Si hay problemas, **el
archivo no se carga**, y se muestran todos juntos con su conteo.

**Confirmación en dos pasos:** si es válido, se muestra el resumen, una vista
previa de 5 filas, y recién ahí el botón *«Usar este archivo como …»*. Reemplazar
la fuente de datos de un tablero no puede ser un solo clic accidental.

Al aceptar hay que **invalidar la caché del índice semántico**: las notas
cambiaron y el índice viejo apunta a filas que ya no existen. Es el tipo de bug que
no da error, solo devuelve resultados equivocados.

**Siempre se puede volver atrás:** el original en disco nunca se tocó.

### Agregar un registro a mano

Dentro de `st.form(..., clear_on_submit=True)`: sin formulario, cada tecla
reejecuta el script entero y recalcula el tablero. En dos columnas.

**Todo campo lleva `placeholder=campo.ejemplo`.** Un formulario de nueve campos
vacíos no dice qué espera en cada uno: ¿`duracion_min` en minutos o en horas?,
¿`lote_resina` con guion o sin guion? El `ejemplo` es un valor real y verosímil del
dominio, no un «escriba aquí».

Las opciones de los `selectbox` **se derivan de los datos**: es lo que impide que
alguien registre una línea que no existe y contamine el tablero con una categoría
fantasma.

Los obligatorios vacíos se listan **por su etiqueta legible**, no por el nombre de
la columna: quien llena el formulario ve «Línea», no `linea`.

> **El detalle que hace que parezca roto:** si alguien agrega una fila con fecha
> **fuera del rango del filtro**, no aparece por ningún lado y parece que no se
> guardó. El rango de fechas debe **seguir a los datos nuevos** cuando el usuario
> no lo haya estrechado a mano.

## La pestaña Generar reporte

Un **PDF** con las gráficas incrustadas, y el mismo material en HTML para la
vista previa de la pestaña. Los dos salen de las mismas figuras y las mismas
cifras, así que no pueden decir cosas distintas.

**Es deductivo, no decorativo: no recalcula nada.** Corre las mismas funciones de
`graficos.py` que dibuja el tablero, con los mismos filtros y supuestos. El mismo
`res` alimenta el pie y el contexto del modelo, así que **el texto del reporte no
puede contradecir a su propia gráfica**.

### Cuatro decisiones

**1. Las gráficas se incrustan sin abrir un navegador.** Un reporte que se manda
por correo tiene que abrirse **sin red y sin la aplicación corriendo**.
`vl-convert` traduce el Vega-Lite de Altair a SVG y a PNG —es una biblioteca en
Rust—, y eso es lo que permite generarlo dentro del proceso de Streamlit. El SVG
va en el HTML; el PNG va en el PDF, que maqueta `fpdf2` (Python puro, sin
librerías nativas que compilar: `weasyprint` habría exigido pango y cairo en cada
máquina del taller).

> **En el PDF las gráficas van como imagen, no como vector.** `fpdf2` sabe
> dibujar los trazos de un SVG pero **no escribir su texto**, y un gráfico sin
> etiquetas de eje no sirve. A escala 2 la impresión se ve bien.

> **Dos trampas de `fpdf2` que se ven feo y no fallan:** `multi_cell` deja el
> cursor **a la derecha** de lo que escribió, así que la siguiente celda arranca
> ahí y el texto se sale de la hoja —hay que devolverlo al margen con
> `new_x=XPos.LMARGIN`—; y `image()` **ya baja el cursor por su cuenta**, así que
> si además le sumas el alto de la imagen, el pie de la gráfica termina a dos
> alturas de distancia, al fondo de la hoja.

Si una gráfica no se puede renderizar, el reporte **no se cae**: queda una nota en
su lugar. Un reporte con cinco gráficas y un aviso es útil; una excepción a mitad
de la generación no le sirve a nadie.

**2. Una hoja por gráfica.** `break-before: page` en cada figura y no
`break-after` en la anterior: así la primera gráfica también arranca en hoja nueva.
En A4 con márgenes de 14 mm el área útil son unos 182 × 255 mm; a 96 ppp eso da
~690 × 965 px, y de ese alto hay que descontar título, pie y aire. De ahí
`ANCHO_GRAFICO = 680` y `ALTO_GRAFICO = 400`: no son un gusto, son la hoja.

**3. Siempre en tema claro**, y la aplicación está en oscuro. Se va a imprimir
o a leer en un cliente de correo, y una gráfica de fondo negro sobre papel blanco no
se lee. Cambia el tema mientras renderiza y **devuélvelo a como estaba** en un
`finally`.

**4. `mailto:` NO puede llevar adjuntos.** Ningún navegador lo permite: es una
restricción del protocolo, no algo que falte implementar. El botón abre el cliente
con el resumen en el cuerpo, y **la interfaz dice explícitamente que el archivo hay
que adjuntarlo a mano**. Ofrecer un botón que promete adjuntar y no adjunta es peor
que decir la verdad. El cuerpo se recorta a ~1.200 caracteres —al codificarse cada
acento pasa a tres— y **cuando se recorta, se dice**.

### Estructura del documento

Portada · KPIs · **el recorte que estás leyendo** (los filtros y supuestos activos:
un reporte que no dice de qué pedazo de planta habla se interpreta como si hablara
de toda) · conclusiones del asistente · una hoja por gráfica · trazabilidad.

### La trazabilidad del reporte hay que anotarla a mano

El reporte calcula por `calculos.py` —igual que el tablero— y **no** por las
herramientas, que son las que van llenando el registro. Sin esto sale con el bloque
vacío.

```python
reg.anotar("gráficas del tablero", vista.traza(*[f.clave for f in a.fuentes]))
```

Los índices salen de la **vista filtrada**, no de los datos completos.

> **El orden importa y es contraintuitivo.** `configurar()` **limpia** el registro,
> así que va **antes** de anotar. Escrito al derecho —anotar primero, configurar
> después, que es como sale natural porque configurar «prepara» las herramientas—
> el bloque sale vacío. No falla nada: simplemente el reporte queda con cifras y
> sin decir sobre cuántas filas se paró.

### El encargo al modelo

Recibe las cifras en JSON tal como salieron del cálculo, y se le piden cuatro
secciones: lo que está pasando · los tres hallazgos que aguantan una pregunta
incómoda, cada uno con su cifra y de qué gráfica sale · qué hacer, en orden de
plata · **qué NO se puede concluir con estos datos** — esta última **no es
opcional**.

**Si hay que recortar el JSON, se dice.** Un JSON cortado a la mitad sin avisar
hace que el modelo concluya sobre datos incompletos creyéndolos completos.

Y un fallo del modelo no puede tumbar el reporte: el texto se acumula **fuera** del
`try`, porque las gráficas y las cifras no dependen de él — ya están calculadas.

---

# Verificación final

## Las comprobaciones

```bash
.venv/bin/python -m pruebas.test_calculos
.venv/bin/python -m src.preguntar
.venv/bin/python -m src.paras.preguntar
```

Y sobre un reporte descargado:

```python
assert pdf[:5] == b'%PDF-'                                 # es un PDF de verdad
assert len(re.findall(rb'/Subtype\s*/Image', pdf)) == 6    # las seis gráficas
assert html.count('<svg') == 6                             # y el HTML también
assert 'Trazabilidad' in html and 'Filas analizadas' in html
assert '**' not in html                                    # sin markdown crudo
assert not re.search(r'https?://(?!www\.w3\.org)', html)   # sin CDN externo
```

## En la aplicación, para **cada agente**

| # | Qué | Cómo se ve que está bien |
|---|---|---|
| 1 | Las cuatro pestañas abren | Sin excepción en pantalla |
| 2 | Contraste | La app arranca en oscuro; ningún texto oscuro sobre oscuro, tampoco en hover |
| 3 | Filtros | Cambiar de asistente y volver: **siguen puestos** |
| 4 | Recarga | F5 en `?agente=paras&tab=tablero` deja donde estaba |
| 5 | Sugerencias | Al hacer clic, lanzan la pregunta |
| 6 | Chat | Sin scroll horizontal; el texto dentro de su pastilla |
| 7 | Datos | Sube un CSV sin una columna obligatoria → mensaje que **nombra la columna** |
| 8 | Reporte | Descarga en PDF, A4, 6 gráficas, una hoja por gráfica |
| 9 | Consola | Cero trazas al arrancar |

## Autocrítica antes de dar por terminado

Repasa esta lista y **reporta lo que no cumplas** en vez de dejarlo pasar:

- [ ] ¿Hay algún `groupby` fuera de los módulos de cálculo?
- [ ] ¿Hay alguna cifra de negocio escrita a mano en el código?
- [ ] ¿Hay alguna fecha o nombre de planta escrito a mano?
- [ ] ¿El bloque de trazabilidad lo arma el código, y suma por unión de conjuntos?
- [ ] ¿Los pies de los gráficos se recalculan del dato, o hay prosa que afirma algo
      que dejaría de ser cierto con otro archivo?
- [ ] ¿Los embeddings tocan algún número?
- [ ] ¿Todos los textos están en español neutro, sin voseo?
- [ ] ¿Hay algún `var(--x)` de CSS esperando una variable que Streamlit no expone?
- [ ] ¿Algún fallo del modelo puede tumbar la interfaz o el reporte?
- [ ] ¿`app.py` cambió para agregar el segundo asistente? **Si sí, el contrato
      quedó corto.**

## Lo que se entrega

- La aplicación corriendo en `http://localhost:8501`, sin errores en consola.
- Un `README.md` en español que arranque en cuatro comandos, con las cinco
  lecciones y sus trampas, el hallazgo de la fecha del turno, y por qué los
  embeddings solo tocan el texto libre.
- Un archivo con las **preguntas de ejemplo y las respuestas reales que dieron** —
  ejecutadas, no inventadas. Si una salió floja, esa es información: o el prompt o
  una herramienta necesitan trabajo.

## Lo que NO hay que hacer

- **No inventes que verificaste.** Si no corriste el comando, dilo.
- **No reemplaces una cifra que no cuadra por una que sí.** Léela primero: casi
  siempre la cifra rara está señalando un error de método real.
- **No agregues dependencias** fuera de las fijadas. Si algo lo exige, fíjala y
  explica por qué en el README.
