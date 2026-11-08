/**
 * Casos de oro: serialización y regeneración (traducción de core/golden.py).
 *
 * `serializarCaso` produce, para un grafo y una pareja origen/destino, exactamente el mismo JSON
 * que `core.golden.serializar_caso` de Python. `construirGolden` regenera los 32 casos (los
 * manuales y los de semilla fija), la validación y el truncamiento; si el port es fiel, el
 * resultado es idéntico al archivo `golden/dijkstra_golden.json` generado por Python.
 */

import { AzarPython } from "./azar.js";
import { INFINITO, LIMITE_CAMINOS, ejecutarDijkstra, reconstruirCaminos } from "./engine.js";
import { explicar } from "./explicaciones.js";
import { analizar, aislados, fuentes, mensajeAdvertencia, sugerirExtremos, sumideros } from "./extremos.js";
import { generarDag, generarDagDidactico } from "./generador.js";
import {
  Grafo,
  GrafoError,
  NODOS_MAXIMO,
  NODOS_MINIMO,
  PESO_MAXIMO,
  PESO_MINIMO,
  validarNumeroNodos,
  validarPeso,
} from "./graph.js";
import { ejemplosAlgoritmo } from "./tutorial.js";

export const FORMATO = 1;

// ------------------------------------------------------------------- serialización

/** Distancia → entero, o `null` si es infinita. */
const _num = (valor) => (valor === INFINITO ? null : Math.trunc(valor));

const _bloques = (bloques) => bloques.map((b) => ({ estilo: b.estilo, texto: b.texto }));

const _mapa = (obj, f) => Object.fromEntries(Object.entries(obj).map(([k, v]) => [k, f(v)]));

function _grafo(g) {
  return { n: g.n, vertices: [...g.vertices], aristas: g.aristas().map(([u, v, p]) => [u, v, p]) };
}

const _tabla = (entradas) =>
  entradas.map((e) => ({
    vertice: e.vertice,
    iteracion: e.iteracion,
    distancia: _num(e.distancia),
    predecesores: [...e.predecesores],
    estado: e.estado,
    texto: e.texto,
  }));

function _snapshot(g, resultado, i) {
  const s = resultado.snapshots[i];
  const e = explicar(g, resultado, i);
  return {
    indice: s.indice,
    iteracion: s.iteracion,
    subpaso: s.subpaso,
    titulo: s.titulo,
    seleccionado: s.seleccionado,
    es_final: s.esFinal,
    distancias: _mapa(s.distancias, _num),
    predecesores: _mapa(s.predecesores, (p) => [...p]),
    iteracion_etiqueta: { ...s.iteracionEtiqueta },
    iteracion_por_predecesor: _mapa(s.iteracionPorPredecesor, (m) => ({ ...m })),
    etiquetas: Object.fromEntries(g.vertices.map((v) => [v, s.etiqueta(v)])),
    visitados: [...s.visitados].sort(),
    aristas_evaluadas: s.aristasEvaluadas.map((a) => [...a]),
    aristas_camino: s.aristasCamino.map((a) => [...a]),
    etiquetas_descartadas: s.etiquetasDescartadas.map((a) => [...a]),
    tabla: _tabla(s.tabla),
    caminos: s.caminos.map((c) => [...c]),
    distancia_destino: _num(s.distanciaDestino),
    explicacion: {
      titulo: e.titulo,
      subtitulo: e.subtitulo,
      breve: _bloques(e.breve),
      detalle: _bloques(e.detalle),
    },
  };
}

/** Todo lo que debe reproducir un port para `g`, `origen` y `destino`. */
export function serializarCaso(nombre, g, origen, destino) {
  const r = ejecutarDijkstra(g, origen, destino);
  const ej = ejemplosAlgoritmo(g, r);
  const analisis = analizar(g, origen, destino);
  const [sugO, sugD] = sugerirExtremos(g);
  return {
    nombre,
    grafo: _grafo(g),
    origen,
    destino,
    resultado: {
      distancia: _num(r.distancia),
      alcanzable: r.alcanzable,
      caminos: r.caminos.map((c) => [...c]),
      cantidad_caminos: r.cantidadCaminos,
      truncado: r.truncado,
      distancias: _mapa(r.distancias, _num),
      predecesores: _mapa(r.predecesores, (p) => [...p]),
    },
    snapshots: r.snapshots.map((_, i) => _snapshot(g, r, i)),
    tutorial: {
      provisionales: ej.provisionales,
      seleccion: ej.seleccion,
      actualizacion: ej.actualizacion,
      empates: ej.empates,
      camino: ej.camino,
    },
    extremos: {
      fuentes: fuentes(g),
      sumideros: sumideros(g),
      aislados: aislados(g),
      sugerido: [sugO, sugD],
      analisis: {
        aislados: [...analisis.aislados],
        sin_alcance: [...analisis.sinAlcance],
        destino_alcanzable: analisis.destinoAlcanzable,
        hay_advertencias: analisis.hayAdvertencias,
        mensaje: analisis.hayAdvertencias ? mensajeAdvertencia(analisis) : null,
      },
    },
  };
}

export function grafoDesdeJson(datos) {
  const g = new Grafo(datos.n);
  for (const [u, v, p] of datos.aristas) g.agregarArista(u, v, p);
  return g;
}

/** Recalcula un caso guardado con el código actual. */
export function reproducirCaso(caso) {
  return serializarCaso(caso.nombre, grafoDesdeJson(caso.grafo), caso.origen, caso.destino);
}

// ------------------------------------------------------------------------ los casos

function _construir(n, aristas) {
  const g = new Grafo(n);
  for (const [u, v, p] of aristas) g.agregarArista(u, v, p);
  return g;
}

/** Cadena de rombos de peso 1: 2**etapas caminos mínimos. */
function _rombos(etapas) {
  const g = new Grafo(1 + 3 * etapas);
  const nombres = g.vertices;
  let anterior = nombres[0];
  let i = 1;
  for (let e = 0; e < etapas; e++) {
    const a = nombres[i];
    const b = nombres[i + 1];
    const fin = nombres[i + 2];
    i += 3;
    for (const medio of [a, b]) {
      g.agregarArista(anterior, medio, 1);
      g.agregarArista(medio, fin, 1);
    }
    anterior = fin;
  }
  return g;
}

// Ejemplos 3 y 4 de la Lectura 5 (el 3 tiene dos caminos mínimos de A a H), orientados de A hacia H.
const PDF_EJEMPLO_3 = [
  ["A", "B", 3], ["A", "C", 1], ["B", "D", 1], ["B", "G", 5], ["C", "D", 2], ["C", "F", 5],
  ["D", "E", 4], ["D", "F", 2], ["E", "G", 2], ["E", "H", 1], ["F", "H", 3],
];
const PDF_EJEMPLO_4 = [
  ["A", "B", 4], ["A", "C", 3], ["B", "C", 1], ["B", "E", 3], ["C", "D", 2], ["C", "E", 2],
  ["D", "E", 1], ["D", "G", 3], ["E", "F", 2], ["E", "G", 2], ["F", "G", 1], ["F", "H", 3],
  ["G", "H", 4],
];

/** `[nombre, grafo, origen, destino]` de los casos armados a mano. */
export function casosManuales() {
  const ejemplo = _construir(8, PDF_EJEMPLO_3);
  const ejemplo4 = _construir(8, PDF_EJEMPLO_4);
  const cadena = _construir(7, [["A", "B", 1], ["B", "C", 2], ["C", "D", 3], ["D", "E", 4], ["E", "F", 5], ["F", "G", 6]]);
  const reemplazo = _construir(7, [["A", "B", 10], ["A", "C", 2], ["C", "B", 3]]);
  const empateSel = _construir(7, [["A", "B", 4], ["A", "C", 4], ["B", "D", 1], ["C", "D", 1], ["D", "E", 2]]);
  const aislado = _construir(7, [["A", "B", 2], ["B", "C", 1]]);
  const pesosExtremos = _construir(7, [["A", "B", 99], ["A", "C", 1], ["C", "B", 98], ["B", "D", 1], ["C", "D", 99]]);
  const dosOrillas = _construir(7, [["A", "B", 2], ["C", "D", 4], ["D", "E", 1]]);
  return [
    ["pdf_ejemplo3_A_H_dos_caminos", ejemplo, "A", "H"],
    ["pdf_ejemplo3_A_G", ejemplo, "A", "G"],
    ["pdf_ejemplo3_origen_igual_destino", ejemplo, "D", "D"],
    ["pdf_ejemplo3_destino_inalcanzable_desde_D", ejemplo, "D", "B"],
    ["pdf_ejemplo4_A_H", ejemplo4, "A", "H"],
    ["cadena_lineal_A_G", cadena, "A", "G"],
    ["cadena_origen_intermedio", cadena, "C", "F"],
    ["reemplazo_de_etiqueta", reemplazo, "A", "B"],
    ["empate_en_la_seleccion", empateSel, "A", "E"],
    ["origen_aislado_origen_igual_destino", aislado, "G", "G"],
    ["destino_aislado_inalcanzable", aislado, "A", "G"],
    ["pesos_extremos_1_y_99", pesosExtremos, "A", "D"],
    ["dos_componentes_inalcanzable", dosOrillas, "A", "E"],
    ["dos_componentes_alcanzable", dosOrillas, "C", "E"],
    ["rombos_2_etapas_n7_4_caminos", _rombos(2), "A", "G"],
    ["rombos_4_etapas_n13_16_caminos", _rombos(4), "A", "M"],
    ["rombos_5_etapas_n16_32_caminos", _rombos(5), "A", "P"],
  ];
}

/** Semillas de los casos aleatorios del golden (mismas que `core.golden.casos_aleatorios`). */
export const SEMILLAS_GOLDEN = {
  generado: (n) => 1000 * n + 1,
  didactico: (n) => 7000 + n,
};

/** Grafos generados con semillas fijas; el generador de azar reproduce el de Python. */
export function casosAleatorios() {
  const salida = [];
  for (const n of [7, 8, 9, 10, 12, 14, 16]) {
    const [g, o, d] = generarDag(n, { rng: new AzarPython(SEMILLAS_GOLDEN.generado(n)) });
    salida.push([`generado_n${n}`, g, o, d]);
  }
  for (const n of [7, 10, 13, 16]) {
    const [g, o, d] = generarDagDidactico(n, { rng: new AzarPython(SEMILLAS_GOLDEN.didactico(n)) });
    salida.push([`didactico_n${n}`, g, o, d]);
  }
  // el mismo grafo con otros extremos: hacia el último vértice y con destino inalcanzable
  for (const n of [8, 12]) {
    const [g] = generarDag(n, { rng: new AzarPython(SEMILLAS_GOLDEN.generado(n)) });
    const primero = g.vertices[0];
    const ultimo = g.vertices[g.vertices.length - 1];
    salida.push([`generado_n${n}_hacia_el_ultimo_vertice`, g, primero, ultimo]);
    salida.push([`generado_n${n}_destino_antes_del_origen`, g, ultimo, primero]);
  }
  return salida;
}

export function casosValidacion() {
  const peso = [
    "1", "99", "50", " 7 ", "007", "0", "100", "-3", "", "   ", "abc", "2.5", "+5", "1_0", "٣", "５",
    "1 0", "0x10", "1e1", "99.0", "-0", "9".repeat(40),
  ];
  const nodos = [
    "7", "16", "10", " 12 ", "0007", "6", "17", "-7", "", "  ", "abc", "7.5", "+8", "1_0", "٨", "１０",
    "7 0", "0x10", "1e1",
  ];
  const salida = [];
  for (const [funcion, validar, entradas] of [
    ["validar_peso", validarPeso, peso],
    ["validar_numero_nodos", validarNumeroNodos, nodos],
  ]) {
    for (const texto of entradas) {
      let valor = null;
      let error = null;
      try {
        valor = validar(texto);
      } catch (e) {
        if (!(e instanceof GrafoError)) throw e;
        error = e.message;
      }
      salida.push({ funcion, entrada: texto, valor, error });
    }
  }
  return salida;
}

function _paralelos(k) {
  const pred = { S: [] };
  const medios = Array.from({ length: k }, (_, i) => `M${i}`);
  for (const m of medios) pred[m] = ["S"];
  pred.T = medios;
  return pred;
}

/** Límite de caminos mínimos: 499, 500 y 501 con el límite real, y casos pequeños con límite reducido. */
export function casosTruncamiento() {
  const salida = [];
  for (const [limite, ks] of [[LIMITE_CAMINOS, [499, 500, 501]], [3, [2, 3, 4]], [1, [1, 2]]]) {
    for (const k of ks) {
      const pred = _paralelos(k);
      const [caminos, truncado] = reconstruirCaminos(pred, "S", "T", limite);
      salida.push({
        nombre: `${k}_caminos_limite_${limite}`,
        limite,
        origen: "S",
        destino: "T",
        predecesores: pred,
        cantidad: caminos.length,
        truncado,
        primero: [...caminos[0]],
        ultimo: [...caminos[caminos.length - 1]],
      });
    }
  }
  return salida;
}

/** Regenera todo el contenido de `golden/dijkstra_golden.json`. */
export function construirGolden() {
  const casos = [...casosManuales(), ...casosAleatorios()].map((c) => serializarCaso(...c));
  return {
    meta: {
      formato: FORMATO,
      descripcion:
        "Casos de oro del simulador de Dijkstra generados por el motor Python. " +
        "Un port debe reproducirlos exactamente.",
      convenciones: {
        infinito: "null",
        vertices: "letras A..P en orden alfabético",
        aristas: "[origen, destino, peso]",
        etiquetas: "texto [d, V]ₙ por vértice; varios predecesores se separan con dos espacios",
        "explicacion.estilo": "titulo | texto | calculo | tabla | nota | exito | alerta",
      },
      constantes: {
        LIMITE_CAMINOS,
        PESO_MINIMO,
        PESO_MAXIMO,
        NODOS_MINIMO,
        NODOS_MAXIMO,
      },
      cantidad_casos: casos.length,
    },
    casos,
    validacion: casosValidacion(),
    truncamiento: casosTruncamiento(),
  };
}

// --------------------------------------------------------------- JSON canónico

/** JSON con claves ordenadas y sin espacios (igual que `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)`). */
export function jsonCanonico(valor) {
  if (valor === null || typeof valor !== "object") return JSON.stringify(valor);
  if (Array.isArray(valor)) return "[" + valor.map(jsonCanonico).join(",") + "]";
  const claves = Object.keys(valor).sort();
  return "{" + claves.map((k) => JSON.stringify(k) + ":" + jsonCanonico(valor[k])).join(",") + "}";
}
