"""Las explicaciones se derivan del estado real de los snapshots: nada inventado."""

import random
import unittest

from core.dijkstra_engine import (
    ACTUALIZACION, FINAL, INFINITO, INICIO, SELECCION, ejecutar_dijkstra, formato_distancia,
)
from core.explicaciones import Explicacion, explicar
from core.generator import generar_dag, generar_dag_didactico
from core.graph import Grafo


def construir(n, aristas):
    g = Grafo(n)
    for u, v, p in aristas:
        g.agregar_arista(u, v, p)
    return g


def texto(bloques):
    return Explicacion.texto_plano(bloques)


def casos():
    """Grafos variados: aleatorios, con empates, mejoras, descartes e inalcanzables."""
    azar = random.Random(7)
    for n in (7, 8, 10, 12, 16):
        for _ in range(4):
            g, o, d = generar_dag(n, rng=azar)
            yield g, o, d
    g, o, d = generar_dag_didactico(9)
    yield g, o, d
    yield construir(7, [("A", "B", 10), ("A", "C", 2), ("C", "B", 3)]), "A", "B"            # mejora con reemplazo
    yield construir(7, [("A", "B", 2), ("A", "C", 2), ("B", "D", 3), ("C", "D", 3)]), "A", "D"  # empate
    yield construir(7, [("A", "B", 1), ("A", "C", 1), ("B", "D", 1), ("C", "D", 8)]), "A", "D"  # descarte
    yield construir(7, [("A", "B", 1), ("C", "D", 2)]), "A", "D"                              # inalcanzable
    yield construir(7, [("A", "B", 1), ("B", "C", 1)]), "A", "A"                              # origen = destino
    yield construir(7, [("A", "B", 1), ("A", "C", 1), ("B", "D", 1), ("C", "D", 1)]), "A", "D"


class TestExplicacionesCoherentesConElEstado(unittest.TestCase):
    def test_todos_los_pasos_tienen_explicacion_breve_y_detallada(self):
        for g, o, d in casos():
            r = ejecutar_dijkstra(g, o, d)
            for i, s in enumerate(r.snapshots):
                e = explicar(g, r, i)
                self.assertEqual(e.titulo, s.titulo)
                self.assertTrue(e.breve and e.detalle, (i, s.subpaso))
                self.assertGreater(len(texto(e.detalle)), len(texto(e.breve)) * 0.8)

    def test_los_calculos_coinciden_con_pesos_y_distancias_del_snapshot(self):
        revisadas = 0
        for g, o, d in casos():
            r = ejecutar_dijkstra(g, o, d)
            for i, s in enumerate(r.snapshots):
                if s.subpaso != ACTUALIZACION:
                    continue
                e = explicar(g, r, i)
                u = s.seleccionado
                for a, v, tipo in s.aristas_evaluadas:
                    esperado = (f"{a} → {v}: {formato_distancia(s.distancias[u])} + {g.peso(a, v)} = "
                                f"{formato_distancia(s.distancias[u] + g.peso(a, v))}")
                    self.assertIn(esperado, texto(e.breve))
                    self.assertIn(esperado, texto(e.detalle))
                    revisadas += 1
        self.assertGreater(revisadas, 50)

    def test_cada_tipo_de_arista_se_explica_segun_lo_que_ocurrio(self):
        vistos = set()
        for g, o, d in casos():
            r = ejecutar_dijkstra(g, o, d)
            for i, s in enumerate(r.snapshots):
                if s.subpaso != ACTUALIZACION:
                    continue
                previo = r.snapshots[i - 1]
                e = explicar(g, r, i)
                for u, v, tipo in s.aristas_evaluadas:
                    nueva = s.distancias[u] + g.peso(u, v)
                    antes = previo.distancias[v]
                    if tipo == "mejora" and antes == INFINITO:
                        self.assertIn(f"{v} no tenía distancia (∞)", texto(e.breve))
                    elif tipo == "mejora":
                        self.assertLess(nueva, antes)
                        vieja = next(t for vert, t in s.etiquetas_descartadas if vert == v)
                        self.assertIn(f"se reemplaza {vieja} por {s.etiqueta(v)}", texto(e.breve))
                        self.assertIn("se descarta", texto(e.detalle))
                    elif tipo == "empate":
                        self.assertEqual(nueva, antes)
                        self.assertIn("empate", texto(e.breve))
                        self.assertIn("predecesor", texto(e.detalle))
                    else:
                        self.assertGreater(nueva, antes)
                        self.assertIn(f"se conserva la etiqueta actual de {v}", texto(e.breve))
                    vistos.add((tipo, antes == INFINITO))
        self.assertEqual(vistos, {("mejora", True), ("mejora", False), ("empate", False), ("descartada", False)})

    def test_la_seleccion_nombra_el_vertice_del_snapshot_y_sus_candidatos(self):
        for g, o, d in casos():
            r = ejecutar_dijkstra(g, o, d)
            for i, s in enumerate(r.snapshots):
                if s.subpaso != SELECCION:
                    continue
                previo = r.snapshots[i - 1]
                e = explicar(g, r, i)
                u = s.seleccionado
                candidatos = sorted(
                    (v for v in g.vertices if v not in previo.visitados and previo.distancias[v] != INFINITO),
                    key=lambda v: (previo.distancias[v], v))
                self.assertEqual(candidatos[0], u)
                self.assertIn(f"Elige {u}", texto(e.breve))
                self.assertIn(", ".join(f"{v} ({formato_distancia(previo.distancias[v])})" for v in candidatos),
                              texto(e.breve))
                for otro in g.vertices:  # ningún otro vértice aparece como elegido
                    if otro != u:
                        self.assertNotIn(f"Elige {otro}", texto(e.breve))

    def test_los_empates_de_seleccion_se_mencionan_solo_si_existen(self):
        g = construir(7, [("A", "B", 2), ("A", "C", 2), ("B", "D", 3), ("C", "D", 3)])
        r = ejecutar_dijkstra(g, "A", "D")
        sel = [i for i, s in enumerate(r.snapshots) if s.subpaso == SELECCION]
        con_empate = [i for i in sel if "Empata con" in texto(explicar(g, r, i).breve)]
        self.assertEqual(len(con_empate), 1)  # B y C empatan con distancia 2 una única vez
        self.assertIn("C", texto(explicar(g, r, con_empate[0]).breve))

    def test_el_resultado_final_suma_los_pesos_de_cada_camino(self):
        for g, o, d in casos():
            r = ejecutar_dijkstra(g, o, d)
            e = explicar(g, r, len(r.snapshots) - 1)
            detalle = texto(e.detalle)
            if r.origen == r.destino:
                self.assertIn("a la vez origen y destino", texto(e.detalle))
            elif not r.alcanzable:
                self.assertIn("nunca recibió una etiqueta", texto(e.breve))
            else:
                for camino in r.caminos:
                    pesos = [g.peso(a, b) for a, b in zip(camino, camino[1:])]
                    self.assertEqual(sum(pesos), r.distancia)
                    self.assertIn(" → ".join(camino) + "   =   " + " + ".join(map(str, pesos))
                                  + f" = {formato_distancia(r.distancia)}", detalle)
                self.assertIn(f"{r.cantidad_caminos} caminos" if r.cantidad_caminos > 1 else "único", detalle + texto(e.breve))

    def test_el_detalle_incluye_la_tabla_de_estado_real(self):
        g, o, d = generar_dag_didactico(9)
        r = ejecutar_dijkstra(g, o, d)
        for i, s in enumerate(r.snapshots):
            filas = [b.texto for b in explicar(g, r, i).detalle if b.estilo == "tabla"][1:]  # sin cabecera
            self.assertEqual(len(filas), len(g.vertices))
            for v, fila in zip(g.vertices, filas):
                self.assertTrue(fila.startswith(v))
                self.assertIn(formato_distancia(s.distancias[v]), fila.split()[1:2])
                estado = "visitado" if v in s.visitados else ("sin alcanzar" if s.distancias[v] == INFINITO else "pendiente")
                self.assertTrue(fila.endswith(estado), (v, fila))

    def test_explicar_no_modifica_los_resultados_del_algoritmo(self):
        g, o, d = generar_dag_didactico(10)
        r = ejecutar_dijkstra(g, o, d)
        antes = (r.distancia, r.caminos, dict(r.predecesores), r.snapshots)
        for i in range(len(r.snapshots)):
            explicar(g, r, i)
        despues = (r.distancia, r.caminos, dict(r.predecesores), r.snapshots)
        self.assertEqual(antes, despues)
        # y el algoritmo sigue dando el mismo resultado al ejecutarlo de nuevo
        self.assertEqual(ejecutar_dijkstra(g, o, d).caminos, r.caminos)

    def test_las_explicaciones_principales_no_tienen_apartado_de_observacion(self):
        for g, o, d in casos():
            r = ejecutar_dijkstra(g, o, d)
            for i in range(len(r.snapshots)):
                e = explicar(g, r, i)
                self.assertNotIn("observar", texto(e.breve).lower(), (o, d, i))
                self.assertNotIn("observar", texto(e.detalle).lower(), (o, d, i))

    def test_inicio_describe_el_origen(self):
        g = construir(7, [("A", "B", 1)])
        r = ejecutar_dijkstra(g, "A", "B")
        e = explicar(g, r, 0)
        self.assertIn("[0, -]₀", texto(e.breve))
        self.assertEqual(r.snapshots[0].subpaso, INICIO)
        self.assertEqual(r.snapshots[-1].subpaso, FINAL)


if __name__ == "__main__":
    unittest.main()
