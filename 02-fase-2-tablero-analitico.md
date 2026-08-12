# Fase 2 · Tablero analítico con cifras auditables

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

Ya existe un asistente con un chat que funciona y dice de dónde sacó cada cifra.
Ahora se le agrega un tablero que muestra lo mismo sin tener que preguntar, más los
filtros y supuestos que recortan el tablero y el chat a la vez.

El chat de la fase 1 no se rehace: se mueve a una pestaña y se conecta a los
filtros. Todo lo que ya funciona ahí se queda como está.

El requisito central de esta fase es que el tablero y el chat nunca puedan decir
cifras distintas para la misma pregunta. Si eso ocurre en una demostración en vivo,
el resto de las cifras deja de ser creíble.

Al terminar debo poder mover un filtro o un supuesto y ver cambiar el tablero y la
siguiente respuesta del chat.

---

## Las restricciones de la fase 1 siguen valiendo

Español neutro, toda cifra sale de una herramienta, el bloque de trazabilidad lo
arma el código, ningún número del negocio escrito a mano, y no afirmar que
verificaste algo sin haberlo hecho. A esas se suma una nueva:

> Los gráficos y el chat usan las mismas funciones de cálculo. Ninguna cifra de
> negocio se calcula fuera del módulo de cálculo.

Si un gráfico hiciera su propia cuenta, tarde o temprano se separaría de lo que dice
el chat. Esta fase existe para hacer imposible ese fallo.

Sigue valiendo `referencia/interfaz.md`, que ahora también trae los colores de
datos, las trampas de la librería de gráficos y los detalles del tablero.

---

# Qué construir

El árbol de archivos está en `referencia/estructura-del-proyecto.md`, sección
**Fase 2**. Es lo que se agrega o se amplía sobre lo que ya existe de la fase 1.

## Las tres capas y qué puede hacer cada una

```
        ┌───────────────────────────────────────────────┐
        │  la pantalla       no calcula NADA             │
        ├──────────────┬────────────────────────────────┤
        │  gráficos    │  herramientas del asistente    │
        │              │                                │
        │       las dos llaman a lo mismo ↓             │
        ├───────────────────────────────────────────────┤
        │  cálculos       LA ÚNICA FUENTE DE CIFRAS     │
        ├───────────────────────────────────────────────┤
        │  carga          los datos                     │
        └───────────────────────────────────────────────┘
```

Que los gráficos y las herramientas llamen a las mismas funciones es la decisión de
arquitectura que sostiene el proyecto: es lo que hace imposible que el tablero y el
chat den cifras distintas.

---

# El contrato

Es la pieza central de esta fase, y lo que hace posible la fase 3.

La pantalla no sabe nada de plásticos. No sabe qué es el desperdicio, ni qué líneas
hay, ni qué gráficos dibujar. Lee una declaración del asistente y de ahí saca todo:
sus fuentes de datos, sus filtros, sus supuestos, sus métricas, sus gráficos, sus
herramientas y sus instrucciones.

En la fase 3 se agrega un segundo asistente de un dominio completamente distinto
sin modificar la pantalla. Esto es lo único que lo permite.

La declaración tiene cinco piezas:

| Pieza | Qué describe |
|---|---|
| **Campo** | Una columna: cómo se llama, de qué tipo es, cómo se le dice a una persona, y un ejemplo |
| **Fuente** | Un archivo de datos y los campos que trae |
| **Filtro** | Algo por lo que se puede recortar: una lista de opciones o un rango de fechas |
| **Parámetro** | Un supuesto con su rango y su paso |
| **Gráfico** | Un título, la función que lo dibuja, y el pie que lo explica |

La declaración del asistente las junta todas, más las herramientas, las
instrucciones, las métricas y las preguntas sugeridas.

La estructura exacta está en `referencia/interfaz.md`.

Declara las Fuentes completas ahora, con su ejemplo, aunque el formulario que las
usa llegue hasta la fase 3. De esa declaración se derivan el validador de archivos
y el formulario; agregarlas después obliga a rehacer ambos.

## El pie de cada gráfico se calcula, no se escribe

El pie recibe las cifras del cálculo. Eso es deliberado: si el archivo de entrada
cambia, el texto bajo el gráfico cambia con él. Un pie que diga «las seis
categorías» con el número escrito a mano pasa a ser falso en cuanto alguien carga un
archivo con cuatro.

Regla: en un pie solo se escribe a mano lo que describa cómo leer el gráfico («el
número es el % de scrap», «la etiqueta emergente trae el número de muestras»),
nunca una afirmación sobre el dato.

## Las opciones de los filtros salen de los datos

Ninguna lista escrita a mano: si el archivo trae una línea nueva, aparece
automáticamente; si trae una menos, desaparece.

---

# Los cuatro gráficos

Ninguno hace cuentas: cada uno llama al módulo de cálculo y devuelve el dibujo y las
cifras. Las mismas cifras alimentan el pie.

| Título | Qué es | Qué regla de cálculo hace visible |
|---|---|---|
| Desperdicio en kg por tipo de origen | Pareto con curva acumulada | **1 y 4** |
| Exceso de material por línea y SKU | Promedios diarios con su tendencia | **2** |
| Porcentaje de desperdicio (scrap) por lote | Lotes de peor a mejor, con los descartados en gris y su número de turnos | **3** |
| Impacto monetario del desperdicio (scrap) | Costo acumulado, dos franjas | — |

Cada gráfico hace visible una regla de cálculo, salvo el último, que muestra la
cifra en dinero.

Dos requisitos del Pareto, que corresponden a la regla 4:

- **Las barras tienen que medir todas lo mismo** para poder compararse entre sí: el
  material rechazado de la línea base, el exceso de cada causa sobre esa base, y el
  material en exceso. Omitir la barra de la línea base haría creer que las causas
  explican todo el desperdicio.
- **El acumulado se calcula sobre las barras del gráfico**, no contra el total de la
  planta. Como las causas se superponen, las barras suman más que el desperdicio
  real, y el pie tiene que decirlo.

Las convenciones visuales y las trampas de la librería están en
`referencia/interfaz.md`.

---

# La pantalla crece

De la fase 1 hay una sola pantalla con el chat. Ahora:

- La barra lateral suma selector de asistente, filtros y supuestos.
- El área principal pasa a dos pestañas: **Preguntar** —el chat de la fase 1, movido
  sin cambios— y **Tablero**.
- Todo lo que la pantalla sabía del dominio se traslada al contrato. La interfaz
  deja de nombrar «desperdicio» en ninguna parte.

En la fase 3 se suman dos pestañas más. Constrúyelas como un elemento más de una
lista, no como un caso especial.

## Los filtros recortan el tablero y el chat

Un filtro no es solo del tablero: las herramientas del chat reciben la misma vista
recortada. Si el usuario filtra por L1, la siguiente respuesta del chat habla solo
de L1, y el bloque de trazabilidad lo demuestra con menos filas.

Indícalo en la barra lateral, porque de lo contrario el usuario asume que el chat
ve todos los datos.

El rango de fechas se ajusta a los datos: si nadie lo cambió a mano, toma la fecha
más antigua y la más reciente que traigan los archivos.

## Los supuestos van aparte

En su propio grupo, separados de los filtros, porque son de otra naturaleza: un
filtro recorta el dato, un supuesto le asigna un precio.

Están en la pantalla y no en el código porque quien presenta tiene que poder
cambiarlos en vivo cuando alguien de la sala diga «ese precio no es el nuestro».

---

# La pestaña Preguntar

El chat entero viene de la fase 1 y no se rehace. Solo cambian tres cosas:

1. **Pasa a estar dentro de una pestaña.**
2. **Recibe la vista filtrada**, junto con los supuestos. Se sigue reconfigurando
   una vez por pregunta.
3. **Su estado incluye qué asistente está activo**, porque en la fase 3 va a haber
   dos conversaciones distintas.

# La pestaña Tablero

Arriba las métricas, debajo una nota, y después los gráficos en rejilla de dos
columnas.

## Las métricas

Cuatro, y las dos primeras son la regla 1 expresada como cifra: material rechazado y
material en exceso, separados. Lo primero que ve quien abre la aplicación es que el
desperdicio son dos cosas distintas.

El texto pequeño bajo cada métrica no es una comparación contra un periodo anterior:
es contexto de la misma cifra — «7.555 USD» bajo los kilos, «6,50 % del consumo»
bajo el porcentaje de desperdicio.

## La nota del tablero

Debajo de las métricas, una línea que explique lo que las cifras no dicen por sí
solas:

> El **material en exceso** se cuantifica desde los pesos de control de calidad, no
> desde la báscula de rechazos: es material que sale dentro de producto conforme.

Es una definición, no una cifra. Sigue siendo cierta con cualquier archivo de
entrada. Ese es el criterio para decidir qué texto puede ir fijo en la pantalla.

---

## Verificación de esta fase

Corre entera la sección **Fase 2** de `referencia/verificacion.md` y pega la salida
real.

Como comprobación final: cambia el precio de la resina en la barra lateral y
verifica que cambian la métrica y la siguiente respuesta del chat. Los kilos no se
mueven; los dólares sí.
