// Pruebas de interfaz con Playwright (Chromium). Se ejecutan con: npm run test:ui
// No hace falta servidor externo: este archivo levanta uno estático propio.
import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { after, before, describe, test } from "node:test";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = require("playwright"));
} catch {
  // Playwright instalado globalmente: se busca en NODE_PATH.
  const dir = (process.env.NODE_PATH || "/usr/local/lib/node_modules_global").split(path.delimiter)[0];
  ({ chromium } = require(path.join(dir, "playwright")));
}

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TIPOS = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json" };
let servidor, URL_BASE, navegador;

before(async () => {
  servidor = http.createServer((q, r) => {
    let p = path.join(RAIZ, decodeURIComponent(q.url.split("?")[0]));
    if (p.endsWith(path.sep)) p += "index.html";
    fs.readFile(p, (e, d) => {
      if (e) { r.writeHead(404); r.end("404"); return; }
      r.writeHead(200, { "Content-Type": TIPOS[path.extname(p)] || "application/octet-stream" });
      r.end(d);
    });
  });
  await new Promise((ok) => servidor.listen(0, ok));
  URL_BASE = `http://localhost:${servidor.address().port}/`;
  navegador = await chromium.launch();
});
after(async () => { await navegador?.close(); servidor?.close(); });

async function abrir({ ancho = 1320, alto = 860, tema, tactil = false } = {}) {
  const ctx = await navegador.newContext({ viewport: { width: ancho, height: alto }, colorScheme: tema ?? "light", ...(tactil ? { hasTouch: true, isMobile: true } : {}) });
  const p = await ctx.newPage();
  p.errores = [];
  p.on("console", (m) => { if (["error", "warning"].includes(m.type())) p.errores.push(`${m.type()}: ${m.text()}`); });
  p.on("pageerror", (e) => p.errores.push(`pageerror: ${e.message}`));
  p.on("requestfailed", (r) => p.errores.push(`requestfailed: ${r.url()}`));
  await p.goto(URL_BASE);
  await p.waitForSelector("[data-pantalla=bienvenida]");
  p.cerrar = () => ctx.close();
  p.ctx = ctx;
  return p;
}
const t = (id) => `[data-testid="${id}"]`;
const texto = (p, id) => p.locator(t(id)).innerText();

async function aConfig(p, n = 8) {
  await p.click(t("empezar"));
  await p.selectOption(t("num-nodos"), String(n));
}
async function aEditor(p, n = 7) {
  await aConfig(p, n);
  await p.click(t("manual"));
  await p.waitForSelector("[data-pantalla=editor]");
}
async function conectar(p, u, v, peso) {
  await p.click(`.nodo[data-v="${u}"]`);
  await p.click(`.nodo[data-v="${v}"]`);
  await p.fill(t("peso-nuevo"), String(peso));
  await p.click(t("crear-conexion"));
}
async function aSimulacionAuto(p, n = 8) {
  await aConfig(p, n);
  await p.click(t("generar"));
  await p.waitForSelector("[data-pantalla=simulacion]");
  await p.waitForTimeout(350); // termina la animación de entrada (con ella en curso Playwright puede desplazar la página para acertar el clic)
}

/** Mide solapes entre rótulos, pesos, marcas y vértices del grafo visible. */
async function medirSolapes(p) {
  return p.evaluate(() => {
    const svg = document.querySelector("[data-pantalla] .grafo-svg");
    const R = (e) => { const r = e.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom }; };
    const items = [];
    svg.querySelectorAll(".peso").forEach((g) => items.push(["peso " + g.dataset.peso, R(g.querySelector("rect"))]));
    svg.querySelectorAll(".marca").forEach((g) => items.push(["marca " + g.dataset.marca, R(g.querySelector("rect"))]));
    svg.querySelectorAll(".etiqueta").forEach((g) => {
      const rs = [...g.querySelectorAll("text")].map(R);
      items.push(["etiqueta " + g.dataset.etiqueta, { l: Math.min(...rs.map((r) => r.l)), t: Math.min(...rs.map((r) => r.t)), r: Math.max(...rs.map((r) => r.r)), b: Math.max(...rs.map((r) => r.b)) }]);
    });
    const nodos = [...svg.querySelectorAll(".nodo")].map((g) => { const r = g.querySelector("circle").getBoundingClientRect(); return [g.dataset.v, (r.left + r.right) / 2, (r.top + r.bottom) / 2, r.width / 2]; });
    const malos = [];
    for (let i = 0; i < items.length; i++) {
      for (let j = i + 1; j < items.length; j++) {
        const a = items[i][1], b = items[j][1];
        if (a.l < b.r && a.r > b.l && a.t < b.b && a.b > b.t) malos.push([items[i][0], items[j][0]]);
      }
      const a = items[i][1];
      for (const [v, cx, cy, rad] of nodos) {
        const dx = Math.max(a.l - cx, 0, cx - a.r), dy = Math.max(a.t - cy, 0, cy - a.b);
        if (dx * dx + dy * dy < rad * rad) malos.push([items[i][0], "nodo " + v]);
      }
      const s = svg.getBoundingClientRect();
      if (a.l < s.left - 1 || a.r > s.right + 1 || a.t < s.top - 1 || a.b > s.bottom + 1) malos.push([items[i][0], "fuera del lienzo"]);
    }
    return malos;
  });
}

describe("flujo general y consola", () => {
  test("bienvenida → configuración → generar → simular, sin errores de consola", async () => {
    const p = await abrir();
    assert.match(await texto(p, "empezar"), /EMPEZAR SIMULACIÓN/);
    await aSimulacionAuto(p, 9);
    assert.match(await texto(p, "ruta"), /Camino mínimo:\s+\w → \w/);
    await p.click(t("ejecutar"));
    for (let i = 0; i < 4; i++) await p.click(t("siguiente"));
    await p.click(t("ir-al-final"));
    assert.match(await texto(p, "resultado"), /Distancia mínima: \d+/);
    assert.deepEqual(p.errores, []);
    await p.cerrar();
  });

  test("el selector de nodos ofrece 7..16 y por defecto 8", async () => {
    const p = await abrir();
    await p.click(t("empezar"));
    const valores = await p.$$eval(`${t("num-nodos")} option`, (o) => o.map((x) => x.value));
    assert.deepEqual(valores, ["7", "8", "9", "10", "11", "12", "13", "14", "15", "16"]);
    assert.equal(await p.inputValue(t("num-nodos")), "8");
    await p.cerrar();
  });
});

describe("editor manual", () => {
  test("crea aristas y rechaza ciclos, duplicados, bucles y pesos inválidos", async () => {
    const p = await abrir();
    await aEditor(p, 7);
    await conectar(p, "A", "B", 5);
    assert.match(await texto(p, "editor-mensaje"), /Conexión creada: A → B \(peso 5\)/);
    await conectar(p, "B", "C", 3);
    // ciclo C → A
    await conectar(p, "C", "A", 2);
    assert.match(await texto(p, "editor-mensaje"), /ciclo/i);
    // duplicado A → B (el editor la rechaza)
    await p.click(t("cancelar-seleccion"));
    await conectar(p, "A", "B", 4);
    assert.match(await texto(p, "editor-mensaje"), /existe|duplic|ya/i);
    // peso inválido
    await p.click(t("cancelar-seleccion"));
    for (const malo of ["0", "100", "abc", "", "2.5", "-3"]) {
      await p.click('.nodo[data-v="A"]'); await p.click('.nodo[data-v="D"]');
      await p.fill(t("peso-nuevo"), malo);
      await p.click(t("crear-conexion"));
      assert.equal(await p.locator(`${t("editor-mensaje")}.mensaje--error`).count(), 1, `peso «${malo}» debe rechazarse`);
      await p.click(t("cancelar-seleccion"));
    }
    // bucle
    await p.click('.nodo[data-v="A"]'); await p.click('.nodo[data-v="A"]');
    assert.match(await texto(p, "editor-mensaje"), /consigo mismo/);
    assert.equal(await p.locator(`${t("lista-aristas")} .arista-fila`).count(), 2);
    assert.deepEqual(p.errores, []);
    await p.cerrar();
  });

  test("Enter crea la conexión y Esc cancela la selección", async () => {
    const p = await abrir();
    await aEditor(p);
    await p.click('.nodo[data-v="A"]'); await p.click('.nodo[data-v="B"]');
    assert.match(await texto(p, "seleccion"), /Origen: A\s+Destino: B/);
    await p.fill(t("peso-nuevo"), "7"); await p.press(t("peso-nuevo"), "Enter");
    assert.equal(await p.locator(".arista-fila").count(), 1);
    await p.click('.nodo[data-v="C"]');
    await p.keyboard.press("Escape");
    assert.match(await texto(p, "seleccion"), /Origen: —/);
    await p.cerrar();
  });

  test("edición del peso en línea: confirma con Enter, mantiene abierto si es inválido, cancela con Esc", async () => {
    const p = await abrir();
    await aEditor(p);
    await conectar(p, "A", "B", 5);
    await p.click('[data-peso="A>B"]');
    await p.waitForSelector(t("peso-editor"));
    await p.fill(t("peso-editor"), "0"); await p.press(t("peso-editor"), "Enter");
    assert.equal(await p.locator(t("peso-editor")).count(), 1, "sigue abierto");
    assert.equal(await p.locator(`${t("peso-editor")}.peso-editor--error`).count(), 1);
    await p.fill(t("peso-editor"), "42"); await p.press(t("peso-editor"), "Enter");
    assert.equal(await p.locator(t("peso-editor")).count(), 0);
    assert.match(await texto(p, "lista-aristas"), /A → B\s+peso 42/);
    assert.equal((await p.locator('[data-peso="A>B"] text').textContent()).trim(), "42");
    await p.click('[data-peso="A>B"]'); await p.fill(t("peso-editor"), "9"); await p.press(t("peso-editor"), "Escape");
    assert.match(await texto(p, "lista-aristas"), /peso 42/);
    // botón «Peso» de la lista y «Eliminar»
    await p.click('[data-fila="A>B"] [data-accion="peso"]');
    await p.fill(t("peso-editor"), "8"); await p.press(t("peso-editor"), "Enter");
    assert.match(await texto(p, "lista-aristas"), /peso 8/);
    await p.click('[data-fila="A>B"] [data-accion="eliminar"]');
    assert.match(await texto(p, "lista-aristas"), /Todavía no hay aristas/);
    assert.deepEqual(p.errores, []);
    await p.cerrar();
  });

  test("finalizar sin aristas da error; con vértices aislados avisa y permite continuar o volver", async () => {
    const p = await abrir();
    await aEditor(p, 7);
    await p.click(t("finalizar-grafo"));
    assert.match(await texto(p, "editor-mensaje"), /no tiene conexiones/);
    await conectar(p, "A", "B", 3);
    await p.click(t("finalizar-grafo"));
    const dlg = await texto(p, "dialogo");
    assert.match(dlg, /Revisa tu grafo antes de simular/);
    assert.match(dlg, /aislados/);
    await p.click(t("dialogo-cancelar"));
    assert.equal(await p.locator("[data-pantalla=editor]").count(), 1);
    await p.click(t("finalizar-grafo"));
    await p.click(t("dialogo-confirmar"));
    await p.waitForSelector("[data-pantalla=simulacion]");
    assert.equal((await p.locator(t("sim-volver")).innerText()).trim(), "Editar grafo");
    await p.cerrar();
  });

  test("grafo sin advertencias pasa directo a la simulación", async () => {
    const p = await abrir();
    await aEditor(p, 7);
    const cadena = ["A", "B", "C", "D", "E", "F", "G"];
    for (let i = 0; i < 6; i++) await conectar(p, cadena[i], cadena[i + 1], i + 1);
    await p.click(t("finalizar-grafo"));
    await p.waitForSelector("[data-pantalla=simulacion]");
    assert.equal(await p.inputValue(t("origen")), "A");
    assert.equal(await p.inputValue(t("destino")), "G");
    await p.cerrar();
  });

  test("arrastrar vértices conserva posiciones al ir a la simulación y volver al editor", async () => {
    const p = await abrir();
    await aEditor(p, 7);
    const cadena = ["A", "B", "C", "D", "E", "F", "G"];
    for (let i = 0; i < 6; i++) await conectar(p, cadena[i], cadena[i + 1], 2);
    const centro = async (v) => { const b = await p.locator(`.nodo[data-v="${v}"] circle`).boundingBox(); return [b.x + b.width / 2, b.y + b.height / 2]; };
    const [x0, y0] = await centro("C");
    await p.mouse.move(x0, y0); await p.mouse.down(); await p.mouse.move(x0 - 50, y0 - 30, { steps: 6 }); await p.mouse.up();
    const [x1, y1] = await centro("C");
    assert.ok(Math.abs(x1 - (x0 - 50)) < 3 && Math.abs(y1 - (y0 - 30)) < 3, `arrastre: ${x1},${y1}`);
    assert.equal(await p.locator(".nodo--seleccion").count(), 0, "arrastrar no es seleccionar");
    const pos = await p.evaluate(() => window.__dijkstra.pantalla.posiciones().C);
    await p.click(t("finalizar-grafo"));
    await p.waitForSelector("[data-pantalla=simulacion]");
    await p.click(t("sim-volver"));
    await p.waitForSelector("[data-pantalla=editor]");
    const pos2 = await p.evaluate(() => window.__dijkstra.pantalla.posiciones().C);
    assert.deepEqual(pos2.map(Math.round), pos.map(Math.round));
    // Restablecer vuelve al círculo
    await p.click(t("editor-restablecer"));
    const pos3 = await p.evaluate(() => window.__dijkstra.pantalla.posiciones().C);
    assert.notDeepEqual(pos3.map(Math.round), pos.map(Math.round));
    assert.deepEqual(p.errores, []);
    await p.cerrar();
  });

  test("volver del editor con aristas pide confirmación; sin aristas vuelve directo", async () => {
    const p = await abrir();
    await aEditor(p);
    await p.click(t("editor-volver"));
    await p.waitForSelector("[data-pantalla=configuracion]");
    await p.click(t("manual"));
    await conectar(p, "A", "B", 1);
    await p.click(t("editor-volver"));
    assert.match(await texto(p, "dialogo"), /¿Descartar grafo\?/);
    await p.click(t("dialogo-cancelar"));
    assert.equal(await p.locator("[data-pantalla=editor]").count(), 1);
    await p.click(t("editor-volver")); await p.click(t("dialogo-confirmar"));
    await p.waitForSelector("[data-pantalla=configuracion]");
    await p.cerrar();
  });
});

describe("simulación", () => {
  async function grafoPropio(p, aristas, n, origen, destino) {
    await p.evaluate(async ({ aristas, n, origen, destino }) => {
      const core = await import("./src/core/index.js");
      const g = new core.Grafo(n);
      for (const [u, v, w] of aristas) g.agregarArista(u, v, w);
      window.__dijkstra.irASimulacion(g, null, [origen, destino], "← Configuración");
    }, { aristas, n, origen, destino });
    await p.waitForSelector("[data-pantalla=simulacion]");
  }
  const DIAMANTE = [["A", "B", 1], ["A", "C", 1], ["B", "D", 2], ["C", "D", 2], ["D", "E", 1], ["B", "E", 5], ["E", "F", 1], ["D", "G", 4]];

  test("botones deshabilitados antes de ejecutar y cambio de extremos invalida la simulación", async () => {
    const p = await abrir();
    await grafoPropio(p, DIAMANTE, 7, "A", "F");
    for (const id of ["anterior", "siguiente", "reiniciar", "ir-al-final", "mas-detalles"]) assert.equal(await p.locator(t(id)).isDisabled(), true, id);
    assert.match(await texto(p, "titulo-paso"), /Simulación no iniciada/);
    await p.click(t("ejecutar"));
    assert.equal(await p.locator(t("siguiente")).isEnabled(), true);
    assert.equal(await p.locator(t("anterior")).isDisabled(), true);
    await p.click(t("siguiente"));
    await p.selectOption(t("destino"), "G");
    assert.match(await texto(p, "titulo-paso"), /Simulación no iniciada/);
    assert.equal(await p.locator(t("siguiente")).isDisabled(), true);
    assert.equal(await p.locator(".celda--vigente").count(), 0);
    assert.match(await texto(p, "ruta"), /A → G/);
    await p.cerrar();
  });

  test("adelante/atrás/reiniciar/final y teclado (un paso por pulsación)", async () => {
    const p = await abrir();
    await grafoPropio(p, DIAMANTE, 7, "A", "F");
    await p.click(t("ejecutar"));
    const paso = async () => Number((await texto(p, "paso-actual")).match(/Paso (\d+) de/)[1]);
    const total = Number((await texto(p, "paso-actual")).match(/de (\d+)/)[1]);
    assert.equal(await paso(), 1);
    await p.keyboard.press("ArrowRight"); assert.equal(await paso(), 2);
    await p.keyboard.press("ArrowDown"); assert.equal(await paso(), 3);
    await p.keyboard.press("ArrowLeft"); assert.equal(await paso(), 2);
    await p.keyboard.press("ArrowUp"); assert.equal(await paso(), 1);
    await p.keyboard.press("ArrowLeft"); assert.equal(await paso(), 1);
    await p.click(t("ir-al-final")); assert.equal(await paso(), total);
    assert.equal(await p.locator(t("siguiente")).isDisabled(), true);
    await p.keyboard.press("ArrowRight"); assert.equal(await paso(), total);
    await p.click(t("anterior")); assert.equal(await paso(), total - 1);
    await p.click(t("reiniciar")); assert.equal(await paso(), 1);
    // recorrer todo con Siguiente hasta el final
    for (let i = 1; i < total; i++) await p.click(t("siguiente"));
    assert.match(await texto(p, "estado"), /Completada · distancia mínima 5 · 2 caminos mínimos/);
    const res = await texto(p, "resultado");
    assert.match(res, /Distancia mínima: 5/); assert.match(res, /Caminos mínimos encontrados: 2/);
    assert.match(res, /A → B → D → E → F/); assert.match(res, /A → C → D → E → F/);
    assert.deepEqual(p.errores, []);
    await p.cerrar();
  });

  test("destino inalcanzable muestra el mensaje y distancia ∞", async () => {
    const p = await abrir();
    await grafoPropio(p, [["A", "B", 2], ["C", "D", 1]], 7, "A", "D");
    await p.click(t("ejecutar")); await p.click(t("ir-al-final"));
    assert.match(await texto(p, "resultado"), /No existe un camino desde A hasta D\.\s+Distancia: ∞/);
    assert.match(await texto(p, "estado"), /no existe camino de A a D/);
    await p.cerrar();
  });

  test("origen = destino: termina de inmediato, distancia 0, una columna en la tabla", async () => {
    const p = await abrir();
    await grafoPropio(p, DIAMANTE, 7, "A", "A");
    await p.click(t("ejecutar"));
    const total = Number((await texto(p, "paso-actual")).match(/de (\d+)/)[1]);
    await p.click(t("ir-al-final"));
    assert.match(await texto(p, "resultado"), /Distancia mínima: 0[\s\S]*A es a la vez origen y destino/);
    assert.equal(await p.locator(`${t("tabla")} thead th`).count(), 2, "Vértice + Iteración 0");
    assert.ok(total <= 3, `sin iteraciones innecesarias (pasos=${total})`);
    assert.equal(await p.locator(".marca").textContent(), "ORIGEN · DESTINO");
    await p.cerrar();
  });

  test("«Más detalles»: se abre, se actualiza al cambiar de paso, no bloquea y se cierra con Esc/botón", async () => {
    const p = await abrir();
    await grafoPropio(p, DIAMANTE, 7, "A", "F");
    await p.click(t("ejecutar"));
    await p.click(t("mas-detalles"));
    const t1 = await texto(p, "detalles-titulo");
    assert.equal(t1, await texto(p, "titulo-paso").then((x) => x.split("\n")[0]).catch(() => t1));
    await p.click(t("siguiente"));
    const t2 = await texto(p, "detalles-titulo");
    assert.notEqual(t1, t2);
    await p.keyboard.press("Escape");
    assert.equal(await p.locator(t("detalles")).count(), 0);
    await p.click(t("mas-detalles")); await p.click(t("detalles-cerrar"));
    assert.equal(await p.locator(t("detalles")).count(), 0);
    await p.click(t("mas-detalles")); await p.selectOption(t("destino"), "E");
    assert.match(await texto(p, "detalles-cuerpo"), /Cambió el origen o el destino/);
    assert.deepEqual(p.errores, []);
    await p.cerrar();
  });

  test("tabla: mostrar/ocultar y coherencia con el snapshot", async () => {
    const p = await abrir();
    await grafoPropio(p, DIAMANTE, 7, "A", "F");
    await p.click(t("ejecutar")); await p.click(t("ir-al-final"));
    const celdas = await p.$$eval(`${t("tabla")} td.celda:not(.celda--cab)`, (c) => c.filter((x) => x.textContent).length);
    assert.ok(celdas > 7);
    assert.ok(await p.locator(".celda--empate").count() >= 1, "hay empates en el diamante");
    await p.click(t("alternar-tabla"));
    assert.equal(await p.locator(t("tabla")).isVisible(), false);
    assert.equal(await p.locator(t("alternar-tabla")).innerText(), "Mostrar tabla del proceso");
    await p.click(t("alternar-tabla"));
    assert.equal(await p.locator(t("tabla")).isVisible(), true);
    await p.cerrar();
  });

  test("la simulación sigue los mismos estados que el motor en los 32 casos de oro (pantalla = Python v1.13)", async () => {
    const p = await abrir();
    const golden = JSON.parse(fs.readFileSync(path.join(RAIZ, "golden/dijkstra_golden.json"), "utf8"));
    assert.equal(golden.casos.length, 32);
    for (const caso of golden.casos) {
      await p.evaluate(async (caso) => {
        const core = await import("./src/core/index.js");
        window.__dijkstra.irASimulacion(core.grafoDesdeJson(caso.grafo), null, [caso.origen, caso.destino], "← Configuración");
      }, caso);
      await p.waitForSelector("[data-pantalla=simulacion]");
      await p.click(t("ejecutar"));
      for (let i = 0; i < caso.snapshots.length; i++) {
        const esp = caso.snapshots[i];
        assert.equal(await texto(p, "titulo-paso"), esp.titulo, `${caso.nombre} paso ${i}: título`);
        const bloques = await p.$$eval(`${t("explicacion")} .bloque`, (b) => b.map((x) => [x.dataset.estilo, x.textContent]));
        assert.deepEqual(bloques, esp.explicacion.breve.map((b) => [b.estilo, b.texto]), `${caso.nombre} paso ${i}: explicación`);
        const tabla = await p.$$eval(`${t("tabla")} td[data-celda]`, (c) => c.filter((x) => x.textContent).map((x) => [x.dataset.celda, x.textContent, x.className.replace("celda celda--", "")]));
        assert.deepEqual(tabla.sort(), esp.tabla.map((e) => [`${e.vertice}:${e.iteracion}`, e.texto, e.estado]).sort(), `${caso.nombre} paso ${i}: tabla`);
        const estados = await p.$$eval(".nodo", (n) => Object.fromEntries(n.map((x) => [x.dataset.v, x.dataset.estado])));
        for (const v of esp.visitados) {
          if (v !== caso.origen && v !== caso.destino && v !== esp.seleccionado) assert.equal(estados[v], "visitado", `${caso.nombre} paso ${i}: ${v} visitado`);
        }
        const aristas = await p.$$eval(".arista", (n) => n.filter((x) => x.dataset.estado !== "normal").map((x) => [x.dataset.arista, x.dataset.estado]));
        const esperadas = [];
        for (const [u, v, tipo] of esp.aristas_evaluadas) esperadas.push([`${u}>${v}`, tipo === "mejora" ? "evaluada" : tipo === "empate" ? "empate" : "descartada"]);
        for (const [u, v] of esp.aristas_camino) { const k = esperadas.findIndex((e) => e[0] === `${u}>${v}`); if (k >= 0) esperadas.splice(k, 1); esperadas.push([`${u}>${v}`, "camino"]); }
        assert.deepEqual(aristas.sort(), esperadas.sort(), `${caso.nombre} paso ${i}: aristas`);
        if (i < caso.snapshots.length - 1) await p.click(t("siguiente"));
      }
      const res = await texto(p, "resultado");
      if (caso.resultado.alcanzable) {
        assert.match(res, new RegExp(`Distancia mínima: ${caso.resultado.distancia}\\b`), `${caso.nombre}: distancia`);
        assert.match(res, new RegExp(`Caminos mínimos encontrados: ${caso.resultado.cantidad_caminos}\\b`), `${caso.nombre}: cantidad`);
        for (const c of caso.resultado.caminos.slice(0, 5)) assert.ok(res.includes(c.join(" → ")), `${caso.nombre}: camino ${c.join("")}`);
      } else assert.match(res, /No existe un camino/);
    }
    assert.deepEqual(p.errores, []);
    await p.cerrar();
  });
});

describe("legibilidad del grafo", () => {
  test("16 nodos: sin solapes entre pesos, etiquetas, marcas y vértices en todos los pasos (6 grafos)", async () => {
    const p = await abrir();
    for (let k = 0; k < 6; k++) {
      await p.goto(URL_BASE);
      await aSimulacionAuto(p, 16);
      assert.deepEqual(await medirSolapes(p), [], `grafo ${k} antes de ejecutar`);
      await p.click(t("ejecutar"));
      const total = Number((await texto(p, "paso-actual")).match(/de (\d+)/)[1]);
      for (let i = 1; i < total; i++) {
        assert.deepEqual(await medirSolapes(p), [], `grafo ${k} paso ${i}`);
        await p.click(t("siguiente"));
      }
      assert.deepEqual(await medirSolapes(p), [], `grafo ${k} final`);
    }
    assert.deepEqual(p.errores, []);
    await p.cerrar();
  });

  test("tamaños 7–16: sin solapes en el paso final", async () => {
    const p = await abrir();
    for (let n = 7; n <= 16; n++) {
      for (let rep = 0; rep < 3; rep++) {
        await p.goto(URL_BASE);
        await aSimulacionAuto(p, n);
        await p.click(t("ejecutar")); await p.click(t("ir-al-final"));
        assert.deepEqual(await medirSolapes(p), [], `n=${n} rep ${rep}`);
      }
    }
    await p.cerrar();
  });

  test("tras arrastrar un vértice los rótulos se recolocan sin solapes", async () => {
    const p = await abrir();
    await aSimulacionAuto(p, 12);
    await p.click(t("ejecutar")); await p.click(t("ir-al-final"));
    const b = await p.locator(".nodo[data-v='B'] circle").boundingBox();
    await p.mouse.move(b.x + b.width / 2, b.y + b.height / 2); await p.mouse.down();
    await p.mouse.move(b.x + 120, b.y + 90, { steps: 8 }); await p.mouse.up();
    assert.deepEqual(await medirSolapes(p), []);
    await p.cerrar();
  });
});

describe("temas", () => {
  test("alterna claro/oscuro, cambia colores, persiste al recargar y no pierde el estado", async () => {
    const p = await abrir();
    await aSimulacionAuto(p, 8);
    await p.click(t("ejecutar")); await p.click(t("siguiente")); await p.click(t("siguiente"));
    const antes = await texto(p, "paso-actual");
    const fondo = () => p.evaluate(() => getComputedStyle(document.body).backgroundColor);
    const claro = await fondo();
    const nodoClaro = await p.evaluate(() => getComputedStyle(document.querySelector(".nodo[data-estado=normal] circle")).fill);
    assert.equal(await p.evaluate(() => document.documentElement.dataset.theme), "light");
    await p.click(t("tema"));
    await p.waitForTimeout(450);
    assert.equal(await p.evaluate(() => document.documentElement.dataset.theme), "dark");
    assert.notEqual(await fondo(), claro);
    assert.equal(await texto(p, "paso-actual"), antes, "la simulación se conserva");
    const nodo = await p.evaluate(() => getComputedStyle(document.querySelector(".nodo[data-estado=normal] circle")).fill);
    assert.notEqual(nodo, nodoClaro);
    await p.reload(); await p.waitForSelector("[data-pantalla=bienvenida]");
    assert.equal(await p.evaluate(() => document.documentElement.dataset.theme), "dark");
    await p.click(t("tema")); await p.waitForTimeout(450);
    assert.equal(await fondo(), claro);
    assert.deepEqual(p.errores, []);
    await p.cerrar();
  });

  test("respeta el tema oscuro del sistema en la primera visita", async () => {
    const p = await abrir({ tema: "dark" });
    assert.equal(await p.evaluate(() => document.documentElement.dataset.theme), "dark");
    await p.cerrar();
  });
});

describe("tutorial guiado", () => {
  async function recorrer(p, esperado) {
    await p.click(t("tutorial"));
    await p.waitForSelector(t("tutorial-tarjeta"));
    const titulos = [];
    for (;;) {
      await p.waitForTimeout(320); // la tarjeta se desliza con una transición de 250 ms
      titulos.push(await texto(p, "tut-titulo"));
      const caja = await p.locator(t("tutorial-tarjeta")).boundingBox();
      const vp = p.viewportSize();
      assert.ok(caja.x >= 0 && caja.y >= 0 && caja.x + caja.width <= vp.width && caja.y + caja.height <= vp.height, `tarjeta dentro de la ventana en «${titulos.at(-1)}»`);
      const ultimo = (await texto(p, "tut-siguiente")) === "Finalizar";
      await p.click(t("tut-siguiente"));
      if (ultimo) break;
    }
    assert.equal(await p.locator(t("tutorial-overlay")).count(), 0);
    if (esperado) assert.deepEqual(titulos, esperado);
    return titulos;
  }

  test("bienvenida y configuración", async () => {
    const p = await abrir();
    await recorrer(p, ["Bienvenido al simulador", "Empezar", "Tutorial y tema"]);
    await p.click(t("empezar"));
    await recorrer(p, ["Configura tu grafo", "Número de vértices", "Generar automáticamente", "Crear manualmente"]);
    assert.deepEqual(p.errores, []);
    await p.cerrar();
  });

  test("editor: 5 pasos y no modifica el grafo", async () => {
    const p = await abrir();
    await aEditor(p); await conectar(p, "A", "B", 4);
    await recorrer(p, ["El área de construcción", "Peso de la conexión", "Aristas del grafo", "Restablecer posiciones", "Finalizar el grafo"]);
    assert.equal(await p.locator(".arista-fila").count(), 1);
    await p.cerrar();
  });

  test("simulación: 16 pasos con ejemplos reales, antes y durante la simulación, sin alterarla", async () => {
    const p = await abrir();
    await aSimulacionAuto(p, 9);
    const ant = await recorrer(p);
    assert.equal(ant.length, 16);
    assert.equal(ant[0], "Bienvenido a la simulación");
    assert.equal(ant.at(-1), "Reconstruir el camino mínimo");
    assert.match(await texto(p, "titulo-paso"), /Simulación no iniciada/);
    await p.click(t("ejecutar")); await p.click(t("siguiente")); await p.click(t("siguiente"));
    const estado = { paso: await texto(p, "paso-actual"), res: await texto(p, "resultado"), expl: await texto(p, "explicacion") };
    await p.click(t("tutorial"));
    // ir hasta los ejemplos del algoritmo y leerlos
    const ejemplos = [];
    for (let i = 0; i < 16; i++) {
      if (await p.locator(t("tut-ejemplo")).isVisible()) ejemplos.push(await texto(p, "tut-ejemplo"));
      if (i < 15) await p.click(t("tut-siguiente"));
    }
    assert.equal(ejemplos.length, 5);
    for (const e of ejemplos) assert.match(e, /Calculado con tu grafo; no modifica tu simulación/);
    assert.match(ejemplos[0], /Al empezar, \w tiene \[0, -\]₀/);
    await p.click(t("tut-siguiente"));
    assert.deepEqual({ paso: await texto(p, "paso-actual"), res: await texto(p, "resultado"), expl: await texto(p, "explicacion") }, estado);
    assert.deepEqual(p.errores, []);
    await p.cerrar();
  });

  test("el tutorial se maneja con teclado (→ ← Esc) y bloquea la interfaz de fondo", async () => {
    const p = await abrir();
    await p.click(t("tutorial"));
    assert.equal(await texto(p, "tut-titulo"), "Bienvenido al simulador");
    await p.keyboard.press("ArrowRight"); assert.equal(await texto(p, "tut-titulo"), "Empezar");
    await p.keyboard.press("ArrowLeft"); assert.equal(await texto(p, "tut-titulo"), "Bienvenido al simulador");
    // el clic sobre el botón «Empezar» queda bloqueado por el tutorial
    await p.mouse.click(660, 600);
    assert.equal(await p.locator("[data-pantalla=bienvenida]").count(), 1);
    await p.keyboard.press("Escape");
    assert.equal(await p.locator(t("tutorial-overlay")).count(), 0);
    await p.cerrar();
  });
});

describe("responsive", () => {
  test("sin desbordamiento horizontal a 1024 y 768 px; la simulación se apila", async () => {
    for (const ancho of [1100, 1024, 768]) {
      const p = await abrir({ ancho, alto: 800 });
      await aSimulacionAuto(p, 12);
      await p.click(t("ejecutar")); await p.click(t("ir-al-final"));
      const desborde = await p.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      assert.ok(desborde <= 1, `desborde ${desborde}px a ${ancho}`);
      assert.deepEqual(await medirSolapes(p), [], `solapes a ${ancho}`);
      await p.cerrar();
    }
  });
});

describe("iconos SVG", () => {
  const EMOJI = /[\u{1F300}-\u{1FAFF}\u2600-\u27BF\u2B00-\u2BFF\u23E9-\u23FF\u25B6\u25C0\u21BA\uFE0F]/u;

  async function revisarIconos(p, contexto) {
    const r = await p.evaluate(() => {
      const malos = [];
      const iconos = [...document.querySelectorAll("svg.icono")];
      for (const i of iconos) {
        const cs = getComputedStyle(i);
        if (i.getAttribute("stroke") !== "currentColor" || i.getAttribute("fill") !== "none") malos.push("no usa currentColor");
        if (i.getAttribute("stroke-width") !== "2") malos.push("grosor distinto de 2");
        if (!i.hasAttribute("aria-hidden") && !i.getAttribute("aria-label")) malos.push("sin aria-hidden ni aria-label");
        if (cs.stroke !== cs.color) malos.push(`trazo ${cs.stroke} ≠ color ${cs.color}`);
      }
      // Los botones que solo tienen icono necesitan nombre accesible.
      for (const b of document.querySelectorAll("button")) {
        if (!b.textContent.trim() && !b.getAttribute("aria-label")) malos.push("botón sin nombre accesible");
      }
      return { malos, total: iconos.length, texto: document.body.innerText };
    });
    assert.deepEqual(r.malos, [], contexto);
    assert.ok(!EMOJI.test(r.texto), `${contexto}: quedan emojis o símbolos gráficos en «${r.texto.match(EMOJI)?.[0]}»`);
    return r.total;
  }

  test("ninguna pantalla muestra emojis; todos los iconos son lineales, usan currentColor y son accesibles (claro y oscuro)", async () => {
    for (const tema of ["claro", "oscuro"]) {
      const p = await abrir({ tema: tema === "oscuro" ? "dark" : "light" });
      let total = await revisarIconos(p, `bienvenida ${tema}`);
      assert.ok(total >= 6, "bienvenida: birrete, tutorial, tema, 3 tarjetas y flecha");
      await p.click(t("tutorial")); await p.waitForSelector(t("tutorial-tarjeta"));
      await revisarIconos(p, `tutorial ${tema}`);
      await p.keyboard.press("Escape");
      await p.click(t("empezar"));
      await revisarIconos(p, `configuración ${tema}`);
      await p.click(t("manual"));
      await conectar(p, "A", "B", 3);
      await revisarIconos(p, `editor ${tema}`);
      await p.click(t("editor-volver")); await p.click(t("dialogo-confirmar"));
      await p.click(t("generar"));
      await revisarIconos(p, `simulación sin ejecutar ${tema}`);
      await p.click(t("ejecutar")); await p.click(t("siguiente")); await p.click(t("mas-detalles"));
      await revisarIconos(p, `simulación en curso ${tema}`);
      await p.click(t("detalles-cerrar")); await p.click(t("ir-al-final"));
      await revisarIconos(p, `simulación final ${tema}`);
      assert.equal(await p.locator(`${t("estado")} svg.icono`).count(), 1, "icono de resultado");
      assert.deepEqual(p.errores, []);
      await p.cerrar();
    }
  });

  test("el botón de tema cambia de luna a sol, con nombre accesible", async () => {
    const p = await abrir();
    assert.equal(await p.locator(`${t("tema")} svg`).getAttribute("class"), "icono icono--luna");
    assert.match(await p.locator(t("tema")).getAttribute("aria-label"), /oscuro/);
    await p.click(t("tema"));
    assert.equal(await p.locator(`${t("tema")} svg`).getAttribute("class"), "icono icono--sol");
    assert.match(await p.locator(t("tema")).getAttribute("aria-label"), /claro/);
    await p.cerrar();
  });

  test("módulo iconos.js: todos los nombres se generan; un nombre desconocido falla", async () => {
    const p = await abrir();
    const r = await p.evaluate(async () => {
      const m = await import("./src/ui/iconos.js");
      const ok = m.NOMBRES_ICONOS.every((n) => m.icono(n).childElementCount > 0 && m.icono(n, { etiqueta: "x" }).getAttribute("role") === "img");
      let fallo = false;
      try { m.icono("no-existe"); } catch { fallo = true; }
      return { ok, fallo, n: m.NOMBRES_ICONOS.length };
    });
    assert.deepEqual({ ok: r.ok, fallo: r.fallo }, { ok: true, fallo: true });
    assert.ok(r.n >= 18);
    await p.cerrar();
  });
});

/** Cuánto sobresale (en px) cada elemento del grafo respecto del área del lienzo; vacío si todo es visible. */
async function medirVisibilidad(p) {
  return p.evaluate(() => {
    const lienzo = document.querySelector("[data-pantalla] .lienzo");
    const L = lienzo.getBoundingClientRect();
    const salidas = [];
    const revisar = (nombre, r) => {
      if (r.left < L.left - 0.5 || r.right > L.right + 0.5 || r.top < L.top - 0.5 || r.bottom > L.bottom + 0.5) salidas.push(nombre);
    };
    lienzo.querySelectorAll(".nodo circle").forEach((e) => revisar("nodo " + e.parentNode.dataset.v, e.getBoundingClientRect()));
    lienzo.querySelectorAll(".peso rect").forEach((e) => revisar("peso " + e.parentNode.dataset.peso, e.getBoundingClientRect()));
    lienzo.querySelectorAll(".marca rect").forEach((e) => revisar("marca " + e.parentNode.dataset.marca, e.getBoundingClientRect()));
    lienzo.querySelectorAll(".etiqueta text").forEach((e) => revisar("etiqueta " + e.parentNode.dataset.etiqueta, e.getBoundingClientRect()));
    lienzo.querySelectorAll(".arista path").forEach((e) => revisar("arista " + e.parentNode.dataset.arista, e.getBoundingClientRect()));
    const dentroDeVentana = L.top >= 0 && L.bottom <= window.innerHeight + 0.5 && L.left >= 0 && L.right <= window.innerWidth + 0.5;
    const viewBox = lienzo.querySelector("svg").getAttribute("viewBox");
    return { salidas, dentroDeVentana, lienzo: [Math.round(L.width), Math.round(L.height), Math.round(L.top), Math.round(L.bottom)], altoVentana: window.innerHeight, viewBox };
  });
}

describe("ajuste automático del grafo", () => {
  const RESOLUCIONES = [[1920, 1080], [1366, 768], [1280, 720], [1024, 768]];

  test("7, 10 y 16 nodos: todo el grafo y el lienzo son visibles al entrar, sin desplazar la página, en varias resoluciones", async () => {
    for (const [ancho, alto] of RESOLUCIONES) {
      const p = await abrir({ ancho, alto });
      for (const n of [7, 10, 16]) {
        await p.goto(URL_BASE);
        await aSimulacionAuto(p, n);
        let m = await medirVisibilidad(p);
        assert.deepEqual(m.salidas, [], `${n} nodos a ${ancho}×${alto} (grafo recién generado)`);
        assert.equal(m.dentroDeVentana, true, `lienzo completo en la ventana ${ancho}×${alto} (n=${n}): ${m.lienzo} / ${m.altoVentana}`);
        assert.equal(await p.evaluate(() => window.scrollY), 0);
        await p.click(t("ejecutar"));
        m = await medirVisibilidad(p);
        assert.deepEqual(m.salidas, [], `${n} nodos a ${ancho}×${alto} (al ejecutar)`);
        const total = Number((await texto(p, "paso-actual")).match(/de (\d+)/)[1]);
        for (let i = 1; i < total; i++) {
          if (n === 16 && i % 4 !== 0 && i !== total - 1) { await p.click(t("siguiente")); if (ancho >= 1100) assert.equal(await p.evaluate(() => window.scrollY), 0, `desplazamiento en el paso ${i} (${ancho}×${alto}, n=${n})`); continue; }
          m = await medirVisibilidad(p);
          assert.deepEqual(m.salidas, [], `${n} nodos a ${ancho}×${alto}, paso ${i}`);
          assert.deepEqual(await medirSolapes(p), [], `solapes: ${n} nodos a ${ancho}×${alto}, paso ${i}`);
          await p.click(t("siguiente"));
          if (ancho >= 1100) assert.equal(await p.evaluate(() => window.scrollY), 0, `la página se desplazó en el paso ${i} (${ancho}×${alto}, n=${n})`);
        }
        m = await medirVisibilidad(p);
        assert.deepEqual(m.salidas, [], `${n} nodos a ${ancho}×${alto} (final)`);
        if (ancho >= 1100) assert.equal(await p.evaluate(() => window.scrollY), 0, `no hizo falta desplazar la página (${ancho}×${alto}, n=${n})`); // por debajo, los controles van bajo el grafo
      }
      assert.deepEqual(p.errores, []);
      await p.cerrar();
    }
  });

  test("la legibilidad se conserva: los vértices y textos no se encogen por debajo de un mínimo", async () => {
    for (const [ancho, alto] of [[1366, 768], [1024, 768]]) {
      const p = await abrir({ ancho, alto });
      await aSimulacionAuto(p, 16);
      await p.click(t("ejecutar")); await p.click(t("ir-al-final"));
      const m = await p.evaluate(() => ({
        radio: document.querySelector(".nodo circle").getBoundingClientRect().width / 2,
        etiqueta: parseFloat(getComputedStyle(document.querySelector(".etq")).fontSize) * (document.querySelector(".grafo-svg").getBoundingClientRect().width / document.querySelector(".grafo-svg").viewBox.baseVal.width),
      }));
      assert.ok(m.radio >= 13, `radio de vértice ${m.radio}px a ${ancho}`);
      assert.ok(m.etiqueta >= 9.5, `texto de etiqueta ${m.etiqueta}px a ${ancho}`);
      await p.cerrar();
    }
  });

  test("el editor también muestra los 7 vértices completos y se reajusta al redimensionar la ventana", async () => {
    const p = await abrir({ ancho: 1280, alto: 720 });
    await aEditor(p, 7);
    assert.deepEqual((await medirVisibilidad(p)).salidas, []);
    await p.setViewportSize({ width: 1000, height: 640 });
    await p.waitForTimeout(200);
    assert.deepEqual((await medirVisibilidad(p)).salidas, [], "tras reducir la ventana");
    await p.setViewportSize({ width: 1500, height: 900 });
    await p.waitForTimeout(200);
    assert.deepEqual((await medirVisibilidad(p)).salidas, [], "tras ampliarla");
    await p.cerrar();
  });

  test("botón «Ajustar grafo»: nombre accesible, tooltip al pasar el cursor y recupera la vista completa", async () => {
    const p = await abrir({ ancho: 1366, alto: 768 });
    await aSimulacionAuto(p, 12);
    await p.click(t("ejecutar")); await p.click(t("ir-al-final"));
    const boton = p.locator(t("ajustar-grafo"));
    assert.equal(await boton.getAttribute("aria-label"), "Ajustar grafo");
    assert.equal(await boton.locator("svg.icono--maximizar").count(), 1);
    const tip = () => p.locator(".lienzo__tip").evaluate((e) => getComputedStyle(e).opacity);
    assert.equal(await tip(), "0");
    await boton.hover(); await p.waitForTimeout(250);
    assert.equal(await tip(), "1");
    assert.equal(await p.locator(".lienzo__tip").innerText(), "Ajustar grafo");
    await p.mouse.move(10, 10);
    const inicial = await p.locator(".grafo-svg").first().getAttribute("viewBox");
    // zoom con la rueda y desplazamiento arrastrando el fondo
    const caja = await p.locator(".grafo-svg").first().boundingBox();
    await p.mouse.move(caja.x + caja.width / 2, caja.y + caja.height / 2);
    await p.mouse.wheel(0, -400); await p.mouse.wheel(0, -400);
    const zoom = await p.locator(".grafo-svg").first().getAttribute("viewBox");
    const ancho = (vb) => Number(vb.split(" ")[2]);
    const cercano = (a, b) => a.split(" ").every((x, i) => Math.abs(Number(x) - Number(b.split(" ")[i])) < 1.5);
    assert.ok(ancho(zoom) < ancho(inicial) * 0.8, `acercó: ${inicial} → ${zoom}`);
    assert.equal(await p.evaluate(() => window.scrollY), 0, "la rueda no desplaza la página");
    await p.mouse.move(caja.x + 40, caja.y + caja.height - 25); // fondo vacío
    await p.mouse.down(); await p.mouse.move(caja.x + 140, caja.y + caja.height - 60, { steps: 5 }); await p.mouse.up();
    const movida = await p.locator(".grafo-svg").first().getAttribute("viewBox");
    assert.notEqual(movida.split(" ")[0], zoom.split(" ")[0], "desplazó la vista");
    assert.equal(await p.evaluate(() => window.scrollY), 0);
    // alejar mucho no permite perderse: el zoom tiene límites
    for (let i = 0; i < 12; i++) await p.mouse.wheel(0, 400);
    assert.ok(ancho(await p.locator(".grafo-svg").first().getAttribute("viewBox")) <= ancho(inicial) * 1.6 + 1);
    await boton.click();
    assert.ok(cercano(await p.locator(".grafo-svg").first().getAttribute("viewBox"), inicial), "Ajustar restaura la vista completa");
    assert.deepEqual((await medirVisibilidad(p)).salidas, []);
    // Siguiente/Anterior no deshacen un zoom del usuario…
    await p.mouse.move(caja.x + caja.width / 2, caja.y + caja.height / 2); await p.mouse.wheel(0, -300);
    const ampliada = await p.locator(".grafo-svg").first().getAttribute("viewBox");
    await p.click(t("anterior"));
    assert.equal(await p.locator(".grafo-svg").first().getAttribute("viewBox"), ampliada);
    // …y el doble clic sobre el fondo también ajusta
    await p.mouse.dblclick(caja.x + 40, caja.y + caja.height - 25);
    assert.ok(cercano(await p.locator(".grafo-svg").first().getAttribute("viewBox"), inicial));
    assert.deepEqual(p.errores, []);
    await p.cerrar();
  });

  test("con zoom, arrastrar un vértice sigue funcionando y los clics siguen llegando a los vértices", async () => {
    const p = await abrir({ ancho: 1366, alto: 768 });
    await aEditor(p, 7);
    const caja = await p.locator(".grafo-svg").boundingBox();
    await p.mouse.move(caja.x + caja.width / 2, caja.y + caja.height / 2);
    await p.mouse.wheel(0, -300);
    const c = async (v) => { const b = await p.locator(`.nodo[data-v="${v}"] circle`).boundingBox(); return [b.x + b.width / 2, b.y + b.height / 2]; };
    // el vértice más cercano al centro del lienzo (los de los bordes pueden quedar fuera tras ampliar)
    const v = await p.evaluate(() => {
      const L = document.querySelector(".lienzo").getBoundingClientRect();
      const cx = (L.left + L.right) / 2; const cy = (L.top + L.bottom) / 2;
      return [...document.querySelectorAll(".nodo")].map((g) => { const b = g.querySelector("circle").getBoundingClientRect(); return [g.dataset.v, Math.hypot((b.left + b.right) / 2 - cx, (b.top + b.bottom) / 2 - cy), b.left > L.left + 40 && b.right < L.right - 60 && b.top > L.top + 40 && b.bottom < L.bottom - 40]; }).filter((x) => x[2]).sort((a, b) => a[1] - b[1])[0][0];
    });
    const antes = await p.evaluate((v) => window.__dijkstra.pantalla.posiciones()[v], v);
    const [x, y] = await c(v);
    await p.mouse.move(x, y); await p.mouse.down(); await p.mouse.move(x + 20, y + 15, { steps: 4 }); await p.mouse.up();
    const despues = await p.evaluate((v) => window.__dijkstra.pantalla.posiciones()[v], v);
    assert.notDeepEqual(despues.map(Math.round), antes.map(Math.round));
    await p.click(t("ajustar-grafo")); // con zoom algunos vértices quedan fuera del área visible
    await conectar(p, "B", "C", 4);
    assert.match(await texto(p, "editor-mensaje"), /Conexión creada: B → C/);
    // editor de peso en línea con zoom: el campo queda sobre el número
    await p.click('[data-peso="B>C"]');
    const campo = await p.locator(t("peso-editor")).boundingBox();
    const peso = await p.locator('[data-peso="B>C"] rect').boundingBox();
    assert.ok(Math.abs(campo.x + campo.width / 2 - (peso.x + peso.width / 2)) < 6 && Math.abs(campo.y + campo.height / 2 - (peso.y + peso.height / 2)) < 6);
    await p.keyboard.press("Escape");
    await p.cerrar();
  });
});

describe("iteraciones e indicador de paso", () => {
  test("el subíndice de iteración es un elemento propio, discreto, proporcional y del color original de la etiqueta", async () => {
    for (const tema of ["light", "dark"]) {
      const p = await abrir({ tema });
      await aSimulacionAuto(p, 9);
      await p.click(t("ejecutar")); await p.click(t("ir-al-final"));
      const r = await p.evaluate(() => {
        const texto = [...document.querySelectorAll(".etiqueta text.etq:not(.etq--descartada)")].find((x) => x.querySelector(".etq__iter"));
        const it = [...texto.querySelectorAll(".etq__iter")].pop();
        const cs = getComputedStyle(it); const cp = getComputedStyle(texto);
        return {
          iter: it.textContent, fontIter: parseFloat(cs.fontSize), fontBase: parseFloat(cp.fontSize), fillIter: cs.fill, fillBase: cp.fill,
          pesoIter: Number(cs.fontWeight),
          contraste: (() => {
            const lum = (c) => { const [r, g, b] = c.match(/\d+(\.\d+)?/g).slice(0, 3).map(Number).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
            const fondo = getComputedStyle(document.querySelector(".lienzo")).backgroundColor;
            const a = lum(cs.fill); const b = lum(fondo);
            return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
          })(),
          aria: texto.getAttribute("aria-label"), todo: texto.textContent,
        };
      });
      assert.match(r.iter, /^\d+$/);
      assert.ok(r.fontIter >= 9.5 && r.fontIter <= r.fontBase * 0.85, `subíndice discreto y legible: ${r.fontIter}px frente a ${r.fontBase}px`);
      assert.ok(r.pesoIter >= 600);
      assert.equal(r.fillIter, r.fillBase, `mismo color naranja que la etiqueta (${tema})`);
      assert.equal(r.fillIter, tema === "dark" ? "rgb(251, 191, 36)" : "rgb(180, 83, 9)", "naranja original");
      assert.ok(r.contraste >= 4.5, `contraste ${r.contraste.toFixed(2)} (${tema})`);
      assert.match(r.aria, /^\[.*\], iteración \d+( \[.*\], iteración \d+)*$/);
      assert.ok(r.todo.endsWith(r.iter));
      assert.deepEqual(await medirSolapes(p), []);
      await p.cerrar();
    }
  });

  test("en un empate cada índice de iteración es un subíndice discreto (ninguno queda como glifo unicode)", async () => {
    const p = await abrir({});
    const r = await p.evaluate(async () => {
      const { GrafoSvg } = await import("./src/ui/grafo-svg.js");
      const nodo = GrafoSvg.prototype._textoEtiqueta.call(null, "[10, D]\u2085 [10, F]\u2086", "etq", {});
      document.querySelector(".lienzo, body").appendChild(Object.assign(document.createElementNS("http://www.w3.org/2000/svg", "svg"), {})).appendChild(nodo);
      const its = [...nodo.querySelectorAll(".etq__iter")];
      const tam = its.map((i) => parseFloat(getComputedStyle(i).fontSize));
      nodo.ownerSVGElement.remove();
      return { n: its.length, txt: its.map((i) => i.textContent), tam, todo: nodo.textContent, aria: nodo.getAttribute("aria-label") };
    });
    assert.equal(r.n, 2);
    assert.deepEqual(r.txt, ["5", "6"]);
    assert.equal(r.tam[0], r.tam[1], "ambos índices con el mismo tamaño");
    assert.ok(!/[\u2080-\u2089]/u.test(r.todo), "sin dígitos subíndice unicode");
    assert.equal(r.todo, "[10, D]5 [10, F]6");
    assert.equal(r.aria, "[10, D], iteración 5 [10, F], iteración 6");
    await p.cerrar();
  });

  test("«Paso X de Y»: contraste AA y jerarquía visual en ambos temas", async () => {
    for (const tema of ["light", "dark"]) {
      const p = await abrir({ tema });
      await aSimulacionAuto(p, 8);
      assert.equal(await p.locator(t("paso-actual")).isVisible(), false, "sin simulación no se muestra");
      await p.click(t("ejecutar")); await p.click(t("siguiente"));
      assert.match(await texto(p, "paso-actual"), /^Paso 2 de \d+$/);
      const r = await p.evaluate(() => {
        const e = document.querySelector("[data-testid=paso-actual]");
        const cs = getComputedStyle(e);
        const lum = (c) => { const [r, g, b] = c.match(/\d+(\.\d+)?/g).slice(0, 3).map(Number).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
        const a = lum(cs.color); const b = lum(cs.backgroundColor);
        return { contraste: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05), tam: parseFloat(cs.fontSize), peso: Number(cs.fontWeight), numero: parseFloat(getComputedStyle(e.querySelector("b")).fontSize) };
      });
      assert.ok(r.contraste >= 4.5, `contraste ${r.contraste.toFixed(2)} (${tema})`);
      assert.ok(r.tam >= 14 && r.peso >= 700 && r.numero > r.tam);
      await p.cerrar();
    }
  });
});

describe("arrastre y vista", () => {
  test("un vértice arrastrado no puede salir del área visible y la vista no salta al soltarlo", async () => {
    const p = await abrir({ ancho: 1366, alto: 768 });
    await aEditor(p, 7);
    await p.waitForTimeout(350);
    const vb0 = await p.locator(".grafo-svg").getAttribute("viewBox");
    const L = await p.locator(".lienzo").boundingBox();
    const b = await p.locator('.nodo[data-v="C"] circle').boundingBox();
    await p.mouse.move(b.x + b.width / 2, b.y + b.height / 2); await p.mouse.down();
    await p.mouse.move(L.x + L.width + 300, L.y + L.height + 300, { steps: 8 }); await p.mouse.up();
    assert.equal(await p.locator(".grafo-svg").getAttribute("viewBox"), vb0, "la vista no cambia");
    assert.deepEqual((await medirVisibilidad(p)).salidas, [], "el vértice sigue visible");
    await p.cerrar();
  });
});

describe("límites del desplazamiento", () => {
  test("arrastrar el fondo muy lejos nunca saca el grafo del lienzo, y «Ajustar grafo» lo recupera", async () => {
    const p = await abrir({});
    await aSimulacionAuto(p, 10);
    const medir = () => p.evaluate(() => {
      const s = document.querySelector("[data-pantalla] .grafo-svg"); const r = s.getBoundingClientRect();
      const nodos = [...document.querySelectorAll(".nodo__circulo")].map((c) => c.getBoundingClientRect());
      const visibles = nodos.filter((b) => b.right > r.left && b.left < r.right && b.bottom > r.top && b.top < r.bottom).length;
      return { visibles, total: nodos.length };
    });
    const caja = await p.locator(".grafo-svg").boundingBox();
    for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [1, 1]]) {
      // el punto de partida es un rincón del fondo, sin vértices
      const x0 = caja.x + caja.width * (dx > 0 ? 0.04 : 0.96) ; const y0 = caja.y + caja.height * (dy > 0 ? 0.04 : 0.96);
      await p.mouse.move(x0, y0); await p.mouse.down();
      await p.mouse.move(x0 + dx * caja.width * 0.9, y0 + dy * caja.height * 0.9, { steps: 8 });
      await p.mouse.move(x0 + dx * caja.width * 2, y0 + dy * caja.height * 2, { steps: 8 });
      await p.mouse.up();
      const m = await medir();
      assert.ok(m.visibles >= 1, `queda al menos un vértice a la vista tras arrastrar hacia (${dx}, ${dy}): ${m.visibles}/${m.total}`);
    }
    await p.click(t("ajustar-grafo"));
    const m = await medir();
    assert.equal(m.visibles, m.total, "«Ajustar grafo» vuelve a mostrar todos");
    await p.cerrar();
  });
});

describe("móvil y táctil (390×844 y 360×640)", () => {
  const PANTALLAS = [[390, 844], [360, 640]];

  async function aSimulacionTactil(p, n) {
    await p.tap(t("empezar"));
    await p.selectOption(t("num-nodos"), String(n));
    await p.tap(t("generar"));
    await p.waitForSelector("[data-pantalla=simulacion]");
    await p.waitForTimeout(400);
  }
  const medirVista = (p) => p.evaluate(() => {
    const s = document.querySelector("[data-pantalla] .grafo-svg"); const r = s.getBoundingClientRect(); const vb = s.viewBox.baseVal;
    return { vb: [vb.x, vb.y, vb.width, vb.height], escala: r.width / vb.width, w: r.width, h: r.height, x: r.x, y: r.y, scrollY: window.scrollY, clase: s.parentElement.className };
  });
  async function toque(p) {
    const cdp = await p.ctx.newCDPSession(p);
    return (tipo, pts) => cdp.send("Input.dispatchTouchEvent", { type: tipo, touchPoints: pts.map(([x, y], id) => ({ x, y, id })) });
  }
  /** Punto del lienzo donde no hay vértices, pesos ni etiquetas (fondo del SVG), para empezar un arrastre. */
  const puntoLibre = (p, cerca = 0.5) => p.evaluate((f) => {
    const s = document.querySelector("[data-pantalla] .grafo-svg"); const r = s.getBoundingClientRect();
    for (let k = 0; k < 400; k++) {
      const x = r.left + r.width * (f + ((k * 37) % 100) / 400 - 0.125); const y = r.top + r.height * (0.25 + ((k * 53) % 100) / 200);
      if (x > r.left + 8 && x < r.right - 60 && y > r.top + 8 && y < r.bottom - 60 && document.elementFromPoint(x, y) === s && document.elementFromPoint(x, y + 50) === s) return [x, y];
    }
    return null;
  }, cerca);
  async function arrastrar(p, enviar, desde, hasta, pasos = 10) {
    await enviar("touchStart", [desde]);
    for (let i = 1; i <= pasos; i++) { await enviar("touchMove", [[desde[0] + ((hasta[0] - desde[0]) * i) / pasos, desde[1] + ((hasta[1] - desde[1]) * i) / pasos]]); await p.waitForTimeout(16); }
    await enviar("touchEnd", []);
    await p.waitForTimeout(150);
  }

  test("sin desbordamiento horizontal y con el texto del grafo legible (7, 10 y 16 vértices)", async () => {
    for (const [ancho, alto] of PANTALLAS) {
      for (const n of [7, 10, 16]) {
        const p = await abrir({ ancho, alto, tactil: true });
        await aSimulacionTactil(p, n);
        await p.tap(t("ejecutar"));
        await p.tap(t("ir-al-final"));
        await p.waitForTimeout(200);
        const m = await p.evaluate(() => {
          const s = document.querySelector("[data-pantalla] .grafo-svg"); const r = s.getBoundingClientRect(); const vb = s.viewBox.baseVal;
          const k = r.width / vb.width;
          const px = (sel) => parseFloat(getComputedStyle(document.querySelector(sel)).fontSize) * k;
          return {
            desborda: document.documentElement.scrollWidth > window.innerWidth + 1, k,
            etiqueta: px(".etiqueta text"), peso: px(".peso__texto"), nodo: parseFloat(document.querySelector(".nodo__circulo").getAttribute("r")) * 2 * k,
          };
        });
        const donde = `${ancho}×${alto} con ${n} vértices`;
        assert.equal(m.desborda, false, `sin scroll horizontal (${donde})`);
        assert.ok(m.k >= 0.64, `escala legible ${m.k.toFixed(2)} (${donde})`);
        assert.ok(m.etiqueta >= 8, `etiquetas ≥ 8 px: ${m.etiqueta.toFixed(1)} (${donde})`);
        assert.ok(m.peso >= 8, `pesos ≥ 8 px: ${m.peso.toFixed(1)} (${donde})`);
        assert.ok(m.nodo >= 26, `nodos ≥ 26 px: ${m.nodo.toFixed(1)} (${donde})`);
        assert.deepEqual(p.errores, []);
        await p.cerrar();
      }
    }
  });

  test("«Ajustar grafo» muestra los 16 vértices completos en el lienzo", async () => {
    for (const [ancho, alto] of PANTALLAS) {
      const p = await abrir({ ancho, alto, tactil: true });
      await aSimulacionTactil(p, 16);
      await p.tap(t("ajustar-grafo"));
      await p.waitForTimeout(150);
      const dentro = await p.evaluate(() => {
        const r = document.querySelector("[data-pantalla] .grafo-svg").getBoundingClientRect();
        return [...document.querySelectorAll(".nodo__circulo")].every((c) => { const b = c.getBoundingClientRect(); return b.left >= r.left - 1 && b.right <= r.right + 1 && b.top >= r.top - 1 && b.bottom <= r.bottom + 1; });
      });
      assert.ok(dentro, `todos los vértices dentro del lienzo (${ancho}×${alto})`);
      await p.cerrar();
    }
  });

  test("controles táctiles: botones de al menos 44 px y barra de navegación compacta de una fila", async () => {
    for (const [ancho, alto] of PANTALLAS) {
      const p = await abrir({ ancho, alto, tactil: true });
      await aSimulacionTactil(p, 10);
      const m = await p.evaluate(() => {
        const h = (id) => document.querySelector(`[data-testid="${id}"]`).getBoundingClientRect();
        const barra = document.querySelector(".barra-nav").getBoundingClientRect();
        return {
          alturas: ["anterior", "siguiente", "reiniciar", "ir-al-final", "alternar-tabla", "ejecutar", "ajustar-grafo"].map((id) => [id, h(id).height, h(id).width]),
          barra: barra.height, vh: window.innerHeight, fixed: getComputedStyle(document.querySelector(".barra-nav")).position,
          cabecera: getComputedStyle(document.querySelector(".cabecera")).position,
          campo: parseFloat(getComputedStyle(document.querySelector("select.campo")).fontSize),
          nombres: ["reiniciar", "ir-al-final", "alternar-tabla"].map((id) => document.querySelector(`[data-testid="${id}"]`).getAttribute("aria-label")),
          visibles: ["reiniciar", "ir-al-final", "alternar-tabla"].map((id) => document.querySelector(`[data-testid="${id}"]`).innerText.trim()),
        };
      });
      for (const [id, alto2, ancho2] of m.alturas) assert.ok(alto2 >= 44 && ancho2 >= 44, `${id} mide ${ancho2}×${alto2} (${ancho}×${alto})`);
      assert.ok(m.barra <= 72, `barra de navegación de una fila: ${m.barra}px`);
      assert.ok(m.barra / m.vh < 0.13, "la barra fija no tapa más del 13 % de la pantalla");
      assert.equal(m.cabecera, "static", "la cabecera no queda fija en el celular");
      assert.ok(m.campo >= 16, "selectores a 16 px (sin zoom automático en iOS)");
      assert.deepEqual(m.nombres, ["Reiniciar", "Ir al final", "Ocultar tabla del proceso"]);
      assert.deepEqual(m.visibles, ["", "", ""], "en celular solo icono");
      await p.cerrar();
    }
  });

  test("pellizco con dos dedos hace zoom, un dedo desplaza el grafo y el zoom no mueve la página", async () => {
    const p = await abrir({ ancho: 390, alto: 844, tactil: true });
    await aSimulacionTactil(p, 16);
    const enviar = await toque(p);
    const antes = await medirVista(p);
    // el pellizco se centra en un vértice visible, para que al ampliar siga habiendo grafo a la vista
    const [cx, cy] = await p.evaluate(() => { const c = [...document.querySelectorAll(".nodo__circulo")].map((n) => n.getBoundingClientRect()).find((b) => b.left > 40 && b.right < innerWidth - 40 && b.top > 0 && b.bottom < innerHeight); return [c.x + c.width / 2, c.y + c.height / 2]; });
    await enviar("touchStart", [[cx - 30, cy], [cx + 30, cy]]);
    for (let i = 1; i <= 10; i++) { await enviar("touchMove", [[cx - 30 - i * 6, cy], [cx + 30 + i * 6, cy]]); await p.waitForTimeout(16); }
    await enviar("touchEnd", []);
    await p.waitForTimeout(150);
    const zoom = await medirVista(p);
    assert.ok(zoom.vb[2] < antes.vb[2] * 0.6, `acercó: ancho visible ${antes.vb[2].toFixed(0)} → ${zoom.vb[2].toFixed(0)}`);
    assert.equal(zoom.scrollY, antes.scrollY, "la página no se movió");
    assert.match(zoom.clase, /lienzo--ampliado/);
    // un dedo: arrastre horizontal y vertical del grafo ampliado
    await p.waitForTimeout(500);
    const libre = await puntoLibre(p);
    assert.ok(libre, "hay un punto libre para arrastrar");
    await arrastrar(p, enviar, [libre[0], libre[1]], [libre[0] - 40, libre[1]]);
    const h = await medirVista(p);
    assert.ok(Math.abs(h.vb[0] - zoom.vb[0]) > 5, "el grafo se desplazó en horizontal");
    const libre2 = await puntoLibre(p);
    await arrastrar(p, enviar, [libre2[0], libre2[1]], [libre2[0], libre2[1] + 50]);
    const v = await medirVista(p);
    assert.ok(Math.abs(v.vb[1] - h.vb[1]) > 5, "el grafo se desplazó en vertical");
    assert.equal(v.scrollY, antes.scrollY, "la página no se movió mientras se desplazaba el grafo");
    // pellizco para alejar: no pasa del grafo completo ×1.5
    await p.waitForTimeout(500);
    await enviar("touchStart", [[cx - 100, cy], [cx + 100, cy]]);
    for (let i = 1; i <= 12; i++) { await enviar("touchMove", [[cx - 100 + i * 8, cy], [cx + 100 - i * 8, cy]]); await p.waitForTimeout(16); }
    await enviar("touchEnd", []);
    await p.waitForTimeout(150);
    const lejos = await medirVista(p);
    assert.ok(lejos.vb[2] > zoom.vb[2] * 1.5, "alejó con el pellizco");
    assert.deepEqual(p.errores, []);
    await p.cerrar();
  });

  test("con el grafo completo a la vista, arrastrar en vertical sobre el lienzo desplaza la página y no el grafo", async () => {
    const p = await abrir({ ancho: 390, alto: 844, tactil: true });
    await aSimulacionTactil(p, 10);
    await p.tap(t("ajustar-grafo"));
    await p.waitForTimeout(600);
    const enviar = await toque(p);
    const antes = await medirVista(p);
    assert.doesNotMatch(antes.clase, /lienzo--recortado/);
    const libre = await puntoLibre(p);
    assert.ok(libre, "hay un punto libre para arrastrar");
    await arrastrar(p, enviar, [libre[0], libre[1] + 40], [libre[0], libre[1] - 160]);
    const despues = await medirVista(p);
    assert.ok(despues.scrollY > 50, `la página se desplazó (${despues.scrollY}px)`);
    assert.deepEqual(despues.vb, antes.vb, "el grafo no se movió");
    await p.cerrar();
  });

  test("un dedo sobre un vértice lo arrastra en el editor sin desplazar la página; el toque simple lo selecciona", async () => {
    const p = await abrir({ ancho: 390, alto: 844, tactil: true });
    await p.tap(t("empezar"));
    await p.selectOption(t("num-nodos"), "7");
    await p.tap(t("manual"));
    await p.waitForSelector("[data-pantalla=editor]");
    await p.waitForTimeout(400);
    await p.tap(t("ajustar-grafo"));
    await p.waitForTimeout(200);
    const enviar = await toque(p);
    const pos = () => p.evaluate(() => { const c = document.querySelector('.nodo[data-v="A"] circle').getBoundingClientRect(); return [c.x + c.width / 2, c.y + c.height / 2, window.scrollY]; });
    const a0 = await pos();
    await arrastrar(p, enviar, [a0[0], a0[1]], [a0[0] + 20, a0[1] + 50]);
    const a1 = await pos();
    assert.ok(Math.hypot(a1[0] - a0[0], a1[1] - a0[1]) > 20, "el vértice se movió");
    assert.equal(a1[2], a0[2], "la página no se desplazó");
    await p.tap('.nodo[data-v="A"]');
    await p.tap('.nodo[data-v="B"]');
    assert.equal(await p.locator(".nodo--seleccion").count(), 2, "dos toques seleccionan origen y destino");
    await p.fill(t("peso-nuevo"), "4");
    await p.tap(t("crear-conexion"));
    assert.equal(await p.locator(".arista-fila").count(), 1);
    await p.cerrar();
  });

  test("el tutorial cabe en la pantalla y no se sale del área visible en ningún paso", async () => {
    for (const [ancho, alto] of PANTALLAS) {
      const p = await abrir({ ancho, alto, tactil: true });
      await p.tap(t("tutorial"));
      await p.waitForSelector(t("tutorial-tarjeta"));
      for (let i = 0; i < 40; i++) {
        await p.waitForTimeout(330);
        const m = await p.evaluate(() => { const r = document.querySelector("[data-testid=tutorial-tarjeta]").getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom, vw: innerWidth, vh: innerHeight }; });
        assert.ok(m.l >= 0 && m.t >= 0 && m.r <= m.vw && m.b <= m.vh, `tarjeta visible en el paso ${i + 1} (${ancho}×${alto}): ${JSON.stringify(m)}`);
        const sig = p.locator(t("tut-siguiente"));
        if ((await sig.innerText()).startsWith("Finalizar")) { await sig.tap(); break; }
        await sig.tap();
      }
      assert.equal(await p.locator(t("tutorial-overlay")).count(), 0, "el tutorial terminó");
      await p.cerrar();
    }
  });

  test("escritorio intacto: botones con texto, barra con la cabecera fija y selectores a su tamaño", async () => {
    const p = await abrir({});
    await aSimulacionAuto(p, 8);
    const m = await p.evaluate(() => ({
      textos: ["reiniciar", "ir-al-final", "alternar-tabla"].map((id) => document.querySelector(`[data-testid="${id}"]`).innerText.trim()),
      cabecera: getComputedStyle(document.querySelector(".cabecera")).position,
      campo: parseFloat(getComputedStyle(document.querySelector("select.campo")).fontSize),
      iconoTabla: getComputedStyle(document.querySelector(".icono--tabla")).display,
    }));
    assert.deepEqual(m.textos, ["Reiniciar", "Ir al final", "Ocultar tabla del proceso"]);
    assert.equal(m.cabecera, "sticky");
    assert.ok(m.campo < 16);
    assert.equal(m.iconoTabla, "none", "el icono de la tabla solo se usa en el celular");
    await p.cerrar();
  });
});
