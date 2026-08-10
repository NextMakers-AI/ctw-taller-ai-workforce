# 11 · La barra lateral: navegación, filtros y supuestos

## Qué lleva, en este orden

1. **Logo** (`st.logo`, que lo coloca arriba solo)
2. **Asistente** — la navegación entre agentes
3. **Datos** — la ficha de la planta
4. **Filtros**
5. **Supuestos** — los parámetros del negocio

Lo que **no** lleva: ningún bloque de «Modelo» diciendo qué LLM está detrás. Se
quitó: es información del constructor, no de quien usa la aplicación.

## La navegación entre asistentes

**Lista de navegación, no un `st.radio`.** Es el patrón `SidebarMenu` de shadcn: el
ítem activo en pastilla translúcida del primario con texto del primario, el resto
transparente.

```python
def nav_agentes(st, agentes, clave_estado="agente_activo"):
    if clave_estado not in st.session_state:
        de_url = st.query_params.get("agente")
        st.session_state[clave_estado] = de_url if de_url in agentes else next(iter(agentes))
    for c, ag in agentes.items():
        activo = c == st.session_state[clave_estado]
        if st.button(ag.nombre_completo(), key=f"nav_{c}",
                     type="primary" if activo else "tertiary", width="stretch"):
            st.session_state[clave_estado] = c
            st.query_params.clear()          # la pestaña del otro agente no aplica
            st.query_params["agente"] = c
            st.rerun()
    return st.session_state[clave_estado]
```

El asistente **vive en la URL** (ver `08`): recargar abre una sesión nueva y el estado
de sesión se pierde entero.

### Cuatro detalles visuales que cuestan hacer bien

- **El hover no puede quedar blanco sobre blanco.** Fija fondo y color explícitos en
  cada estado; no confíes en heredar.
- **El activo, translúcido**, no un relleno sólido: un bloque de color saturado en la
  barra lateral pesa más que el contenido de la página.
- **Espacio entre ítems con `margin-bottom` en el botón**, no con `gap` del bloque:
  con `gap`, los ítems se montan sobre la etiqueta del grupo.
- **Sin `help=`.** El tooltip de Streamlit es una caja grande que **tapa el ítem
  activo** y desplaza el layout. La descripción del asistente elegido va como texto
  debajo de la lista, que además se lee sin pasar el mouse.

## La ficha de la planta

Tarjeta de borde 1 px —no un título grande— con el nombre de la planta **derivado de
los datos**, el rango disponible y el conteo de filas por fuente:

```
Envases del Pacífico S.A.S.
2026-02-08 → 2026-08-06
25,395  muestras_qc
   562  produccion_turno
 3,194  eventos_operacion
```

Cuando hay archivos cargados o filas agregadas, debajo va un aviso diciendo qué se
modificó en esta sesión.

## Los filtros

Todas las opciones se **derivan de los datos**. Ninguna lista escrita a mano: si el
archivo trae una línea nueva, aparece sola; si trae una menos, desaparece sola.

| Agente 1 | Agente 2 |
|---|---|
| Rango de fechas · Línea · SKU · Turno | Rango de fechas · Línea · Máquina · Turno · Categoría de falla |

Cada `Filtro` puede traer `etiquetas` (cómo se muestra cada opción, distinto de su
valor) y `mostrar` (una función para formatear).

### Los filtros aplican TAMBIÉN al chat

No solo al tablero. Las herramientas del agente reciben la vista filtrada:

```python
vista = a.filtrar(datos, **filtros)
a.configurar(datos, params, filtros, buscador, error_buscador)
```

**Dilo en la barra lateral**, porque si no la gente asume que el chat ve todo:

> Los filtros se aplican **también al chat**. El bloque de trazabilidad al final de
> cada respuesta muestra el rango y las filas que realmente se consultaron.

Y ese bloque es la prueba: si alguien duda, ahí está el rango consultado.

### La trampa grande: Streamlit recolecta el estado de los widgets no dibujados

Al cambiar de asistente, los filtros del otro **no se renderizan** y Streamlit
**borra su estado**. Al volver, aparecen reseteados. Es el defecto más molesto de la
aplicación si no se resuelve.

La solución es espejar el valor en una clave propia por agente —que Streamlit no
limpia— y desde ahí recalcular el valor inicial de cada control:

```python
vista_previa = st.session_state.setdefault(k(clave, "vista"), {})
...
valor = st.selectbox(f.etiqueta, opciones,
                     index=opciones.index(vista_previa.get(f.clave, opciones[0])))
vista_previa[f.clave] = valor
```

> **Estos widgets NO llevan `key=`.** Si lo llevaran, el estado del widget le ganaría
> al valor que le pasas por `index=`/`value=` y el espejo no serviría para nada. Es
> contraintuitivo y es exactamente lo que hay que hacer.

### El rango de fechas se reconcilia con los datos actuales

El rango guardado se compara con el que tienen los datos **ahora**. Si alguien cargó
un archivo con otro periodo, o agregó una fila fuera del rango, el filtro tiene que
seguir a los datos **cuando el usuario no lo haya estrechado a mano**.

Sin esto, agregar una fila con la fecha de hoy la deja invisible y parece que no se
guardó.

## Los supuestos

Van en su propio grupo, separados de los filtros, porque **son de otra naturaleza**:
un filtro recorta el dato, un supuesto le pone precio.

| Agente | Parámetro | Por defecto |
|---|---|---|
| Desperdicio | Precio de resina (USD/kg) | 1.85 |
| Paradas | Costo de paro (COP/hora) | 2 000 000 |

Están en la interfaz y no en el código porque **quien presenta tiene que poder
cambiarlos en vivo** cuando alguien de la sala diga «ese precio no es el nuestro» —
que es la pregunta que siempre aparece.

El tablero y el chat deben reaccionar al cambio de inmediato, y el pie de los
gráficos debe decir que la cifra depende de ese supuesto:

> Las horas se valoran al costo de paro configurado en la barra lateral, que es un
> **supuesto del negocio** y no una medición del archivo.

> **Trampa:** `st.number_input` con `format="%d"` y un `value` flotante lanza
> `NumberInput value has type float but format %d`. Usa `"%.0f"`.

## Etiquetas de grupo

Cada bloque lleva su etiqueta en versalitas —`ASISTENTE`, `DATOS`, `FILTROS`,
`SUPUESTOS`—: 0.6875rem, peso 600, `letter-spacing: 0.06em`, mayúsculas, tinta suave.
Es el `SidebarGroupLabel` de shadcn y es lo que hace que la barra lateral se lea como
secciones y no como una lista larga.

**El divisor de la barra lateral tiene que verse también con la barra cerrada.**

## Verificación de esta fase

1. Pon un filtro de línea, cambia de asistente y vuelve → **el filtro sigue puesto**.
2. Cambia el precio de la resina → las métricas y los gráficos cambian, y también la
   siguiente respuesta del chat.
3. Agrega una fila con la fecha de hoy en la pestaña Datos → aparece sin tener que
   tocar el filtro de fechas.
4. Cierra la barra lateral → el divisor se sigue viendo.

```bash
.venv/bin/python -c "
from src import registro, carga
d = carga.cargar()
a = registro.por_clave('desperdicio')
for f in a.filtros:
    print(f'{f.clave}: {registro.opciones_de_filtro(d, f)[:4]}')
"
```

Todas las opciones tienen que salir de los datos, ninguna escrita a mano.
