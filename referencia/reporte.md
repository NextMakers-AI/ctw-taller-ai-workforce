# Referencia · El reporte descargable

> **Esto no se lee en voz alta.** Es la maquetación del reporte de la fase 3: cómo
> se incrustan las gráficas, cómo se arma el PDF y qué se le encarga al modelo.
> Cada nota existe porque algo salió torcido y costó verlo.

---

### Cuatro decisiones

**1. Las gráficas se incrustan sin abrir un navegador.** Un reporte que se manda
por correo tiene que abrirse **sin red y sin la aplicación corriendo**.
`vl-convert` traduce el Vega-Lite de Altair a SVG y a PNG —es una biblioteca en
Rust—, y eso es lo que permite generarlo dentro del proceso de Streamlit. El SVG
va en el HTML; el PNG va en el PDF, que maqueta `fpdf2` (Python puro, sin
librerías nativas que compilar: `weasyprint` habría exigido pango y cairo en cada
máquina del taller).

> **En el PDF las gráficas van como imagen, no como vector.** `fpdf2` sabe
> dibujar los trazos de un SVG pero **no escribir su texto**, y un gráfico sin
> etiquetas de eje no sirve. A escala 2 la impresión se ve bien.

> **Dos trampas de `fpdf2` que se ven feo y no fallan:** `multi_cell` deja el
> cursor **a la derecha** de lo que escribió, así que la siguiente celda arranca
> ahí y el texto se sale de la hoja —hay que devolverlo al margen con
> `new_x=XPos.LMARGIN`—; y `image()` **ya baja el cursor por su cuenta**, así que
> si además le sumas el alto de la imagen, el pie de la gráfica termina a dos
> alturas de distancia, al fondo de la hoja.

Si una gráfica no se puede renderizar, el reporte **no se cae**: queda una nota en
su lugar. Un reporte con cinco gráficas y un aviso es útil; una excepción a mitad
de la generación no le sirve a nadie.

**2. Una hoja por gráfica.** `break-before: page` en cada figura y no
`break-after` en la anterior: así la primera gráfica también arranca en hoja nueva.
En A4 con márgenes de 14 mm el área útil son unos 182 × 255 mm; a 96 ppp eso da
~690 × 965 px, y de ese alto hay que descontar título, pie y aire. De ahí
`ANCHO_GRAFICO = 680` y `ALTO_GRAFICO = 400`: no son un gusto, son la hoja.

**3. Siempre en tema claro**, y la aplicación está en oscuro. Se va a imprimir
o a leer en un cliente de correo, y una gráfica de fondo negro sobre papel blanco no
se lee. Cambia el tema mientras renderiza y **devuélvelo a como estaba** en un
`finally`.

**4. `mailto:` NO puede llevar adjuntos.** Ningún navegador lo permite: es una
restricción del protocolo, no algo que falte implementar. El botón abre el cliente
con el resumen en el cuerpo, y **la interfaz dice explícitamente que el archivo hay
que adjuntarlo a mano**. Ofrecer un botón que promete adjuntar y no adjunta es peor
que decir la verdad. El cuerpo se recorta a ~1.200 caracteres —al codificarse cada
acento pasa a tres— y **cuando se recorta, se dice**.

### Estructura del documento

Portada · KPIs · **el recorte que estás leyendo** (los filtros y supuestos activos:
un reporte que no dice de qué pedazo de planta habla se interpreta como si hablara
de toda) · conclusiones del asistente · una hoja por gráfica · trazabilidad.

### La trazabilidad del reporte hay que anotarla a mano

El reporte calcula por `calculos.py` —igual que el tablero— y **no** por las
herramientas, que son las que van llenando el registro. Sin esto sale con el bloque
vacío.

```python
reg.anotar("gráficas del tablero", vista.traza(*[f.clave for f in a.fuentes]))
```

Los índices salen de la **vista filtrada**, no de los datos completos.

> **El orden importa y es contraintuitivo.** `configurar()` **limpia** el registro,
> así que va **antes** de anotar. Escrito al derecho —anotar primero, configurar
> después, que es como sale natural porque configurar «prepara» las herramientas—
> el bloque sale vacío. No falla nada: simplemente el reporte queda con cifras y
> sin decir cuántas filas de datos las sustentan.

### El encargo al modelo

Recibe las cifras en JSON tal como salieron del cálculo, y se le piden cuatro
secciones: lo que está pasando · los tres hallazgos que aguantan una pregunta
incómoda, cada uno con su cifra y de qué gráfica sale · qué hacer, en orden de
plata · **qué NO se puede concluir con estos datos** — esta última **no es
opcional**.

**Si hay que recortar el JSON, se dice.** Un JSON cortado a la mitad sin avisar
hace que el modelo concluya sobre datos incompletos creyéndolos completos.

Y un fallo del modelo no puede dejar inservible el reporte: el texto se acumula **fuera** del
`try`, porque las gráficas y las cifras no dependen de él — ya están calculadas.

---
