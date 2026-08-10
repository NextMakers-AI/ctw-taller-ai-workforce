# Fase 2 · Tablero analítico con cifras auditables

> **Cómo se usa.** Pega este archivo entero en el mismo agente de código, sobre lo
> que construiste en la fase 1.

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

Ya tienes un asistente con un chat que funciona y dice de dónde sacó cada cifra.
Ahora le pones lo que le falta: **un tablero que muestra lo mismo sin tener que
preguntar**, y los filtros y supuestos que recortan a los dos a la vez.

El chat de la fase 1 no se rehace: se **mueve** a una pestaña y se le
enchufan los filtros. Todo lo que ya funciona ahí —la caja de alto fijo, las
pastillas, el streaming, el bloque de trazabilidad— se queda como está.

**Lo que se juega esta fase es una sola cosa:** que el tablero y el chat
**nunca** puedan decir cifras distintas para la misma pregunta. Si eso pasa en una
demostración en vivo, se acabó la credibilidad de todo lo demás.

**Al terminar** vas a poder abrir `http://localhost:8501`, preguntarle al agente
viéndolo consultar los datos, y mover un filtro o un supuesto y ver cambiar el
tablero **y** la siguiente respuesta del chat.

---

## Las reglas de la fase 1 siguen valiendo

Español neutro, toda cifra de una herramienta, el bloque de trazabilidad lo arma
el código, ningún número del negocio escrito a mano, y nunca inventes que
verificaste. A esas se suma una nueva, que es la más importante de esta parte:

> **Los gráficos y el chat usan las mismas funciones de cálculo.** Ni un `groupby`
> fuera de `calculos.py`.

La regla exacta es más fina que «ni un groupby»: ninguna **cifra de negocio** se
calcula fuera del módulo de cálculo. Agrupar para **presentación** sí se permite —
binificar un histograma, por ejemplo: ahí el `groupby` no produce una cifra que
alguien vaya a citar, produce los bordes de las barras, y además evita mandarle a
Altair 28.000 filas crudas. **Si dejas uno, escribe en el comentario por qué no es
una cifra.** Cualquier otro es un error.

---

# Qué construir

```
app.py                      SE AMPLÍA: barra lateral, dos pestañas, tablero.
                            Ni un groupby acá.
src/
  registro.py               NUEVO. EL CONTRATO: Campo, Fuente, Filtro, Parametro,
                            Grafico, AgenteDef + la instancia del agente.
  estilo.py                 SE AMPLÍA: paleta validada, escalas y tema de Altair.
                            Los tokens y el CSS ya están de la fase 1.
  graficos.py               NUEVO. Los 6 gráficos. Ni un groupby.
.streamlit/config.toml      Ya está, copiado tal cual en la fase 1.
assets/                     Ya está: el logo y el favicon.
```

## Las tres capas y la regla de cada una

```
        ┌───────────────────────────────────────────────┐
        │  app.py            interfaz — CERO groupby     │
        ├──────────────┬────────────────────────────────┤
        │ graficos.py  │ herramientas.py   (@tool)      │
        │              │                                │
        │       las dos llaman a lo mismo ↓             │
        ├───────────────────────────────────────────────┤
        │  calculos.py    LA ÚNICA FUENTE DE CIFRAS     │
        ├───────────────────────────────────────────────┤
        │  carga.py       Datos (dataclass congelado)   │
        └───────────────────────────────────────────────┘
```

Que los gráficos y las herramientas llamen a las mismas funciones **es la decisión
de arquitectura más importante del proyecto**. Es lo que hace *imposible* que el
tablero y el chat diverjan. Si un gráfico tuviera su propio `groupby`, tarde o
temprano se separa.

---

# `src/registro.py` — el contrato

**La interfaz no sabe nada de sopladoras ni de empacadoras.** Lee un *registro de
agentes* y de ahí saca las fuentes, los filtros, los parámetros, las métricas, los
gráficos, las herramientas y el prompt. En la fase 3 vas a agregar un segundo
asistente de otro dominio **sin tocar `app.py`**, y esto es lo que lo permite.

```python
@dataclass(frozen=True)
class Campo:
    nombre: str          # el nombre real de la columna en el CSV
    tipo: str            # texto | texto_largo | numero | entero | fecha | hora | opcion
    etiqueta: str        # cómo se le dice a una persona
    opciones: tuple = ()           # lista fija de valores
    opciones_de: str | None = None # o derivadas de una columna de los datos
    obligatorio: bool = True
    ayuda: str = ""      # el tooltip
    defecto: Any = None
    ejemplo: str = ""    # EL PLACEHOLDER, y no es opcional

@dataclass(frozen=True)
class Fuente:
    clave: str; nombre: str; archivo: str; descripcion: str
    campos: tuple[Campo, ...]

@dataclass(frozen=True)
class Filtro:
    clave: str; etiqueta: str; tipo: str   # opcion | rango_fechas
    opciones_de: str | None = None
    etiquetas: dict | None = None
    mostrar: Callable | None = None

@dataclass(frozen=True)
class Parametro:
    clave: str; etiqueta: str; valor: float
    minimo: float; maximo: float; paso: float; formato: str; ayuda: str

@dataclass(frozen=True)
class Grafico:
    titulo: str
    fn: Callable[..., tuple[Any, dict]]   # devuelve (gráfico, cifras)
    pie: Callable[[dict], str] = lambda _: ""

@dataclass(frozen=True)
class AgenteDef:
    clave, nombre, icono, resumen
    fuentes, filtros, parametros
    cargar, desde_marcos, filtrar, configurar, registro_actual, contexto
    herramientas, prompt, metricas, graficos, preguntas
    columnas_texto, coleccion_semantica, marco_principal
    nombres_fuentes, nota_dashboard
```

Aunque los campos de `Fuente` no se usan todavía —el formulario llega en la
fase 3— **decláralos completos ahora**, con su `ejemplo`. De esa declaración
van a salir solos el validador de CSV y el formulario, y agregarlos después
obligaría a volver sobre todo.

### El pie de cada gráfico recibe las cifras, no es prosa fija

`Grafico.pie` es una función que recibe el diccionario del cálculo. Eso es
deliberado: **si el archivo de entrada cambia, el texto bajo el gráfico cambia con
él.** Un pie que diga «las seis categorías» con el número escrito a mano miente en
cuanto alguien carga un archivo con cuatro.

Regla: en un pie solo se escribe a mano lo que describa la *codificación* («el
número es el % de scrap», «el tooltip trae el `n`»), nunca una afirmación sobre el
dato.

### Las opciones de los filtros se derivan de los datos

Ninguna lista escrita a mano: si el archivo trae una línea nueva, aparece sola; si
trae una menos, desaparece sola.

---

# `src/estilo.py` — el sistema visual, ahora con color de datos

De la fase 1 ya están los tokens, la hoja de estilos como **función del
modo** (Streamlit 1.61 no expone ninguna variable CSS), `key=` como único ancla
estable y el naranja de marca con su tinta oscura encima. **Nada de eso se
rehace.** Lo que se agrega acá es todo lo que solo existe cuando hay algo que
pintar.

## Dos tokens más

Al diccionario de tokens se le suman los que solo usan los gráficos:

```python
CLARO  = { ..., "grilla": "#F1F1F2", "neutral_serie": "#71717A" }
OSCURO = { ..., "grilla": "#1C1C1F", "neutral_serie": "#A1A1AA" }
```

## Las dos paletas, y por qué son seis colores

```python
SERIES_CLARO  = ("#EB652B", "#A43650", "#069FF9", "#E35EBD", "#40C68B", "#7756DC")
SERIES_OSCURO = ("#EB652B", "#AB2440", "#1E8FEE", "#D551B1", "#00A66D", "#7546CA")

SECUENCIAL_CLARO  = ("#E6A188", "#DB8261", "#CF6136", "#C13D00", "#9F2E00", "#7C2400")
SECUENCIAL_OSCURO = ("#79371D", "#9D431E", "#C24E1C", "#E45E24", "#FA7A48", "#FF9B73")
```

**Que sean seis es un hallazgo de la verificación, no un recorte por gusto.** Con
ocho falla en oscuro: la banda de luminosidad ahí es angosta y ocho tonos se
pisan — el ámbar y el naranja quedaban a ΔE 0,5 bajo deuteranopía, o sea el mismo
color. Verificadas en modo **todos los pares**: peor par CVD ΔE 10,6 en claro y
9,3 en oscuro, visión normal ΔE 18,5 en ambos.

El **orden es el mismo en los dos modos** a propósito: la serie *i* tiene que ser
la misma entidad en claro y en oscuro.

Los números completos de la verificación están en
`referencia/paleta-validada.md`. **Cópialos tal cual: si cambias un hex, la
verificación deja de valer.**

### Las dos escalas

- **`escala(dominio, neutral=None)`** — por entidad. El dominio se pasa explícito
  y completo para que un filtro que cambie la cantidad de series no repinte a las
  que quedan. `neutral` va en gris: «no sabemos» no es un par de las demás.
- **`escala_calida(dominio, neutral=None)`** — monocromática. **Su límite está
  medido:** como escala ordinal pasa todo, pero como escala de *identidad* con seis
  pasos el peor par queda en ΔE 7,8 contra un piso de 15. Con hasta **tres**
  categorías los pasos se reparten a lo ancho (índices 0, 2 y 5) y sube a ΔE 16,2;
  con **cuatro o más**, quien la use **tiene que poner etiquetas directas**.

### `serie(i)` no cicla

Pasado el último color **lanza `IndexError`** con un mensaje que dice qué hacer.
Si un día hacen falta más series, la respuesta no es generar un color nuevo —que
rompería la verificación— sino agrupar el resto en «Otras» o separar el gráfico.

## El modo activo ya es estado de módulo

Viene de la fase 1, y ahora se entiende para qué: las funciones de gráficos
lo leen de ahí en vez de recibirlo por parámetro. Eso asume **un proceso por
persona**, que es exactamente la restricción de este taller.

## Los patrones de componente que se suman

A los de la fase 1 —Card, SidebarGroupLabel, Muted surface, Badge, Button,
Separator, Avatar— se les agregan dos:

| Componente shadcn | Cómo se ve acá |
|---|---|
| **SidebarMenu** | El selector de asistente es una **lista de navegación, no un radio**: activo en pastilla translúcida del primario |
| **Tabs** | Subrayado del primario en la activa, no pastilla rellena |

Y las tarjetas de KPI del tablero son **Card**, igual que la caja del chat.

### Cuatro detalles que se ven mal si no se cuidan

- El **hover** de un ítem de navegación no puede quedar blanco sobre blanco: fija
  fondo y color explícitos en cada estado, no confíes en heredar.
- El **activo va translúcido**, no relleno sólido: un bloque de color saturado en
  la barra lateral pesa más que el contenido de la página.
- **Espacio entre ítems con `margin-bottom` en el botón**, no con `gap` del
  bloque: con `gap` los ítems se montan sobre la etiqueta del grupo.
- **Sin `help=` en la navegación.** El tooltip de Streamlit es una caja grande que
  **tapa el ítem activo** y desplaza el layout. La descripción va como texto
  debajo de la lista.

---

# `src/graficos.py` — los seis

**Ni un `groupby` en este módulo.** Cada función llama a `calculos.py` y devuelve
`(gráfico, cifras)`. Las mismas cifras alimentan el pie.

| Título | Qué es |
|---|---|
| ¿De qué tipo es el desperdicio? | **Pareto** con curva acumulada |
| ¿Dónde y cuándo se concentra? | Mapa de calor línea × turno |
| ¿Cuánto nos alejamos del objetivo? | Histograma del delta de peso |
| ¿Se desgasta o está descalibrada? | Medias diarias + regresión, trazo por clasificación |
| ¿Qué lote se comporta distinto? | Ranking con los descartados en gris y su `n` |
| ¿Cuánto llevamos gastado? | Costo acumulado, dos franjas |

## Reglas de forma

**Nunca un eje doble.** Dos escalas *y* distintas en un gráfico es el error número
uno. **Excepción única y legítima:** el Pareto, donde la curva acumulada va en
porcentaje contra el eje derecho — ahí el segundo eje es parte de la forma
canónica.

**Las barras de un Pareto van de un solo color.** La categoría ya está escrita en
el eje; pintar cada barra distinto sugiere una distinción que no existe. Excepción
acá: **una** barra en otro color, la del gramaje exceso, porque es la categoría
que la planta no ve. Eso sí codifica algo.

**El texto lleva tokens de texto, nunca el color de la serie.**

Las barras del Pareto tienen que medir **todas lo mismo** para poder ponerse una
al lado de la otra: el scrap del nivel base, el exceso de cada causa sobre esa
base, y el gramaje exceso. Omitir la barra del nivel base haría creer que las
causas atribuidas explican todo el scrap. Y **el acumulado se calcula sobre las
barras del gráfico**, no contra el total de la planta: como las causas se solapan,
las barras suman algo más que el desperdicio real, y el pie tiene que decirlo.

## Trampas de Altair

- **Un histograma pre-binificado dibuja púas de 1 px.** Si los datos ya vienen
  agrupados, `mark_bar()` no sabe el ancho de cada barra: hay que dar la extensión
  explícita con `x="inicio:Q", x2="fin:Q"`.
- **La leyenda de `strokeDash` muestra círculos idénticos.** Por defecto dibuja el
  símbolo relleno, no el trazo: `legend=alt.Legend(symbolType="stroke")`.
- **Las etiquetas de eje se recortan.** `labelLimit` por defecto es corto: súbelo
  a 220 cuando las categorías tengan nombres largos.
- **El separador de miles del eje sale en inglés** (`20,000`). Usa `format="~s"`
  (`20k`), que se lee igual en español.

## El mapa de calor y la tinta del número

En un mapa de calor, la tinta del número **cambia con el relleno de su celda**:
sobre los pasos oscuros de la rampa un texto oscuro no se lee.

> **Y la tinta del extremo fuerte depende del MODO**, porque las dos rampas corren
> en sentidos opuestos de luminosidad:
>
> - en claro la rampa va de claro a oscuro → el valor más alto cae sobre un
>   relleno **oscuro** y su número va en **blanco**;
> - en oscuro va de oscuro a claro —tiene que despegar del fondo #09090B— → el
>   valor más alto cae sobre el relleno **más claro**, donde un blanco da ~2:1 e
>   ilegible: ahí va la **tinta oscura**.
>
> Un `alt.value("#FFFFFF")` fijo funciona en claro y falla en oscuro. Sácalo a una
> función que reciba el modo. Es el tipo de error que no rompe nada, no pone
> ninguna prueba en rojo, y solo se nota si uno **no** sabe ya qué número dice ahí.

## Modo oscuro elegido, no volteado

Los pasos de los colores de serie se **re-eligieron** para la superficie #09090B y
se validaron contra ella. Un volteo automático del modo claro produce colores que
pasaban sobre blanco y fallan sobre negro.

---

# `app.py` — el armazón crece

De la fase 1 hay una sola pantalla con el chat y una barra lateral con la
ficha de la planta. Ahora:

- La barra lateral suma **selector de asistente, filtros y supuestos**.
- El área principal pasa a **dos pestañas**: **Preguntar** —el chat de la
  fase 1, movido tal cual— y **Tablero**. En la fase 3 se suman
  «Generar reporte» y «Datos»: déjalo preparado para que sean **un elemento más de
  una lista**, no un `if`.
- Todo lo que app.py sabía del dominio se muda al registro. La interfaz deja de
  nombrar «desperdicio» en ninguna parte.

**Sin título de página sobre las pestañas.** La navegación de la barra lateral ya
dice qué asistente está activo; un `h1` encima solo repetiría eso y empujaría el
contenido hacia abajo.

> El chat, al entrar en una pestaña, deja de anclarse al pie por su cuenta. Por
> eso se construyó desde la fase 1 dentro de la caja de alto fijo: si
> respetaste esa estructura, mudarlo no cuesta nada. Si no, ahora se nota.

**La caché ya está** (`cache_data` para los archivos, `cache_resource` para los
datos y el agente), y sigue valiendo la trampa: **Streamlit no recarga un módulo
ya importado**, así que al cambiar `estilo.py` o `registro.py` hay que reiniciar
el proceso.

## Estado por agente

Chat y filtros viven en claves separadas por agente:

```python
def k(clave: str, *partes: str) -> str:
    """Clave de session_state con el agente adentro: cada uno con su estado."""
    return "__".join([clave, *partes])
```

## Las pestañas y la persistencia en la URL

Un F5 abre una sesión nueva y **el estado de sesión se pierde entero**. La URL es
lo único que sobrevive, así que agente y pestaña van en `st.query_params`:
`http://localhost:8501/?agente=desperdicio&tab=tablero`.

> **La trampa del `default` de `st.tabs`.** Pasarlo en **cada** corrida hace que la
> pestaña vuelva sola a la de la URL apenas se hace clic en otra: el clic cambia el
> estado y el `default` de la corrida siguiente lo pisa. La pestaña parece no
> responder. Pásalo **solo en la primera corrida** de ese agente.

Y **escribe la URL solo si cambió**: asignar el mismo valor en cada corrida
provoca otra reejecución y el ciclo no para nunca.

## Los filtros, y la trampa más molesta de todas

Al cambiar de asistente, los filtros del otro **no se renderizan y Streamlit borra
su estado**. Al volver, aparecen reseteados.

La solución es espejar el valor en una clave propia por agente —que Streamlit no
limpia— y desde ahí recalcular el valor inicial de cada control:

```python
vista_previa = st.session_state.setdefault(k(clave, "vista"), {})
valor = st.selectbox(f.etiqueta, opciones,
                     index=opciones.index(vista_previa.get(f.clave, opciones[0])))
vista_previa[f.clave] = valor
```

> **Estos widgets NO llevan `key=`.** Si lo llevaran, el estado del widget le
> ganaría al valor que le pasas por `index=`/`value=` y el espejo no serviría para
> nada. Es contraintuitivo y es exactamente lo que hay que hacer.

**El rango de fechas se reconcilia con los datos actuales**: si el usuario no lo
estrechó a mano, sigue a los datos.

**Los filtros aplican TAMBIÉN al chat**, no solo al tablero: las herramientas
reciben la vista filtrada. **Dilo en la barra lateral**, porque si no la gente
asume que el chat ve todo. Y el bloque de trazabilidad es la prueba.

## Los supuestos

En su propio grupo, separados de los filtros, porque **son de otra naturaleza**:
un filtro recorta el dato, un supuesto le pone precio. Están en la interfaz y no
en el código porque **quien presenta tiene que poder cambiarlos en vivo** cuando
alguien de la sala diga «ese precio no es el nuestro» — que es la pregunta que
siempre aparece.

> **Trampa:** `st.number_input` con `format="%d"` y un `value` flotante lanza
> `NumberInput value has type float but format %d`. Usa `"%.0f"`.

---

# La pestaña Preguntar — lo que cambia

El chat entero viene de la fase 1 y **no se rehace**: la caja de alto fijo,
las pastillas asimétricas, las sugerencias, el streaming con el nombre de la
herramienta en vivo y el bloque de trazabilidad se mudan tal cual dentro de la
pestaña. Si algo de eso se rompió al mudarlo, el problema es la estructura de la
caja, no la pestaña.

Acá solo cambian tres cosas:

1. **Vive dentro de `st.tabs`.** Ahí `st.chat_input` deja de anclarse al pie por
   su cuenta: el alto fijo de la caja y el `flex` de la transcripción son lo que
   lo sostienen.
2. **Recibe la vista filtrada.** `configurar()` deja de recibir los datos
   completos y pasa a recibir el recorte de la barra lateral, junto con los
   supuestos. Sigue llamándose **una vez por pregunta**.
3. **El estado del chat pasa a llevar el agente adentro** (`k("chat", clave)`),
   porque en la fase 3 va a haber dos conversaciones distintas.

Todo lo demás —incluido que un fallo del modelo no puede tumbar la interfaz y el
reintento silencioso del `already processing`— ya está escrito y funcionando.

---

# La pestaña Tablero

```python
cols = st.columns(len(a.metricas(vista, params)))
for col, m in zip(cols, a.metricas(vista, params)):
    col.metric(m["etiqueta"], m["valor"], m["delta"])
if a.nota_dashboard:
    st.caption(a.nota_dashboard)
st.divider()

for i in range(0, len(a.graficos), 2):
    for col, g in zip(st.columns(2), a.graficos[i:i + 2]):
        with col:
            st.subheader(g.titulo)
            chart, res = g.fn(vista, params[a.parametros[0].clave])
            st.altair_chart(chart, width="stretch")
            if pie := g.pie(res):
                st.caption(pie)
```

`width="stretch"` reemplaza al `use_container_width` obsoleto.

**Rejilla de dos columnas, no de tres.** Con tres por fila las etiquetas de eje se
recortan y los mapas de calor quedan ilegibles.

## Las métricas

Cuatro, y **las dos primeras son la lección 1 hecha número**: scrap pesado y
gramaje exceso, separados. La primera cosa que ve quien abre la aplicación es que
el desperdicio son dos cosas.

El `delta` **no es una comparación contra un periodo anterior**: es contexto de la
misma cifra —«7.555 USD» bajo los kilos, «6,50 % del consumo» bajo el scrap—.
Nombrarlo «delta» es de Streamlit, no del dominio.

> **Trampa visual:** `st.metric` pinta el delta **en verde y con flecha hacia
> arriba** cuando lo interpreta como positivo. Eso **afirma una mejora que nadie
> dijo** — «6,5 % del consumo» no es una buena noticia. Neutralízalo por CSS:
> fondo, color y flecha.

> **Y la unidad va en la ETIQUETA, no en el valor**, cuando el valor es largo:
> `st.metric` recorta el valor si no cabe, y un número cortado es peor que ninguno.

## La nota del tablero

Debajo de las métricas, una línea que explique lo que las cifras no dicen solas:

> El **gramaje exceso** no aparece en ningún reporte de scrap de la planta: es
> material regalado dentro de producto conforme, que se despacha.

**Es una definición, no una cifra.** Sigue siendo cierta con cualquier archivo de
entrada. Esa es la vara para decidir qué texto puede ir fijo en la interfaz.

## Cuando el filtro no deja nada

```python
if getattr(vista, a.marco_principal).empty:
    st.error("El filtro no deja ningún registro. "
             "Amplía el rango o quita una condición.")
```

Un tablero de gráficos vacíos sin explicación parece una aplicación rota. El
mensaje tiene que decir **qué hacer**, no solo qué pasó.

---

## Iconos: Material Symbols, nunca unicode

```python
st.tabs([":material/forum: Preguntar", ":material/monitoring: Tablero"])
```

Un emoji o un carácter unicode se dibuja con la fuente del sistema: se ve distinto
en macOS, Windows y Linux, cambia de ancho y rompe la alineación de una fila de
pestañas.

**Solo se resuelven en etiquetas de widget**, no dentro de HTML crudo: un
`:material/mail:` dentro de un `<a>` escrito con `unsafe_allow_html=True` sale como
**texto literal**.

El logo va con `st.logo("assets/next-makers-log.png", size="medium")`, que lo
coloca arriba de la barra lateral por sí solo. El favicon es
`assets/favicon.png` — la marca recortada, no el logotipo: a 32 px un logotipo con
texto no es legible.

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

El `grep` no debería devolver ninguna cifra de negocio. Si dejaste un `groupby` de
presentación, tiene que estar el comentario que dice por qué no es una cifra.

Con la app corriendo (arranca en **oscuro**, y así se queda):

1. Las dos pestañas abren sin excepción y **cero trazas en consola** al arrancar.
2. El chat **sigue funcionando igual que en la fase 1** ahora que está dentro
   de una pestaña: la caja llega al pie, su alto no cambia al empezar a responder,
   las sugerencias lanzan la pregunta, la pastilla va a la derecha con el texto
   dentro del fondo, y una respuesta larga con tablas no produce scroll horizontal.
3. Ninguna píldora de delta en verde con flecha; ningún número de métrica cortado.
4. Los seis gráficos con su pie, sin etiquetas de eje recortadas.
5. Recargar en `?agente=desperdicio&tab=tablero` deja donde estaba.
6. Pon un filtro de línea y pregunta: el bloque de trazabilidad del chat tiene que
   bajar de filas. **Es la prueba de que el filtro llegó al agente y no solo al
   tablero.**
7. **La demostración que importa**: cambia el precio de la resina en la barra
   lateral y mira cambiar la métrica **y** la siguiente respuesta del chat. Los
   kilos no se mueven; los dólares sí.
