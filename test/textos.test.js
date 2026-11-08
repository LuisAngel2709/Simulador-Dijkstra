import assert from "node:assert/strict";
import { test } from "node:test";

import { ejecutarDijkstra } from "../src/core/engine.js";
import { CALCULO, Explicacion, TITULO, explicar } from "../src/core/explicaciones.js";
import { Grafo } from "../src/core/graph.js";
import { ejemplosAlgoritmo } from "../src/core/tutorial.js";

const construir = (n, aristas) => {
  const g = new Grafo(n);
  for (const [u, v, p] of aristas) g.agregarArista(u, v, p);
  return g;
};
const EJEMPLO = [["A", "B", 3], ["A", "C", 1], ["B", "D", 1], ["B", "G", 5], ["C", "D", 2], ["C", "F", 5],
  ["D", "E", 4], ["D", "F", 2], ["E", "G", 2], ["E", "H", 1], ["F", "H", 3]];
const textos = (bloques) => bloques.map((b) => b.texto);

test("cada snapshot tiene explicación breve y extendida y los bloques son inmutables", () => {
  const g = construir(8, EJEMPLO);
  const r = ejecutarDijkstra(g, "A", "H");
  r.snapshots.forEach((s, i) => {
    const e = explicar(g, r, i);
    assert.equal(e.titulo, s.titulo);
    assert.ok(e.breve.length > 0 && e.detalle.length >= e.breve.length - 2);
    assert.ok(e.breve.every((b) => b.estilo && b.texto));
    assert.throws(() => { e.breve[0].texto = "x"; }, TypeError);
  });
  assert.equal(explicar(g, r, 0).subtitulo, "Etiquetado inicial");
  assert.equal(explicar(g, r, 1).subtitulo, "Subpaso 1 · Selección");
  assert.equal(explicar(g, r, 2).subtitulo, "Subpaso 2 · Actualización");
  assert.equal(explicar(g, r, r.snapshots.length - 1).subtitulo, "Fin de la simulación");
});

test("explicación de una actualización con empate y con reemplazo", () => {
  const g = construir(8, EJEMPLO);
  const r = ejecutarDijkstra(g, "A", "H");
  const todo = r.snapshots.map((_, i) => Explicacion.textoPlano(explicar(g, r, i).detalle)).join("\n");
  assert.match(todo, /8 es igual a la distancia actual de H \(8\)\. No hay un recorrido mejor/);
  assert.match(todo, /La etiqueta anterior \[6, C\]₂ se descarta \(aparece tachada\)/);
  const h = r.snapshots.findIndex((s) => s.seleccionado === "F" && s.subpaso === "actualizacion");
  assert.ok(textos(explicar(g, r, h).breve).some((t) => t.includes("F → H: 5 + 3 = 8")));
});

test("el final distingue camino único, varios caminos, inalcanzable y origen = destino", () => {
  const g = construir(8, EJEMPLO);
  const dos = ejecutarDijkstra(g, "A", "H");
  const ult = (r, gr = g) => explicar(gr, r, r.snapshots.length - 1);
  assert.ok(textos(ult(dos).breve).join(" ").includes("cada camino mínimo"));
  assert.ok(textos(ult(dos).detalle).some((t) => t.startsWith("Existen 2 caminos mínimos distintos")));
  const unico = ejecutarDijkstra(g, "A", "B");
  assert.ok(textos(ult(unico).detalle).some((t) => t.includes("el camino mínimo es único")));
  assert.ok(textos(ult(ejecutarDijkstra(g, "D", "B")).breve).includes("Por qué no hay camino"));
  assert.equal(textos(ult(ejecutarDijkstra(g, "D", "D")).breve)[0], "Origen y destino coinciden");
  assert.equal(textos(explicar(g, ejecutarDijkstra(g, "D", "D"), 0).breve)[2], "Origen y destino coinciden");
});

test("la tabla de estado de «Más detalles» usa columnas alineadas", () => {
  const g = construir(8, EJEMPLO);
  const r = ejecutarDijkstra(g, "A", "H");
  const filas = explicar(g, r, 0).detalle.filter((b) => b.estilo === "tabla").map((b) => b.texto);
  assert.equal(filas[0], "Vértice Distancia  Predecesor   Estado");
  assert.equal(filas[1], "A       0          -            pendiente");
  assert.equal(filas[2], "B       ∞          -            sin alcanzar");
});

test("ejemplos del tutorial para un grafo con empates, sin empates, inalcanzable y origen = destino", () => {
  const g = construir(8, EJEMPLO);
  const e = ejemplosAlgoritmo(g, ejecutarDijkstra(g, "A", "H"));
  assert.match(e.provisionales, /^Al empezar, A tiene \[0, -\]₀ y los otros 7 vértices están en ∞\. Tras examinar las aristas de A, reciben una distancia provisional: B \(3\), C \(1\)\./);
  assert.match(e.seleccion, /^Iteración 2\. Candidatos con su distancia: C \(1\), B \(3\)\. Elige C,/);
  assert.match(e.actualizacion, /^Iteración \d+, desde \w:\n/);
  assert.match(e.empates, /^Iteración \d+, desde \w:\n.*= /s);
  assert.match(e.camino, /^La etiqueta de H es \[8, F\]₅  \[8, E\]₆\. Siguiendo los predecesores hacia atrás desde H hasta A se obtiene:\nA → C → D → F → H = 1 \+ 2 \+ 2 \+ 3 = 8/);

  const lineal = construir(7, [["A", "B", 1], ["B", "C", 2]]);
  const sin = ejemplosAlgoritmo(lineal, ejecutarDijkstra(lineal, "A", "C"));
  assert.match(sin.empates, /^En tu grafo no se produce ningún empate/);

  const inalc = ejemplosAlgoritmo(g, ejecutarDijkstra(g, "D", "B"));
  assert.match(inalc.camino, /^En tu grafo B no es alcanzable desde D/);

  const igual = ejemplosAlgoritmo(g, ejecutarDijkstra(g, "D", "D"));
  for (const campo of [igual.provisionales, igual.seleccion, igual.actualizacion, igual.camino]) assert.match(campo, /coinciden/);
  assert.throws(() => { igual.camino = ""; }, TypeError);
});

test("«(y N aristas más)» cuando una actualización tiene más de tres aristas", () => {
  const g = construir(7, [["A", "B", 1], ["A", "C", 2], ["A", "D", 3], ["A", "E", 4], ["A", "F", 5], ["B", "G", 1]]);
  const e = ejemplosAlgoritmo(g, ejecutarDijkstra(g, "A", "G"));
  assert.match(e.actualizacion, /\(y 2 aristas más\)$/);
});
