# 08 · La interfaz: armazón

Este archivo cubre el esqueleto. Las cuatro piezas grandes van aparte:

- `09-chat.md` — la conversación
- `10-formularios-y-cargue.md` — carga de archivos y captura manual
- `11-filtros-sidebar.md` — la barra lateral y los filtros
- `13-estilos-y-paleta.md` — el sistema visual

## Estructura

Barra lateral con: selector de asistente, ficha de la planta, filtros, supuestos.
Área principal con **cuatro pestañas**: Preguntar · Tablero · Generar reporte ·
Datos.

`app.py` no menciona sopladoras ni empacadoras: todo sale del registro de agentes.

**Sin título de página sobre las pestañas.** Se quitó a propósito: la navegación de
la barra lateral ya dice qué asistente está activo, así que un `h1` encima solo
repetía eso y empujaba el contenido hacia abajo.

**Sin barra de herramientas de Streamlit.** «Deploy» y las opciones de
desarrollador son controles de Streamlit, no de esta aplicación; en un taller no
hay nada que desplegar y ese botón invita a apretarlo.

> **`toolbarMode` decide también si existe el selector de tema**, y eso hay que
> decidirlo a propósito. Las dos opciones esconden «Deploy»:
>
> - `"viewer"` deja el menú ⋮ con **System / Light / Dark**.
> - `"minimal"` se lleva el menú entero, y con él ese selector.
>
> Importa porque el tema **sigue al sistema operativo**: con `"minimal"`, quien
> tenga el equipo en claro ve la aplicación en claro y no tiene ninguna forma de
> cambiarlo salvo cambiarle la apariencia a todo su computador. En una sala con
> equipos mezclados y un proyector de por medio, eso es una limitación real.
>
> Y **no se puede reemplazar por un control propio en la barra lateral**: el tema
> de los widgets lo resuelve Streamlit desde el `config.toml`, así que un botón
> hecho a mano solo cambiaría el CSS propio y las gráficas, y dejaría los widgets
> del color contrario.
>
> Regla: si la aplicación sigue al sistema, va `"viewer"`. `"minimal"` solo es
> correcto si el tema está **fijado** —los dos bloques del `config.toml` con la
> misma paleta— porque ahí las tres opciones renderizarían lo mismo y un selector
> que no cambia nada se lee como un defecto.

Más una regla CSS de respaldo.

## Caché

Streamlit reejecuta el script entero en cada interacción. Sin caché, cada mensaje
volvería a leer los CSV y a cargar el modelo de embeddings —más de un gigabyte—
desde cero.

- `@st.cache_data` para los archivos
- `@st.cache_resource` para el objeto de datos, el modelo de embeddings, el índice y
  el agente

Los parámetros que no son *hashables* llevan `_` delante del nombre para que
Streamlit los ignore al calcular la clave de caché: `def _agente(clave, _datos)`.

## Estado por agente

Chat, archivos cargados y filas agregadas a mano viven en claves separadas por
agente. Un ayudante corto lo resuelve:

```python
def k(clave: str, *partes: str) -> str:
    """Clave de session_state con el agente adentro: cada uno con su estado."""
    return "__".join([clave, *partes])
```

Cambiar de asistente y volver no pierde la conversación ni los datos.

## Las pestañas y la persistencia en la URL

Un F5 abre una sesión nueva y **el estado de sesión se pierde entero**. La URL es lo
único que sobrevive, así que agente y pestaña van en `st.query_params`:

```
http://localhost:8501/?agente=paras&tab=tablero
```

De paso, el enlace se puede compartir apuntando a una vista concreta.

Se guarda un **id corto** y no la etiqueta completa de la pestaña, para que la barra
de direcciones quede legible y para que cambiar un texto de pestaña no invalide los
enlaces guardados.

### La trampa del `default` de `st.tabs`

Pasar `default=` en **cada** corrida hace que la pestaña vuelva sola a la de la URL
apenas se hace clic en otra: el clic cambia el estado y el `default` de la corrida
siguiente lo pisa. La pestaña parece no responder.

Pásalo **solo en la primera corrida** de ese agente:

```python
primera_vez = clave_pestana not in st.session_state
pedida = st.query_params.get("tab") if primera_vez else None
pestanas = st.tabs(
    list(ETIQUETAS.values()),
    default=ETIQUETAS.get(pedida),      # None = la primera
    key=clave_pestana,
    on_change=_sincronizar_pestana,     # escribe el cambio en la URL
)
```

El agente se persiste igual, leyéndolo de `st.query_params` la primera vez que se
inicializa el estado. **Escribe la URL solo si cambió**: asignar el mismo valor en
cada corrida provoca otra reejecución y el ciclo no para nunca.

## Dos trampas de CSS que condicionan todo lo demás

### Streamlit 1.61 no expone NINGUNA variable CSS

Sus estilos son CSS-en-JS con los valores ya interpolados. Cualquier
`var(--algo, #reserva)` que escribas **siempre** usa el valor de reserva.

Consecuencia real: en modo oscuro toda la interfaz usaba los colores claros y había
cajas con texto blanco sobre fondo blanco. La hoja de estilos tiene que ser una
**función de Python que recibe el modo** e interpola los hex reales:

```python
def css(modo_oscuro: bool) -> str:
    t = tokens(modo_oscuro)
    return f"""<style> ... background: {t['fondo']}; ... </style>"""
```

El modo se lee con `st.context.theme.type`.

### `key=` es el único ancla CSS estable

Streamlit publica `key="x"` como clase `st-key-x`. El alto, el borde y el resto los
pone en clases generadas (`st-emotion-cache-*`) que **cambian entre versiones**.

**Nunca apuntes a `st-emotion-cache-*`.** Si necesitas estilar un contenedor, dale
un `key` aunque no necesites su estado.

## Verificación de esta fase

```bash
.venv/bin/streamlit run app.py --server.port 8501
```

1. Las cuatro pestañas abren sin excepción, en los dos agentes.
2. Recargar en Paradas/Tablero deja donde estaba; la URL dice `?agente=paras&tab=tablero`.
3. Hacer clic en otra pestaña la cambia **y se queda** (si vuelve sola, el `default`
   se está pasando en cada corrida).
4. Cero trazas en consola al arrancar.
