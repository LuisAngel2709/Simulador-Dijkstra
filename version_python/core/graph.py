"""Representación del grafo dirigido, ponderado y acíclico (DAG).

Este módulo no depende de la interfaz gráfica.
"""

from __future__ import annotations

import re

NOMBRES_VERTICES = "ABCDEFGHIJKLMNOP"  # soporta hasta 16 vértices

PESO_MINIMO = 1
PESO_MAXIMO = 99

NODOS_MINIMO = 7
NODOS_MAXIMO = 16


class GrafoError(ValueError):
    """Error de validación del grafo, con un mensaje apto para mostrar al usuario."""


# Formato estricto de los números escritos por el usuario: solo dígitos ASCII 0-9
# (con un «-» opcional, únicamente para poder avisar de que los negativos no se admiten).
# No se aceptan «+», guiones bajos, espacios internos ni dígitos de otros alfabetos,
# de modo que Python y JavaScript interpreten exactamente la misma entrada.
_ENTERO_ASCII = re.compile(r"-?[0-9]+")
_ESPACIOS_EXTERIORES = " \t\r\n"
_MAX_DIGITOS = 9  # más dígitos que esto es, en cualquier caso, un valor fuera de rango


def _leer_entero(valor) -> int | None:
    """Entero escrito en formato estricto, o ``None`` si el texto no tiene ese formato."""
    texto = str(valor).strip(_ESPACIOS_EXTERIORES)
    if not _ENTERO_ASCII.fullmatch(texto):
        return None
    if len(texto.lstrip("-")) > _MAX_DIGITOS:
        return -(10 ** _MAX_DIGITOS) if texto.startswith("-") else 10 ** _MAX_DIGITOS
    return int(texto)


def validar_numero_nodos(valor) -> int:
    """Valida el número de nodos introducido por el usuario (7 a 16)."""
    if not str(valor).strip(_ESPACIOS_EXTERIORES):
        raise GrafoError("Debe introducir el número de nodos.")
    n = _leer_entero(valor)
    if n is None:
        raise GrafoError("El número de nodos debe ser un número entero.")
    if not (NODOS_MINIMO <= n <= NODOS_MAXIMO):
        raise GrafoError(
            f"El número de nodos debe estar entre {NODOS_MINIMO} y {NODOS_MAXIMO}."
        )
    return n


def validar_peso(valor) -> int:
    """Valida un peso introducido por el usuario: entero positivo de 1 a 99."""
    if not str(valor).strip(_ESPACIOS_EXTERIORES):
        raise GrafoError("Debe introducir un peso.")
    peso = _leer_entero(valor)
    if peso is None:
        raise GrafoError("El peso debe ser un número entero.")
    if peso <= 0:
        raise GrafoError("El peso debe ser un entero positivo (no se admite 0 ni negativos).")
    if peso > PESO_MAXIMO:
        raise GrafoError(f"El peso debe estar entre {PESO_MINIMO} y {PESO_MAXIMO}.")
    return peso


class Grafo:
    """Grafo dirigido y ponderado que se mantiene acíclico en todo momento."""

    def __init__(self, n: int):
        if not (1 <= n <= len(NOMBRES_VERTICES)):
            raise GrafoError(
                f"El grafo admite entre 1 y {len(NOMBRES_VERTICES)} vértices."
            )
        self.vertices: list[str] = list(NOMBRES_VERTICES[:n])
        self._salientes: dict[str, dict[str, int]] = {v: {} for v in self.vertices}
        self._entrantes: dict[str, dict[str, int]] = {v: {} for v in self.vertices}

    # ------------------------------------------------------------------ consulta

    @property
    def n(self) -> int:
        return len(self.vertices)

    def existe_vertice(self, v: str) -> bool:
        return v in self._salientes

    def _exigir_vertice(self, v: str) -> None:
        if not self.existe_vertice(v):
            raise GrafoError(f"El vértice {v} no pertenece al grafo.")

    def existe_arista(self, u: str, v: str) -> bool:
        return self.existe_vertice(u) and v in self._salientes[u]

    def peso(self, u: str, v: str) -> int:
        if not self.existe_arista(u, v):
            raise GrafoError(f"No existe la arista {u} → {v}.")
        return self._salientes[u][v]

    def salientes(self, u: str) -> list[tuple[str, int]]:
        """Aristas que salen de u, ordenadas alfabéticamente por destino."""
        self._exigir_vertice(u)
        return sorted(self._salientes[u].items())

    def entrantes(self, v: str) -> list[tuple[str, int]]:
        self._exigir_vertice(v)
        return sorted(self._entrantes[v].items())

    def aristas(self) -> list[tuple[str, str, int]]:
        return [
            (u, v, p)
            for u in self.vertices
            for v, p in sorted(self._salientes[u].items())
        ]

    def cantidad_aristas(self) -> int:
        return sum(len(d) for d in self._salientes.values())

    def hay_camino(self, origen: str, destino: str) -> bool:
        """Indica si existe un camino dirigido de origen a destino."""
        self._exigir_vertice(origen)
        self._exigir_vertice(destino)
        if origen == destino:
            return True
        pendientes = [origen]
        vistos = {origen}
        while pendientes:
            actual = pendientes.pop()
            for siguiente in self._salientes[actual]:
                if siguiente == destino:
                    return True
                if siguiente not in vistos:
                    vistos.add(siguiente)
                    pendientes.append(siguiente)
        return False

    def crearia_ciclo(self, u: str, v: str) -> bool:
        """La arista u → v cerraría un ciclo si v ya alcanza a u."""
        if u == v:
            return True
        return self.hay_camino(v, u)

    def es_dag(self) -> bool:
        """Verificación independiente de aciclicidad (orden topológico de Kahn)."""
        return len(self.orden_topologico()) == self.n

    def orden_topologico(self) -> list[str]:
        """Orden topológico; si hay ciclo devuelve una lista incompleta."""
        grado = {v: len(self._entrantes[v]) for v in self.vertices}
        disponibles = sorted(v for v in self.vertices if grado[v] == 0)
        orden: list[str] = []
        while disponibles:
            actual = disponibles.pop(0)
            orden.append(actual)
            for siguiente in sorted(self._salientes[actual]):
                grado[siguiente] -= 1
                if grado[siguiente] == 0:
                    disponibles.append(siguiente)
            disponibles.sort()
        return orden

    # ---------------------------------------------------------------- modificación

    def agregar_arista(self, u: str, v: str, peso) -> None:
        """Agrega la arista dirigida u → v. Rechaza duplicados, bucles y ciclos."""
        self._exigir_vertice(u)
        self._exigir_vertice(v)
        if u == v:
            raise GrafoError("Un vértice no puede conectarse consigo mismo.")
        if self.existe_arista(u, v):
            raise GrafoError(
                f"La arista {u} → {v} ya existe. Puede modificar su peso o eliminarla."
            )
        peso_valido = validar_peso(peso)
        if self.crearia_ciclo(u, v):
            raise GrafoError(
                f"La conexión {u} → {v} produciría un ciclo, porque ya existe un "
                f"camino de {v} hacia {u}. El grafo debe ser acíclico."
            )
        self._salientes[u][v] = peso_valido
        self._entrantes[v][u] = peso_valido

    def modificar_peso(self, u: str, v: str, peso) -> None:
        if not self.existe_arista(u, v):
            raise GrafoError(f"No existe la arista {u} → {v}.")
        peso_valido = validar_peso(peso)
        self._salientes[u][v] = peso_valido
        self._entrantes[v][u] = peso_valido

    def eliminar_arista(self, u: str, v: str) -> None:
        if not self.existe_arista(u, v):
            raise GrafoError(f"No existe la arista {u} → {v}.")
        del self._salientes[u][v]
        del self._entrantes[v][u]

    def copiar(self) -> "Grafo":
        copia = Grafo(self.n)
        for u, v, p in self.aristas():
            copia._salientes[u][v] = p
            copia._entrantes[v][u] = p
        return copia

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuración
        return f"Grafo(n={self.n}, aristas={self.cantidad_aristas()})"
