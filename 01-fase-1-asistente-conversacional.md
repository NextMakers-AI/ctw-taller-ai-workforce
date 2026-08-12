# Fase 1 · Asistente conversacional con trazabilidad

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

Construir un asistente que responde preguntas sobre una planta de empaques
plásticos que no tiene un sistema que capture automáticamente los datos de las
máquinas (SCADA): todo entra a mano, en archivos que alguien llena al cierre de
cada turno.

Esta fase incluye interfaz, pero solo el chat. Sin gráficos ni filtros: una
pantalla donde se pregunta y se ve al asistente consultar los datos. El tablero es
la fase 2 y se construye sobre esto.

Al terminar debo poder abrir la aplicación en el navegador, preguntarle, y ver en
vivo qué consultó para cada cifra y cuántas filas de datos usó para calcularla.

---

## Restricciones

1. Todo en español neutro: el código, los comentarios, los nombres y los mensajes.
   Sin voseo.

2. Toda cifra que el asistente diga sale de una herramienta. El modelo no suma, no
   promedia, no estima. Si le falta un dato, llama a otra herramienta; si no hay
   herramienta, dice que no lo sabe.

3. El bloque de trazabilidad lo arma el código, no el modelo. Las filas se cuentan
   sin repetir: si tres herramientas consultan las mismas 28.000 filas, el bloque
   dice 28.000, no 84.000.

4. Ningún número del negocio va escrito a mano. Ni fechas, ni umbrales, ni nombres
   de planta. Todo sale de los datos o de la configuración.

5. Corre los comandos y muestra la salida real. Si falla, arréglalo y vuelve a
   correrlo.

---

## Punto de partida

Todo está instalado. Las versiones están fijadas en `referencia/requirements.txt`:
no las resuelvas por tu cuenta.

Hay cinco archivos de referencia que debes leer y seguir. Cada nota que traen
viene de un problema que ya ocurrió antes.

| Archivo | Qué trae |
|---|---|
| `referencia/esquema-de-datos.md` | Las columnas de cada archivo, y qué hay que saber de cada una |
| `referencia/estructura-del-proyecto.md` | El árbol de archivos a crear, fase por fase |
| `referencia/implementacion.md` | Las decisiones técnicas del motor |
| `referencia/interfaz.md` | Cómo se dibuja la pantalla |
| `referencia/verificacion.md` | Las comprobaciones al cerrar cada fase |

Los datos están en `datos/`, ya generados. No escribas un generador: los archivos
vienen de la planta tal como están, con sus columnas vacías y sus imperfecciones.
En esta fase se usan tres: `muestras_qc.csv`, `produccion_turno.csv` y
`eventos_operacion.csv`.

---

# Las cuatro reglas de cálculo

Son la especificación de los cálculos del negocio. Cada una corrige un error en el
que cae un análisis ingenuo, y el sistema tiene que estar construido para evitarlo.

## 1 · El desperdicio son dos cosas distintas que no se superponen

- **Material rechazado**: la pieza no cumple, se rechaza y va a la báscula de
  rechazos. Queda pesada y registrada.
- **Material en exceso**: material que sale dentro de producto conforme. La pieza
  pesa más que su objetivo, cumple la inspección y se despacha.

Los dos son desperdicio y cuestan lo mismo, pero se miden desde fuentes distintas:
el primero desde la báscula de rechazos, el segundo desde los pesos de control de
calidad. Rara vez aparecen sumados en la misma cifra, así que convertirlos a la
misma unidad y a la misma moneda es parte del trabajo.

Se calcula multiplicando el exceso medio de cada pieza por las unidades que pasaron
la inspección (`delta_medio × unidades_conformes`), desglosado por línea y por SKU.
Nunca un promedio global: cada SKU tiene su propio peso objetivo, y promediar
gramos de piezas de 3 g con piezas de 96 g no significa nada.

Solo cuentan las muestras cuya columna `veredicto` dice `conforme`, y el delta se
recorta en cero con la función `.clip(lower=0)` de pandas. Una pieza que pesa menos
del objetivo no compensa a otra que pesa de más; es un problema distinto.

Repórtalos separados y sumados, indicando de qué fuente sale cada uno.

## 2 · Una máquina desgastada y una descalibrada no se arreglan igual

- **Desgaste**: la máquina arrancó bien y el peso sube con el tiempo →
  mantenimiento.
- **Descalibración**: está programada en el número equivocado desde el principio,
  pero es estable → un ajuste del parámetro.

Recomendar lo contrario cuesta tiempo y dinero.

Cómo se distinguen: se traza la tendencia de las medias diarias, dándole a cada día
un peso proporcional a sus muestras. Un día con 4 muestras no puede influir lo mismo
que uno con 300. Se clasifica por la pendiente de esa tendencia, no por el promedio.

Ese cálculo se hace con la clase `WLS` de la librería `statsmodels` — una regresión
ponderada.

La descalibración se juzga por el **intercepto** —el peso en el que arranca esa
tendencia—, no por la media de la serie. Una línea desgastada tiene una media alta
precisamente porque se desgastó; juzgarla por la media la clasifica como
descalibrada, que es exactamente el error a evitar.

El costo mensual proyectado del desgaste:

```python
costo = (pendiente * 30) * (unidades_por_dia * 30) / 1000 * precio
```

Los dos factores tienen que estar en la misma unidad de tiempo. Multiplicar los
gramos de un mes por las unidades de un solo día da una cifra unas 30 veces menor,
tan pequeña que nadie actuaría sobre ella.

## 3 · Un lote de resina con pocas muestras no es evidencia

Exige un mínimo de turnos (10 por defecto, configurable en el archivo de
configuración `.env`). Los lotes que no alcanzan ese mínimo se devuelven igual,
mostrando sobre cuántos turnos se calcularon (`n`). Mostrar por qué se descartaron
es más útil que omitirlos.

Si el asistente menciona un lote, dice en cuántos turnos se basa. Los descartados
se pueden mencionar como pendientes de confirmar, nunca como la causa del problema.

Para decidir si la diferencia entre lotes es real o puede ser azar, usa la función
`ttest_ind` de la librería `scipy`. Un lote puede tener el peor promedio y aun así
no ser significativamente distinto de los demás.

## 4 · Las categorías de desperdicio se superponen

Un mismo turno puede tener cambio de color y paro no programado. Los porcentajes no
suman 100 % y no deben presentarse como si fueran las partes exactas de un total,
ni en un gráfico circular.

Cada cifra es el exceso sobre una línea base, y la línea base son los turnos sin
transiciones.

El problema está en el denominador. El porcentaje de cada categoría se mide contra
el exceso de toda la planta sobre la línea base. Dividir entre la suma de las
categorías da 100 % exacto por construcción: la advertencia no se activa nunca, los
porcentajes parecen las partes exactas de un total, y la regla desaparece sin que
ninguna prueba falle.

Devuelve las dos cifras con nombres distintos: `pct_del_exceso_de_planta` y
`pct_de_lo_atribuido`. Las dos se usan más adelante.

---

# Qué construir

El árbol de archivos está en `referencia/estructura-del-proyecto.md`. Crea lo de la
sección **Fase 1** y nada más.

Fuera de alcance en esta fase: gráficos, tablero, filtros y supuestos. Todo eso
corresponde a la fase 2.

## Los cálculos son la única fuente de cifras

De `calculos.py` sale toda cifra que la aplicación muestre o diga. Nadie más suma:
ni la pantalla, ni las herramientas, ni el modelo.

Una función por regla de cálculo, más dos de apoyo:

| Función | Para qué |
|---|---|
| `calcular_desperdicio` | Regla 1 — los dos tipos, separados y sumados |
| `analizar_tendencia_de_peso` | Regla 2 — desgaste vs. descalibración, con su recomendación |
| `ordenar_lotes_resina` | Regla 3 — lotes con evidencia, y descartados con su `n` |
| `atribuir_categorias` | Regla 4 — exceso sobre la línea base, con su advertencia |
| `comparar_dimension` | Comparar por línea, SKU, turno o molde |
| `detectar_turnos_anomalos` | El turno que se salió de lo normal |

Toda función que haga un supuesto o tenga un límite lo dice en su respuesta. Son
las salvedades que permiten defender la cifra si alguien la cuestiona.

## Las siete herramientas

Una por cada función de cálculo, más una séptima:

| Herramienta | Para qué |
|---|---|
| `calcular_desperdicio` | Los dos tipos, separados y sumados |
| `analizar_tendencia_de_peso` | Desgaste vs. descalibración, con su clasificación |
| `ordenar_lotes_resina` | Lotes con evidencia + descartados con su `n` |
| `atribuir_categorias` | Exceso sobre línea base, con aviso de superposición |
| `comparar_dimension` | Línea, SKU, turno, molde |
| `detectar_turnos_anomalos` | El turno que se salió de lo normal |
| `listar_notas_distintas` | Todavía no existe: devuelve un aviso de que no está disponible |

Ninguna herramienta calcula. Cada una llama al módulo de cálculo, devuelve lo que
este le dé, y anota qué filas consultó.

La séptima se construye completa en la fase 3. Déjala declarada y devolviendo un
aviso claro —«las notas de texto libre todavía no están disponibles»— para que el
asistente sepa que existe y no invente su contenido.

## Las instrucciones del asistente

No contienen ninguna cifra. Lo único concreto que llevan es el inventario de la
planta —qué líneas, qué SKU con su peso objetivo, qué turnos, qué rango de fechas—
derivado de los archivos al arrancar.

Un número escrito ahí es un número que nadie puede auditar y que el asistente
repetirá con seguridad cuando los datos ya hayan cambiado.

Contenido, en este orden:

1. **Quién eres**: analista de desperdicio, respondes en español y con precisión,
   sabiendo que cualquiera puede pedirte verificar la cifra.
2. **La planta**, derivada de los datos.
3. **La regla principal**: toda cifra sale de una herramienta.
4. **Cómo leer lo que devuelven las herramientas**: las cuatro reglas de cálculo,
   escritas como instrucciones de lectura.
5. **Cómo escribir**: primero la respuesta directa en una o dos frases, después la
   evidencia con las cifras tal como vienen, y al final qué hacer, distinguiendo un
   ajuste de un mantenimiento.
6. **Prohibido escribir el bloque de trazabilidad**: lo agrega el código. Un bloque
   de auditoría redactado por el modelo tendría el mismo problema que viene a
   resolver.

## El diagnóstico por consola

Un guion que corre las preguntas por consola, imprimiendo qué herramienta se
ejecuta y, al final, el bloque de trazabilidad.

Constrúyelo y córrelo antes de empezar la interfaz. Permite distinguir un problema
del asistente de un problema de la pantalla. No se borra después: queda como la
forma rápida de probarlo sin abrir el navegador.

Las cuatro preguntas de ejemplo no llevan fechas escritas a mano. Una pregunta con
la fecha adentro deja de funcionar el día que los archivos cambien:

1. «¿Cuánto material estamos desperdiciando y de qué tipo es? Separa lo que va a la
   báscula de rechazos de lo que sale dentro de producto conforme.» → regla 1
2. «¿Qué líneas hay que recalibrar y cuáles necesitan mantenimiento? No me las
   mezcles.» → regla 2
3. «¿Hay algún lote de resina que se comporte peor que los demás?» → regla 3
4. «¿Cuál fue el peor turno del período y qué pasó ahí?» → el turno anómalo

## Las pruebas

Sin librería de pruebas: un guion que imprime `[PASA]`/`[FALLA]` y sale con código
distinto de cero si algo falla.

No comprueban que el código corra: comprueban que recupere los patrones que hay en
los datos. Qué tiene que comprobar cada una está en `referencia/verificacion.md`,
sección **Fase 1**.

---

# La pantalla

Solo después de que todas las comprobaciones pasen se construye la pantalla. Son
tres piezas: la apariencia, la estructura de la página y la pantalla de chat.

Sigue `referencia/interfaz.md` al pie de la letra. Trae los colores, los patrones
de componente y las particularidades de Streamlit ya resueltas.

Dos requisitos: un fallo del modelo no puede dejar la interfaz inservible, y la
caja del chat no cambia de alto cuando el asistente empieza a responder.

---

## Verificación de esta fase

Corre entera la sección **Fase 1** de `referencia/verificacion.md` —primero por
consola, después en la interfaz— y pega la salida real.

Como comprobación final: cambia el precio de la resina (`PRECIO_RESINA_USD_KG`) en
el archivo `.env`, reinicia la app, vuelve a preguntar, y verifica que cambia la
cifra en dólares y no la de kilos.
