# 09 · Sistema visual y paleta validada

## Qué es y qué no es

shadcn/ui **no se puede instalar en Streamlit**: es un catálogo de componentes React
sobre Tailwind, y Tailwind resuelve sus clases en tiempo de build — no aplicarían al
DOM que genera Streamlit.

Lo que sí es portable, y de donde viene el aspecto, son sus **tokens**: la escala
neutra `zinc`, un borde de 1 px en vez de sombra, radios de 0.5rem, tipografía
Inter.

Esos tokens van en `.streamlit/config.toml`, que es tema **nativo**. Cópialo de
`replica/referencia/config.toml`. El CSS a mano se reserva para lo poco que el tema
nativo no alcanza: no apuntes a clases internas de Streamlit si el tema nativo puede
hacerlo, porque esas clases cambian de versión y se rompen sin avisar.

## Los patrones de componente que hay que reproducir

Los tokens dan el color; esto da el aspecto. Cada fila es un componente de shadcn y
cómo se consigue en Streamlit.

| Componente shadcn | Cómo se ve acá |
|---|---|
| **Card** | Borde de 1 px del token `borde`, radio 0.5rem, **sin sombra**. Las tarjetas de KPI y la caja del chat |
| **SidebarGroupLabel** | Etiquetas de grupo en versalitas: 0.6875rem, peso 600, `letter-spacing: 0.06em`, mayúsculas, en tinta suave |
| **SidebarMenu** | El selector de asistente es una **lista de navegación, no un radio**: ítem activo en pastilla translúcida del primario con texto del primario, el resto transparente |
| **Muted surface** | La barra lateral va un tono por debajo del lienzo: separa sin necesitar una línea gruesa |
| **Tabs** | Subrayado del primario en la activa, no pastilla rellena |
| **Badge / chip** | Las sugerencias del chat: pastillas de borde 1 px, radio 999px, 0.78rem, tinta suave |
| **Button** | Primario = fondo naranja con **letra oscura** (ver contraste abajo). Terciario = sin borde, solo tinta |
| **Input** | Borde 1 px, radio 0.5rem, y **placeholder en todos los campos** |
| **Separator** | 1 px del token `borde`. Debe verse **también con la barra lateral cerrada** |
| **Avatar** | El del asistente en el chat: círculo de 1.75rem con borde 1 px y el ícono en tinta de texto, no en el gris del borde |

### El chat, que es donde más se nota

`st.chat_message` dibuja avatar y texto plano, sin burbujas: no lee como una
conversación. El patrón correcto es **asimétrico**:

- **La pregunta** en pastilla a la derecha, fondo del primario, radio
  `1rem 1rem 0.25rem 1rem`, ancho máximo 70 %, y el avatar del usuario oculto.
- **La respuesta** como texto corrido con su avatar a la izquierda. Meterla en
  burbuja sería un error: son reportes largos, con tablas y bloques de código.

Tipografía de la conversación: 14 px de base (no los 15 de Streamlit), interlínea
1.65, y **títulos discretos** — una respuesta del agente trae subtítulos, y a 24 px
compiten con la interfaz.

### Iconos: Material, nunca símbolos unicode

En las etiquetas de widget, `:material/forum:`, `:material/monitoring:`. Un emoji o
un carácter unicode se ve distinto en cada sistema operativo y rompe la alineación.

**Cuidado:** los iconos Material **solo se resuelven en etiquetas de widget**, no
dentro de HTML crudo. Un `:material/mail:` dentro de un `<a>` sale como texto
literal; para un enlace con icono, usa `st.link_button`.

### Detalles que se ven mal si no se cuidan

- El divisor de la barra lateral tiene que verse **con la barra cerrada**.
- Los tooltips (`help=`) de Streamlit son cajas grandes que **tapan el elemento
  activo** y desplazan el layout. En la navegación, muestra la descripción como
  texto debajo de la lista en vez de en un tooltip.
- El hover de un ítem de navegación **no puede quedar blanco sobre blanco**: fija
  fondo y color explícitos en cada estado.
- Espacio entre ítems de navegación con `margin-bottom` en el botón, no con `gap`
  del bloque: con `gap` los ítems se montan sobre la etiqueta del grupo.

## Los tokens

```python
CLARO = {
  "fondo": "#FFFFFF", "superficie": "#FFFFFF",
  "muted": "#F4F4F5", "borde": "#E4E4E7",
  "texto": "#09090B", "texto_suave": "#71717A",
  "grilla": "#F1F1F2", "neutral_serie": "#71717A",
  "primario": "#EB652B", "sobre_primario": "#1C0A02",
}
OSCURO = {
  "fondo": "#09090B", "superficie": "#09090B",
  "muted": "#18181B", "borde": "#27272A",
  "texto": "#FAFAFA", "texto_suave": "#A1A1AA",
  "grilla": "#1C1C1F", "neutral_serie": "#A1A1AA",
  "primario": "#EB652B", "sobre_primario": "#1C0A02",
}
```

## La marca manda sobre el color; la accesibilidad manda sobre la marca

El naranja **#EB652B** es el del logo, medido sobre la imagen: son el 66 % de sus
píxeles opacos. Sirve igual en los dos modos porque su luminosidad OKLCH (L = 0,666)
cae dentro de las dos bandas permitidas — la clara 0,43–0,77 y la oscura 0,48–0,67.

**La tinta encima no es blanca.** Blanco sobre ese naranja da 3,27:1, insuficiente
para texto normal. Un casi negro cálido (#1C0A02) da 5,88:1. Por eso los botones
primarios de esta aplicación llevan letra oscura: no es una preferencia estética.

Los enlaces tampoco usan el naranja del logo tal cual —necesitan 4,5:1—: van
`#C13D00` en claro (5,34:1) y `#FA7A48` en oscuro (7,52:1).

## La paleta categórica: seis colores, no ocho

```python
SERIES_CLARO  = ("#EB652B", "#A43650", "#069FF9", "#E35EBD", "#40C68B", "#7756DC")
SERIES_OSCURO = ("#EB652B", "#AB2440", "#1E8FEE", "#D551B1", "#00A66D", "#7546CA")
```

**Que sean seis es un hallazgo de la verificación, no un recorte por gusto.** Con
ocho tonos falla de raíz en modo oscuro: la banda de luminosidad ahí es angosta
(L 0,48–0,67) y ocho tonos dentro de esa franja se pisan — el ámbar y el naranja
quedaban a ΔE 0,5 bajo deuteranopía, o sea el mismo color. Seis caben con margen, y
seis alcanzan: lo máximo que colorea el tablero son las seis categorías de paradas.

Verificada en modo **todos los pares**, no solo pares adyacentes, así que cualquier
subconjunto en cualquier orden es seguro:

| | peor par CVD | visión normal |
|---|---|---|
| claro | ΔE 10,6 | ΔE 18,5 |
| oscuro | ΔE 9,3 | ΔE 18,5 |

El **orden es el mismo en los dos modos** a propósito: la serie *i* tiene que ser la
misma entidad en claro y en oscuro, o el color deja de identificar nada.

### La paleta de shadcn fue rechazada, y por qué

Sus `--chart-1..5` no pasan: ΔE 4,7 en deuteranopía entre sus slots 4 y 5 (objetivo
≥8), tres cálidos análogos juntos, y uno de sus colores lee gris. Se verificó con el
validador antes de descartarla — no de vista.

## La rampa secuencial

```python
SECUENCIAL_CLARO  = ("#E6A188", "#DB8261", "#CF6136", "#C13D00", "#9F2E00", "#7C2400")
SECUENCIAL_OSCURO = ("#79371D", "#9D431E", "#C24E1C", "#E45E24", "#FA7A48", "#FF9B73")
```

Un solo tono, el de la marca. **El extremo más claro no es casi blanco**, y no por
gusto: el paso vecino a la superficie tiene que despegar 2:1 de ella. Un `#FDE8DC`
rinde 1,18:1 sobre blanco — la celda de valor más bajo se confunde con el fondo y
«poco» se vuelve indistinguible de «nada». Estos arrancan en 2,14:1 y 2,25:1.

En oscuro va al revés, para que «más» siga siendo «más lejos del fondo».

> **Que corran al revés tiene una consecuencia que solo se ve mirando.** En un
> mapa de calor con el número escrito sobre la celda, la tinta del valor más alto
> **no puede ser un color fijo**:
>
> - en claro la rampa va de claro a oscuro → el valor más alto cae sobre un
>   relleno oscuro y su número va en **blanco**;
> - en oscuro va de oscuro a claro → el valor más alto cae sobre el relleno **más
>   claro**, donde un blanco da ~2:1 e ilegible; ahí va la tinta oscura.
>
> Un `alt.value("#FFFFFF")` fijo funciona en claro y falla en oscuro. Sácalo a una
> función que reciba el modo. Es el tipo de error que no rompe nada, no pone
> ninguna prueba en rojo, y solo se nota si uno **no** sabe ya qué número dice ahí.

### `chartSequentialColors` exige EXACTAMENTE diez valores

Con siete, Streamlit **descarta la lista entera y cae a sus colores por defecto**,
sin más aviso que una línea en el log. La rampa de marca no se aplicaba y nadie se
había dado cuenta. Los diez están en `replica/referencia/config.toml`.

Esos diez son puntos de interpolación de un degradado continuo, no diez bins
discretos: ahí **no** se exige la separación mínima de luminosidad entre pasos
vecinos que sí se le exige a una escala ordinal — en un degradado, que dos puntos
contiguos se parezcan es el objetivo. Lo que sí se verificó es lo que aplica a un
continuo: luminosidad monótona, un solo tono y el extremo despegado de la superficie.

## Las dos escalas y cuándo usar cada una

### `escala(dominio, neutral=None)` — por entidad

El dominio se pasa **explícito y completo** para que un filtro que cambie la cantidad
de series no repinte a las que quedan: «Mecánica» tiene que seguir siendo del mismo
color cuando desaparece «Sensor». **El color sigue a la entidad, nunca a su posición
en el ranking.**

`neutral` va en gris: una categoría que significa «no sabemos» no es un par de las
demás.

### `escala_calida(dominio, neutral=None)` — monocromática

Un solo tono, para armonizar con la marca. **Su límite está medido, no supuesto:**

- Como escala **ordinal** pasa todo — luminosidad monótona, salto mínimo entre
  pasos, extremo claro despegado.
- Como escala de **identidad** no llega: con seis pasos de un tono el peor par queda
  en ΔE 7,8 contra un piso de 15.

O sea: sirve para «¿cuál banda es más gruesa que su vecina?», no para «busca este
color en la leyenda». De ahí dos reglas de uso:

- Con **hasta tres** categorías, los pasos se reparten a lo ancho (índices 0, 2 y 5)
  y el peor par sube a ΔE 16,2 en ambos modos: ahí sí identifica por color.
- Con **cuatro o más**, quien la use **tiene que poner etiquetas directas** sobre las
  marcas. Si el color no alcanza para identificar, el texto lo hace.

> Se intentó una paleta categórica de puros naranjas y **no se puede validar**: con
> 5 tonos cálidos el peor par da ΔE 14,8 y con 6 da 13,6, contra un piso de 15 para
> visión normal. No es un tecnicismo de daltonismo: ni alguien con visión de color
> completa distingue esos pares. Documenta el intento; ahorra que el siguiente lo
> repita.

## `serie(i)` no cicla

Pasado el último color **lanza `IndexError`** con un mensaje que dice qué hacer. Si
un día hacen falta más series, la respuesta no es generar un color nuevo: es agrupar
el resto en «Otras» o separar en varios gráficos.

## El validador

La regla de oro: **el color es computable, así que se computa.** Nunca decidas de
vista si una paleta es segura para daltonismo. Si tienes el validador de paletas
disponible, córrelo; si no, verifica a mano estas cinco cosas por paleta y por modo:

1. Luminosidad OKLCH dentro de la banda del modo
2. Croma mínimo (ningún color que lea gris)
3. Separación CVD ≥ 8 (protanopía, deuteranopía, tritanopía)
4. Separación para visión normal ≥ 15 — **este es un fallo duro, no una advertencia**
5. Contraste ≥ 3:1 contra la superficie

Los números de esta paleta están en `replica/referencia/paleta-validada.md`.

## Verificación de esta fase

```bash
.venv/bin/python -c "
from src import estilo
import re
for m in (False, True):
    c = estilo.css(m)
    assert not re.findall(r'\{[a-z_\[\]\047\"]+\}', c), 'quedó un marcador sin resolver'
print('css resuelto en los dos modos')
print('claro ', estilo.SERIES_CLARO)
print('oscuro', estilo.SERIES_OSCURO)
"
```

Y a ojo, en los dos modos: ningún texto blanco sobre fondo blanco, ni en reposo ni
en hover, ni en botones ni en desplegables.
