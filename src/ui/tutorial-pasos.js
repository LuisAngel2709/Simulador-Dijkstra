/**
 * Contenido del tutorial: los pasos de cada pantalla (textos de la versión Python v1.13).
 * Cada paso solo referencia elementos que la pantalla ya tiene; ninguno ejecuta acciones.
 * Los ejemplos de «Cómo funciona Dijkstra» salen de `ejemplosAlgoritmo` (motor), calculados con
 * el grafo actual sin tocar la simulación en curso.
 */

import { NODOS_MAXIMO, NODOS_MINIMO, ejecutarDijkstra, ejemplosAlgoritmo } from "../core/index.js";

const INTERFAZ = "Interfaz";
const ALGORITMO = "Cómo funciona Dijkstra";
const NOTA_EJEMPLO = "\n(Calculado con tu grafo; no modifica tu simulación.)";

export function pasosBienvenida(p, cab) {
  return [
    { titulo: "Bienvenido al simulador", seccion: "Inicio", objetivo: () => p.tarjeta,
      texto: "Esta aplicación te enseña cómo el algoritmo de Dijkstra encuentra el camino más corto entre dos vértices de un grafo, paso a paso. Primero construyes o generas un grafo y después lo simulas." },
    { titulo: "Empezar", seccion: "Inicio", objetivo: () => p.boton_empezar, texto: "Este botón te lleva a la configuración del grafo." },
    { titulo: "Tutorial y tema", seccion: "Inicio", objetivo: () => [cab.botonTutorial, cab.botonTema],
      texto: "«Tutorial» repite este recorrido en la pantalla donde estés: cada pantalla tiene su propia guía. El botón de la luna o el sol cambia entre tema claro y oscuro sin perder tu trabajo." },
  ];
}

export function pasosConfiguracion(p) {
  return [
    { titulo: "Configura tu grafo", seccion: "Configuración", objetivo: () => p.tarjeta,
      texto: "Aquí decides cuántos vértices tendrá el grafo y cómo quieres crearlo. Después podrás simularlo." },
    { titulo: "Número de vértices", seccion: "Configuración", objetivo: () => p.marco_nodos,
      texto: `Elige cuántos vértices tendrá el grafo, entre ${NODOS_MINIMO} y ${NODOS_MAXIMO}. Se nombran con letras: A, B, C…` },
    { titulo: "Generar automáticamente", seccion: "Configuración", objetivo: () => p.tarjeta_auto,
      texto: "Crea un grafo dirigido sin ciclos con pesos pensados para aprender y pasa directamente a la simulación, con un origen y un destino sugeridos." },
    { titulo: "Crear manualmente", seccion: "Configuración", objetivo: () => p.tarjeta_manual,
      texto: "Abre un editor donde tú dibujas las conexiones y eliges sus pesos. Es la mejor opción para probar tus propios ejemplos." },
  ];
}

export function pasosEditor(p) {
  return [
    { titulo: "El área de construcción", seccion: "Editor", objetivo: () => p.canvas,
      texto: "Los vértices ya están dibujados. Arrástralos para ubicarlos donde quieras. Para conectar dos, haz clic en el vértice de origen y luego en el de destino: la flecha irá de uno al otro." },
    { titulo: "Peso de la conexión", seccion: "Editor", objetivo: () => [p.etiqueta_seleccion, p.fila_peso, p.fila_botones],
      texto: "Con origen y destino elegidos, escribe un peso entero de 1 a 99 y pulsa Enter o «Crear conexión». «Cancelar» (o Esc) anula la selección. El editor no admite ciclos, bucles ni conexiones repetidas, y te avisa si lo intentas." },
    { titulo: "Aristas del grafo", seccion: "Editor", objetivo: () => p.lista_aristas,
      texto: "Aquí aparece cada conexión creada. Con «Peso» cambias su valor y con «Eliminar» la quitas. También puedes hacer clic sobre el número de una flecha en el grafo y escribir el peso ahí mismo (Enter confirma, Esc cancela)." },
    { titulo: "Restablecer posiciones", seccion: "Editor", objetivo: () => p.boton_restablecer,
      texto: "Si arrastraste los vértices y quedaron enredados, este botón los vuelve a colocar en círculo. No cambia las conexiones." },
    { titulo: "Finalizar el grafo", seccion: "Editor", objetivo: () => p.boton_finalizar_grafo,
      texto: "Cuando el grafo esté listo (con al menos una conexión), este botón pasa a la simulación. Si hay vértices aislados o el destino no se puede alcanzar, te avisa antes y puedes continuar o volver al editor. Desde la simulación podrás volver sin perder lo construido." },
  ];
}

export function pasosSimulacion(p) {
  const cache = {};
  /** Resultado del motor, de solo lectura: el de la simulación o uno calculado aparte. */
  const ejemplos = () => {
    const origen = p.origen;
    const destino = p.destino;
    let resultado = p.resultado;
    if (!resultado) {
      if (cache.clave !== `${origen}>${destino}`) {
        cache.clave = `${origen}>${destino}`;
        cache.resultado = ejecutarDijkstra(p.grafo, origen, destino);
        cache.ej = null;
      }
      resultado = cache.resultado;
    }
    if (cache.ejDe !== resultado) {
      cache.ejDe = resultado;
      cache.ej = ejemplosAlgoritmo(p.grafo, resultado);
    }
    return cache.ej;
  };
  const volver = p.textoVolver === "← Editar grafo"
    ? "Vuelve al editor con tu grafo, para añadir, cambiar o quitar conexiones sin perder las posiciones de los vértices."
    : "Vuelve a la configuración, donde puedes generar otro grafo automáticamente o crearlo a mano en el editor. Si el grafo tiene conexiones te pedirá confirmación antes de descartarlo.";
  const expl = () => [p.titulo_paso, p.fila_subpaso, p.texto_explicacion];
  const res = () => [p.etiqueta_resultado, p.texto_resultado];
  return [
    { titulo: "Bienvenido a la simulación", seccion: INTERFAZ, objetivo: () => p.barra_superior,
      texto: "Aquí verás cómo Dijkstra calcula el camino mínimo, un paso cada vez. Este recorrido explica cada zona de la pantalla y, al final, los conceptos del algoritmo. No cambia tu grafo ni tu simulación, y puedes salir cuando quieras." },
    { titulo: "El grafo", seccion: INTERFAZ, objetivo: () => p.lienzo,
      texto: "Cada círculo es un vértice y cada flecha una conexión dirigida: solo se puede avanzar en el sentido de la flecha. Puedes arrastrar los vértices para verlos mejor." },
    { titulo: "Crear o generar otro grafo", seccion: INTERFAZ, objetivo: () => p.boton_volver, texto: volver },
    { titulo: "Origen y destino", seccion: INTERFAZ, objetivo: () => p.marco_extremos,
      texto: "Elige desde qué vértice parte el camino y a cuál quieres llegar (al empezar se propone una pareja válida, que puedes cambiar). Aparecen marcados como ORIGEN y DESTINO sobre el grafo y en el encabezado. Si los cambias, hay que volver a ejecutar la simulación." },
    { titulo: "Etiquetas, pesos y conexiones", seccion: INTERFAZ, objetivo: () => [p.lienzo, p.marco_leyenda],
      texto: "• El número en un recuadro sobre cada flecha es su peso.\n" +
        "• [d, V]ₙ es la etiqueta de un vértice: d = distancia acumulada desde el origen, V = vértice anterior (predecesor), n = iteración en que se asignó. [∞, -] significa que aún no se llegó a él.\n" +
        "• La leyenda explica los colores: en los vértices, verde = origen, rosa = destino, amarillo = actual y azul = visitado; en las flechas, ámbar = arista evaluada, naranja = empate y verde = camino mínimo. Una flecha roja es una arista evaluada que no mejora la distancia (no aparece en la leyenda)." },
    { titulo: "Iniciar la simulación", seccion: INTERFAZ, objetivo: () => p.boton_ejecutar,
      texto: "«Ejecutar Dijkstra» calcula el algoritmo y muestra su primer paso. Si ya hay una simulación en curso, volver a pulsarlo la empieza de nuevo; por eso el tutorial no lo pulsa por ti." },
    { titulo: "Avanzar y retroceder", seccion: INTERFAZ, objetivo: () => p.barra_navegacion,
      texto: "«Siguiente» y «Anterior» recorren la simulación subpaso a subpaso (también las flechas del teclado). «Reiniciar» vuelve al primer paso e «Ir al final» salta al resultado. Retroceder no recalcula nada: revisa pasos ya calculados. El último botón muestra u oculta la tabla." },
    { titulo: "Tabla del proceso", seccion: INTERFAZ, objetivo: () => p.tabla,
      texto: "Una fila por vértice y una columna por iteración. Cada celda guarda la etiqueta [d, V] que el vértice recibió en esa iteración: verde = vigente, amarillo = empate, gris = descartada." },
    { titulo: "Explicación de cada paso", seccion: INTERFAZ, objetivo: expl,
      texto: "Este cuadro cuenta qué hace el algoritmo en el paso actual: qué vértice examina, qué aristas considera, cómo calcula cada distancia nueva y por qué una etiqueta se actualiza, se conserva o se descarta. Cambia sola al avanzar o retroceder." },
    { titulo: "Más detalles", seccion: INTERFAZ, objetivo: () => p.boton_detalles,
      texto: "Abre una ventana aparte con el razonamiento ampliado, la lectura de la etiqueta y el estado de todos los vértices. No bloquea la aplicación: se actualiza sola al cambiar de paso y se cierra con su botón o con Esc. Se activa al ejecutar la simulación." },
    { titulo: "Resultado", seccion: INTERFAZ, objetivo: res,
      texto: "Al terminar muestra la distancia mínima y los caminos mínimos entre origen y destino (varios si hay empates), o avisa de que el destino no se puede alcanzar. Con «Ir al final» lo ves al instante." },
    { titulo: "Distancias provisionales", seccion: ALGORITMO, objetivo: () => p.lienzo,
      texto: "Dijkstra guarda, para cada vértice, la mejor distancia conocida hasta ahora desde el origen. Empieza con 0 en el origen y ∞ en los demás. Mientras un vértice no se selecciona, su distancia es provisional: todavía puede mejorar.",
      ejemplo: () => ejemplos().provisionales + NOTA_EJEMPLO },
    { titulo: "Elegir el vértice de menor distancia", seccion: ALGORITMO, objetivo: expl,
      texto: "Cada iteración empieza con la Selección: entre los vértices aún no visitados se elige el de menor distancia provisional. Como los pesos son positivos, esa distancia ya no puede mejorar: se vuelve definitiva y el vértice pasa a visitado (azul).",
      ejemplo: () => ejemplos().seleccion + NOTA_EJEMPLO },
    { titulo: "Actualizar etiquetas y predecesores", seccion: ALGORITMO, objetivo: () => p.lienzo,
      texto: "Después viene la Actualización: se miran las aristas que salen del vértice elegido y se calcula distancia nueva = d(elegido) + peso. Si es menor que la etiqueta del vecino, la reemplaza (la anterior se tacha) y su predecesor pasa a ser el vértice elegido.",
      ejemplo: () => ejemplos().actualizacion + NOTA_EJEMPLO },
    { titulo: "Empates", seccion: ALGORITMO, objetivo: () => p.tabla,
      texto: "Si la distancia nueva es igual a la que ya tenía el vecino, hay un empate: se conserva la distancia y se añade otro predecesor, para no perder ningún camino mínimo. En el grafo la arista se pinta de naranja y en la tabla la celda de amarillo.",
      ejemplo: () => ejemplos().empates + NOTA_EJEMPLO },
    { titulo: "Reconstruir el camino mínimo", seccion: ALGORITMO, objetivo: res,
      texto: "Cuando no quedan vértices alcanzables por visitar, se parte del destino y se siguen los predecesores hacia atrás hasta el origen. Si un vértice tiene varios predecesores, cada uno da un camino mínimo distinto; todos se resaltan en verde.",
      ejemplo: () => ejemplos().camino + NOTA_EJEMPLO },
  ];
}
