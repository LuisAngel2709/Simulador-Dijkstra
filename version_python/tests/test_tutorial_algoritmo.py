"""Los ejemplos del tutorial salen del estado real del motor, sin modificarlo ni inventar cifras."""

import random
import re
import unittest

from core.dijkstra_engine import ejecutar_dijkstra, formato_distancia, INFINITO
from core.generator import generar_dag, generar_dag_didactico
from core.graph import Grafo
from core.tutorial_algoritmo import ejemplos_algoritmo

FORMULA = re.compile(r"(\w) → (\w): (\d+) \+ (\d+) = (\d+)")


def casos():
    azar = random.Random(21)
    for n in (7, 9, 12, 16):
        for _ in range(5):
            yield generar_dag(n, rng=azar)
    for n in (8, 10):
        yield generar_dag_didactico(n)
    g = Grafo(7)
    for u, v, p in [("A", "B", 2), ("A", "C", 2), ("B", "D", 3), ("C", "D", 3)]:
        g.agregar_arista(u, v, p)
    yield g, "A", "D"          # camino mínimo doble y empate
    yield g, "B", "C"          # destino inalcanzable
    yield g, "A", "A"          # origen = destino
    yield g, "G", "F"          # origen aislado


class TestEjemplos(unittest.TestCase):
    def test_todos_los_casos_producen_texto_para_cada_concepto(self):
        for g, o, d in casos():
            e = ejemplos_algoritmo(g, ejecutar_dijkstra(g, o, d))
            for campo in ("provisionales", "seleccion", "actualizacion", "empates", "camino"):
                self.assertTrue(getattr(e, campo).strip(), (o, d, campo))

    def test_las_formulas_coinciden_con_pesos_y_distancias_del_motor(self):
        for g, o, d in casos():
            r = ejecutar_dijkstra(g, o, d)
            e = ejemplos_algoritmo(g, r)
            for texto in (e.actualizacion, e.empates):
                for u, v, du, w, total in FORMULA.findall(texto):
                    self.assertEqual(g.peso(u, v), int(w), (u, v))
                    self.assertEqual(int(du) + int(w), int(total))
                    # d(u) es la distancia definitiva de u en la ejecución real
                    self.assertEqual(int(du), int(r.snapshots[-1].distancias[u]))

    def test_provisionales_nombran_al_origen_y_la_cantidad_real_de_vertices_en_infinito(self):
        for g, o, d in casos():
            r = ejecutar_dijkstra(g, o, d)
            texto = ejemplos_algoritmo(g, r).provisionales
            self.assertIn(f"{o} tiene [0, -]₀", texto)
            self.assertIn(f"los otros {g.n - 1} vértices", texto)

    def test_el_camino_suma_la_distancia_y_lista_todos_los_caminos(self):
        for g, o, d in casos():
            r = ejecutar_dijkstra(g, o, d)
            texto = ejemplos_algoritmo(g, r).camino
            if o != d and r.alcanzable:
                lineas = [l for l in texto.splitlines() if " → " in l and "=" in l]
                self.assertEqual(len(lineas), len(r.caminos), (o, d))
                for linea in lineas:
                    self.assertTrue(linea.endswith(f"= {formato_distancia(r.distancia)}"), linea)
                for camino in r.caminos:
                    self.assertTrue(any(l.startswith(" → ".join(camino)) for l in lineas), camino)
            elif o == d:
                self.assertIn("coinciden", texto)
            else:
                self.assertIn("no es alcanzable", texto)

    def test_los_empates_solo_se_describen_si_existen(self):
        for g, o, d in casos():
            r = ejecutar_dijkstra(g, o, d)
            hay = any(t == "empate" for s in r.snapshots for _, _, t in s.aristas_evaluadas)
            texto = ejemplos_algoritmo(g, r).empates
            self.assertEqual(": empate," in texto, hay, (o, d))
            self.assertEqual("no se produce ningún empate" in texto, not hay, (o, d))

    def test_no_modifica_el_resultado_del_motor(self):
        for g, o, d in casos():
            r = ejecutar_dijkstra(g, o, d)
            antes = (repr(r.snapshots), r.caminos, r.distancia, repr(g.aristas()) if hasattr(g, "aristas") else "")
            ejemplos_algoritmo(g, r)
            despues = (repr(r.snapshots), r.caminos, r.distancia, repr(g.aristas()) if hasattr(g, "aristas") else "")
            self.assertEqual(antes, despues)

    def test_la_seleccion_nombra_un_candidato_real_de_menor_distancia(self):
        g = Grafo(7)
        for u, v, p in [("A", "B", 5), ("A", "C", 2), ("C", "D", 1), ("B", "D", 1)]:
            g.agregar_arista(u, v, p)
        r = ejecutar_dijkstra(g, "A", "D")
        texto = ejemplos_algoritmo(g, r).seleccion
        self.assertIn("Candidatos con su distancia: C (2), B (5)", texto)
        self.assertIn("Elige C", texto)


if __name__ == "__main__":
    unittest.main()
