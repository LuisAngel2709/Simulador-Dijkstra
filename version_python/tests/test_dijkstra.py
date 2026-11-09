import unittest

from core.dijkstra_engine import INFINITO, ejecutar_dijkstra, texto_etiqueta
from core.explicaciones import Explicacion, explicar
from core.graph import Grafo


def construir(n, aristas):
    g = Grafo(n)
    for u, v, p in aristas:
        g.agregar_arista(u, v, p)
    return g


# Ejemplo 3 del PDF (matriz de la página 5), orientado de A hacia H.
GRAFO_PDF_EJEMPLO3 = [
    ("A", "B", 3), ("A", "C", 1),
    ("B", "D", 1), ("B", "G", 5),
    ("C", "D", 2), ("C", "F", 5),
    ("D", "E", 4), ("D", "F", 2),
    ("E", "G", 2), ("E", "H", 1),
    ("F", "H", 3),
]

# Ejemplo 4 del PDF (red de caminos dirigida de la página 9).
GRAFO_PDF_EJEMPLO4 = [
    ("A", "B", 4), ("A", "C", 3),
    ("B", "C", 1), ("B", "E", 3),
    ("C", "D", 2), ("C", "E", 2),
    ("D", "E", 1), ("D", "G", 3),
    ("E", "F", 2), ("E", "G", 2),
    ("F", "G", 1), ("F", "H", 3),
    ("G", "H", 4),
]


class TestCasosBasicos(unittest.TestCase):
    def test_caso_basico(self):
        g = construir(7, [("A", "B", 2), ("B", "C", 3), ("A", "C", 9)])
        r = ejecutar_dijkstra(g, "A", "C")
        self.assertEqual(r.distancia, 5)
        self.assertEqual(r.caminos, (("A", "B", "C"),))

    def test_pesos_diferentes_varios_vertices(self):
        g = construir(8, GRAFO_PDF_EJEMPLO3)
        r = ejecutar_dijkstra(g, "A", "G")
        self.assertEqual(r.distancia, 8)  # A-B-G = 8 y A-C-D-E-G = 9
        self.assertEqual(r.caminos, (("A", "B", "G"),))

    def test_direccion_de_las_aristas(self):
        g = construir(7, [("A", "B", 2), ("B", "C", 2)])
        r = ejecutar_dijkstra(g, "C", "A")
        self.assertEqual(r.distancia, INFINITO)

    def test_origen_igual_destino(self):
        g = construir(7, [("A", "B", 2)])
        r = ejecutar_dijkstra(g, "A", "A")
        self.assertEqual(r.distancia, 0)
        self.assertEqual(r.caminos, (("A",),))
        self.assertTrue(r.snapshots[-1].es_final)

    def test_destino_inalcanzable(self):
        g = construir(7, [("A", "B", 2), ("C", "D", 4)])
        r = ejecutar_dijkstra(g, "A", "D")
        self.assertEqual(r.distancia, INFINITO)
        self.assertEqual(r.caminos, ())
        self.assertFalse(r.alcanzable)
        final = explicar(g, r, len(r.snapshots) - 1)
        self.assertIn("Por qué no hay camino", [b.texto for b in final.breve])

    def test_empate_en_la_seleccion_no_pierde_caminos(self):
        # B y C quedan ambos a distancia 4 desde A.
        g = construir(7, [
            ("A", "B", 4), ("A", "C", 4),
            ("B", "D", 2), ("C", "D", 2),
        ])
        r = ejecutar_dijkstra(g, "A", "D")
        self.assertEqual(r.distancia, 6)
        self.assertEqual(r.cantidad_caminos, 2)


class TestFidelidadAlPDF(unittest.TestCase):
    def test_ejemplo3_distancia_y_dos_caminos(self):
        g = construir(8, GRAFO_PDF_EJEMPLO3)
        r = ejecutar_dijkstra(g, "A", "H")
        self.assertEqual(r.distancia, 8)
        self.assertEqual(r.cantidad_caminos, 2)
        self.assertIn(("A", "C", "D", "F", "H"), r.caminos)
        self.assertIn(("A", "C", "D", "E", "H"), r.caminos)

    def test_ejemplo3_etiquetas_intermedias(self):
        g = construir(8, GRAFO_PDF_EJEMPLO3)
        r = ejecutar_dijkstra(g, "A", "H")
        esperado = {"A": 0, "B": 3, "C": 1, "D": 3, "E": 7, "F": 5, "G": 8, "H": 8}
        self.assertEqual(dict(r.distancias), esperado)
        self.assertEqual(r.predecesores["F"], ("D",))  # se descarta [6, C]

    def test_ejemplo4_etiqueta_de_E_y_camino_unico(self):
        g = construir(8, GRAFO_PDF_EJEMPLO4)
        r = ejecutar_dijkstra(g, "A", "H")
        self.assertEqual(r.distancia, 10)
        self.assertEqual(r.cantidad_caminos, 1)
        self.assertEqual(r.caminos[0], ("A", "C", "E", "F", "H"))
        # El PDF concluye que la etiqueta de E es [5, C] en la iteración 2.
        final = r.snapshots[-1]
        self.assertEqual(final.distancias["E"], 5)
        self.assertEqual(final.predecesores["E"], ("C",))
        self.assertEqual(final.iteracion_etiqueta["E"], 2)
        self.assertEqual(final.etiqueta("E"), "[5, C]₂")

    def test_etiqueta_del_origen(self):
        g = construir(8, GRAFO_PDF_EJEMPLO3)
        r = ejecutar_dijkstra(g, "A", "H")
        self.assertEqual(r.snapshots[0].etiqueta("A"), "[0, -]₀")


class TestPredecesoresMultiples(unittest.TestCase):
    def test_distancia_menor_reemplaza_predecesores(self):
        g = construir(7, [
            ("A", "B", 1), ("A", "C", 9), ("B", "C", 2),
        ])
        r = ejecutar_dijkstra(g, "A", "C")
        self.assertEqual(r.predecesores["C"], ("B",))
        self.assertEqual(r.distancia, 3)

    def test_distancia_igual_agrega_predecesor(self):
        g = construir(7, [
            ("A", "B", 2), ("A", "C", 2), ("B", "D", 3), ("C", "D", 3),
        ])
        r = ejecutar_dijkstra(g, "A", "D")
        self.assertEqual(set(r.predecesores["D"]), {"B", "C"})

    def test_distancia_mayor_no_altera_la_etiqueta(self):
        g = construir(7, [
            ("A", "B", 1), ("A", "C", 1), ("B", "D", 1), ("C", "D", 8),
        ])
        r = ejecutar_dijkstra(g, "A", "D")
        self.assertEqual(r.predecesores["D"], ("B",))
        self.assertEqual(r.distancia, 2)

    def test_etiquetas_separadas_en_empate(self):
        # Múltiples predecesores deben mostrarse como etiquetas separadas
        etiqueta = texto_etiqueta(13, ["D", "E"], 5)
        self.assertEqual(etiqueta, "[13, D]₅  [13, E]₅")

    def test_explicacion_reemplazo_incluye_razon_pedagogica(self):
        g = construir(7, [
            ("A", "B", 10), ("A", "C", 2), ("C", "B", 3),
        ])
        r = ejecutar_dijkstra(g, "A", "B")
        # En algún snapshot de actualización debe figurar la explicación pedagógica
        # (la única fuente de textos es core.explicaciones)
        textos = [Explicacion.texto_plano(explicar(g, r, i).detalle) for i in range(len(r.snapshots))]
        self.assertTrue(
            any("pasar por C es un recorrido más corto" in t and "se descarta" in t for t in textos),
            "Debe incluir la razón pedagógica en el reemplazo de etiquetas"
        )

    def test_el_snapshot_ya_no_guarda_textos_de_explicacion(self):
        # Única fuente de explicaciones: core.explicaciones.explicar
        r = ejecutar_dijkstra(construir(7, [("A", "B", 1)]), "A", "B")
        self.assertFalse(hasattr(r.snapshots[0], "explicacion"))


if __name__ == "__main__":
    unittest.main()
