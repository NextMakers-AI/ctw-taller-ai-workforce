# 09 · El chat

La pestaña **Preguntar**. Es donde el taller se juega su credibilidad: aquí se ve al
agente consultar los datos en vivo, y eso es lo que distingue «el modelo dijo un
número» de «el modelo consultó y reportó un número».

## El problema de partida

`st.chat_input` **dentro de una pestaña se dibuja en línea**, no anclado al pie de la
ventana como en una aplicación de chat. Sin una estructura explícita, el campo de
entrada termina **arriba** de los mensajes. Esa fue la razón principal de que la
primera versión «no pareciera un chat».

## La estructura, de fuera hacia adentro

Todo dentro de **una sola caja con borde**, para que se lea como un componente y no
como tres cosas sueltas apiladas:

```python
with st.container(border=True, key="caja_chat"):
    # 1. barra de acciones (solo si ya hay conversación)
    # 2. transcripción, con su propio scroll
    # 3. sugerencias (solo si NO hay conversación)
    # 4. st.chat_input
```

`key=` no es para el estado: es el único ancla CSS estable (ver `08`).

### La caja llega hasta el pie de la pantalla

```css
.st-key-caja_chat {
  height: calc(100vh - 118px) !important;
  min-height: 320px;
  flex: 0 0 auto;
}
```

El `!important` y el `flex-shrink: 0` son los dos necesarios: Streamlit dimensiona
sus bloques por contenido y, sin las dos cosas, la caja se encoge al ritmo de la
conversación en vez de quedarse quieta.

### La transcripción es lo elástico

Se queda con todo el espacio que sobra, de modo que **el campo de entrada siempre
toca el pie de la pantalla**.

```css
.st-key-transcripcion {
  flex: 1 1 auto;
  height: auto !important;
  min-height: 0 !important;     /* deja que un hijo flexible encoja bajo su contenido */
  overflow-y: auto;
  overflow-x: hidden;
}
```

> **Trampa que cuesta una hora:** Streamlit envuelve cada contenedor en un
> `stLayoutWrapper` y **al envoltorio es al que le pone el alto** (`flex: 0 0 430px`).
> Estirar solo el bloque de adentro no sirve de nada. Hay que soltar los dos:
>
> ```css
> .st-key-caja_chat > [data-testid="stLayoutWrapper"]:has(> .st-key-transcripcion) {
>   flex: 1 1 auto !important; height: auto !important;
> }
> ```

### Dos cosas de Streamlit que rompen esta estructura

Las dos hacen lo mismo: el campo de entrada se va al tope o se convierte en una
caja gigante, y la conversación se queda sin sitio.

**1. Un `st.container()` vacío NO llega al DOM.** Sin conversación, el contenedor
de la transcripción no existe, la caja se queda sin su elemento elástico y el
campo de entrada sube. Hay que meterle un hueco de 1 px cuando no hay mensajes:

```python
if not st.session_state[clave_chat]:
    st.markdown('<div class="hueco-transcripcion"></div>', unsafe_allow_html=True)
```

**2. `st.chat_input` se estira dentro de un contenedor flex.** No basta con fijar
el `flex` de su contenedor: sus divisiones internas llevan `flex: 1 1 0%` y
arrastran el `textarea` hasta ~170 px, o sea seis líneas de alto vacías. Hay que
neutralizar las dos divisiones y devolverle al `textarea` su alto de contenido:

```css
.st-key-caja_chat [data-testid="stChatInput"] > div,
.st-key-caja_chat [data-testid="stChatInput"] > div > div { flex: 0 0 auto !important; }
.st-key-caja_chat [data-testid="stChatInputTextArea"] {
  height: auto !important; min-height: 1.5rem !important; max-height: 7.5rem !important;
}
```

El `max-height` no es defensivo: es el comportamiento correcto de un chat — crece
con el texto hasta unas líneas y después hace scroll adentro.

### El alto es FIJO, jamás adaptativo

Hacer que dependa de si hay conversación —más baja cuando está vacía— encoge la caja
**justo cuando el agente empieza a responder**, que es el peor momento posible para
mover el layout. Se probó y se revirtió.

## Los mensajes

`st.chat_message` dibuja avatar y texto plano, sin burbujas: no lee como una
conversación. El patrón correcto es **asimétrico**:

- **La pregunta**: pastilla a la derecha, fondo del primario, radio
  `1rem 1rem 0.25rem 1rem`, ancho máximo 70 %, avatar del usuario oculto.
- **La respuesta**: texto corrido con su avatar a la izquierda. Meterla en burbuja
  sería un error — son reportes largos, con listas, tablas y bloques de código.

### Cuatro defectos de render y su causa

**1. El texto se salía por fuera del fondo de color.** Streamlit le pone a
`stMarkdownContainer` un **margen inferior negativo de 15 px** para compensar el
margen de los párrafos. Al quitarle el margen al párrafo de la pastilla, esa
compensación se queda sin contraparte: el bloque medía 8 px donde el texto medía 23.
Donde anules el margen del párrafo, **anula también el negativo del contenedor**.

**2. La pastilla salía centrada** aunque la fila tuviera `justify-content: flex-end`.
Se resuelve con `margin-left: auto; margin-right: 0` sobre el contenido, que no
depende de quién gane la regla de la fila.

**3. Desborde horizontal de ~34 px** — exactamente el ancho del avatar más su
separación. El ancho se reparte **distinto según el rol**:

```css
/* la respuesta encoge para hacerle sitio al avatar */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])
  [data-testid="stChatMessageContent"] { flex: 1 1 0 !important; min-width: 0 !important; }
/* la pregunta mide lo que mide su texto */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
  [data-testid="stChatMessageContent"] { flex: 0 0 auto !important; }
```

**4. El ícono del asistente casi no se veía**: iba en el gris del borde. Va con la
tinta del texto sobre la superficie de la página.

### Nada de scroll horizontal

El texto se ajusta al ancho de la caja. Las palabras largas se parten donde toque
—un id de lote o una URL no tienen espacios donde cortar— y lo que de verdad no se
puede partir hace **su propio scroll adentro**:

```css
.st-key-transcripcion p, li, td, th { overflow-wrap: anywhere; word-break: break-word; }
.st-key-transcripcion pre, [data-testid="stTable"] { overflow-x: auto; max-width: 100%; }
.st-key-transcripcion code { white-space: pre-wrap; overflow-wrap: anywhere; }
```

### Tipografía

14 px de base (no los 15 de Streamlit), interlínea 1.65, y **títulos discretos**: una
respuesta del agente trae subtítulos, y a 24 px compiten con la interfaz. El código
en línea va en pastilla con borde, 0.8125rem.

## Las sugerencias

Cuatro preguntas de ejemplo, **dentro de la caja** y **se lanzan al hacer clic**: una
lista para copiar y pegar obliga a un paso que no aporta nada.

```python
clave_pendiente = k(clave, "pendiente")
pendiente = st.session_state.pop(clave_pendiente, None)   # POP, y ANTES de dibujar
...
if st.button(pregunta, key=..., type="tertiary"):
    st.session_state[clave_pendiente] = pregunta
    st.rerun()
...
if pregunta := (escrita or pendiente):
    ...
```

El `pop` antes de dibujar es lo que evita que **el mismo clic se procese dos veces**.

Van como **pastillas compactas en fila** (`st.container(horizontal=True)`), no en
rejilla: una rejilla de dos columnas reservaba media caja para cuatro botones y le
robaba el espacio a la conversación. Radio 999px, 0.78rem, borde de 1 px, y hover con
el primario translúcido.

Solo se muestran cuando **no hay conversación y no hay pregunta pendiente**.

## El streaming y el estado en vivo

Dos clases de evento (ver `06`): herramienta y texto.

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

Las herramientas van al `status` y el texto al cuerpo. **Ver qué herramienta se
ejecuta mientras corre es medio taller**: es lo que deja claro que el agente no está
improvisando.

Al final, el **bloque de trazabilidad**, que lo arma el código (ver `06`), y se
concatena al texto que se guarda en el historial.

## Un fallo del modelo no puede tumbar la interfaz

El texto se acumula **fuera** del `try`, y el error se guarda en su propia variable
—Python borra el nombre de `except ... as exc` al salir del bloque, así que
consultarlo después daría `NameError`:

```python
fallo, texto = None, ""
try:
    texto = st.write_stream(flujo())
except Exception as exc:
    fallo = exc
```

**Caso especial `already processing`:** el agente vive en `cache_resource` y sobrevive
a un F5. Si alguien recarga mientras el modelo escribe, la petición vieja sigue en
curso y la nueva choca. No es culpa de quien preguntó: se descarta el agente trabado
(`_agente.clear()`) y se reintenta **una vez**, en silencio.

El mensaje de error dice, siempre, que **los datos y los cálculos no dependen del
modelo: el tablero sigue funcionando**.

## La barra de acciones

Limpiar conversación y descargar la conversación en Markdown. Van **adentro de la
caja y arriba**: abajo y afuera obligaban a dejarle 125 px de pantalla libres, que es
justo lo que la conversación necesita. Discretos —sin borde, tinta suave— para que no
compitan con el contenido.

## Verificación de esta fase

Con la app corriendo, en claro y en oscuro:

1. La caja llega al pie de la pantalla (menos de ~20 px de margen).
2. El alto **no cambia** al empezar a responder.
3. Clic en una sugerencia → la pregunta se lanza y aparecen dos mensajes.
4. La pastilla de la pregunta va a la derecha y el texto queda **dentro** del fondo.
5. Una respuesta larga con código y tablas **no** produce scroll horizontal.
6. Al final de la respuesta está el bloque de trazabilidad.
