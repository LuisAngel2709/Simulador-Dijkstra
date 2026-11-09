"""Explicaciones didácticas de cada paso de la simulación.

Este módulo NO ejecuta ni duplica el algoritmo: solo lee los snapshots que ya
produjo el motor (distancias, predecesores, visitados, aristas evaluadas,
etiquetas descartadas) y el grafo (para conocer el peso de cada arista). Todo
número que aparece en un texto sale de ese estado; no se calcula nada nuevo más
allá de la suma ``distancia(u) + peso(u, v)`` que el propio paso muestra.

Tampoco depende de la interfaz: devuelve bloques de texto con un estilo
semántico que la pantalla se encarga de dibujar.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dijkstra_engine import (
    ACTUALIZACION,
    FINAL,
    INFINITO,
    INICIO,
    SELECCION,
    ResultadoDijkstra,
    Snapshot,
    formato_distancia,
)
from .graph import Grafo

# Estilos de los bloques
TITULO = "titulo"        # encabezado de sección
TEXTO = "texto"          # párrafo
CALCULO = "calculo"      # línea de cálculo (tipografía monoespaciada)
TABLA = "tabla"          # fila de una tabla de texto (monoespaciada)
NOTA = "nota"            # aclaración secundaria
EXITO = "exito"          # resultado favorable
ALERTA = "alerta"        # resultado desfavorable


@dataclass(frozen=True)
class Bloque:
    estilo: str
    texto: str


@dataclass(frozen=True)
class Explicacion:
    """``breve`` es lo que se ve en el panel; ``detalle`` alimenta «Más detalles»."""

    titulo: str
    subtitulo: str
    breve: tuple[Bloque, ...]
    detalle: tuple[Bloque, ...]

    @staticmethod
    def texto_plano(bloques) -> str:
        return "\n".join(b.texto for b in bloques)


# ---------------------------------------------------------------------- utilidades

def _d(distancia: float) -> str:
    return formato_distancia(distancia)


def _lista(vertices) -> str:
    vertices = list(vertices)
    if not vertices:
        return "ninguno"
    if len(vertices) == 1:
        return vertices[0]
    return ", ".join(vertices[:-1]) + " y " + vertices[-1]


def _calculo(snapshot: Snapshot, grafo: Grafo, u: str, v: str) -> tuple[int, float]:
    """(peso, distancia nueva) de la arista u → v según el estado del snapshot."""
    peso = grafo.peso(u, v)
    return peso, snapshot.distancias[u] + peso


def _formula(distancia_u: float, peso: int, nueva: float, u: str, v: str) -> str:
    return f"{u} → {v}: {_d(distancia_u)} + {peso} = {_d(nueva)}"


def _etiqueta_descartada(snapshot: Snapshot, v: str) -> str | None:
    return next((t for vert, t in snapshot.etiquetas_descartadas if vert == v), None)


def _bloque_etiquetas() -> tuple[Bloque, ...]:
    return (
        Bloque(TITULO, "Cómo leer una etiqueta [d, V]ₙ"),
        Bloque(
            TEXTO,
            "d es la distancia acumulada desde el origen; V es el predecesor, es decir, "
            "el vértice por el que se llega con esa distancia; el subíndice n indica en "
            "qué iteración se asignó la etiqueta. Si dos recorridos empatan en distancia, "
            "el vértice conserva una etiqueta por cada predecesor.",
        ),
    )


def _tabla_estado(snapshot: Snapshot, grafo: Grafo) -> tuple[Bloque, ...]:
    filas = [Bloque(TITULO, "Estado de todos los vértices"),
             Bloque(TABLA, f"{'Vértice':<8}{'Distancia':<11}{'Predecesor':<13}Estado")]
    for v in grafo.vertices:
        distancia = snapshot.distancias[v]
        preds = "/".join(snapshot.predecesores.get(v, ())) or "-"
        if v in snapshot.visitados:
            estado = "visitado"
        elif distancia == INFINITO:
            estado = "sin alcanzar"
        else:
            estado = "pendiente"
        filas.append(Bloque(TABLA, f"{v:<8}{_d(distancia):<11}{preds:<13}{estado}"))
    return tuple(filas)


def _anterior(resultado: ResultadoDijkstra, indice: int) -> Snapshot | None:
    return resultado.snapshots[indice - 1] if indice > 0 else None


# ------------------------------------------------------------------------- API

def explicar(grafo: Grafo, resultado: ResultadoDijkstra, indice: int) -> Explicacion:
    """Explicación del snapshot ``indice`` a partir del estado ya calculado."""
    snapshot = resultado.snapshots[indice]
    if snapshot.subpaso == INICIO:
        return _explicar_inicio(grafo, resultado, snapshot)
    if snapshot.subpaso == SELECCION:
        return _explicar_seleccion(grafo, resultado, indice, snapshot)
    if snapshot.subpaso == ACTUALIZACION:
        return _explicar_actualizacion(grafo, resultado, indice, snapshot)
    return _explicar_final(grafo, resultado, snapshot)


# ---------------------------------------------------------------------- inicio

def _explicar_inicio(grafo, resultado, snapshot) -> Explicacion:
    o = resultado.origen
    if o == resultado.destino:
        breve = (
            Bloque(TITULO, "Qué hace"),
            Bloque(TEXTO, f"Etiqueta el origen {o} con [0, -]₀. Como el destino es el mismo vértice, "
                          "ya no hay nada más que calcular."),
            Bloque(TITULO, "Origen y destino coinciden"),
            Bloque(TEXTO, f"La distancia de un vértice a sí mismo es 0, así que Dijkstra termina "
                          f"de inmediato: el camino mínimo es solo {o}."),
        )
        detalle = (*breve,
                   Bloque(TEXTO, "No se genera ninguna iteración de selección ni de actualización: "
                                 "no se elige ningún otro vértice ni se examina ninguna arista."),
                   Bloque(TEXTO, "Para ver el algoritmo en acción, elige un destino distinto del origen."),
                   *_bloque_etiquetas(), *_tabla_estado(snapshot, grafo))
        return Explicacion(snapshot.titulo, "Etiquetado inicial", breve, detalle)
    breve = (
        Bloque(TITULO, "Qué hace"),
        Bloque(TEXTO, f"Prepara el algoritmo: etiqueta el origen {o} con [0, -]₀ y deja "
                      "todos los demás vértices a distancia infinita (∞)."),
        Bloque(TITULO, "Por qué"),
        Bloque(TEXTO, f"Se parte de {o} porque la distancia de un vértice a sí mismo es 0; "
                      "de ahí en adelante, cada distancia se construye a partir de otra ya conocida."),
    )
    detalle = (
        Bloque(TITULO, "Qué ocurre en este paso"),
        Bloque(TEXTO, f"Antes de procesar nada, el algoritmo registra lo único que se sabe con certeza: "
                      f"llegar a {o} desde {o} cuesta 0. Para el resto de vértices todavía no se conoce "
                      "ningún recorrido, así que su distancia acumulada es infinita (∞) y no tienen predecesor."),
        Bloque(TITULO, "Qué vendrá después"),
        Bloque(TEXTO, "Dijkstra repite dos subpasos hasta quedarse sin vértices alcanzables:"),
        Bloque(TEXTO, "1. Selección: se elige, entre los vértices aún no visitados, el de menor distancia acumulada."),
        Bloque(TEXTO, "2. Actualización: se examinan las aristas que salen del vértice elegido y, para cada "
                      "vecino no visitado, se compara la distancia que ofrece pasar por él con la etiqueta que "
                      "el vecino ya tenía."),
        *_bloque_etiquetas(),
        *_tabla_estado(snapshot, grafo),
    )
    return Explicacion(snapshot.titulo, "Etiquetado inicial", breve, detalle)


# ------------------------------------------------------------------- selección

def _explicar_seleccion(grafo, resultado, indice, snapshot) -> Explicacion:
    previo = _anterior(resultado, indice)
    u = snapshot.seleccionado
    d_u = snapshot.distancias[u]
    candidatos = sorted(
        (v for v in grafo.vertices if v not in previo.visitados and previo.distancias[v] != INFINITO),
        key=lambda v: (previo.distancias[v], v),
    )
    empatados = [v for v in candidatos if v != u and previo.distancias[v] == d_u]
    otros = [v for v in candidatos if v != u]
    sin_alcanzar = [v for v in grafo.vertices if v not in previo.visitados and previo.distancias[v] == INFINITO]
    lista_candidatos = ", ".join(f"{v} ({_d(previo.distancias[v])})" for v in candidatos)
    etiqueta_u = snapshot.etiqueta(u)

    if d_u == 0:
        por_que = (f"El origen tiene distancia 0, la menor posible (los pesos son positivos): "
                   "siempre es el primero en procesarse y su etiqueta ya es definitiva.")
    else:
        por_que = (
            f"Con pesos positivos, ningún recorrido que pase por otros vértices pendientes puede llegar a "
            f"{u} con menos de {_d(d_u)}: por eso su etiqueta ya es definitiva."
        )
    if empatados:
        por_que += (f" {_lista(empatados)} tiene{'n' if len(empatados) > 1 else ''} la misma distancia; "
                    "el empate se resuelve por orden alfabético y no se pierde ningún camino mínimo.")

    corto = (f"Con pesos positivos, ningún otro recorrido puede llegar a {u} con menos de {_d(d_u)}: "
             "su etiqueta ya es definitiva." if d_u != 0 else
             "El origen tiene distancia 0, la menor posible: siempre se procesa primero.")
    if empatados:
        corto += f" Empata con {_lista(empatados)}: se desempata por orden alfabético."
    breve = [
        Bloque(TITULO, "Qué hace"),
        Bloque(TEXTO, f"Elige {u}, el vértice no visitado con menor distancia acumulada ({_d(d_u)})."),
        Bloque(TITULO, "Candidatos"),
        Bloque(CALCULO, lista_candidatos),
        Bloque(TITULO, "Por qué"),
        Bloque(TEXTO, corto),
    ]
    if u == resultado.destino and u != resultado.origen:
        breve.append(Bloque(NOTA, f"{u} es el destino, pero se sigue con los demás vértices alcanzables "
                                  "para no perder predecesores de igual distancia."))

    detalle = [
        Bloque(TITULO, "Qué ocurre en este paso"),
        Bloque(TEXTO, f"Subpaso 1 de la iteración {snapshot.iteracion}: selección. El algoritmo mira todos los "
                      "vértices que todavía no se han visitado y que ya tienen una distancia finita, y elige el menor."),
        Bloque(TITULO, "Vértices candidatos (no visitados con distancia finita)"),
        *[Bloque(CALCULO, f"{v:<3} distancia {_d(previo.distancias[v]):<4} etiqueta {previo.etiqueta(v)}"
                          + ("   ← elegido" if v == u else ""))
          for v in candidatos],
    ]
    if sin_alcanzar:
        detalle.append(Bloque(NOTA, f"Todavía sin alcanzar (distancia ∞), por lo que no compiten: {_lista(sin_alcanzar)}."))
    detalle += [
        Bloque(TITULO, "Por qué es correcto elegir " + u),
        Bloque(TEXTO, por_que),
        Bloque(TEXTO, "Cualquier otro recorrido hacia " + u + " tendría que pasar antes por un vértice pendiente, "
                      "cuya distancia ya es igual o mayor, y sumarle pesos positivos solo puede aumentar el total."),
    ]
    if not otros:
        detalle.append(Bloque(NOTA, f"{u} es el único candidato en este momento."))
    detalle += [
        Bloque(TITULO, "Qué vendrá después"),
        Bloque(TEXTO, f"{u} pasa a la lista de visitados. En el subpaso siguiente se examinarán sus aristas salientes."),
        *_bloque_etiquetas(),
        *_tabla_estado(snapshot, grafo),
    ]
    return Explicacion(snapshot.titulo, "Subpaso 1 · Selección", tuple(breve), tuple(detalle))


# ----------------------------------------------------------------- actualización

def _lineas_de_arista(grafo, snapshot, anterior, u, v, tipo):
    """(fórmula, conclusión corta, conclusión larga) de una arista evaluada."""
    d_u = snapshot.distancias[u]
    peso = grafo.peso(u, v)
    nueva = d_u + peso
    antes = anterior.distancias[v]
    formula = _formula(d_u, peso, nueva, u, v)
    if tipo == "mejora" and antes == INFINITO:
        corta = f"{v} no tenía distancia (∞): se etiqueta {v} con {snapshot.etiqueta(v)}."
        larga = (f"{v} todavía no había sido alcanzado (distancia ∞), así que cualquier recorrido es mejor: "
                 f"se le asigna la etiqueta {snapshot.etiqueta(v)}, con {u} como predecesor.")
    elif tipo == "mejora":
        vieja = _etiqueta_descartada(snapshot, v) or anterior.etiqueta(v)
        corta = (f"{_d(nueva)} < {_d(antes)}: se reemplaza {vieja} por {snapshot.etiqueta(v)}.")
        larga = (f"{_d(nueva)} es menor que la distancia actual de {v} ({_d(antes)}): pasar por {u} es un "
                 f"recorrido más corto. La etiqueta anterior {vieja} se descarta (aparece tachada) y {v} "
                 f"pasa a tener {snapshot.etiqueta(v)}.")
    elif tipo == "empate":
        corta = (f"{_d(nueva)} = {_d(antes)}: empate, {v} conserva su distancia y suma a {u} como predecesor.")
        larga = (f"{_d(nueva)} es igual a la distancia actual de {v} ({_d(antes)}). No hay un recorrido mejor, "
                 f"pero sí otro igual de corto: {v} conserva su distancia y registra también a {u} como "
                 f"predecesor ({snapshot.etiqueta(v)}). Así se conservan todos los caminos mínimos.")
    else:
        corta = f"{_d(nueva)} > {_d(antes)}: se conserva la etiqueta actual de {v}."
        larga = (f"{_d(nueva)} es mayor que la distancia actual de {v} ({_d(antes)}): pasar por {u} no mejora "
                 f"nada, así que {v} conserva su etiqueta {anterior.etiqueta(v)}. El cálculo queda tachado "
                 "en la tabla.")
    return formula, corta, larga


def _explicar_actualizacion(grafo, resultado, indice, snapshot) -> Explicacion:
    anterior = _anterior(resultado, indice)  # snapshot de la selección: estado ANTES de actualizar
    u = snapshot.seleccionado
    d_u = snapshot.distancias[u]
    evaluadas = list(snapshot.aristas_evaluadas)
    omitidas = [w for w, _ in grafo.salientes(u) if w in snapshot.visitados]

    por_que = (f"Pasar por {u} puede acortar el camino a sus vecinos. Cada vecino conserva la menor "
               "distancia (y todos los predecesores si hay empate).")

    breve = [
        Bloque(TITULO, "Qué hace"),
        Bloque(TEXTO, f"Examina las aristas de {u} (distancia {_d(d_u)}) hacia vértices no visitados: "
                      f"distancia({u}) + peso."),
    ]
    if evaluadas:
        breve.append(Bloque(TITULO, "Cálculos"))
        for v, tipo in ((v, t) for _, v, t in evaluadas):
            formula, corta, _ = _lineas_de_arista(grafo, snapshot, anterior, u, v, tipo)
            breve.append(Bloque(CALCULO, formula))
            breve.append(Bloque(TEXTO, "   " + corta))
    else:
        breve.append(Bloque(TEXTO, f"{u} no tiene aristas hacia vértices no visitados: no hay etiquetas que actualizar."))
    if omitidas:
        breve.append(Bloque(NOTA, f"Se omiten las aristas hacia {_lista(omitidas)}: ya están visitados y su "
                                  "distancia es definitiva."))
    breve += [Bloque(TITULO, "Por qué"), Bloque(TEXTO, por_que)]

    detalle = [
        Bloque(TITULO, "Qué ocurre en este paso"),
        Bloque(TEXTO, f"Subpaso 2 de la iteración {snapshot.iteracion}: actualización. {u} ya está visitado "
                      f"con distancia {_d(d_u)}. Para cada arista {u} → v hacia un vértice no visitado se calcula "
                      f"distancia nueva = d({u}) + peso({u}, v) y se compara con la distancia actual de v."),
        Bloque(TITULO, "Reglas de comparación"),
        Bloque(TEXTO, "• Si la distancia nueva es menor: se reemplaza la etiqueta (la anterior se descarta)."),
        Bloque(TEXTO, "• Si es igual: se conserva la distancia y se añade un predecesor (hay otro camino igual de corto)."),
        Bloque(TEXTO, "• Si es mayor: no se cambia nada."),
    ]
    if evaluadas:
        detalle.append(Bloque(TITULO, "Cálculo arista por arista"))
        for _, v, tipo in evaluadas:
            formula, _, larga = _lineas_de_arista(grafo, snapshot, anterior, u, v, tipo)
            detalle.append(Bloque(CALCULO, formula))
            detalle.append(Bloque(TEXTO, larga))
    else:
        detalle.append(Bloque(TEXTO, f"{u} no tiene aristas salientes hacia vértices no visitados; "
                                     "el paso no modifica ninguna etiqueta."))
    if omitidas:
        detalle.append(Bloque(NOTA, f"Aristas omitidas: {u} → {_lista(omitidas)}. Esos vértices ya fueron visitados, "
                                    "lo que significa que su distancia mínima ya es definitiva y no puede mejorarse."))
    siguiente = resultado.snapshots[indice + 1] if indice + 1 < len(resultado.snapshots) else None
    detalle.append(Bloque(TITULO, "Qué vendrá después"))
    if siguiente is not None and siguiente.subpaso == FINAL:
        detalle.append(Bloque(TEXTO, "No quedan vértices alcanzables sin visitar: el siguiente paso muestra el resultado final."))
    else:
        detalle.append(Bloque(TEXTO, "Se volverá a elegir, entre los no visitados con distancia finita, el de menor distancia acumulada."))
    detalle += [*_bloque_etiquetas(), *_tabla_estado(snapshot, grafo)]
    return Explicacion(snapshot.titulo, "Subpaso 2 · Actualización", tuple(breve), tuple(detalle))


# -------------------------------------------------------------------------- final

def _explicar_final(grafo, resultado, snapshot) -> Explicacion:
    o, d = resultado.origen, resultado.destino
    alcanzados = [v for v in grafo.vertices if snapshot.distancias[v] != INFINITO]
    # El cuadro «Resultado» de la pantalla ya muestra distancia y caminos: aquí se explica qué significan.
    por_que_fin = ("Terminó porque no queda ningún vértice no visitado con distancia finita: "
                   "las distancias de todos los alcanzables ya son definitivas.")

    if o == d:
        breve = (
            Bloque(TITULO, "Origen y destino coinciden"),
            Bloque(TEXTO, f"{o} es a la vez origen y destino: la distancia mínima es 0 y el camino "
                          f"mínimo es solo el vértice {o}."),
            Bloque(TEXTO, "Dijkstra terminó de inmediato: no hubo selecciones ni actualizaciones, "
                          "y no se recorrió ninguna arista."),
        )
        detalle = (*breve, *_bloque_etiquetas(), *_tabla_estado(snapshot, grafo))
        return Explicacion(snapshot.titulo, "Fin de la simulación", breve, detalle)

    if not resultado.alcanzable:
        breve = (
            Bloque(TITULO, "Qué hace"),
            Bloque(TEXTO, por_que_fin),
            Bloque(TITULO, "Por qué no hay camino"),
            Bloque(ALERTA, f"{d} nunca recibió una etiqueta (distancia ∞)."),
            Bloque(TEXTO, f"Desde {o} solo se pueden alcanzar {_lista(alcanzados)}."),
        )
        detalle = (*breve, *_bloque_etiquetas(), *_tabla_estado(snapshot, grafo))
        return Explicacion(snapshot.titulo, "Fin de la simulación", breve, detalle)

    n = resultado.cantidad_caminos
    lineas_caminos = []
    for camino in resultado.caminos:
        pesos = [grafo.peso(a, b) for a, b in zip(camino, camino[1:])]
        lineas_caminos.append(Bloque(
            CALCULO, " → ".join(camino) + "   =   " + " + ".join(map(str, pesos)) + f" = {_d(sum(pesos))}"))
    plural = n != 1
    breve = [
        Bloque(TITULO, "Qué hace"),
        Bloque(TEXTO, por_que_fin),
        Bloque(TITULO, "Cómo se obtuvo"),
        Bloque(TEXTO, f"La etiqueta de {d} es {snapshot.etiqueta(d)}. Siguiendo los predecesores hacia atrás, "
                      f"desde {d} hasta {o}, se reconstruye " + ("cada camino mínimo." if plural else "el camino mínimo.")),
    ]
    if resultado.truncado:
        breve.append(Bloque(NOTA, "Se muestra solo una parte de los caminos por su elevada cantidad."))
    detalle = [
        Bloque(EXITO, f"Distancia mínima de {o} a {d}: {_d(resultado.distancia)}."),
        Bloque(TITULO, "Cómo se obtuvo"),
        Bloque(TEXTO, f"La etiqueta de {d} es {snapshot.etiqueta(d)}. Para reconstruir el recorrido se sigue "
                      f"hacia atrás el predecesor de cada vértice, desde {d} hasta {o}."),
        Bloque(TEXTO, (f"Existen {n} caminos mínimos distintos porque al menos un vértice del recorrido "
                       "conservó varios predecesores con la misma distancia.") if plural
               else "Cada vértice del recorrido tiene un único predecesor, así que el camino mínimo es único."),
        Bloque(TITULO, "Caminos mínimos y suma de pesos"),
        *lineas_caminos,
        Bloque(TEXTO, por_que_fin),
        *_bloque_etiquetas(),
        *_tabla_estado(snapshot, grafo),
    ]
    return Explicacion(snapshot.titulo, "Fin de la simulación", tuple(breve), tuple(detalle))
