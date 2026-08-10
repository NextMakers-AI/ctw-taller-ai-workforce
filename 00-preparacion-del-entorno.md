# Preparación del entorno

**Son cinco minutos y se hace una sola vez.** No instalas nada en tu computador:
el ambiente de trabajo vive en la nube y lo abres desde el navegador.

**No necesitas saber programar.** Ni para esto, ni para el taller.

---

## Lo que vas a abrir

Un **Codespace**: un Visual Studio Code completo dentro del navegador, corriendo
en un servidor de GitHub. Ya trae todo puesto —Python, las librerías, el modelo
de búsqueda y Claude Code— así que no hay nada que descargar ni que instalar.

Es idéntico para los quince asistentes. Si a alguien le funciona, a todos les
funciona.

---

## Paso 1 · Guarda tu llave de API

Te la enviaron por mensaje directo. **Guárdala como secreto de tu cuenta de
GitHub antes de abrir el Codespace** — así queda disponible cada vez que lo
abras, sin volver a pegarla.

1. Entra a **github.com** → tu foto (arriba a la derecha) → **Settings**.
2. En el menú de la izquierda, hasta abajo: **Codespaces**.
3. En **Codespaces secrets**, botón **New secret**.
4. Nombre: `ANTHROPIC_API_KEY` — escrito exactamente así, en mayúsculas.
5. Valor: la llave que te enviaron (empieza por `sk-ant-`).
6. En **Repository access**, marca el repositorio del taller.
7. **Add secret**.

> **Por qué como secreto y no pegándola en la terminal.** Si la pegas en la
> terminal con `export`, funciona para Claude Code en modo texto pero el panel
> gráfico no la ve y te va a pedir iniciar sesión. Como secreto funcionan los
> dos.

Tu llave es solo tuya, es desechable, y se desactiva al terminar el taller.

---

## Paso 2 · Abre el Codespace

1. Entra al repositorio del taller (el enlace te lo enviaron con la llave).
2. Botón verde **Code** → pestaña **Codespaces** → **Create codespace on main**.
3. Espera. La primera vez tarda alrededor de un minuto.

Cuando termine vas a ver Visual Studio Code en el navegador, y abajo un mensaje
que dice:

```
Ambiente listo. Abre 01-fase-1-asistente-conversacional.md para empezar.
```

**Si dice eso, ya está.** No tienes que hacer nada más hasta el día del taller.

---

## Paso 3 · Comprueba que la llave llegó

Una sola cosa, para no descubrirlo en la sala. En la terminal de abajo, escribe:

```bash
claude
```

Claude Code se abre y **te pide aprobar tu llave una vez**. Acepta. Después
escríbele cualquier cosa —«hola, ¿me ves?»— y confirma que responde.

Si respondió, cierra con `/exit`. Ya estás listo.

---

## Si algo sale mal

**«Ambiente casi listo: hay 1 cosa por resolver»** — el mensaje de abajo te dice
cuál. Casi siempre es la llave: vuelve al paso 1 y revisa que el nombre del
secreto esté escrito exactamente `ANTHROPIC_API_KEY`.

**Claude Code me pide iniciar sesión en vez de aprobar la llave** — el secreto no
llegó. Revisa en el paso 1 que marcaste el repositorio del taller en *Repository
access*. Después cierra el Codespace y vuelve a crearlo.

**No encuentro el botón Codespaces** — necesitas estar dentro del repositorio del
taller y con la sesión de GitHub iniciada. Si el botón sigue sin aparecer,
escríbele a quien organiza el taller: puede faltar tu invitación a la
organización.

**Cualquier otra cosa** — descríbela con tus palabras a quien organiza el taller,
**antes del día del taller**. «Se quedó pegado» o «dice algo de un permiso» es
suficiente.

---

## Al terminar cada sesión

Cierra el Codespace cuando termines: **Code** → **Codespaces** → los tres puntos
junto al tuyo → **Stop codespace**. Si se te olvida, se suspende solo por
inactividad, pero conviene tomar la costumbre.

Tu trabajo queda guardado. La próxima vez que lo abras, sigue donde lo dejaste.

---

## Cómo va a funcionar la práctica

Una hora, **tres fases**. Cada una es un archivo de esta carpeta que le pasas a
Claude Code, y cada una **termina en algo que puedes abrir y usar**.

| | Qué construyes | Qué puedes hacer al terminar |
|---|---|---|
| **1** | El asistente, sus cálculos y un chat | Abrirlo en el navegador y ver de dónde sacó cada cifra |
| **2** | El tablero, los filtros y los supuestos | Mover un filtro y ver cambiar el tablero y el chat |
| **3** | Un segundo asistente de otro dominio | Cambiar de asistente, generar un reporte, cargar tu CSV |

Cada fase se apoya en la anterior. **No hace falta que entiendas el código que
escribe**: lo que importa es mirar qué hace y por qué, que es de lo que trata el
taller.
