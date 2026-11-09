"""Subíndice por predecesor: cada predecesor de un vértice conserva la iteración
en que fue descubierto (``Snapshot.iteracion_por_predecesor``)."""

import unittest

from core.dijkstra_engine import ACTUALIZACION, ejecutar_dijkstra, texto_etiqueta
from core.graph import Grafo


def construir(n, aristas):
    g = Grafo(n)
    for u, v, p in aristas:
        g.agregar_arista(u, v, p)
    return g


class TestIteracionPorPredecesor(unittest.TestCase):
    def setUp(self):
        # D se alcanza con distancia 4 por B (iteración 2) y por C (iteración 3): empate.
        self.empate = ejecutar_dijkstra(
            construir(7, [("A", "B", 1), ("A", "C", 2), ("B", "D", 3), ("C", "D", 2)]), "A", "D"
        )
        # C se etiqueta con [5, A]₁ y luego se reemplaza por [2, B]₂ (mejor camino).
        self.reemplazo = ejecutar_dijkstra(
            construir(7, [("A", "C", 5), ("A", "B", 1), ("B", "C", 1)]), "A", "C"
        )

    def test_cada_predecesor_del_empate_conserva_su_propia_iteracion(self):
        final = self.empate.snapshots[-1]
        self.assertEqual(dict(final.iteracion_por_predecesor["D"]), {"B": 2, "C": 3})
        self.assertEqual(final.etiqueta("D"), "[4, B]₂  [4, C]₃")

    def test_el_subindice_aparece_en_cuanto_se_descubre_cada_predecesor(self):
        por_indice = {s.indice: s for s in self.empate.snapshots}
        self.assertEqual(dict(por_indice[4].iteracion_por_predecesor["D"]), {"B": 2})
        self.assertEqual(por_indice[4].etiqueta("D"), "[4, B]₂")
        self.assertEqual(dict(por_indice[6].iteracion_por_predecesor["D"]), {"B": 2, "C": 3})
        self.assertEqual(por_indice[6].subpaso, ACTUALIZACION)

    def test_al_reemplazar_la_etiqueta_se_descarta_el_subindice_anterior(self):
        por_indice = {s.indice: s for s in self.reemplazo.snapshots}
        antes, despues = por_indice[2], por_indice[4]
        self.assertEqual(dict(antes.iteracion_por_predecesor["C"]), {"A": 1})
        self.assertEqual(antes.etiqueta("C"), "[5, A]₁")
        self.assertEqual(dict(despues.iteracion_por_predecesor["C"]), {"B": 2})
        self.assertEqual(despues.etiqueta("C"), "[2, B]₂")
        self.assertEqual(despues.etiquetas_descartadas, (("C", "[5, A]₁"),))

    def test_el_origen_y_los_vertices_sin_etiquetar_no_tienen_subindices_por_predecesor(self):
        inicial = self.empate.snapshots[0]
        self.assertEqual(dict(inicial.iteracion_por_predecesor), {})
        self.assertEqual(inicial.etiqueta("A"), "[0, -]₀")
        self.assertEqual(inicial.etiqueta("D"), "[∞, -]")

    def test_los_snapshots_anteriores_no_cambian_al_avanzar(self):
        por_indice = {s.indice: s for s in self.empate.snapshots}
        self.assertEqual(dict(por_indice[4].iteracion_por_predecesor["D"]), {"B": 2})
        self.assertEqual(por_indice[4].etiqueta("D"), "[4, B]₂")

    def test_los_mapas_por_predecesor_son_inmutables(self):
        final = self.empate.snapshots[-1]
        with self.assertRaises(TypeError):
            final.iteracion_por_predecesor["D"]["X"] = 9
        with self.assertRaises(TypeError):
            final.iteracion_por_predecesor["Z"] = {}

    def test_texto_etiqueta_acepta_entero_o_mapa(self):
        self.assertEqual(texto_etiqueta(4, ["B", "C"], 2), "[4, B]₂  [4, C]₂")
        self.assertEqual(texto_etiqueta(4, ["B", "C"], {"B": 2, "C": 3}), "[4, B]₂  [4, C]₃")
        self.assertEqual(texto_etiqueta(0, [], 0), "[0, -]₀")


if __name__ == "__main__":
    unittest.main()
