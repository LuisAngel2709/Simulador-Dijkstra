"""Casos de oro («golden tests») exportados desde el motor Python.

Genera ``golden/dijkstra_golden.json``: grafos de entrada junto con TODO lo que el
motor y los módulos de texto producen para ellos. La versión web (JavaScript) debe
reproducir exactamente estos resultados; esta suite también los usa como prueba de
regresión del propio motor Python.

Uso (desde la carpeta ``simulador_dijkstra``)::

    python -m core.golden                 # regenera golden/dijkstra_golden.json
    python -m core.golden otra/ruta.json

Convenciones del JSON
  * ``∞`` (distancia infinita) se escribe como ``null``.
  * Los vértices son letras mayúsculas ``A``…``P`` y se ordenan alfabéticamente.
  * Las aristas se listan como ``[origen, destino, peso]``.
  * Los grafos están guardados en el archivo: no hace falta reproducir el generador
    aleatorio de Python para usarlos.

Este módulo solo usa la librería estándar y no depende de la interfaz.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from .dijkstra_engine import (INFINITO, LIMITE_CAMINOS, ejecutar_dijkstra, reconstruir_caminos)
from .explicaciones import explicar
from .extremos import analizar, aislados, fuentes, mensaje_advertencia, sugerir_extremos, sumideros
from .generator import generar_dag, generar_dag_didactico
from .graph import (NODOS_MAXIMO, NODOS_MINIMO, PESO_MAXIMO, PESO_MINIMO, Grafo, GrafoError,
                    validar_numero_nodos, validar_peso)
from .tutorial_algoritmo import ejemplos_algoritmo

FORMATO = 1
RUTA_POR_DEFECTO = Path(__file__).resolve().parent.parent / "golden" / "dijkstra_golden.json"


# ------------------------------------------------------------------- serialización

def _num(valor):
    """Distancia → entero, o ``None`` si es infinita."""
    return None if valor == INFINITO else int(valor)


def _bloques(bloques) -> list[dict]:
    return [{"estilo": b.estilo, "texto": b.texto} for b in bloques]


def _grafo(g: Grafo) -> dict:
    return {"n": g.n, "vertices": list(g.vertices), "aristas": [[u, v, p] for u, v, p in g.aristas()]}


def _tabla(entradas) -> list[dict]:
    return [{"vertice": e.vertice, "iteracion": e.iteracion, "distancia": _num(e.distancia),
             "predecesores": list(e.predecesores), "estado": e.estado, "texto": e.texto} for e in entradas]


def _snapshot(g: Grafo, resultado, i: int) -> dict:
    s = resultado.snapshots[i]
    e = explicar(g, resultado, i)
    return {
        "indice": s.indice,
        "iteracion": s.iteracion,
        "subpaso": s.subpaso,
        "titulo": s.titulo,
        "seleccionado": s.seleccionado,
        "es_final": s.es_final,
        "distancias": {v: _num(d) for v, d in s.distancias.items()},
        "predecesores": {v: list(p) for v, p in s.predecesores.items()},
        "iteracion_etiqueta": dict(s.iteracion_etiqueta),
        "iteracion_por_predecesor": {v: dict(m) for v, m in s.iteracion_por_predecesor.items()},
        "etiquetas": {v: s.etiqueta(v) for v in g.vertices},
        "visitados": sorted(s.visitados),
        "aristas_evaluadas": [list(a) for a in s.aristas_evaluadas],
        "aristas_camino": [list(a) for a in s.aristas_camino],
        "etiquetas_descartadas": [list(a) for a in s.etiquetas_descartadas],
        "tabla": _tabla(s.tabla),
        "caminos": [list(c) for c in s.caminos],
        "distancia_destino": _num(s.distancia_destino),
        "explicacion": {"titulo": e.titulo, "subtitulo": e.subtitulo,
                        "breve": _bloques(e.breve), "detalle": _bloques(e.detalle)},
    }


def serializar_caso(nombre: str, g: Grafo, origen: str, destino: str) -> dict:
    """Todo lo que debe reproducir un port para ``g``, ``origen`` y ``destino``."""
    r = ejecutar_dijkstra(g, origen, destino)
    ej = ejemplos_algoritmo(g, r)
    analisis = analizar(g, origen, destino)
    sug_o, sug_d = sugerir_extremos(g)
    caso = {
        "nombre": nombre,
        "grafo": _grafo(g),
        "origen": origen,
        "destino": destino,
        "resultado": {
            "distancia": _num(r.distancia),
            "alcanzable": r.alcanzable,
            "caminos": [list(c) for c in r.caminos],
            "cantidad_caminos": r.cantidad_caminos,
            "truncado": r.truncado,
            "distancias": {v: _num(d) for v, d in r.distancias.items()},
            "predecesores": {v: list(p) for v, p in r.predecesores.items()},
        },
        "snapshots": [_snapshot(g, r, i) for i in range(len(r.snapshots))],
        "tutorial": {"provisionales": ej.provisionales, "seleccion": ej.seleccion,
                     "actualizacion": ej.actualizacion, "empates": ej.empates, "camino": ej.camino},
        "extremos": {
            "fuentes": fuentes(g),
            "sumideros": sumideros(g),
            "aislados": aislados(g),
            "sugerido": [sug_o, sug_d],
            "analisis": {
                "aislados": list(analisis.aislados),
                "sin_alcance": list(analisis.sin_alcance),
                "destino_alcanzable": analisis.destino_alcanzable,
                "hay_advertencias": analisis.hay_advertencias,
                "mensaje": mensaje_advertencia(analisis) if analisis.hay_advertencias else None,
            },
        },
    }
    return caso


def grafo_desde_json(datos: dict) -> Grafo:
    g = Grafo(datos["n"])
    for u, v, p in datos["aristas"]:
        g.agregar_arista(u, v, p)
    return g


def reproducir_caso(caso: dict) -> dict:
    """Recalcula un caso guardado con el código actual (tal como lo leería ``json.loads``)."""
    g = grafo_desde_json(caso["grafo"])
    return json.loads(json.dumps(serializar_caso(caso["nombre"], g, caso["origen"], caso["destino"])))


# ------------------------------------------------------------------------ los casos

def _construir(n: int, aristas) -> Grafo:
    g = Grafo(n)
    for u, v, p in aristas:
        g.agregar_arista(u, v, p)
    return g


def _rombos(etapas: int) -> Grafo:
    """Cadena de rombos de peso 1: 2**etapas caminos mínimos."""
    g = Grafo(1 + 3 * etapas)
    nombres = g.vertices
    anterior, i = nombres[0], 1
    for _ in range(etapas):
        a, b, fin = nombres[i], nombres[i + 1], nombres[i + 2]
        i += 3
        for medio in (a, b):
            g.agregar_arista(anterior, medio, 1)
            g.agregar_arista(medio, fin, 1)
        anterior = fin
    return g


# Ejemplos 3 y 4 de la Lectura 5 (el 3 tiene dos caminos mínimos de A a H), orientados de A hacia H.
_PDF_EJEMPLO_3 = [("A", "B", 3), ("A", "C", 1), ("B", "D", 1), ("B", "G", 5), ("C", "D", 2), ("C", "F", 5),
                  ("D", "E", 4), ("D", "F", 2), ("E", "G", 2), ("E", "H", 1), ("F", "H", 3)]
_PDF_EJEMPLO_4 = [("A", "B", 4), ("A", "C", 3), ("B", "C", 1), ("B", "E", 3), ("C", "D", 2), ("C", "E", 2),
                  ("D", "E", 1), ("D", "G", 3), ("E", "F", 2), ("E", "G", 2), ("F", "G", 1), ("F", "H", 3),
                  ("G", "H", 4)]


def casos_manuales() -> list[tuple[str, Grafo, str, str]]:
    ejemplo = _construir(8, _PDF_EJEMPLO_3)
    ejemplo4 = _construir(8, _PDF_EJEMPLO_4)
    cadena = _construir(7, [("A", "B", 1), ("B", "C", 2), ("C", "D", 3), ("D", "E", 4), ("E", "F", 5), ("F", "G", 6)])
    reemplazo = _construir(7, [("A", "B", 10), ("A", "C", 2), ("C", "B", 3)])
    empate_sel = _construir(7, [("A", "B", 4), ("A", "C", 4), ("B", "D", 1), ("C", "D", 1), ("D", "E", 2)])
    aislado = _construir(7, [("A", "B", 2), ("B", "C", 1)])
    pesos_extremos = _construir(7, [("A", "B", 99), ("A", "C", 1), ("C", "B", 98), ("B", "D", 1), ("C", "D", 99)])
    dos_orillas = _construir(7, [("A", "B", 2), ("C", "D", 4), ("D", "E", 1)])
    return [
        ("pdf_ejemplo3_A_H_dos_caminos", ejemplo, "A", "H"),
        ("pdf_ejemplo3_A_G", ejemplo, "A", "G"),
        ("pdf_ejemplo3_origen_igual_destino", ejemplo, "D", "D"),
        ("pdf_ejemplo3_destino_inalcanzable_desde_D", ejemplo, "D", "B"),
        ("pdf_ejemplo4_A_H", ejemplo4, "A", "H"),
        ("cadena_lineal_A_G", cadena, "A", "G"),
        ("cadena_origen_intermedio", cadena, "C", "F"),
        ("reemplazo_de_etiqueta", reemplazo, "A", "B"),
        ("empate_en_la_seleccion", empate_sel, "A", "E"),
        ("origen_aislado_origen_igual_destino", aislado, "G", "G"),
        ("destino_aislado_inalcanzable", aislado, "A", "G"),
        ("pesos_extremos_1_y_99", pesos_extremos, "A", "D"),
        ("dos_componentes_inalcanzable", dos_orillas, "A", "E"),
        ("dos_componentes_alcanzable", dos_orillas, "C", "E"),
        ("rombos_2_etapas_n7_4_caminos", _rombos(2), "A", "G"),
        ("rombos_4_etapas_n13_16_caminos", _rombos(4), "A", "M"),
        ("rombos_5_etapas_n16_32_caminos", _rombos(5), "A", "P"),
    ]


def casos_aleatorios() -> list[tuple[str, Grafo, str, str]]:
    """Grafos generados con semillas fijas (se guardan en el JSON, no se regeneran al comparar)."""
    salida: list[tuple[str, Grafo, str, str]] = []
    # Se omiten algunos tamaños para que el archivo no crezca de más (las explicaciones son extensas).
    for n in (7, 8, 9, 10, 12, 14, 16):
        g, o, d = generar_dag(n, rng=random.Random(1000 * n + 1))
        salida.append((f"generado_n{n}", g, o, d))
    for n in (7, 10, 13, 16):
        g, o, d = generar_dag_didactico(n, rng=random.Random(7000 + n))
        salida.append((f"didactico_n{n}", g, o, d))
    # el mismo grafo con otros extremos: hacia el último vértice y con destino inalcanzable
    for n in (8, 12):
        g, _, _ = generar_dag(n, rng=random.Random(1000 * n + 1))
        primero, ultimo = g.vertices[0], g.vertices[-1]
        salida.append((f"generado_n{n}_hacia_el_ultimo_vertice", g, primero, ultimo))
        salida.append((f"generado_n{n}_destino_antes_del_origen", g, ultimo, primero))
    return salida


def casos_validacion() -> list[dict]:
    peso = ["1", "99", "50", " 7 ", "007", "0", "100", "-3", "", "   ", "abc", "2.5", "+5", "1_0", "٣", "５",
            "1 0", "0x10", "1e1", "99.0", "-0", "9" * 40]
    nodos = ["7", "16", "10", " 12 ", "0007", "6", "17", "-7", "", "  ", "abc", "7.5", "+8", "1_0", "٨", "１０",
             "7 0", "0x10", "1e1"]
    salida: list[dict] = []
    for funcion, validar, entradas in (("validar_peso", validar_peso, peso),
                                       ("validar_numero_nodos", validar_numero_nodos, nodos)):
        for texto in entradas:
            try:
                resultado, error = validar(texto), None
            except GrafoError as e:
                resultado, error = None, str(e)
            salida.append({"funcion": funcion, "entrada": texto, "valor": resultado, "error": error})
    return salida


def _paralelos(k: int) -> dict:
    pred: dict = {"S": []}
    medios = [f"M{i}" for i in range(k)]
    for m in medios:
        pred[m] = ["S"]
    pred["T"] = medios
    return pred


def casos_truncamiento() -> list[dict]:
    """Límite de caminos mínimos: 499, 500 y 501 con el límite real, y casos pequeños con límite reducido."""
    salida: list[dict] = []
    for limite, ks in ((LIMITE_CAMINOS, (499, 500, 501)), (3, (2, 3, 4)), (1, (1, 2))):
        for k in ks:
            pred = _paralelos(k)
            caminos, truncado = reconstruir_caminos({v: tuple(p) for v, p in pred.items()}, "S", "T", limite)
            salida.append({
                "nombre": f"{k}_caminos_limite_{limite}", "limite": limite, "origen": "S", "destino": "T",
                "predecesores": pred, "cantidad": len(caminos), "truncado": truncado,
                "primero": list(caminos[0]), "ultimo": list(caminos[-1]),
            })
    return salida


# ----------------------------------------------------------------------- exportación

def construir_golden() -> dict:
    casos = [serializar_caso(*c) for c in (*casos_manuales(), *casos_aleatorios())]
    return {
        "meta": {
            "formato": FORMATO,
            "descripcion": "Casos de oro del simulador de Dijkstra generados por el motor Python. "
                           "Un port debe reproducirlos exactamente.",
            "convenciones": {
                "infinito": "null",
                "vertices": "letras A..P en orden alfabético",
                "aristas": "[origen, destino, peso]",
                "etiquetas": "texto [d, V]ₙ por vértice; varios predecesores se separan con dos espacios",
                "explicacion.estilo": "titulo | texto | calculo | tabla | nota | exito | alerta",
            },
            "constantes": {"LIMITE_CAMINOS": LIMITE_CAMINOS, "PESO_MINIMO": PESO_MINIMO, "PESO_MAXIMO": PESO_MAXIMO,
                           "NODOS_MINIMO": NODOS_MINIMO, "NODOS_MAXIMO": NODOS_MAXIMO},
            "cantidad_casos": len(casos),
        },
        "casos": casos,
        "validacion": casos_validacion(),
        "truncamiento": casos_truncamiento(),
    }


def escribir_golden(ruta: Path | str = RUTA_POR_DEFECTO) -> Path:
    """Escribe el JSON (un caso por línea, para que los cambios se lean bien en diffs)."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos = construir_golden()
    def linea(x):
        return json.dumps(x, ensure_ascii=False, separators=(",", ":"))
    partes = [
        '{"meta":' + linea(datos["meta"]),
        '"casos":[\n' + ",\n".join(linea(c) for c in datos["casos"]) + "\n]",
        '"validacion":[\n' + ",\n".join(linea(c) for c in datos["validacion"]) + "\n]",
        '"truncamiento":[\n' + ",\n".join(linea(c) for c in datos["truncamiento"]) + "\n]}",
    ]
    ruta.write_text(",\n".join(partes) + "\n", encoding="utf-8")
    return ruta


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    destino = escribir_golden(argv[0] if argv else RUTA_POR_DEFECTO)
    print(f"Escrito {destino} ({destino.stat().st_size / 1024:.0f} KiB)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
