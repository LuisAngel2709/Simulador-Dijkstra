"""Ejemplos reales para la parte «Cómo funciona Dijkstra» del tutorial.

No ejecuta ni reimplementa el algoritmo: recibe el ``ResultadoDijkstra`` que ya
produjo el motor (el de la simulación en curso o uno calculado aparte, sin
interfaz de por medio) y escoge los momentos de esa ejecución que ilustran cada
concepto. Todo texto sale de los snapshots y de ``core.explicaciones``.
Es una función pura: no modifica el resultado ni el grafo.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dijkstra_engine import ACTUALIZACION, FINAL, INFINITO, SELECCION, ResultadoDijkstra, formato_distancia
from .explicaciones import CALCULO, TEXTO, TITULO, Bloque, explicar
from .graph import Grafo


@dataclass(frozen=True)
class EjemplosAlgoritmo:
    provisionales: str
    seleccion: str
    actualizacion: str
    empates: str
    camino: str


def _seccion(bloques, titulo: str) -> list[Bloque]:
    """Bloques que siguen al encabezado ``titulo`` hasta el siguiente encabezado."""
    salida: list[Bloque] = []
    dentro = False
    for b in bloques:
        if b.estilo == TITULO:
            if dentro:
                break
            dentro = b.texto == titulo
        elif dentro:
            salida.append(b)
    return salida


def _calculos(bloques) -> list[str]:
    """Pares «fórmula + qué ocurrió» de la sección Cálculos de una actualización."""
    lineas: list[str] = []
    for b in _seccion(bloques, "Cálculos"):
        lineas.append(b.texto if b.estilo == CALCULO else b.texto.strip())
    return lineas


def _con_tres_aristas(lineas: list[str]) -> str:
    # Cada arista ocupa dos líneas (fórmula y explicación): se muestran como máximo tres.
    resto = len(lineas) // 2 - 3
    texto = "\n".join(lineas[:6])
    return texto + (f"\n(y {resto} arista{'s' if resto > 1 else ''} más)" if resto > 0 else "")


def ejemplos_algoritmo(grafo: Grafo, resultado: ResultadoDijkstra) -> EjemplosAlgoritmo:
    snaps = resultado.snapshots
    o, d = resultado.origen, resultado.destino
    indices = {k: [i for i, s in enumerate(snaps) if s.subpaso == k] for k in (SELECCION, ACTUALIZACION)}
    con_aristas = [i for i in indices[ACTUALIZACION] if snaps[i].aristas_evaluadas]

    # 1. Distancias provisionales -------------------------------------------------
    inicial = snaps[0]
    sin_distancia = sum(1 for v in grafo.vertices if inicial.distancias[v] == INFINITO)
    if o == d:
        provisionales = (f"Al empezar, {o} tiene [0, -]₀ y los otros {sin_distancia} vértices están en ∞. "
                         "Como origen y destino coinciden, el algoritmo termina enseguida y ninguno recibe distancia.")
    elif con_aristas:
        s = snaps[con_aristas[0]]
        provisionales = ", ".join(f"{v} ({formato_distancia(s.distancias[v])})"
                                  for _, v, _ in s.aristas_evaluadas)
        provisionales = (f"Al empezar, {o} tiene [0, -]₀ y los otros {sin_distancia} vértices están en ∞. "
                         f"Tras examinar las aristas de {o}, reciben una distancia provisional: {provisionales}. "
                         "Siguen siendo provisionales hasta que se seleccionen.")
    else:
        provisionales = (f"Al empezar, {o} tiene [0, -]₀ y los otros {sin_distancia} vértices están en ∞. "
                         f"{o} no tiene aristas hacia otros vértices, así que ninguno recibe distancia.")

    # 2. Selección del vértice de menor distancia -----------------------------------
    selecciones = indices[SELECCION]
    if selecciones:
        i = selecciones[1] if len(selecciones) > 1 else selecciones[0]
        e = explicar(grafo, resultado, i)
        candidatos = " ".join(b.texto for b in _seccion(e.breve, "Candidatos"))
        que_hace = " ".join(b.texto for b in _seccion(e.breve, "Qué hace"))
        seleccion = f"Iteración {snaps[i].iteracion}. Candidatos con su distancia: {candidatos}. {que_hace}"
    else:  # origen = destino: Dijkstra termina sin seleccionar nada
        seleccion = (f"En tu grafo origen y destino coinciden ({o}): no hay ninguna selección, "
                     "porque la distancia mínima ya es 0.")

    # 3. Actualización de etiquetas y predecesores ---------------------------------
    con_reemplazo = [i for i in con_aristas if snaps[i].etiquetas_descartadas]
    elegido = (con_reemplazo or con_aristas or [None])[0]
    if o == d:
        actualizacion = "En tu grafo no hay actualizaciones: origen y destino coinciden y no se examina ninguna arista."
    elif elegido is None:
        actualizacion = "En tu grafo ningún vértice alcanzable tiene aristas hacia vértices pendientes."
    else:
        e = explicar(grafo, resultado, elegido)
        actualizacion = (f"Iteración {snaps[elegido].iteracion}, desde {snaps[elegido].seleccionado}:\n"
                         + _con_tres_aristas(_calculos(e.breve)))

    # 4. Empates ----------------------------------------------------------------------
    con_empate = [i for i in con_aristas if any(t == "empate" for _, _, t in snaps[i].aristas_evaluadas)]
    if con_empate:
        e = explicar(grafo, resultado, con_empate[0])
        empates = (f"Iteración {snaps[con_empate[0]].iteracion}, desde {snaps[con_empate[0]].seleccionado}:\n"
                   + _con_tres_aristas(_calculos(e.breve)))
    else:
        empates = ("En tu grafo no se produce ningún empate en esta ejecución: cada vértice llega por un "
                   "único camino mínimo. Si usas otro grafo, verás las aristas de empate en naranja.")

    # 5. Reconstrucción del camino mínimo ---------------------------------------------
    final = explicar(grafo, resultado, len(snaps) - 1)
    if o == d:
        camino = f"En tu grafo origen y destino coinciden ({o}): la distancia es 0 y no hay camino que recorrer."
    elif not resultado.alcanzable:
        camino = f"En tu grafo {d} no es alcanzable desde {o}: nunca recibió etiqueta, así que no hay camino."
    else:
        sumas = [b.texto for b in _seccion(final.detalle, "Caminos mínimos y suma de pesos") if b.estilo == CALCULO]
        camino = (f"La etiqueta de {d} es {snaps[-1].etiqueta(d)}. Siguiendo los predecesores hacia atrás desde "
                  f"{d} hasta {o} se obtiene:\n" + "\n".join(s.replace("   ", " ") for s in sumas))
    return EjemplosAlgoritmo(provisionales, seleccion, actualizacion, empates, camino)
