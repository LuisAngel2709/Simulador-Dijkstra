/**
 * Ejemplos reales para la parte «Cómo funciona Dijkstra» del tutorial.
 * Traducción de core/tutorial_algoritmo.py.
 *
 * No ejecuta ni reimplementa el algoritmo: recibe el `ResultadoDijkstra` ya calculado y escoge
 * los momentos de esa ejecución que ilustran cada concepto. Todo texto sale de los snapshots y
 * de `explicaciones.js`. Es una función pura.
 */

import { ACTUALIZACION, INFINITO, SELECCION, formatoDistancia } from "./engine.js";
import { CALCULO, TITULO, explicar } from "./explicaciones.js";

/** Bloques que siguen al encabezado `titulo` hasta el siguiente encabezado. */
function _seccion(bloques, titulo) {
  const salida = [];
  let dentro = false;
  for (const b of bloques) {
    if (b.estilo === TITULO) {
      if (dentro) break;
      dentro = b.texto === titulo;
    } else if (dentro) {
      salida.push(b);
    }
  }
  return salida;
}

/** Pares «fórmula + qué ocurrió» de la sección Cálculos de una actualización. */
function _calculos(bloques) {
  return _seccion(bloques, "Cálculos").map((b) => (b.estilo === CALCULO ? b.texto : b.texto.trim()));
}

function _conTresAristas(lineas) {
  // Cada arista ocupa dos líneas (fórmula y explicación): se muestran como máximo tres.
  const resto = Math.floor(lineas.length / 2) - 3;
  const texto = lineas.slice(0, 6).join("\n");
  return texto + (resto > 0 ? `\n(y ${resto} arista${resto > 1 ? "s" : ""} más)` : "");
}

/** Devuelve `{provisionales, seleccion, actualizacion, empates, camino}`. */
export function ejemplosAlgoritmo(grafo, resultado) {
  const snaps = resultado.snapshots;
  const o = resultado.origen;
  const d = resultado.destino;
  const indices = {
    [SELECCION]: snaps.flatMap((s, i) => (s.subpaso === SELECCION ? [i] : [])),
    [ACTUALIZACION]: snaps.flatMap((s, i) => (s.subpaso === ACTUALIZACION ? [i] : [])),
  };
  const conAristas = indices[ACTUALIZACION].filter((i) => snaps[i].aristasEvaluadas.length > 0);

  // 1. Distancias provisionales -------------------------------------------------
  const inicial = snaps[0];
  const sinDistancia = grafo.vertices.filter((v) => inicial.distancias[v] === INFINITO).length;
  let provisionales;
  if (o === d) {
    provisionales =
      `Al empezar, ${o} tiene [0, -]₀ y los otros ${sinDistancia} vértices están en ∞. ` +
      "Como origen y destino coinciden, el algoritmo termina enseguida y ninguno recibe distancia.";
  } else if (conAristas.length) {
    const s = snaps[conAristas[0]];
    const lista = s.aristasEvaluadas.map(([, v]) => `${v} (${formatoDistancia(s.distancias[v])})`).join(", ");
    provisionales =
      `Al empezar, ${o} tiene [0, -]₀ y los otros ${sinDistancia} vértices están en ∞. ` +
      `Tras examinar las aristas de ${o}, reciben una distancia provisional: ${lista}. ` +
      "Siguen siendo provisionales hasta que se seleccionen.";
  } else {
    provisionales =
      `Al empezar, ${o} tiene [0, -]₀ y los otros ${sinDistancia} vértices están en ∞. ` +
      `${o} no tiene aristas hacia otros vértices, así que ninguno recibe distancia.`;
  }

  // 2. Selección del vértice de menor distancia -----------------------------------
  const selecciones = indices[SELECCION];
  let seleccion;
  if (selecciones.length) {
    const i = selecciones.length > 1 ? selecciones[1] : selecciones[0];
    const e = explicar(grafo, resultado, i);
    const candidatos = _seccion(e.breve, "Candidatos").map((b) => b.texto).join(" ");
    const queHace = _seccion(e.breve, "Qué hace").map((b) => b.texto).join(" ");
    seleccion = `Iteración ${snaps[i].iteracion}. Candidatos con su distancia: ${candidatos}. ${queHace}`;
  } else {
    // origen = destino: Dijkstra termina sin seleccionar nada
    seleccion =
      `En tu grafo origen y destino coinciden (${o}): no hay ninguna selección, ` +
      "porque la distancia mínima ya es 0.";
  }

  // 3. Actualización de etiquetas y predecesores ---------------------------------
  const conReemplazo = conAristas.filter((i) => snaps[i].etiquetasDescartadas.length > 0);
  const elegido = conReemplazo.length ? conReemplazo[0] : conAristas.length ? conAristas[0] : null;
  let actualizacion;
  if (o === d) {
    actualizacion = "En tu grafo no hay actualizaciones: origen y destino coinciden y no se examina ninguna arista.";
  } else if (elegido === null) {
    actualizacion = "En tu grafo ningún vértice alcanzable tiene aristas hacia vértices pendientes.";
  } else {
    const e = explicar(grafo, resultado, elegido);
    actualizacion =
      `Iteración ${snaps[elegido].iteracion}, desde ${snaps[elegido].seleccionado}:\n` +
      _conTresAristas(_calculos(e.breve));
  }

  // 4. Empates ----------------------------------------------------------------------
  const conEmpate = conAristas.filter((i) => snaps[i].aristasEvaluadas.some(([, , t]) => t === "empate"));
  let empates;
  if (conEmpate.length) {
    const e = explicar(grafo, resultado, conEmpate[0]);
    empates =
      `Iteración ${snaps[conEmpate[0]].iteracion}, desde ${snaps[conEmpate[0]].seleccionado}:\n` +
      _conTresAristas(_calculos(e.breve));
  } else {
    empates =
      "En tu grafo no se produce ningún empate en esta ejecución: cada vértice llega por un " +
      "único camino mínimo. Si usas otro grafo, verás las aristas de empate en naranja.";
  }

  // 5. Reconstrucción del camino mínimo ---------------------------------------------
  const final = explicar(grafo, resultado, snaps.length - 1);
  let camino;
  if (o === d) {
    camino = `En tu grafo origen y destino coinciden (${o}): la distancia es 0 y no hay camino que recorrer.`;
  } else if (!resultado.alcanzable) {
    camino = `En tu grafo ${d} no es alcanzable desde ${o}: nunca recibió etiqueta, así que no hay camino.`;
  } else {
    const sumas = _seccion(final.detalle, "Caminos mínimos y suma de pesos")
      .filter((b) => b.estilo === CALCULO)
      .map((b) => b.texto);
    camino =
      `La etiqueta de ${d} es ${snaps[snaps.length - 1].etiqueta(d)}. Siguiendo los predecesores hacia atrás desde ` +
      `${d} hasta ${o} se obtiene:\n` +
      sumas.map((s) => s.replaceAll("   ", " ")).join("\n");
  }
  return Object.freeze({ provisionales, seleccion, actualizacion, empates, camino });
}
