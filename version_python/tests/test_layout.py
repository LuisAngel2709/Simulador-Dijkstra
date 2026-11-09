import random
import unittest

from core.generator import (
    MAX_ENTRANTES,
    MAX_SALIENTES,
    generar_dag,
    repartir_en_capas,
)
from core.graph import NODOS_MAXIMO, NODOS_MINIMO, Grafo

try:  # el layout vive en la UI y necesita Tkinter instalado
    from ui.graph_canvas import GrafoCanvas, _contar_cruces, calcular_capas, ordenar_por_capas
    HAY_UI = True
except Exception:  # pragma: no cover - entorno sin Tkinter
    HAY_UI = False


class TestGeneracionPorCapas(unittest.TestCase):
    def test_reparto_sin_capas_sueltas_de_un_vertice(self):
        azar = random.Random(2)
        for n in range(NODOS_MINIMO, NODOS_MAXIMO + 1):
            tamanos = repartir_en_capas(n, azar)
            self.assertEqual(sum(tamanos), n)
            self.assertEqual(tamanos[0], 1)
            self.assertEqual(tamanos[-1], 1)
            self.assertTrue(all(t >= 2 for t in tamanos[1:-1]))

    def test_las_aristas_no_saltan_mas_de_dos_capas(self):
        azar = random.Random(19)
        for n in range(NODOS_MINIMO, NODOS_MAXIMO + 1):
            grafo, _, _ = generar_dag(n, rng=azar)
            capas = self._capas_por_camino_mas_largo(grafo)
            for u, v, _ in grafo.aristas():
                salto = capas[v] - capas[u]
                self.assertGreaterEqual(salto, 1)
                self.assertLessEqual(salto, 2, f"{u} → {v} salta {salto} capas")

    def test_grados_acotados(self):
        azar = random.Random(23)
        # El límite solo se supera cuando la conectividad lo exige (capas de un
        # vértice seguidas de capas grandes), y nunca por más de un vecino.
        for n in range(NODOS_MINIMO, NODOS_MAXIMO + 1):
            grafo, _, _ = generar_dag(n, rng=azar)
            for v in grafo.vertices:
                self.assertLessEqual(len(grafo.salientes(v)), MAX_SALIENTES + 1)
                self.assertLessEqual(len(grafo.entrantes(v)), MAX_ENTRANTES + 1)

    def test_hay_variedad_entre_grafos(self):
        formas = set()
        for semilla in range(12):
            grafo, _, _ = generar_dag(10, rng=random.Random(semilla))
            formas.add(tuple(grafo.aristas()))
        self.assertGreaterEqual(len(formas), 10)

    def test_el_grafo_no_es_excesivamente_denso(self):
        azar = random.Random(31)
        for n in range(NODOS_MINIMO, NODOS_MAXIMO + 1):
            grafo, _, _ = generar_dag(n, rng=azar)
            self.assertGreaterEqual(grafo.cantidad_aristas(), n)
            self.assertLessEqual(grafo.cantidad_aristas(), 2.5 * n)

    @staticmethod
    def _capas_por_camino_mas_largo(grafo):
        capas = {v: 0 for v in grafo.vertices}
        for v in grafo.orden_topologico():
            for destino, _ in grafo.salientes(v):
                capas[destino] = max(capas[destino], capas[v] + 1)
        return capas


@unittest.skipUnless(HAY_UI, "Tkinter/CustomTkinter no disponible")
class TestLayout(unittest.TestCase):
    def _grafo_con_cruce(self):
        g = Grafo(7)
        for u, v, p in [
            ("A", "B", 1), ("A", "C", 1),
            ("B", "E", 1), ("C", "D", 1),
            ("D", "F", 1), ("E", "F", 1), ("F", "G", 1),
        ]:
            g.agregar_arista(u, v, p)
        return g

    def test_las_capas_respetan_la_direccion_de_las_aristas(self):
        grafo, _, _ = generar_dag(12, rng=random.Random(5))
        capas = calcular_capas(grafo)
        for u, v, _ in grafo.aristas():
            self.assertLess(capas[u], capas[v])

    def test_el_orden_es_determinista(self):
        grafo, _, _ = generar_dag(14, rng=random.Random(6))
        capas = calcular_capas(grafo)
        primero = ordenar_por_capas(grafo, capas)
        segundo = ordenar_por_capas(grafo, capas)
        self.assertEqual(primero, segundo)

    def test_el_orden_contiene_todos_los_vertices_una_sola_vez(self):
        grafo, _, _ = generar_dag(16, rng=random.Random(7))
        orden = ordenar_por_capas(grafo, calcular_capas(grafo))
        colocados = [v for vs in orden.values() for v in vs]
        self.assertCountEqual(colocados, grafo.vertices)

    def test_la_ordenacion_no_empeora_los_cruces(self):
        for semilla in range(8):
            grafo, _, _ = generar_dag(13, rng=random.Random(semilla))
            capas = calcular_capas(grafo)
            aristas = [(u, v) for u, v, _ in grafo.aristas()]

            alfabetico = {}
            for v in sorted(grafo.vertices):
                alfabetico.setdefault(capas[v], []).append(v)
            pos_inicial = {v: i for vs in alfabetico.values() for i, v in enumerate(vs)}

            ordenado = ordenar_por_capas(grafo, capas)
            pos_final = {v: i for vs in ordenado.values() for i, v in enumerate(vs)}

            self.assertLessEqual(
                _contar_cruces(aristas, capas, pos_final),
                _contar_cruces(aristas, capas, pos_inicial),
            )

    def test_reduce_el_cruce_de_un_caso_conocido(self):
        grafo = self._grafo_con_cruce()
        capas = calcular_capas(grafo)
        aristas = [(u, v) for u, v, _ in grafo.aristas()]
        orden = ordenar_por_capas(grafo, capas)
        posiciones = {v: i for vs in orden.values() for i, v in enumerate(vs)}
        self.assertEqual(_contar_cruces(aristas, capas, posiciones), 0)


def _hay_pantalla() -> bool:
    """True si Tkinter puede abrir una ventana (hay display disponible)."""
    if not HAY_UI:
        return False
    try:
        import customtkinter as ctk
        raiz = ctk.CTk()
    except Exception:
        return False
    raiz.destroy()
    return True


@unittest.skipUnless(_hay_pantalla(), "Requiere Tkinter y un display disponible")
class TestCanvasDragAndDrop(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        import customtkinter as ctk
        self.root = ctk.CTk()
        self.root.withdraw()
        self.canvas = GrafoCanvas(self.root)
        self.canvas.pack()
        self.root.update_idletasks()

    def tearDown(self):
        try:
            self.root.update_idletasks()
        except Exception:
            pass
        self.root.destroy()

    def test_distribucion_circular_inicial(self):
        grafo = Grafo(8)
        self.canvas.establecer_grafo(grafo, modo_layout="circular")
        pos = self.canvas.obtener_posiciones()

        # Cada vértice tiene una posición
        self.assertEqual(set(pos.keys()), set(grafo.vertices))
        # Las posiciones están normalizadas en [0, 1]
        for v, (rx, ry) in pos.items():
            self.assertGreaterEqual(rx, 0.0)
            self.assertLessEqual(rx, 1.0)
            self.assertGreaterEqual(ry, 0.0)
            self.assertLessEqual(ry, 1.0)

        # No hay vértices solapados
        vertices = list(pos.keys())
        for i in range(len(vertices)):
            for j in range(i + 1, len(vertices)):
                p1 = pos[vertices[i]]
                p2 = pos[vertices[j]]
                dist = ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
                self.assertGreater(dist, 0.1, "Los nodos no deben solaparse en círculo")

    def test_persistencia_posiciones_al_agregar_aristas(self):
        grafo = Grafo(8)
        self.canvas.establecer_grafo(grafo, modo_layout="circular")
        pos_iniciales = self.canvas.obtener_posiciones()

        # Simulamos que el usuario crea una arista en el editor
        grafo.agregar_arista("A", "B", 5)
        self.canvas.establecer_grafo(grafo)
        pos_tras_arista1 = self.canvas.obtener_posiciones()
        self.assertEqual(pos_iniciales, pos_tras_arista1, "Las posiciones no deben cambiar al agregar arista")

        # Agregamos otra arista
        grafo.agregar_arista("B", "C", 3)
        self.canvas.establecer_grafo(grafo)
        pos_tras_arista2 = self.canvas.obtener_posiciones()
        self.assertEqual(pos_iniciales, pos_tras_arista2)

    def test_persistencia_al_arrastrar_y_pasar_a_simulacion(self):
        grafo = Grafo(8)
        self.canvas.establecer_grafo(grafo, modo_layout="circular")

        # Simulamos mover el nodo A a una nueva posición personalizada
        self.canvas._posiciones_relativas["A"] = (0.2, 0.2)
        pos_modificada = self.canvas.obtener_posiciones()
        self.assertEqual(pos_modificada["A"], (0.2, 0.2))

        # Crear nuevo canvas (como en la pantalla de simulación) pasando las posiciones
        canvas_simulacion = GrafoCanvas(self.root)
        canvas_simulacion.establecer_grafo(grafo, posiciones=pos_modificada)
        pos_sim = canvas_simulacion.obtener_posiciones()
        self.assertEqual(pos_sim["A"], (0.2, 0.2))
        self.assertEqual(pos_sim, pos_modificada)
        canvas_simulacion.destroy()

    def test_arrastre_cerca_del_borde_no_salta(self):
        grafo = Grafo(5)
        self.canvas.establecer_grafo(grafo, modo_layout="circular")

        class EventoFicticio:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        self.canvas._vertice_arrastrado = "A"
        self.canvas._ha_arrastrado = True

        # Arrastramos a x=25, y=25 (el borde permitido)
        self.canvas._al_arrastrar(EventoFicticio(25, 25))
        pos_arrastre = self.canvas._posiciones["A"]
        self.assertEqual(pos_arrastre, (25.0, 25.0))

        # Soltamos el nodo: al redibujar no debe saltar a (78, 70)
        self.canvas._al_soltar(EventoFicticio(25, 25))
        pos_tras_soltar = self.canvas._posiciones["A"]
        self.assertAlmostEqual(pos_tras_soltar[0], 25.0, delta=1.0)
        self.assertAlmostEqual(pos_tras_soltar[1], 25.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()
