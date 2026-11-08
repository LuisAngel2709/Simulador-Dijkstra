/**
 * Generación aleatoria de grafos dirigidos acíclicos organizados por capas.
 * Traducción de core/generator.py. Con el mismo generador de azar (`AzarPython`) y la misma
 * semilla produce exactamente los mismos grafos que la versión Python.
 *
 * El grafo se construye sobre capas explícitas (una capa de origen, varias intermedias y una
 * de destino). Solo se crean aristas hacia capas posteriores, de modo que el DAG está
 * garantizado por construcción, y cada vértice recibe al menos una arista de la capa anterior.
 */

import { AzarPython } from "./azar.js";
import { ejecutarDijkstra } from "./engine.js";
import { Grafo, PESO_MAXIMO, PESO_MINIMO } from "./graph.js";

export const MAX_SALIENTES = 3;
export const MAX_ENTRANTES = 3;
export const TAMANOS_DE_CAPA = [2, 3, 3, 4];

/** Probabilidad de arista extra entre capas consecutivas. */
export function densidadPorDefecto(n) {
  return n <= 9 ? 0.38 : 0.28;
}

/**
 * Tamaños de cada capa: la primera y la última siempre tienen un vértice, de modo que el
 * origen y el destino quedan aislados en sus capas y siempre existe camino entre ambos.
 */
export function repartirEnCapas(n, azar) {
  let restante = n - 2;
  const tamanos = [];
  const maximo = Math.max(...TAMANOS_DE_CAPA);
  while (restante > 0) {
    let tam = Math.min(azar.choice(TAMANOS_DE_CAPA), restante);
    if (restante - tam === 1) {
      // evita dejar suelta una capa de un solo vértice
      tam = tam + 1 <= maximo ? restante : tam - 1;
    }
    tamanos.push(tam);
    restante -= tam;
  }
  return [1, ...tamanos, 1];
}

/**
 * Genera un DAG por capas y devuelve `[grafo, origen, destino]`.
 *
 * Todos los vértices son alcanzables desde el origen y todos alcanzan el destino. Los pesos se
 * sortean en un rango pequeño (1..9 por defecto) para que aparezcan empates con frecuencia.
 *
 * @param {number} n
 * @param {{densidad?: number|null, rng?: AzarPython|null, pesoMaximo?: number}} [opciones]
 */
export function generarDag(n, { densidad = null, rng = null, pesoMaximo = 9 } = {}) {
  if (!(PESO_MINIMO <= pesoMaximo && pesoMaximo <= PESO_MAXIMO)) {
    throw new RangeError("peso_maximo fuera del rango admitido.");
  }
  if (n < 3) throw new RangeError("La generación por capas necesita al menos 3 vértices.");
  if (densidad === null || densidad === undefined) densidad = densidadPorDefecto(n);

  const azar = rng ?? new AzarPython();
  const grafo = new Grafo(n);
  const vertices = [...grafo.vertices];
  azar.shuffle(vertices);

  const capas = [];
  let inicio = 0;
  for (const tam of repartirEnCapas(n, azar)) {
    capas.push(vertices.slice(inicio, inicio + tam));
    inicio += tam;
  }

  const conectar = (u, v, forzar = false) => {
    if (grafo.existeArista(u, v)) return false;
    if (!forzar && (grafo.salientes(u).length >= MAX_SALIENTES || grafo.entrantes(v).length >= MAX_ENTRANTES)) {
      return false;
    }
    grafo.agregarArista(u, v, azar.randint(PESO_MINIMO, pesoMaximo));
    return true;
  };

  // Reparte las conexiones en lugar de concentrarlas en un mismo vértice. Igual que `sorted(key=…)`
  // de Python, las claves se calculan una vez por elemento y en el orden de la lista.
  const menosCargados = (candidatos, clave) => {
    const conClave = candidatos.map((x) => [x, clave(x), azar.random()]);
    conClave.sort((a, b) => a[1] - b[1] || a[2] - b[2]); // ordenación estable
    return conClave.map((t) => t[0]);
  };

  // 1. Cada vértice recibe al menos una arista de la capa inmediatamente anterior.
  for (let k = 1; k < capas.length; k++) {
    for (const v of capas[k]) {
      const candidatos = menosCargados(capas[k - 1], (u) => grafo.salientes(u).length);
      if (!candidatos.some((u) => conectar(u, v))) conectar(candidatos[0], v, true);
    }
  }

  // 2. Cada vértice que no esté en la última capa envía al menos una arista.
  for (let k = 0; k < capas.length - 1; k++) {
    for (const u of capas[k]) {
      if (grafo.salientes(u).length) continue;
      const candidatos = menosCargados(capas[k + 1], (v) => grafo.entrantes(v).length);
      if (!candidatos.some((v) => conectar(u, v))) conectar(u, candidatos[0], true);
    }
  }

  // 3. Aristas adicionales entre capas consecutivas.
  for (let k = 0; k < capas.length - 1; k++) {
    for (const u of capas[k]) {
      for (const v of capas[k + 1]) {
        if (azar.random() < densidad) conectar(u, v);
      }
    }
  }

  // 4. Unos pocos saltos de dos capas, para que el grafo no sea un simple tejido.
  const saltosPermitidos = Math.max(1, Math.floor(n / 5));
  let saltos = 0;
  for (let k = 0; k < capas.length - 2; k++) {
    for (const u of capas[k]) {
      for (const v of capas[k + 2]) {
        if (saltos >= saltosPermitidos) break;
        if (azar.random() < densidad / 2 && conectar(u, v)) saltos += 1;
      }
    }
  }

  return [grafo, capas[0][0], capas[capas.length - 1][0]];
}

/**
 * Genera un DAG y prefiere, si lo encuentra, uno con varios caminos mínimos.
 * Si ningún intento produce un empate, devuelve el último grafo generado.
 */
export function generarDagDidactico(n, { densidad = null, intentos = 40, rng = null, pesoMaximo = 9 } = {}) {
  const azar = rng ?? new AzarPython();
  let ultimo = generarDag(n, { densidad, rng: azar, pesoMaximo });
  for (let i = 0; i < intentos; i++) {
    const candidato = generarDag(n, { densidad, rng: azar, pesoMaximo });
    const [grafo, origen, destino] = candidato;
    const resultado = ejecutarDijkstra(grafo, origen, destino);
    if (resultado.cantidadCaminos >= 2) return candidato;
    ultimo = candidato;
  }
  return ultimo;
}
