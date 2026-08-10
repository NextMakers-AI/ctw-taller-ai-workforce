# 12 · La pestaña Tablero

Las cifras de un vistazo, sin preguntar nada. Es lo que ve quien no quiere escribir
en un chat — y son **las mismas cifras que diría el agente**, porque salen de las
mismas funciones.

## Estructura

```
┌─────────────────────────────────────────────────────────┐
│  [KPI]   [KPI]   [KPI]   [KPI]     ← st.columns(n)      │
│  nota del tablero                                        │
│  ───────────────────────────────                         │
│  Gráfico 1        │  Gráfico 2      ← rejilla de 2      │
│  pie derivado     │  pie derivado                        │
│  Gráfico 3        │  Gráfico 4                           │
│  ...                                                     │
└─────────────────────────────────────────────────────────┘
```

Todo sale del registro; `app.py` no sabe qué mide cada agente:

```python
cols = st.columns(len(a.metricas(vista, params)))
for col, m in zip(cols, a.metricas(vista, params)):
    col.metric(m["etiqueta"], m["valor"], m["delta"])
if a.nota_dashboard:
    st.caption(a.nota_dashboard)
st.divider()

for i in range(0, len(a.graficos), 2):
    for col, g in zip(st.columns(2), a.graficos[i:i + 2]):
        with col:
            st.subheader(g.titulo)
            chart, res = g.fn(vista, params[a.parametros[0].clave])
            st.altair_chart(chart, width="stretch")
            if pie := g.pie(res):
                st.caption(pie)
```

`width="stretch"` reemplaza al `use_container_width` obsoleto.

## Las métricas

Cada `metricas()` devuelve `etiqueta`, `valor` y `delta`. **El delta no es una
comparación contra un periodo anterior**: es contexto de la misma cifra —«7 555 USD»
bajo los kilos, «6.50 % del consumo» bajo el scrap—. Nombrarlo «delta» es de
Streamlit, no del dominio.

> **Trampa visual:** `st.metric` pinta el delta **en verde y con flecha hacia arriba**
> cuando lo interpreta como positivo. Eso **afirma una mejora que nadie dijo** — «6.5 %
> del consumo» no es una buena noticia. Neutralízalo por CSS: fondo, color y flecha.

Las dos primeras métricas del agente 1 son la lección 1 hecha número: scrap pesado y
gramaje exceso, separados. La primera cosa que ve quien abre la aplicación es que el
desperdicio son dos cosas.

## La nota del tablero

Debajo de las métricas, una línea que explique lo que las cifras no dicen solas:

> El **gramaje exceso** no aparece en ningún reporte de scrap de la planta: es
> material regalado dentro de producto conforme, que se despacha.

**Es una definición, no una cifra.** Sigue siendo cierta con cualquier archivo de
entrada. Esa es la vara para decidir qué texto puede ir fijo en la interfaz.

## Los pies de gráfico

Cada uno es una función que recibe el diccionario del cálculo (ver `03`). En el
tablero se renderizan con `st.caption` justo debajo de su gráfico.

Regla, otra vez porque es la que más se rompe: **solo se escribe a mano lo que
describa la codificación**; toda afirmación sobre el dato se interpola. Un pie que
diga «las seis categorías» miente en cuanto alguien cargue un archivo con cuatro.

## Cuando el filtro no deja nada

```python
if getattr(vista, a.marco_principal).empty:
    st.error("El filtro no deja ningún registro. "
             "Amplía el rango o quita una condición.")
```

Un tablero de gráficos vacíos sin explicación parece una aplicación rota. El mensaje
tiene que decir **qué hacer**, no solo qué pasó.

Lo mismo en la pestaña del reporte: *«no hay nada que reportar»* antes de dejar que
alguien genere un documento en blanco.

## Rejilla de dos columnas, no de tres

Con tres por fila, las etiquetas de eje se recortan y los mapas de calor quedan
ilegibles. Dos es el máximo con el ancho `layout="wide"` de Streamlit.

En el **reporte**, en cambio, va una sola columna: en un documento que se lee de
corrido no hay razón para apretar dos gráficas por fila (ver `16`).

## Verificación de esta fase

```bash
.venv/bin/python -c "
from src import registro, carga
for clave, cargador in (('desperdicio', None),):
    a = registro.por_clave(clave)
    d = carga.cargar()
    ms = a.metricas(d, {p.clave: p.valor for p in a.parametros})
    for m in ms:
        print(f\"  {m['etiqueta']}: {m['valor']}  ({m.get('delta')})\")
"
```

Y en la aplicación, para cada agente y en los dos modos:

1. Las métricas se ven completas, sin cortar el número.
2. Ninguna píldora de delta en verde con flecha.
3. Los seis gráficos con su pie, sin etiquetas de eje recortadas.
4. Pon un filtro que no deje registros → sale el mensaje accionable, no gráficos
   vacíos.
5. Cambia el supuesto en la barra lateral → las métricas y los pies cambian.
