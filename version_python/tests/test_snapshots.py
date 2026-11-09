import random
import unittest

from core.dijkstra_engine import (
    ACTUALIZACION,
    FINAL,
    INICIO,
    SELECCION,
    Simulacion,
    ejecutar_dijkstra,
)
from core.generator import generar_dag, generar_dag_didactico, pesos_validos
from core.graph import NODOS_MAXIMO, NODOS_MINIMO, Grafo


def grafo_demo():
    g = Grafo(8)
    for u, v, p in [
        ("A", "B", 3), ("A", "C", 1), ("B", "D", 1), ("B", "G", 5),
        ("C", "D", 2), ("C", "F", 5), ("D", "E", 4), ("D", "F", 2),
        ("E", "G", 2), ("E", "H", 1), ("F", "H", 3),
    ]:
        g.agregar_arista(u, v, p)
    return g


class TestSnapshots(unittest.TestCase):
    def setUp(self):
        self.resultado = ejecutar_dijkstra(grafo_demo(), "A", "H")
        self.sim = Simulacion(self.resultado)

    def test_secuencia_de_subpasos(self):
        subpasos = [s.subpaso for s in self.resultado.snapshots]
        self.assertEqual(subpasos[0], INICIO)
        self.assertEqual(subpasos[-1], FINAL)
        self.assertEqual(subpasos[1], SELECCION)
        self.assertEqual(subpasos[2], ACTUALIZACION)

    def test_avanzar_y_retroceder(self):
        self.assertFalse(self.sim.puede_retroceder)
        primero = self.sim.actual
        self.sim.siguiente()
        self.sim.siguiente()
        tercero = self.sim.actual
        self.assertEqual(tercero.indice, 2)
        self.sim.anterior()
        self.sim.anterior()
        self.assertIs(self.sim.actual, primero)
        self.assertFalse(self.sim.puede_retroceder)

    def test_finalizar_y_reiniciar(self):
        final = self.sim.finalizar()
        self.assertTrue(final.es_final)
        self.assertFalse(self.sim.puede_avanzar)
        self.assertIs(self.sim.reiniciar(), self.sim.snapshots[0])

    def test_un_snapshot_anterior_no_se_modifica(self):
        primero = self.resultado.snapshots[0]
        ultimo = self.resultado.snapshots[-1]
        self.assertEqual(primero.distancias["H"], float("inf"))
        self.assertEqual(ultimo.distancias["H"], 8)
        with self.assertRaises(TypeError):
            primero.distancias["H"] = 0  # las distancias son de solo lectura
        with self.assertRaises(Exception):
            primero.visitados.add("Z")

    def test_los_snapshots_conservan_la_tabla_del_proceso(self):
        ultimo = self.resultado.snapshots[-1]
        etiquetas_f = [e for e in ultimo.tabla if e.vertice == "F"]
        # F recibe [6, C] y luego [5, D]: la peor queda descartada.
        self.assertEqual(len(etiquetas_f), 2)
        self.assertEqual([e.estado for e in etiquetas_f], ["descartada", "vigente"])

    def test_la_tabla_registra_el_empate_del_destino(self):
        ultimo = self.resultado.snapshots[-1]
        etiquetas_h = [e for e in ultimo.tabla if e.vertice == "H"]
        self.assertEqual(len(etiquetas_h), 2)
        self.assertTrue(all(e.estado == "empate" for e in etiquetas_h))


class TestGenerador(unittest.TestCase):
    def test_genera_dag_valido_en_todo_el_rango(self):
        azar = random.Random(7)
        for n in range(NODOS_MINIMO, NODOS_MAXIMO + 1):
            grafo, origen, destino = generar_dag(n, rng=azar)
            self.assertEqual(grafo.n, n)
            self.assertTrue(grafo.es_dag())
            self.assertTrue(pesos_validos(grafo))
            self.assertTrue(grafo.hay_camino(origen, destino))

    def test_todos_los_vertices_son_alcanzables_desde_el_origen(self):
        azar = random.Random(13)
        grafo, origen, destino = generar_dag(12, rng=azar)
        for v in grafo.vertices:
            self.assertTrue(grafo.hay_camino(origen, v))
            self.assertTrue(grafo.hay_camino(v, destino))

    def test_generacion_didactica_produce_grafo_valido(self):
        grafo, origen, destino = generar_dag_didactico(9, rng=random.Random(3))
        self.assertTrue(grafo.es_dag())
        resultado = ejecutar_dijkstra(grafo, origen, destino)
        self.assertTrue(resultado.alcanzable)


if __name__ == "__main__":
    unittest.main()
