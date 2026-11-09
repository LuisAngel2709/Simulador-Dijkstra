# Simulador de Dijkstra 

**Versión web 1.15**

Simulador interactivo del algoritmo de Dijkstra diseñado para aprender y comprender cómo se obtiene el camino mínimo en un grafo dirigido y acíclico (DAG).

La aplicación permite crear grafos manualmente o generar ejemplos aleatorios, configurar un origen y un destino, y ejecutar el algoritmo paso a paso. Durante la simulación se visualizan las etiquetas, las actualizaciones de distancias, los vértices seleccionados y los caminos mínimos encontrados.

Es una aplicación web estática desarrollada con **HTML, CSS y JavaScript**, que utiliza SVG para representar los grafos. No necesita un servidor backend ni dependencias durante su ejecución.

## Acceso a la aplicación

**[Abrir Simulador de Dijkstra](https://luisangel2709.github.io/Simulador-Dijkstra/)**

## Características principales

### 1. Creación y edición de grafos

- Generación manual o aleatoria de grafos.
- Compatibilidad con grafos de entre 7 y 16 vértices.
- Creación de aristas dirigidas con pesos entre 1 y 99.
- Edición de pesos directamente sobre el grafo.
- Eliminación de aristas y modificación de la estructura.
- Movimiento de vértices mediante arrastre, conservando sus posiciones.
- Validación de ciclos, aristas duplicadas, bucles y pesos inválidos.
- Advertencias sobre vértices aislados o que no pueden alcanzar el destino.

### 2. Visualización del grafo

- Distribución automática de vértices por niveles.
- Reducción de cruces entre aristas.
- Representación de aristas curvas para mejorar la lectura.
- Pesos visibles en recuadros.
- Identificación de los vértices de origen y destino.
- Visualización de etiquetas del algoritmo con el formato `[d, V]ₙ`.
- Identificación de etiquetas vigentes, empatadas y descartadas.
- Reorganización de etiquetas al mover los vértices.
- Ajuste automático del grafo al área disponible.

También incluye controles para acercar, alejar, desplazar y ajustar la vista del grafo.

### 3. Simulación paso a paso

La aplicación permite seguir el desarrollo del algoritmo de Dijkstra mediante dos subpasos por iteración:

1. Selección del vértice no visitado con la menor distancia conocida.
2. Actualización de las distancias de sus vértices vecinos.

Durante el proceso se puede:

- Avanzar o retroceder entre los pasos.
- Reiniciar la simulación.
- Ir directamente al resultado final.
- Utilizar las flechas del teclado para navegar.
- Consultar la tabla de iteraciones.
- Leer explicaciones sobre las operaciones realizadas.
- Abrir una ventana con información adicional mediante «Más detalles».

Al finalizar, se muestran todos los caminos mínimos encontrados, incluyendo los casos en los que existen varias rutas con la misma distancia.

También se contemplan situaciones especiales, como un destino inalcanzable o cuando el origen y el destino son el mismo vértice.

### 4. Tutorial interactivo

Incluye una guía que acompaña al usuario por las principales secciones de la aplicación:

- Bienvenida y configuración inicial.
- Creación y edición del grafo.
- Selección del origen y destino.
- Desarrollo de la simulación.
- Interpretación de los resultados.

El tutorial utiliza ejemplos calculados con el grafo actual, sin modificar el estado de la simulación.

### 5. Interfaz adaptable

La aplicación incorpora:

- Tema claro y oscuro, con transición visual.
- Conservación de la preferencia de tema.
- Compatibilidad con la configuración de apariencia del sistema.
- Diseño adaptable a diferentes tamaños de pantalla.
- Controles optimizados para pantallas táctiles.

## Compatibilidad con dispositivos móviles

La interfaz adapta su distribución para pantallas pequeñas sin alterar el funcionamiento de la versión de escritorio.

Entre sus características móviles se encuentran:

- Diseño reorganizado para aprovechar el espacio disponible.
- Controles táctiles con áreas de interacción ampliadas.
- Zoom mediante el gesto de pellizco.
- Desplazamiento del grafo con un dedo cuando corresponde.
- Edición de vértices y pesos mediante toques.
- Controles de navegación accesibles.
- Paneles y ventanas adaptados al ancho de la pantalla.

**Pruebas realizadas:** emulación táctil en resoluciones de 390 × 844 y 360 × 640 píxeles, utilizando grafos de 7, 10 y 16 vértices.

> La compatibilidad móvil se ha comprobado mediante emulación en Chromium. Todavía no se ha realizado una validación completa en dispositivos físicos con Safari o Firefox.

## Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| HTML5 | Estructura de la aplicación. |
| CSS3 | Estilos, diseño adaptable y temas. |
| JavaScript (ES Modules) | Lógica de la interfaz y comunicación con el motor. |
| SVG | Representación gráfica de los vértices, aristas y etiquetas. |
| Node.js | Ejecución de pruebas automatizadas. |
| Playwright | Pruebas de interfaz y simulación de interacciones. |

La aplicación no utiliza frameworks de interfaz ni requiere dependencias externas durante su ejecución.

## Arquitectura del proyecto

El proyecto separa el motor del algoritmo de la interfaz gráfica. De esta manera, los cálculos se realizan independientemente de cómo se representan los resultados en pantalla.

```text
simulador_dijkstra_web/
│
├── index.html
├── .nojekyll
├── package.json
├── README.md
├── README_MOTOR.md
│
├── css/
│   └── estilos.css
│
├── src/
│   ├── core/
│   │   └── Motor del algoritmo y gestión del grafo
│   │
│   └── ui/
│       ├── dom.js
│       ├── tema.js
│       ├── layout.js
│       ├── grafo-svg.js
│       ├── tabla.js
│       ├── explicacion.js
│       ├── dialogos.js
│       ├── editor.js
│       ├── simulacion.js
│       ├── pantallas.js
│       ├── tutorial.js
│       ├── tutorial-pasos.js
│       ├── app.js
│       └── main.js
│
├── test/
│   └── Pruebas del motor
│
├── tests_ui/
│   └── Pruebas de interfaz
│
├── golden/
│   └── Casos de referencia
│
└── tools/
    └── Herramientas auxiliares
```

El directorio `src/core/` contiene el motor encargado de gestionar el grafo y calcular los caminos mínimos. El directorio `src/ui/` contiene los módulos responsables de la interacción, visualización y navegación.

El motor JavaScript es una traducción del motor de la versión Python v1.13 y conserva su comportamiento mediante pruebas de comparación.

## Ejecución local

Para ejecutar el simulador en un entorno local, inicia un servidor HTTP desde la carpeta raíz del proyecto:

```bash
python -m http.server 8000
```

Luego accede desde tu navegador a `http://localhost:8000/`.

También puedes utilizar Node.js con el servidor incluido:

```bash
node tools/servir.mjs . 8000
```

> La aplicación utiliza módulos JavaScript ES, por lo que debe ejecutarse mediante un servidor HTTP y no abriendo directamente `index.html`.

## Despliegue

La aplicación está publicada mediante **GitHub Pages**, por lo que puede utilizarse directamente desde el navegador, sin instalaciones ni configuraciones adicionales.

**[Acceder al simulador](https://luisangel2709.github.io/Simulador-Dijkstra/)**

El proyecto también puede desplegarse desde un repositorio propio utilizando GitHub Pages y sus rutas relativas.

## Pruebas y validación

El proyecto cuenta con pruebas automatizadas para verificar el comportamiento del motor y de la interfaz.

| Tipo de prueba | Cantidad | Herramienta |
|---|---:|---|
| Pruebas del motor | 83 | Node.js Test Runner |
| Pruebas de interfaz | 47 | Playwright |
| **Total** | **130** | — |

### Ejecutar las pruebas del motor

No requieren instalar dependencias adicionales:

```bash
npm test
```

### Ejecutar las pruebas de interfaz

Primero instala Playwright y Chromium:

```bash
npm i -D playwright
npx playwright install chromium
```

Después ejecuta:

```bash
npm run test:ui
```

### Ejecutar todas las pruebas

```bash
npm run test:todo
```

Las pruebas verifican, entre otros aspectos:

- Creación y validación de grafos.
- Cálculo de distancias y caminos mínimos.
- Coincidencia con los 32 casos de referencia de Python v1.13.
- Funcionamiento del editor y la simulación.
- Navegación entre iteraciones.
- Temas y tutorial interactivo.
- Solapamientos de elementos gráficos.
- Interacciones táctiles y adaptación móvil.
- Ausencia de errores y advertencias en la consola del navegador.

## Relación con la versión de escritorio

ProyectoMP también cuenta con una versión de escritorio desarrollada en **Python y CustomTkinter**.

Ambas versiones comparten el mismo propósito educativo y la lógica del algoritmo, pero utilizan interfaces y tecnologías diferentes.

| Versión | Tecnologías |
|---|---|
| Web | HTML, CSS, JavaScript y SVG |
| Escritorio | Python y CustomTkinter |

La versión web no utiliza Pyodide ni ejecuta Python en el navegador. Su motor está implementado directamente en JavaScript.

La versión Python es independiente y no se modifica al desarrollar la versión web.

## Documentación adicional

Para conocer con mayor profundidad la implementación y el funcionamiento interno del algoritmo, consulta:

- `README_MOTOR.md`: documentación técnica del motor de Dijkstra.

Autor

Desarrollado por: Luis Angel Vilchez Valencia.
