# 12 · Primer agente — desperdicio de material

Este archivo es la **definición del agente 1 como entrada del registro**: qué
fuentes declara, qué filtros, qué supuestos, qué métricas, qué gráficos y qué
prompt. Su dominio está en `01`, sus cálculos en `05`, sus herramientas en `06` y
sus gráficos en `10`; acá se junta todo en el `AgenteDef` que consume `app.py`.

Es el **agente de referencia**: se construye primero y completo, y el segundo
(`18-agente-paradas.md`) replica el patrón en otro dominio para probar que la
abstracción sirve.

## Identidad

```python
clave   = "desperdicio"
nombre  = "Desperdicio de material"
icono   = ":material/scale:"
resumen = ("Dónde, cuándo, cómo y por qué se desperdicia material en una planta "
           "de empaques plásticos: scrap pesado y gramaje regalado dentro de "
           "producto conforme.")
marco_principal = "muestras"
```

El nombre de la planta **no se escribe acá**: sale de los datos. Ningún nombre
propio de empresa en el código.

## Las tres fuentes

Cada una declara sus campos con tipo, etiqueta, si es obligatorio, ayuda y
**`ejemplo`, que es el placeholder del formulario**. De esa declaración salen solos
el validador de CSV y el formulario de carga manual.

| Fuente | Clave | Qué trae |
|---|---|---|
| Muestras de laboratorio | `muestras` | Peso pieza por pieza, con **molde y cavidad**, veredicto, lote de resina |
| Cierres de turno | `produccion` | Kilos consumidos y de scrap, unidades, cambios de molde/color, **nota del supervisor** |
| Eventos de operación | `eventos` | HMI y bitácora, con **quién firmó** cada evento y su descripción |

Las columnas de texto libre —la nota del supervisor y la descripción del evento—
son las únicas que se indexan semánticamente (ver `07`).

## Filtros y supuestos

**Filtros** (todas las opciones se derivan de los datos, ninguna escrita a mano):
rango de fechas, línea, SKU, turno.

**Supuesto** (un solo parámetro): precio de la resina en USD/kg, por defecto 1.85,
con paso de 0.05. Va en la barra lateral porque **es un supuesto del negocio y no
una medición del archivo**, y quien presenta tiene que poder cambiarlo en vivo.

Los filtros aplican **también al chat**, no solo al tablero: las herramientas
reciben la vista filtrada. Dilo en la barra lateral, porque si no la gente asume que
el chat ve todo.

## Las métricas del tablero

Cuatro, y las dos primeras son la lección 1 hecha número:

| Métrica | Delta |
|---|---|
| Desperdicio total (kg) | su equivalente en USD |
| Scrap pesado (kg) | % del consumo |
| Gramaje exceso (kg) | % del total |
| Turnos analizados | — |

`nota_dashboard`, debajo de las métricas:

> El **gramaje exceso** no aparece en ningún reporte de scrap de la planta: es
> material regalado dentro de producto conforme, que se despacha.

Es una definición, no una cifra: sigue siendo cierta con cualquier archivo.

## Los seis gráficos y sus pies

Los pies son **funciones que reciben el diccionario del cálculo**. Regla: solo se
escribe a mano lo que describa la *codificación*; toda afirmación sobre el dato se
interpola.

| Gráfico | Qué lleva el pie |
|---|---|
| ¿De qué tipo es el desperdicio? | Cuántas categorías concentran el 80 % **de lo atribuido**, más la aclaración de que se solapan y la advertencia de solapamiento si viene |
| ¿Dónde y cuándo se concentra? | Solo la codificación: «el número es el % de scrap» |
| ¿Cuánto nos alejamos del objetivo? | % de muestras por encima, n de muestras y delta medio — los tres del cálculo |
| ¿Se desgasta o está descalibrada? | La clasificación de cada grupo, interpolada |
| ¿Qué lote se comporta distinto? | El mínimo de turnos exigido, interpolado del parámetro |
| ¿Cuánto llevamos gastado? | USD acumulados y USD/día, más qué es la franja de arriba |

> **Trampa a evitar en el último pie:** decía «la franja de arriba es la que hoy
> nadie mide». Eso afirma algo sobre la planta de quien lee, no sobre el dato.
> Correcto: nombrar qué es la franja —el gramaje exceso, que se despacha dentro de
> producto conforme— y dejarle la conclusión a quien lee.

## Las cuatro preguntas de ejemplo

Van en el registro y aparecen como sugerencias en el chat. Cada una ejercita una
lección distinta, y **ninguna lleva una fecha escrita a mano**:

1. «¿Cuánto material estamos desperdiciando y de qué tipo es? Separa lo que la
   planta ya mide de lo que no.» → lección 1
2. «¿Qué líneas hay que recalibrar y cuáles necesitan mantenimiento? No me las
   mezcles.» → lección 2
3. «¿Hay algún lote de resina que se comporte peor que los demás?» → lección 3
4. «¿Cuál fue el peor turno del período y qué pasó ahí? ¿Ha pasado algo parecido
   antes?» → patrón 6 + patrón 7 (embeddings)

La cuarta decía «el 18 de junio» y hubo que cambiarla: el rango de los datos se
deriva del día en que se generaron, así que la pregunta se rompía sola en cuanto
alguien volvía a correr el generador. Además, que el agente **encuentre** el peor
turno es la demostración que importa.

## El prompt del sistema

Detallado en `06-agente-y-herramientas.md`. Lo específico de este agente:

- El inventario que se interpola es **líneas, SKU con su peso objetivo, turnos y
  rango de fechas**, todo derivado de los CSV al arrancar.
- Las seis reglas de interpretación son las cinco lecciones más «`buscar_notas_similares`
  no cuenta nada».

## Verificación de esta fase

```bash
.venv/bin/python -c "
from src import registro
a = registro.por_clave('desperdicio')
print(f'{len(a.fuentes)} fuentes · {len(a.filtros)} filtros · {len(a.parametros)} parámetro(s)')
print(f'{len(a.herramientas)} herramientas · {len(a.graficos)} gráficos · {len(a.preguntas)} preguntas')
assert all(f.ejemplo for fu in a.fuentes for f in fu.campos), 'hay campos sin placeholder'
print('todos los campos tienen placeholder')
"
```

Debe dar **3 fuentes · 4 filtros · 1 parámetro · 7 herramientas · 6 gráficos · 4
preguntas**.

Y en la aplicación, con el agente activo: las cuatro sugerencias se lanzan al hacer
clic, y cada respuesta trae su bloque de trazabilidad al final.
