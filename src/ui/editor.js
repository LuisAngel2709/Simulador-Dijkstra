/**
 * Pantalla del editor manual. Toda la validación vive en el motor (`Grafo`, `validarPeso`):
 * aquí solo se recogen las acciones y se muestran los mensajes de error.
 */

import { GrafoError, analizar, mensajeAdvertencia, sugerirExtremos, validarPeso } from "../core/index.js";
import { dialogoConfirmacion } from "./dialogos.js";
import { el } from "./dom.js";
import { icono } from "./iconos.js";
import { GrafoSvg } from "./grafo-svg.js";

export class PantallaEditor {
  constructor({ grafo, alFinalizar, alVolver, posiciones = null, extremos = sugerirExtremos }) {
    this.grafo = grafo;
    this.alFinalizar = alFinalizar;
    this.alVolver = alVolver;
    this.extremos = extremos;
    this.origenArista = null;
    this.destinoArista = null;
    this._mostradas = null;

    this.boton_volver = el("button", { clase: "boton boton--sec", type: "button", "data-testid": "editor-volver", onClick: () => this._volver() }, icono("flechaIzquierda"), "Volver");
    this.boton_restablecer = el("button", { clase: "boton boton--sec boton--pequeno", type: "button", "data-testid": "editor-restablecer", onClick: () => this._reorganizar() }, icono("deshacer", { tam: 14 }), "Restablecer");
    this.barra = el(
      "div", { clase: "barra" }, this.boton_volver, el("span", { clase: "barra__titulo", texto: "Editor manual del grafo" }),
      el("span", { clase: "barra__ayuda", texto: "Arrastra los vértices para ubicarlos · Clic en origen y luego en destino para conectar" }),
      el("span", { clase: "barra__espacio", estilo: { flex: "1" } }), this.boton_restablecer,
    );

    this.canvas = el("div", { "data-testid": "editor-lienzo" });
    this.svg = new GrafoSvg(this.canvas, {
      alClicNodo: (v) => this._alClicNodo(v), alClicPeso: (u, v) => this._editarPesoEnLinea(u, v), etiqueta: "Editor del grafo",
    });
    this.svg.establecerGrafo(grafo, { posiciones, modo: "circular" });

    this.etiqueta_seleccion = el("div", { clase: "seleccion-aristas", "data-testid": "seleccion" });
    this.entradaPeso = el("input", { clase: "campo campo--peso", type: "text", inputmode: "numeric", maxlength: 3, "aria-label": "Peso (1-99)", "data-testid": "peso-nuevo", placeholder: "1-99" });
    this.entradaPeso.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); this._crearArista(); }
    });
    this.fila_peso = el("div", { clase: "fila" }, el("label", { for: "x", texto: "Peso (1-99):" }), this.entradaPeso);
    this.fila_botones = el(
      "div", { clase: "fila" },
      el("button", { clase: "boton", type: "button", "data-testid": "crear-conexion", texto: "Crear conexión", onClick: () => this._crearArista() }),
      el("button", { clase: "boton boton--sec", type: "button", "data-testid": "cancelar-seleccion", texto: "Cancelar", onClick: () => this._cancelar() }),
    );
    this.mensaje = el("div", { clase: "mensaje", role: "status", "aria-live": "polite", "data-testid": "editor-mensaje" });
    this.lista_aristas = el("div", { clase: "lista-aristas", "data-testid": "lista-aristas" });
    this.boton_finalizar_grafo = el("button", { clase: "boton boton--grande", type: "button", "data-testid": "finalizar-grafo", onClick: () => this._finalizar() }, "Finalizar grafo", icono("flechaDerecha"));

    this.panel = el(
      "aside", { clase: "panel" },
      el("h2", { clase: "titulo-seccion", texto: "Nueva arista" }), this.etiqueta_seleccion, this.fila_peso, this.fila_botones, this.mensaje,
      el("h2", { clase: "titulo-seccion", texto: "Aristas del grafo" }), this.lista_aristas, this.boton_finalizar_grafo,
    );
    this.elemento = el("section", { clase: "pantalla", "data-pantalla": "editor" }, this.barra, el("div", { clase: "editor-cuerpo" }, this.canvas, this.panel));

    this._escape = (e) => {
      if (e.key === "Escape" && (this.origenArista || this.destinoArista) && !document.querySelector(".capa, .tutorial")) this._cancelar();
    };
    document.addEventListener("keydown", this._escape);
    this._refrescar();
    if (grafo.cantidadAristas() > 0) this._informar("Grafo conservado: puedes seguir editándolo.");
  }

  destruir() {
    document.removeEventListener("keydown", this._escape);
  }

  posiciones() {
    return this.svg.obtenerPosiciones();
  }

  /* ----------------------------------------------------------------- acciones */

  _volver() {
    const total = this.grafo.cantidadAristas();
    if (total > 0) {
      dialogoConfirmacion({
        titulo: "¿Descartar grafo?",
        mensaje: `El grafo actual tiene ${total === 1 ? "1 arista" : `${total} aristas`}.\n\nSi vuelves a la configuración perderás todas las conexiones creadas.`,
        textoConfirmar: "Descartar y volver", textoCancelar: "Continuar editando", peligro: true, alConfirmar: () => this.alVolver(),
      });
    } else this.alVolver();
  }

  _alClicNodo(v) {
    if (this.svg.editandoPeso) this.svg.cerrarEditorPeso(false);
    if (this.origenArista === null) this.origenArista = v;
    else if (this.destinoArista === null) {
      if (v === this.origenArista) return this._informar("Un vértice no puede conectarse consigo mismo.", true);
      this.destinoArista = v;
      this._refrescar();
      this.entradaPeso.focus();
      return undefined;
    } else {
      this.origenArista = v;
      this.destinoArista = null;
    }
    this._refrescar();
    return undefined;
  }

  _cancelar() {
    this.origenArista = null;
    this.destinoArista = null;
    this.entradaPeso.value = "";
    this._informar("Selección cancelada.");
    this._refrescar();
  }

  _crearArista() {
    if (this.origenArista === null || this.destinoArista === null) {
      return this._informar("Selecciona primero el vértice de origen y el de destino.", true);
    }
    let peso;
    try {
      peso = validarPeso(this.entradaPeso.value);
      this.grafo.agregarArista(this.origenArista, this.destinoArista, peso);
    } catch (e) {
      if (e instanceof GrafoError) return this._informar(e.message, true);
      throw e;
    }
    this._informar(`Conexión creada: ${this.origenArista} → ${this.destinoArista} (peso ${peso}).`);
    this.origenArista = null;
    this.destinoArista = null;
    this.entradaPeso.value = "";
    this.svg.establecerGrafo(this.grafo);
    this._refrescar();
    return undefined;
  }

  _eliminar(u, v) {
    try {
      this.grafo.eliminarArista(u, v);
    } catch (e) {
      if (e instanceof GrafoError) return this._informar(e.message, true);
      throw e;
    }
    this._informar(`Arista ${u} → ${v} eliminada.`);
    this.svg.establecerGrafo(this.grafo);
    this._refrescar();
    return undefined;
  }

  _editarPesoEnLinea(u, v) {
    this.svg.abrirEditorPeso(u, v, this.grafo.peso(u, v), (texto) => this._aplicarPeso(u, v, texto));
  }

  _aplicarPeso(u, v, texto) {
    try {
      this.grafo.modificarPeso(u, v, texto);
    } catch (e) {
      if (e instanceof GrafoError) {
        this._informar(e.message, true);
        return false;
      }
      throw e;
    }
    this._informar(`Peso de ${u} → ${v} actualizado a ${this.grafo.peso(u, v)}.`);
    this.svg.redibujar();
    this._refrescar();
    return true;
  }

  _reorganizar() {
    this.svg.reorganizarEnCirculo();
    this._informar("Posiciones de los vértices restablecidas.");
  }

  _finalizar() {
    if (this.grafo.cantidadAristas() === 0) {
      return this._informar("El grafo no tiene conexiones. Crea al menos una arista antes de continuar.", true);
    }
    this.svg.cerrarEditorPeso(false);
    const [origen, destino] = this.extremos(this.grafo);
    const analisis = analizar(this.grafo, origen, destino);
    if (!analisis.hayAdvertencias) return this._continuar();
    dialogoConfirmacion({
      titulo: "Revisa tu grafo antes de simular", mensaje: mensajeAdvertencia(analisis),
      textoConfirmar: "Continuar de todos modos", textoCancelar: "Volver al editor", alConfirmar: () => this._continuar(),
    });
    return undefined;
  }

  _continuar() {
    this.alFinalizar(this.grafo, this.svg.obtenerPosiciones());
  }

  /* ------------------------------------------------------------ presentación */

  _informar(texto, error = false) {
    this.mensaje.textContent = texto;
    this.mensaje.className = `mensaje ${error ? "mensaje--error" : "mensaje--ok"}`;
  }

  _refrescar() {
    this.etiqueta_seleccion.replaceChildren(
      el("span", { texto: `Origen: ${this.origenArista ?? "—"}`, "data-testid": "sel-origen" }),
      el("span", { texto: `Destino: ${this.destinoArista ?? "—"}`, "data-testid": "sel-destino" }),
    );
    const sel = [this.origenArista, this.destinoArista].filter(Boolean);
    this.svg.actualizarEstado({ seleccionEditor: sel });
    this.svg.establecerPreview(this.origenArista ? { origen: this.origenArista, destino: this.destinoArista, cursor: null } : null);
    const aristas = this.grafo.aristas();
    const firma = JSON.stringify(aristas);
    if (firma === this._mostradas) return;
    this._mostradas = firma;
    if (!aristas.length) {
      this.lista_aristas.replaceChildren(el("div", { clase: "lista-aristas__vacia", texto: "Todavía no hay aristas." }));
      return;
    }
    this.lista_aristas.replaceChildren(
      ...aristas.map(([u, v, peso]) =>
        el(
          "div", { clase: "arista-fila", "data-fila": `${u}>${v}` },
          el("strong", { texto: `${u} → ${v}` }), el("span", { clase: "arista-fila__peso", texto: `peso ${peso}` }),
          el("button", { clase: "boton boton--sec boton--pequeno", type: "button", texto: "Peso", "data-accion": "peso", onClick: () => this._editarPesoEnLinea(u, v) }),
          el("button", { clase: "boton boton--peligro boton--pequeno", type: "button", texto: "Eliminar", "data-accion": "eliminar", onClick: () => this._eliminar(u, v) }),
        )),
    );
  }
}
