"""Origen = destino: Dijkstra termina de inmediato, sin iteraciones innecesarias."""

import random
import unittest

from core.dijkstra_engine import (FINAL, INICIO, INFINITO, SELECCION, ACTUALIZACION,
                                  ejecutar_dijkstra, MotorDijkstra)
from core.explicaciones import explicar
from core.generator import generar_dag
from core.graph import Grafo
from core.tutorial_algoritmo import ejemplos_algoritmo

try:
    import customtkinter as ctk
    from ui.app import App
    HAY_UI = True
except Exception:  # pragma: no cover
    HAY_UI = False


def grafo_ejemplo() -> Grafo:
    g = Grafo(7)
    for u, v, p in [("A", "B", 2), ("A", "C", 4), ("B", "D", 1), ("C", "D", 3), ("D", "E", 2),
                    ("E", "F", 1), ("F", "G", 5)]:
        g.agregar_arista(u, v, p)
    return g


def texto(expl):
    return " ".join(b.texto for b in (*expl.breve, *expl.detalle))


class TestMotorOrigenIgualDestino(unittest.TestCase):
    def test_solo_hay_inicio_y_final_sin_selecciones_ni_actualizaciones(self):
        for v in "ABCDEFG":
            r = ejecutar_dijkstra(grafo_ejemplo(), v, v)
            self.assertEqual([s.subpaso for s in r.snapshots], [INICIO, FINAL], v)
            self.assertEqual(r.snapshots[-1].iteracion, 0)
            for s in r.snapshots:
                self.assertIsNone(s.seleccionado)
                self.assertEqual(s.aristas_evaluadas, ())

    def test_distancia_cero_y_camino_con_un_unico_vertice(self):
        r = ejecutar_dijkstra(grafo_ejemplo(), "C", "C")
        self.assertEqual(r.distancia, 0)
        self.assertTrue(r.alcanzable)
        self.assertEqual(r.caminos, (("C",),))
        self.assertEqual(r.cantidad_caminos, 1)
        self.assertEqual(r.snapshots[-1].aristas_camino, ())

    def test_ningun_otro_vertice_recibe_etiqueta_ni_se_visita(self):
        r = ejecutar_dijkstra(grafo_ejemplo(), "A", "A")
        self.assertEqual(r.distancias["A"], 0)
        for v in "BCDEFG":
            self.assertEqual(r.distancias[v], INFINITO)
            self.assertEqual(r.predecesores[v], ())
        self.assertEqual([e.vertice for e in r.snapshots[-1].tabla], ["A"])

    def test_vertice_aislado_como_origen_y_destino(self):
        g = Grafo(7)
        g.agregar_arista("A", "B", 1)
        r = ejecutar_dijkstra(g, "G", "G")
        self.assertEqual((r.distancia, r.caminos), (0, (("G",),)))
        self.assertEqual(len(r.snapshots), 2)

    def test_se_explica_la_coincidencia_en_inicio_y_final(self):
        g = grafo_ejemplo()
        r = ejecutar_dijkstra(g, "B", "B")
        self.assertIn("coinciden", texto(explicar(g, r, 0)))
        self.assertIn("coinciden", texto(explicar(g, r, 1)))
        self.assertIn("distancia mínima es 0", texto(explicar(g, r, 1)))

    def test_con_destino_distinto_el_comportamiento_no_cambia(self):
        r = ejecutar_dijkstra(grafo_ejemplo(), "A", "G")
        self.assertEqual(r.distancia, 11)
        self.assertEqual(r.caminos, (("A", "B", "D", "E", "F", "G"),))
        tipos = [s.subpaso for s in r.snapshots]
        self.assertEqual(tipos[0], INICIO)
        self.assertEqual(tipos[-1], FINAL)
        self.assertEqual(tipos.count(SELECCION), 7)
        self.assertEqual(tipos.count(ACTUALIZACION), 7)

    def test_destino_inalcanzable_sigue_recorriendo_lo_alcanzable(self):
        r = ejecutar_dijkstra(grafo_ejemplo(), "C", "B")
        self.assertFalse(r.alcanzable)
        self.assertGreater(len(r.snapshots), 2)

    def test_misma_cantidad_de_pasos_en_grafos_aleatorios_con_destino_distinto(self):
        azar = random.Random(11)
        for n in range(7, 17):
            g, o, d = generar_dag(n, rng=azar)
            if o == d:  # pragma: no cover
                continue
            r = ejecutar_dijkstra(g, o, d)
            self.assertTrue(r.alcanzable)
            self.assertGreater(len(r.snapshots), 2)
            # cualquier otro vértice como origen=destino sigue dando 2 snapshots
            self.assertEqual(len(ejecutar_dijkstra(g, o, o).snapshots), 2)


class TestExplicacionesOrigenIgualDestino(unittest.TestCase):
    def setUp(self):
        self.g = grafo_ejemplo()
        self.r = ejecutar_dijkstra(self.g, "A", "A")

    def test_explicacion_inicial_y_final_indican_que_coinciden(self):
        for i in (0, 1):
            e = explicar(self.g, self.r, i)
            t = texto(e)
            self.assertIn("Origen y destino coinciden", t)
            self.assertIn("distancia", t)
            self.assertTrue(any(b.texto == "Origen y destino coinciden" for b in e.breve), i)

    def test_no_se_promete_una_fase_de_selecciones_que_no_ocurre(self):
        e = explicar(self.g, self.r, 0)
        self.assertNotIn("Qué vendrá después", texto(e))
        self.assertNotIn("Candidatos", texto(e))

    def test_el_final_no_dice_que_se_procesaron_otros_vertices(self):
        t = texto(explicar(self.g, self.r, 1))
        self.assertNotIn("procesó los vértices", t)
        self.assertIn("no se recorrió ninguna arista", t)

    def test_ejemplos_del_tutorial_funcionan_sin_selecciones(self):
        ej = ejemplos_algoritmo(self.g, self.r)
        for campo in (ej.provisionales, ej.seleccion, ej.actualizacion, ej.camino):
            self.assertIn("coinciden", campo)
        self.assertTrue(ej.empates)


@unittest.skipUnless(HAY_UI, "Requiere CustomTkinter")
class TestUIOrigenIgualDestino(unittest.TestCase):
    def setUp(self):
        try:
            self.app = App()
        except Exception as error:  # sin display
            self.skipTest(str(error))
        self.app.geometry("1320x860+0+0")
        self.app.mostrar_simulacion(grafo_ejemplo(), origen="A", destino="G")
        self.app.update()
        self.sim = self.app.pantalla

    def tearDown(self):
        self.app.destroy()

    def elegir(self, o, d):
        self.sim.menu_origen.set(o)
        self.sim.menu_destino.set(d)
        self.sim._al_elegir_extremo()
        self.app.update()

    def resultado_texto(self):
        return self.sim.texto_resultado.get("1.0", "end")

    def test_la_simulacion_tiene_dos_pasos_y_se_puede_recorrer(self):
        self.elegir("D", "D")
        self.sim._ejecutar()
        self.app.update()
        self.assertEqual(len(self.sim.simulacion.resultado.snapshots), 2)
        self.assertFalse(self.sim.simulacion.puede_retroceder)
        self.assertTrue(self.sim.simulacion.puede_avanzar)
        self.sim._siguiente()
        self.app.update()
        self.assertFalse(self.sim.simulacion.puede_avanzar)
        self.sim._anterior()
        self.app.update()
        self.assertFalse(self.sim.simulacion.puede_retroceder)

    def test_al_finalizar_muestra_distancia_0_y_solo_el_vertice(self):
        self.elegir("D", "D")
        self.sim._ejecutar()
        self.sim._finalizar()
        self.app.update()
        lineas = [l for l in self.resultado_texto().splitlines() if l.strip()]
        self.assertEqual(lineas[0], "Distancia mínima: 0")
        self.assertEqual(lineas[1], "Caminos mínimos encontrados: 1")
        self.assertEqual(lineas[2], "D")
        self.assertIn("a la vez origen y destino", lineas[3])
        self.assertNotIn("→", self.resultado_texto())
        self.assertEqual(self.sim.canvas.destino, "D")

    def test_la_tabla_solo_tiene_la_iteracion_0(self):
        self.elegir("D", "D")
        self.sim._ejecutar()
        self.sim._finalizar()
        self.app.update()
        self.assertEqual(self.sim.tabla._iteraciones, [0])
        self.elegir("A", "G")
        self.sim._ejecutar()
        self.assertEqual(self.sim.tabla._iteraciones, list(range(8)))

    def test_el_panel_de_explicacion_menciona_la_coincidencia(self):
        self.elegir("D", "D")
        self.sim._ejecutar()
        self.app.update()
        self.assertIn("coinciden", self._explicacion())
        self.sim._finalizar()
        self.app.update()
        self.assertIn("coinciden", self._explicacion())

    def _explicacion(self):
        for nombre in ("texto_explicacion", "caja_explicacion"):
            caja = getattr(self.sim, nombre, None)
            if caja is not None:
                return caja.get("1.0", "end")
        self.fail("no se encontró el panel de explicación")

    def test_volver_a_un_destino_distinto_restaura_la_simulacion_completa(self):
        self.elegir("A", "A")
        self.sim._ejecutar()
        self.elegir("A", "G")
        self.sim._ejecutar()
        self.assertGreater(len(self.sim.simulacion.resultado.snapshots), 2)
        self.sim._finalizar()
        self.assertIn("A → B → D → E → F → G", self.resultado_texto())


if __name__ == "__main__":
    unittest.main()
