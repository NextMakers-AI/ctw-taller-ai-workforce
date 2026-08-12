# Asistentes de planta — taller práctico

Vas a construir **dos asistentes de IA** que responden preguntas sobre los datos
de una planta de empaques plásticos que no tiene SCADA: todo entra a mano, en
archivos que alguien llena al cierre de cada turno.

No es un chatbot sobre documentos. Es un asistente en el que **cada cifra que dice
sale de una función de cálculo**, y al final de cada respuesta el código —no el
modelo— escribe cuántas filas de datos usó para calcularla.

---

## Antes de empezar

Abre **`00-preparacion-del-entorno.md`** y pega en Claude Code el texto que trae. Él
deja el computador listo: instala lo que falte, descarga el modelo y comprueba que
todo quedó bien.

**No necesitas saber programar**, ni acá ni en el resto del taller. Son unos 15
minutos, casi todos de descargas, y **no caben en la hora de práctica**: si pasan
en vivo con la wifi del venue, se comen la mitad de la sesión.

---

## Cómo funciona la práctica

Una hora, **tres fases**. Cada archivo se pega entero en tu agente de código
—Claude Code, Cursor— y cada uno **termina en algo que puedes abrir y usar**.

| | Archivo | Qué construyes | Qué puedes hacer al terminar |
|---|---|---|---|
| **1** | `01-fase-1-asistente-conversacional.md` | El asistente, sus cálculos y un chat en el navegador | Abrirlo, preguntarle y ver de dónde sacó cada cifra |
| **2** | `02-fase-2-tablero-analitico.md` | El tablero: seis gráficos, filtros y supuestos | Mover un filtro o un supuesto y ver cambiar el tablero **y** el chat |
| **3** | `03-fase-3-plataforma-multidominio.md` | Un segundo asistente de otro dominio | Cambiar de asistente, generar un reporte, cargar tu CSV |

Cada fase se apoya en la anterior, en el mismo proyecto y con el mismo agente
de código abierto.

**Si la hora se acaba en la 2, lo que tienes es una aplicación completa y honesta
de un asistente.** La 3 es la que se puede cortar — está ordenada por dentro para
que lo que falte sea lo menos valioso.

---

## Los datos ya están

En `datos/`. **No los generes**: son cinco CSV que salen de la planta y llegan como
llegan, con sus columnas vacías y sus notas escritas a mano.

Su esquema completo —columna por columna, con lo que hay que saber de cada una—
está en **`referencia/esquema-de-datos.md`**. Vale la pena leerlo antes de la
fase 1.

Dentro hay patrones puestos a propósito, y encontrarlos es el trabajo. **No están
anotados en ninguna parte del archivo.**

---

## Qué hay en esta carpeta

```
00-preparacion-del-entorno.md      Preparación. Hazlo antes.
01-fase-1-….md         ─┐
02-fase-2-….md          ├─ los tres que se pegan
03-fase-3-….md         ─┘

datos/                      Los cinco CSV. Ya están.
referencia/                 Lo que lee el agente, no tú.
  esquema-de-datos.md       Las columnas de los cinco archivos.
  estructura-del-proyecto.md  El árbol de archivos, fase por fase.
  implementacion.md         Las decisiones técnicas del motor.
  interfaz.md               Cómo se dibuja la pantalla.
  requirements.txt          Versiones fijadas. Se copia tal cual.
  config.toml               Tema nativo de Streamlit. Se copia tal cual.
  paleta-validada.md        Los hex con sus números de verificación.
  verificacion.md           Las comprobaciones al cerrar cada fase.
assets/                     El logo y el favicon.
.env.example                Se copia a .env y se le pone la llave.

referencia-detallada/       OPCIONAL. Ver abajo.
```

### Sobre `referencia-detallada/`

Son diecinueve archivos que desarrollan cada tema con mucho más detalle del que
cabe en tres fases: la arquitectura pieza por pieza, el sistema visual
completo, las trampas de Altair y de Streamlit una por una, cómo se generaron los
datos.

**No hacen falta para el taller.** Los tres archivos de fase son
autocontenidos: no los mencionan, no dependen de ellos y **puedes borrar esa
carpeta entera sin que nada se rompa**.

Están para después, si quieres seguir por tu cuenta.

---

## Las reglas que atraviesan todo

1. **Todo en español neutro** — el código, los comentarios, los nombres de
   variable y la interfaz.
2. **Toda cifra que el asistente diga sale de una herramienta.** El modelo no
   suma, no promedia, no estima. Si falta un dato, dice que no lo sabe.
3. **El bloque de trazabilidad lo arma el código, no el modelo**, y cuenta las
   filas por unión de conjuntos.
4. **Los gráficos y el chat usan las mismas funciones de cálculo.** Si el tablero
   dijera una cifra y el agente otra para la misma pregunta, se acabó la
   credibilidad de todo lo demás.
5. **Ningún número del negocio escrito a mano en el código.** Ni fechas, ni
   umbrales, ni nombres de planta: todo sale de los datos o del `.env`.
6. **Nunca inventes que verificaste algo.** Si un archivo dice «verifica X», corre
   el comando y mira la salida real.

---

## Una advertencia sobre el `.env`

Los umbrales de `.env.example` —`MIN_TURNOS_LOTE`, `TOLERANCIA_PESO_G`,
`UMBRAL_Z_ANOMALIA`— **tienen que coincidir con los que se usaron al generar los
datos**. Los patrones están sembrados justo por encima de ellos.

Moverlos es un ejercicio interesante —sube `MIN_TURNOS_LOTE` a 25 y mira cómo el
asistente deja de acusar al lote sospechoso, correctamente— pero acuérdate de
volver a los valores del ejemplo.
