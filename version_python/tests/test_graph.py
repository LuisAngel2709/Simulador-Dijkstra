import unittest

from core.graph import Grafo, GrafoError, validar_numero_nodos, validar_peso


class TestCreacionGrafo(unittest.TestCase):
    def test_vertices_con_letras(self):
        g = Grafo(8)
        self.assertEqual(g.vertices, list("ABCDEFGH"))
        self.assertEqual(g.cantidad_aristas(), 0)

    def test_validar_numero_nodos(self):
        self.assertEqual(validar_numero_nodos("7"), 7)
        self.assertEqual(validar_numero_nodos(16), 16)
        for invalido in ["6", "17", "", "abc", "7.5", "+7", "1_0", "٧", "１０", " ٨ "]:
            with self.assertRaises(GrafoError):
                validar_numero_nodos(invalido)


class TestAristasDirigidas(unittest.TestCase):
    def setUp(self):
        self.g = Grafo(7)

    def test_la_arista_conserva_direccion(self):
        self.g.agregar_arista("A", "C", 5)
        self.assertTrue(self.g.existe_arista("A", "C"))
        self.assertFalse(self.g.existe_arista("C", "A"))
        self.assertEqual(self.g.peso("A", "C"), 5)

    def test_arista_duplicada(self):
        self.g.agregar_arista("A", "B", 3)
        with self.assertRaises(GrafoError):
            self.g.agregar_arista("A", "B", 4)

    def test_modificar_y_eliminar(self):
        self.g.agregar_arista("A", "B", 3)
        self.g.modificar_peso("A", "B", 9)
        self.assertEqual(self.g.peso("A", "B"), 9)
        self.g.eliminar_arista("A", "B")
        self.assertFalse(self.g.existe_arista("A", "B"))
        with self.assertRaises(GrafoError):
            self.g.eliminar_arista("A", "B")

    def test_vertice_inexistente(self):
        with self.assertRaises(GrafoError):
            self.g.agregar_arista("A", "Z", 2)


class TestPesos(unittest.TestCase):
    def test_pesos_validos(self):
        self.assertEqual(validar_peso("1"), 1)
        self.assertEqual(validar_peso(99), 99)

    def test_pesos_invalidos(self):
        for invalido in ["0", "-3", "", "   ", "cinco", "100", "2.5", "+5", "1_0", "٣", "５", "1 0", "0x10", "1e1"]:
            with self.assertRaises(GrafoError):
                validar_peso(invalido)

    def test_peso_invalido_no_modifica_el_grafo(self):
        g = Grafo(7)
        with self.assertRaises(GrafoError):
            g.agregar_arista("A", "B", 0)
        self.assertEqual(g.cantidad_aristas(), 0)


class TestCiclos(unittest.TestCase):
    def setUp(self):
        self.g = Grafo(7)
        self.g.agregar_arista("A", "B", 1)
        self.g.agregar_arista("B", "C", 1)

    def test_rechaza_ciclo_directo(self):
        with self.assertRaises(GrafoError):
            self.g.agregar_arista("B", "A", 1)

    def test_rechaza_ciclo_indirecto(self):
        with self.assertRaises(GrafoError):
            self.g.agregar_arista("C", "A", 1)

    def test_rechaza_bucle(self):
        with self.assertRaises(GrafoError):
            self.g.agregar_arista("A", "A", 1)

    def test_el_grafo_anterior_se_conserva(self):
        aristas = self.g.aristas()
        with self.assertRaises(GrafoError):
            self.g.agregar_arista("C", "A", 1)
        self.assertEqual(self.g.aristas(), aristas)
        self.assertTrue(self.g.es_dag())

    def test_arista_valida_entre_ramas_no_es_ciclo(self):
        self.g.agregar_arista("A", "C", 7)  # A → C ya existe por camino, no es ciclo
        self.assertTrue(self.g.es_dag())

    def test_orden_topologico_completo(self):
        orden = self.g.orden_topologico()
        self.assertEqual(len(orden), self.g.n)
        self.assertLess(orden.index("A"), orden.index("B"))
        self.assertLess(orden.index("B"), orden.index("C"))

    def test_copiar_es_independiente(self):
        copia = self.g.copiar()
        copia.agregar_arista("C", "D", 2)
        self.assertFalse(self.g.existe_arista("C", "D"))


if __name__ == "__main__":
    unittest.main()
