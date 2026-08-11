# Los cinco archivos que recibiste

Salen de una planta de empaques plásticos que **no tiene SCADA**: todo lo llena
una persona a mano al cierre de cada turno. Están en `datos/` y no hay que
generarlos.

**Léelos siempre con `encoding="utf-8-sig"`, nunca con `utf-8`.** Salen de Excel y
traen BOM: sin eso, el BOM se pega a la primera columna y la vuelve ilegible — el
clásico `KeyError: '﻿fecha'`, con un carácter invisible adelante.

---

## Para el asistente de desperdicio

### `muestras_qc.csv` — 28.236 filas

Pesos pieza por pieza. Es la única fuente que permite cuantificar el material en
exceso que sale dentro de producto conforme.

| Columna | Tipo | Ejemplo |
|---|---|---|
| `fecha` | AAAA-MM-DD | `2026-02-08` |
| `turno` | texto | `mañana`, `tarde`, `noche` |
| `linea` | texto | `L1` |
| `sku` | texto | `ENV-500` |
| `molde` | texto | `M-12` |
| `cavidad` | entero | `2` |
| `lote_resina` | texto | `R-P0001` |
| `peso_g` | decimal | `24.575` |
| `peso_objetivo_g` | decimal | `24.5` |
| `veredicto` | texto | `conforme` / `no conforme` |

> **La tolerancia de inspección de esta planta es asimétrica**: rechaza por debajo
> del 3 % del objetivo, pero acepta hasta un 25 % por encima. Una pieza pesada
> cumple de sobra, pasa la inspección y se despacha. Ese detalle del dominio es la
> razón de que exista material en exceso, que la báscula de rechazos no registra
> porque nada se rechazó.


### `produccion_turno.csv` — 1.137 filas

El cierre de turno.

| Columna | Tipo | Ejemplo |
|---|---|---|
| `planta` | texto | `Envases del Pacífico S.A.S.` |
| `fecha` | AAAA-MM-DD | `2026-02-08` |
| `turno` | texto | `mañana` |
| `linea` | texto | `L1` |
| `sku` | texto | `ENV-500` |
| `lote_resina` | texto | `R-P0001` |
| `kg_consumida` | decimal | `604.89` |
| `kg_scrap` | decimal | `20.26` |
| `unidades_producidas` | entero | `23860` — las conformes |
| `unidades_rechazadas` | entero | `538` |
| `cambios_molde` | entero | `0` |
| `cambios_color` | entero | `0` |
| `paro_no_programado_min` | entero | `0` |
| `arranque_post_mantenimiento` | entero | `0` / `1` |
| `nota_supervisor` | **texto libre** | `sin novedad` |

> **De la columna `planta` sale el nombre que muestra la aplicación.** No lo
> escribas en el código: léelo del archivo, igual que leerías el de una planta
> real.

> **`kg_consumida` incluye la purga**, que es resina que se consume y nunca llega a
> ser pieza. La masa de las piezas no es igual al consumo, y esa diferencia es
> legítima: no la trates como un error del archivo.

> `nota_supervisor` es una de las **dos únicas columnas de texto libre** de todo
> el paquete. Son las únicas que tiene sentido indexar semánticamente.

### `eventos_operacion.csv` — 3.930 filas

HMI y bitácora, con quién firmó cada evento.

`fecha`, `hora`, `turno`, `linea`, `sku`, `origen` (`HMI` / `Bitácora`),
`tipo_evento`, `descripcion` (**texto libre**), `firmado_por`.

---

## Para el asistente de paradas

### `downtime_log.csv` — 1.556 filas

Cada parada no planeada.

| Columna | Tipo | Ejemplo |
|---|---|---|
| `planta` | texto | `Envases del Pacífico S.A.S.` |
| `fecha` | AAAA-MM-DD | `2026-02-08` — **la del calendario** |
| `hora_inicio` | HH:MM | `10:25` |
| `turno` | texto | `mañana` |
| `linea` | texto | `L3` |
| `maquina` | texto | `EMP-06` |
| `duracion_min` | decimal | `22.7` |
| `codigo_falla` | texto | `CAL-02` — **vacío en ~26 % de las filas** |
| `categoria_falla` | texto | `Calidad` — vacío en las mismas |
| `comentario_operario` | **texto libre** | `rebaba persistente, revisión de molde` |

> **La `fecha` es la del calendario, no la del turno.** El turno de noche va de
> 22:00 a 05:59, así que una parada de las 02:00 del sábado está registrada con
> fecha de sábado y turno `noche`, aunque pertenezca al turno que empezó el
> viernes. Derivarlo es trabajo tuyo — y no es un detalle.

> **Una de cada cuatro filas llega sin código de falla**, solo con el comentario
> del operario. Clasificarlas es parte del problema, y el vocabulario para hacerlo
> tiene que salir del propio archivo: cruza las palabras del comentario contra la
> `categoria_falla` de las filas que sí la traen. Adivinar por intuición se
> equivoca.

### `mantenimiento_historico.csv` — 91 filas

`fecha`, `maquina`, `tipo` (`preventivo` / `correctivo`), `duracion_min`,
`descripcion`, `responsable`.

Sirve para saber dónde ya se intentó un preventivo. Si el preventivo se hizo y el
problema sigue, la probabilidad de que funcione esta vez es menor.

---

## Lo que hay dentro de los datos

No son datos planos: tienen patrones puestos a propósito, y encontrarlos es el
trabajo. **No están anotados en ninguna parte del archivo** — se descubren
calculando.

Lo que sí conviene saber, porque condiciona el método:

- Hay **líneas que se comportan distinto entre sí**, y no todas por la misma razón.
- Hay **lotes de resina con muy pocos turnos**. Un lote con 4 turnos no sostiene
  una acusación por más que su promedio se vea mal.
- Hay **un turno claramente fuera de norma**, tan extremo que arrastra cualquier
  media y desviación estándar que lo incluya.
- Hay **notas escritas por personas distintas que describen el mismo problema con
  palabras completamente distintas**, sin una sola palabra en común.
- Las condiciones que explican el scrap **se solapan**: un mismo turno puede tener
  cambio de color y paro no programado, y cuenta en los dos.
