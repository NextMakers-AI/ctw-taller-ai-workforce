# 07 · Búsqueda semántica

## Para qué sirve, y para qué no

**Solo para el texto libre.** Es el patrón 7: notas distintas que significan lo
mismo. Un supervisor escribe «arranque con molde tibio», otro «la máquina salió
fría», otro «primeras cajas con rebaba» — tres textos sin una palabra en común y el
mismo problema.

**Nunca para números.** Un embedding de «4 084 kg» no significa nada; ese número se
suma. Escríbelo en el código y en el README, porque es la confusión más común al
meter una base vectorial en un proyecto de datos.

La herramienta `buscar_notas_similares` **no cuenta nada**. Sirve para «¿ha pasado
esto antes?» y para mostrar que varias personas reportaron lo mismo con palabras
distintas. Si alguien pregunta *cuánto*, la respuesta viene de una función de
cálculo.

## El modelo y sus prefijos

`intfloat/multilingual-e5-base`. Este modelo **exige prefijos asimétricos** y sin
ellos la calidad se degrada de forma silenciosa:

- lo que se indexa lleva `passage: `
- lo que se consulta lleva `query: `

En `chromadb` eso se implementa con una `EmbeddingFunction` que tiene los dos
métodos separados:

```python
class FuncionE5(EmbeddingFunction):
    def __call__(self, input):        # indexado
        return modelo.encode([f"passage: {t}" for t in input]).tolist()
    def embed_query(self, input):     # consulta
        return modelo.encode([f"query: {t}" for t in input]).tolist()
```

Ese gancho de dos métodos es justamente el que hace falta; una sola función para
ambos lados desperdicia la mitad de lo que el modelo sabe hacer.

## Se embebe por texto distinto, no por fila

Si 40 turnos comparten la nota «sin novedad», eso es **un** vector, no 40. Embeber
por fila multiplica el costo y llena los resultados de duplicados que no aportan.

Guarda junto a cada texto las filas donde aparece, para poder devolver cuántas veces
se escribió algo parecido — que es dato, aunque el conteo no venga del modelo.

## Genérico desde el principio

El módulo no sabe de desperdicio ni de paradas: recibe qué columnas de qué marcos
contienen texto.

```python
recopilar_textos(marcos, columnas)
construir_indice(marcos, columnas, coleccion, forzar=False)
buscar_notas(buscador, marcos, consulta, k, columna, campos_ejemplo)

COLUMNAS_DESPERDICIO = [("produccion", "nota_supervisor"), ...]
COLUMNAS_PARAS       = [("downtime", "comentario_operario"), ...]
```

El modelo de embeddings se comparte entre los dos agentes con `functools.lru_cache`:
pesa más de un gigabyte y cargarlo dos veces es un minuto perdido y memoria de más.

## En macOS Intel el camino normal NO existe

Y no es algo que se arregle configurando. PyPI publica `torch` **hasta 2.2.2**
para `macosx x86_64` —PyTorch dejó de compilar para esa plataforma— y ese binario
está construido contra NumPy 1.x, mientras que este stack fija `numpy==2.5.1`
porque `pandas 3` lo exige. Cualquier llamada a `encode` termina en
«RuntimeError: Numpy is not available», y un `import sentence_transformers` suelto
escupe una traza larga que **no es un error de la aplicación**.

La salida fácil sería degradar la búsqueda semántica. No se hace: es el único
patrón que justifica los embeddings en todo el proyecto. Se usa **el mismo modelo
por otro camino** — `intfloat/multilingual-e5-base` publica su exportación a ONNX
en su propio repositorio (`onnx/model.onnx` y `onnx/tokenizer.json`), y
`onnxruntime` y `tokenizers` ya están en el entorno.

Los dos motores tienen que hacer **exactamente lo mismo**: los mismos prefijos,
*mean pooling* sobre la máscara de atención y normalización L2. Si no, los
vectores del índice y los de la consulta no viven en el mismo espacio.

```python
@functools.lru_cache(maxsize=1)
def motor():
    try:
        # El intento fallido escupe cientos de líneas por stderr que se leen como
        # errores de la aplicación sin serlo: se silencian, y el motivo queda
        # guardado en el motor de respaldo para poder mostrarlo si hace falta.
        with warnings.catch_warnings(), contextlib.redirect_stderr(io.StringIO()):
            warnings.simplefilter("ignore")
            return _MotorTorch()
    except Exception as error:
        return _MotorOnnx(motivo=str(error))
```

Importante para que esto funcione: **`sentence_transformers` no se importa a nivel
de módulo en ninguna parte**, solo dentro de ese `try`. Un import arriba del
archivo tumbaría la aplicación entera en esas máquinas, y el resto del sistema no
depende de él.

## El índice no puede tumbar la aplicación

Si `chromadb` o el modelo fallan, **el resto del sistema tiene que seguir
funcionando**: el tablero y las seis herramientas de cálculo no dependen de esto.
Captura la excepción, guarda el mensaje y muéstralo como advertencia en la barra
lateral. Nada de una traza en pantalla completa por una pieza opcional.

## Verificación de esta fase

```bash
.venv/bin/python -m src.indexar_notas
.venv/bin/python -m src.preguntar "¿Ha pasado antes algo parecido a un arranque con el molde frío?"
```

La respuesta debe traer notas con palabras **distintas** a las de la pregunta. Si
solo trae coincidencias literales, revisa que los prefijos `query:`/`passage:` estén
puestos y en el lado correcto.
