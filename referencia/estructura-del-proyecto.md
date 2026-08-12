# Referencia · Estructura del proyecto

> Esto no se lee en voz alta. Es el árbol de archivos que el agente de código tiene
> que crear, fase por fase.
>
> **Construye solo lo que corresponde a la fase que estás haciendo.** Las secciones
> de fases posteriores están acá para que sepas dónde va a encajar cada cosa, no
> para adelantarlas.

---

## Fase 1 — el asistente y su motor de cálculo

```
app.py                      La interfaz: SOLO el chat.
requirements.txt            copia de referencia/requirements.txt
.streamlit/config.toml      copia de referencia/config.toml, tal cual
src/
  config.py                 Los parámetros. Cero cifras de negocio.
  carga.py                  Leer los archivos, recortarlos, y saber qué filas se tocaron.
  calculos.py               LA ÚNICA FUENTE DE CIFRAS.
  trazabilidad.py           El registro de filas consultadas.
  herramientas.py           Las 7 que el asistente puede llamar.
  agente.py                 El modelo, sus instrucciones, y el streaming.
  estilo.py                 La apariencia. Todavía sin colores de gráficos.
  preguntar.py              Las mismas preguntas, por consola. Es el diagnóstico.
pruebas/test_calculos.py    Las comprobaciones sobre los cálculos.
```

Fuera de alcance en la fase 1: gráficos, tablero, filtros y supuestos.

## Fase 2 — el tablero

```
app.py                      SE AMPLÍA: barra lateral, dos pestañas, tablero.
src/
  registro.py               NUEVO. EL CONTRATO.
  estilo.py                 SE AMPLÍA: los colores de datos.
  graficos.py               NUEVO. Los 4 gráficos.
```

---

## Carpetas que ya existen y no se tocan

```
datos/                      Los cinco CSV. Ya generados. No escribas un generador.
referencia/                 Lo que lee el agente. No se modifica.
assets/                     El logo y el favicon.
.env                        Copia de .env.example, con la llave puesta.
```
