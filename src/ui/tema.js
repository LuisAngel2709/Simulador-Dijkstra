/** Tema claro/oscuro: un atributo `data-theme` en <html>; todos los colores son variables CSS. */

const CLAVE = "dijkstra.tema";

function leer() {
  try {
    const guardado = localStorage.getItem(CLAVE);
    if (guardado === "claro" || guardado === "oscuro") return guardado;
  } catch {
    /* almacenamiento no disponible: se usa el del sistema */
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "oscuro" : "claro";
}

export class Tema {
  constructor(alCambiar = () => {}) {
    this.alCambiar = alCambiar;
    this.actual = leer();
    this._aplicar();
  }

  _aplicar() {
    const raiz = document.documentElement;
    raiz.dataset.theme = this.actual === "oscuro" ? "dark" : "light";
    raiz.style.colorScheme = this.actual === "oscuro" ? "dark" : "light";
  }

  alternar() {
    this.actual = this.actual === "oscuro" ? "claro" : "oscuro";
    this._aplicar();
    try {
      localStorage.setItem(CLAVE, this.actual);
    } catch {
      /* sin persistencia */
    }
    this.alCambiar(this.actual);
    return this.actual;
  }
}
