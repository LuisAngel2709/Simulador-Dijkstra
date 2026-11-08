/** Diálogos modales de confirmación (colores distintos de las tarjetas del tutorial). */

import { el } from "./dom.js";

/**
 * @returns {{cerrar: Function, elemento: HTMLElement}}
 */
export function dialogoConfirmacion({
  titulo, mensaje, textoConfirmar, textoCancelar, alConfirmar, alCancelar = () => {}, peligro = false,
}) {
  const previo = document.activeElement;
  const cerrar = () => {
    document.removeEventListener("keydown", teclas, true);
    capa.remove();
    previo?.focus?.();
  };
  const cancelar = el("button", { clase: "boton boton--sec", type: "button", "data-testid": "dialogo-cancelar", texto: textoCancelar, onClick: () => { cerrar(); alCancelar(); } });
  const confirmar = el("button", { clase: `boton ${peligro ? "boton--peligro" : ""}`, type: "button", "data-testid": "dialogo-confirmar", texto: textoConfirmar, onClick: () => { cerrar(); alConfirmar(); } });
  const caja = el(
    "div", { clase: "dialogo", role: "alertdialog", "aria-modal": "true", "aria-labelledby": "dlg-titulo", "aria-describedby": "dlg-mensaje", "data-testid": "dialogo" },
    el("div", { clase: "dialogo__titulo", id: "dlg-titulo", texto: titulo }),
    el("div", { clase: "dialogo__mensaje", id: "dlg-mensaje", texto: mensaje }),
    el("div", { clase: "dialogo__botones" }, cancelar, confirmar),
  );
  const capa = el("div", { clase: "capa" }, caja);
  const teclas = (e) => {
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      cerrar();
      alCancelar();
    } else if (e.key === "Tab") {
      const focos = [cancelar, confirmar];
      const i = focos.indexOf(document.activeElement);
      e.preventDefault();
      focos[(i + (e.shiftKey ? -1 : 1) + focos.length) % focos.length].focus();
    }
  };
  document.addEventListener("keydown", teclas, true);
  document.body.append(capa);
  (peligro ? cancelar : confirmar).focus();
  return { cerrar, elemento: capa };
}
