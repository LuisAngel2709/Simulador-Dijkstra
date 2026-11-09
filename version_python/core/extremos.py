"""Origen y destino sugeridos, y revisión de un grafo antes de simularlo.

Funciones puras sobre ``Grafo``: no ejecutan Dijkstra ni dependen de la interfaz.

* ``sugerir_extremos``: con una sola fuente (vértice sin aristas entrantes) y un
  solo sumidero (sin salientes) devuelve exactamente esa pareja; con varias
  opciones elige una pareja válida (el destino es alcanzable desde el origen).
* ``analizar``: detecta vértices aislados, vértices que el origen no alcanza y si el
  destino es inalcanzable, para avisar al usuario antes de simular.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .graph import Grafo


def fuentes(grafo: Grafo) -> list[str]:
    """Vértices con aristas salientes y ninguna entrante (posibles orígenes)."""
    return [v for v in grafo.vertices if not grafo.entrantes(v) and grafo.salientes(v)]


def sumideros(grafo: Grafo) -> list[str]:
    """Vértices con aristas entrantes y ninguna saliente (posibles destinos)."""
    return [v for v in grafo.vertices if not grafo.salientes(v) and grafo.entrantes(v)]


def aislados(grafo: Grafo) -> list[str]:
    """Vértices sin ninguna arista (ni entrante ni saliente)."""
    return [v for v in grafo.vertices if not grafo.entrantes(v) and not grafo.salientes(v)]


def saltos_desde(grafo: Grafo, origen: str) -> dict[str, int]:
    """Número mínimo de aristas desde ``origen`` a cada vértice alcanzable (incluido él mismo)."""
    saltos = {origen: 0}
    cola = deque([origen])
    while cola:
        u = cola.popleft()
        for w, _ in grafo.salientes(u):
            if w not in saltos:
                saltos[w] = saltos[u] + 1
                cola.append(w)
    return saltos


def sugerir_extremos(grafo: Grafo) -> tuple[str, str]:
    """Pareja (origen, destino) sugerida para el grafo.

    Una sola fuente y un solo sumidero: esa pareja. Varias opciones: la fuente que
    alcanza más vértices y, entre sus sumideros alcanzables, el más lejano (así la
    simulación recorre la mayor parte del grafo); los empates se resuelven por el
    orden alfabético. Sin aristas no hay pareja significativa: primer y último vértice.
    """
    origenes, destinos = fuentes(grafo), sumideros(grafo)
    if len(origenes) == 1 and len(destinos) == 1:
        return origenes[0], destinos[0]
    mejor: tuple[tuple[int, int], str, str] | None = None
    for o in origenes:
        saltos = saltos_desde(grafo, o)
        for d in destinos:
            if d in saltos:
                clave = (len(saltos), saltos[d])
                if mejor is None or clave > mejor[0]:
                    mejor = (clave, o, d)
    if mejor is not None:
        return mejor[1], mejor[2]
    return grafo.vertices[0], grafo.vertices[-1]


@dataclass(frozen=True)
class AnalisisGrafo:
    origen: str
    destino: str
    aislados: tuple[str, ...]            # sin ninguna conexión
    sin_alcance: tuple[str, ...]         # con conexiones, pero el origen no llega a ellos
    destino_alcanzable: bool

    @property
    def hay_advertencias(self) -> bool:
        return bool(self.aislados or self.sin_alcance or not self.destino_alcanzable)


def analizar(grafo: Grafo, origen: str, destino: str) -> AnalisisGrafo:
    """Qué vértices no intervendrán en la simulación desde ``origen``."""
    alcanzados = saltos_desde(grafo, origen)
    solos = set(aislados(grafo))
    sin_alcance = [v for v in grafo.vertices if v not in alcanzados and v not in solos]
    return AnalisisGrafo(
        origen=origen,
        destino=destino,
        aislados=tuple(v for v in grafo.vertices if v in solos),
        sin_alcance=tuple(sin_alcance),
        destino_alcanzable=destino in alcanzados,
    )


def _lista(vertices) -> str:
    return ", ".join(vertices)


def mensaje_advertencia(a: AnalisisGrafo) -> str:
    """Texto de la advertencia para mostrar al usuario (una sección por problema)."""
    partes = []
    if not a.destino_alcanzable:
        partes.append(
            f"⚠ El destino {a.destino} no es alcanzable desde el origen {a.origen}: "
            "la simulación terminará sin camino."
        )
    if a.aislados:
        partes.append(f"Vértices aislados (sin ninguna conexión): {_lista(a.aislados)}.")
    if a.sin_alcance:
        partes.append(
            f"Vértices que el origen {a.origen} no alcanza y no participarán en el recorrido: "
            f"{_lista(a.sin_alcance)}."
        )
    partes.append(f"Se simulará de {a.origen} a {a.destino}; podrás cambiarlos en la simulación.")
    return "\n\n".join(partes)
