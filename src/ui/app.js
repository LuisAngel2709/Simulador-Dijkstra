/** Orquestación: pantallas, navegación, tema y tutorial. Sin lógica del algoritmo. */

import { Grafo, generarDagDidactico, sugerirExtremos } from "../core/index.js";
import { PantallaEditor } from "./editor.js";
import { el, svg, vaciar } from "./dom.js";
import { icono } from "./iconos.js";
import { PantallaBienvenida, PantallaConfiguracion } from "./pantallas.js";
import { PantallaSimulacion } from "./simulacion.js";
import { Tema } from "./tema.js";
import { Tutorial } from "./tutorial.js";
import { pasosBienvenida, pasosConfiguracion, pasosEditor, pasosSimulacion } from "./tutorial-pasos.js";

export class App {
  constructor(raiz) {
    this.raiz = raiz;
    this.pantalla = null;
    this.nombre = null;
    this.tutorial = null;
    this.extremosManuales = null; // lo que el usuario eligió en los menús para el grafo actual
    this.nodos = 8;

    this.tema = new Tema(() => this._actualizarBotonTema());
    this.botonTema = el("button", { clase: "boton boton--sec boton--icono", type: "button", "data-testid": "tema", onClick: () => this.tema.alternar() });
    this.botonTutorial = el("button", { clase: "boton boton--sec", type: "button", "data-testid": "tutorial", "aria-label": "Tutorial", onClick: () => this.abrirTutorial() }, icono("ayuda", { tam: 17 }), el("span", { clase: "boton-texto", texto: "Tutorial" }));
    this.contenido = el("main", { clase: "principal", id: "contenido" });
    const logo = svg(
      "svg", { clase: "cabecera__logo", viewBox: "0 0 32 32", "aria-hidden": "true" },
      svg("rect", { width: 32, height: 32, rx: 8, fill: "#2563eb" }),
      svg("path", { d: "M8 22 L16 10 L24 22", fill: "none", stroke: "#fff", "stroke-width": 2.2, "stroke-linecap": "round", "stroke-linejoin": "round" }),
      svg("circle", { cx: 8, cy: 22, r: 3.2, fill: "#bbf7d0" }), svg("circle", { cx: 16, cy: 10, r: 3.2, fill: "#fef08a" }), svg("circle", { cx: 24, cy: 22, r: 3.2, fill: "#fbcfe8" }),
    );
    this.cabecera = el(
      "header", { clase: "cabecera" }, el("div", { clase: "cabecera__marca" }, logo, "Simulador de Dijkstra"),
      el("div", { clase: "cabecera__espacio" }), this.botonTutorial, this.botonTema,
    );
    vaciar(raiz).append(el("div", { clase: "app" }, this.cabecera, this.contenido));
    this._actualizarBotonTema();
    this.irABienvenida();
  }

  _actualizarBotonTema() {
    const oscuro = this.tema.actual === "oscuro";
    this.botonTema.replaceChildren(icono(oscuro ? "sol" : "luna", { tam: 19 }));
    this.botonTema.title = oscuro ? "Cambiar a tema claro" : "Cambiar a tema oscuro";
    this.botonTema.setAttribute("aria-label", this.botonTema.title);
  }

  _mostrar(nombre, pantalla) {
    this.tutorial?.cerrar();
    this.pantalla?.destruir();
    this.pantalla = pantalla;
    this.nombre = nombre;
    this.contenido.replaceChildren(pantalla.elemento);
    window.scrollTo(0, 0);
    document.title = "Simulador de Dijkstra";
  }

  irABienvenida() {
    this.extremosManuales = null;
    this._mostrar("bienvenida", new PantallaBienvenida({ alEmpezar: () => this.irAConfiguracion() }));
  }

  irAConfiguracion() {
    this.extremosManuales = null;
    this._mostrar("configuracion", new PantallaConfiguracion({
      nodosIniciales: this.nodos,
      alGenerar: (n) => { this.nodos = n; this.generar(n); },
      alCrearManual: (n) => { this.nodos = n; this.irAEditor(new Grafo(n)); },
      alVolver: () => this.irABienvenida(),
    }));
  }

  generar(n) {
    const [grafo, origen, destino] = generarDagDidactico(n);
    this.extremosManuales = null;
    this.irASimulacion(grafo, null, [origen, destino], "← Configuración");
  }

  irAEditor(grafo, posiciones = null) {
    this._mostrar("editor", new PantallaEditor({
      grafo, posiciones, extremos: (g) => this._extremosPara(g),
      alVolver: () => this.irAConfiguracion(),
      alFinalizar: (g, pos) => this.irASimulacion(g, pos, this._extremosPara(g), "← Editar grafo"),
    }));
  }

  _extremosPara(grafo) {
    const m = this.extremosManuales;
    if (m && grafo.vertices.includes(m[0]) && grafo.vertices.includes(m[1])) return m;
    return sugerirExtremos(grafo);
  }

  irASimulacion(grafo, posiciones, [origen, destino], textoVolver) {
    this._mostrar("simulacion", new PantallaSimulacion({
      grafo, posiciones, origen, destino, textoVolver,
      alCambiarExtremos: (o, d) => { this.extremosManuales = [o, d]; },
      alVolver: (pos) => (textoVolver === "← Editar grafo" ? this.irAEditor(grafo, pos) : this.irAConfiguracion()),
    }));
  }

  abrirTutorial() {
    if (this.tutorial) return;
    const p = this.pantalla;
    const pasos = {
      bienvenida: () => pasosBienvenida(p, { botonTutorial: this.botonTutorial, botonTema: this.botonTema }),
      configuracion: () => pasosConfiguracion(p),
      editor: () => pasosEditor(p),
      simulacion: () => pasosSimulacion(p),
    }[this.nombre]();
    this.tutorial = new Tutorial(pasos, { alCerrar: () => { this.tutorial = null; } });
  }
}
