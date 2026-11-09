"""Validación estricta de números: solo dígitos ASCII (misma interpretación en Python y JavaScript)."""

import unittest

from core.graph import Grafo, GrafoError, validar_numero_nodos, validar_peso

# Entradas que Python (int) aceptaba pero que ya no deben aceptarse.
FORMATOS_RAROS = ["+5", "+16", "1_0", "1_000", "٣", "５", "１０", "٣٣", "²", "①", "1 0", "0x10", "0b11", "1e1",
                  "1.0", "10.", ".5", "--5", "-+5", "5-", " 5 ", "　5", "5 ", "5\x0b", "5\x0c",
                  "5\x00", "٧", "　７"]


class TestPesoEstricto(unittest.TestCase):
    def test_rango_actual_se_respeta(self):
        for n in range(1, 100):
            self.assertEqual(validar_peso(str(n)), n)
            self.assertEqual(validar_peso(n), n)
        for fuera in ("0", "100", "101", "999", "-1", "-99", "-0", "00"):
            with self.assertRaises(GrafoError, msg=fuera):
                validar_peso(fuera)

    def test_formatos_raros_se_rechazan(self):
        for raro in FORMATOS_RAROS:
            with self.assertRaises(GrafoError, msg=repr(raro)):
                validar_peso(raro)

    def test_mensajes_se_conservan(self):
        casos = {
            "": "Debe introducir un peso.",
            "   ": "Debe introducir un peso.",
            "abc": "El peso debe ser un número entero.",
            "+5": "El peso debe ser un número entero.",
            "٣": "El peso debe ser un número entero.",
            "2.5": "El peso debe ser un número entero.",
            "0": "El peso debe ser un entero positivo (no se admite 0 ni negativos).",
            "-3": "El peso debe ser un entero positivo (no se admite 0 ni negativos).",
            "100": "El peso debe estar entre 1 y 99.",
        }
        for texto, mensaje in casos.items():
            with self.assertRaises(GrafoError, msg=texto) as cm:
                validar_peso(texto)
            self.assertEqual(str(cm.exception), mensaje, texto)

    def test_espacios_alrededor_ascii_se_toleran(self):
        for texto in (" 5", "5 ", "  5  ", "\t5\n"):
            self.assertEqual(validar_peso(texto), 5, repr(texto))

    def test_ceros_a_la_izquierda_siguen_siendo_dígitos_ascii(self):
        self.assertEqual(validar_peso("007"), 7)
        self.assertEqual(validar_peso("099"), 99)

    def test_numeros_enormes_no_rompen(self):
        for texto in ("9" * 5000, "1" + "0" * 30, "-" + "9" * 5000):
            with self.assertRaises(GrafoError):
                validar_peso(texto)

    def test_agregar_y_modificar_aristas_usan_la_misma_regla(self):
        g = Grafo(7)
        for raro in ("+5", "1_0", "٣"):
            with self.assertRaises(GrafoError):
                g.agregar_arista("A", "B", raro)
        self.assertEqual(g.cantidad_aristas(), 0)
        g.agregar_arista("A", "B", "5")
        for raro in ("+6", "６"):
            with self.assertRaises(GrafoError):
                g.modificar_peso("A", "B", raro)
        self.assertEqual(g.peso("A", "B"), 5)


class TestNodosEstricto(unittest.TestCase):
    def test_rango_actual_se_respeta(self):
        for n in range(7, 17):
            self.assertEqual(validar_numero_nodos(str(n)), n)
            self.assertEqual(validar_numero_nodos(n), n)
        for fuera in ("0", "6", "17", "100", "-7"):
            with self.assertRaises(GrafoError, msg=fuera) as cm:
                validar_numero_nodos(fuera)
            self.assertEqual(str(cm.exception), "El número de nodos debe estar entre 7 y 16.")

    def test_formatos_raros_se_rechazan(self):
        for raro in FORMATOS_RAROS + ["+7", "1_0", "１０", "٨"]:
            with self.assertRaises(GrafoError, msg=repr(raro)):
                validar_numero_nodos(raro)

    def test_mensajes_se_conservan(self):
        with self.assertRaises(GrafoError) as cm:
            validar_numero_nodos("")
        self.assertEqual(str(cm.exception), "Debe introducir el número de nodos.")
        for texto in ("abc", "7.5", "+8", "٨"):
            with self.assertRaises(GrafoError) as cm:
                validar_numero_nodos(texto)
            self.assertEqual(str(cm.exception), "El número de nodos debe ser un número entero.")

    def test_numeros_enormes_no_rompen(self):
        with self.assertRaises(GrafoError):
            validar_numero_nodos("9" * 5000)


if __name__ == "__main__":
    unittest.main()
