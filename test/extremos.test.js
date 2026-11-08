import assert from "node:assert/strict";
import { test } from "node:test";

import { Grafo } from "../src/core/graph.js";
import {
  analizar, aislados, fuentes, mensajeAdvertencia, saltosDesde, sugerirExtremos, sumideros,
} from "../src/core/extremos.js";

const construir = (n, aristas) => {
  const g = new Grafo(n);
  for (const [u, v, p] of aristas) g.agregarArista(u, v, p);
  return g;
};
const CONECTADO = [["A", "B", 2], ["A", "C", 4], ["B", "D", 1], ["C", "D", 3], ["D", "E", 2], ["E", "F", 1], ["F", "G", 5]];

test("una sola fuente y un solo sumidero: esa pareja", () => {
  const g = construir(7, CONECTADO);
  assert.deepEqual([fuentes(g), sumideros(g), aislados(g)], [["A"], ["G"], []]);
  assert.deepEqual(sugerirExtremos(g), ["A", "G"]);
});

test("varias opciones: pareja válida, la que más alcanza y más lejos; sin aristas: primero y último", () => {
  const g = construir(8, [["A", "C", 1], ["B", "C", 2], ["C", "D", 3], ["C", "E", 1], ["E", "F", 2]]);
  const [o, d] = sugerirExtremos(g);
  assert.ok(fuentes(g).includes(o) && sumideros(g).includes(d) && d in saltosDesde(g, o));
  assert.deepEqual([o, d], ["A", "F"]);
  assert.deepEqual(sugerirExtremos(new Grafo(7)), ["A", "G"]);
});

test("saltosDesde cuenta aristas mínimas y solo los alcanzables", () => {
  assert.deepEqual(saltosDesde(construir(7, CONECTADO), "A"), { A: 0, B: 1, C: 1, D: 2, E: 3, F: 4, G: 5 });
  assert.deepEqual(saltosDesde(construir(7, CONECTADO), "D"), { D: 0, E: 1, F: 2, G: 3 });
});

test("analizar: aislados, vértices sin alcance y destino inalcanzable", () => {
  const g = construir(7, [["A", "B", 1], ["B", "C", 2], ["D", "E", 2]]);
  const a = analizar(g, "A", "E");
  assert.deepEqual([a.aislados, a.sinAlcance, a.destinoAlcanzable, a.hayAdvertencias], [["F", "G"], ["D", "E"], false, true]);
  assert.equal(
    mensajeAdvertencia(a),
    "⚠ El destino E no es alcanzable desde el origen A: la simulación terminará sin camino.\n\n" +
      "Vértices aislados (sin ninguna conexión): F, G.\n\n" +
      "Vértices que el origen A no alcanza y no participarán en el recorrido: D, E.\n\n" +
      "Se simulará de A a E; podrás cambiarlos en la simulación.",
  );
  assert.ok(!analizar(construir(7, CONECTADO), "A", "G").hayAdvertencias);
  assert.throws(() => { a.destino = "X"; }, TypeError);
});
