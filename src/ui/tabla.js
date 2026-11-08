/**
 * Tabla del proceso: una fila por vértice y una columna por iteración. No guarda estado propio:
 * `mostrar(snapshot)` vuelca las celdas del snapshot (vigente / empate / descartada).
 */

import { DESCARTADA, EMPATE } from "../core/index.js";
import { el } from "./dom.js";

export class TablaProceso {
  constructor(contenedor) {
    this.contenedor = contenedor;
    this.celdas = new Map();
    this.limpiar();
  }

  limpiar() {
    this.celdas.clear();
    this.contenedor.replaceChildren(el("p", { clase: "lista-aristas__vacia", "data-testid": "tabla-vacia", texto: "La tabla se llenará al ejecutar Dijkstra." }));
  }

  construir(vertices, iteraciones) {
    this.celdas.clear();
    const cab = el("tr", {}, el("th", { clase: "celda celda--cab", texto: "Vértice" }));
    const its = Array.from({ length: iteraciones + 1 }, (_, i) => i);
    for (const i of its) cab.append(el("th", { clase: "celda celda--cab", texto: `Iteración ${i}` }));
    const cuerpo = el("tbody");
    for (const v of vertices) {
      const fila = el("tr", { "data-vertice": v }, el("td", { clase: "celda celda--cab", texto: v }));
      for (const i of its) {
        const c = el("td", { clase: "celda", "data-celda": `${v}:${i}` });
        this.celdas.set(`${v}:${i}`, c);
        fila.append(c);
      }
      cuerpo.append(fila);
    }
    this.contenedor.replaceChildren(el("table", { clase: "tabla", "data-testid": "tabla" }, el("thead", {}, cab), cuerpo));
  }

  mostrar(snapshot) {
    for (const c of this.celdas.values()) {
      c.textContent = "";
      c.className = "celda";
    }
    for (const e of snapshot.tabla) {
      const c = this.celdas.get(`${e.vertice}:${e.iteracion}`);
      if (!c) continue;
      c.textContent = e.texto;
      c.className = `celda celda--${e.estado === DESCARTADA ? "descartada" : e.estado === EMPATE ? "empate" : "vigente"}`;
    }
  }
}
