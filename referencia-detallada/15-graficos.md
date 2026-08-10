# 10 · Los gráficos

Altair. **Ni un `groupby` en este módulo**: cada función llama a `calculos.py` y
devuelve `(gráfico, cifras)`. Las mismas cifras alimentan el pie del gráfico y, en el
reporte, el contexto que recibe el modelo.

## Los seis del agente 1

| Título | Qué es |
|---|---|
| ¿De qué tipo es el desperdicio? | **Pareto** con curva acumulada |
| ¿Dónde y cuándo se concentra? | Mapa de calor línea × turno |
| ¿Cuánto nos alejamos del objetivo? | Histograma de delta de peso |
| ¿Se desgasta o está descalibrada? | Medias diarias + regresión, trazo por clasificación |
| ¿Qué lote se comporta distinto? | Ranking con los descartados en gris y su `n` |
| ¿Cuánto llevamos gastado? | Costo acumulado, dos franjas |

## Reglas de forma

### Nunca un eje doble

Dos escalas *y* distintas en un gráfico es el error número uno. Dos medidas de escala
distinta → dos gráficos, series pequeñas, o indexadas a una base común.

**Excepción única y legítima**: el Pareto, donde la curva acumulada va en porcentaje
contra el eje derecho. Ahí el segundo eje es parte de la forma canónica.

### El Pareto lleva curva acumulada… en un agente y no en el otro

No es una inconsistencia, y hay que escribirlo en el código:

- En **paradas** las causas son una partición real —cada parada pertenece a
  exactamente una categoría— así que el acumulado suma 100 % y el 80/20 se lee.
- En **desperdicio** las categorías se solapan, y una curva acumulada contra el total
  afirmaría algo falso. El acumulado se calcula **sobre las barras del gráfico**, y
  el pie lo dice: *«léela como "de lo que pudimos atribuir", no como una torta»*.

### Barras de un Pareto: un solo color

En un Pareto la categoría ya está escrita en el eje. Pintar cada barra distinto no
codifica nada: sugiere una distinción que no existe —todas miden lo mismo— y le quita
peso a lo único que el gráfico afirma, que es el orden.

El color se reserva para donde sí codifica identidad.

Excepción: en el Pareto de desperdicio, **una** barra va en otro color, la del
gramaje exceso, porque es la categoría que la planta no ve. Eso sí codifica algo.

### El texto lleva tokens de texto, nunca el color de la serie

Valores, etiquetas y leyendas van en la tinta primaria o suave. Un color al lado
carga la identidad.

En un mapa de calor, la tinta del número **cambia con el relleno**: sobre los pasos
oscuros de la rampa un texto oscuro no se lee. Se resuelve con
`alt.condition(datum.valor > max * 0.55, ...)`.

## Trampas de Altair encontradas

### Un histograma pre-binificado dibuja púas de 1 px

Si los datos ya vienen agrupados, `mark_bar()` no sabe el ancho de cada barra. Hay
que dar la extensión explícita:

```python
.encode(x="inicio:Q", x2="fin:Q")   # y mark_bar(strokeWidth=0)
```

### La leyenda de `strokeDash` muestra tres círculos idénticos

Por defecto dibuja el símbolo relleno, no el trazo. `symbolType="stroke"`.

### Las etiquetas de eje se recortan

`labelLimit` por defecto es corto. Súbelo (220) cuando las categorías tengan nombres
largos.

### Píldoras de delta verdes con flecha hacia arriba

`st.metric` pinta el delta en verde con flecha si es positivo, o sea **afirma una
mejora que nadie dijo**. Neutralízalo por CSS: fondo, color y flecha.

## El tema de Altair

Registrado con `@alt.theme.register(nombre, enable=)`, uno por modo. El modo activo
se guarda como estado de módulo en `estilo.py` para que las doce funciones de
gráficos no tengan que recibirlo por parámetro.

Eso asume **un proceso por persona** — que es exactamente la restricción del taller.
Escríbelo en el comentario: si esto sirviera a varios navegadores a la vez, el modo
tendría que viajar en el estado de sesión.

## Modo oscuro elegido, no volteado

Los pasos de los colores de serie se **re-eligieron** para la superficie #09090B y se
validaron contra ella. Un volteo automático del modo claro produce colores que
pasaban sobre blanco y fallan sobre negro.

## Verificación de esta fase

```bash
.venv/bin/python -c "
from src import carga, graficos, estilo, registro
d = carga.cargar()
a = registro.por_clave('desperdicio')
for g in a.graficos:
    ch, res = g.fn(d, 1.85)
    pie = g.pie(res)
    print(f'{g.titulo}: ok · pie {len(pie)} chars')
"
```

Los seis tienen que construirse sin excepción y devolver un pie no vacío. Después,
a ojo en la app: ninguna etiqueta recortada, ninguna barra de 1 px, ninguna leyenda
con símbolos repetidos.
