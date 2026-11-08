/** Utilidades mínimas para crear elementos DOM y SVG sin dependencias. */

const NS_SVG = "http://www.w3.org/2000/svg";

function aplicar(nodo, atributos) {
  for (const [k, v] of Object.entries(atributos ?? {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "clase") nodo.setAttribute("class", v);
    else if (k === "texto") nodo.textContent = v;
    else if (k === "estilo" && typeof v === "object") Object.assign(nodo.style, v);
    else if (k.startsWith("on") && typeof v === "function") nodo.addEventListener(k.slice(2).toLowerCase(), v);
    else nodo.setAttribute(k, v === true ? "" : String(v));
  }
}

function agregar(nodo, hijos) {
  for (const h of hijos.flat()) {
    if (h === null || h === undefined || h === false) continue;
    nodo.append(h instanceof Node ? h : document.createTextNode(String(h)));
  }
  return nodo;
}

/** el("div", {clase: "x", onClick: fn}, hijo1, "texto") */
export function el(etiqueta, atributos = {}, ...hijos) {
  const nodo = document.createElement(etiqueta);
  aplicar(nodo, atributos);
  return agregar(nodo, hijos);
}

export function svg(etiqueta, atributos = {}, ...hijos) {
  const nodo = document.createElementNS(NS_SVG, etiqueta);
  aplicar(nodo, atributos);
  return agregar(nodo, hijos);
}

export function vaciar(nodo) {
  nodo.replaceChildren();
  return nodo;
}

export const $ = (selector, raiz = document) => raiz.querySelector(selector);
export const $$ = (selector, raiz = document) => [...raiz.querySelectorAll(selector)];
