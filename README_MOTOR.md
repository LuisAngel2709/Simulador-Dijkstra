# Motor JavaScript del simulador de Dijkstra (etapa 1 de la migración web)

Traducción de `core/` de **ProyectoMP v1.13** (Python) a JavaScript puro: módulos ES, **sin dependencias**,
sin Pyodide ni Flet, sin navegador ni interfaz. La versión Python/CustomTkinter (`../simulador_dijkstra/`)
no se modifica; es la fuente de verdad.

## Módulos (`src/core/`)

| JavaScript | Python de origen | Contenido |
| --- | --- | --- |
| `graph.js` | `graph.py` | `Grafo` (DAG), `GrafoError`, validación estricta (`validarPeso`, `validarNumeroNodos`), detección de ciclos, orden topológico |
| `engine.js` | `dijkstra_engine.py` | `MotorDijkstra`, `Snapshot` (inmutables), `EntradaTabla`, `ResultadoDijkstra`, `Simulacion`, `reconstruirCaminos`, `textoEtiqueta` |
| `explicaciones.js` | `explicaciones.py` | `explicar()`: explicación breve y extendida de cada snapshot (única fuente de textos) |
| `extremos.js` | `extremos.py` | `sugerirExtremos`, `analizar`, `mensajeAdvertencia`, fuentes/sumideros/aislados |
| `generador.js` | `generator.py` | `generarDag`, `generarDagDidactico` |
| `azar.js` | `random.Random` de CPython | Mersenne Twister y `random`, `randint`, `choice`, `shuffle` **idénticos a Python**: misma semilla ⇒ mismo grafo |
| `tutorial.js` | `tutorial_algoritmo.py` | `ejemplosAlgoritmo` |
| `golden.js` | `golden.py` | serialización de casos y regeneración del golden |

Uso: `import { Grafo, ejecutarDijkstra, explicar } from "./src/core/index.js"`.
Convenciones: nombres en camelCase (`aristasEvaluadas`); `∞` es `Infinity` (en el JSON del golden, `null`).

## Pruebas

```
npm test        # o: node --test        (Node 18 o superior; sin instalar nada)
```

* `test/golden.test.js` — los **32 casos de oro** (`golden/dijkstra_golden.json`, copia del de Python):
  grafo, resultado, cada snapshot (distancias, predecesores, visitados, aristas, tabla, etiquetas),
  explicaciones breve y extendida, ejemplos del tutorial, extremos y advertencias; además
  `construirGolden()` en JS debe ser **idéntico** al archivo de Python (incluye los grafos generados
  con semilla, validación y truncamiento 499/500/501).
* `test/equivalencia_amplia.test.js` — 720 casos más (generados por Python, comparados por hash SHA-256 de
  toda la serialización), los 240 grafos de semilla y 1 200 validaciones aleatorias.
  El fixture se regenera con `python tools/generar_equivalencia_amplia.py` (solo importa el motor Python).
* `test/grafo|motor|extremos|generador|textos.test.js` — comportamiento: ciclos, duplicados, desempates,
  empates, inalcanzables, origen = destino, inmutabilidad, navegación, truncamiento, azar, textos.

## Limitaciones pendientes

* Falta toda la interfaz web (diseño, canvas/SVG, tutorial visual, temas).
* Probado con Node 22; no se ejecutó en navegadores ni en Node 18/20.
* `random` de Python solo se replica para enteros pequeños, y los métodos usados por el generador.
