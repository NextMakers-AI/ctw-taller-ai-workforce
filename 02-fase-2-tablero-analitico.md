# Fase 2 · Tablero analítico con cifras auditables

> **Cómo se usa.** Pásale este archivo entero al mismo agente de código, sobre lo
> que construiste en la fase 1.

## Cómo trabajar conmigo

**No sé programar.** Trabaja de forma autónoma y no me pidas decisiones técnicas.

- Háblame en **español sencillo**, sin jerga y sin trazas de error.
- Si algo falla, **diagnostícalo y arréglalo tú**. Después cuéntame en una frase
  qué pasó y qué hiciste.
- Si de verdad necesitas algo de mí, pídeme **una sola cosa a la vez**.
- **No inventes que verificaste algo.** Corre el comando y mira la salida real.
- Al terminar, dime en pocas frases **qué construiste y qué puedo probar yo**.

---

Ya tienes un asistente con un chat que funciona y dice de dónde sacó cada cifra.
Ahora le pones lo que le falta: **un tablero que muestra lo mismo sin tener que
preguntar**, y los filtros y supuestos que recortan a los dos a la vez.

El chat de la fase 1 no se rehace: se **mueve** a una pestaña y se le enchufan los
filtros. Todo lo que ya funciona ahí se queda como está.

**Lo que se juega esta fase es una sola cosa:** que el tablero y el chat **nunca**
puedan decir cifras distintas para la misma pregunta. Si eso pasa en una
demostración en vivo, se acabó la credibilidad de todo lo demás.

**Al terminar** vas a poder mover un filtro o un supuesto y ver cambiar el tablero
**y** la siguiente respuesta del chat.

---

## Las reglas de la fase 1 siguen valiendo

Español neutro, toda cifra de una herramienta, el bloque de trazabilidad lo arma el
código, ningún número del negocio escrito a mano, y nunca inventes que verificaste.
A esas se suma una nueva, que es la más importante de esta parte:

> **Los gráficos y el chat usan las mismas funciones de cálculo.** Ninguna cifra de
> negocio se calcula fuera del módulo de cálculo.

Si un gráfico hiciera su propia cuenta, tarde o temprano se separa de lo que dice
el chat. Y ese es exactamente el fallo que esta fase existe para hacer imposible.

**Sigue valiendo `referencia/interfaz.md`**, que ahora también trae los colores de
datos, las trampas de la librería de gráficos y los detalles del tablero.

---

# Qué construir

```
app.py                      SE AMPLÍA: barra lateral, dos pestañas, tablero.
src/
  registro.py               NUEVO. EL CONTRATO.
  estilo.py                 SE AMPLÍA: los colores de datos.
  graficos.py               NUEVO. Los 4 gráficos.
```

## Las tres capas y la regla de cada una

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

Que los gráficos y las herramientas llamen a las mismas funciones **es la decisión
de arquitectura más importante del proyecto**. Es lo que hace *imposible* que el
tablero y el chat diverjan.

---

# El contrato

Este es el corazón de la fase, y la razón de que la fase 3 sea posible.

**La pantalla no sabe nada de plásticos.** No sabe qué es el desperdicio, ni qué
líneas hay, ni qué gráficos dibujar. Lee una **declaración del asistente** y de ahí
saca todo: sus fuentes de datos, sus filtros, sus supuestos, sus métricas, sus
gráficos, sus herramientas y sus instrucciones.

En la fase 3 vas a agregar un segundo asistente de un dominio completamente
distinto **sin tocar la pantalla**. Esto es lo único que lo permite.

La declaración tiene cinco piezas:

| Pieza | Qué describe |
|---|---|
| **Campo** | Una columna: cómo se llama, de qué tipo es, cómo se le dice a una persona, y un ejemplo |
| **Fuente** | Un archivo de datos y los campos que trae |
| **Filtro** | Algo por lo que se puede recortar: una lista de opciones o un rango de fechas |
| **Parámetro** | Un supuesto con su rango y su paso |
| **Gráfico** | Un título, la función que lo dibuja, y el pie que lo explica |

Y la declaración del asistente las junta todas, más las herramientas, el prompt,
las métricas y las preguntas sugeridas.

La estructura exacta está en `referencia/interfaz.md`.

**Declara las Fuentes completas ahora**, con su ejemplo, aunque el formulario que
las usa llegue hasta la fase 3. De esa declaración van a salir solos el validador
de archivos y el formulario; agregarlas después obliga a volver sobre todo.

## El pie de cada gráfico se calcula, no se escribe

El pie recibe las cifras del cálculo. Eso es deliberado: **si el archivo de entrada
cambia, el texto bajo el gráfico cambia con él.** Un pie que diga «las seis
categorías» con el número escrito a mano miente en cuanto alguien carga un archivo
con cuatro.

Regla: en un pie solo se escribe a mano lo que describa **cómo leer el gráfico**
(«el número es el % de scrap», «el tooltip trae el `n`»), nunca una afirmación
sobre el dato.

## Las opciones de los filtros salen de los datos

Ninguna lista escrita a mano: si el archivo trae una línea nueva, aparece sola; si
trae una menos, desaparece sola.

---

# Los cuatro gráficos

Ninguno hace cuentas: cada uno llama al módulo de cálculo y devuelve el dibujo y
las cifras. Las mismas cifras alimentan el pie.

| Título | Qué es | Qué lección hace visible |
|---|---|---|
| Desperdicio en kg por tipo de origen | Pareto con curva acumulada | **1 y 4** |
| Exceso de material por línea y SKU | Promedios diarios con su tendencia | **2** |
| Porcentaje de desperdicio (scrap) por lote | Ranking, con los descartados en gris y su `n` | **3** |
| Impacto monetario del desperdicio (scrap) | Costo acumulado, dos franjas | — |

**Cada gráfico es una lección hecha imagen**, salvo el último, que es la cifra que
le importa a quien firma el presupuesto.

Dos cosas que el Pareto tiene que hacer bien, porque son la lección 4:

- **Las barras tienen que medir todas lo mismo** para poder ponerse una al lado de
  la otra: el material rechazado de la línea base, el exceso de cada causa sobre esa
  base, y el material en exceso. Omitir la barra de la línea base haría creer que
  las causas explican todo el desperdicio.
- **El acumulado se calcula sobre las barras del gráfico**, no contra el total de la
  planta. Como las causas se solapan, las barras suman más que el desperdicio real
  — y el pie tiene que decirlo.

Las reglas de forma y las trampas de la librería están en `referencia/interfaz.md`.

---

# La pantalla crece

De la fase 1 hay una sola pantalla con el chat. Ahora:

- La barra lateral suma **selector de asistente, filtros y supuestos**.
- El área principal pasa a **dos pestañas**: **Preguntar** —el chat de la fase 1,
  movido tal cual— y **Tablero**.
- **Todo lo que la pantalla sabía del dominio se muda al contrato.** La interfaz
  deja de nombrar «desperdicio» en ninguna parte.

> En la fase 3 se suman dos pestañas más. Déjalo preparado para que sean **un
> elemento más de una lista**, no un caso especial.

## Los filtros recortan las dos cosas

Un filtro no es solo del tablero: **las herramientas del chat reciben la misma
vista recortada.** Si el usuario filtra por L1, la siguiente respuesta del chat
habla solo de L1, y el bloque de trazabilidad lo demuestra con menos filas.

**Dilo en la barra lateral**, porque si no la gente asume que el chat lo ve todo.

El rango de fechas se reconcilia con los datos: si nadie lo estrechó a mano, sigue
a los datos.

## Los supuestos van aparte

En su propio grupo, separados de los filtros, porque **son de otra naturaleza**: un
filtro recorta el dato, un supuesto le pone precio.

Están en la pantalla y no en el código porque **quien presenta tiene que poder
cambiarlos en vivo** cuando alguien de la sala diga «ese precio no es el nuestro» —
que es la pregunta que siempre aparece.

---

# La pestaña Preguntar

El chat entero viene de la fase 1 y **no se rehace**. Solo cambian tres cosas:

1. **Vive dentro de una pestaña.**
2. **Recibe la vista filtrada**, junto con los supuestos. Se sigue reconfigurando
   una vez por pregunta.
3. **Su estado lleva el asistente adentro**, porque en la fase 3 va a haber dos
   conversaciones distintas.

# La pestaña Tablero

Arriba las métricas, debajo una nota, y después los gráficos en rejilla de dos
columnas.

## Las métricas

Cuatro, y **las dos primeras son la lección 1 hecha número**: material rechazado y
material en exceso, separados. La primera cosa que ve quien abre la aplicación es
que el desperdicio son dos cosas.

El texto pequeño bajo cada métrica **no es una comparación contra un periodo
anterior**: es contexto de la misma cifra — «7.555 USD» bajo los kilos, «6,50 % del
consumo» bajo el scrap.

## La nota del tablero

Debajo de las métricas, una línea que explique lo que las cifras no dicen solas:

> El **material en exceso** se cuantifica desde los pesos de control de calidad, no
> desde la báscula de rechazos: es material que sale dentro de producto conforme.

**Es una definición, no una cifra.** Sigue siendo cierta con cualquier archivo de
entrada. Esa es la vara para decidir qué texto puede ir fijo en la pantalla.

---

## Verificación de esta fase

```bash
.venv/bin/python -c "
from src import registro, carga, estilo
import re
for m in (False, True):
    c = estilo.css(m)
    assert not re.findall(r'\{[a-z_\[\]\047\"]+\}', c), 'marcador sin resolver'
    assert 'var(--' not in c, 'quedó un var(--x) que Streamlit no expone'
print('css resuelto en los dos modos, sin var(--x)')
d = carga.cargar()
a = registro.por_clave('desperdicio')
for g in a.graficos:
    ch, res = g.fn(d, a.parametros[0].valor)
    ch.to_dict()
    assert g.pie(res), f'pie vacío en {g.titulo}'
    print(f'  {g.titulo}: ok')
"
grep -rn "groupby" app.py src/graficos.py
.venv/bin/streamlit run app.py --server.port 8501
```

El `grep` no debería devolver ninguna cifra de negocio.

Con la app corriendo (arranca en **oscuro**, y así se queda):

1. Las dos pestañas abren sin excepción y **cero trazas en consola** al arrancar.
2. El chat **sigue funcionando igual que en la fase 1** ahora que está dentro
   de una pestaña: la caja llega al pie, su alto no cambia al empezar a responder,
   las sugerencias lanzan la pregunta, la pastilla va a la derecha con el texto
   dentro del fondo, y una respuesta larga con tablas no produce scroll horizontal.
3. Ninguna píldora de delta en verde con flecha; ningún número de métrica cortado.
4. Los cuatro gráficos con su pie, sin etiquetas de eje recortadas.
5. Recargar en `?agente=desperdicio&tab=tablero` deja donde estaba.
6. Pon un filtro de línea y pregunta: el bloque de trazabilidad del chat tiene que
   bajar de filas. **Es la prueba de que el filtro llegó al agente y no solo al
   tablero.**
7. **La demostración que importa**: cambia el precio de la resina en la barra
   lateral y mira cambiar la métrica **y** la siguiente respuesta del chat. Los
   kilos no se mueven; los dólares sí.
