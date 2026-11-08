// 720 casos extra generados por Python (hash SHA-256 de la serialización completa) + validación aleatoria.
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { AzarPython } from "../src/core/azar.js";
import { grafoDesdeJson, jsonCanonico, serializarCaso } from "../src/core/golden.js";
import { generarDag, generarDagDidactico } from "../src/core/generador.js";
import { GrafoError, validarNumeroNodos, validarPeso } from "../src/core/graph.js";
import { RAIZ } from "./ayuda.js";

const datos = JSON.parse(readFileSync(`${RAIZ}/test/fixtures/equivalencia_amplia.json`, "utf-8"));
const sha = (caso) => createHash("sha256").update(jsonCanonico(caso), "utf8").digest("hex");

test("el fixture amplio tiene 720 casos y 1200 validaciones", () => {
  assert.equal(datos.casos.length, 720);
  assert.equal(datos.validacion.length, 1200);
});

test("720 grafos: motor, tablas, explicaciones, tutorial y advertencias dan el mismo hash que Python", () => {
  const fallos = [];
  for (const c of datos.casos) {
    const g = grafoDesdeJson({ n: c.n, aristas: c.aristas });
    if (sha(serializarCaso(c.nombre, g, c.origen, c.destino)) !== c.hash) fallos.push(c.nombre);
  }
  assert.deepStrictEqual(fallos, []);
});

test("el generador JS reproduce, con la misma semilla, los 240 grafos de Python", () => {
  const vistos = new Set();
  for (const c of datos.casos) {
    const clave = `${c.tipo}_${c.n}_${c.semilla}`;
    if (vistos.has(clave)) continue;
    vistos.add(clave);
    const funcion = c.tipo === "generado" ? generarDag : generarDagDidactico;
    const [g, o, d] = funcion(c.n, { rng: new AzarPython(c.semilla) });
    assert.deepStrictEqual(
      { aristas: g.aristas(), origen: o, destino: d },
      { aristas: c.aristas, origen: c.origen_generado, destino: c.destino_generado },
      clave,
    );
  }
  assert.equal(vistos.size, 240);
});

test("1200 validaciones aleatorias (Unicode, signos, espacios…) coinciden con Python", () => {
  const funciones = { validar_peso: validarPeso, validar_numero_nodos: validarNumeroNodos };
  for (const c of datos.validacion) {
    let valor = null;
    let error = null;
    try {
      valor = funciones[c.funcion](c.entrada);
    } catch (e) {
      assert.ok(e instanceof GrafoError, e.stack);
      error = e.message;
    }
    assert.deepStrictEqual({ valor, error }, { valor: c.valor, error: c.error }, `${c.funcion}(${JSON.stringify(c.entrada)})`);
  }
});
