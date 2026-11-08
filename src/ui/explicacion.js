/** Pinta los bloques de `explicaciones.js` (título, texto, cálculo, tabla, nota, éxito, alerta). */

import { el } from "./dom.js";

export function pintarBloques(contenedor, bloques) {
  contenedor.replaceChildren(
    ...bloques.map((b) => el("div", { clase: `bloque bloque--${b.estilo}`, "data-estilo": b.estilo, texto: b.texto })),
  );
  contenedor.scrollTop = 0;
}
