/**
 * Origen y destino sugeridos, y revisión de un grafo antes de simularlo.
 * Traducción de core/extremos.py. Funciones puras sobre `Grafo`.
 *
 *  - sugerirExtremos: con una sola fuente (sin aristas entrantes) y un solo sumidero (sin
 *    salientes) devuelve exactamente esa pareja; con varias opciones elige una pareja válida.
 *  - analizar: detecta vértices aislados, vértices que el origen no alcanza y si el destino
 *    es inalcanzable, para avisar al usuario antes de simular.
 */

/** Vértices con aristas salientes y ninguna entrante (posibles orígenes). */
export function fuentes(grafo) {
  return grafo.vertices.filter((v) => grafo.entrantes(v).length === 0 && grafo.salientes(v).length > 0);
}

/** Vértices con aristas entrantes y ninguna saliente (posibles destinos). */
export function sumideros(grafo) {
  return grafo.vertices.filter((v) => grafo.salientes(v).length === 0 && grafo.entrantes(v).length > 0);
}

/** Vértices sin ninguna arista (ni entrante ni saliente). */
export function aislados(grafo) {
  return grafo.vertices.filter((v) => grafo.entrantes(v).length === 0 && grafo.salientes(v).length === 0);
}

/** Número mínimo de aristas desde `origen` a cada vértice alcanzable (incluido él mismo): `{vértice: saltos}`. */
export function saltosDesde(grafo, origen) {
  const saltos = { [origen]: 0 };
  const cola = [origen];
  let cabeza = 0;
  while (cabeza < cola.length) {
    const u = cola[cabeza++];
    for (const [w] of grafo.salientes(u)) {
      if (!(w in saltos)) {
        saltos[w] = saltos[u] + 1;
        cola.push(w);
      }
    }
  }
  return saltos;
}

/**
 * Pareja `[origen, destino]` sugerida para el grafo.
 *
 * Una sola fuente y un solo sumidero: esa pareja. Varias opciones: la fuente que alcanza más
 * vértices y, entre sus sumideros alcanzables, el más lejano; los empates se resuelven por el
 * orden alfabético (se conserva la primera pareja encontrada). Sin aristas: primer y último vértice.
 */
export function sugerirExtremos(grafo) {
  const origenes = fuentes(grafo);
  const destinos = sumideros(grafo);
  if (origenes.length === 1 && destinos.length === 1) return [origenes[0], destinos[0]];
  let mejor = null; // [alcanzados, saltosAlDestino, origen, destino]
  for (const o of origenes) {
    const saltos = saltosDesde(grafo, o);
    const alcanzados = Object.keys(saltos).length;
    for (const d of destinos) {
      if (d in saltos) {
        const s = saltos[d];
        // comparación de tuplas (len(saltos), saltos[d]) con «mayor estricto»
        if (mejor === null || alcanzados > mejor[0] || (alcanzados === mejor[0] && s > mejor[1])) {
          mejor = [alcanzados, s, o, d];
        }
      }
    }
  }
  if (mejor !== null) return [mejor[2], mejor[3]];
  return [grafo.vertices[0], grafo.vertices[grafo.vertices.length - 1]];
}

/** Qué vértices no intervendrán en la simulación desde `origen`. */
export function analizar(grafo, origen, destino) {
  const alcanzados = saltosDesde(grafo, origen);
  const solos = new Set(aislados(grafo));
  const sinAlcance = grafo.vertices.filter((v) => !(v in alcanzados) && !solos.has(v));
  const analisis = {
    origen,
    destino,
    aislados: grafo.vertices.filter((v) => solos.has(v)),
    sinAlcance,
    destinoAlcanzable: destino in alcanzados,
  };
  analisis.hayAdvertencias =
    analisis.aislados.length > 0 || analisis.sinAlcance.length > 0 || !analisis.destinoAlcanzable;
  return Object.freeze(analisis);
}

const _lista = (vertices) => vertices.join(", ");

/** Texto de la advertencia para mostrar al usuario (una sección por problema). */
export function mensajeAdvertencia(a) {
  const partes = [];
  if (!a.destinoAlcanzable) {
    partes.push(
      `⚠ El destino ${a.destino} no es alcanzable desde el origen ${a.origen}: ` +
        "la simulación terminará sin camino.",
    );
  }
  if (a.aislados.length) partes.push(`Vértices aislados (sin ninguna conexión): ${_lista(a.aislados)}.`);
  if (a.sinAlcance.length) {
    partes.push(
      `Vértices que el origen ${a.origen} no alcanza y no participarán en el recorrido: ` +
        `${_lista(a.sinAlcance)}.`,
    );
  }
  partes.push(`Se simulará de ${a.origen} a ${a.destino}; podrás cambiarlos en la simulación.`);
  return partes.join("\n\n");
}
