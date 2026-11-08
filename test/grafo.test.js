import assert from "node:assert/strict";
import { test } from "node:test";

import { Grafo, GrafoError, validarNumeroNodos, validarPeso } from "../src/core/graph.js";

const error = (f, mensaje) => assert.throws(f, (e) => e instanceof GrafoError && (!mensaje || e.message === mensaje));

test("el grafo admite de 1 a 16 vértices con nombres A..P", () => {
  assert.deepEqual(new Grafo(7).vertices, ["A", "B", "C", "D", "E", "F", "G"]);
  assert.equal(new Grafo(16).vertices.at(-1), "P");
  error(() => new Grafo(0));
  error(() => new Grafo(17));
});

test("agregar aristas, consultar pesos y listar en orden alfabético", () => {
  const g = new Grafo(7);
  g.agregarArista("A", "C", 4);
  g.agregarArista("A", "B", 2);
  g.agregarArista("B", "C", 1);
  assert.deepEqual(g.salientes("A"), [["B", 2], ["C", 4]]);
  assert.deepEqual(g.entrantes("C"), [["A", 4], ["B", 1]]);
  assert.deepEqual(g.aristas(), [["A", "B", 2], ["A", "C", 4], ["B", "C", 1]]);
  assert.equal(g.peso("A", "C"), 4);
  assert.equal(g.cantidadAristas(), 3);
  assert.ok(g.esDag());
  assert.deepEqual(g.ordenTopologico().slice(0, 3), ["A", "B", "C"]);
});

test("se rechazan bucles, duplicados y ciclos (directos e indirectos) con los mismos mensajes", () => {
  const g = new Grafo(7);
  g.agregarArista("A", "B", 1);
  g.agregarArista("B", "C", 1);
  error(() => g.agregarArista("A", "A", 1), "Un vértice no puede conectarse consigo mismo.");
  error(() => g.agregarArista("A", "B", 3), "La arista A → B ya existe. Puede modificar su peso o eliminarla.");
  error(() => g.agregarArista("B", "A", 1), "La conexión B → A produciría un ciclo, porque ya existe un camino de A hacia B. El grafo debe ser acíclico.");
  error(() => g.agregarArista("C", "A", 1), "La conexión C → A produciría un ciclo, porque ya existe un camino de A hacia C. El grafo debe ser acíclico.");
  error(() => g.agregarArista("A", "Z", 1), "El vértice Z no pertenece al grafo.");
  assert.equal(g.cantidadAristas(), 2, "una arista rechazada no deja rastro");
  assert.ok(g.esDag());
});

test("el rechazo de un ciclo no modifica el grafo y la dirección contraria sigue siendo válida", () => {
  const g = new Grafo(7);
  g.agregarArista("A", "B", 1);
  assert.ok(g.creariaCiclo("B", "A"));
  assert.ok(!g.creariaCiclo("A", "C"));
  assert.ok(g.hayCamino("A", "B") && !g.hayCamino("B", "A") && g.hayCamino("A", "A"));
});

test("modificar y eliminar aristas", () => {
  const g = new Grafo(7);
  g.agregarArista("A", "B", 5);
  g.modificarPeso("A", "B", "9");
  assert.equal(g.peso("A", "B"), 9);
  assert.deepEqual(g.entrantes("B"), [["A", 9]]);
  error(() => g.modificarPeso("A", "B", "0"));
  error(() => g.modificarPeso("B", "A", 3), "No existe la arista B → A.");
  g.eliminarArista("A", "B");
  assert.equal(g.cantidadAristas(), 0);
  error(() => g.eliminarArista("A", "B"), "No existe la arista A → B.");
  error(() => g.peso("A", "B"), "No existe la arista A → B.");
});

test("copiar produce un grafo independiente", () => {
  const g = new Grafo(7);
  g.agregarArista("A", "B", 3);
  const c = g.copiar();
  c.agregarArista("B", "C", 1);
  assert.equal(g.cantidadAristas(), 1);
  assert.deepEqual(c.aristas(), [["A", "B", 3], ["B", "C", 1]]);
});

test("validación estricta de pesos: dígitos ASCII, rango 1..99 y mismos mensajes", () => {
  for (let p = 1; p <= 99; p++) {
    assert.equal(validarPeso(String(p)), p);
    assert.equal(validarPeso(p), p);
  }
  const mensajes = {
    "": "Debe introducir un peso.",
    "   ": "Debe introducir un peso.",
    abc: "El peso debe ser un número entero.",
    "+5": "El peso debe ser un número entero.",
    "1_0": "El peso debe ser un número entero.",
    "٣": "El peso debe ser un número entero.",
    "５": "El peso debe ser un número entero.",
    "2.5": "El peso debe ser un número entero.",
    "1e1": "El peso debe ser un número entero.",
    "0x10": "El peso debe ser un número entero.",
    " 5": "El peso debe ser un número entero.",
    "0": "El peso debe ser un entero positivo (no se admite 0 ni negativos).",
    "-3": "El peso debe ser un entero positivo (no se admite 0 ni negativos).",
    "-0": "El peso debe ser un entero positivo (no se admite 0 ni negativos).",
    "100": "El peso debe estar entre 1 y 99.",
    ["9".repeat(5000)]: "El peso debe estar entre 1 y 99.",
  };
  for (const [texto, mensaje] of Object.entries(mensajes)) error(() => validarPeso(texto), mensaje);
  assert.equal(validarPeso(" 7 "), 7);
  assert.equal(validarPeso("\t7\n"), 7);
  assert.equal(validarPeso("007"), 7);
});

test("validación estricta del número de nodos (7 a 16)", () => {
  for (let n = 7; n <= 16; n++) assert.equal(validarNumeroNodos(String(n)), n);
  for (const fuera of ["6", "17", "0", "-7", "100"]) {
    error(() => validarNumeroNodos(fuera), "El número de nodos debe estar entre 7 y 16.");
  }
  for (const raro of ["+7", "1_0", "٨", "１０", "7.5", "abc"]) {
    error(() => validarNumeroNodos(raro), "El número de nodos debe ser un número entero.");
  }
  error(() => validarNumeroNodos(""), "Debe introducir el número de nodos.");
});
