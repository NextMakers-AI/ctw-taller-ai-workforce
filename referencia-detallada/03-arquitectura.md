# 03 · Arquitectura

## La idea que ordena todo

**La interfaz no sabe nada de sopladoras ni de empacadoras.** Lee un *registro de
agentes* y de ahí saca las fuentes de datos, los filtros, los parámetros, las
métricas, los gráficos, las herramientas y el prompt de cada asistente. Agregar un
tercer asistente es escribir un `AgenteDef` más; `app.py` no se toca.

Esto no es abstracción por gusto: los dos agentes son **deliberadamente distintos**
—gramos contra minutos, SKU contra máquina, USD/kg contra COP/hora— y esa
disimilitud es la prueba de que la abstracción sirve. Si los dos fueran parecidos,
no probaría nada.

## Mapa de archivos

```
app.py                      La interfaz. Ni un groupby acá.
src/
  config.py                 Parámetros desde el entorno. Cero cifras de negocio.
  registro.py               EL CONTRATO: Campo, Fuente, Filtro, Parametro,
                            Grafico, AgenteDef + las dos instancias.
  agente.py                 Modelo, prompt, puente de streaming async→sync.
  trazabilidad.py           Registro de filas tocadas, por unión de conjuntos.
  semantica.py              Embeddings e índice vectorial (genérico).
  estilo.py                 Tokens, paleta validada, CSS, tema de Altair.
  reporte.py                El HTML descargable con gráficas incrustadas.

  carga.py                  Agente 1: Datos, preparar_*, filtrar, validar, traza.
  calculos.py               Agente 1: LA ÚNICA FUENTE DE CIFRAS.
  herramientas.py           Agente 1: las 7 @tool.
  graficos.py               Agente 1: 6 gráficos. Ni un groupby.
  generar_datos.py          Agente 1: generador con los 7 patrones.
  verificar_datos.py        Agente 1: verificador independiente.
  preguntar.py              Agente 1: 4 preguntas por consola, sin Streamlit.

  paras/                    Agente 2: mismo esquema, dominio distinto.
    carga.py  calculos.py  herramientas.py  graficos.py
    agente.py  verificar_datos.py  preguntar.py

pruebas/test_calculos.py    19 comprobaciones sobre los cálculos.
```

## Las tres capas y la regla de cada una

```
        ┌───────────────────────────────────────────────┐
        │  app.py            interfaz — CERO groupby     │
        ├──────────────┬────────────────────────────────┤
        │ graficos.py  │ herramientas.py   (@tool)      │
        │              │                                │
        │       las dos llaman a lo mismo ↓             │
        ├───────────────────────────────────────────────┤
        │  calculos.py    LA ÚNICA FUENTE DE CIFRAS     │
        ├───────────────────────────────────────────────┤
        │  carga.py       Datos (dataclass congelado)   │
        └───────────────────────────────────────────────┘
```

**Que los gráficos y las herramientas llamen a las mismas funciones es la decisión
de arquitectura más importante del proyecto.** Es lo que hace imposible que el
tablero y el chat digan cifras distintas para la misma pregunta. Si un gráfico
tuviera su propio `groupby`, tarde o temprano diverge, y en una demostración en vivo
eso destruye la credibilidad de todo lo demás.

## El contrato del registro

```python
@dataclass(frozen=True)
class Campo:
    nombre: str; tipo: str; etiqueta: str
    opciones: tuple = ()          # lista fija
    opciones_de: str | None = None  # o derivadas de una columna de los datos
    obligatorio: bool = True
    ayuda: str = ""; defecto: Any = None; ejemplo: str = ""   # ejemplo = placeholder

@dataclass(frozen=True)
class Fuente:
    clave: str; nombre: str; ruta: Path; descripcion: str; campos: tuple[Campo, ...]

@dataclass(frozen=True)
class Filtro:
    clave: str; etiqueta: str; tipo: str
    opciones_de: str | None = None
    etiquetas: dict | None = None      # cómo se muestra cada opción
    mostrar: Callable | None = None

@dataclass(frozen=True)
class Parametro:
    clave: str; etiqueta: str; valor: float; minimo: float; maximo: float
    paso: float; formato: str; ayuda: str

@dataclass(frozen=True)
class Grafico:
    titulo: str
    fn: Callable[..., tuple[Any, dict]]   # devuelve (gráfico, cifras)
    pie: Callable[[dict], str] = lambda _: ""

@dataclass(frozen=True)
class AgenteDef:
    clave, nombre, icono, resumen, planta_por_defecto
    fuentes, filtros, parametros
    desde_marcos, filtrar, configurar, contexto
    herramientas, prompt, metricas, graficos, preguntas
    columnas_texto, coleccion_semantica, marco_principal
    nota_dashboard: str = ""
```

### El pie de cada gráfico recibe las cifras, no es prosa fija

`Grafico.pie` es una función que recibe el diccionario del cálculo. Eso es
deliberado: **si el archivo de entrada cambia, el texto bajo el gráfico cambia con
él.** Un pie que diga «las seis categorías» con el número escrito a mano miente en
cuanto alguien carga un archivo con cuatro.

Regla: en un pie solo se escribe a mano lo que describa la *codificación* («el
número es el % de scrap», «el tooltip trae MTTR»), nunca una afirmación sobre el
dato.

## El objeto de datos

`Datos` es un **dataclass congelado**. Sus métodos:

- `desde_marcos(marcos)` — construye desde diccionarios de DataFrame, que es lo que
  permite que la interfaz mezcle archivos cargados con los de disco
- `cargar()` — desde los CSV en disco
- `filtrar(**filtros)` — devuelve otro `Datos`, **recortando los tres archivos de
  forma coherente**
- `validar()` — mensajes accionables, no trazas
- `marcos()` — vuelve a diccionarios
- `traza(*fuentes)` — **devuelve los índices de las filas tocadas, no el conteo**

Lo último importa: el registro de trazabilidad tiene que poder *unir* lo que
tocaron varias herramientas sin contar dos veces las mismas filas. Con conteos eso
es imposible; con conjuntos de índices es trivial.

## Verificación de esta fase

```bash
.venv/bin/python -c "
from src import registro
for a in registro.AGENTES.values():
    print(f'{a.clave}: {len(a.herramientas)} herramientas, {len(a.graficos)} gráficos, {len(a.fuentes)} fuentes')
"
```

Y una comprobación de que la regla se cumple:

```bash
grep -rn "groupby\|\.sum()\|\.mean()" app.py src/paras/graficos.py
```

**La regla exacta, que es más fina que «ni un groupby»:** ninguna *cifra de negocio*
se calcula fuera de los módulos de cálculo. Agrupar para **presentación** sí se
permite, y hay un caso legítimo: binificar un histograma por línea. Ahí el `groupby`
no produce una cifra que alguien vaya a citar —produce los bordes de las barras— y
además evita mandarle a Altair 25 000 filas crudas que serializaría enteras en cada
reejecución de Streamlit.

Si dejas un `groupby` de presentación, **escribe en el comentario por qué no es una
cifra**. Cualquier otro es un error.
