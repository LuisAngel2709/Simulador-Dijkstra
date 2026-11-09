# Simulador educativo del algoritmo de Dijkstra

Aplicación de escritorio (Python + CustomTkinter) para aprender el problema del
camino mínimo sobre **grafos dirigidos acíclicos** con pesos enteros positivos.
No solo calcula la respuesta: muestra, paso a paso, cómo se etiquetan los
vértices, por qué se elige cada uno y cuáles son **todos** los caminos mínimos.

La terminología sigue la *Lectura 5: Algoritmo de Dijkstra* (Matemática
computacional, UPC): cada vértice recibe una etiqueta `[d, V]ₙ` con la distancia
acumulada `d`, el vértice predecesor `V` y el número de iteración `n`.

## Requisitos

- Python 3.10 o superior, con Tkinter incluido (en Linux: `sudo apt install python3-tk`)
- CustomTkinter

```bash
pip install -r requirements.txt
```

La interfaz usa las fuentes *Segoe UI* y *Consolas* (presentes en Windows). En
otros sistemas se sustituyen automáticamente por una fuente disponible.

## Ejecución

Desde la carpeta del proyecto:

```bash
python main.py
```

## Pruebas

```bash
python -m unittest discover -s tests -t .
```

La suite tiene 290 pruebas (144 requieren pantalla y se omiten sin ella). Las del Core (grafo, Dijkstra, caminos, snapshots,
generador) no necesitan interfaz. Las de la interfaz (`test_layout.py` en su parte
de arrastre y `test_navegacion.py`) abren ventanas reales y requieren un entorno
gráfico; en un Linux sin pantalla se ejecutan con `xvfb-run -a python -m unittest
discover -s tests -t .`.

## Simulación: explicaciones, desplazamiento y «Más detalles»

- Cada paso tiene una explicación breve en el panel (qué hace, por qué, qué observar) y otra extendida en la ventana **Más detalles**, no modal, que se actualiza al cambiar de paso y se cierra con Esc. Ambas se calculan en `core/explicaciones.py` a partir de los snapshots del motor; no repiten la lógica de Dijkstra.
- La página se desplaza con la rueda cuando el contenido no cabe; la barra de navegación queda fija. La tabla y los cuadros de texto con desbordamiento se desplazan por sí solos (Mayús + rueda: horizontal).
- El grafo marca ORIGEN y DESTINO sobre los nodos elegidos, y el encabezado muestra «Camino mínimo: A → B» y el estado de la ejecución.

## Modo tutorial

El botón **? Tutorial** del encabezado (siempre visible, junto al selector de tema) inicia un recorrido guiado de la pantalla en la que estés: bienvenida, configuración, editor y simulación (16 pasos: 11 de interfaz y 5 sobre cómo funciona Dijkstra). Cada paso resalta el elemento explicado con un contorno de color y muestra una tarjeta junto a él con «Paso n de N», «Anterior», «Siguiente» y «Salir». Se puede repetir las veces que se quiera.

- No toca la aplicación: no ejecuta, reinicia ni avanza la simulación, no abre «Más detalles» y no modifica el grafo. Se puede seguir editando o simulando mientras está abierto; cambiar de pantalla lo cierra.
- Los ejemplos «En tu grafo» salen del motor (`core/tutorial_algoritmo.py` lee el resultado de la simulación en curso, o uno calculado aparte, y reutiliza `core/explicaciones.py`).
- Tk no permite oscurecer parcialmente widgets hijos, así que la atención se dirige con el contorno y la tarjeta, sin velo.
- Código: `ui/tutorial.py` (motor), `ui/tutorial_pasos.py` (contenido de cada pantalla).

## Tema claro / oscuro

El botón luna/sol del encabezado (esquina superior derecha, fuera de las pantallas) alterna el tema al instante sin reconstruir la pantalla: la simulación, el grafo, la tabla y la selección se conservan. Los colores de `ui/theme.py` son pares `(claro, oscuro)`; CustomTkinter los cambia con `set_appearance_mode()` y solo el canvas y la tabla (Tk puro) se repintan con `theme.resolver()`.

## Uso

1. **Bienvenida**: pulse *Empezar simulación*.
2. **Configuración**: elija el número de nodos (7 a 16) y cómo crear el grafo:
   *Generar automáticamente* o *Crear manualmente*.
3. **Editor manual** (solo en modo manual):
   - Haga clic en el vértice de origen y luego en el de destino; escriba el peso
     (entero de 1 a 99) y pulse *Crear conexión*.
   - Las conexiones que cerrarían un ciclo, las duplicadas y los pesos inválidos se
     rechazan con un mensaje explicativo; el grafo anterior se conserva.
   - Arrastre los nodos para ubicarlos a su gusto; *Restablecer* los devuelve a la
     distribución circular inicial.
   - En la lista de aristas puede cambiar un peso o eliminar una conexión.
   - *Finalizar grafo* pasa a la simulación.
4. **Simulación**: elija origen y destino, pulse *Ejecutar Dijkstra* y avance con
   *Siguiente* / *Anterior*. También puede usar *Reiniciar* o *Ir al final*. Cada
   iteración tiene dos subpasos: **selección** del vértice no visitado con menor
   distancia acumulada y **actualización** de las etiquetas de sus vecinos. La
   tabla del proceso (que puede ocultar) y el cuadro de explicación siempre
   corresponden al paso que está viendo. Los nodos también se pueden arrastrar.
5. **Resultado**: al llegar al final se muestran la distancia mínima, la cantidad
   de caminos mínimos y todas las rutas, resaltadas en el grafo.
6. **Volver**: el botón superior izquierdo depende de cómo creó el grafo.
   - Grafo **manual**: *← Editar grafo* regresa al editor con el mismo grafo y los
     nodos donde los dejó, para corregirlo o ampliarlo y volver a simular.
   - Grafo **aleatorio**: *← Configuración* regresa a la pantalla de configuración
     (no hay nada que editar).

### Colores del grafo

| Color | Significado |
|---|---|
| Verde claro | Vértice origen |
| Rosa | Vértice destino |
| Amarillo | Vértice seleccionado en el paso actual |
| Azul claro | Vértice ya visitado |
| Ámbar / naranja | Arista que se evalúa / arista que produce un empate |
| Verde intenso | Arista de un camino mínimo (en el resultado final) |

Las etiquetas descartadas aparecen tachadas en la tabla, y cuando hay empate el
vértice muestra una etiqueta por cada predecesor.

## Decisiones de diseño

- **Predecesores múltiples**: si una distancia nueva es estrictamente menor se
  reemplazan los predecesores; si es igual se agrega uno más. Así se conservan
  todos los caminos mínimos.
- **Empates de selección**: se resuelven por orden alfabético; esto afecta al orden
  de procesamiento, no a los caminos encontrados.
- **Fin del algoritmo**: no se detiene al seleccionar el destino, sino al procesar
  todos los vértices alcanzables, para no perder predecesores de igual distancia.
- **Snapshots**: cada paso es un estado inmutable. *Anterior* muestra el snapshot
  previo; nunca "deshace" operaciones.
- **Generación aleatoria**: el DAG se construye sobre capas explícitas, con pocas
  aristas que salten capas y grados de entrada y salida acotados. Los pesos se
  sortean entre 1 y 9 para que el grafo sea legible; el editor admite de 1 a 99.
  Entre varios candidatos se prefiere uno con más de un camino mínimo.
- **Layout**: los grafos aleatorios parten de una distribución por capas con
  reducción de cruces (mediana); los manuales, de una distribución circular. En
  ambos casos los nodos se pueden mover a mano y su posición se conserva.

## Estructura

```
main.py                  punto de entrada
core/graph.py            grafo dirigido, validaciones y detección de ciclos
core/dijkstra_engine.py  algoritmo, predecesores múltiples, snapshots, caminos
core/generator.py        generación aleatoria de DAG por capas
ui/app.py                ventana principal, bienvenida, configuración y navegación
ui/editor.py             editor manual del grafo
ui/simulation.py         simulación paso a paso
ui/graph_canvas.py       layout por capas, arrastre de nodos y dibujo del grafo
ui/table.py              tabla del proceso de etiquetación
ui/rueda.py              enrutador único de la rueda del ratón (por posición del puntero)
ui/pagina_desplazable.py contenido de la simulación con desplazamiento vertical
ui/texto_rico.py         texto con estilos para las explicaciones
ui/detalles.py           ventana secundaria «Más detalles»
core/explicaciones.py    explicaciones de cada paso, derivadas de los snapshots
core/golden.py            exporta los casos de oro (golden/dijkstra_golden.json) para comparar con la versión web
core/tutorial_algoritmo.py  ejemplos reales del motor para el tutorial
core/extremos.py            origen/destino sugeridos y análisis de vértices aislados/inalcanzables
ui/tutorial.py           motor del tutorial (resalte, tarjeta, navegación)
ui/tutorial_pasos.py     pasos del tutorial de cada pantalla
ui/theme.py              colores y fuentes
ui/boton_tema.py         botón luna/sol del encabezado (tema claro/oscuro)
tests/                   pruebas (unittest): tema, grafo, Dijkstra, caminos, snapshots,
                         generador y layout, y navegación entre pantallas
```

El paquete `core` no importa CustomTkinter: el algoritmo es independiente de la
interfaz y puede ejecutarse o probarse por separado.

## Mejoras del editor (v1.11)

- **Origen y destino automáticos**: con una sola fuente y un solo sumidero se eligen solos; con varias opciones se propone una pareja válida y se puede cambiar. Tu selección manual se respeta al volver al editor y simular de nuevo (se olvida al crear otro grafo).
- **Validación al finalizar**: avisa de vértices aislados, de vértices que el origen no alcanza y de un destino inalcanzable; permite «Continuar de todos modos» o «Volver al editor».
- **Editar pesos con clic**: clic sobre el número de una arista abre un campo; Enter confirma, Esc cancela. Actualiza el gráfico y el panel lateral al instante.
- **Origen = destino**: Dijkstra termina de inmediato tras etiquetar el origen (solo 2 pasos: inicio y resultado). Distancia 0, camino mínimo formado solo por ese vértice, sin selecciones ni actualizaciones, con mensaje explicativo; la tabla muestra solo la iteración 0.

## Preparación para la versión web (v1.13)

- **Casos de oro**: `golden/dijkstra_golden.json` contiene 32 grafos con todo lo que produce el motor (resultado, cada snapshot con su tabla, etiquetas y explicaciones, ejemplos del tutorial, extremos sugeridos y advertencias), más casos de validación y de truncamiento. Se regenera con `python -m core.golden` (desde esta carpeta). `∞` se escribe `null`. `tests/test_golden.py` comprueba que el motor actual lo reproduce exactamente; la versión web debe hacer lo mismo.
- **Validación estricta**: pesos y número de nodos solo aceptan dígitos ASCII (`0-9`), con espacios ASCII alrededor tolerados. Se rechazan `+5`, `1_0`, dígitos Unicode (`٣`, `５`), `1e1`, etc. Rangos sin cambios (nodos 7–16, pesos 1–99).
- **Una sola fuente de explicaciones**: los textos se construyen únicamente en `core/explicaciones.py`; `Snapshot` ya no guarda textos (`explicacion` se eliminó), solo datos.
- **Truncamiento**: `truncado` solo es verdadero si existen más caminos mínimos que el límite (500). Con exactamente 500 no se trunca. Cubierto con 499, 500 y 501 caminos en `tests/test_truncamiento.py`.
