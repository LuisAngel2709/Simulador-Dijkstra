"""Origen/destino sugeridos y revisión del grafo (Core, sin interfaz)."""

import random
import unittest

from core.extremos import (
    analizar, aislados, fuentes, mensaje_advertencia, saltos_desde, sugerir_extremos, sumideros,
)
from core.generator import generar_dag, generar_dag_didactico
from core.graph import Grafo


def grafo(n, aristas):
    g = Grafo(n)
    for u, v, p in aristas:
        g.agregar_arista(u, v, p)
    return g


class TestSugerirExtremos(unittest.TestCase):
    def test_una_sola_fuente_y_un_solo_destino_se_eligen_solos(self):
        g = grafo(7, [("A", "B", 1), ("A", "C", 2), ("B", "D", 1), ("C", "D", 3), ("D", "E", 2),
                      ("E", "F", 1), ("E", "G", 4)] [:6] + [("F", "G", 1)])
        self.assertEqual((fuentes(g), sumideros(g)), (["A"], ["G"]))
        self.assertEqual(sugerir_extremos(g), ("A", "G"))

    def test_un_vertice_aislado_no_cuenta_como_fuente_ni_destino(self):
        g = grafo(7, [("B", "C", 1), ("C", "E", 2)])
        self.assertEqual(aislados(g), ["A", "D", "F", "G"])
        self.assertEqual(sugerir_extremos(g), ("B", "E"))

    def test_con_varias_opciones_elige_una_pareja_valida_y_es_determinista(self):
        g = grafo(8, [("A", "C", 1), ("B", "C", 2), ("C", "D", 3), ("C", "E", 1), ("E", "F", 2)])
        o, d = sugerir_extremos(g)
        self.assertIn(o, fuentes(g))
        self.assertIn(d, sumideros(g))
        self.assertIn(d, saltos_desde(g, o))
        self.assertEqual(sugerir_extremos(g), (o, d))
        # el origen que más alcanza y el destino más lejano: A → F (3 saltos), no A → D (2)
        self.assertEqual((o, d), ("A", "F"))

    def test_en_grafos_aleatorios_la_pareja_siempre_es_valida(self):
        azar = random.Random(3)
        for n in (7, 8, 10, 13, 16):
            for _ in range(10):
                g, _o, _d = generar_dag(n, rng=azar)
                o, d = sugerir_extremos(g)
                self.assertIn(d, saltos_desde(g, o), (n, o, d))
                self.assertIn(o, fuentes(g))
                self.assertIn(d, sumideros(g))

    def test_grafos_didacticos_conservan_su_pareja_natural_cuando_hay_una_sola(self):
        for n in (8, 10, 12):
            g, o, d = generar_dag_didactico(n)
            if len(fuentes(g)) == 1 and len(sumideros(g)) == 1:
                self.assertEqual(sugerir_extremos(g), (o, d))

    def test_sin_aristas_usa_primer_y_ultimo_vertice(self):
        self.assertEqual(sugerir_extremos(Grafo(7)), ("A", "G"))


class TestAnalizar(unittest.TestCase):
    def test_grafo_conectado_sin_advertencias(self):
        g = grafo(7, [("A", "B", 1), ("B", "C", 1), ("C", "D", 1), ("D", "E", 1), ("E", "F", 1), ("F", "G", 1)])
        a = analizar(g, "A", "G")
        self.assertFalse(a.hay_advertencias)

    def test_detecta_aislados_y_vertices_sin_alcance_por_separado(self):
        g = grafo(8, [("A", "B", 1), ("B", "C", 1), ("D", "E", 2)])  # F, G, H aislados; D y E aparte
        a = analizar(g, "A", "C")
        self.assertEqual(a.aislados, ("F", "G", "H"))
        self.assertEqual(a.sin_alcance, ("D", "E"))
        self.assertTrue(a.destino_alcanzable)
        self.assertTrue(a.hay_advertencias)

    def test_destino_inalcanzable(self):
        g = grafo(7, [("A", "B", 1), ("C", "D", 1)])
        a = analizar(g, "A", "D")
        self.assertFalse(a.destino_alcanzable)
        self.assertIn("no es alcanzable", mensaje_advertencia(a))

    def test_origen_igual_a_destino_es_alcanzable(self):
        g = grafo(7, [("A", "B", 1)])
        self.assertTrue(analizar(g, "A", "A").destino_alcanzable)

    def test_el_mensaje_nombra_cada_vertice_afectado(self):
        g = grafo(8, [("A", "B", 1), ("B", "C", 1), ("D", "E", 2)])
        texto = mensaje_advertencia(analizar(g, "A", "C"))
        self.assertIn("aislados (sin ninguna conexión): F, G, H", texto)
        self.assertIn("no alcanza", texto)
        self.assertIn("D, E", texto)
        self.assertIn("de A a C", texto)

    def test_no_modifica_el_grafo(self):
        g = grafo(8, [("A", "B", 1), ("B", "C", 1), ("D", "E", 2)])
        antes = g.aristas()
        analizar(g, "A", "C")
        sugerir_extremos(g)
        self.assertEqual(antes, g.aristas())


if __name__ == "__main__":
    unittest.main()
