// Equivalencia con los casos de oro generados por el motor Python v1.13.
import assert from "node:assert/strict";
import { test } from "node:test";

import { INFINITO, ejecutarDijkstra } from "../src/core/engine.js";
import {
  casosAleatorios,
  casosManuales,
  construirGolden,
  grafoDesdeJson,
  reproducirCaso,
  serializarCaso,
} from "../src/core/golden.js";
import { reconstruirCaminos } from "../src/core/engine.js";
import { GrafoError, validarNumeroNodos, validarPeso } from "../src/core/graph.js";
import { existsSync, readFileSync } from "node:fs";
import { RAIZ, RUTA_GOLDEN, cargarGolden } from "./ayuda.js";

const golden = cargarGolden();

test("el golden tiene los 32 casos esperados", () => {
  assert.equal(golden.casos.length, 32);
  assert.equal(golden.meta.cantidad_casos, 32);
  assert.equal(golden.meta.formato, 1);
});

for (const caso of golden.casos) {
  test(`caso «${caso.nombre}»: el motor JS reproduce todo lo que produjo Python`, () => {
    const obtenido = reproducirCaso(caso);
    // Se comparan por partes para que un fallo indique exactamente dónde difiere.
    assert.deepStrictEqual(obtenido.grafo, caso.grafo, "grafo");
    assert.deepStrictEqual(obtenido.resultado, caso.resultado, "resultado");
    assert.equal(obtenido.snapshots.length, caso.snapshots.length, "cantidad de snapshots");
    caso.snapshots.forEach((esperado, i) => {
      const real = obtenido.snapshots[i];
      for (const campo of Object.keys(esperado)) {
        if (campo === "tabla" || campo === "explicacion") continue;
        assert.deepStrictEqual(real[campo], esperado[campo], `snapshot ${i}: ${campo}`);
      }
      assert.deepStrictEqual(real.tabla, esperado.tabla, `snapshot ${i}: tabla`);
      assert.deepStrictEqual(real.explicacion.titulo, esperado.explicacion.titulo, `snapshot ${i}: título`);
      assert.deepStrictEqual(real.explicacion.subtitulo, esperado.explicacion.subtitulo, `snapshot ${i}: subtítulo`);
      assert.deepStrictEqual(real.explicacion.breve, esperado.explicacion.breve, `snapshot ${i}: explicación breve`);
      assert.deepStrictEqual(real.explicacion.detalle, esperado.explicacion.detalle, `snapshot ${i}: explicación extendida`);
    });
    assert.deepStrictEqual(obtenido.tutorial, caso.tutorial, "ejemplos del tutorial");
    assert.deepStrictEqual(obtenido.extremos, caso.extremos, "extremos y advertencias");
    assert.deepStrictEqual(obtenido, caso, "caso completo");
  });
}

test("los casos manuales se regeneran idénticos desde el código JS", () => {
  const guardados = new Map(golden.casos.map((c) => [c.nombre, c]));
  for (const [nombre, g, o, d] of casosManuales()) {
    assert.deepStrictEqual(serializarCaso(nombre, g, o, d), guardados.get(nombre), nombre);
  }
});

test("el generador JS (con el azar compatible de Python) produce los mismos grafos que Python", () => {
  const guardados = new Map(golden.casos.map((c) => [c.nombre, c]));
  const casos = casosAleatorios();
  assert.equal(casos.length, 15);
  for (const [nombre, g, o, d] of casos) {
    const esperado = guardados.get(nombre);
    assert.ok(esperado, `falta ${nombre} en el golden`);
    assert.deepStrictEqual(
      { aristas: g.aristas(), origen: o, destino: d },
      { aristas: esperado.grafo.aristas, origen: esperado.origen, destino: esperado.destino },
      nombre,
    );
  }
});

test("construirGolden() en JS es idéntico al archivo generado por Python", () => {
  assert.deepStrictEqual(construirGolden(), golden);
});

test("la validación guardada coincide con las funciones JS", () => {
  const funciones = { validar_peso: validarPeso, validar_numero_nodos: validarNumeroNodos };
  assert.ok(golden.validacion.length > 30);
  for (const c of golden.validacion) {
    let valor = null;
    let error = null;
    try {
      valor = funciones[c.funcion](c.entrada);
    } catch (e) {
      assert.ok(e instanceof GrafoError);
      error = e.message;
    }
    assert.deepStrictEqual({ valor, error }, { valor: c.valor, error: c.error }, JSON.stringify(c));
  }
});

test("el truncamiento guardado (499, 500, 501 y límites pequeños) coincide", () => {
  const resumen = Object.fromEntries(golden.truncamiento.map((c) => [c.nombre, [c.cantidad, c.truncado]]));
  assert.deepStrictEqual(resumen["499_caminos_limite_500"], [499, false]);
  assert.deepStrictEqual(resumen["500_caminos_limite_500"], [500, false]);
  assert.deepStrictEqual(resumen["501_caminos_limite_500"], [500, true]);
  for (const c of golden.truncamiento) {
    const [caminos, truncado] = reconstruirCaminos(c.predecesores, c.origen, c.destino, c.limite);
    assert.deepStrictEqual([caminos.length, truncado], [c.cantidad, c.truncado], c.nombre);
    assert.deepStrictEqual([caminos[0], caminos[caminos.length - 1]], [c.primero, c.ultimo], c.nombre);
  }
});

test("coherencia interna del golden: caminos válidos, snapshots ordenados e ∞ como null", () => {
  for (const x of golden.casos) {
    const g = grafoDesdeJson(x.grafo);
    const r = ejecutarDijkstra(g, x.origen, x.destino);
    assert.equal(r.alcanzable, x.resultado.alcanzable, x.nombre);
    assert.equal(r.distancia === INFINITO ? null : r.distancia, x.resultado.distancia, x.nombre);
    assert.equal(r.snapshots.length, x.snapshots.length, x.nombre);
  }
});

test("la copia local del golden es idéntica byte a byte a la de la versión Python (si está al lado)", (t) => {
  const original = `${RAIZ}/../simulador_dijkstra/golden/dijkstra_golden.json`;
  if (!existsSync(original)) return t.skip("no está la carpeta de la versión Python junto a esta");
  assert.ok(readFileSync(original).equals(readFileSync(RUTA_GOLDEN)), "golden/dijkstra_golden.json difiere del de Python");
});
