# Fase 3 · Plataforma multidominio y reportería

## Forma de trabajo

Trabaja de forma autónoma y no me pidas decisiones técnicas.

- Háblame en español sencillo, sin jerga y sin trazas de error.
- Si algo falla, diagnostícalo y arréglalo. Después cuéntame en una frase qué pasó
  y qué hiciste.
- Si necesitas algo de mí, pídeme una sola cosa a la vez, con instrucciones exactas.
- Cuando este archivo diga «verifica X», ejecuta el comando y mira la salida real.
  No afirmes que verificaste algo si no lo hiciste.
- Al terminar, dime en pocas frases qué construiste y qué puedo probar yo.

---

## Objetivo

Ya existe una aplicación completa de un asistente. Esta fase comprueba si el
contrato de la fase 2 funciona: agregar un segundo asistente de un dominio
completamente distinto sin modificar la pantalla.

Además se agregan las dos piezas que convierten la demostración en algo entregable:
leer las notas de texto libre y generar un reporte que se pueda enviar por correo.

Constrúyelo en este orden, para que lo que quede sin hacer si se acaba el tiempo sea
lo menos valioso:

1. **Las notas de texto libre** — completa la séptima herramienta que quedó
   declarada en la fase 1.
2. **El segundo asistente** — es lo que verifica que el contrato sirve.
3. **Las dos pestañas que faltan** — Datos y Generar reporte.

Siguen valiendo `referencia/interfaz.md` y `referencia/implementacion.md`, y se
suma `referencia/reporte.md`.

---

# 1 · Las notas de texto libre

## El patrón que hay que poder encontrar

En la columna `nota_supervisor` hay siete supervisores describiendo el mismo
problema sin compartir casi ninguna palabra:

```
arranque con el molde frío, mucha rebaba en las primeras cajas
el equipo no había alcanzado temperatura al iniciar, sobró material
la máquina salió fría y las primeras piezas llevaron material de más
molde tibio al inicio, se estabilizó pasada la media hora
partimos en frío, las primeras bandejas se fueron a reproceso
primeras cajas con rebaba, hubo que purgar más de lo normal
turno perdido: el molde se enfrió tras el paro y salió rebaba toda la jornada
```

Buscar «molde frío» encuentra dos. Las otras cinco no llevan esa palabra.

Encontrarlas completa la regla 1: los números dicen que hay material saliendo dentro
de producto conforme, y estas notas dicen por qué.

## Por qué esto no lleva embeddings ni base vectorial

Cuenta los textos antes de elegir la herramienta. Las dos columnas de texto libre
tienen treinta textos distintos en total, unos dos kilobytes.

El asistente que estás construyendo ya es un modelo de lenguaje. Si le pasas los
treinta y le preguntas cuáles describen el mismo problema, los agrupa igual de bien,
porque agrupar significados es exactamente lo que sabe hacer.

Los embeddings se justifican con cien mil notas, cuando ya no caben en el contexto.
Con treinta serían una herramienta pesada para un problema que no la requiere.

Esto es una decisión de diseño y va escrita en el README, porque saber cuándo no
hace falta la pieza sofisticada es parte de lo que este proyecto demuestra.

## La herramienta

`listar_notas_distintas` — sin argumentos. Devuelve los textos distintos de las
columnas de texto libre de la vista filtrada, cada uno con cuántas filas lo
escribieron.

- **Textos distintos, no filas.** Si cuarenta turnos dicen «sin novedad», eso es una
  entrada con el campo `filas: 40`. Agrupar textos idénticos es del código; agrupar
  significados parecidos es del modelo.
- **Respeta los filtros.** Si la vista está en L1, solo salen las notas de L1.
- **Anota las filas en el registro**, como cualquier otra herramienta.
- **No calcula nada del negocio.** Sirve para «¿ha pasado esto antes?». Si alguien
  pregunta *cuánto*, la cifra sale de una función de cálculo.

Nunca incluyas números en esta herramienta. «4.084 kg» no se busca por parecido, se
suma.

El módulo que recopila los textos no sabe de dominios: recibe qué columnas de qué
archivos llevan texto. Son las columnas `nota_supervisor` y `descripcion` en el
asistente de desperdicio, y `comentario_operario` y `descripcion` en el de paradas.

---

# 2 · El segundo asistente: paradas no planeadas

## Por qué existe

Para verificar que la abstracción sirve. Es deliberadamente distinto del primero:
minutos en vez de gramos, máquinas en vez de SKU, pesos por hora en vez de dólares
por kilo, y causas que no se superponen —cada parada tiene una sola— en vez de
categorías que sí lo hacen.

Si los dos fueran parecidos, la abstracción no probaría nada. La pantalla no se
modifica: si terminas editándola, el contrato quedó incompleto y hay que corregir el
contrato, no la interfaz.

Sus fuentes son `downtime_log.csv` y `mantenimiento_historico.csv`. Va en la
carpeta `src/paras/`, con la misma estructura que el primero.

## El hallazgo que define este agente

**La fecha del turno no es la fecha del calendario.**

El turno de noche va de 22:00 a 05:59 y pertenece al día en que empezó. Una parada a
las 02:00 del sábado es del turno de noche del **viernes**.

Sin esa corrección, el patrón más fuerte de todo el archivo aparece repartido entre
dos días contiguos y se interpreta como ruido. Con la fecha del turno queda en una
sola celda y la prueba estadística lo confirma.

Una corrección de tres líneas es la diferencia entre encontrar el patrón y no verlo.
El mapa día × turno va sobre la fecha del turno, y el filtro de fechas también.

```python
madrugada_de_turno_noche = (p["turno"] == "noche") & (hora < 6)
p["fecha_turno"] = p["fecha"] - pd.to_timedelta(
    madrugada_de_turno_noche.astype(int), unit="D")
```

## Clasificar causas cuando falta el código de falla

Una de cada cuatro filas trae el código vacío y solo el comentario del operario.

El vocabulario se construye desde el propio archivo, no desde la intuición. Se
cruzan las palabras del comentario con la categoría de las filas que sí la tienen, y
se ve qué categoría le corresponde de verdad a cada palabra.

El caso que lo demuestra: «tolva» parece materia prima. En este archivo, todas las
filas que la mencionan y además traen categoría son operativas. Corregirlo por el
dato y no por la intuición reduce mucho las filas sin clasificar.

Cada palabra vota, y su voto se reparte entre las categorías en la misma proporción
en que aparece en el archivo: si «tolva» sale en 8 filas operativas y 2 de materia
prima, aporta 0,8 a operativa y 0,2 a materia prima. Quedarse solo con las palabras
que apuntan a una sola categoría parece más limpio, pero deja fuera justamente las
que vuelven ambiguo un comentario, y entonces la marca de ambigüedad no se activa
nunca.

Marca cada fila con el origen de su categoría —código de falla o comentario— y con
si el comentario era ambiguo, y reporta en el pie del gráfico qué porcentaje se
dedujo del comentario. Es una
medida de calidad del dato que quien lee tiene derecho a ver.

## Las nueve herramientas

`resumen_de_paras`, `ordenar_causas`, `detectar_patron_recurrente`,
`comparar_lineas`, `analizar_microparadas`, `cuantificar_ahorro`,
`generar_reporte_de_entrega`, `consultar_maquina`, `listar_comentarios_distintos`.

Cuatro decisiones de método que hay que respetar:

**Un patrón se compara contra la actividad real de la planta**, no contra un
promedio plano. Si la planta corre menos los domingos, tener menos paradas el
domingo no es un hallazgo. Las horas que la planta realmente operó hay que
aproximarlas —el archivo no trae el calendario de operación— y eso se dice en la
respuesta.

**Comparar líneas es comparar perfil, no volumen.** Una línea que corre el doble
tiene el doble de paradas y eso no dice nada. Devuelve horas por día y número de
máquinas, y el pie lo advierte.

**Las microparadas (menos de 5 minutos) devuelven un dato incómodo pero honesto.**
Son muchísimas en cantidad y pocas en horas: contarlas por cantidad las hace parecer
el problema principal cuando no lo son. La respuesta contesta «si juntáramos todas
en una sola causa, ¿en qué puesto quedaría?», que es la pregunta que importa.

**El ahorro solo cuenta patrones confirmados**, solo el exceso sobre lo esperado, y
baja la probabilidad de éxito si ya se intentaron preventivos en esa máquina: si el
preventivo ya se hizo y el problema sigue, es menos probable que funcione ahora.

## Los seis gráficos

Pareto con curva acumulada, gráfico circular de causas, horas por línea, evolución
semanal, mapa día × turno sobre la fecha del turno, y las máquinas con más paradas.

El Pareto lleva curva acumulada acá y no en el otro tablero. No es una
inconsistencia; documéntalo en el código:

- En **paradas** cada parada pertenece a exactamente una categoría, así que el
  acumulado suma 100 % y se puede ver qué pocas causas explican la mayor parte del
  tiempo perdido.
- En **desperdicio** las categorías se superponen, y una curva acumulada contra el
  total afirmaría algo falso.

Los colores de este tablero están en `referencia/interfaz.md`.

## Registrarlo

Escribe su declaración y agrégala al registro de asistentes. Eso debería ser todo lo
necesario.

Sus métricas: horas de paro, costo, paradas registradas y porcentaje de
microparadas. Su supuesto: el costo de paro por hora. Sus filtros: rango de fechas,
línea, máquina, turno y categoría de falla.

Antes de seguir, comprueba que la fecha del turno quedó bien aplicada: el comando
está en `referencia/verificacion.md`, sección **Fase 3**.

---

# 3 · Las dos pestañas que faltan

## La pestaña Datos

Es la pieza que convierte una demostración en una herramienta: sin ella, el
asistente solo puede hablar del archivo con el que se construyó.

Nada de esto se escribe a mano por asistente. Cada fuente ya declara sus campos en
el contrato de la fase 2, y de esa declaración se derivan el validador de archivos,
el formulario de captura y la lista de columnas esperadas.

> Regla, y va escrita en la pantalla, arriba de todo: los cambios valen solo para
> esta sesión. El tablero y el chat los ven de inmediato. Los archivos en disco no se
> modifican. Quien carga un archivo en una sala llena necesita saber que no está
> sobrescribiendo nada.

Dos cosas por fuente: cargar un archivo y agregar un registro a mano. La mecánica de
las dos —validación con mensajes accionables, confirmación en dos pasos, formulario
con ejemplos reales— está en `referencia/interfaz.md`.

## La pestaña Generar reporte

Un PDF con las gráficas incrustadas, y el mismo material en HTML para la vista
previa. Los dos salen de las mismas figuras y las mismas cifras, así que no pueden
decir cosas distintas.

No recalcula nada. Corre las mismas funciones que dibuja el tablero, con los mismos
filtros y supuestos. Las mismas cifras alimentan el pie del gráfico y el texto del
reporte, así que el texto no puede contradecir a su propia gráfica.

La maquetación completa está en `referencia/reporte.md`.

---

# Verificación final

Corre entera la sección **Fase 3** de `referencia/verificacion.md`: las
comprobaciones por consola, los asertos sobre el reporte descargado, la revisión en
pantalla de cada agente y la autorrevisión final. Pega la salida real y reporta lo
que no cumplas en vez de dejarlo pasar.

## Lo que se entrega

- La aplicación corriendo en `http://localhost:8501`, sin errores en consola.
- Un `README.md` en español que arranque en cuatro comandos, con las cuatro reglas
  de cálculo y sus trampas, el hallazgo de la fecha del turno, y por qué las notas
  de texto libre no llevan embeddings.
- Un archivo con las preguntas de ejemplo y las respuestas reales que dieron,
  ejecutadas, no inventadas. Si una salió deficiente, esa es información: o el
  prompt o una herramienta necesitan trabajo.

## Lo que no hay que hacer

- **No afirmes que verificaste algo si no lo hiciste.** Si no corriste el comando,
  dilo.
- **No reemplaces una cifra que no cuadra por una que sí.** Léela primero: casi
  siempre la cifra rara está señalando un error de método real.
- **No agregues dependencias** fuera de las fijadas. Si algo lo exige, fíjala y
  explica por qué en el README.
