/**
 * Motor del algoritmo de Dijkstra con etiquetación al estilo académico.
 * Traducción de core/dijkstra_engine.py (mismo comportamiento, mismos textos de etiqueta).
 *
 *  - etiqueta [d, V]n → distancia acumulada, predecesor(es) e iteración;
 *  - un vértice puede conservar VARIOS predecesores cuando hay empate de distancia;
 *  - la ejecución se registra en snapshots inmutables (avanzar / retroceder);
 *  - reconstruye TODOS los caminos mínimos entre origen y destino.
 *
 * No depende de ninguna interfaz ni del navegador.
 */

import { GrafoError } from "./graph.js";

export const INFINITO = Infinity;

export const SUBINDICES = "₀₁₂₃₄₅₆₇₈₉";

// Subpasos de la simulación
export const INICIO = "inicio";
export const SELECCION = "seleccion";
export const ACTUALIZACION = "actualizacion";
export const FINAL = "final";

// Estados de una etiqueta en la tabla
export const VIGENTE = "vigente";
export const EMPATE = "empate";
export const DESCARTADA = "descartada";

export const LIMITE_CAMINOS = 500;

export function subindice(n) {
  return [...String(Math.trunc(n))].map((d) => SUBINDICES[Number(d)]).join("");
}

export function formatoDistancia(d) {
  return d === INFINITO ? "∞" : String(Math.trunc(d));
}

/**
 * Construye la etiqueta educativa [d, V]n separando múltiples predecesores si los hay.
 *
 * `iteracion` puede ser un entero (mismo subíndice para todos los predecesores), un objeto
 * `{predecesor: iteración}` cuando cada predecesor se descubrió en una iteración distinta,
 * o `null`/`undefined`.
 */
export function textoEtiqueta(distancia, predecesores, iteracion) {
  if (distancia === INFINITO) return "[∞, -]";
  const d = Math.trunc(distancia);
  const esEntero = typeof iteracion === "number";
  const esMapa = iteracion !== null && typeof iteracion === "object";
  if (!predecesores || predecesores.length === 0) {
    const sufijo = esEntero ? subindice(iteracion) : "";
    return `[${d}, -]${sufijo}`;
  }
  if (esMapa) return predecesores.map((p) => `[${d}, ${p}]${subindice(iteracion[p])}`).join("  ");
  const sufijo = iteracion !== null && iteracion !== undefined ? subindice(iteracion) : "";
  return predecesores.map((p) => `[${d}, ${p}]${sufijo}`).join("  ");
}

/** Equivalente del `x or y` de Python para «mapa vacío o ausente → alternativa». */
function mapaONulo(mapa, alternativa) {
  return mapa && Object.keys(mapa).length > 0 ? mapa : alternativa;
}

/** Conjunto de solo lectura (equivalente de ``frozenset``). */
export class ConjuntoInmutable extends Set {
  constructor(elementos) {
    super(elementos);
    this._cerrado = true;
  }

  add(valor) {
    if (this._cerrado) throw new TypeError("El conjunto es inmutable.");
    return super.add(valor);
  }

  delete() {
    throw new TypeError("El conjunto es inmutable.");
  }

  clear() {
    throw new TypeError("El conjunto es inmutable.");
  }
}

/** Congela recursivamente objetos y arreglos (los snapshots no deben modificarse nunca). */
function congelar(valor) {
  if (valor !== null && typeof valor === "object" && !(valor instanceof Set) && !Object.isFrozen(valor)) {
    Object.freeze(valor);
    for (const v of Object.values(valor)) congelar(v);
  }
  return valor;
}

/** Una etiqueta registrada en la tabla del proceso. */
export class EntradaTabla {
  constructor(vertice, iteracion, distancia, predecesores, estado) {
    this.vertice = vertice;
    this.iteracion = iteracion;
    this.distancia = distancia;
    this.predecesores = Object.freeze([...predecesores]);
    this.estado = estado; // VIGENTE | EMPATE | DESCARTADA
    Object.freeze(this);
  }

  get texto() {
    const preds = this.predecesores.length ? this.predecesores.join("/") : "-";
    return `${formatoDistancia(this.distancia)}, ${preds}`;
  }
}

/** Estado inmutable y completo de la simulación en un instante dado. Solo contiene datos:
 * los textos para el usuario se construyen siempre en `explicaciones.js` (única fuente). */
export class Snapshot {
  constructor(campos) {
    this.indice = campos.indice;
    this.iteracion = campos.iteracion;
    this.subpaso = campos.subpaso;
    this.titulo = campos.titulo;
    this.distancias = campos.distancias; // {vértice: distancia}
    this.predecesores = campos.predecesores; // {vértice: [predecesores]}
    this.iteracionEtiqueta = campos.iteracionEtiqueta; // {vértice: iteración}
    this.iteracionPorPredecesor = campos.iteracionPorPredecesor; // {vértice: {predecesor: iteración}}
    this.visitados = campos.visitados; // ConjuntoInmutable
    this.seleccionado = campos.seleccionado; // string | null
    this.aristasEvaluadas = campos.aristasEvaluadas; // [[u, v, tipo]]
    this.aristasCamino = campos.aristasCamino; // [[u, v]]
    this.etiquetasDescartadas = campos.etiquetasDescartadas; // [[vértice, texto tachado]]
    this.tabla = campos.tabla; // [EntradaTabla]
    this.caminos = campos.caminos; // [[vértices]]
    this.distanciaDestino = campos.distanciaDestino;
    this.esFinal = campos.esFinal;
    congelar(this);
  }

  etiqueta(vertice) {
    const info = mapaONulo(this.iteracionPorPredecesor[vertice], this.iteracionEtiqueta[vertice]);
    return textoEtiqueta(this.distancias[vertice], this.predecesores[vertice] ?? [], info);
  }

  iteracionesTabla() {
    return [...new Set(this.tabla.map((e) => e.iteracion))].sort((a, b) => a - b);
  }
}

export class ResultadoDijkstra {
  constructor({ origen, destino, distancia, caminos, distancias, predecesores, snapshots, truncado = false }) {
    this.origen = origen;
    this.destino = destino;
    this.distancia = distancia;
    this.caminos = caminos;
    this.distancias = distancias;
    this.predecesores = predecesores;
    this.snapshots = snapshots;
    this.truncado = truncado;
    congelar(this);
  }

  get alcanzable() {
    return this.distancia !== INFINITO;
  }

  get cantidadCaminos() {
    return this.caminos.length;
  }
}

/**
 * Devuelve `[caminos, truncado]`: todos los caminos mínimos origen → destino y si hubo truncamiento.
 *
 * Recorre hacia atrás todos los predecesores registrados; como el grafo de predecesores es
 * acíclico, la recursión con memoización siempre termina. Tener exactamente `limite` caminos
 * NO es truncar: solo se marca cuando existe al menos un camino más del que cabe.
 */
export function reconstruirCaminos(predecesores, origen, destino, limite = LIMITE_CAMINOS) {
  let truncado = false;
  const memoria = new Map();

  function caminosHasta(v) {
    if (v === origen) return [[origen]];
    if (memoria.has(v)) return memoria.get(v);
    const resultado = [];
    let lleno = false;
    for (const p of predecesores[v] ?? []) {
      // orden estable
      for (const parcial of caminosHasta(p)) {
        if (resultado.length >= limite) {
          truncado = lleno = true;
          break;
        }
        resultado.push([...parcial, v]);
      }
      if (lleno) break;
    }
    memoria.set(v, resultado);
    return resultado;
  }

  if (origen === destino) return [[[origen]], false];
  return [caminosHasta(destino), truncado];
}

/** Copia superficial de un objeto `{vértice: valor}` con cada valor copiado por `f`. */
function copiarMapa(mapa, f = (x) => x) {
  const salida = {};
  for (const [k, v] of Object.entries(mapa)) salida[k] = f(v);
  return salida;
}

/** Ejecuta Dijkstra sobre un grafo y produce la secuencia de snapshots. */
export class MotorDijkstra {
  constructor(grafo, origen, destino) {
    if (!grafo.existeVertice(origen)) throw new GrafoError(`El vértice origen ${origen} no pertenece al grafo.`);
    if (!grafo.existeVertice(destino)) throw new GrafoError(`El vértice destino ${destino} no pertenece al grafo.`);
    this.grafo = grafo;
    this.origen = origen;
    this.destino = destino;

    this._distancias = Object.fromEntries(grafo.vertices.map((v) => [v, INFINITO]));
    this._predecesores = Object.fromEntries(grafo.vertices.map((v) => [v, []]));
    this._iteracionEtiqueta = {};
    this._iterPorPred = {};
    this._visitados = new Set();
    this._tabla = []; // entradas mutables {vertice, iteracion, distancia, predecesores, estado}
    this._snapshots = [];
    this._iteracion = 0;
  }

  // ------------------------------------------------------------------ ejecución

  ejecutar() {
    this._distancias[this.origen] = 0;
    this._iteracionEtiqueta[this.origen] = 0;
    this._tabla.push({ vertice: this.origen, iteracion: 0, distancia: 0, predecesores: ["-"], estado: VIGENTE });

    const coinciden = this.origen === this.destino;
    this._guardar({ subpaso: INICIO, titulo: "Iteración 0 — Etiquetado del vértice origen" });

    // Origen = destino: la distancia ya es definitiva (0), no hay nada más que recorrer.
    while (!coinciden) {
      const seleccionado = this._elegirVertice();
      if (seleccionado === null) break;
      this._iteracion += 1;
      this._pasoSeleccion(seleccionado);
      this._pasoActualizacion(seleccionado);
    }

    const distancia = this._distancias[this.destino];
    let [caminos, truncado] = reconstruirCaminos(
      copiarMapa(this._predecesores, (p) => [...p]),
      this.origen,
      this.destino,
    );
    if (distancia === INFINITO) caminos = [];

    this._guardarFinal(distancia, caminos);

    return new ResultadoDijkstra({
      origen: this.origen,
      destino: this.destino,
      distancia,
      caminos,
      distancias: copiarMapa(this._distancias),
      predecesores: copiarMapa(this._predecesores, (p) => [...p]),
      snapshots: this._snapshots,
      truncado,
    });
  }

  // --------------------------------------------------------------------- pasos

  /** Vértice no visitado con menor distancia; empate por orden alfabético. */
  _elegirVertice() {
    let mejor = null;
    for (const v of this.grafo.vertices) {
      if (this._visitados.has(v) || this._distancias[v] === INFINITO) continue;
      if (
        mejor === null ||
        this._distancias[v] < this._distancias[mejor] ||
        (this._distancias[v] === this._distancias[mejor] && v < mejor)
      ) {
        mejor = v;
      }
    }
    return mejor;
  }

  _pasoSeleccion(u) {
    this._visitados.add(u);
    this._guardar({
      subpaso: SELECCION,
      titulo: `Iteración ${this._iteracion} — Selección de vértice`,
      seleccionado: u,
    });
  }

  _pasoActualizacion(u) {
    const aristas = [];
    const descartadas = [];
    const vecinos = this.grafo.salientes(u).filter(([v]) => !this._visitados.has(v));

    for (const [v, peso] of vecinos) {
      const nueva = this._distancias[u] + peso;
      const actual = this._distancias[v];

      if (nueva < actual) {
        if (actual !== INFINITO) {
          const info = mapaONulo(this._iterPorPred[v], this._iteracionEtiqueta[v]);
          descartadas.push([v, textoEtiqueta(actual, this._predecesores[v], info)]);
          for (const entrada of this._tabla) {
            if (entrada.vertice === v && entrada.estado !== DESCARTADA) entrada.estado = DESCARTADA;
          }
        }
        this._distancias[v] = nueva;
        this._predecesores[v] = [u];
        this._iteracionEtiqueta[v] = this._iteracion;
        this._iterPorPred[v] = { [u]: this._iteracion };
        this._tabla.push({ vertice: v, iteracion: this._iteracion, distancia: nueva, predecesores: [u], estado: VIGENTE });
        aristas.push([u, v, "mejora"]);
      } else if (nueva === actual) {
        if (!this._predecesores[v].includes(u)) this._predecesores[v].push(u);
        (this._iterPorPred[v] ??= {})[u] = this._iteracion;
        for (const entrada of this._tabla) {
          if (entrada.vertice === v && entrada.estado === VIGENTE) entrada.estado = EMPATE;
        }
        this._tabla.push({ vertice: v, iteracion: this._iteracion, distancia: nueva, predecesores: [u], estado: EMPATE });
        aristas.push([u, v, "empate"]);
      } else {
        this._tabla.push({ vertice: v, iteracion: this._iteracion, distancia: nueva, predecesores: [u], estado: DESCARTADA });
        aristas.push([u, v, "descartada"]);
      }
    }

    this._guardar({
      subpaso: ACTUALIZACION,
      titulo: `Iteración ${this._iteracion} — Actualización de etiquetas`,
      seleccionado: u,
      aristas,
      descartadas,
    });
  }

  _guardarFinal(distancia, caminos) {
    const aristasCamino = [];
    for (const camino of caminos) {
      for (let i = 0; i + 1 < camino.length; i++) {
        const a = camino[i];
        const b = camino[i + 1];
        if (!aristasCamino.some(([x, y]) => x === a && y === b)) aristasCamino.push([a, b]);
      }
    }
    this._guardar({
      subpaso: FINAL,
      titulo: "Resultado final",
      caminos,
      distanciaDestino: distancia,
      aristasCamino,
      esFinal: true,
    });
  }

  // ----------------------------------------------------------------- snapshots

  _guardar({
    subpaso,
    titulo,
    seleccionado = null,
    aristas = [],
    descartadas = [],
    caminos = [],
    aristasCamino = [],
    distanciaDestino = INFINITO,
    esFinal = false,
  }) {
    this._snapshots.push(
      new Snapshot({
        indice: this._snapshots.length,
        iteracion: this._iteracion,
        subpaso,
        titulo,
        distancias: copiarMapa(this._distancias),
        predecesores: copiarMapa(this._predecesores, (p) => [...p]),
        iteracionEtiqueta: copiarMapa(this._iteracionEtiqueta),
        iteracionPorPredecesor: copiarMapa(this._iterPorPred, (m) => ({ ...m })),
        visitados: new ConjuntoInmutable(this._visitados),
        seleccionado,
        aristasEvaluadas: aristas.map((a) => [...a]),
        aristasCamino: aristasCamino.map((a) => [...a]),
        etiquetasDescartadas: descartadas.map((a) => [...a]),
        tabla: this._tabla.map((e) => new EntradaTabla(e.vertice, e.iteracion, e.distancia, e.predecesores, e.estado)),
        caminos: caminos.map((c) => [...c]),
        distanciaDestino,
        esFinal,
      }),
    );
  }
}

/** Navegación por los snapshots: avanzar, retroceder, reiniciar, finalizar. */
export class Simulacion {
  constructor(resultado) {
    this.resultado = resultado;
    this.snapshots = resultado.snapshots;
    this.indice = 0;
  }

  get total() {
    return this.snapshots.length;
  }

  get actual() {
    return this.snapshots[this.indice];
  }

  get puedeAvanzar() {
    return this.indice < this.total - 1;
  }

  get puedeRetroceder() {
    return this.indice > 0;
  }

  siguiente() {
    if (this.puedeAvanzar) this.indice += 1;
    return this.actual;
  }

  anterior() {
    if (this.puedeRetroceder) this.indice -= 1;
    return this.actual;
  }

  reiniciar() {
    this.indice = 0;
    return this.actual;
  }

  finalizar() {
    this.indice = this.total - 1;
    return this.actual;
  }
}

/** Atajo cómodo para el resto de la aplicación. */
export function ejecutarDijkstra(grafo, origen, destino) {
  return new MotorDijkstra(grafo, origen, destino).ejecutar();
}
