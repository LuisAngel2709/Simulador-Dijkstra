/**
 * Iconos SVG lineales (estilo Lucide, licencia ISC): cuadrícula de 24×24, trazo de 2, extremos y
 * uniones redondeados, sin relleno. Heredan `currentColor`, así que siguen al tema claro/oscuro.
 * Es el único sitio donde se definen: el resto de la interfaz llama a `icono("nombre")`.
 */

import { svg } from "./dom.js";

const FORMAS = {
  birrete: ['<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/>', '<path d="M22 10v6"/>', '<path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>'],
  grafo: ['<circle cx="18" cy="5" r="3"/>', '<circle cx="6" cy="12" r="3"/>', '<circle cx="18" cy="19" r="3"/>', '<line x1="8.59" x2="15.42" y1="13.51" y2="17.49"/>', '<line x1="15.41" x2="8.59" y1="6.51" y2="10.49"/>'],
  buscar: ['<circle cx="11" cy="11" r="8"/>', '<path d="m21 21-4.3-4.3"/>'],
  objetivo: ['<circle cx="12" cy="12" r="10"/>', '<circle cx="12" cy="12" r="6"/>', '<circle cx="12" cy="12" r="2"/>'],
  rayo: ['<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>'],
  lapiz: ['<path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/>', '<path d="m15 5 4 4"/>'],
  ayuda: ['<circle cx="12" cy="12" r="10"/>', '<path d="M9.09 9a3 3 0 0 1 5.82 1c0 2-3 3-3 3"/>', '<path d="M12 17h.01"/>'],
  reiniciar: ['<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>', '<path d="M3 3v5h5"/>'],
  deshacer: ['<path d="M9 14 4 9l5-5"/>', '<path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"/>'],
  luna: ['<path d="M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401"/>'],
  sol: ['<circle cx="12" cy="12" r="4"/>', '<path d="M12 2v2"/>', '<path d="M12 20v2"/>', '<path d="m4.93 4.93 1.41 1.41"/>', '<path d="m17.66 17.66 1.41 1.41"/>', '<path d="M2 12h2"/>', '<path d="M20 12h2"/>', '<path d="m6.34 17.66-1.41 1.41"/>', '<path d="m19.07 4.93-1.41 1.41"/>'],
  flechaIzquierda: ['<path d="M19 12H5"/>', '<path d="m12 19-7-7 7-7"/>'],
  flechaDerecha: ['<path d="M5 12h14"/>', '<path d="m12 5 7 7-7 7"/>'],
  reproducir: ['<polygon points="6 3 20 12 6 21 6 3"/>'],
  anterior: ['<path d="m15 18-6-6 6-6"/>'],
  siguiente: ['<path d="m9 18 6-6-6-6"/>'],
  alFinal: ['<polygon points="5 4 15 12 5 20 5 4"/>', '<line x1="19" x2="19" y1="5" y2="19"/>'],
  maximizar: ['<path d="M8 3H5a2 2 0 0 0-2 2v3"/>', '<path d="M21 8V5a2 2 0 0 0-2-2h-3"/>', '<path d="M3 16v3a2 2 0 0 0 2 2h3"/>', '<path d="M16 21h3a2 2 0 0 0 2-2v-3"/>'],
  tabla: ['<path d="M12 3v18"/>', '<rect width="18" height="18" x="3" y="3" rx="2"/>', '<path d="M3 9h18"/>', '<path d="M3 15h18"/>'],
  correcto: ['<path d="M20 6 9 17l-5-5"/>'],
  error: ['<path d="M18 6 6 18"/>', '<path d="m6 6 12 12"/>'],
};

export const NOMBRES_ICONOS = Object.keys(FORMAS);

/**
 * @param {string} nombre una de NOMBRES_ICONOS
 * @param {{tam?: number, etiqueta?: string|null}} [o] `etiqueta`: texto accesible; sin ella el icono es decorativo (aria-hidden).
 */
export function icono(nombre, { tam = 16, etiqueta = null } = {}) {
  const formas = FORMAS[nombre];
  if (!formas) throw new RangeError(`Icono desconocido: ${nombre}`);
  const nodo = svg("svg", {
    clase: `icono icono--${nombre}`, viewBox: "0 0 24 24", width: tam, height: tam, fill: "none", stroke: "currentColor",
    "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round", focusable: "false",
    ...(etiqueta ? { role: "img", "aria-label": etiqueta } : { "aria-hidden": "true" }),
  });
  nodo.innerHTML = formas.join(""); // contenido fijo y propio de este módulo, nunca datos del usuario
  return nodo;
}
