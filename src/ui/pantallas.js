/** Pantallas de bienvenida y de configuración del grafo. */

import { NODOS_MAXIMO, NODOS_MINIMO, GrafoError, validarNumeroNodos } from "../core/index.js";
import { el } from "./dom.js";
import { icono } from "./iconos.js";

export class PantallaBienvenida {
  constructor({ alEmpezar }) {
    this.boton_empezar = el("button", { clase: "boton boton--grande", type: "button", "data-testid": "empezar", onClick: alEmpezar }, "EMPEZAR SIMULACIÓN", icono("flechaDerecha"));
    const mini = (ic, titulo, texto) => el("div", { clase: "minitarjeta" }, el("div", { clase: "minitarjeta__titulo" }, icono(ic, { tam: 18 }), titulo), el("div", { clase: "minitarjeta__texto", texto }));
    this.tarjeta = el(
      "div", { clase: "tarjeta bienvenida__tarjeta" },
      el("span", { clase: "etiqueta-chip" }, icono("birrete", { tam: 15 }), "SIMULADOR EDUCATIVO INTERACTIVO"),
      el("h1", { clase: "bienvenida__titulo", texto: "ENCUENTRA EL CAMINO MÍNIMO" }),
      el("p", { clase: "bienvenida__subtitulo", texto: "Descubre paso a paso cómo funciona el algoritmo de Dijkstra" }),
      el("p", { clase: "bienvenida__texto", texto: "Construye un grafo, elige un punto de partida y descubre cómo encontrar el camino más corto." }),
      el(
        "div", { clase: "minitarjetas" },
        mini("grafo", "Grafo Visual", "Estructura por capas y conexiones claras."),
        mini("buscar", "Paso a Paso", "Etiquetado y relajación en cada iteración."),
        mini("objetivo", "Rutas Óptimas", "Cálculo de distancias y detección de empates."),
      ),
      this.boton_empezar,
      el("p", { clase: "bienvenida__pie", texto: "Simulación interactiva del algoritmo de Dijkstra" }),
    );
    this.elemento = el("section", { clase: "pantalla bienvenida", "data-pantalla": "bienvenida" }, this.tarjeta);
  }

  destruir() {}
}

export class PantallaConfiguracion {
  constructor({ alGenerar, alCrearManual, alVolver, nodosIniciales = 8 }) {
    this.alGenerar = alGenerar;
    this.alCrearManual = alCrearManual;
    this.selectorNodos = el(
      "select", { clase: "campo", "aria-label": "Número de nodos", "data-testid": "num-nodos" },
      ...Array.from({ length: NODOS_MAXIMO - NODOS_MINIMO + 1 }, (_, i) => el("option", { value: NODOS_MINIMO + i, texto: String(NODOS_MINIMO + i) })),
    );
    this.selectorNodos.value = String(nodosIniciales);
    this.mensaje = el("div", { clase: "mensaje mensaje--error", role: "alert", "data-testid": "config-mensaje" });
    this.marco_nodos = el("div", { clase: "campo-fila" }, el("label", { texto: "¿Cuántos nodos quieres?", for: "nn" }), this.selectorNodos, el("span", { clase: "barra__ayuda", texto: `(entre ${NODOS_MINIMO} y ${NODOS_MAXIMO})` }));

    this.boton_auto = el("button", { clase: "boton boton--grande", type: "button", "data-testid": "generar", onClick: () => this._con(alGenerar) }, "Generar y Continuar", icono("flechaDerecha"));
    this.boton_manual = el("button", { clase: "boton boton--grande boton--contorno", type: "button", "data-testid": "manual", onClick: () => this._con(alCrearManual) }, "Abrir Editor Manual", icono("flechaDerecha"));
    this.tarjeta_auto = el(
      "div", { clase: "opcion" }, el("div", { clase: "opcion__titulo" }, icono("rayo", { tam: 20 }), "Generar automáticamente"),
      el("div", { clase: "opcion__texto", texto: "Deja que el sistema cree un grafo dirigido sin ciclos con pesos didácticos y camino óptimo garantizado." }), this.boton_auto,
    );
    this.tarjeta_manual = el(
      "div", { clase: "opcion" }, el("div", { clase: "opcion__titulo" }, icono("lapiz", { tam: 20 }), "Crear manualmente"),
      el("div", { clase: "opcion__texto", texto: "Define las conexiones y los pesos tú mismo en un editor visual interactivo nodo por nodo." }), this.boton_manual,
    );
    this.boton_volver = el("button", { clase: "boton boton--sec", type: "button", "data-testid": "config-volver", onClick: alVolver }, icono("flechaIzquierda"), "Volver al inicio");
    this.tarjeta = el(
      "div", { clase: "tarjeta config__tarjeta" },
      el("span", { clase: "etiqueta-chip", texto: "PASO 1 · CONFIGURACIÓN DEL GRAFO", estilo: { alignSelf: "flex-start" } }),
      el("h1", { clase: "config__titulo", texto: "Primero, configuremos tu grafo" }),
      el("p", { clase: "config__sub", texto: "Elige cuántos nodos tendrá y cómo quieres construirlo." }),
      this.marco_nodos, this.mensaje,
      el("h2", { clase: "titulo-seccion", texto: "¿Cómo quieres crear el grafo?" }),
      el("div", { clase: "opciones" }, this.tarjeta_auto, this.tarjeta_manual),
      el("div", {}, this.boton_volver),
    );
    this.elemento = el("section", { clase: "pantalla config", "data-pantalla": "configuracion" }, this.tarjeta);
  }

  _con(accion) {
    try {
      const n = validarNumeroNodos(this.selectorNodos.value);
      this.mensaje.textContent = "";
      accion(n);
    } catch (e) {
      if (e instanceof GrafoError) this.mensaje.textContent = e.message;
      else throw e;
    }
  }

  destruir() {}
}
