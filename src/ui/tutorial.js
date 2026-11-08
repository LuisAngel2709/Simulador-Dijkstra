/**
 * Motor del tutorial guiado. Superpone un recuadro de foco y una tarjeta sobre elementos reales
 * de la pantalla. Un bloqueador transparente impide pulsar la interfaz mientras dura el recorrido,
 * así que el tutorial nunca modifica el grafo ni la simulación.
 */

import { el } from "./dom.js";
import { icono } from "./iconos.js";

export class Tutorial {
  /** @param {{titulo:string, texto:string, seccion:string, objetivo?:Function, preparar?:Function, ejemplo?:Function}[]} pasos */
  constructor(pasos, { alCerrar = () => {} } = {}) {
    this.pasos = pasos;
    this.i = 0;
    this.alCerrar = alCerrar;
    this.previo = document.activeElement;

    this.seccion = el("div", { clase: "tutorial__seccion", "data-testid": "tut-seccion" });
    this.titulo = el("div", { clase: "tutorial__titulo", id: "tut-titulo", "data-testid": "tut-titulo" });
    this.texto = el("div", { clase: "tutorial__texto", "data-testid": "tut-texto" });
    this.ejemplo = el("div", { clase: "tutorial__ejemplo", "data-testid": "tut-ejemplo" });
    this.contador = el("span", { clase: "tutorial__contador", "data-testid": "tut-contador" });
    this.bAnterior = el("button", { clase: "boton boton--sec boton--pequeno", type: "button", "data-testid": "tut-anterior", onClick: () => this.ir(this.i - 1) }, icono("flechaIzquierda", { tam: 14 }), "Anterior");
    this.bSiguiente = el("button", { clase: "boton boton--pequeno", type: "button", "data-testid": "tut-siguiente", onClick: () => (this.i === this.pasos.length - 1 ? this.cerrar() : this.ir(this.i + 1)) });
    this.bSalir = el("button", { clase: "boton boton--sec boton--pequeno", type: "button", "data-testid": "tut-salir", texto: "Salir", onClick: () => this.cerrar() });
    this.tarjeta = el(
      "div", { clase: "tutorial__tarjeta", role: "dialog", "aria-modal": "true", "aria-labelledby": "tut-titulo", "data-testid": "tutorial-tarjeta" },
      this.seccion, this.titulo, this.texto, this.ejemplo, el("div", { clase: "tutorial__pie" }, this.contador, this.bSalir, this.bAnterior, this.bSiguiente),
    );
    this.foco = el("div", { clase: "tutorial__foco", "data-testid": "tutorial-foco" });
    this.raiz = el("div", { clase: "tutorial", "data-testid": "tutorial-overlay" }, el("div", { clase: "tutorial__bloqueo" }), this.foco, this.tarjeta);
    document.body.append(this.raiz);

    this._teclas = (e) => {
      if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); this.cerrar(); }
      else if (e.key === "ArrowRight" || e.key === "Enter") {
        if (e.key === "Enter" && e.target instanceof HTMLButtonElement) return;
        e.preventDefault(); e.stopPropagation();
        this.i === this.pasos.length - 1 ? this.cerrar() : this.ir(this.i + 1);
      } else if (e.key === "ArrowLeft") { e.preventDefault(); e.stopPropagation(); this.ir(this.i - 1); }
    };
    this._reubicar = () => this._colocar();
    document.addEventListener("keydown", this._teclas, true);
    window.addEventListener("resize", this._reubicar);
    window.addEventListener("scroll", this._reubicar, true);
    this.ir(0);
  }

  ir(i) {
    if (i < 0 || i >= this.pasos.length) return;
    this.i = i;
    const p = this.pasos[i];
    p.preparar?.();
    this.seccion.textContent = p.seccion;
    this.titulo.textContent = p.titulo;
    this.texto.textContent = p.texto;
    const ej = p.ejemplo?.();
    this.ejemplo.textContent = ej ?? "";
    this.ejemplo.classList.toggle("oculto", !ej);
    this.contador.textContent = `${i + 1} de ${this.pasos.length}`;
    this.bAnterior.disabled = i === 0;
    this.bSiguiente.replaceChildren(...(i === this.pasos.length - 1 ? ["Finalizar"] : ["Siguiente", icono("flechaDerecha", { tam: 14 })]));
    this.objetivos = [].concat(p.objetivo?.() ?? []).filter(Boolean);
    this.objetivos[0]?.scrollIntoView?.({ block: "center", inline: "nearest" });
    requestAnimationFrame(() => { this._colocar(); this.bSiguiente.focus({ preventScroll: true }); });
    this._colocar();
  }

  _rect() {
    const rs = (this.objetivos ?? []).map((e) => e.getBoundingClientRect()).filter((r) => r.width > 0 && r.height > 0);
    if (!rs.length) return null;
    const l = Math.min(...rs.map((r) => r.left)); const t = Math.min(...rs.map((r) => r.top));
    const r = Math.max(...rs.map((x) => x.right)); const b = Math.max(...rs.map((x) => x.bottom));
    return { left: l, top: t, right: r, bottom: b, width: r - l, height: b - t };
  }

  _colocar() {
    const vw = window.innerWidth; const vh = window.innerHeight;
    const rc = this._rect();
    const tw = this.tarjeta.offsetWidth; const th = this.tarjeta.offsetHeight;
    let x; let y;
    if (!rc) {
      this.foco.style.cssText = "left:50%;top:50%;width:0;height:0;border-width:0";
      x = (vw - tw) / 2; y = (vh - th) / 2;
    } else {
      const pad = 6;
      const f = { l: Math.max(0, rc.left - pad), t: Math.max(0, rc.top - pad), r: Math.min(vw, rc.right + pad), b: Math.min(vh, rc.bottom + pad) };
      Object.assign(this.foco.style, { left: `${f.l}px`, top: `${f.t}px`, width: `${f.r - f.l}px`, height: `${f.b - f.t}px`, borderWidth: "3px" });
      const libre = { abajo: vh - f.b, arriba: f.t, derecha: vw - f.r, izquierda: f.l };
      const lado = libre.abajo >= th + 16 ? "abajo" : libre.arriba >= th + 16 ? "arriba" : libre.derecha >= tw + 16 ? "derecha" : libre.izquierda >= tw + 16 ? "izquierda" : null;
      if (lado === "abajo") { y = f.b + 12; x = f.l; }
      else if (lado === "arriba") { y = f.t - th - 12; x = f.l; }
      else if (lado === "derecha") { x = f.r + 12; y = f.t; }
      else if (lado === "izquierda") { x = f.l - tw - 12; y = f.t; }
      else { x = (vw - tw) / 2; y = vh - th - 16; } // el objetivo ocupa casi todo: tarjeta abajo, sobre él
    }
    this.tarjeta.style.left = `${Math.max(12, Math.min(vw - tw - 12, x))}px`;
    this.tarjeta.style.top = `${Math.max(12, Math.min(vh - th - 12, y))}px`;
  }

  cerrar() {
    document.removeEventListener("keydown", this._teclas, true);
    window.removeEventListener("resize", this._reubicar);
    window.removeEventListener("scroll", this._reubicar, true);
    this.raiz.remove();
    this.previo?.focus?.({ preventScroll: true });
    this.alCerrar();
  }
}
