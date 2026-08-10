# 11 · El reporte descargable

Una cuarta pestaña, **Generar reporte**, que produce un HTML autocontenido con las
gráficas incrustadas, las cifras del tablero y las conclusiones del asistente.

## Es deductivo, no decorativo

**No recalcula nada.** Corre las mismas funciones de `graficos.py` que dibuja el
tablero, con los mismos filtros y los mismos supuestos, y de ahí sale todo — las
gráficas, los pies y los números que el modelo recibe para concluir.

El mismo `res` alimenta el pie y el contexto del modelo, así que **el texto del
reporte no puede contradecir a su propia gráfica**. Si el reporte dijera una cifra
distinta al tablero, el reporte sería el problema.

## Cuatro decisiones

### 1. Las gráficas van como SVG dentro del archivo

Un reporte que se manda por correo tiene que abrirse en la máquina de quien lo
recibe, **sin red y sin la aplicación corriendo**. `vl-convert` traduce el Vega-Lite
de Altair a SVG sin abrir un navegador:

```python
spec = chart.properties(width=ANCHO_GRAFICO, height=ALTO_GRAFICO).to_json()
svg = vlc.vegalite_to_svg(spec)
```

Verifica que **no quede ni una referencia a un CDN externo** en el archivo generado.

Si una gráfica no se puede renderizar, el reporte **no se cae**: queda una nota en su
lugar. Un reporte con cinco gráficas y un aviso es útil; una excepción a mitad de la
generación no le sirve a nadie.

### 2. Una hoja por gráfica

```css
@page { size: A4; margin: 14mm; }
@media print {
  figure { break-before: page; break-inside: avoid; }
  footer { break-before: page; }
}
```

`break-before` en cada figura y no `break-after` en la anterior: así la primera
gráfica también arranca en hoja nueva, después de la portada y las conclusiones.

Las gráficas se dimensionan para que **quepan** en una hoja con su título y su pie.
En A4 con márgenes de 14 mm el área útil son unos 182 × 255 mm; a 96 ppp eso da
~690 × 965 px, y de ese alto hay que descontar título, pie y aire. De ahí
`ANCHO_GRAFICO = 680` y `ALTO_GRAFICO = 400`: no son un gusto, son la hoja.

### 3. Siempre en tema claro

Aunque la aplicación esté en oscuro. Se va a imprimir o a leer en un cliente de
correo, y una gráfica de fondo negro sobre papel blanco no se lee. Cambia el tema
mientras renderiza y **devuélvelo a como estaba** en un `finally`.

### 4. `mailto:` NO puede llevar adjuntos

Ningún navegador lo permite: es una restricción de seguridad del protocolo, no algo
que falte implementar.

El botón de correo abre el cliente con el destinatario, el asunto y el resumen
ejecutivo en el cuerpo, y **la interfaz dice explícitamente que el archivo hay que
adjuntarlo a mano** después de descargarlo. Ofrecer un botón que promete adjuntar y
no adjunta es peor que decir la verdad.

El cuerpo se recorta a ~1 200 caracteres: al codificarse para la URL cada acento y
cada salto pasan a tres caracteres, y varios clientes —Outlook entre ellos— truncan
el `mailto:` cerca de los 2 000. **Un cuerpo cortado a mitad de frase es peor que uno
resumido a propósito**, así que cuando se recorta, se dice.

## Estructura del documento

1. **Portada** — asistente, planta, rango, fecha de generación
2. **KPIs** del tablero
3. **El recorte que estás leyendo** — tabla con los filtros y los supuestos activos.
   Un reporte que no dice de qué pedazo de planta habla se interpreta como si
   hablara de toda.
4. **Conclusiones del asistente**
5. **Una hoja por gráfica**, con su pie derivado
6. **Trazabilidad**

## La trazabilidad del reporte hay que anotarla a mano

El reporte calcula por `calculos.py` —igual que el tablero— y **no** por las
herramientas del agente, que son las que van llenando el registro. Sin esto el
reporte sale con el bloque de trazabilidad vacío: cifras sin decir sobre cuántas
filas se pararon, justo lo que ese bloque viene a evitar.

```python
reg.anotar("gráficas del tablero", vista.traza(*[f.clave for f in a.fuentes]))
```

Los índices salen de la **vista filtrada**, no de los datos completos.

> **El orden importa y es contraintuitivo.** `configurar()` **limpia** el
> registro, así que va **antes** de anotar. Escrito al derecho —anotar primero,
> configurar después, que es como sale natural porque configurar «prepara» las
> herramientas— el bloque de trazabilidad del reporte sale vacío. No falla nada:
> simplemente el reporte queda con cifras y sin decir sobre cuántas filas se
> pararon, justo lo que ese bloque viene a evitar.

## El encargo al modelo

Recibe las cifras en JSON, tal como salieron del cálculo, y se le pide:

1. **Lo que está pasando** — dos o tres frases de lectura de conjunto
2. **Los tres hallazgos que aguantan una pregunta incómoda** — cada uno con su cifra
   y de qué gráfica sale; si depende de una muestra chica, se dice en el mismo renglón
3. **Qué hacer, en orden de plata** — separando ajuste de mantenimiento
4. **Qué NO se puede concluir con estos datos** — **esta sección no es opcional**

### Si hay que recortar el JSON, se dice

Un JSON cortado a la mitad sin avisar hace que el modelo concluya sobre datos
incompletos creyéndolos completos. Avisado, lo reporta como límite o pide la
herramienta.

> Esto salió de leer un reporte real: el propio agente detectó el corte y lo anotó
> en su sección de límites. La corrección fue subir el tope a 18 000 caracteres por
> gráfica **y** anunciar el recorte cuando ocurra.

## Un fallo del modelo no puede tumbar el reporte

El texto se acumula **fuera** del `try`. Si el modelo se cae a mitad de camino, lo
que alcanzó a escribir se conserva y el reporte se genera igual, porque las gráficas
y las cifras no dependen de él — ya están calculadas.

Con `MaxTokensReachedException` el mensaje debe explicar que el modelo llegó a su
tope de escritura y que **el resto del reporte no depende de él**.

## Verificación de esta fase

Genera un reporte de cada agente y comprueba sobre el archivo descargado:

```python
assert '<svg' in html and html.count('<svg') == 6      # las seis gráficas
assert 'Trazabilidad' in html                          # no vacía
assert '**' not in html                                # sin markdown crudo
assert not re.search(r'https?://(?!www\.w3\.org)', html)   # sin CDN externo
```

Y renderízalo a PDF para contar las páginas: deben ser **una por gráfica** más
portada y trazabilidad.
