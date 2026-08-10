# 04 · El generador de datos y su verificador

## Por qué el generador es una pieza seria

De él depende que el taller funcione. Si los patrones no están *realmente* en los
números, el asistente no encuentra nada y parece que el agente falla cuando lo que
falla es el dato. Por eso el generador tiene tantas protecciones como el análisis.

## Estructura en dos pasadas

Primero el **esqueleto** —qué turnos, qué líneas, qué SKU, qué lote de resina en
cada turno— y después los números. Es al revés de lo intuitivo, y hace falta porque
el patrón del lote malo tiene que caer donde haya suficientes turnos para que sea
detectable. Sembrarlo sobre la marcha lo deja con `n = 4` y la lección 3 lo descarta
—correctamente— por muestra insuficiente.

## El mecanismo que hace invisible al gramaje exceso

Es el detalle más importante del generador, y es de dominio, no de programación.

```python
fuera = peso < objetivo * 0.97 or peso > objetivo * 1.25
```

**La tolerancia es asimétrica**: 3 % por debajo, **25 % por encima**. Así es en una
planta real — una pieza liviana falla la especificación y se rechaza; una pieza
pesada cumple de sobra, pasa la inspección y se despacha. Esa asimetría es
*exactamente* la razón por la que el gramaje exceso existe y nadie lo ve.

Si pones tolerancia simétrica, el sobrepeso se rechaza y la lección 1 desaparece.

## Aritmética cerrada: las unidades no pueden contradecir a los kilos

Un error común es generar kilos por un lado y unidades por otro; después el
analista divide y le salen pesos por pieza imposibles.

```python
kg_consumida = kg_molde / (1 - frac_purga * p)
kg_scrap     = p * kg_consumida
unidades_rechazadas = int(round((kg_scrap - kg_purga) * 1000 / peso_medio))
```

Todo se deriva del porcentaje objetivo de scrap y del peso medio real de las piezas
de ese turno. Así cualquier cociente que alguien calcule después da un número
coherente.

## El `assert` contra la trampa del generador

Obligatorio. Al final del generador:

```python
peor_kg  = produccion["kg_scrap"].idxmax()
peor_pct = produccion["pct_scrap"].idxmax()
assert peor_kg == idx_turno_sembrado and peor_pct == idx_turno_sembrado, (
    "El turno catastrófico está escrito en la nota pero NO en los números. "
    "Esta es la trampa clásica: se redacta el texto y se olvida mover los kilos."
)
```

Sin esto el dataset puede salir mudo y nadie se entera hasta la demostración.

## El verificador, y por qué NO usa el módulo de cálculos

`src/verificar_datos.py` comprueba que los 7 patrones estén en los datos usando
**pandas plano y `numpy.polyfit`**, deliberadamente sin importar `calculos.py`.

La razón: si el verificador usara las mismas funciones que el análisis, un bug en
el análisis podría esconder un patrón mal sembrado, y las dos piezas fallarían de
acuerdo. Dos implementaciones independientes que llegan al mismo número es
evidencia; una sola que se confirma a sí misma no lo es.

Son 10 comprobaciones, cada una impresa como `[PASA]` o `[FALLA]` con la cifra.

### Dos fallos reales del verificador, con su corrección

Escríbelos en los comentarios: quien replique esto va a toparse con los mismos.

**Comprobación 1 fallaba** — rankear las combinaciones línea+SKU por delta medio
conflacaba deriva con desviación fija, que es *la trampa de la lección 2 cometida
por el propio verificador*. Corrección: comparar solo entre combinaciones **planas**
(`|pendiente| < 0.01`).

**Comprobación 2 fallaba** — la medida de dilución quedaba contaminada por los
sesgos propios de cada línea y SKU. Corrección: comparar los números de cavidad
**globalmente**, no dentro de cada combinación.

## Convención de fecha del turno

El turno de noche va de 22:00 a 05:59 y **conserva la fecha de su inicio**. Un
evento de las 02:00 del martes pertenece al turno de noche del lunes.

Agrupar por fecha de calendario parte ese turno entre dos días. En el agente 1 es un
detalle; en el agente 2 es *el* hallazgo (ver `18-agente-paradas.md`).

## Verificación de esta fase

```bash
.venv/bin/python -m src.generar_datos
.venv/bin/python -m src.verificar_datos
```

El segundo tiene que terminar en `✓ Los 7 patrones son detectables`. Pega la salida
completa con las 10 líneas. **Si alguna dice `[FALLA]`, el problema está en el
generador, no en el verificador** — arregla el dato, no la prueba.
