"""Generación aleatoria de grafos dirigidos acíclicos organizados por capas.

El grafo se construye sobre capas explícitas (una capa de origen, varias capas
intermedias y una capa de destino). Solo se crean aristas hacia capas
posteriores, de modo que el DAG está garantizado por construcción, y como cada
vértice recibe al menos una arista de la capa inmediatamente anterior, la
estructura por capas del grafo coincide con la que después calcula el layout.

Restricciones que mantienen el dibujo legible:
  * la mayoría de las aristas unen capas consecutivas;
  * los saltos son como mucho de dos capas y están limitados en número;
  * el grado de entrada y de salida está acotado;
  * el reparto en capas y las aristas extra son aleatorios, así que dos grafos
    con el mismo número de nodos no tienen la misma forma.
"""

from __future__ import annotations

import random

from .graph import PESO_MAXIMO, PESO_MINIMO, Grafo

MAX_SALIENTES = 3
MAX_ENTRANTES = 3
TAMANOS_DE_CAPA = [2, 3, 3, 4]


def densidad_por_defecto(n: int) -> float:
    """Probabilidad de arista extra entre capas consecutivas."""
    return 0.38 if n <= 9 else 0.28


def repartir_en_capas(n: int, azar: random.Random) -> list[int]:
    """Tamaños de cada capa: la primera y la última siempre tienen un vértice.

    El origen y el destino quedan así aislados en sus capas, lo que produce la
    silueta de diagrama académico y garantiza que exista camino entre ambos.
    """
    restante = n - 2
    tamanos: list[int] = []
    while restante > 0:
        tam = min(azar.choice(TAMANOS_DE_CAPA), restante)
        if restante - tam == 1:  # evita dejar suelta una capa de un solo vértice
            tam = restante if tam + 1 <= max(TAMANOS_DE_CAPA) else tam - 1
        tamanos.append(tam)
        restante -= tam
    return [1] + tamanos + [1]


def generar_dag(
    n: int,
    densidad: float | None = None,
    rng: random.Random | None = None,
    peso_maximo: int = 9,
) -> tuple[Grafo, str, str]:
    """Genera un DAG por capas y devuelve (grafo, origen, destino).

    Todos los vértices son alcanzables desde el origen y todos alcanzan el
    destino, de modo que la simulación siempre resulta útil.

    Los pesos se sortean en un rango pequeño (1..9 por defecto) para que el
    grafo sea legible y aparezcan empates con frecuencia; el rango admitido por
    el grafo sigue siendo 1..99.
    """
    if not (PESO_MINIMO <= peso_maximo <= PESO_MAXIMO):
        raise ValueError("peso_maximo fuera del rango admitido.")
    if n < 3:
        raise ValueError("La generación por capas necesita al menos 3 vértices.")
    if densidad is None:
        densidad = densidad_por_defecto(n)

    azar = rng or random.Random()
    grafo = Grafo(n)
    vertices = list(grafo.vertices)
    azar.shuffle(vertices)

    capas: list[list[str]] = []
    inicio = 0
    for tam in repartir_en_capas(n, azar):
        capas.append(vertices[inicio:inicio + tam])
        inicio += tam

    def conectar(u: str, v: str, forzar: bool = False) -> bool:
        if grafo.existe_arista(u, v):
            return False
        if not forzar and (
            len(grafo.salientes(u)) >= MAX_SALIENTES
            or len(grafo.entrantes(v)) >= MAX_ENTRANTES
        ):
            return False
        grafo.agregar_arista(u, v, azar.randint(PESO_MINIMO, peso_maximo))
        return True

    def menos_cargados(candidatos, clave) -> list[str]:
        """Reparte las conexiones en lugar de concentrarlas en un mismo vértice."""
        return sorted(candidatos, key=lambda x: (clave(x), azar.random()))

    # 1. Cada vértice recibe al menos una arista de la capa inmediatamente anterior.
    for k in range(1, len(capas)):
        for v in capas[k]:
            candidatos = menos_cargados(capas[k - 1], lambda u: len(grafo.salientes(u)))
            if not any(conectar(u, v) for u in candidatos):
                conectar(candidatos[0], v, forzar=True)

    # 2. Cada vértice que no esté en la última capa envía al menos una arista.
    for k in range(len(capas) - 1):
        for u in capas[k]:
            if grafo.salientes(u):
                continue
            candidatos = menos_cargados(capas[k + 1], lambda v: len(grafo.entrantes(v)))
            if not any(conectar(u, v) for v in candidatos):
                conectar(u, candidatos[0], forzar=True)

    # 3. Aristas adicionales entre capas consecutivas.
    for k in range(len(capas) - 1):
        for u in capas[k]:
            for v in capas[k + 1]:
                if azar.random() < densidad:
                    conectar(u, v)

    # 4. Unos pocos saltos de dos capas, para que el grafo no sea un simple tejido.
    saltos_permitidos = max(1, n // 5)
    saltos = 0
    for k in range(len(capas) - 2):
        for u in capas[k]:
            for v in capas[k + 2]:
                if saltos >= saltos_permitidos:
                    break
                if azar.random() < densidad / 2 and conectar(u, v):
                    saltos += 1

    return grafo, capas[0][0], capas[-1][0]


def generar_dag_didactico(
    n: int,
    densidad: float | None = None,
    intentos: int = 40,
    rng: random.Random | None = None,
    peso_maximo: int = 9,
) -> tuple[Grafo, str, str]:
    """Genera un DAG y prefiere, si lo encuentra, uno con varios caminos mínimos.

    Si ningún intento produce un empate, devuelve el último grafo generado: el
    resultado siempre es un DAG válido con ruta entre origen y destino.
    """
    from .dijkstra_engine import ejecutar_dijkstra  # import local: evita ciclo

    azar = rng or random.Random()
    ultimo = generar_dag(n, densidad, azar, peso_maximo)
    for _ in range(intentos):
        candidato = generar_dag(n, densidad, azar, peso_maximo)
        grafo, origen, destino = candidato
        resultado = ejecutar_dijkstra(grafo, origen, destino)
        if resultado.cantidad_caminos >= 2:
            return candidato
        ultimo = candidato
    return ultimo


def pesos_validos(grafo: Grafo) -> bool:
    return all(
        PESO_MINIMO <= peso <= PESO_MAXIMO and isinstance(peso, int)
        for _, _, peso in grafo.aristas()
    )
