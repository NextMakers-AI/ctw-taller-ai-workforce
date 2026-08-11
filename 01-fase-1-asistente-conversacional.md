# Fase 1 · Asistente conversacional con trazabilidad

> **Cómo se usa.** Pásale este archivo entero a tu agente de código, en la carpeta
> del taller. Antes, haz lo de `00-preparacion-del-entorno.md`.

## Cómo trabajar conmigo

**No sé programar.** Trabaja de forma autónoma y no me pidas decisiones técnicas.

- Háblame en **español sencillo**, sin jerga y sin trazas de error.
- Si algo falla, **diagnostícalo y arréglalo tú**. Después cuéntame en una frase
  qué pasó y qué hiciste.
- Si de verdad necesitas algo de mí, pídeme **una sola cosa a la vez**, con
  instrucciones exactas.
- **No inventes que verificaste algo.** Cuando este archivo diga «verifica X»,
  ejecuta el comando y mira la salida real.
- Al terminar, dime en pocas frases **qué construiste y qué puedo probar yo**.

---

Vas a construir un asistente que responde preguntas sobre una planta de empaques
plásticos que **no tiene SCADA**: todo entra a mano, en archivos que alguien llena
al cierre de cada turno.

En esta fase hay interfaz, pero **solo el chat**. Nada de gráficos ni filtros: una
pantalla donde se pregunta y se ve al asistente consultar los datos. El tablero
llega en la fase 2, y llega sobre esto.

**Al terminar** vas a poder abrir la aplicación en el navegador, preguntarle, y ver
en vivo qué consultó para cada cifra y sobre cuántas filas se paró.

---

## Las reglas que no se negocian

Si rompes una de estas, el resultado no es esta aplicación.

1. **Todo va en español neutro** — el código, los comentarios, los nombres y los
   mensajes. Nada de voseo.

2. **Toda cifra que el asistente diga sale de una herramienta.** El modelo no suma,
   no promedia, no estima. Si le falta un dato, llama a otra herramienta; si no hay
   herramienta, dice que no lo sabe.

3. **El bloque de trazabilidad lo arma el código, no el modelo.** Y las filas se
   cuentan sin repetir: si tres herramientas consultan las mismas 28.000 filas, el
   bloque dice 28.000, no 84.000.

4. **Ningún número del negocio va escrito a mano.** Ni fechas, ni umbrales, ni
   nombres de planta. Todo sale de los datos o de la configuración.

5. **Nunca inventes que verificaste algo.** Corre el comando y muestra la salida
   real. Si falla, arréglalo y vuelve a correrlo.

---

## El punto de partida

**Ya está todo instalado.** Las versiones están fijadas en
`referencia/requirements.txt`: no las resuelvas por tu cuenta.

Tres archivos de referencia que **hay que leer y seguir**. No son sugerencias: cada
nota que traen existe porque algo falló antes y costó encontrarlo.

| Archivo | Qué trae |
|---|---|
| `referencia/esquema-de-datos.md` | Las columnas de cada archivo, y qué hay que saber de cada una |
| `referencia/implementacion.md` | Las decisiones técnicas del motor |
| `referencia/interfaz.md` | Cómo se dibuja la pantalla |

Los datos están en `datos/`, ya generados. **No escribas un generador**: llegan de
la planta como llegan. En esta fase se usan tres: `muestras_qc.csv`,
`produccion_turno.csv` y `eventos_operacion.csv`.

---

# Las cuatro lecciones

Son el corazón de todo esto. **Cada una es una trampa en la que un análisis
ingenuo cae**, y el sistema tiene que estar construido para no caer.

## 1 · El desperdicio son DOS cosas que no se solapan

- **Material rechazado**: la pieza no cumple, se rechaza y va a la báscula de
  rechazos. Queda pesada y registrada.
- **Material en exceso**: material que sale dentro de producto conforme. La pieza
  pesa más que su objetivo, cumple la inspección y se despacha.

Los dos son desperdicio y se pagan igual, pero **se miden desde fuentes
distintas**: el primero desde la báscula de rechazos, el segundo desde los pesos
de control de calidad. Por eso rara vez aparecen sumados en la misma cifra, y
ponerlos en la misma unidad y en la misma moneda es parte del trabajo.

Se calcula `delta_medio × unidades_conformes`, **desglosado por línea y por SKU**
— nunca un promedio global, porque cada SKU tiene su propio peso objetivo y
promediar gramos de piezas de 3 g con piezas de 96 g no significa nada.

Solo cuentan las muestras con `veredicto == "conforme"`, y el delta se recorta en
cero (`.clip(lower=0)`): una pieza que pesa *menos* del objetivo no es un ahorro
que compense a otra que pesa de más, es otro problema.

**Repórtalos separados y sumados**, y di de qué fuente sale cada uno.

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

## 4 · Las categorías de desperdicio se solapan

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

---

# Qué construir

```
app.py                      La interfaz: SOLO el chat.
requirements.txt            copia de referencia/requirements.txt
.streamlit/config.toml      copia de referencia/config.toml, tal cual
src/
  config.py                 Los parámetros. Cero cifras de negocio.
  carga.py                  Leer los archivos, recortarlos, y saber qué filas se tocaron.
  calculos.py               LA ÚNICA FUENTE DE CIFRAS.
  trazabilidad.py           El registro de filas consultadas.
  herramientas.py           Las 7 que el asistente puede llamar.
  agente.py                 El modelo, sus instrucciones, y el streaming.
  estilo.py                 La apariencia. Todavía sin colores de gráficos.
  preguntar.py              Las mismas preguntas, por consola. Es el diagnóstico.
pruebas/test_calculos.py    Las comprobaciones sobre los cálculos.
```

**Lo que NO se construye acá, a propósito:** gráficos, tablero, filtros y supuestos.
Todo eso es la fase 2. Si te descubres dibujando una barra, te saliste del encargo.

## Los cálculos son la única fuente de cifras

De ahí sale **toda** cifra que la aplicación muestre o diga. Nadie más suma: ni la
pantalla, ni las herramientas, ni el modelo.

Una función por lección, más dos de apoyo:

| Función | Para qué |
|---|---|
| `calcular_desperdicio` | Lección 1 — las dos mitades, separadas y sumadas |
| `analizar_deriva` | Lección 2 — desgaste vs. descalibración, con su recomendación |
| `rankear_lotes_resina` | Lección 3 — lotes con evidencia, y descartados con su `n` |
| `atribuir_categorias` | Lección 4 — exceso sobre la línea base, con su advertencia |
| `comparar_dimension` | Comparar por línea, SKU, turno o molde |
| `detectar_turnos_anomalos` | El turno que se salió de norma |

**Toda función que haga un supuesto o tenga un límite lo dice en su respuesta.** Son
las salvedades que hacen que la cifra aguante una pregunta incómoda: un número sin
decir sobre qué se paró se cae en la primera repregunta.

## Las siete herramientas

Son la lista de lo que el asistente puede consultar. Una por cada función de
cálculo, más una séptima:

| Herramienta | Para qué |
|---|---|
| `calcular_desperdicio` | Las dos mitades, separadas y sumadas |
| `analizar_deriva` | Desgaste vs. descalibración, con su clasificación |
| `rankear_lotes_resina` | Lotes con evidencia + descartados con su `n` |
| `atribuir_categorias` | Exceso sobre línea base, con aviso de solapamiento |
| `comparar_dimension` | Línea, SKU, turno, molde |
| `detectar_turnos_anomalos` | El turno fuera de norma |
| `listar_notas_distintas` | Marcador por ahora: devuelve un aviso de que aún no existe |

**Ninguna herramienta calcula.** Cada una llama al módulo de cálculo, devuelve lo
que este le dé, y anota qué filas consultó.

La séptima se construye completa en la fase 3. Déjala declarada y devolviendo un
aviso honesto —«las notas de texto libre todavía no están disponibles»— para que el
asistente sepa que existe y no invente su contenido.

## Las instrucciones del asistente

**No contienen ni una cifra.** Lo único concreto que llevan es el inventario de la
planta —qué líneas, qué SKU con su peso objetivo, qué turnos, qué rango de fechas—
y eso se deriva de los archivos al arrancar.

Un número escrito ahí es un número que nadie puede auditar y que el asistente
repetirá con total seguridad cuando los datos ya hayan cambiado.

Lo que tienen que decir, en este orden:

1. **Quién eres** — analista de desperdicio, respondes en español, con la precisión
   de quien sabe que cualquiera en la sala puede pedirle verificar la cifra.
2. **La planta**, derivada de los datos.
3. **La regla que no se negocia** — toda cifra sale de una herramienta.
4. **Cómo leer lo que devuelven las herramientas** — las cuatro lecciones,
   escritas como instrucciones de lectura.
5. **Cómo escribir** — primero la respuesta directa en una o dos frases, después la
   evidencia con las cifras tal como vienen, y al final qué hacer, distinguiendo un
   ajuste de un mantenimiento.
6. **Prohibido escribir el bloque de trazabilidad**: lo agrega el código. Un bloque
   de auditoría redactado por el modelo tendría exactamente el problema que viene a
   resolver.

## El diagnóstico por consola, y se hace primero

Un guion que corre las preguntas por consola, imprimiendo qué herramienta se
ejecuta y, al final, el bloque de trazabilidad.

**Constrúyelo y córrelo antes de tocar la interfaz.** Es lo que separa un problema
del asistente de un problema de la pantalla, y no se borra después: queda como la
forma rápida de probarlo sin abrir el navegador.

Las cuatro preguntas de ejemplo **no llevan fechas escritas a mano**. Una pregunta
con la fecha adentro se rompe el día que los archivos cambien:

1. «¿Cuánto material estamos desperdiciando y de qué tipo es? Separa lo que va a la
   báscula de rechazos de lo que sale dentro de producto conforme.» → lección 1
2. «¿Qué líneas hay que recalibrar y cuáles necesitan mantenimiento? No me las
   mezcles.» → lección 2
3. «¿Hay algún lote de resina que se comporte peor que los demás?» → lección 3
4. «¿Cuál fue el peor turno del período y qué pasó ahí?» → el turno fuera de norma

## Las pruebas

Sin framework: un guion que imprime `[PASA]`/`[FALLA]` y sale con código distinto
de cero si algo falla.

**No comprueban que el código corra: comprueban que recupere los patrones que hay
en los datos.** Es la diferencia entre una prueba que se siente bien y una que
sirve. Al menos:

- Las dos mitades del desperdicio existen, se suman sin solaparse, y el desglose
  por línea+SKU reconstruye el total.
- Solo se cuentan muestras conformes, y ningún delta medio es negativo.
- Se detecta la línea que **se desgasta** y la que está **descalibrada**.
- **La descalibración se juzga por el punto de partida, no por el promedio**:
  comprueba que la línea que se desgasta tiene el promedio más alto y *aun así* no
  se clasifica como descalibrada. Esta es la prueba que más enseña.
- El costo del desgaste está escalado a un mes completo.
- Los lotes con evidencia superan el mínimo; los descartados vienen con su `n`.
- Los porcentajes de categoría **pasan del 100 %** y hay advertencia.
- El z robusto encuentra el turno más extremo.
- El recorte por filtros toca **todos** los archivos de forma coherente.

**Si una prueba falla, lee la cifra que imprime antes de tocar nada.**

---

# La pantalla

Con la consola en verde, recién ahora se dibuja. Son tres piezas: la apariencia, el
armazón de la página y la pantalla de chat.

**Sigue `referencia/interfaz.md` al pie de la letra.** Trae los colores, los
patrones de componente y las trampas de Streamlit ya resueltas — es un archivo
largo y aburrido a propósito, para que la pantalla salga bien a la primera.

Lo único que hay que tener claro acá: **un fallo del modelo no puede tumbar la
interfaz**, y la caja del chat **no cambia de alto** cuando el asistente empieza a
responder.

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
