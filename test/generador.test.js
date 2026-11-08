import assert from "node:assert/strict";
import { test } from "node:test";

import { AzarPython } from "../src/core/azar.js";
import { ejecutarDijkstra } from "../src/core/engine.js";
import { generarDag, generarDagDidactico } from "../src/core/generador.js";
import { pesosValidos } from "../src/core/graph.js";
import { saltosDesde } from "../src/core/extremos.js";

test("AzarPython coincide con random.Random de CPython (valores calculados con Python 3.12/3.13)", () => {
  const a = new AzarPython(12345);
  assert.equal(a.random(), 0.41661987254534116);
  assert.equal(a.randint(1, 9), 1);
  assert.equal(a.getrandbits(5), 26);
  const lista = [1, 2, 3, 4, 5, 6, 7, 8];
  a.shuffle(lista);
  assert.deepEqual(lista, [1, 8, 4, 6, 2, 3, 7, 5]);
  assert.equal(a.choice([2, 3, 3, 4]), 3);
  // semillas grandes (varios trozos de 32 bits) y cero
  assert.equal(new AzarPython(0).random(), 0.8444218515250481);
  assert.equal(new AzarPython(42).random(), 0.6394267984578837);
});

test("la misma semilla da el mismo grafo y semillas distintas casi siempre dan grafos distintos", () => {
  const a = generarDag(12, { rng: new AzarPython(5) });
  const b = generarDag(12, { rng: new AzarPython(5) });
  assert.deepEqual([a[0].aristas(), a[1], a[2]], [b[0].aristas(), b[1], b[2]]);
  const distintos = new Set(Array.from({ length: 20 }, (_, s) => JSON.stringify(generarDag(12, { rng: new AzarPython(s) })[0].aristas())));
  assert.ok(distintos.size > 15);
});

test("DAG válido, pesos 1..9, sin repetidos y todo vértice alcanzable desde el origen (n = 7..16)", () => {
  for (let n = 7; n <= 16; n++) {
    for (let semilla = 0; semilla < 40; semilla++) {
      const [g, o, d] = generarDag(n, { rng: new AzarPython(semilla * 31 + n) });
      assert.ok(g.esDag(), `n=${n} s=${semilla}`);
      assert.ok(pesosValidos(g) && g.aristas().every(([, , p]) => p >= 1 && p <= 9));
      assert.equal(Object.keys(saltosDesde(g, o)).length, n, "todo vértice alcanzable desde el origen");
      assert.ok(g.hayCamino(o, d));
      assert.equal(g.entrantes(o).length, 0);
      assert.equal(g.salientes(d).length, 0);
    }
  }
});

test("parámetros inválidos y valores por defecto", () => {
  assert.throws(() => generarDag(2), RangeError);
  assert.throws(() => generarDag(8, { pesoMaximo: 100 }), RangeError);
  assert.throws(() => generarDag(8, { pesoMaximo: 0 }), RangeError);
  const [g] = generarDag(8); // sin semilla: usa el azar del sistema
  assert.ok(g.esDag());
});

test("el generador didáctico prefiere grafos con varios caminos mínimos", () => {
  let con = 0;
  for (let s = 0; s < 20; s++) {
    const [g, o, d] = generarDagDidactico(10, { rng: new AzarPython(s) });
    if (ejecutarDijkstra(g, o, d).cantidadCaminos >= 2) con += 1;
  }
  assert.ok(con >= 15, `solo ${con}/20 con empate`);
});
