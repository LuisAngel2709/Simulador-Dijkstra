"""Detección de truncamiento de caminos mínimos: límites 499, 500 y 501."""

import unittest

from core.dijkstra_engine import LIMITE_CAMINOS, ejecutar_dijkstra, reconstruir_caminos
from core.graph import Grafo


def paralelos(k: int) -> dict:
    """S → M1…Mk → T: exactamente k caminos."""
    pred = {"S": ()}
    medios = [f"M{i}" for i in range(k)]
    for m in medios:
        pred[m] = ("S",)
    pred["T"] = tuple(medios)
    return pred


def diamantes(etapas: int) -> dict:
    """Cadena de rombos: 2**etapas caminos de S a T (el truncamiento ocurre en vértices intermedios)."""
    pred = {"S": ()}
    anterior = "S"
    for e in range(etapas):
        a, b, fin = f"a{e}", f"b{e}", "T" if e == etapas - 1 else f"j{e}"
        pred[a], pred[b] = (anterior,), (anterior,)
        pred[fin] = (a, b)
        anterior = fin
    return pred


class TestLimiteTruncamiento(unittest.TestCase):
    def test_el_limite_por_defecto_es_500(self):
        self.assertEqual(LIMITE_CAMINOS, 500)

    def test_499_caminos_no_trunca(self):
        caminos, truncado = reconstruir_caminos(paralelos(499), "S", "T")
        self.assertEqual(len(caminos), 499)
        self.assertFalse(truncado)

    def test_500_caminos_exactos_no_trunca(self):
        caminos, truncado = reconstruir_caminos(paralelos(500), "S", "T")
        self.assertEqual(len(caminos), 500)
        self.assertFalse(truncado, "tener exactamente el límite no es truncar")

    def test_501_caminos_trunca_y_devuelve_500(self):
        caminos, truncado = reconstruir_caminos(paralelos(501), "S", "T")
        self.assertEqual(len(caminos), 500)
        self.assertTrue(truncado)

    def test_muchos_mas_que_el_limite_trunca(self):
        caminos, truncado = reconstruir_caminos(paralelos(2000), "S", "T")
        self.assertEqual(len(caminos), 500)
        self.assertTrue(truncado)

    def test_los_caminos_devueltos_son_distintos_y_validos(self):
        for k in (499, 500, 501):
            caminos, _ = reconstruir_caminos(paralelos(k), "S", "T")
            self.assertEqual(len(set(caminos)), len(caminos), k)
            for c in caminos:
                self.assertEqual((c[0], c[-1], len(c)), ("S", "T", 3))

    def test_el_orden_de_los_caminos_es_estable(self):
        a, _ = reconstruir_caminos(paralelos(501), "S", "T")
        b, _ = reconstruir_caminos(paralelos(501), "S", "T")
        self.assertEqual(a, b)
        self.assertEqual(a[0], ("S", "M0", "T"))
        self.assertEqual(a[-1], ("S", "M499", "T"))


class TestLimiteParametrizado(unittest.TestCase):
    def test_en_el_limite_exacto_no_trunca_y_uno_menos_si(self):
        for k in (1, 2, 7, 162):
            caminos, truncado = reconstruir_caminos(paralelos(k), "S", "T", limite=k)
            self.assertEqual((len(caminos), truncado), (k, False), k)
            caminos, truncado = reconstruir_caminos(paralelos(k), "S", "T", limite=k - 1)
            self.assertEqual((len(caminos), truncado), (k - 1, True), k)
            caminos, truncado = reconstruir_caminos(paralelos(k), "S", "T", limite=k + 1)
            self.assertEqual((len(caminos), truncado), (k, False), k)

    def test_truncamiento_en_vertices_intermedios(self):
        # 2**9 = 512 > 500: el recorte se produce en un vértice intermedio y debe propagarse.
        caminos, truncado = reconstruir_caminos(diamantes(9), "S", "T")
        self.assertEqual((len(caminos), truncado), (500, True))
        # 2**8 = 256: cabe de sobra.
        caminos, truncado = reconstruir_caminos(diamantes(8), "S", "T")
        self.assertEqual((len(caminos), truncado), (256, False))
        # y justo en el límite de ese tamaño
        self.assertEqual(reconstruir_caminos(diamantes(8), "S", "T", limite=256), (reconstruir_caminos(diamantes(8), "S", "T")[0], False))
        self.assertTrue(reconstruir_caminos(diamantes(8), "S", "T", limite=255)[1])

    def test_origen_igual_destino_nunca_trunca(self):
        self.assertEqual(reconstruir_caminos({"S": ()}, "S", "S", limite=1), ([("S",)], False))


class TestTruncamientoEnElMotor(unittest.TestCase):
    def grafo_rombos(self, etapas: int) -> Grafo:
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

    def test_el_resultado_no_marca_truncado_con_todos_los_caminos(self):
        for etapas in (2, 3, 4, 5):  # hasta 16 vértices: 2**5 = 32 caminos
            if 1 + 3 * etapas < 7:
                continue
            g = self.grafo_rombos(etapas)
            r = ejecutar_dijkstra(g, g.vertices[0], g.vertices[-1])
            self.assertEqual(r.cantidad_caminos, 2 ** etapas)
            self.assertFalse(r.truncado)

    def test_el_motor_usa_los_predecesores_con_la_misma_regla(self):
        g = self.grafo_rombos(5)
        r = ejecutar_dijkstra(g, g.vertices[0], g.vertices[-1])
        # con el límite justo no trunca, con uno menos sí (mismos predecesores que el motor)
        caminos, truncado = reconstruir_caminos(dict(r.predecesores), r.origen, r.destino, limite=32)
        self.assertEqual((len(caminos), truncado), (32, False))
        caminos, truncado = reconstruir_caminos(dict(r.predecesores), r.origen, r.destino, limite=31)
        self.assertEqual((len(caminos), truncado), (31, True))


if __name__ == "__main__":
    unittest.main()
