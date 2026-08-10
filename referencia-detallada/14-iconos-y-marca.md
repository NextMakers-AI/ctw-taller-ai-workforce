# 14 · Iconos, logo y favicon

## Iconos: Material Symbols, nunca símbolos unicode

```python
st.tabs([":material/forum: Preguntar",
         ":material/monitoring: Tablero",
         ":material/description: Generar reporte",
         ":material/database: Datos"])
```

**Por qué no un emoji ni un carácter unicode:** se dibujan con la fuente del sistema,
así que se ven distintos en macOS, Windows y Linux, cambian de ancho, rompen la
alineación vertical de una fila de pestañas y algunos ni siquiera existen en todas
las plataformas. Un Material Symbol se renderiza igual en todas partes y hereda el
color del texto.

### Dónde funcionan y dónde no

**Solo se resuelven en las etiquetas de widget** de Streamlit: pestañas, botones,
`st.metric`, `st.status`, `st.info(icon=...)`, `st.download_button`, `st.link_button`.

**No se resuelven dentro de HTML crudo.** Un `:material/mail:` dentro de un `<a>` que
escribiste con `unsafe_allow_html=True` sale como **texto literal**. Si necesitas un
enlace con icono, usa `st.link_button(..., icon=":material/mail:")` en vez de un
ancla a mano.

### Los que usa la aplicación

| Dónde | Icono |
|---|---|
| Pestañas | `forum` · `monitoring` · `description` · `database` |
| Agente 1 | `scale` (una balanza: se pesa material) |
| Agente 2 | `pause_circle` (una parada) |
| Herramienta ejecutándose | `build` |
| Sub-pestañas de Datos | `upload_file` · `edit_note` |
| Acciones del chat | `delete_sweep` · `download` |
| Generar reporte | `auto_awesome` |
| Avisos | `info` · `warning` |

El icono de cada agente vive en su `AgenteDef`, no en `app.py`.

## El logo

```python
st.logo("assets/next-makers-log.png", size="medium",
        link="https://…")
```

`st.logo` lo coloca **arriba de la barra lateral por sí solo**: no hace falta
pintarlo a mano ni reservarle espacio con una columna.

## La marca da el color primario

El naranja de la aplicación **no se eligió: se midió sobre el archivo del logo**.

```python
from PIL import Image
from collections import Counter
im = Image.open("assets/next-makers-log.png").convert("RGBA")
c = Counter((r, g, b) for r, g, b, a in im.getdata() if a > 200)
# → #EB652B con el 66 % de los píxeles opacos
```

Ese hex entra al sistema de diseño y de ahí sale todo lo demás (ver `13`). Extraer el
color en vez de escogerlo «parecido» es lo que hace que la interfaz y el logo se vean
del mismo proyecto.

## El favicon: la marca sola, no el logotipo

Un favicon mide 32 px. **El logotipo «NextMakers» no es legible a ese tamaño**, así
que hay que recortar solo el símbolo.

```python
# 1. Encuentra el primer hueco vertical ancho: separa la marca del texto.
px = im.load(); w, h = im.size
cols = [x for x in range(w) if any(px[x, y][3] > 200 for y in range(h))]
corte = next((cols[i] + 1 for i in range(len(cols) - 1)
              if cols[i + 1] - cols[i] > 30), w)
marca = im.crop((cols[0], 0, corte, h))
# 2. Céntrala en un lienzo cuadrado (un favicon no rectangular se deforma).
```

### El detalle que casi nadie ve venir

La mitad clara del símbolo es **#F3F7FA**, casi blanco. Existe para leerse sobre
fondo oscuro en el logo original, pero **en una pestaña del navegador el fondo es
desconocido**: sobre una pestaña blanca esa mitad desaparece y el favicon se ve como
media letra rota.

Solución: en el favicon —y **solo** en el favicon, no en el logo— esa mitad se pasa a
un gris neutro que aguanta los dos casos: 2,6:1 sobre blanco y 5,1:1 sobre negro.

```python
GRIS = (154, 163, 172)
for y in range(im.height):
    for x in range(im.width):
        r, g, b, a = d[x, y]
        if a > 40 and r > 200 and g > 200 and b > 200:
            d[x, y] = (*GRIS, a)
```

Se declara con:

```python
st.set_page_config(page_title="…", page_icon="assets/favicon.png", layout="wide")
```

## Verificación de esta fase

1. Abre la app en macOS y en Windows si puedes: los iconos de las pestañas se ven
   **idénticos** y alineados.
2. Mira la pestaña del navegador en tema claro **y** oscuro: el favicon se ve entero
   en los dos.
3. Busca símbolos unicode que se hayan colado:

```bash
grep -rnP "[\x{2190}-\x{2BFF}\x{1F300}-\x{1FAFF}]" app.py src/*.py | grep -v "^.*#" | head
```

Los que aparezcan dentro de comentarios o de texto en prosa (como «→» en una
descripción) están bien; los que estén en una **etiqueta de widget** hay que
cambiarlos por un Material Symbol.
