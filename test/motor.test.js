import assert from "node:assert/strict";
import { test } from "node:test";

import {
  ACTUALIZACION, DESCARTADA, EMPATE, FINAL, INFINITO, INICIO, LIMITE_CAMINOS, SELECCION, Simulacion, VIGENTE,
  ejecutarDijkstra, reconstruirCaminos, textoEtiqueta,
} from "../src/core/engine.js";
import { Grafo, GrafoError } from "../src/core/graph.js";

function construir(n, aristas) {
  const g = new Grafo(n);
  for (const [u, v, p] of aristas) g.agregarArista(u, v, p);
  return g;
}
const EJEMPLO = [["A", "B", 3], ["A", "C", 1], ["B", "D", 1], ["B", "G", 5], ["C", "D", 2], ["C", "F", 5],
  ["D", "E", 4], ["D", "F", 2], ["E", "G", 2], ["E", "H", 1], ["F", "H", 3]];

test("ejemplo de la Lectura 5: distancia, predecesores múltiples y dos caminos mínimos", () => {
  const r = ejecutarDijkstra(construir(8, EJEMPLO), "A", "H");
  assert.equal(r.distancia, 8);
  assert.deepEqual(r.caminos, [["A", "C", "D", "F", "H"], ["A", "C", "D", "E", "H"]]);
  assert.deepEqual(r.predecesores.H, ["F", "E"]); // predecesores múltiples en orden de descubrimiento
  assert.equal(r.cantidadCaminos, 2);
  assert.ok(r.alcanzable && !r.truncado);
});

test("dos subpasos por iteración: inicio, (selección, actualización)×k y final", () => {
  const r = ejecutarDijkstra(construir(8, EJEMPLO), "A", "H");
  const tipos = r.snapshots.map((s) => s.subpaso);
  assert.equal(tipos[0], INICIO);
  assert.equal(tipos.at(-1), FINAL);
  const medio = tipos.slice(1, -1);
  medio.forEach((t, i) => assert.equal(t, i % 2 === 0 ? SELECCION : ACTUALIZACION));
  assert.deepEqual(r.snapshots.map((s) => s.indice), r.snapshots.map((_, i) => i));
  // No se detiene al llegar al destino: se procesan todos los vértices alcanzables.
  assert.equal(medio.length, 2 * 8);
});

test("desempate alfabético en la selección", () => {
  const g = construir(7, [["A", "C", 4], ["A", "B", 4], ["B", "D", 1], ["C", "D", 1]]);
  const r = ejecutarDijkstra(g, "A", "D");
  const elegidos = r.snapshots.filter((s) => s.subpaso === SELECCION).map((s) => s.seleccionado);
  assert.deepEqual(elegidos, ["A", "B", "C", "D"]);
  assert.deepEqual(r.predecesores.D, ["B", "C"]);
});

test("reemplazo de etiqueta: la anterior queda tachada y la tabla marca el estado", () => {
  const g = construir(7, [["A", "B", 10], ["A", "C", 2], ["C", "B", 3]]);
  const r = ejecutarDijkstra(g, "A", "B");
  const act = r.snapshots.filter((s) => s.subpaso === ACTUALIZACION && s.seleccionado === "C")[0];
  assert.deepEqual(act.etiquetasDescartadas, [["B", "[10, A]₁"]]);
  const b = act.tabla.filter((e) => e.vertice === "B");
  assert.deepEqual(b.map((e) => [e.distancia, e.estado]), [[10, DESCARTADA], [5, VIGENTE]]);
  assert.equal(r.distancia, 5);
});

test("empates: etiqueta con varios predecesores y estado «empate»", () => {
  const r = ejecutarDijkstra(construir(8, EJEMPLO), "A", "H");
  const fin = r.snapshots.at(-1);
  assert.equal(fin.etiqueta("H"), "[8, F]₅  [8, E]₆");
  assert.ok(fin.tabla.some((e) => e.estado === EMPATE));
});

test("destino inalcanzable: distancia ∞, sin caminos y el resto alcanzable se procesa", () => {
  const g = construir(7, [["A", "B", 2], ["C", "D", 4]]);
  const r = ejecutarDijkstra(g, "A", "D");
  assert.equal(r.distancia, INFINITO);
  assert.ok(!r.alcanzable);
  assert.deepEqual(r.caminos, []);
  assert.equal(r.snapshots.at(-1).etiqueta("D"), "[∞, -]");
  assert.deepEqual(r.snapshots.at(-1).aristasCamino, []);
});

test("origen = destino: solo inicio y final, distancia 0 y camino de un vértice", () => {
  const r = ejecutarDijkstra(construir(8, EJEMPLO), "D", "D");
  assert.deepEqual(r.snapshots.map((s) => s.subpaso), [INICIO, FINAL]);
  assert.equal(r.distancia, 0);
  assert.deepEqual(r.caminos, [["D"]]);
  assert.equal(r.distancias.A, INFINITO);
  assert.equal(r.snapshots.at(-1).iteracion, 0);
});

test("vértice aislado como origen y destino, y como destino", () => {
  const g = construir(7, [["A", "B", 1]]);
  assert.deepEqual(ejecutarDijkstra(g, "G", "G").caminos, [["G"]]);
  assert.ok(!ejecutarDijkstra(g, "A", "G").alcanzable);
});

test("vértices inexistentes se rechazan con el mismo mensaje", () => {
  const g = construir(7, [["A", "B", 1]]);
  assert.throws(() => ejecutarDijkstra(g, "Z", "B"), (e) => e instanceof GrafoError && e.message === "El vértice origen Z no pertenece al grafo.");
  assert.throws(() => ejecutarDijkstra(g, "A", "Z"), (e) => e instanceof GrafoError && e.message === "El vértice destino Z no pertenece al grafo.");
});

test("los snapshots y el resultado son inmutables", () => {
  const r = ejecutarDijkstra(construir(8, EJEMPLO), "A", "H");
  const s = r.snapshots[3];
  assert.throws(() => { s.iteracion = 99; }, TypeError);
  assert.throws(() => { s.distancias.A = 99; }, TypeError);
  assert.throws(() => { s.predecesores.B.push("Z"); }, TypeError);
  assert.throws(() => s.visitados.add("Z"), TypeError);
  assert.throws(() => { r.snapshots.push(null); }, TypeError);
  assert.throws(() => { r.distancia = 0; }, TypeError);
  assert.throws(() => { s.tabla[0].distancia = 1; }, TypeError);
});

test("el motor no modifica el grafo y dos ejecuciones dan lo mismo", () => {
  const g = construir(8, EJEMPLO);
  const antes = JSON.stringify(g.aristas());
  const a = ejecutarDijkstra(g, "A", "H");
  const b = ejecutarDijkstra(g, "A", "H");
  assert.equal(JSON.stringify(g.aristas()), antes);
  assert.deepEqual(JSON.parse(JSON.stringify(a)), JSON.parse(JSON.stringify(b)));
});

test("textoEtiqueta: ∞, origen, un predecesor, varios y subíndices por predecesor", () => {
  assert.equal(textoEtiqueta(INFINITO, [], null), "[∞, -]");
  assert.equal(textoEtiqueta(0, [], 0), "[0, -]₀");
  assert.equal(textoEtiqueta(5, ["A"], 12), "[5, A]₁₂");
  assert.equal(textoEtiqueta(5, ["B", "C"], { B: 2, C: 3 }), "[5, B]₂  [5, C]₃");
  assert.equal(textoEtiqueta(5, ["B", "C"], 4), "[5, B]₄  [5, C]₄");
  assert.equal(textoEtiqueta(5, ["B"], null), "[5, B]");
});

test("Simulacion: avanzar, retroceder, reiniciar y finalizar sin salirse del rango", () => {
  const r = ejecutarDijkstra(construir(8, EJEMPLO), "A", "H");
  const sim = new Simulacion(r);
  assert.ok(!sim.puedeRetroceder && sim.puedeAvanzar);
  sim.anterior();
  assert.equal(sim.indice, 0);
  sim.siguiente();
  sim.siguiente();
  assert.equal(sim.indice, 2);
  sim.anterior();
  assert.equal(sim.indice, 1);
  assert.equal(sim.finalizar().esFinal, true);
  assert.ok(!sim.puedeAvanzar);
  sim.siguiente();
  assert.equal(sim.indice, sim.total - 1);
  assert.equal(sim.reiniciar().subpaso, INICIO);
});

// ----------------------------------------------------------------- truncamiento

const paralelos = (k) => {
  const pred = { S: [] };
  const medios = Array.from({ length: k }, (_, i) => `M${i}`);
  for (const m of medios) pred[m] = ["S"];
  pred.T = medios;
  return pred;
};
const diamantes = (etapas) => {
  const pred = { S: [] };
  let anterior = "S";
  for (let e = 0; e < etapas; e++) {
    const fin = e === etapas - 1 ? "T" : `j${e}`;
    pred[`a${e}`] = [anterior];
    pred[`b${e}`] = [anterior];
    pred[fin] = [`a${e}`, `b${e}`];
    anterior = fin;
  }
  return pred;
};

test("límite de caminos: 499 y 500 no truncan; 501 trunca y devuelve 500", () => {
  assert.equal(LIMITE_CAMINOS, 500);
  for (const [k, esperado, trunca] of [[499, 499, false], [500, 500, false], [501, 500, true], [2000, 500, true]]) {
    const [caminos, truncado] = reconstruirCaminos(paralelos(k), "S", "T");
    assert.deepEqual([caminos.length, truncado], [esperado, trunca], `k=${k}`);
    assert.equal(new Set(caminos.map((c) => c.join())).size, caminos.length);
  }
  const [caminos] = reconstruirCaminos(paralelos(501), "S", "T");
  assert.deepEqual([caminos[0], caminos.at(-1)], [["S", "M0", "T"], ["S", "M499", "T"]]);
});

test("límite parametrizado y truncamiento en vértices intermedios", () => {
  for (const k of [1, 2, 7, 162]) {
    assert.deepEqual(reconstruirCaminos(paralelos(k), "S", "T", k).slice(1), [false]);
    assert.deepEqual(reconstruirCaminos(paralelos(k), "S", "T", k - 1).slice(1), [true]);
    assert.deepEqual(reconstruirCaminos(paralelos(k), "S", "T", k + 1).slice(1), [false]);
  }
  assert.deepEqual(reconstruirCaminos(diamantes(9), "S", "T").map((x, i) => (i ? x : x.length)), [500, true]);
  assert.deepEqual(reconstruirCaminos(diamantes(8), "S", "T").map((x, i) => (i ? x : x.length)), [256, false]);
  assert.deepEqual(reconstruirCaminos({ S: [] }, "S", "S", 1), [[["S"]], false]);
});
