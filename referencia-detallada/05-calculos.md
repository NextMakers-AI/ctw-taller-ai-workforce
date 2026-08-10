# 05 · Los cálculos: la única fuente de cifras

`src/calculos.py` es el módulo del que sale **toda** cifra que la aplicación
muestre o diga. Los gráficos lo llaman, las herramientas lo llaman. Nadie más suma.

Cada función devuelve un **diccionario**, no un DataFrame. Las claves que empiezan
por `_` son para el código (series diarias, índices de trazabilidad) y se filtran
antes de mandarle nada al modelo.

## Las funciones

### `calcular_desperdicio(datos, precio_usd_kg)`

Las dos mitades de la lección 1, separadas y sumadas.

- Solo muestras con `veredicto == "conforme"` para el gramaje exceso
- `delta.clip(lower=0)`: una pieza liviana no compensa a una pesada
- Desglose por línea y SKU, no un promedio global

### `analizar_deriva(datos)`

`statsmodels.WLS` sobre las **medias diarias**, ponderadas por el `n` de cada día:
un día con 4 muestras no puede pesar lo mismo que uno con 300.

Clasifica por pendiente en `deriva` o `setpoint_desviado`, y **el setpoint se juzga
por el intercepto, nunca por la media** (ver lección 2).

Costo mensual proyectado de la deriva:

```python
costo = (pendiente * 30) * (unidades_por_dia * 30) / 1000 * precio
```

> **Error real que se cometió acá y hay que evitar:** la primera versión multiplicaba
> los gramos de un mes por las unidades de **un solo día**, y el costo salía en 2
> USD/mes — una cifra tan chica que nadie actuaría. Correcto son 54 USD/mes. Los dos
> factores tienen que estar en la misma unidad de tiempo.

### `rankear_lotes_resina(datos, min_turnos)`

Lección 3. Devuelve los lotes con evidencia y, por separado, la lista
`descartados_por_muestra_insuficiente` **con su `n`**, para que el gráfico los pinte
en gris y el modelo los mencione como pendientes y no como culpables.

Usa `scipy.stats.ttest_ind` para decir si la diferencia es significativa.

### `atribuir_categorias(datos, precio)`

Lección 5. Línea base = turnos **sin transiciones**; cada categoría es el exceso
sobre esa base.

> **Otro error real:** la primera versión definía la base como «turnos completamente
> limpios» y quedaban 5 turnos — una base de 5 no aguanta nada. Relajado a «sin
> transiciones» quedan 115, que ya es una base.

Devuelve `advertencia` cuando la suma pasa del 100 %, con el número exacto de turnos
que caen en más de una categoría.

> **La trampa está en el DENOMINADOR, y es silenciosa.** El porcentaje de cada
> categoría se mide contra el exceso de **toda la planta** sobre la línea base.
> Dividir entre la suma de las categorías —que es lo que sale natural— da 100 %
> exacto **por construcción**: la advertencia no se dispara nunca, los
> porcentajes parecen una partición prolija, y la lección 5 desaparece sin que
> nada falle ni ninguna prueba se ponga roja.
>
> Devuelve las dos cifras con nombres distintos —`pct_del_exceso_de_planta` y
> `pct_de_lo_atribuido`— porque las dos se usan: la primera para la advertencia,
> la segunda para la curva acumulada del Pareto, que se lee «de lo que pudimos
> atribuir».

### `comparar_dimension(datos, dimension)`

Lección 4. Cuando la dimensión es `cavidad`, agrupa por **molde + cavidad** y
devuelve `advertencia` diciéndolo.

```python
# El promedio de las hermanas EXCLUYE a la propia cavidad. Incluirla diluye
# su desviación y el exceso sale más chico de lo que realmente es.
exceso_vs_hermanas_g = propio - (suma_del_molde - propio) / (cuenta - 1)
```

### `detectar_turnos_anomalos(datos, umbral_z)`

**Z robusto**, con mediana y MAD × 1.4826, no media y desviación estándar. El turno
catastrófico que buscamos es tan extremo que *arrastra* la media y la desviación
clásicas, y termina escondiéndose a sí mismo. La mediana no se mueve.

### Funciones de apoyo para los gráficos

`distribucion_delta_peso`, `serie_costo_acumulado`. Devuelven series bajo claves con
`_` para que no viajen al modelo.

> **Dos funciones que miden lo mismo tienen que cuadrar, y hay que comprobarlo.**
> La regla de «los gráficos y las herramientas llaman a las mismas funciones» no
> cubre este caso: `serie_costo_acumulado` y `calcular_desperdicio` son funciones
> **distintas** que miden lo mismo, y el final de la curva tiene que ser el KPI
> del tablero.
>
> Error real: la primera versión de la curva promediaba el delta de **todas** las
> muestras juntas y lo multiplicaba por las unidades del día. Eso mezcla gramos de
> piezas de 3 g con gramos de piezas de 96 g —la lección 1 rota dentro de un
> gráfico— y daba 87.942 USD contra los 57.222 del KPI. Nadie lo nota mirando: son
> dos pantallas distintas.
>
> La corrección tiene dos partes: que la curva **reutilice** el delta por
> línea+SKU que ya calculó `calcular_desperdicio` en vez de rehacerlo, y que ese
> delta viaje **sin redondear** en una clave `_`. Sumar las cifras ya redondeadas
> de cada combinación desplaza el total y reaparece la diferencia, más chica pero
> visible. Deja el `assert` escrito: la diferencia tiene que ser 0,00.

## La regla de la salida

Toda función que haga un supuesto o tenga una limitación devuelve una de estas
claves: `advertencia`, `aviso`, `nota_metodo`, `nota_conservadora`. El prompt del
agente le ordena incorporarlas.

**Son las salvedades que hacen que la cifra aguante una pregunta incómoda.** Una
respuesta que da un número sin decir sobre qué se paró es una respuesta que se cae
en la primera repregunta.

## Las pruebas

`pruebas/test_calculos.py`, 19 comprobaciones, sin framework: un script que imprime
`[PASA]`/`[FALLA]` y sale con código distinto de cero si algo falla.

No comprueban que el código corra: comprueban que **recupere los siete patrones
sembrados**. Es la diferencia entre una prueba que se siente bien y una que sirve.

Incluye una comprobación de que `filtrar()` recorta los tres archivos de forma
coherente: es fácil que un filtro recorte las muestras y no la producción, y de ahí
salen cocientes absurdos.

## Verificación de esta fase

```bash
.venv/bin/python -m pruebas.test_calculos
```

Debe terminar en `✓ Los cálculos recuperan los 7 patrones`. Pega las 19 líneas.

**Si una prueba falla, lee la cifra que imprime antes de tocar nada.** De las tres
cifras equivocadas que se encontraron construyendo esto, las tres aparecieron
leyendo la salida de las pruebas, no depurando el código.
