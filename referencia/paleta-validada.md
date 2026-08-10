# Paleta validada — valores y números de verificación

Todo lo de este archivo está **medido**, no elegido de vista. Cópialo tal cual: si
cambias un hex, la verificación deja de valer y hay que rehacerla completa.

## El color de marca

| | |
|---|---|
| Naranja del logo | **#EB652B** |
| Origen | 66 % de los píxeles opacos de `assets/next-makers-log.png` |
| Luminosidad OKLCH | L = 0,666 · C = 0,180 · H = 41° |
| Banda clara (0,43–0,77) | dentro |
| Banda oscura (0,48–0,67) | dentro |

Que caiga en las dos bandas es lo que permite usar **el mismo naranja en los dos
modos**, sin tener que elegir un segundo.

## Contraste del primario

| Combinación | Contraste | Veredicto |
|---|---|---|
| Blanco sobre #EB652B | 3,27:1 | **insuficiente para texto** |
| #1C0A02 sobre #EB652B | 5,88:1 | ok para texto |
| #C13D00 sobre blanco (enlace claro) | 5,34:1 | ok |
| #FA7A48 sobre #09090B (enlace oscuro) | 7,52:1 | ok |

Por eso los botones primarios llevan **letra oscura**, y los enlaces no usan el
naranja del logo tal cual.

## Paleta categórica — seis colores

```
SERIES_CLARO  = #EB652B  #A43650  #069FF9  #E35EBD  #40C68B  #7756DC
SERIES_OSCURO = #EB652B  #AB2440  #1E8FEE  #D551B1  #00A66D  #7546CA
```

Verificada en modo **todos los pares** (no solo adyacentes):

| Modo | Banda | Croma | Peor par CVD | Visión normal | Contraste |
|---|---|---|---|---|---|
| claro | pasa | pasa | **ΔE 10,6** (objetivo ≥8) | **ΔE 18,5** (piso 15) | aviso en 2 tonos |
| oscuro | pasa | pasa | **ΔE 9,3** | **ΔE 18,5** | aviso en 1 tono |

El aviso de contraste bajo 3:1 obliga a un relevo, que está: leyenda siempre
presente, etiquetas directas sobre las barras, tooltips y la pestaña «Datos» con la
tabla completa. Nunca se depende del color solo.

### Por qué seis y no ocho

Con ocho tonos falla en oscuro: la banda es angosta (L 0,48–0,67) y ocho colores ahí
se pisan. El peor caso medido fue **ámbar contra naranja a ΔE 0,5 bajo
deuteranopía** — el mismo color. También hubo dos verdes a ΔE 3,3 para visión
normal.

### Paletas rechazadas, con su motivo

| Paleta | Por qué se descartó |
|---|---|
| shadcn `--chart-1..5` | ΔE 4,7 deutan entre slots 4 y 5; tres cálidos análogos; uno lee gris |
| Cálida de 5 tonos (H 15–85°) | Visión normal ΔE 14,8 — bajo el piso de 15 |
| Cálida de 6 tonos (H 15–85°) | Visión normal ΔE 13,6 |
| Apagada anclada al naranja | Pasa raspando (ΔE 8,8) y sale olivo/vino/malva: no armoniza |

## Rampa secuencial — seis pasos discretos

```
SECUENCIAL_CLARO  = #E6A188 #DB8261 #CF6136 #C13D00 #9F2E00 #7C2400
SECUENCIAL_OSCURO = #79371D #9D431E #C24E1C #E45E24 #FA7A48 #FF9B73
```

Como escala **ordinal**, los dos modos pasan todo:

| Comprobación | claro | oscuro |
|---|---|---|
| Luminosidad monótona | pasa | pasa |
| Salto mínimo entre pasos (≥0,06) | pasa | pasa |
| Extremo vecino a la superficie (≥2:1) | 2,14:1 | 2,25:1 |
| Un solo tono | 3° | 2° |

Como escala **de identidad** con seis pasos: **ΔE 7,8**, bajo el piso de 15. Por eso
`escala_calida` con cuatro o más categorías exige etiquetas directas.

Con **tres** categorías, usando los índices **0, 2 y 5**: ΔE 16,2 en los dos modos —
ahí sí identifica por color.

## Rampa para `chartSequentialColors` — DIEZ pasos

Streamlit exige exactamente diez; con menos descarta la lista entera y cae a sus
colores por defecto sin más aviso que una línea en el log.

```
#E5A48C #DD9276 #D58060 #CC6E4A #C5592E #BE4200 #B22D00 #9E2200 #881F00 #731A00
```

Son puntos de interpolación de un degradado continuo, no bins discretos: no se les
exige la separación mínima entre pasos vecinos. Verificado lo que sí aplica —
luminosidad monótona, un solo tono, extremo a 2,10:1 de la superficie.

## Los cinco criterios, para revalidar si algo cambia

1. Luminosidad OKLCH dentro de la banda del modo — clara 0,43–0,77, oscura 0,48–0,67
2. Croma ≥ 0,1 (ningún color que lea gris)
3. Separación CVD ≥ 8 en protanopía, deuteranopía y tritanopía (6–8 solo con
   codificación secundaria)
4. Separación para visión normal ≥ 15 — **fallo duro, no advertencia**
5. Contraste ≥ 3:1 contra la superficie (por debajo, obliga a etiquetas o tabla)

Para escalas ordinales, en vez de 3 y 4: luminosidad monótona, salto ≥ 0,06 entre
pasos vecinos, un solo tono, y el extremo vecino a la superficie ≥ 2:1.
