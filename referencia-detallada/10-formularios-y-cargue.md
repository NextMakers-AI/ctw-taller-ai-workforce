# 10 · Formularios, cargue de archivos y placeholders

La pestaña **Datos**. Es la pieza que convierte una demostración en una herramienta:
sin ella, el asistente solo sabe hablar del dataset sintético.

## La idea que la hace barata de mantener

**Nada de esto se escribe a mano por agente.** Cada fuente declara sus campos en el
registro, y de esa declaración salen solos el validador de CSV, el formulario de
captura y la lista de columnas esperadas.

```python
@dataclass(frozen=True)
class Campo:
    nombre: str          # el nombre real de la columna en el CSV
    tipo: str            # texto | texto_largo | numero | entero | fecha | hora | opcion
    etiqueta: str        # cómo se le dice a una persona
    opciones: tuple = ()          # lista fija de valores
    opciones_de: str | None = None  # o derivadas de una columna de los datos
    obligatorio: bool = True
    ayuda: str = ""      # el tooltip
    defecto: Any = None  # valor inicial
    ejemplo: str = ""    # EL PLACEHOLDER
```

Agregar una columna a una fuente es agregar un `Campo`. El formulario y el validador
se enteran solos.

## Regla de oro de la pestaña

> Los cambios valen **para esta sesión**. El tablero y el chat los ven de inmediato,
> porque los dos leen del mismo objeto de datos. **Los archivos en disco no se
> tocan.**

Dilo en la interfaz, arriba de todo. Quien carga un archivo en una sala llena
necesita saber que no está sobrescribiendo nada.

## Estructura

Un `expander` por fuente, con el título mostrando el estado real:

```
**Cierres de turno** · `produccion.csv` — 563 filas · archivo cargado · +1 a mano
```

Dentro, dos pestañas: **Cargar un archivo** y **Agregar un registro**.

---

## Cargar un CSV completo

### Se dicen las columnas esperadas ANTES de pedir el archivo

```
Columnas que espera: `fecha`, `turno`*, `linea`*, `kg_consumida`*, …
Las marcadas con * son obligatorias.
```

Sin esto, la gente sube el archivo, falla, y no sabe qué arreglar.

### Lectura

```python
pd.read_csv(archivo, encoding="utf-8-sig")
```

`utf-8-sig` y **no** `utf-8`: los archivos que salen de Excel traen BOM, que sin esto
se pega a la primera columna y la vuelve ilegible — el error clásico de
`'﻿columna' not found`.

Si la lectura falla, el mensaje no es una traza:

> No pude leer el archivo: `ParserError: ...`
> Revisa que sea un CSV separado por comas y guardado en UTF-8.

### Validación: mensajes accionables, no stacktraces

Dos capas: las columnas obligatorias que faltan, y el validador propio de la fuente
(tipos, rangos, coherencia).

Los mensajes tienen que decir **qué columna y qué tan mal está**:

> ✗ `duracion_min` no es numérica en el 40 % de las filas
> ✗ Faltan columnas obligatorias: `linea`, `turno`

y no:

> ✗ ValueError: could not convert string to float

Si hay problemas, **el archivo no se carga**. Se muestran todos juntos con su
conteo: `3 problema(s) — no lo cargué`.

### Confirmación en dos pasos

Si es válido: se muestra el resumen (`1.204 filas, 9 columnas`), **una vista previa
de 5 filas**, y recién ahí el botón *«Usar este archivo como …»*. Reemplazar la
fuente de datos de un tablero no puede ser un solo clic accidental.

Al aceptar hay que **invalidar la caché del índice semántico** (`_buscador.clear()`):
las notas cambiaron y el índice viejo apunta a filas que ya no existen. Es el tipo de
bug que no da error, solo devuelve resultados equivocados.

### Siempre se puede volver atrás

Un botón *«Volver al archivo original»* cuando hay un archivo cargado. El original en
disco nunca se tocó, así que revertir es poner la clave de sesión en `None`.

---

## Agregar un registro a mano

Para cargar lo que acaba de pasar en el turno sin editar el CSV.

Va dentro de `st.form(..., clear_on_submit=True)`: sin formulario, cada tecla
reejecuta el script entero y recalcula el tablero. En dos columnas, porque una
fuente con nueve campos en una sola columna obliga a hacer scroll para llenarla.

### Cada tipo de campo tiene su control

| `tipo` | Control | Detalle |
|---|---|---|
| `opcion` | `selectbox` | Con `opciones` fijas |
| (con `opciones_de`) | `selectbox` | **Opciones derivadas de los datos**: las líneas que existen, no una lista escrita a mano |
| `fecha` | `date_input` | Se guarda como texto ISO |
| `hora` | `time_input` | Se guarda como `%H:%M` |
| `entero` | `number_input` | `step=1` |
| `numero` | `number_input` | `step=0.1`, `format="%.2f"` |
| `texto_largo` | `text_area` | Para la nota del supervisor |
| `texto` | `text_input` | |

Que las opciones se deriven de los datos es lo que impide que alguien registre una
línea que no existe y contamine el tablero con una categoría fantasma.

### Los placeholders no son opcionales

**Todo campo lleva `placeholder=campo.ejemplo`.** Un formulario de nueve campos
vacíos no dice qué espera en cada uno: ¿`duracion_min` en minutos o en horas?,
¿`lote_resina` con guion o sin guion?

El `ejemplo` es un valor real y verosímil del dominio —`R-P2512`, `1250.5`,
`arranque con molde tibio, se estabilizó`— no un texto genérico tipo «escriba aquí».

`ayuda` va aparte, como tooltip, para lo que no cabe en un placeholder.

> **Trampa de `number_input`:** si pasas `format="%d"` con un `value` flotante,
> Streamlit lanza `NumberInput value has type float but format %d`. Usa `"%.0f"` para
> enteros mostrados sin decimales.

### Validación al enviar

Los obligatorios que quedaron vacíos se listan **por su etiqueta legible**, no por el
nombre de la columna: quien llena el formulario ve «Línea», no `linea`.

Al aceptar, la fila entra al final y **se recalcula todo**: métricas, gráficos y las
herramientas del agente. Es el momento en que se ve que el tablero y el chat leen del
mismo sitio.

### El detalle que hace que parezca roto

Si alguien agrega una fila con fecha **fuera del rango del filtro**, no aparece por
ningún lado y parece que no se guardó.

Solución: el rango de fechas debe **seguir a los datos nuevos cuando el usuario no lo
haya estrechado a mano**. Si lo estrechó a propósito, se respeta su decisión.

---

## Cómo se mezclan las tres fuentes de datos

```python
def datos_activos(a):
    """base en disco + archivo cargado + filas agregadas a mano."""
    overrides, notas = {}, []
    for f in a.fuentes:
        subido = st.session_state.get(k(a.clave, "subido", f.clave))
        extras = st.session_state.get(k(a.clave, "extra", f.clave)) or []
        if subido is None and not extras:
            continue
        marco = subido if subido is not None else _marcos_base(a.clave)[f.clave]
        if extras:
            marco = pd.concat([marco, pd.DataFrame(extras)], ignore_index=True)
        overrides[f.clave] = marco
    if not overrides:
        return _datos_base(a.clave), []          # el objeto cacheado, tal cual
    return a.desde_marcos({**_marcos_base(a.clave), **overrides}), notas
```

Si nadie tocó nada, se devuelve el objeto cacheado **sin reconstruir**. Solo cuando
hay cambios se rearma — cuesta unas décimas de segundo y es la única forma de que lo
cargado se refleje en el tablero y en el chat a la vez.

Las `notas` se muestran en la barra lateral: *«Cierres de turno: archivo cargado
(1.204 filas)»*, para que nadie olvide que está mirando datos modificados.

## Verificación de esta fase

1. Sube un CSV al que le falte una columna obligatoria → mensaje que **nombra la
   columna**, y el archivo **no** se carga.
2. Sube uno válido → resumen, vista previa de 5 filas, y recién ahí el botón.
3. Agrega una fila a mano con la fecha de hoy → aparece en el tablero **y** el
   asistente la ve al preguntarle.
4. Todos los campos de todos los formularios muestran un placeholder:

```bash
.venv/bin/python -c "
from src import registro
for a in registro.AGENTES.values():
    faltan = [(f.clave, c.nombre) for f in a.fuentes for c in f.campos if not c.ejemplo]
    print(f'{a.clave}: {faltan or \"todos los campos con placeholder\"}')
"
```
