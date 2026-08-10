# 12 · Segundo agente — paradas no planeadas

## Por qué existe

Para probar que la abstracción del registro sirve. Este agente es **deliberadamente
distinto** del primero: minutos en vez de gramos, máquinas en vez de SKU, COP/hora en
vez de USD/kg, y una partición real de causas en vez de categorías que se solapan.

Si los dos fueran parecidos, la abstracción no probaría nada. `app.py` no se toca
para agregarlo.

Sus fuentes: `downtime_log` (cada parada con máquina, línea, turno, duración, código
de falla y comentario del operario) y `mantenimiento_historico`.

## El hallazgo que define este agente

**La fecha del turno no es la fecha del calendario.**

El turno de noche va de 22:00 a 05:59 y pertenece al día en que empezó. Una parada a
las 02:00 del sábado es del turno de noche del **viernes**.

```python
madrugada_de_turno_noche = (p["turno"] == "noche") & (hora < 6)
p["fecha_turno"] = p["fecha"] - pd.to_timedelta(
    madrugada_de_turno_noche.astype(int), unit="D")
```

Sin esta derivación, el patrón fuerte del dataset —una concentración de paradas los
viernes de noche— **aparece partido entre dos columnas contiguas y se lee como
ruido**: 105 en una y 28 en otra. Con la fecha del turno son 129 paradas, 4,7× la
tasa esperada, p = 5e-60.

Es la lección del agente: una derivación de tres líneas es la diferencia entre
encontrar el patrón y no verlo. El mapa día × turno tiene que ir sobre `fecha_turno`.

## Clasificar causas cuando falta el código de falla

Muchas filas traen el código vacío y solo el comentario del operario. La
clasificación sale de un vocabulario de pistas.

**El vocabulario se construye desde el propio dataset, no desde la intuición.** Se
cruzan las palabras del comentario con el `codigo_falla` de las filas que sí lo
tienen, y se ve qué categoría le corresponde de verdad a cada palabra.

> Ejemplo real: «tolva» parecía materia prima. En el dataset, 16 de 16 filas con esa
> palabra y código presente eran **operativas**. Corregirlo bajó las filas sin
> clasificar de 224 a 27.

Marca cada fila con `categoria_origen` (código o comentario) y `comentario_ambiguo`,
y reporta en el pie del gráfico **qué porcentaje se infirió del comentario**. Es una
medida de calidad del dato que quien lee tiene derecho a ver.

## Las nueve herramientas

`resumen_de_paras`, `rankear_causas`, `detectar_patron_recurrente`,
`comparar_lineas`, `analizar_microparos`, `cuantificar_ahorro`,
`generar_reporte_handoff`, `consultar_maquina`, `buscar_comentarios_similares`.

Cuatro decisiones de método que hay que respetar:

### `detectar_patron_recurrente` compara contra la actividad de la planta

No contra un promedio plano. Se usa `scipy.stats.binomtest` contra la actividad real
de esa celda día × turno: si la planta corre menos los domingos, tener menos paradas
el domingo no es un hallazgo.

### `comparar_lineas` compara perfil, no volumen

Una línea que corre el doble tiene el doble de paradas y eso no dice nada. Devuelve
horas **por día** y número de máquinas, y el pie lo advierte.

### `analizar_microparos` devuelve un dato honesto e incómodo

Microparada = menos de 5 minutos. La clave
`si_fuera_una_causa_ocuparia_el_puesto` responde *«si juntáramos todas las
microparadas en una sola causa, ¿en qué puesto del Pareto quedaría?»* — que es la
pregunta que importa y evita exagerarlas.

### `cuantificar_ahorro` solo cuenta patrones confirmados

Y penaliza la probabilidad de éxito si ya se intentaron preventivos sobre esa
máquina: si el preventivo ya se hizo y el problema sigue, la probabilidad de que
funcione esta vez es menor.

## Los seis gráficos

Pareto (con curva acumulada, porque acá **sí** es una partición real), torta de
causas, horas por línea, evolución semanal, mapa día × turno sobre `fecha_turno`, y
top de máquinas.

### Color

Este tablero usa la escala **monocromática cálida** (`escala_calida`), no la
categórica de seis tonos: seis colores saturados en un tablero de marca naranja se
leen chillones.

Como esa escala **no identifica por leyenda** con más de tres categorías (ver
`13-estilos-y-paleta.md`), los dos gráficos que la usan con seis llevan
**etiquetas directas**:

- **Torta**: nombre y porcentaje sobre cada gajo con peso suficiente. El color
  armoniza; el nombre identifica. Es lo que hace legítima una torta monocromática.
- **Área apilada**: es el mejor caso de la rampa —bandas contiguas que se comparan
  contra su vecina— y conserva la leyenda.
- **Top de máquinas**: colorea por línea, y son tres, así que los pasos se reparten a
  lo ancho de la rampa y ahí el color sí identifica solo.

«Indeterminada» va en gris: significa «no sabemos qué pasó», no es una causa más.

## Verifica y reporta lo que NO se sostiene

El verificador de este agente encontró dos promesas del plan original que los datos
no sostienen. **Repórtalas como aviso en vez de forzar el dato para que cuadre:**

1. Las **microparadas no son la 2.ª causa** de pérdida de OEE: son la 7.ª, con el
   2,5 % de las horas. Para llegar al 2.º puesto harían falta ~2 236 microparadas más.
2. El patrón de **humedad en la línea 1 no es verificable**: el dataset no tiene
   columna de humedad. Hace falta la fuente o hay que quitar la afirmación.

Que un verificador diga «esto no está» es el verificador funcionando. Cambiar el
generador para que la promesa se cumpla sería fabricar la evidencia.

## Verificación de esta fase

```bash
.venv/bin/python -m src.paras.verificar_datos
```

Debe terminar en `✓ Los patrones verificables están en los datos · 2 aviso(s)`.

Y la comprobación del hallazgo, que vale la pena dejar escrita:

```bash
.venv/bin/python -c "
from src.paras import carga, calculos
d = carga.cargar()
r = calculos.distribucion_turno(d, 2_000_000)
print(r['_mapa'].sort_values('horas', ascending=False).head(3))
"
```

La celda más alta tiene que ser **una sola** combinación día × turno. Si el pico
aparece repartido entre dos días contiguos, `fecha_turno` no se está aplicando.
