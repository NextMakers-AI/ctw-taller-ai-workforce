# Referencia · La pantalla del asistente

> **Esto no se lee en voz alta.** Es la guía de implementación de la interfaz que
> el agente de código sigue al pie de la letra. Recoge las trampas de Streamlit y
> los patrones visuales que ya están verificados: cada una de estas notas existe
> porque algo se veía mal y costó encontrarlo.
>
> Se usa desde la fase 1 y sigue valiendo en las fases 2 y 3.

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


---
---

# Fase 2 · El tablero

> Todo lo de abajo entra con el tablero. Igual que arriba: son las trampas ya
> resueltas, no sugerencias.

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

## Reglas de forma

**Nunca un eje doble.** Dos escalas *y* distintas en un gráfico es el error número
uno. **Excepción única y legítima:** el Pareto, donde la curva acumulada va en
porcentaje contra el eje derecho — ahí el segundo eje es parte de la forma
canónica.

**Las barras de un Pareto van de un solo color.** La categoría ya está escrita en
el eje; pintar cada barra distinto sugiere una distinción que no existe. Excepción
acá: **una** barra en otro color, la del material en exceso, porque se cuantifica
desde otra fuente de medición. Eso sí codifica algo.

**El texto lleva tokens de texto, nunca el color de la serie.**

Las barras del Pareto tienen que medir **todas lo mismo** para poder ponerse una
al lado de la otra: el material rechazado del nivel base, el exceso de cada causa
sobre esa base, y el material en exceso. Omitir la barra del nivel base haría creer que las
causas atribuidas explican todo el scrap. Y **el acumulado se calcula sobre las
barras del gráfico**, no contra el total de la planta: como las causas se solapan,
las barras suman algo más que el desperdicio real, y el pie tiene que decirlo.

## Trampas de Altair

- **La leyenda de `strokeDash` muestra círculos idénticos.** Por defecto dibuja el
  símbolo relleno, no el trazo: `legend=alt.Legend(symbolType="stroke")`.
- **Las etiquetas de eje se recortan.** `labelLimit` por defecto es corto: súbelo
  a 220 cuando las categorías tengan nombres largos.
- **El separador de miles del eje sale en inglés** (`20,000`). Usa `format="~s"`
  (`20k`), que se lee igual en español.

## Modo oscuro elegido, no volteado

Los pasos de los colores de serie se **re-eligieron** para la superficie #09090B y
se validaron contra ella. Un volteo automático del modo claro produce colores que
pasaban sobre blanco y fallan sobre negro.

---

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

---

## Las trampas sueltas del tablero

**Los filtros: el estado que Streamlit borra.** Al cambiar de asistente, los
filtros del otro no se renderizan y Streamlit borra su estado; al volver, aparecen
reseteados. La solución es espejar el valor en una clave propia por agente —que
Streamlit no limpia— y desde ahí recalcular el valor inicial de cada control:

```python
vista_previa = st.session_state.setdefault(k(clave, "vista"), {})
valor = st.selectbox(f.etiqueta, opciones,
                     index=opciones.index(vista_previa.get(f.clave, opciones[0])))
vista_previa[f.clave] = valor
```

> **Estos widgets NO llevan `key=`.** Si lo llevaran, el estado del widget le
> ganaría al valor que le pasas por `index=`/`value=` y el espejo no serviría para
> nada. Es contraintuitivo y es exactamente lo que hay que hacer.

**El estado va por agente.** Chat y filtros viven en claves separadas:

```python
def k(clave: str, *partes: str) -> str:
    """Clave de session_state con el agente adentro: cada uno con su estado."""
    return "__".join([clave, *partes])
```

**El supuesto numérico.** `st.number_input` con `format="%d"` y un `value`
flotante lanza `NumberInput value has type float but format %d`. Usa `"%.0f"`.

**La rejilla del tablero es de dos columnas, no de tres.** Con tres por fila las
etiquetas de eje se recortan.

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

**`st.metric` pinta el delta en verde y con flecha hacia arriba** cuando lo
interpreta como positivo. Eso **afirma una mejora que nadie dijo** — «6,5 % del
consumo» no es una buena noticia. Neutralízalo por CSS: fondo, color y flecha.

**La unidad va en la ETIQUETA, no en el valor**, cuando el valor es largo:
`st.metric` recorta el valor si no cabe, y un número cortado es peor que ninguno.

**El chat, al entrar en una pestaña, deja de anclarse al pie por su cuenta.** Por
eso se construyó desde la fase 1 dentro de la caja de alto fijo: si se respetó esa
estructura, mudarlo no cuesta nada.

**Streamlit no recarga un módulo ya importado**, así que al cambiar `estilo.py` o
`registro.py` hay que reiniciar el proceso.


---
---

# Fase 3 · El segundo tablero y la pestaña Datos

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

Al aceptar hay que **invalidar las cachés de datos**: los marcos cambiaron y
cualquier resultado memorizado apunta a filas que ya no existen. Es el tipo de bug
que no da error, solo devuelve cifras equivocadas.

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
