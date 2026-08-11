# Referencia · Notas de implementación del motor

> **Esto no se lee en voz alta.** Son las decisiones técnicas que el agente de
> código tiene que respetar. Cada una está acá porque algo falló antes y costó
> encontrarlo.
>
> Se usa desde la fase 1 y sigue valiendo en las fases 2 y 3.

---

## Leer los CSV

Siempre con **`encoding="utf-8-sig"`**, nunca `utf-8`. Los archivos salen de Excel
y traen BOM: sin eso, el carácter invisible se pega a la primera columna y produce
el clásico `KeyError: '﻿fecha'`.

## La configuración

Un dataclass **congelado** que lee todo del entorno. Ni un valor de negocio
escrito en el código:

```python
proveedor            = os.getenv("PROVEEDOR_LLM", "bedrock").strip().lower()
modelo_bedrock       = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-sonnet-5")
modelo_anthropic     = os.getenv("ANTHROPIC_MODEL_ID", "claude-sonnet-5")
region_aws           = os.getenv("AWS_REGION", "us-east-1")

precio_resina_usd_kg = float(os.getenv("PRECIO_RESINA_USD_KG", "1.85"))
tolerancia_peso_g    = float(os.getenv("TOLERANCIA_PESO_G", "0.15"))
umbral_deriva_g_dia  = float(os.getenv("UMBRAL_DERIVA_G_DIA", "0.01"))
min_turnos_lote      = int(os.getenv("MIN_TURNOS_LOTE", "10"))
umbral_z_anomalia    = float(os.getenv("UMBRAL_Z_ANOMALIA", "3.5"))
```

## Los datos en memoria

`Datos` es un dataclass **congelado** con los marcos ya tipados:

- `desde_marcos(marcos)` — construye desde diccionarios de DataFrame. Es lo que
  después permite mezclar archivos cargados con los de disco.
- `cargar()` — desde los CSV.
- `filtrar(**filtros)` — devuelve otro `Datos` recortando **todos los archivos de
  forma coherente**. Es fácil recortar las muestras y no la producción, y de ahí
  salen cocientes absurdos: los kilos de toda la planta divididos entre las piezas
  de una sola línea.
- `validar()` — mensajes accionables, no trazas.
- `marcos()` — vuelve a diccionarios.
- `traza(*fuentes)` — **devuelve los índices de las filas tocadas, no el conteo.**

**`filtrar()` no reindexa.** Los índices originales son los que viajan, porque el
registro de trazabilidad tiene que poder *unir* lo que tocaron varias herramientas
sin contar dos veces las mismas filas. Con conteos es imposible; con conjuntos de
índices es trivial.

Deriva a nivel de fila, no como agregado: el `delta_g` de cada pieza contra su
objetivo y el `pct_scrap` de cada turno.

El **nombre de la planta sale de la columna `planta`**, nunca del código.

## Los cálculos

Cada función devuelve un **diccionario**, no un DataFrame. Las claves que empiezan
por `_` son para el código —series, mapas, índices de trazabilidad— y se filtran
antes de mandarle nada al modelo.

Toda función que haga un supuesto o tenga una limitación devuelve una de estas
claves: `advertencia`, `aviso`, `nota_metodo`, `nota_conservadora`.

> **Dos funciones que miden lo mismo tienen que cuadrar, y hay que comprobarlo.**
> `serie_costo_acumulado` y `calcular_desperdicio` son funciones **distintas** que
> miden lo mismo: el final de la curva tiene que ser el total.
>
> Que la curva **reutilice** el delta por línea+SKU que ya calculó
> `calcular_desperdicio` en vez de rehacerlo, y que ese delta viaje **sin
> redondear** en una clave `_`. Sumar las cifras ya redondeadas de cada
> combinación desplaza el total y aparece una diferencia. Deja un `assert`: la
> diferencia tiene que ser 0,00.

## La trazabilidad

```python
class Registro:
    def anotar(self, herramienta, traza):
        # UNIÓN DE CONJUNTOS de índices, no suma de conteos
        for fuente, indices in (traza.get("filas") or {}).items():
            self._filas.setdefault(fuente, set()).update(int(i) for i in indices)
```

El bloque en markdown **lo arma el código** y se pega al final de la respuesta:

```
---
**Trazabilidad** *(generada por el código, no por el modelo)*
Rango consultado: **2026-02-08 → 2026-08-06**
Filas analizadas: **29.373** — 1.137 cierres · 28.236 muestras
Precio de resina aplicado: **1.85 USD/kg**
Herramientas ejecutadas: `calcular_desperdicio`, `atribuir_categorias`
```

`limpiar_para_modelo(resultado)` quita las claves con `_` antes de mandar nada al
modelo: son series y arreglos de índices que gastarían miles de tokens y además lo
tentarían a sumar a mano justo lo que las herramientas ya sumaron bien.

**El registro es de una respuesta, no de la sesión.** `configurar()` lo limpia, y
por eso vive a nivel de módulo y no dentro del contexto. **Cada pregunta
reconfigura**: si `configurar()` se llama una sola vez al arrancar, el bloque de la
cuarta pregunta lista las herramientas y las filas de las cuatro — exactamente el
número inflado que este bloque viene a evitar.

## Las herramientas

Con el decorador `@tool` de `strands`, que **saca el esquema del docstring y de las
anotaciones de tipo**. El docstring no es documentación: es la interfaz que el
modelo lee para decidir cuándo llamarla. Escríbelo pensando en eso.

Todas devuelven `dict`, todas anotan la traza, y ninguna calcula: cada una llama al
módulo de cálculo.

El modelo **no elige el recorte de datos ni el precio**: eso lo fija `configurar()`
desde fuera, y las herramientas reciben siempre la vista ya preparada.

## El modelo

`MAX_TOKENS = 16_384`, y no 4.096. Con 4.096 el chat funciona bien, pero el reporte
de la fase 3 se corta a mitad de frase con `MaxTokensReachedException`. No es la
ventana de contexto sino el **tope de escritura**.

A los modelos Claude recientes **no** se les pasa `temperature` ni `top_p`: los
rechazan.

El identificador cambia según por dónde se llegue:

- Claude API directa → `claude-sonnet-5` (**sin** prefijo)
- Amazon Bedrock → `anthropic.claude-sonnet-5` (el prefijo es de Bedrock)

```python
def crear_modelo():
    if CONFIG.proveedor == "anthropic":
        from strands.models.anthropic import AnthropicModel
        llave = os.getenv("ANTHROPIC_API_KEY")
        if not llave:
            raise RuntimeError(
                "PROVEEDOR_LLM=anthropic pero no hay ANTHROPIC_API_KEY en el "
                "entorno. Ponla en el .env (que está en .gitignore)."
            )
        return AnthropicModel(
            client_args={"api_key": llave},
            model_id=CONFIG.modelo_anthropic,
            max_tokens=MAX_TOKENS,
        )
    from strands.models import BedrockModel
    return BedrockModel(
        model_id=CONFIG.modelo_bedrock,
        region_name=CONFIG.region_aws,
        max_tokens=MAX_TOKENS,
    )
```

### `callback_handler=None` no es opcional

```python
Agent(model=..., tools=..., system_prompt=..., callback_handler=None)
```

Por omisión `Agent` instala un manejador que va imprimiendo la respuesta a stdout
por su cuenta. Como el texto se consume por `stream_async`, dejarlo activo hace que
cada trozo salga **dos veces**.

### El puente de streaming async → sync

`stream_async` es asíncrono y ni la consola ni Streamlit lo son. Un hilo aparte con
una `queue.Queue` y un centinela de fin. **Se escribe una sola vez y lo usan los
dos**: la consola y el chat consumen exactamente el mismo generador.

Formas de evento verificadas contra el código de `strands`:

- texto → `{"data": "trozo de texto"}`
- herramienta → `{"current_tool_use": {"toolUseId": ..., "name": ...}}`

`current_tool_use` **se repite en cada delta** mientras se arman los argumentos.
Emítelo una sola vez por invocación, recordando el último `toolUseId` visto.

Emite dos clases de evento: `{"tipo": "herramienta"}` y `{"tipo": "texto"}`.
