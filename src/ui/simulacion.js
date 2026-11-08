/**
 * Pantalla de simulación paso a paso. Solo navega entre los snapshots que produce el motor:
 * nunca recalcula ni deshace nada («Anterior» muestra el snapshot previo).
 */

import {
  ACTUALIZACION, FINAL, INFINITO, INICIO, SELECCION, Simulacion, ejecutarDijkstra, explicar, formatoDistancia,
  Bloque, TEXTO, TITULO,
} from "../core/index.js";
import { dialogoConfirmacion } from "./dialogos.js";
import { el } from "./dom.js";
import { icono } from "./iconos.js";
import { pintarBloques } from "./explicacion.js";
import { GrafoSvg } from "./grafo-svg.js";
import { TablaProceso } from "./tabla.js";

const NOMBRE_SUBPASO = {
  [INICIO]: "Etiquetado inicial",
  [SELECCION]: "Subpaso 1 · Selección",
  [ACTUALIZACION]: "Subpaso 2 · Actualización",
  [FINAL]: "Fin de la simulación",
};

const LEYENDA = [
  ["var(--nodo-origen)", "Origen"], ["var(--nodo-destino)", "Destino"], ["var(--nodo-actual)", "Actual"],
  ["var(--nodo-visitado)", "Visitado"], ["var(--arista-evaluada)", "Arista evaluada"], ["var(--arista-empate)", "Empate"],
  ["var(--arista-camino)", "Camino"],
];

export class PantallaSimulacion {
  constructor({ grafo, origen, destino, alVolver, posiciones = null, textoVolver = "← Volver", alCambiarExtremos = () => {} }) {
    this.grafo = grafo;
    this.alVolver = alVolver;
    this.textoVolver = textoVolver;
    this.alCambiarExtremos = alCambiarExtremos;
    this.simulacion = null;
    this.resultado = null;
    this.tablaVisible = true;
    this.detalles = null;

    /* barra superior */
    this.boton_volver = el("button", { clase: "boton boton--sec", type: "button", "data-testid": "sim-volver", onClick: () => this._volver() }, icono("flechaIzquierda"), textoVolver.replace(/^←\s*/, ""));
    this.etiqueta_paso = el("span", { clase: "paso-indicador", "data-testid": "paso-actual", "aria-live": "polite" });
    this.barra_superior = el(
      "div", { clase: "barra" }, this.boton_volver, el("span", { clase: "barra__titulo", texto: "Simulación del algoritmo de Dijkstra" }),
      el("span", { estilo: { flex: "1" } }), this.etiqueta_paso,
    );

    /* grafo */
    this.encabezado_ruta = el("div", { clase: "encabezado-grafo__ruta", "data-testid": "ruta" });
    this.encabezado_estado = el("div", { clase: "encabezado-grafo__estado", "data-testid": "estado" });
    this.barraProgreso = el("div", { clase: "progreso__barra" });
    this.lienzo = el("div", { "data-testid": "sim-lienzo" });
    this.svg = new GrafoSvg(this.lienzo, { etiqueta: "Grafo de la simulación" });
    this.marco_leyenda = el(
      "div", { clase: "leyenda", "data-testid": "leyenda" },
      ...LEYENDA.map(([color, texto]) => el("span", { clase: "leyenda__item" }, el("span", { clase: "leyenda__cuadro", estilo: { background: color } }), texto)),
    );
    this.izquierda = el(
      "div", { clase: "sim-izq" },
      el("div", { clase: "encabezado-grafo" }, this.encabezado_ruta, this.encabezado_estado, el("div", { clase: "progreso" }, this.barraProgreso)),
      this.lienzo, this.marco_leyenda,
    );

    /* panel derecho */
    const opciones = () => grafo.vertices.map((v) => el("option", { value: v, texto: v }));
    this.menu_origen = el("select", { clase: "campo", "aria-label": "Vértice de origen", "data-testid": "origen" }, ...opciones());
    this.menu_destino = el("select", { clase: "campo", "aria-label": "Vértice de destino", "data-testid": "destino" }, ...opciones());
    this.menu_origen.value = origen;
    this.menu_destino.value = destino;
    for (const m of [this.menu_origen, this.menu_destino]) m.addEventListener("change", () => this._alElegirExtremo());
    this.marco_extremos = el(
      "div", { clase: "selectores" }, el("label", {}, "Origen:", this.menu_origen), el("label", {}, "Destino:", this.menu_destino),
    );
    this.boton_ejecutar = el("button", { clase: "boton boton--grande", type: "button", "data-testid": "ejecutar", onClick: () => this._ejecutar() }, "Ejecutar Dijkstra", icono("reproducir", { tam: 15 }));
    this.titulo_paso = el("div", { clase: "paso__titulo", "data-testid": "titulo-paso" });
    this.subtitulo_paso = el("span", { clase: "paso__sub", "data-testid": "subtitulo-paso" });
    this.boton_detalles = el("button", { clase: "boton boton--contorno boton--pequeno", type: "button", "data-testid": "mas-detalles", texto: "Más detalles", onClick: () => this._alternarDetalles() });
    this.fila_subpaso = el("div", { clase: "paso__fila" }, this.subtitulo_paso, this.boton_detalles);
    this.texto_explicacion = el("div", { clase: "caja-texto caja-texto--explicacion", "data-testid": "explicacion", tabindex: 0, "aria-label": "Explicación del paso" });
    this.etiqueta_resultado = el("h2", { clase: "titulo-seccion", texto: "Resultado" });
    this.texto_resultado = el("div", { clase: "caja-texto caja-texto--resultado", "data-testid": "resultado", role: "status", tabindex: 0 });
    this.panelSim = el(
      "aside", { clase: "panel panel-sim" }, this.marco_extremos, this.boton_ejecutar, this.titulo_paso, this.fila_subpaso,
      this.texto_explicacion, this.etiqueta_resultado, this.texto_resultado,
    );
    this.cuerpo = el("div", { clase: "sim-cuerpo" }, this.izquierda, this.panelSim);

    /* navegación */
    const b = (hijos, id, fn, sec = false, nombre = null) => el("button", { clase: `boton ${sec ? "boton--sec" : ""}`, type: "button", "data-testid": id, ...(nombre ? { "aria-label": nombre } : {}), onClick: fn }, ...hijos);
    this.boton_anterior = b([icono("anterior"), "Anterior"], "anterior", () => this._anterior());
    this.boton_siguiente = b(["Siguiente", icono("siguiente")], "siguiente", () => this._siguiente());
    this.boton_reiniciar = b([icono("reiniciar"), el("span", { clase: "boton-texto-movil", texto: "Reiniciar" })], "reiniciar", () => this._reiniciar(), true, "Reiniciar");
    this.boton_final = b([icono("alFinal"), el("span", { clase: "boton-texto-movil", texto: "Ir al final" })], "ir-al-final", () => this._finalizar(), true, "Ir al final");
    this.boton_tabla = b([], "alternar-tabla", () => this._alternarTabla(), true);
    this._textoTabla();
    this.barra_navegacion = el(
      "div", { clase: "barra barra-nav" }, this.boton_anterior, this.boton_siguiente, this.boton_reiniciar, this.boton_final,
      el("span", { clase: "barra-nav__espacio", estilo: { flex: "1" } }), this.boton_tabla,
    );

    /* tabla */
    this.contenedorTabla = el("div", { clase: "tabla-scroll" });
    this.tabla = el("section", { clase: "panel tabla-seccion", "aria-label": "Tabla del proceso" }, el("h2", { clase: "titulo-seccion", texto: "Tabla del proceso" }), this.contenedorTabla);
    this.tablaProceso = new TablaProceso(this.contenedorTabla);

    this.elemento = el("section", { clase: "pantalla", "data-pantalla": "simulacion" }, this.barra_superior, this.cuerpo, this.barra_navegacion, this.tabla);
    // La barra de navegación queda fija abajo; el orden visual es: grafo + panel, navegación, tabla.

    this.svg.establecerGrafo(grafo, { posiciones, modo: "capas" });
    this._teclas = (e) => this._alTecla(e);
    document.addEventListener("keydown", this._teclas);
    this._alCambiarExtremos();
  }

  destruir() {
    document.removeEventListener("keydown", this._teclas);
    this._cerrarDetalles();
  }

  posiciones() {
    return this.svg.obtenerPosiciones();
  }

  get origen() { return this.menu_origen.value; }
  get destino() { return this.menu_destino.value; }

  /* ----------------------------------------------------------------- acciones */

  _alTecla(e) {
    if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.altKey) return;
    if (document.querySelector(".capa, .tutorial")) return;
    const t = e.target;
    if (t instanceof HTMLElement && (t.closest("select, input, textarea") || t.isContentEditable)) return;
    if (e.key === "Escape" && this.detalles) {
      this._cerrarDetalles();
      return;
    }
    if (!this.simulacion) return;
    if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      if (this.simulacion.puedeRetroceder) { e.preventDefault(); this._anterior(); }
    } else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
      if (this.simulacion.puedeAvanzar) { e.preventDefault(); this._siguiente(); }
    }
  }

  _volver() {
    const total = this.grafo.cantidadAristas();
    if (this.textoVolver === "← Configuración" && total > 0) {
      dialogoConfirmacion({
        titulo: "¿Descartar grafo?",
        mensaje: `El grafo actual tiene ${total === 1 ? "1 arista" : `${total} aristas`}.\n\nSi vuelves a la configuración perderás el grafo y la simulación actual.`,
        textoConfirmar: "Descartar y volver", textoCancelar: "Permanecer en la simulación", peligro: true,
        alConfirmar: () => this.alVolver(this.posiciones()),
      });
    } else this.alVolver(this.posiciones());
  }

  _alElegirExtremo() {
    this.alCambiarExtremos(this.origen, this.destino);
    this._alCambiarExtremos();
  }

  /** Cambiar origen o destino invalida la simulación anterior. */
  _alCambiarExtremos() {
    this.simulacion = null;
    this.resultado = null;
    this.tablaProceso.limpiar();
    this.svg.establecerReserva(null);
    this.svg.actualizarEstado({ snapshot: null, origen: this.origen, destino: this.destino, mostrarEtiquetas: false });
    pintarBloques(this.texto_explicacion, [
      Bloque(TITULO, "Cómo empezar"),
      Bloque(
        TEXTO,
        "Elige el origen y el destino y pulsa «Ejecutar Dijkstra». Cada iteración se muestra en dos subpasos: " +
          "primero se SELECCIONA el vértice no visitado con menor distancia y después se ACTUALIZAN las etiquetas de sus vecinos.",
      ),
    ]);
    this.texto_resultado.textContent = "Elige origen y destino y pulsa «Ejecutar Dijkstra».";
    this.titulo_paso.textContent = "Simulación no iniciada";
    this.subtitulo_paso.textContent = "";
    this.etiqueta_paso.textContent = "";
    this.panelSim.classList.remove("final");
    this._encabezado();
    this._actualizarDetalles();
    this._botones();
  }

  _ejecutar() {
    this.resultado = ejecutarDijkstra(this.grafo, this.origen, this.destino);
    this.simulacion = new Simulacion(this.resultado);
    // Origen = destino: no hay selecciones, solo la columna de la iteración 0.
    this.tablaProceso.construir(this.grafo.vertices, this.resultado.origen === this.resultado.destino ? 0 : this.grafo.n);
    this.svg.establecerReserva(this.resultado);
    this._refrescar();
  }

  _siguiente() { if (this.simulacion) { this.simulacion.siguiente(); this._refrescar(); } }
  _anterior() { if (this.simulacion) { this.simulacion.anterior(); this._refrescar(); } }
  _reiniciar() { if (this.simulacion) { this.simulacion.reiniciar(); this._refrescar(); } }
  _finalizar() { if (this.simulacion) { this.simulacion.finalizar(); this._refrescar(); } }

  _alternarTabla() {
    this.tablaVisible = !this.tablaVisible;
    this.tabla.classList.toggle("oculto", !this.tablaVisible);
    this._textoTabla();
  }

  /** En escritorio es el texto completo; en celulares queda solo el icono (con el mismo nombre accesible). */
  _textoTabla() {
    const texto = this.tablaVisible ? "Ocultar tabla del proceso" : "Mostrar tabla del proceso";
    this.boton_tabla.setAttribute("aria-label", texto);
    this.boton_tabla.replaceChildren(icono("tabla", { tam: 16 }), el("span", { clase: "boton-texto-movil", texto }));
  }

  /* ------------------------------------------------------------ presentación */

  _refrescar() {
    if (!this.simulacion) return;
    const s = this.simulacion.actual;
    this.svg.actualizarEstado({ snapshot: s, origen: this.resultado.origen, destino: this.resultado.destino, mostrarEtiquetas: true });
    this.tablaProceso.mostrar(s);
    this.titulo_paso.textContent = s.titulo;
    this.subtitulo_paso.textContent = NOMBRE_SUBPASO[s.subpaso] ?? "";
    const explicacion = explicar(this.grafo, this.resultado, this.simulacion.indice);
    pintarBloques(this.texto_explicacion, explicacion.breve);
    this.etiqueta_paso.replaceChildren("Paso ", el("b", { clase: "paso-indicador__n", texto: String(this.simulacion.indice + 1) }), ` de ${this.simulacion.total}`);
    this.texto_resultado.textContent = this._textoResultado(s);
    this.panelSim.classList.toggle("final", s.esFinal);
    this._encabezado();
    this._actualizarDetalles(explicacion);
    this._botones();
  }

  _encabezado() {
    const { origen, destino } = this;
    this.encabezado_ruta.textContent = `Camino mínimo:  ${origen} → ${destino}`;
    const estado = this.encabezado_estado;
    const barra = this.barraProgreso;
    estado.className = "encabezado-grafo__estado";
    barra.className = "progreso__barra";
    if (!this.simulacion) {
      estado.textContent = "Pulsa Ejecutar Dijkstra para comenzar";
      barra.style.width = "0%";
      return;
    }
    const s = this.simulacion.actual;
    const r = this.resultado;
    barra.style.width = `${(this.simulacion.indice / Math.max(this.simulacion.total - 1, 1)) * 100}%`;
    if (!s.esFinal) {
      const d = s.distancias[destino];
      if (s.visitados.has(destino) || destino === origen) estado.textContent = `Distancia a ${destino}: ${formatoDistancia(d)} · definitiva`;
      else if (d !== INFINITO) estado.textContent = `Distancia a ${destino}: ${formatoDistancia(d)} · provisional`;
      else estado.textContent = `Distancia a ${destino}: ∞ · aún sin alcanzar`;
    } else if (r.alcanzable) {
      const n = r.cantidadCaminos;
      estado.replaceChildren(icono("correcto", { tam: 14 }), ` Completada · distancia mínima ${formatoDistancia(r.distancia)} · ${n} camino${n !== 1 ? "s" : ""} mínimo${n !== 1 ? "s" : ""}`);
      estado.classList.add("encabezado-grafo__estado--ok");
      barra.classList.add("progreso__barra--ok");
    } else {
      estado.replaceChildren(icono("error", { tam: 14 }), ` Completada · no existe camino de ${origen} a ${destino}`);
      estado.classList.add("encabezado-grafo__estado--error");
      barra.classList.add("progreso__barra--error");
    }
  }

  _textoResultado(s) {
    if (!s.esFinal) return "La simulación está en curso.\nAvanza con «Siguiente» o pulsa «Ir al final» para ver el resultado.";
    const r = this.resultado;
    if (!r.alcanzable) return `No existe un camino desde ${r.origen} hasta ${r.destino}.\nDistancia: ∞`;
    const lineas = [`Distancia mínima: ${formatoDistancia(r.distancia)}`, `Caminos mínimos encontrados: ${r.cantidadCaminos}`, ""];
    if (r.origen === r.destino) {
      lineas.push(r.origen, "", `${r.origen} es a la vez origen y destino: la distancia es 0 y no se recorre ninguna arista.`);
    } else lineas.push(...r.caminos.map((c) => c.join(" → ")));
    if (r.truncado) lineas.push("(lista truncada por la elevada cantidad de caminos)");
    return lineas.join("\n");
  }

  _botones() {
    const activa = this.simulacion !== null;
    this.boton_anterior.disabled = !(activa && this.simulacion.puedeRetroceder);
    this.boton_siguiente.disabled = !(activa && this.simulacion.puedeAvanzar);
    this.boton_reiniciar.disabled = !activa;
    this.boton_final.disabled = !activa;
    this.boton_detalles.disabled = !activa;
  }

  /* ------------------------------------------------------------ más detalles */

  _alternarDetalles() {
    if (this.detalles) return this._cerrarDetalles();
    if (!this.simulacion) return undefined;
    const titulo = el("div", { clase: "detalles__titulo", "data-testid": "detalles-titulo" });
    const sub = el("div", { clase: "detalles__sub" });
    const paso = el("div", { clase: "detalles__paso" });
    const cuerpo = el("div", { clase: "detalles__cuerpo", "data-testid": "detalles-cuerpo", tabindex: 0 });
    const cerrar = el("button", { clase: "boton boton--sec", type: "button", "data-testid": "detalles-cerrar", texto: "Cerrar", onClick: () => this._cerrarDetalles() });
    const caja = el(
      "div", { clase: "detalles", role: "dialog", "aria-label": "Más detalles del paso", "data-testid": "detalles" },
      el("div", { clase: "detalles__cab" }, titulo, paso, sub), cuerpo, el("div", { clase: "detalles__pie" }, cerrar),
    );
    document.body.append(caja);
    this.detalles = { caja, titulo, sub, paso, cuerpo };
    this._actualizarDetalles();
    return undefined;
  }

  _cerrarDetalles() {
    if (!this.detalles) return;
    this.detalles.caja.remove();
    this.detalles = null;
  }

  _actualizarDetalles(explicacion = null) {
    const d = this.detalles;
    if (!d) return;
    if (!this.simulacion) {
      d.titulo.textContent = "Simulación no iniciada";
      d.sub.textContent = "";
      d.paso.textContent = "";
      pintarBloques(d.cuerpo, [Bloque(TEXTO, "Cambió el origen o el destino. Pulsa «Ejecutar Dijkstra» para generar de nuevo la simulación; esta ventana mostrará el detalle de cada paso.")]);
      return;
    }
    const e = explicacion ?? explicar(this.grafo, this.resultado, this.simulacion.indice);
    d.titulo.textContent = e.titulo;
    d.sub.textContent = e.subtitulo;
    d.paso.textContent = `Paso ${this.simulacion.indice + 1} de ${this.simulacion.total}`;
    pintarBloques(d.cuerpo, e.detalle);
  }
}
