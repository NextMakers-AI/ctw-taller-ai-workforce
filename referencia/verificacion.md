# Referencia · Verificación de cada fase

> Esto no se lee en voz alta. Son las comprobaciones que el agente de código tiene
> que correr al cerrar cada fase, con la salida real a la vista.
>
> **Corre la sección de la fase que estás haciendo, entera, y pega la salida.** No
> declares una comprobación superada sin haberla ejecutado.

---

## Fase 1

### Qué tienen que comprobar las pruebas

Sin librería de pruebas: un guion que imprime `[PASA]`/`[FALLA]` y sale con código
distinto de cero si algo falla.

No comprueban que el código corra: comprueban que recupere los patrones que hay en
los datos. Como mínimo:

- Los dos tipos de desperdicio existen, se suman sin superponerse, y el desglose por
  línea+SKU reconstruye el total.
- Solo se cuentan muestras conformes, y ningún delta medio es negativo.
- Se detecta la línea que se desgasta y la que está descalibrada.
- La descalibración se juzga por el punto de partida, no por el promedio: comprueba
  que la línea que se desgasta tiene el promedio más alto y aun así no se clasifica
  como descalibrada.
- El costo del desgaste está escalado a un mes completo.
- Los lotes con evidencia superan el mínimo; los descartados vienen con su `n`.
- Los porcentajes de categoría pasan del 100 % y hay advertencia.
- El método robusto de detección de anomalías encuentra el turno más extremo.
- El recorte por filtros afecta a todos los archivos de forma coherente.

Si una prueba falla, lee la cifra que imprime antes de cambiar nada.

### Por consola, que es donde se diagnostica

```bash
.venv/bin/python -m pruebas.test_calculos
.venv/bin/python -m src.preguntar "¿Cuánto material estamos desperdiciando y de qué tipo es?"
```

Lo que tiene que verse:

1. Todas las comprobaciones marcadas `[PASA]`.
2. El agente llamando herramientas, una línea por invocación.
3. El bloque de trazabilidad al final.
4. Las filas analizadas no superan el total de filas de los archivos. Si lo superan,
   estás sumando conteos en vez de unir conjuntos: `muestras_qc.csv` tiene 28.236
   filas y `produccion_turno.csv` 1.137, así que ningún bloque puede decir más de
   33.303 en total.

### En la interfaz

```bash
.venv/bin/streamlit run app.py --server.port 8501
```

1. Abre en modo oscuro, sin importar cómo esté configurado el sistema operativo. Sin
   excepción en pantalla y sin trazas en consola al arrancar.
2. **La página no tiene barra de desplazamiento propia.** Mira el borde derecho del
   navegador: la única barra que puede aparecer es la de la conversación, dentro de
   la caja. Si la página entera se desplaza, sube `--alto-fuera-del-chat`.
3. **El campo de entrada está pegado al pie de la caja**, no flotando en la mitad, y
   mide una línea de alto cuando está vacío.
4. El alto de la caja **no cambia** cuando el agente empieza a responder.
5. **Las cuatro sugerencias caben en una o dos filas**, con los botones del ancho de
   su texto. Si cada una ocupa el ancho completo y hay huecos verticales entre
   ellas, el contenedor quedó vertical.
6. Clic en una sugerencia → la pregunta se envía automáticamente y aparecen los dos
   mensajes.
7. La burbuja de la pregunta va a la derecha y el texto queda dentro del fondo de
   color, sin sobresalir por abajo.
8. **Haz una pregunta con respuesta larga y no toques el scroll**: la conversación
   baja sola a medida que el agente escribe, y al terminar se ve el final de la
   respuesta. Mientras responde, el botón de enviar es un botón de **detener** y no
   se puede escribir.
9. Una respuesta larga con tablas no obliga a desplazarse en horizontal. Las tablas
   anchas se desplazan **dentro de su propio recuadro**.
10. En una ventana ancha, los mensajes quedan centrados con un ancho máximo de
    lectura, no estirados de borde a borde.
11. Se ve el nombre de la herramienta mientras corre, y el bloque de trazabilidad al
    final: el mismo que imprimió la consola, con las mismas cifras.
12. Ningún texto oscuro sobre fondo oscuro ni blanco sobre blanco, tampoco al pasar
    el mouse sobre un botón.
13. Pon `TEMA=claro` en el `.env` y comprueba que la hoja de estilos propia cambia.
    Los controles nativos no van a cambiar: eso confirma que el tema se configura en
    dos lugares y hay que cambiar los dos. Vuelve a dejarlo en `oscuro`.

---

## Fase 2

```bash
.venv/bin/python -c "
from src import registro, carga, estilo
import re
for m in (False, True):
    c = estilo.css(m)
    assert not re.findall(r'\{[a-z_\[\]\047\"]+\}', c), 'marcador sin resolver'
    assert 'var(--' not in c, 'quedó un var(--x) que Streamlit no expone'
print('css resuelto en los dos modos, sin var(--x)')
d = carga.cargar()
a = registro.por_clave('desperdicio')
for g in a.graficos:
    ch, res = g.fn(d, a.parametros[0].valor)
    ch.to_dict()
    assert g.pie(res), f'pie vacío en {g.titulo}'
    print(f'  {g.titulo}: ok')
"
grep -rn "groupby" app.py src/graficos.py
.venv/bin/streamlit run app.py --server.port 8501
```

El `grep` no debería devolver ninguna cifra de negocio.

Con la app corriendo (arranca en oscuro, y así se queda):

1. Las dos pestañas abren sin excepción y sin trazas en consola al arrancar.
2. El chat sigue funcionando igual que en la fase 1 ahora que está dentro de una
   pestaña: la caja llega al pie, su alto no cambia al empezar a responder, las
   sugerencias envían la pregunta, la burbuja va a la derecha con el texto dentro
   del fondo, y una respuesta larga con tablas no obliga a desplazarse en
   horizontal.
3. Ningún indicador de variación en verde con flecha bajo las métricas; ningún
   número de métrica cortado.
4. Los cuatro gráficos con su pie, sin etiquetas de eje recortadas.
5. Recargar en `?agente=desperdicio&tab=tablero` deja la app donde estaba.
6. Pon un filtro de línea y pregunta: el bloque de trazabilidad del chat tiene que
   bajar de filas. Es la prueba de que el filtro llegó al agente y no solo al
   tablero.

---

## Fase 3

### El hallazgo de la fecha del turno

Córrelo al terminar el segundo asistente, antes de seguir con las pestañas:

```bash
.venv/bin/python -c "
from src.paras import carga, calculos
d = carga.cargar()
r = calculos.distribucion_turno(d, 2_000_000)
print(r['_mapa'].sort_values('horas', ascending=False).head(3))
"
```

La celda más alta tiene que ser una sola combinación día × turno. Si el pico aparece
repartido entre dos días contiguos, la fecha del turno no se está aplicando.

### Al cerrar la fase

```bash
.venv/bin/python -m pruebas.test_calculos
.venv/bin/python -m src.preguntar
.venv/bin/python -m src.paras.preguntar
```

Y sobre un reporte descargado:

```python
assert pdf[:5] == b'%PDF-'                                 # es un PDF de verdad
assert len(re.findall(rb'/Subtype\s*/Image', pdf)) == 4    # 4 en desperdicio, 6 en paradas
assert html.count('<svg') == 4                             # y el HTML también
assert 'Trazabilidad' in html and 'Filas analizadas' in html
assert '**' not in html                                    # sin markdown crudo
assert not re.search(r'https?://(?!www\.w3\.org)', html)   # sin CDN externo
```

### En la aplicación, para cada agente

| # | Qué | Cómo se ve que está bien |
|---|---|---|
| 1 | Las cuatro pestañas abren | Sin excepción en pantalla |
| 2 | Contraste | La app arranca en oscuro; ningún texto oscuro sobre oscuro, tampoco al pasar el mouse |
| 3 | Filtros | Cambiar de asistente y volver: siguen puestos |
| 4 | Recarga | F5 en `?agente=paras&tab=tablero` deja la app donde estaba |
| 5 | Sugerencias | Al hacer clic, envían la pregunta |
| 6 | Chat | Sin desplazamiento horizontal; el texto dentro de su burbuja |
| 7 | Datos | Sube un CSV sin una columna obligatoria → mensaje que nombra la columna |
| 8 | Reporte | Descarga en PDF, A4, 6 gráficas, una hoja por gráfica |
| 9 | Consola | Sin trazas al arrancar |

### Autorrevisión antes de dar por terminado

Repasa esta lista y reporta lo que no cumplas en vez de dejarlo pasar:

- [ ] ¿Hay algún `groupby` fuera de los módulos de cálculo?
- [ ] ¿Hay alguna cifra de negocio escrita a mano en el código?
- [ ] ¿Hay alguna fecha o nombre de planta escrito a mano?
- [ ] ¿El bloque de trazabilidad lo arma el código, y suma por unión de conjuntos?
- [ ] ¿Los pies de los gráficos se recalculan del dato, o hay prosa que afirma algo
      que dejaría de ser cierto con otro archivo?
- [ ] ¿La herramienta de notas devuelve o insinúa alguna cifra de negocio?
- [ ] ¿Todos los textos están en español neutro, sin voseo?
- [ ] ¿Hay algún `var(--x)` de CSS esperando una variable que Streamlit no expone?
- [ ] ¿Algún fallo del modelo puede dejar inservible la interfaz o el reporte?
- [ ] ¿`app.py` cambió para agregar el segundo asistente? Si sí, el contrato quedó
      incompleto.
