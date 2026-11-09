"""Motor del algoritmo de Dijkstra con etiquetación al estilo académico.

Características:
  * etiqueta [d, V]n  →  distancia acumulada, predecesor(es) e iteración;
  * un vértice puede conservar VARIOS predecesores cuando hay empate de distancia;
  * la ejecución se registra en snapshots inmutables (avanzar / retroceder);
  * reconstruye TODOS los caminos mínimos entre origen y destino.

Este módulo no depende de la interfaz gráfica.
"""

from __future__ import annotations

from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .graph import Grafo, GrafoError

INFINITO = float("inf")

SUBINDICES = "₀₁₂₃₄₅₆₇₈₉"

# Subpasos de la simulación
INICIO = "inicio"
SELECCION = "seleccion"
ACTUALIZACION = "actualizacion"
FINAL = "final"

# Estados de una etiqueta en la tabla
VIGENTE = "vigente"
EMPATE = "empate"
DESCARTADA = "descartada"

LIMITE_CAMINOS = 500


def subindice(n: int) -> str:
    return "".join(SUBINDICES[int(d)] for d in str(n))


def formato_distancia(d: float) -> str:
    return "∞" if d == INFINITO else str(int(d))


def texto_etiqueta(distancia: float, predecesores, iteracion) -> str:
    """Construye la etiqueta educativa [d, V]n separando múltiples predecesores si los hay.

    ``iteracion`` puede ser un entero (mismo subíndice para todos los
    predecesores) o un diccionario ``{predecesor: iteración}`` cuando cada
    predecesor fue descubierto en una iteración distinta.
    """
    if distancia == INFINITO:
        return "[∞, -]"
    if not predecesores:
        sufijo = subindice(iteracion) if isinstance(iteracion, int) else ""
        return f"[{int(distancia)}, -]{sufijo}"
    if isinstance(iteracion, MappingABC):
        return "  ".join(
            f"[{int(distancia)}, {p}]{subindice(iteracion[p])}"
            for p in predecesores
        )
    sufijo = subindice(iteracion) if iteracion is not None else ""
    return "  ".join(f"[{int(distancia)}, {p}]{sufijo}" for p in predecesores)


@dataclass(frozen=True)
class EntradaTabla:
    """Una etiqueta registrada en la tabla del proceso."""

    vertice: str
    iteracion: int
    distancia: float
    predecesores: tuple[str, ...]
    estado: str  # VIGENTE | EMPATE | DESCARTADA

    @property
    def texto(self) -> str:
        preds = "/".join(self.predecesores) if self.predecesores else "-"
        return f"{formato_distancia(self.distancia)}, {preds}"


@dataclass
class _EntradaMutable:
    vertice: str
    iteracion: int
    distancia: float
    predecesores: list[str]
    estado: str

    def congelar(self) -> EntradaTabla:
        return EntradaTabla(
            self.vertice,
            self.iteracion,
            self.distancia,
            tuple(self.predecesores),
            self.estado,
        )


@dataclass(frozen=True)
class Snapshot:
    """Estado inmutable y completo de la simulación en un instante dado.

    Solo contiene datos. Los textos que se muestran al usuario (breves y extendidos) se
    construyen siempre en ``core.explicaciones.explicar``, que es la única fuente de explicaciones.
    """

    indice: int
    iteracion: int
    subpaso: str
    titulo: str
    distancias: Mapping[str, float]
    predecesores: Mapping[str, tuple[str, ...]]
    iteracion_etiqueta: Mapping[str, int]
    iteracion_por_predecesor: Mapping[str, Mapping[str, int]]
    visitados: frozenset
    seleccionado: str | None
    aristas_evaluadas: tuple[tuple[str, str, str], ...]  # (u, v, tipo)
    aristas_camino: tuple[tuple[str, str], ...]
    etiquetas_descartadas: tuple[tuple[str, str], ...]  # (vértice, texto tachado)
    tabla: tuple[EntradaTabla, ...]
    caminos: tuple[tuple[str, ...], ...]
    distancia_destino: float
    es_final: bool

    def etiqueta(self, vertice: str) -> str:
        iter_info = self.iteracion_por_predecesor.get(vertice) or self.iteracion_etiqueta.get(vertice)
        return texto_etiqueta(
            self.distancias[vertice],
            self.predecesores.get(vertice, ()),
            iter_info,
        )

    def iteraciones_tabla(self) -> list[int]:
        return sorted({e.iteracion for e in self.tabla})


@dataclass(frozen=True)
class ResultadoDijkstra:
    origen: str
    destino: str
    distancia: float
    caminos: tuple[tuple[str, ...], ...]
    distancias: Mapping[str, float]
    predecesores: Mapping[str, tuple[str, ...]]
    snapshots: tuple[Snapshot, ...]
    truncado: bool = False

    @property
    def alcanzable(self) -> bool:
        return self.distancia != INFINITO

    @property
    def cantidad_caminos(self) -> int:
        return len(self.caminos)


def reconstruir_caminos(
    predecesores: Mapping[str, tuple[str, ...]],
    origen: str,
    destino: str,
    limite: int = LIMITE_CAMINOS,
) -> tuple[list[tuple[str, ...]], bool]:
    """Devuelve todos los caminos mínimos origen → destino y si hubo truncamiento.

    Recorre hacia atrás todos los predecesores registrados; como el grafo de
    predecesores es acíclico, la recursión con memoización siempre termina.
    """
    truncado = False
    memoria: dict[str, list[tuple[str, ...]]] = {}

    def caminos_hasta(v: str) -> list[tuple[str, ...]]:
        nonlocal truncado
        if v == origen:
            return [(origen,)]
        if v in memoria:
            return memoria[v]
        resultado: list[tuple[str, ...]] = []
        lleno = False
        for p in predecesores.get(v, ()):  # orden estable
            for parcial in caminos_hasta(p):
                if len(resultado) >= limite:
                    # Hay un camino más del que cabe: solo ahora existe truncamiento real.
                    # Tener exactamente ``limite`` caminos NO es truncar.
                    truncado = lleno = True
                    break
                resultado.append(parcial + (v,))
            if lleno:
                break
        memoria[v] = resultado
        return resultado

    if origen == destino:
        return [(origen,)], False
    return caminos_hasta(destino), truncado


class MotorDijkstra:
    """Ejecuta Dijkstra sobre un grafo y produce la secuencia de snapshots."""

    def __init__(self, grafo: Grafo, origen: str, destino: str):
        if not grafo.existe_vertice(origen):
            raise GrafoError(f"El vértice origen {origen} no pertenece al grafo.")
        if not grafo.existe_vertice(destino):
            raise GrafoError(f"El vértice destino {destino} no pertenece al grafo.")
        self.grafo = grafo
        self.origen = origen
        self.destino = destino

        self._distancias: dict[str, float] = {v: INFINITO for v in grafo.vertices}
        self._predecesores: dict[str, list[str]] = {v: [] for v in grafo.vertices}
        self._iteracion_etiqueta: dict[str, int] = {}
        self._iter_por_pred: dict[str, dict[str, int]] = {}
        self._visitados: set[str] = set()
        self._tabla: list[_EntradaMutable] = []
        self._snapshots: list[Snapshot] = []
        self._iteracion = 0

    # ------------------------------------------------------------------ ejecución

    def ejecutar(self) -> ResultadoDijkstra:
        self._distancias[self.origen] = 0
        self._iteracion_etiqueta[self.origen] = 0
        self._tabla.append(_EntradaMutable(self.origen, 0, 0, ["-"], VIGENTE))

        coinciden = self.origen == self.destino
        self._guardar(
            subpaso=INICIO,
            titulo="Iteración 0 — Etiquetado del vértice origen",
        )

        # Origen = destino: la distancia ya es definitiva (0), no hay nada más que recorrer.
        while not coinciden:
            seleccionado = self._elegir_vertice()
            if seleccionado is None:
                break
            self._iteracion += 1
            self._paso_seleccion(seleccionado)
            self._paso_actualizacion(seleccionado)

        distancia = self._distancias[self.destino]
        caminos, truncado = reconstruir_caminos(
            {v: tuple(p) for v, p in self._predecesores.items()},
            self.origen,
            self.destino,
        )
        if distancia == INFINITO:
            caminos = []

        self._guardar_final(distancia, caminos)

        return ResultadoDijkstra(
            origen=self.origen,
            destino=self.destino,
            distancia=distancia,
            caminos=tuple(caminos),
            distancias=MappingProxyType(dict(self._distancias)),
            predecesores=MappingProxyType(
                {v: tuple(p) for v, p in self._predecesores.items()}
            ),
            snapshots=tuple(self._snapshots),
            truncado=truncado,
        )

    # --------------------------------------------------------------------- pasos

    def _elegir_vertice(self) -> str | None:
        """Vértice no visitado con menor distancia; empate por orden alfabético."""
        candidatos = [
            v
            for v in self.grafo.vertices
            if v not in self._visitados and self._distancias[v] != INFINITO
        ]
        if not candidatos:
            return None
        return min(candidatos, key=lambda v: (self._distancias[v], v))

    def _paso_seleccion(self, u: str) -> None:
        self._visitados.add(u)
        self._guardar(
            subpaso=SELECCION,
            titulo=f"Iteración {self._iteracion} — Selección de vértice",
            seleccionado=u,
        )

    def _paso_actualizacion(self, u: str) -> None:
        aristas: list[tuple[str, str, str]] = []
        descartadas: list[tuple[str, str]] = []

        vecinos = [
            (v, peso) for v, peso in self.grafo.salientes(u) if v not in self._visitados
        ]

        for v, peso in vecinos:
            nueva = self._distancias[u] + peso
            actual = self._distancias[v]

            if nueva < actual:
                if actual != INFINITO:
                    iter_info = self._iter_por_pred.get(v) or self._iteracion_etiqueta.get(v)
                    descartadas.append(
                        (v, texto_etiqueta(actual, self._predecesores[v], iter_info))
                    )
                    for entrada in self._tabla:
                        if entrada.vertice == v and entrada.estado != DESCARTADA:
                            entrada.estado = DESCARTADA
                self._distancias[v] = nueva
                self._predecesores[v] = [u]
                self._iteracion_etiqueta[v] = self._iteracion
                self._iter_por_pred[v] = {u: self._iteracion}
                self._tabla.append(
                    _EntradaMutable(v, self._iteracion, nueva, [u], VIGENTE)
                )
                aristas.append((u, v, "mejora"))

            elif nueva == actual:
                if u not in self._predecesores[v]:
                    self._predecesores[v].append(u)
                self._iter_por_pred.setdefault(v, {})[u] = self._iteracion
                for entrada in self._tabla:
                    if entrada.vertice == v and entrada.estado == VIGENTE:
                        entrada.estado = EMPATE
                self._tabla.append(
                    _EntradaMutable(v, self._iteracion, nueva, [u], EMPATE)
                )
                aristas.append((u, v, "empate"))

            else:
                self._tabla.append(
                    _EntradaMutable(v, self._iteracion, nueva, [u], DESCARTADA)
                )
                aristas.append((u, v, "descartada"))

        self._guardar(
            subpaso=ACTUALIZACION,
            titulo=f"Iteración {self._iteracion} — Actualización de etiquetas",
            seleccionado=u,
            aristas=tuple(aristas),
            descartadas=tuple(descartadas),
        )

    def _guardar_final(self, distancia, caminos) -> None:
        aristas_camino = []
        for camino in caminos:
            for a, b in zip(camino, camino[1:]):
                if (a, b) not in aristas_camino:
                    aristas_camino.append((a, b))

        self._guardar(
            subpaso=FINAL,
            titulo="Resultado final",
            caminos=tuple(caminos),
            distancia_destino=distancia,
            aristas_camino=tuple(aristas_camino),
            es_final=True,
        )

    # ----------------------------------------------------------------- snapshots

    def _guardar(
        self,
        subpaso: str,
        titulo: str,
        seleccionado: str | None = None,
        aristas: tuple = (),
        descartadas: tuple = (),
        caminos: tuple = (),
        aristas_camino: tuple = (),
        distancia_destino: float = INFINITO,
        es_final: bool = False,
    ) -> None:
        snapshot = Snapshot(
            indice=len(self._snapshots),
            iteracion=self._iteracion,
            subpaso=subpaso,
            titulo=titulo,
            distancias=MappingProxyType(dict(self._distancias)),
            predecesores=MappingProxyType(
                {v: tuple(p) for v, p in self._predecesores.items()}
            ),
            iteracion_etiqueta=MappingProxyType(dict(self._iteracion_etiqueta)),
            iteracion_por_predecesor=MappingProxyType(
                {v: MappingProxyType(dict(m)) for v, m in self._iter_por_pred.items()}
            ),
            visitados=frozenset(self._visitados),
            seleccionado=seleccionado,
            aristas_evaluadas=tuple(aristas),
            aristas_camino=tuple(aristas_camino),
            etiquetas_descartadas=tuple(descartadas),
            tabla=tuple(e.congelar() for e in self._tabla),
            caminos=tuple(caminos),
            distancia_destino=distancia_destino,
            es_final=es_final,
        )
        self._snapshots.append(snapshot)


class Simulacion:
    """Navegación por los snapshots: avanzar, retroceder, reiniciar, finalizar."""

    def __init__(self, resultado: ResultadoDijkstra):
        self.resultado = resultado
        self.snapshots = resultado.snapshots
        self.indice = 0

    @property
    def total(self) -> int:
        return len(self.snapshots)

    @property
    def actual(self) -> Snapshot:
        return self.snapshots[self.indice]

    @property
    def puede_avanzar(self) -> bool:
        return self.indice < self.total - 1

    @property
    def puede_retroceder(self) -> bool:
        return self.indice > 0

    def siguiente(self) -> Snapshot:
        if self.puede_avanzar:
            self.indice += 1
        return self.actual

    def anterior(self) -> Snapshot:
        if self.puede_retroceder:
            self.indice -= 1
        return self.actual

    def reiniciar(self) -> Snapshot:
        self.indice = 0
        return self.actual

    def finalizar(self) -> Snapshot:
        self.indice = self.total - 1
        return self.actual


def ejecutar_dijkstra(grafo: Grafo, origen: str, destino: str) -> ResultadoDijkstra:
    """Atajo cómodo para el resto de la aplicación."""
    return MotorDijkstra(grafo, origen, destino).ejecutar()
