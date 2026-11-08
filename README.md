# Simulador de Dijkstra — versión web (ProyectoMP v1.15)

Aplicación web **estática** (HTML + CSS + JavaScript + SVG), sin servidor, sin Pyodide, sin Flet y sin
dependencias en tiempo de ejecución. Reutiliza el motor `src/core/` (traducción exacta de `core/` de Python v1.13);
la interfaz solo dibuja lo que el motor calcula. La versión Python/CustomTkinter (`../simulador_dijkstra/`) no se toca.

## Ejecutarla en local

Los módulos ES no se cargan con doble clic (`file://`); basta cualquier servidor estático:

```bash
cd simulador_dijkstra_web
python -m http.server 8000      # o:  node tools/servir.mjs . 8000
# abrir http://localhost:8000/
```

## Publicarla en GitHub Pages

* Opción A: sube esta carpeta como raíz del repositorio y en *Settings → Pages* elige «Deploy from a branch» (`/ (root)`).
* Opción B: usa el flujo `.github/workflows/pages.yml` de este proyecto (publica la carpeta `simulador_dijkstra_web/`
  con *Settings → Pages → Source: GitHub Actions*).

Todas las rutas son relativas y hay un `.nojekyll`, así que funciona también en `https://usuario.github.io/repo/`.

## Qué incluye

| Área | Implementación |
| --- | --- |
| Editor | Clic en origen y destino para crear aristas; peso 1–99 con Enter; edición del peso en línea (clic sobre el número); botones Peso/Eliminar; arrastre de vértices con posiciones conservadas; «Restablecer» en círculo; rechazo de ciclos, duplicados, bucles y pesos inválidos (lo hace el motor); advertencias de vértices aislados / inalcanzables antes de simular |
| Vista | El grafo se ajusta solo al área disponible (también al redimensionar); botón «Ajustar grafo» (icono de maximizar) en el lienzo; zoom con la rueda y desplazamiento arrastrando el fondo, siempre dentro del lienzo (el grafo nunca sale del todo de la vista); doble clic en el fondo también ajusta |
| Grafo SVG | Capas de izquierda a derecha con reducción de cruces, aristas curvas que esquivan vértices, pesos en recuadro, marcas ORIGEN/DESTINO, etiquetas `[d, V]ₙ` y etiquetas descartadas tachadas, colocadas **sin solaparse** (hasta 16 vértices) y recolocadas al arrastrar |
| Simulación | Los dos subpasos por iteración, Siguiente/Anterior/Reiniciar/Ir al final, flechas del teclado, tabla del proceso (vigente/empate/descartada), explicación breve y ventana «Más detalles», resultado con todos los caminos mínimos, origen = destino y destino inalcanzable |
| Tutorial | Guía interactiva por pantalla (bienvenida, configuración, editor, simulación) con foco resaltado, textos de v1.13 y ejemplos reales calculados con tu grafo sin alterar la simulación |
| UX | Tema claro/oscuro con transición (recuerda la elección y respeta el del sistema); diseño responsive con prioridad en escritorio y adaptación a celulares (ver abajo) |

## Celulares y pantallas táctiles

Con el ancho de un celular (probado en 390×844 y 360×640, con 7, 10 y 16 vértices) la interfaz cambia así; en
escritorio todo sigue como antes.

* **Legibilidad:** en pantallas estrechas el grafo no se encoge hasta que el texto sea ilegible. La vista inicial usa una
  escala mínima de 0,65 (etiquetas y pesos de unos 8,5 px); si el grafo no cabe a esa escala se ve la parte izquierda
  y el resto se alcanza arrastrando o con zoom. «Ajustar grafo» siempre muestra el grafo completo.
* **Gestos en el lienzo:** pellizco con dos dedos para acercar o alejar; un dedo desplaza el grafo cuando está ampliado o
  recortado, y arrastra el vértice que se toca (editor); con el grafo completo a la vista, un dedo en vertical
  desplaza la página con normalidad. Zonas de toque ampliadas en vértices y pesos (el peso reacciona en un área de al menos 44 px aunque su recuadro mida ~10 px; un toque con temblor sigue siendo un toque y un arrastre desde un peso desplaza el grafo). En el campo del peso en línea, la tecla «Siguiente» del teclado numérico del celular confirma el peso (en escritorio, Enter).
* **Controles:** botones de al menos 44 px, selectores a 16 px (evita el zoom automático de iOS), cabecera no fija y barra
  de navegación de una sola fila con Reiniciar, Ir al final y la tabla como iconos (con nombre accesible).
* **Paneles:** «Más detalles» ocupa el ancho de la pantalla y la tarjeta del tutorial se limita al área visible.

Límites conocidos: solo se ha probado con Chromium (emulación táctil), no con Safari ni Firefox en un celular real; en el
editor de un celular el grafo parte recortado (usa «Ajustar grafo» para verlo entero); en el tutorial la tarjeta puede
tapar parte del elemento resaltado cuando este ocupa casi toda la pantalla.

## Estructura

```
index.html  css/estilos.css  .nojekyll
src/core/   motor (sin cambios respecto a v1.14)
src/ui/     dom.js  tema.js  layout.js (puro)  grafo-svg.js  tabla.js  explicacion.js  dialogos.js
            editor.js  simulacion.js  pantallas.js  tutorial.js  tutorial-pasos.js  app.js  main.js
test/       83 pruebas del motor (node --test, sin dependencias)
tests_ui/   47 pruebas de interfaz (Playwright + Chromium)
```

## Pruebas

```bash
npm test          # 83 pruebas del motor, incluye los 32 casos de oro de Python (no necesita instalar nada)
npm run test:ui   # 47 pruebas de interfaz; requiere Playwright:  npm i -D playwright && npx playwright install chromium
npm run test:todo # ambas
```

Las pruebas de interfaz recorren los flujos del editor y la simulación, vigilan la consola del navegador (cualquier
error o aviso hace fallar la prueba), comprueban temas y tutorial, miden solapes en pantalla con grafos de 7 a 16
vértices y comparan **paso a paso** (título, explicación, tabla y colores de aristas) lo que muestra la pantalla con
los 32 casos de oro de Python v1.13. Las pruebas móviles emulan un celular táctil (390×844 y 360×640) y envían gestos reales de uno y dos dedos.

Documentación del motor: `README_MOTOR.md`.
