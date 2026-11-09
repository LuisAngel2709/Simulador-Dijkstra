"""Casos de oro: golden/dijkstra_golden.json debe coincidir con lo que produce el motor actual."""

import json
import tempfile
import unittest
from pathlib import Path

from core import golden
from core.dijkstra_engine import FINAL, INICIO, reconstruir_caminos
from core.graph import GrafoError, validar_numero_nodos, validar_peso

RUTA = golden.RUTA_POR_DEFECTO


def cargar() -> dict:
    with open(RUTA, encoding="utf-8") as f:
        return json.load(f)


class TestArchivoGolden(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datos = cargar()

    def test_estructura_y_metadatos(self):
        d = self.datos
        self.assertEqual(set(d), {"meta", "casos", "validacion", "truncamiento"})
        self.assertEqual(d["meta"]["formato"], golden.FORMATO)
        self.assertEqual(d["meta"]["cantidad_casos"], len(d["casos"]))
        self.assertEqual(d["meta"]["constantes"]["LIMITE_CAMINOS"], 500)
        nombres = [c["nombre"] for c in d["casos"]]
        self.assertEqual(len(nombres), len(set(nombres)), "nombres de caso repetidos")

    def test_cada_caso_se_reproduce_exactamente_con_el_motor_actual(self):
        for caso in self.datos["casos"]:
            with self.subTest(caso=caso["nombre"]):
                self.assertEqual(golden.reproducir_caso(caso), caso)

    def test_los_casos_manuales_se_regeneran_identicos(self):
        # Los grafos manuales son deterministas; los aleatorios viven en el archivo y no se regeneran
        # (random.Random puede variar entre versiones de Python).
        guardados = {c["nombre"]: c for c in self.datos["casos"]}
        for nombre, g, o, d in golden.casos_manuales():
            with self.subTest(caso=nombre):
                nuevo = json.loads(json.dumps(golden.serializar_caso(nombre, g, o, d)))
                self.assertEqual(nuevo, guardados[nombre])

    def test_la_validacion_guardada_coincide_con_las_funciones_actuales(self):
        funciones = {"validar_peso": validar_peso, "validar_numero_nodos": validar_numero_nodos}
        self.assertGreater(len(self.datos["validacion"]), 30)
        for caso in self.datos["validacion"]:
            try:
                valor, error = funciones[caso["funcion"]](caso["entrada"]), None
            except GrafoError as e:
                valor, error = None, str(e)
            self.assertEqual((valor, error), (caso["valor"], caso["error"]), caso)

    def test_la_validacion_guardada_es_estricta(self):
        por_entrada = {(c["funcion"], c["entrada"]): c for c in self.datos["validacion"]}
        for raro in ("+5", "1_0", "٣", "５"):
            self.assertIsNone(por_entrada[("validar_peso", raro)]["valor"], raro)
        self.assertEqual(por_entrada[("validar_peso", "99")]["valor"], 99)
        self.assertEqual(por_entrada[("validar_numero_nodos", "16")]["valor"], 16)

    def test_el_truncamiento_guardado_coincide_y_cubre_499_500_501(self):
        self.assertTrue(self.datos["truncamiento"])
        resumen = {c["nombre"]: (c["cantidad"], c["truncado"]) for c in self.datos["truncamiento"]}
        self.assertEqual(resumen["499_caminos_limite_500"], (499, False))
        self.assertEqual(resumen["500_caminos_limite_500"], (500, False))
        self.assertEqual(resumen["501_caminos_limite_500"], (500, True))
        for c in self.datos["truncamiento"]:
            caminos, truncado = reconstruir_caminos(
                {v: tuple(p) for v, p in c["predecesores"].items()}, c["origen"], c["destino"], c["limite"])
            self.assertEqual((len(caminos), truncado), (c["cantidad"], c["truncado"]), c["nombre"])
            self.assertEqual((list(caminos[0]), list(caminos[-1])), (c["primero"], c["ultimo"]), c["nombre"])

    def test_el_archivo_se_puede_regenerar_y_es_json_valido(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = golden.escribir_golden(Path(tmp) / "g.json")
            with open(ruta, encoding="utf-8") as f:
                nuevo = json.load(f)
        self.assertEqual(nuevo["meta"], self.datos["meta"])
        self.assertEqual(len(nuevo["casos"]), len(self.datos["casos"]))
        self.assertEqual(nuevo["validacion"], self.datos["validacion"])
        self.assertEqual(nuevo["truncamiento"], self.datos["truncamiento"])


class TestContenidoDelGolden(unittest.TestCase):
    """Comprobaciones independientes del motor sobre el propio JSON (no dependen de reproducirlo)."""

    @classmethod
    def setUpClass(cls):
        cls.casos = cargar()["casos"]

    def test_cubre_los_casos_importantes(self):
        c = self.casos
        self.assertTrue(any(x["origen"] == x["destino"] for x in c))
        self.assertTrue(any(not x["resultado"]["alcanzable"] for x in c))
        self.assertTrue(any(x["resultado"]["cantidad_caminos"] >= 2 for x in c))
        self.assertTrue(any(x["grafo"]["n"] == 16 for x in c))
        self.assertTrue(any(x["grafo"]["n"] == 7 for x in c))
        self.assertTrue(any(x["resultado"]["cantidad_caminos"] == 32 for x in c))
        self.assertTrue(any(x["extremos"]["analisis"]["mensaje"] for x in c))
        self.assertTrue(any(not x["extremos"]["analisis"]["hay_advertencias"] for x in c))

    def test_los_caminos_son_validos_y_suman_la_distancia(self):
        for x in self.casos:
            pesos = {(u, v): p for u, v, p in x["grafo"]["aristas"]}
            r = x["resultado"]
            self.assertEqual(len(r["caminos"]), r["cantidad_caminos"], x["nombre"])
            self.assertEqual(r["alcanzable"], r["distancia"] is not None, x["nombre"])
            self.assertFalse(r["truncado"], x["nombre"])
            for camino in r["caminos"]:
                self.assertEqual((camino[0], camino[-1]), (x["origen"], x["destino"]), x["nombre"])
                self.assertEqual(sum(pesos[a, b] for a, b in zip(camino, camino[1:])), r["distancia"], x["nombre"])

    def test_la_secuencia_de_snapshots_es_coherente(self):
        for x in self.casos:
            s = x["snapshots"]
            self.assertEqual([p["indice"] for p in s], list(range(len(s))), x["nombre"])
            self.assertEqual((s[0]["subpaso"], s[-1]["subpaso"]), (INICIO, FINAL), x["nombre"])
            self.assertEqual([p["es_final"] for p in s], [False] * (len(s) - 1) + [True], x["nombre"])
            self.assertEqual(s[-1]["distancia_destino"], x["resultado"]["distancia"], x["nombre"])
            if x["origen"] == x["destino"]:
                self.assertEqual(len(s), 2, x["nombre"])
            for p in s:
                self.assertTrue(p["explicacion"]["breve"], (x["nombre"], p["indice"]))
                self.assertTrue(p["explicacion"]["titulo"], (x["nombre"], p["indice"]))

    def test_infinito_se_escribe_como_null(self):
        x = next(c for c in self.casos if not c["resultado"]["alcanzable"])
        self.assertIsNone(x["resultado"]["distancia"])
        self.assertIsNone(x["snapshots"][0]["distancias"][x["destino"]])
        self.assertEqual(x["snapshots"][0]["etiquetas"][x["destino"]], "[∞, -]")


if __name__ == "__main__":
    unittest.main()
