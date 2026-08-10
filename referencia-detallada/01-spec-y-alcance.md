# 01 · Alcance, las cinco lecciones y los siete patrones

## El problema

Una planta de empaques plásticos que **no tiene SCADA**. Todo el dato entra a mano,
en archivos que alguien llena al cierre de cada turno. La pregunta que el asistente
tiene que responder es **dónde, cuándo, cómo y por qué se desperdicia material**.

Restricciones del contexto, que definen decisiones de arquitectura:

- **Una persona, una máquina.** Sin login, sin registro, sin multiusuario, sin base
  de datos. Estado en memoria y archivos en disco.
- **Tres archivos de entrada**, en CSV (así salen de Excel):
  - `muestras_qc.csv` — pesos pieza por pieza, con molde y cavidad
  - `produccion_turno.csv` — cierre de turno: kilos, unidades, cambios, nota libre
  - `eventos_operacion.csv` — HMI y bitácora, con quién firmó cada evento
- Lee los CSV con `encoding="utf-8-sig"`, no `utf-8`: los archivos que salen de
  Excel traen BOM, que sin eso se pega a la primera columna y la vuelve ilegible.

## Las cinco lecciones

Son el corazón del taller. Cada una es una trampa en la que un análisis ingenuo cae,
y el sistema tiene que estar construido para no caer.

### 1. El desperdicio son DOS cosas que no se solapan

- **Scrap pesado**: lo que la planta ya mide, va a la báscula de rechazos.
- **Gramaje exceso**: material regalado *dentro de producto conforme*. La pieza pesa
  más que su objetivo, pasa la inspección y **se despacha**. No aparece en ningún
  reporte de scrap de la planta: es invisible para el sistema actual.

Se calcula como `delta_medio × unidades_conformes`, desglosado **por línea y por
SKU** — no un promedio global, porque cada SKU tiene su propio peso objetivo.

Solo cuentan las muestras con `veredicto == "conforme"`, y el delta se recorta en
cero (`.clip(lower=0)`): una pieza que pesa *menos* del objetivo no es un ahorro que
compense a otra que pesa de más, es otro problema.

**Repórtalos separados y sumados**, y di explícitamente que el segundo es invisible
para el sistema actual.

### 2. Deriva y desviación sistemática se corrigen distinto

- **Deriva** (`deriva`): la máquina se desgasta, el peso sube con el tiempo. Se
  corrige con **mantenimiento**.
- **Setpoint desviado** (`setpoint_desviado`): está calibrada en el número
  equivocado desde el principio, pero estable. Se corrige con **un ajuste**.

Recomendar lo contrario hace perder tiempo y plata.

Cómo se distinguen: **regresión sobre las medias diarias**, ponderada por el número
de muestras de cada día (`statsmodels.WLS`). Se clasifica **por la pendiente**, no
por el promedio.

> **La trampa, y es la más fácil de pisar:** el setpoint se juzga por el
> **intercepto** de la regresión, no por la media de la serie. Una línea con deriva
> tiene una media alta *porque derivó*, y si la juzgas por la media la clasificas
> como setpoint desviado — que es exactamente el error que la lección quiere evitar.

### 3. Un lote de resina sin muestra suficiente no es evidencia

Exige un mínimo de turnos (por defecto 10, configurable). Los lotes que no llegan
**se muestran igual, en gris, con su `n` visible al final de la barra**. No se
esconden: mostrarlos descartados enseña más que omitirlos, porque deja ver por qué
se descartaron.

Si el asistente menciona un lote, dice en cuántos turnos se basa. Los descartados se
pueden mencionar como pendientes de confirmar, **nunca como culpables**.

### 4. Una cavidad solo existe junto a su molde

La cavidad 3 del molde A y la cavidad 3 del molde B no tienen nada que ver. Agrupar
por número de cavidad sin el molde mezcla piezas de máquinas distintas.

Cuando se compara por cavidad, se agrupa por **molde + cavidad** y se devuelve una
advertencia diciéndolo. El número accionable es `exceso_vs_hermanas_g`: cuánto pesa
de más una cavidad **contra sus hermanas del mismo molde**.

> **La trampa aritmética:** al calcular el promedio de las hermanas hay que
> **excluir la cavidad que se está evaluando** — `(suma - propia) / (cuenta - 1)`.
> Incluirla diluye su propia desviación y el exceso sale más chico de lo que es.

### 5. Las categorías de desperdicio se solapan

Un mismo turno puede tener cambio de color **y** rechazo de calidad. Los porcentajes
**no suman 100 %** y jamás deben presentarse como una partición ni como una torta.

Cada cifra es el **exceso sobre una línea base**, y la línea base son los turnos sin
transiciones. La función devuelve una `advertencia` cuando la suma pasa del 100 %, y
esa advertencia se muestra al usuario y se le pasa al modelo.

## Los siete patrones sembrados en los datos

El generador siembra estos siete. Cada uno existe para que una lección tenga algo
que encontrar.

| # | Patrón | Qué debe encontrar el asistente |
|---|---|---|
| 1 | Una línea+SKU con **deriva** de peso creciente | Mantenimiento, no ajuste |
| 2 | Otra línea+SKU con **setpoint desviado** plano | Ajuste, no mantenimiento |
| 3 | Un **lote de resina** con más scrap, con n suficiente | El único culpable con evidencia |
| 4 | Lotes con n insuficiente | Se muestran en gris, no se acusan |
| 5 | Una **cavidad** de un molde que pesa de más | Nombrada como molde + cavidad |
| 6 | Un **turno catastrófico** puntual | Anomalía por z robusto |
| 7 | **Notas distintas que significan lo mismo** | Solo esto justifica los embeddings |

### La trampa del generador

Es el error más fácil y el más difícil de ver: **escribir la nota que describe el
turno catastrófico y olvidar mover los números.** El texto dice «arranque con el
molde frío, muchísima rebaba» y los kilos de ese turno son iguales a los de
cualquier otro. Entonces el asistente busca, no encuentra nada, y parece que el
agente falla cuando lo que falla es el dato.

**Protección obligatoria:** el generador termina con un `assert` que compara el
turno sembrado contra el `idxmax` real de kilos de scrap **y** de porcentaje. Si no
coincide, el generador falla ruidosamente en vez de escribir datos mudos.

## Verificación de esta fase

No hay código todavía. Antes de seguir, escribe en el README del proyecto la
sección de las cinco lecciones con sus trampas. Vas a necesitar tenerlas a la vista
en las fases 4 y 5, y escribirlas primero obliga a entenderlas.
