import unittest

from core.dijkstra_engine import ejecutar_dijkstra, reconstruir_caminos
from core.graph import Grafo


def construir(n, aristas):
    g = Grafo(n)
    for u, v, p in aristas:
        g.agregar_arista(u, v, p)
    return g


class TestDosCaminosMinimos(unittest.TestCase):
    def test_dos_rutas_de_igual_costo(self):
        # A → B → D  y  A → C → D con el mismo costo total.
        g = construir(7, [
            ("A", "B", 3), ("A", "C", 4),
            ("B", "D", 5), ("C", "D", 4),
        ])
        r = ejecutar_dijkstra(g, "A", "D")
        self.assertEqual(r.distancia, 8)
        self.assertEqual(r.cantidad_caminos, 2)
        self.assertEqual(set(r.caminos), {("A", "B", "D"), ("A", "C", "D")})

    def test_cuatro_caminos_por_dos_bifurcaciones(self):
        g = construir(8, [
            ("A", "B", 1), ("A", "C", 1),
            ("B", "D", 1), ("C", "D", 1),
            ("D", "E", 1), ("D", "F", 1),
            ("E", "G", 1), ("F", "G", 1),
        ])
        r = ejecutar_dijkstra(g, "A", "G")
        self.assertEqual(r.distancia, 4)
        self.assertEqual(r.cantidad_caminos, 4)
        for camino in r.caminos:
            self.assertEqual(camino[0], "A")
            self.assertEqual(camino[-1], "G")

    def test_todos_los_caminos_tienen_la_distancia_minima(self):
        g = construir(8, [
            ("A", "B", 2), ("A", "C", 3), ("A", "D", 5),
            ("B", "E", 4), ("C", "E", 3), ("D", "E", 1),
        ])
        r = ejecutar_dijkstra(g, "A", "E")
        for camino in r.caminos:
            total = sum(
                g.peso(u, v) for u, v in zip(camino, camino[1:])
            )
            self.assertEqual(total, r.distancia)


class TestReconstruccion(unittest.TestCase):
    def test_reconstruccion_directa_desde_predecesores(self):
        predecesores = {
            "A": (),
            "B": ("A",),
            "C": ("A",),
            "D": ("B", "C"),
        }
        caminos, truncado = reconstruir_caminos(predecesores, "A", "D")
        self.assertFalse(truncado)
        self.assertEqual(set(caminos), {("A", "B", "D"), ("A", "C", "D")})

    def test_origen_igual_destino(self):
        caminos, _ = reconstruir_caminos({"A": ()}, "A", "A")
        self.assertEqual(caminos, [("A",)])

    def test_limite_de_caminos(self):
        predecesores = {"A": (), "B": ("A",), "C": ("A",), "D": ("B", "C")}
        caminos, truncado = reconstruir_caminos(predecesores, "A", "D", limite=1)
        self.assertTrue(truncado)
        self.assertEqual(len(caminos), 1)


if __name__ == "__main__":
    unittest.main()
