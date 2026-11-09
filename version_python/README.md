# Simulador educativo del algoritmo de Dijkstra

Aplicación de escritorio desarrollada en **Python y CustomTkinter** para aprender el problema del camino mínimo sobre grafos dirigidos acíclicos con pesos enteros positivos.

El simulador no solo calcula la solución: permite observar paso a paso cómo se etiquetan los vértices, por qué se selecciona cada uno y cómo se determinan todos los caminos mínimos.

La terminología sigue la *Lectura 5: Algoritmo de Dijkstra* (Matemática Computacional, UPC). Cada vértice recibe una etiqueta `[d, V]ₙ`, donde `d` representa la distancia acumulada, `V` el vértice predecesor y `n` el número de iteración.

## Versiones disponibles

- **Versión web:** [Abrir simulador](https://luisangel2709.github.io/Simulador-Dijkstra/)
- **Versión de escritorio:** Python + CustomTkinter (esta versión).

## Características principales

- **Creación de grafos:** permite generar grafos aleatorios o construirlos manualmente.
- **Editor interactivo:** permite crear, eliminar y modificar conexiones, así como mover los vértices libremente.
- **Simulación paso a paso:** muestra las etapas de selección y actualización del algoritmo de Dijkstra.
- **Visualización de etiquetas:** representa las distancias acumuladas y los vértices predecesores.
- **Múltiples caminos mínimos:** identifica y muestra todas las rutas que alcanzan la distancia mínima, incluyendo los casos de empate.
- **Tabla de iteraciones:** permite consultar los cambios producidos en cada etapa de la ejecución.
- **Explicaciones didácticas:** proporciona explicaciones breves y detalladas sobre cada paso.
- **Modo tutorial:** ofrece un recorrido guiado por las pantallas de la aplicación y explica el funcionamiento del algoritmo.
- **Tema claro y oscuro:** permite alternar entre ambos temas sin perder el estado de la simulación.
- **Navegación por pasos:** permite avanzar, retroceder, reiniciar o ir directamente al resultado final.

## Requisitos

- Python 3.10 o superior.
- Tkinter.
- CustomTkinter.

En Linux, si Tkinter no está instalado, puede instalarse mediante:

```bash
sudo apt install python3-tk
```

## Instalación y ejecución

1. Descarga el proyecto desde este repositorio.
2. Extrae los archivos y abre una terminal en la carpeta del proyecto.
3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. Ejecuta la aplicación:

```bash
python main.py
```

La interfaz utiliza las fuentes Segoe UI y Consolas, disponibles normalmente en Windows. En otros sistemas se sustituyen por fuentes disponibles.

## Funcionamiento de la aplicación

### 1. Bienvenida

Desde la pantalla inicial se puede comenzar una nueva simulación.

### 2. Configuración

Selecciona la cantidad de vértices, entre 7 y 16, y elige cómo construir el grafo:

- **Generar automáticamente:** crea un grafo dirigido acíclico con pesos positivos.
- **Crear manualmente:** permite diseñar el grafo mediante el editor.

### 3. Editor manual

En el modo manual se pueden realizar las siguientes acciones:

- Seleccionar un vértice de origen y otro de destino para crear una conexión.
- Asignar un peso entero entre 1 y 99.
- Mover los vértices para organizar visualmente el grafo.
- Modificar el peso de una conexión haciendo clic sobre su etiqueta.
- Eliminar conexiones existentes.
- Restablecer la distribución inicial de los vértices.

El editor valida las conexiones y rechaza aquellas que producirían ciclos, duplicados o pesos inválidos, mostrando mensajes explicativos.

Al finalizar, se realiza una validación del grafo que identifica vértices aislados, vértices inaccesibles desde el origen y destinos inalcanzables. El usuario puede continuar o regresar al editor para realizar modificaciones.

### 4. Simulación de Dijkstra

Una vez configurado el grafo, se seleccionan el origen y el destino y se inicia la ejecución.

Cada iteración se divide en dos subpasos:

1. **Selección:** se elige el vértice no visitado con la menor distancia acumulada.
2. **Actualización:** se revisan sus vecinos y se actualizan sus etiquetas cuando se encuentra una distancia menor o un camino alternativo de igual longitud.

La simulación permite avanzar y retroceder entre los pasos, reiniciar el proceso o ir directamente al resultado final.

La tabla de iteraciones y las explicaciones se actualizan de acuerdo con el paso seleccionado.

### 5. Resultado

Al finalizar se muestran:

- La distancia mínima entre el origen y el destino.
- La cantidad de caminos mínimos encontrados.
- Todas las rutas que alcanzan esa distancia.
- Las aristas correspondientes a los caminos mínimos resaltadas en el grafo.

### 6. Funcionalidades adicionales

- **Selección automática de extremos:** el simulador propone automáticamente el origen y el destino según la estructura del grafo. Si existen varias opciones, permite modificarlos manualmente.
- **Validación del grafo:** identifica vértices aislados, inaccesibles y destinos que no pueden alcanzarse desde el origen.
- **Edición de conexiones:** permite modificar pesos y eliminar conexiones sin reconstruir el grafo.
- **Conservación del grafo:** al regresar desde la simulación al editor manual se mantiene la estructura y la posición de los vértices.
- **Origen igual a destino:** contempla este caso especial, mostrando una distancia mínima de 0 y un camino formado únicamente por el vértice seleccionado.

## Explicaciones y modo tutorial

### Explicaciones de la simulación

Cada paso cuenta con una explicación breve en el panel principal y una explicación extendida disponible mediante la ventana **Más detalles**.

Esta última se actualiza al cambiar de paso y puede cerrarse con la tecla `Esc`.

### Modo tutorial

El botón **? Tutorial** permite realizar un recorrido guiado por las distintas pantallas de la aplicación:

- Bienvenida.
- Configuración.
- Editor.
- Simulación.

El recorrido contiene 16 pasos: 11 relacionados con la interfaz y 5 dedicados al funcionamiento de Dijkstra.

Cada paso resalta el elemento correspondiente y presenta una tarjeta con instrucciones y controles de navegación.

El tutorial no modifica el grafo ni altera el estado de la simulación.

## Tema claro y oscuro

La aplicación permite alternar entre ambos temas mediante el botón ubicado en el encabezado.

El cambio se realiza sin reconstruir la pantalla, por lo que se conservan el grafo, la tabla, la selección y el estado actual de la simulación.

## Colores del grafo

| Color | Significado |
|---|---|
| Verde claro | Vértice de origen |
| Rosa | Vértice de destino |
| Amarillo | Vértice seleccionado en el paso actual |
| Azul claro | Vértice visitado |
| Ámbar / naranja | Arista que se evalúa o produce un empate |
| Verde intenso | Arista perteneciente a un camino mínimo |

Las etiquetas descartadas aparecen tachadas en la tabla. Cuando existen varios predecesores con la misma distancia mínima, se muestran todos en la etiqueta del vértice.

## Decisiones de diseño del algoritmo

- **Predecesores múltiples:** cuando se encuentra una distancia estrictamente menor, se reemplazan los predecesores anteriores. Si la distancia es igual, se agrega el nuevo predecesor para conservar todos los caminos mínimos.
- **Empates de selección:** se resuelven mediante orden alfabético. Esto determina el orden de procesamiento, pero no elimina caminos mínimos.
- **Finalización del algoritmo:** no se detiene al seleccionar el destino, sino que procesa todos los vértices alcanzables para no perder posibles predecesores de igual distancia.
- **Snapshots:** cada paso de la simulación representa un estado inmutable. La navegación hacia atrás muestra un estado anterior sin deshacer operaciones.
- **Generación aleatoria:** construye grafos dirigidos acíclicos mediante capas, procurando reducir cruces y mantener una distribución visual legible.
- **Validación:** se aceptan entre 7 y 16 vértices y pesos enteros entre 1 y 99.

## Estructura del proyecto

```text
version-python/
│
├── main.py
├── requirements.txt
│
├── core/
│   ├── graph.py
│   ├── dijkstra_engine.py
│   ├── generator.py
│   ├── explicaciones.py
│   ├── extremos.py
│   ├── tutorial_algoritmo.py
│   └── ...
│
├── ui/
│   ├── app.py
│   ├── editor.py
│   ├── simulation.py
│   ├── graph_canvas.py
│   ├── table.py
│   ├── theme.py
│   ├── tutorial.py
│   └── ...
│
├── tests/
│   └── ...
│
└── golden/
    └── dijkstra_golden.json
```

### Arquitectura

El proyecto separa la lógica del algoritmo de la interfaz gráfica.

El paquete `core` contiene las estructuras del grafo, las validaciones, el motor de Dijkstra, la generación aleatoria y las explicaciones. No depende de CustomTkinter.

El paquete `ui` contiene las ventanas, los componentes visuales, el editor, la simulación y los elementos de navegación.

Esta separación permite probar la lógica del algoritmo independientemente de la interfaz.

## Pruebas

El proyecto cuenta con una suite de pruebas automatizadas mediante `unittest`.

Para ejecutarlas:

```bash
python -m unittest discover -s tests -t .
```

La suite documentada contiene 290 pruebas. Algunas requieren un entorno gráfico para abrir ventanas reales, mientras que las pruebas del núcleo pueden ejecutarse sin interfaz.

En Linux, las pruebas que necesitan pantalla pueden ejecutarse mediante Xvfb:

```bash
xvfb-run -a python -m unittest discover -s tests -t .
```

## Autor

Desarrollado por: **[Nombre del autor]**.
