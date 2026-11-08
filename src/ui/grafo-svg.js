/**
 * Componente SVG del grafo: dibuja vértices, aristas dirigidas, pesos, marcas y etiquetas de
 * Dijkstra; permite arrastrar vértices, hacer clic en vértices y en pesos, y editar un peso en línea.
 *
 * No calcula nada del algoritmo: solo pinta el `Snapshot` que le dan. Los colores vienen de clases
 * CSS (variables), así el cambio de tema no necesita redibujar.
 */

import { INFINITO } from "../core/index.js";
import { el, svg } from "./dom.js";
import { icono } from "./iconos.js";
import {
  ALTO, ANCHO, RADIO, ALTO_LINEA, anchoTexto, claveArista, colocarRotulos, geometriaAristas, limitar,
  posicionesCirculares, posicionesPorCapas,
} from "./layout.js";

const UMBRAL_ARRASTRE = 4;
// En pantallas estrechas (celulares) la vista inicial no baja de esta escala (px por unidad del mundo):
// así los nodos, pesos y etiquetas siguen siendo legibles y el resto del grafo se alcanza con arrastre o zoom.
const PISO_ESCALA = 0.65;
const ANCHO_MOVIL = 700;

export class GrafoSvg {
  /**
   * @param {HTMLElement} contenedor
   * @param {{alClicNodo?: Function, alClicPeso?: Function, arrastrable?: boolean, etiqueta?: string}} [opciones]
   */
  constructor(contenedor, { alClicNodo = null, alClicPeso = null, arrastrable = true, etiqueta = "Grafo" } = {}) {
    this.contenedor = contenedor;
    this.alClicNodo = alClicNodo;
    this.alClicPeso = alClicPeso;
    this.arrastrable = arrastrable;
    this.grafo = null;
    this.pos = {};
    this.snapshot = null;
    this.origen = null;
    this.destino = null;
    this.seleccionEditor = [];
    this.reserva = {}; // vértice → {ancho, lineas}
    this.mostrarEtiquetas = false;
    this.preview = null; // {origen, destino, cursor}
    this.ultimo = null; // última geometría y rótulos (para pruebas y editor en línea)
    this._pendiente = null;
    this._editor = null;
    this.vista = null; // {x, y, w, h}: región visible del mundo (viewBox)
    this.ajuste = null; // la vista que muestra todo el contenido
    this.vistaManual = false; // true si el usuario hizo zoom o desplazamiento
    this._arrastrando = false;
    this._toques = new Map(); // punteros táctiles activos (pellizco de dos dedos)
    this._pinza = null;
    this._gestoActual = null;
    this.ajusteTodo = null; // la vista que muestra todo el contenido (puede ser más amplia que `ajuste`)

    this.svg = svg("svg", {
      clase: "grafo-svg", viewBox: `0 0 ${ANCHO} ${ALTO}`, preserveAspectRatio: "xMidYMid meet",
      role: "img", "aria-label": etiqueta, "data-testid": "grafo",
    });
    this.capaAristas = svg("g", { clase: "capa-aristas" });
    this.capaPreview = svg("g", { clase: "capa-preview" });
    this.capaPesos = svg("g", { clase: "capa-pesos" });
    this.capaNodos = svg("g", { clase: "capa-nodos" });
    this.capaRotulos = svg("g", { clase: "capa-rotulos" });
    this.svg.append(this.capaAristas, this.capaPreview, this.capaNodos, this.capaPesos, this.capaRotulos);
    contenedor.classList.add("lienzo");
    contenedor.append(this.svg);

    this.svg.addEventListener("pointerdown", (e) => { this._registrarToque(e); this._alPresionar(e); });
    // `touch-action` no sirve sobre elementos internos del SVG: un dedo sobre un vértice se reserva aquí para arrastrarlo
    // (si no, el navegador empezaría a desplazar la página). El toque simple se resuelve en `_alPresionar`.
    this.svg.addEventListener("touchstart", (e) => { if (this.arrastrable && e.touches.length === 1 && e.target.closest?.("[data-v]")) e.preventDefault(); }, { passive: false });
    this.svg.addEventListener("pointermove", (e) => this._alMoverRaton(e));
    this.svg.addEventListener("pointerleave", () => this._cursorFuera());
    this.svg.addEventListener("click", (e) => this._alHacerClic(e));
    this.svg.addEventListener("wheel", (e) => this._alRueda(e), { passive: false });
    this.svg.addEventListener("dblclick", (e) => { if (!e.target.closest?.("[data-v], [data-peso]")) this.ajustar(true); });

    this.botonAjustar = el(
      "button", { clase: "lienzo__ajustar", type: "button", "aria-label": "Ajustar grafo", "data-testid": "ajustar-grafo", onClick: () => this.ajustar(true) },
      icono("maximizar", { tam: 18 }), el("span", { clase: "lienzo__tip", "aria-hidden": "true", texto: "Ajustar grafo" }),
    );
    contenedor.append(this.botonAjustar);
    // Si el área cambia de tamaño (ventana, paneles), la vista se reajusta sola salvo que el usuario la haya movido.
    this._observador = typeof ResizeObserver === "function" ? new ResizeObserver(() => this._alRedimensionar()) : null;
    this._observador?.observe(contenedor);
  }

  /* ------------------------------------------------------------- vista (zoom) */

  _tamano() {
    const r = this.svg.getBoundingClientRect();
    return [r.width, r.height];
  }

  /** Rectángulo del mundo que contiene vértices, aristas, pesos, marcas y etiquetas. */
  _cajaContenido() {
    if (!this.ultimo || !this.grafo) return null;
    let x0 = Infinity; let y0 = Infinity; let x1 = -Infinity; let y1 = -Infinity;
    const punto = (x, y) => { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); };
    for (const v of this.grafo.vertices) {
      const [x, y] = this.pos[v];
      punto(x - RADIO - 3, y - RADIO - 3);
      punto(x + RADIO + 3, y + RADIO + 3);
    }
    for (const g of this.ultimo.geometria.values()) for (const [x, y] of g.puntos) punto(x, y);
    const { pesos, marcas, etiquetas } = this.ultimo.rotulos;
    for (const mapa of [pesos, marcas, etiquetas]) for (const r of mapa.values()) { punto(r.x - r.w / 2, r.y - r.h / 2); punto(r.x + r.w / 2, r.y + r.h / 2); }
    return Number.isFinite(x0) ? { x: x0, y: y0, w: x1 - x0, h: y1 - y0 } : null;
  }

  /** Vista que muestra todo el contenido, centrado y con margen, para un área de `cw`×`ch` píxeles. */
  _vistaTodo(caja, cw, ch) {
    const margen = 20;
    const bw = caja.w + 2 * margen;
    const bh = caja.h + 2 * margen;
    let w = bw;
    let h = bh;
    if (bw / bh > cw / ch) h = (bw * ch) / cw;
    else w = (bh * cw) / ch;
    return { x: caja.x + caja.w / 2 - w / 2, y: caja.y + caja.h / 2 - h / 2, w, h };
  }

  /**
   * Muestra el grafo completo, centrado y con margen, usando todo el espacio disponible.
   * En un celular, si al mostrarlo todo la escala bajara de PISO_ESCALA, se parte de una vista más cercana
   * (empezando por el lado izquierdo/superior del grafo) para que el texto siga siendo legible;
   * `todo = true` fuerza ver el grafo completo (botón «Ajustar grafo»).
   */
  ajustar(todo) {
    if (todo !== undefined) this._verTodo = todo;
    todo = !!this._verTodo;
    const caja = this._cajaContenido();
    const [cw, ch] = this._tamano();
    if (!caja || cw < 20 || ch < 20) return;
    const completa = this._vistaTodo(caja, cw, ch);
    let vista = completa;
    if (!todo && cw <= ANCHO_MOVIL && cw / completa.w < PISO_ESCALA) {
      const w = cw / PISO_ESCALA;
      const h = ch / PISO_ESCALA;
      const margen = 20;
      vista = {
        x: w >= caja.w + 2 * margen ? caja.x + caja.w / 2 - w / 2 : caja.x - margen,
        y: h >= caja.h + 2 * margen ? caja.y + caja.h / 2 - h / 2 : caja.y - margen,
        w, h,
      };
    }
    this.vistaManual = false;
    this.ajusteTodo = completa;
    this.ajuste = vista;
    this._aplicarVista(vista);
  }

  /** Mantiene un vértice arrastrado dentro de la región visible (con margen para sus rótulos). */
  _dentroDeLaVista([x, y]) {
    const v = this.vista;
    if (!v) return [x, y];
    const m = RADIO + 26;
    return [Math.min(v.x + v.w - m, Math.max(v.x + m, x)), Math.min(v.y + v.h - m, Math.max(v.y + m, y))];
  }

  /** Desplazamiento [dx, dy] mínimo que haría entrar el vértice más cercano en la vista `v` ([0, 0] si ya hay uno a la vista). */
  _faltaParaVerUnNodo(v) {
    const m = Math.min(RADIO + 12, v.w / 4, v.h / 4);
    let mejor = null;
    for (const u of this.grafo.vertices) {
      const [px, py] = this.pos[u];
      const dx = px < v.x + m ? px - (v.x + m) : px > v.x + v.w - m ? px - (v.x + v.w - m) : 0;
      const dy = py < v.y + m ? py - (v.y + m) : py > v.y + v.h - m ? py - (v.y + v.h - m) : 0;
      if (dx === 0 && dy === 0) return [0, 0];
      if (!mejor || Math.abs(dx) + Math.abs(dy) < Math.abs(mejor[0]) + Math.abs(mejor[1])) mejor = [dx, dy];
    }
    return mejor ?? [0, 0];
  }

  /**
   * Al desplazar (un dedo, ratón o pellizco) el grafo no puede salir del lienzo: siempre queda a la vista al menos
   * un vértice. Solo se frena el movimiento que alejaría más el grafo; acercarlo o hacer zoom nunca se bloquea.
   */
  _desplazamientoLimitado(nueva) {
    if (!this.grafo?.vertices.length || !this.vista) return nueva;
    const [nx, ny] = this._faltaParaVerUnNodo(nueva);
    if (nx === 0 && ny === 0) return nueva;
    const [ax, ay] = this._faltaParaVerUnNodo(this.vista);
    if (Math.abs(nx) + Math.abs(ny) <= Math.abs(ax) + Math.abs(ay)) return nueva; // se acerca o se mantiene
    if (ax === 0 && ay === 0) return { ...nueva, x: nueva.x + nx, y: nueva.y + ny }; // tope: el último vértice queda en el borde
    return this.vista;
  }

  _aplicarVista(v) {
    this.vista = v;
    this.svg.setAttribute("viewBox", `${v.x.toFixed(2)} ${v.y.toFixed(2)} ${v.w.toFixed(2)} ${v.h.toFixed(2)}`);
    this.contenedor.classList.toggle("lienzo--ampliado", this.vistaManual);
    this.contenedor.classList.toggle("lienzo--recortado", !!this.ajusteTodo && v.w < this.ajusteTodo.w * 0.98);
  }

  _alRedimensionar() {
    if (!this.grafo) return;
    if (!this.vistaManual) { this.ajustar(); return; }
    // Vista manual: se conserva el centro y el zoom, solo se adapta la proporción.
    const [cw, ch] = this._tamano();
    if (cw < 20 || ch < 20 || !this.vista) return;
    const v = this.vista;
    const h = (v.w * ch) / cw;
    this._aplicarVista({ x: v.x, y: v.y + v.h / 2 - h / 2, w: v.w, h });
    const caja = this._cajaContenido();
    if (caja) this.ajusteTodo = this.ajuste = this._vistaTodo(caja, cw, ch);
  }

  _zoom(factor, [px, py]) {
    const v = this.vista;
    if (!v) return;
    const base = this.ajusteTodo ?? this.ajuste ?? v;
    const w = Math.min(base.w * 1.5, Math.max(base.w / 8, v.w / factor));
    const k = w / v.w;
    this.vistaManual = true;
    this.cerrarEditorPeso(false);
    this._aplicarVista({ x: px - (px - v.x) * k, y: py - (py - v.y) * k, w, h: v.h * k });
  }

  _alRueda(e) {
    if (!this.vista) return;
    e.preventDefault(); // el zoom ocurre dentro del grafo: la página no se desplaza
    this._zoom(Math.exp(-Math.sign(e.deltaY) * Math.min(Math.abs(e.deltaY), 120) * 0.0016), this._puntoVirtual(e));
  }

  _iniciarDesplazamiento(e) {
    const inicio = [e.clientX, e.clientY];
    const v0 = { ...this.vista };
    const [cw] = this._tamano();
    let moviendo = false;
    const mover = (ev) => {
      if (this._pinza) return;
      // Con el grafo completo a la vista, un dedo que se mueve en vertical desplaza la página, no el grafo.
      if (!moviendo && ev.pointerType === "touch" && !this.contenedor.classList.contains("lienzo--recortado")
        && Math.abs(ev.clientY - inicio[1]) > Math.abs(ev.clientX - inicio[0])) return;
      if (!moviendo && Math.hypot(ev.clientX - inicio[0], ev.clientY - inicio[1]) < UMBRAL_ARRASTRE) return;
      moviendo = true;
      this.vistaManual = true;
      this.contenedor.classList.add("lienzo--desplazando");
      this.cerrarEditorPeso(false);
      const esc = v0.w / cw;
      this._aplicarVista(this._desplazamientoLimitado({ ...v0, x: v0.x - (ev.clientX - inicio[0]) * esc, y: v0.y - (ev.clientY - inicio[1]) * esc }));
    };
    const soltar = () => {
      window.removeEventListener("pointermove", mover);
      window.removeEventListener("pointerup", soltar);
      window.removeEventListener("pointercancel", soltar);
      this.contenedor.classList.remove("lienzo--desplazando");
      if (this._gestoActual === soltar) this._gestoActual = null;
    };
    this._gestoActual = soltar;
    window.addEventListener("pointermove", mover);
    window.addEventListener("pointerup", soltar);
    window.addEventListener("pointercancel", soltar);
  }

  /* ---------------------------------------------- táctil: pellizco con dos dedos */

  _registrarToque(e) {
    if (e.pointerType !== "touch") return;
    this._toques.set(e.pointerId, [e.clientX, e.clientY]);
    if (!this._escuchaToques) this._escucharToques();
    if (this._toques.size === 2 && this.vista) this._iniciarPinza();
  }

  _escucharToques() {
    this._escuchaToques = true;
    const mover = (ev) => {
      if (!this._toques.has(ev.pointerId)) return;
      this._toques.set(ev.pointerId, [ev.clientX, ev.clientY]);
      if (this._pinza) this._moverPinza();
    };
    const soltar = (ev) => {
      this._toques.delete(ev.pointerId);
      if (this._toques.size < 2 && this._pinza) { this._pinza = null; this.contenedor.classList.remove("lienzo--desplazando"); }
      if (!this._toques.size) {
        window.removeEventListener("pointermove", mover);
        window.removeEventListener("pointerup", soltar);
        window.removeEventListener("pointercancel", soltar);
        this._escuchaToques = false;
      }
    };
    window.addEventListener("pointermove", mover);
    window.addEventListener("pointerup", soltar);
    window.addEventListener("pointercancel", soltar);
  }

  _puntosPinza() {
    const [a, b] = [...this._toques.values()];
    return { d: Math.hypot(a[0] - b[0], a[1] - b[1]) || 1, cx: (a[0] + b[0]) / 2, cy: (a[1] + b[1]) / 2 };
  }

  _iniciarPinza() {
    this._gestoActual?.(); // cancela el arrastre de un dedo en curso
    this.cerrarEditorPeso(false);
    const [cw] = this._tamano();
    const caja = this.svg.getBoundingClientRect();
    const p = this._puntosPinza();
    const v0 = { ...this.vista };
    // Punto del mundo que está bajo el centro de los dedos al empezar.
    this._pinza = { d0: p.d, v0, caja, wx: v0.x + ((p.cx - caja.left) * v0.w) / cw, wy: v0.y + ((p.cy - caja.top) * v0.w) / cw };
    this.contenedor.classList.add("lienzo--desplazando");
  }

  _moverPinza() {
    const z = this._pinza;
    if (!z || this._toques.size < 2) return;
    const [cw, ch] = this._tamano();
    const p = this._puntosPinza();
    const base = this.ajusteTodo ?? this.ajuste ?? z.v0;
    const w = Math.min(base.w * 1.5, Math.max(base.w / 8, z.v0.w / (p.d / z.d0)));
    const esc = w / cw;
    this.vistaManual = true;
    this._aplicarVista(this._desplazamientoLimitado({ x: z.wx - (p.cx - z.caja.left) * esc, y: z.wy - (p.cy - z.caja.top) * esc, w, h: (w * ch) / cw }));
  }

  /* ----------------------------------------------------------------- estado */

  /** @param {{posiciones?: object|null, modo?: "capas"|"circular"}} [o] */
  establecerGrafo(grafo, { posiciones = null, modo = "capas" } = {}) {
    this.grafo = grafo;
    const conservadas = posiciones ?? this.pos;
    const completo = grafo.vertices.every((v) => conservadas[v]);
    if (completo) {
      this.pos = Object.fromEntries(grafo.vertices.map((v) => [v, limitar(conservadas[v])]));
    } else {
      this.pos = modo === "circular" ? posicionesCirculares(grafo.vertices) : posicionesPorCapas(grafo);
    }
    this.cerrarEditorPeso();
    this.vistaManual = false;
    this.redibujar();
  }

  /** Cambia solo lo indicado (snapshot, origen, destino, seleccionEditor, mostrarEtiquetas) y redibuja. */
  actualizarEstado(cambios) {
    for (const k of ["snapshot", "origen", "destino", "seleccionEditor", "mostrarEtiquetas"]) {
      if (k in cambios) this[k] = cambios[k];
    }
    this.redibujar();
  }

  /** Reserva de espacio para las etiquetas: el máximo que cada vértice llegará a necesitar. */
  establecerReserva(resultado) {
    this.reserva = {};
    this.vistaManual = false;
    if (!resultado) return;
    for (const v of this.grafo.vertices) {
      let ancho = 0;
      let lineas = 1;
      for (const s of resultado.snapshots) {
        ancho = Math.max(ancho, anchoTexto(s.etiqueta(v)));
        const d = s.etiquetasDescartadas.filter(([x]) => x === v);
        if (d.length) {
          lineas = Math.max(lineas, 1 + d.length);
          for (const [, t] of d) ancho = Math.max(ancho, anchoTexto(t));
        }
      }
      this.reserva[v] = { ancho, lineas };
    }
  }

  establecerPreview(preview) {
    this.preview = preview;
    this._dibujarPreview();
  }

  obtenerPosiciones() {
    return Object.fromEntries(Object.entries(this.pos).map(([v, p]) => [v, [...p]]));
  }

  reorganizarEnCirculo() {
    this.pos = posicionesCirculares(this.grafo.vertices);
    this.redibujar();
  }

  reorganizarPorCapas() {
    this.pos = posicionesPorCapas(this.grafo);
    this.redibujar();
  }

  /* --------------------------------------------------------------- dibujo */

  redibujar() {
    if (!this.grafo) return;
    this.cerrarEditorPeso(false);
    const geometria = geometriaAristas(this.grafo, this.pos);
    const marcas = {};
    for (const v of this.grafo.vertices) {
      const t = this._textoMarca(v);
      if (t) marcas[v] = t;
    }
    const etiquetas = {};
    if (this.mostrarEtiquetas && this.snapshot) {
      for (const v of this.grafo.vertices) etiquetas[v] = this.reserva[v] ?? { ancho: anchoTexto(this.snapshot.etiqueta(v)), lineas: 2 };
    }
    const rotulos = colocarRotulos({ pos: this.pos, geometria, marcas, etiquetas });
    this.ultimo = { geometria, rotulos };

    this.capaAristas.replaceChildren(...[...geometria.values()].map((g) => this._aristaSvg(g)));
    this.capaPesos.replaceChildren(...[...geometria.values()].map((g) => this._pesoSvg(g, rotulos.pesos.get(claveArista(g.u, g.v)))));
    this.capaNodos.replaceChildren(...this.grafo.vertices.map((v) => this._nodoSvg(v)));
    const rot = [];
    for (const [v, r] of rotulos.marcas) rot.push(this._marcaSvg(v, r));
    if (this.mostrarEtiquetas && this.snapshot) {
      for (const [v, r] of rotulos.etiquetas) rot.push(this._etiquetaSvg(v, r));
    }
    this.capaRotulos.replaceChildren(...rot);
    this._dibujarPreview();
    // Tras soltar un vértice la vista no salta: durante el arrastre el vértice no puede salir del área visible.
    if (this._trasArrastre) this._trasArrastre = false;
    else if (!this.vistaManual && !this._arrastrando) this.ajustar();
    this.svg.setAttribute("aria-label", `Grafo de ${this.grafo.n} vértices y ${this.grafo.cantidadAristas()} aristas`);
  }

  _textoMarca(v) {
    if (this.origen !== null && v === this.origen && v === this.destino) return "ORIGEN · DESTINO";
    if (this.origen !== null && v === this.origen) return "ORIGEN";
    if (this.destino !== null && v === this.destino) return "DESTINO";
    return null;
  }

  _estadoArista(u, v) {
    const s = this.snapshot;
    if (s) {
      if (s.aristasCamino.some(([a, b]) => a === u && b === v)) return "camino";
      for (const [a, b, tipo] of s.aristasEvaluadas) {
        if (a === u && b === v) return tipo === "mejora" ? "evaluada" : tipo === "empate" ? "empate" : "descartada";
      }
    }
    return "normal";
  }

  _aristaSvg(g) {
    const estado = this._estadoArista(g.u, g.v);
    const d = g.puntos.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
    const [tx, ty] = g.puntos[g.puntos.length - 1];
    const a = g.angulo;
    const bx = tx - 12 * Math.cos(a);
    const by = ty - 12 * Math.sin(a);
    const nx = -Math.sin(a) * 5.5;
    const ny = Math.cos(a) * 5.5;
    return svg(
      "g", { clase: `arista arista--${estado}`, "data-arista": claveArista(g.u, g.v), "data-estado": estado },
      svg("path", { d, clase: "arista__linea" }),
      svg("polygon", { clase: "arista__punta", points: `${tx.toFixed(1)},${ty.toFixed(1)} ${(bx + nx).toFixed(1)},${(by + ny).toFixed(1)} ${(bx - nx).toFixed(1)},${(by - ny).toFixed(1)}` }),
    );
  }

  _pesoSvg(g, r) {
    const estado = this._estadoArista(g.u, g.v);
    const editable = !!this.alClicPeso;
    return svg(
      "g",
      {
        clase: `peso peso--${estado}${editable ? " peso--editable" : ""}`, "data-peso": claveArista(g.u, g.v),
        transform: `translate(${r.x.toFixed(1)} ${r.y.toFixed(1)})`,
      },
      svg("rect", { x: -r.w / 2, y: -r.h / 2, width: r.w, height: r.h, rx: 5, clase: "peso__caja" }),
      svg("text", { clase: "peso__texto", "text-anchor": "middle", "dominant-baseline": "central", texto: String(g.peso) }),
      svg("ellipse", { rx: r.w / 2 + 8, ry: r.h / 2 + 8, clase: "zona-tactil" }),
    );
  }

  _colorNodo(v) {
    const s = this.snapshot;
    if (this.seleccionEditor.includes(v)) return "seleccion";
    if (s && s.seleccionado === v && !s.esFinal) return "actual";
    if (v === this.origen) return "origen";
    if (v === this.destino) return "destino";
    if (s && s.visitados.has(v)) return "visitado";
    return "normal";
  }

  _nodoSvg(v) {
    const [x, y] = this.pos[v];
    const estado = this._colorNodo(v);
    return svg(
      "g",
      {
        clase: `nodo nodo--${estado}${this.arrastrable ? " nodo--arrastrable" : ""}`, "data-v": v, "data-estado": estado,
        transform: `translate(${x.toFixed(1)} ${y.toFixed(1)})`,
      },
      svg("circle", { r: RADIO, clase: "nodo__circulo" }),
      svg("text", { clase: "nodo__texto", "text-anchor": "middle", "dominant-baseline": "central", texto: v }),
      svg("ellipse", { rx: RADIO + 9, ry: RADIO + 9, clase: "zona-tactil" }),
    );
  }

  _marcaSvg(v, r) {
    const texto = this._textoMarca(v);
    const tipo = v === this.origen ? "origen" : "destino";
    return svg(
      "g", { clase: `marca marca--${tipo}`, "data-marca": v, transform: `translate(${r.x.toFixed(1)} ${r.y.toFixed(1)})` },
      svg("rect", { x: -r.w / 2, y: -r.h / 2, width: r.w, height: r.h, rx: 9, clase: "marca__caja" }),
      svg("text", { clase: "marca__texto", "text-anchor": "middle", "dominant-baseline": "central", texto }),
    );
  }

  _etiquetaSvg(v, r) {
    const s = this.snapshot;
    const dist = s.distancias[v] ?? INFINITO;
    const lineas = [{ texto: s.etiqueta(v), clase: dist === INFINITO ? "etq etq--inf" : "etq" }];
    for (const [x, t] of s.etiquetasDescartadas) if (x === v) lineas.push({ texto: t, clase: "etq etq--descartada" });
    // La etiqueta vigente queda siempre pegada al vértice y las descartadas más lejos.
    const arriba = r.y < this.pos[v][1];
    if (arriba) lineas.reverse();
    const alto = ALTO_LINEA * lineas.length;
    const yAbs0 = arriba ? r.y + r.h / 2 - 2 - alto + ALTO_LINEA / 2 : r.y - r.h / 2 + 2 + ALTO_LINEA / 2;
    // Si la etiqueta queda a un lado del vértice, el texto se pega al lado del vértice.
    const dx = r.x - this.pos[v][0];
    const lado = Math.abs(dx) > RADIO + 6 ? (dx < 0 ? "end" : "start") : "middle";
    const xt = lado === "end" ? r.w / 2 - 5 : lado === "start" ? -r.w / 2 + 5 : 0;
    return svg(
      "g", { clase: "etiqueta", "data-etiqueta": v, transform: `translate(${r.x.toFixed(1)} ${r.y.toFixed(1)})` },
      ...lineas.map((l, i) => this._textoEtiqueta(l.texto, l.clase, { "text-anchor": lado, x: xt, y: (yAbs0 - r.y + i * ALTO_LINEA).toFixed(1) })),
    );
  }

  /**
   * `[d, V]ₙ` se dibuja en dos partes: el valor `[d, V]` y la iteración `n` como subíndice
   * propio (más grande, en otro color y con su propio nombre accesible).
   */
  _textoEtiqueta(texto, clase, atributos) {
    const base = { clase, "dominant-baseline": "central", ...atributos };
    // En un empate la etiqueta trae varias partes `[d, V]ₙ [d, W]ₘ`: cada índice es un subíndice.
    const partes = [...texto.matchAll(/([^\u2080-\u2089]+)([\u2080-\u2089]+)?/gu)];
    if (!partes.some((m) => m[2])) return svg("text", { ...base, texto });
    const digitos = (u) => [...u].map((c) => c.codePointAt(0) - 0x2080).join("");
    const hijos = [];
    const nombre = [];
    let bajado = false;
    for (const m of partes) {
      // dy es relativo: tras un subíndice, el texto que sigue vuelve a la línea base.
      hijos.push(bajado ? svg("tspan", { dy: -3.5, texto: m[1] }) : m[1]);
      bajado = false;
      if (m[2]) {
        const n = digitos(m[2]);
        hijos.push(svg("tspan", { clase: "etq__iter", dx: 1, dy: 3.5, texto: n }));
        bajado = true;
        nombre.push(`${m[1].trim()}, iteración ${n}`);
      } else nombre.push(m[1].trim());
    }
    return svg("text", { ...base, "aria-label": nombre.join(" ") }, ...hijos);
  }

  _dibujarPreview() {
    this.capaPreview.replaceChildren();
    const p = this.preview;
    if (!p || !p.origen || !this.pos[p.origen]) return;
    const a = this.pos[p.origen];
    let b = null;
    if (p.destino && this.pos[p.destino]) b = this.pos[p.destino];
    else if (p.cursor) b = p.cursor;
    if (!b) return;
    const d = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (d < RADIO + 4) return;
    const ux = (b[0] - a[0]) / d;
    const uy = (b[1] - a[1]) / d;
    const x1 = a[0] + ux * (RADIO + 1);
    const y1 = a[1] + uy * (RADIO + 1);
    const fin = p.destino ? RADIO + 3 : 0;
    const x2 = b[0] - ux * fin;
    const y2 = b[1] - uy * fin;
    this.capaPreview.append(
      svg("line", { x1, y1, x2, y2, clase: "preview__linea" }),
      svg("polygon", {
        clase: "preview__punta",
        points: `${x2},${y2} ${x2 - ux * 12 - uy * 5.5},${y2 - uy * 12 + ux * 5.5} ${x2 - ux * 12 + uy * 5.5},${y2 - uy * 12 - ux * 5.5}`,
      }),
    );
  }

  /* ---------------------------------------------------------- interacción */

  _puntoVirtual(e) {
    const m = this.svg.getScreenCTM();
    if (!m) return [0, 0];
    const p = new DOMPoint(e.clientX, e.clientY).matrixTransform(m.inverse());
    return [p.x, p.y];
  }

  _alPresionar(e) {
    if (e.button !== 0) return;
    const nodo = e.target.closest?.("[data-v]");
    if (!nodo) {
      if (!e.target.closest?.("[data-peso]") && this.vista) this._iniciarDesplazamiento(e);
      return;
    }
    const v = nodo.dataset.v;
    const inicio = [e.clientX, e.clientY];
    const [px, py] = this._puntoVirtual(e);
    const [x0, y0] = this.pos[v];
    let arrastrando = false;
    const mover = (ev) => {
      if (!this.arrastrable || this._pinza) return;
      if (!arrastrando && Math.hypot(ev.clientX - inicio[0], ev.clientY - inicio[1]) < UMBRAL_ARRASTRE) return;
      arrastrando = true;
      this._arrastrando = true;
      const [qx, qy] = this._puntoVirtual(ev);
      this.pos[v] = this._dentroDeLaVista(limitar([x0 + qx - px, y0 + qy - py]));
      this._pedirRedibujo();
    };
    const soltar = (ev) => {
      window.removeEventListener("pointermove", mover);
      window.removeEventListener("pointerup", soltar);
      window.removeEventListener("pointercancel", soltar);
      if (this._gestoActual === soltar) this._gestoActual = null;
      // Con `touchstart` cancelado no llega el clic: el toque simple sobre un vértice se resuelve aquí.
      if (ev?.type === "pointerup" && ev.pointerType === "touch" && !arrastrando && this.arrastrable && this.alClicNodo) this.alClicNodo(v);
      this._arrastrando = false;
      this.contenedor.classList.remove("lienzo--arrastrando");
      if (arrastrando) {
        this._trasArrastre = true;
        this._suprimirClic = true;
        setTimeout(() => (this._suprimirClic = false), 0);
        this.redibujar();
      }
    };
    this._gestoActual = soltar;
    if (this.arrastrable) this.contenedor.classList.add("lienzo--arrastrando");
    window.addEventListener("pointermove", mover);
    window.addEventListener("pointerup", soltar);
    window.addEventListener("pointercancel", soltar);
    e.preventDefault();
  }

  _pedirRedibujo() {
    if (this._pendiente) return;
    this._pendiente = requestAnimationFrame(() => {
      this._pendiente = null;
      this.redibujar();
    });
  }

  _alHacerClic(e) {
    if (this._suprimirClic) return;
    const peso = e.target.closest?.("[data-peso]");
    if (peso && this.alClicPeso) {
      const [u, v] = peso.dataset.peso.split(">");
      this.alClicPeso(u, v);
      return;
    }
    const nodo = e.target.closest?.("[data-v]");
    if (nodo && this.alClicNodo) this.alClicNodo(nodo.dataset.v);
  }

  _alMoverRaton(e) {
    if (this.preview && this.preview.origen && !this.preview.destino) {
      this.preview.cursor = this._puntoVirtual(e);
      this._dibujarPreview();
    }
  }

  _cursorFuera() {
    if (this.preview && !this.preview.destino) {
      this.preview.cursor = null;
      this._dibujarPreview();
    }
  }

  /* ------------------------------------------------------- peso en línea */

  /** Campo de texto sobre el número de una arista. `alConfirmar(texto)` devuelve true si lo acepta. */
  abrirEditorPeso(u, v, valorActual, alConfirmar) {
    this.cerrarEditorPeso(false);
    const r = this.ultimo?.rotulos.pesos.get(claveArista(u, v));
    if (!r) return;
    const entrada = el("input", {
      clase: "peso-editor", type: "text", inputmode: "numeric", maxlength: 3, value: String(valorActual),
      "aria-label": `Nuevo peso de ${u} → ${v}`, "data-testid": "peso-editor",
    });
    const confirmar = () => {
      if (!this._editor) return;
      if (alConfirmar(entrada.value) !== false) this.cerrarEditorPeso();
      else {
        entrada.classList.add("peso-editor--error");
        entrada.focus();
        entrada.select();
      }
    };
    entrada.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        ev.stopPropagation();
        confirmar();
      } else if (ev.key === "Escape") {
        ev.preventDefault();
        ev.stopPropagation();
        this.cerrarEditorPeso();
      }
    });
    entrada.addEventListener("input", () => entrada.classList.remove("peso-editor--error"));
    this._editor = { u, v, entrada };
    this.contenedor.append(entrada);
    this._reubicarEditor(r);
    entrada.focus();
    entrada.select();
  }

  _reubicarEditor(r) {
    const e = this._editor;
    if (!e) return;
    const caja = this.svg.getBoundingClientRect();
    const padre = this.contenedor.getBoundingClientRect();
    const v = this.vista ?? { x: 0, y: 0, w: ANCHO, h: ALTO };
    const esc = Math.min(caja.width / v.w, caja.height / v.h);
    const offX = caja.left - padre.left + (caja.width - v.w * esc) / 2;
    const offY = caja.top - padre.top + (caja.height - v.h * esc) / 2;
    e.entrada.style.left = `${offX + (r.x - v.x) * esc}px`;
    e.entrada.style.top = `${offY + (r.y - v.y) * esc}px`;
  }

  cerrarEditorPeso(devolverFoco = true) {
    if (!this._editor) return;
    this._editor.entrada.remove();
    this._editor = null;
    if (devolverFoco) this.svg.focus?.();
  }

  get editandoPeso() {
    return this._editor ? [this._editor.u, this._editor.v] : null;
  }
}
