"""Navegación entre pantallas: "volver" desde la simulación no debe perder el grafo."""

import unittest

try:
    import customtkinter as ctk
    from ui.app import App
    from ui.editor import PantallaEditor
    from ui.app import PantallaConfiguracion
    from ui.simulation import PantallaSimulacion
    HAY_UI = True
except Exception:  # pragma: no cover - entorno sin Tkinter
    HAY_UI = False

ARISTAS = [("A", "B", 3), ("A", "C", 1), ("B", "D", 2), ("C", "D", 2)]


def _hay_pantalla() -> bool:
    if not HAY_UI:
        return False
    try:
        raiz = ctk.CTk()
    except Exception:
        return False
    raiz.destroy()
    return True


@unittest.skipUnless(_hay_pantalla(), "Requiere Tkinter y un display disponible")
class TestVolverDesdeSimulacion(unittest.TestCase):
    def setUp(self):
        self.app = App()
        self.app.withdraw()
        self.app.update()

    def tearDown(self):
        self.app.destroy()

    # ------------------------------------------------------------------ ayudas

    def _abrir_editor(self, n=7):
        self.app.mostrar_configuracion()
        self.app.update()
        self.app.pantalla.entrada_nodos.set(str(n))
        self.app.pantalla._manual()
        self.app.update()
        self.assertIsInstance(self.app.pantalla, PantallaEditor)
        return self.app.pantalla

    @staticmethod
    def _conectar(editor, u, v, peso):
        editor._al_hacer_clic_en_nodo(u)
        editor._al_hacer_clic_en_nodo(v)
        editor.entrada_peso.delete(0, "end")
        editor.entrada_peso.insert(0, str(peso))
        editor._crear_arista()

    def _finalizar(self, editor):
        """«Finalizar grafo»; estos grafos tienen vértices aislados, así que se acepta la advertencia."""
        editor._finalizar()
        self.app.update()
        if editor.dialogo_confirmacion is not None and editor.dialogo_confirmacion.winfo_exists():
            editor.dialogo_confirmacion._confirmar()
            self.app.update()

    def _editor_con_grafo(self):
        editor = self._abrir_editor()
        for u, v, p in ARISTAS:
            self._conectar(editor, u, v, p)
        return editor

    # ------------------------------------------------------------------- pruebas

    def test_flujo_manual_vuelve_al_editor_con_el_mismo_grafo(self):
        editor = self._editor_con_grafo()
        grafo = editor.grafo
        self._finalizar(editor)
        self.app.update()

        simulacion = self.app.pantalla
        self.assertIsInstance(simulacion, PantallaSimulacion)
        simulacion.boton_volver.invoke()
        self.app.update()

        self.assertIsInstance(self.app.pantalla, PantallaEditor)
        self.assertIs(self.app.pantalla.grafo, grafo)
        self.assertEqual(self.app.pantalla.grafo.aristas(), sorted(ARISTAS))

    def test_las_posiciones_movidas_en_la_simulacion_se_conservan(self):
        editor = self._editor_con_grafo()
        self._finalizar(editor)
        self.app.update()

        simulacion = self.app.pantalla
        simulacion.canvas._posiciones_relativas["A"] = (0.2, 0.3)
        esperadas = simulacion.canvas.obtener_posiciones()
        simulacion.boton_volver.invoke()
        self.app.update()

        self.assertEqual(self.app.pantalla.canvas.obtener_posiciones(), esperadas)
        self.assertEqual(self.app.pantalla.canvas.obtener_posiciones()["A"], (0.2, 0.3))

    def test_el_editor_restaurado_lista_las_aristas_y_avisa(self):
        editor = self._editor_con_grafo()
        self._finalizar(editor)
        self.app.update()
        self.app.pantalla.boton_volver.invoke()
        self.app.update()

        filas = self.app.pantalla.lista_aristas.winfo_children()
        self.assertEqual(len(filas), len(ARISTAS))
        self.assertIn("conservado", self.app.pantalla.mensaje.cget("text"))

    def test_se_puede_seguir_editando_y_volver_a_simular(self):
        editor = self._editor_con_grafo()
        self._finalizar(editor)
        self.app.update()
        self.app.pantalla.boton_volver.invoke()
        self.app.update()

        editor = self.app.pantalla
        self._conectar(editor, "D", "E", 1)
        self.assertTrue(editor.grafo.existe_arista("D", "E"))
        self._finalizar(editor)
        self.app.update()

        simulacion = self.app.pantalla
        self.assertIsInstance(simulacion, PantallaSimulacion)
        simulacion.menu_origen.set("A")
        simulacion.menu_destino.set("E")
        simulacion._al_cambiar_extremos()
        simulacion._ejecutar()
        # La arista nueva D→E participa: A→C→D→E = 1 + 2 + 1 (frente a A→B→D→E = 6).
        self.assertEqual(simulacion.resultado.distancia, 4)
        self.assertEqual(simulacion.resultado.caminos, (("A", "C", "D", "E"),))

    def test_la_validacion_de_ciclos_sigue_activa_tras_volver(self):
        editor = self._editor_con_grafo()
        self._finalizar(editor)
        self.app.update()
        self.app.pantalla.boton_volver.invoke()
        self.app.update()

        editor = self.app.pantalla
        self._conectar(editor, "D", "A", 1)  # D alcanzaría a A: ciclo
        self.assertFalse(editor.grafo.existe_arista("D", "A"))
        self.assertIn("ciclo", editor.mensaje.cget("text"))

    def test_el_boton_indica_a_donde_lleva_en_el_flujo_manual(self):
        editor = self._editor_con_grafo()
        self._finalizar(editor)
        self.app.update()
        self.assertEqual(self.app.pantalla.boton_volver.cget("text"), "← Editar grafo")

    def test_flujo_aleatorio_vuelve_a_configuracion(self):
        self.app.mostrar_configuracion()
        self.app.update()
        self.app.pantalla.entrada_nodos.set("9")
        self.app.pantalla._aleatorio()
        self.app.update()

        simulacion = self.app.pantalla
        self.assertIsInstance(simulacion, PantallaSimulacion)
        self.assertEqual(simulacion.boton_volver.cget("text"), "← Configuración")
        simulacion.boton_volver.invoke()
        self.app.update()

        # Debe pedir confirmación porque el grafo generado tiene aristas
        self.assertIsNotNone(simulacion.dialogo_confirmacion)
        simulacion.dialogo_confirmacion.boton_confirmar.invoke()
        self.app.update()
        self.assertIsInstance(self.app.pantalla, PantallaConfiguracion)

    def test_editor_volver_con_aristas_pide_confirmacion_y_cancelar_permanece(self):
        editor = self._editor_con_grafo()
        editor.boton_volver.invoke()
        self.app.update()

        # Se abre el diálogo
        self.assertIsNotNone(editor.dialogo_confirmacion)
        self.assertIsInstance(self.app.pantalla, PantallaEditor)

        # Cancelar mantiene al usuario en el editor con su grafo intacto
        editor.dialogo_confirmacion.boton_cancelar.invoke()
        self.app.update()
        self.assertIsInstance(self.app.pantalla, PantallaEditor)
        self.assertEqual(len(self.app.pantalla.grafo.aristas()), len(ARISTAS))

    def test_editor_volver_con_aristas_confirmar_descarta_y_vuelve(self):
        editor = self._editor_con_grafo()
        editor.boton_volver.invoke()
        self.app.update()

        self.assertIsNotNone(editor.dialogo_confirmacion)
        editor.dialogo_confirmacion.boton_confirmar.invoke()
        self.app.update()
        self.assertIsInstance(self.app.pantalla, PantallaConfiguracion)

    def test_dialogo_de_confirmacion_no_tiene_barra_de_titulo_ni_boton_cerrar(self):
        editor = self._editor_con_grafo()
        editor.boton_volver.invoke()
        self.app.update()

        dialogo = editor.dialogo_confirmacion
        self.assertTrue(dialogo.overrideredirect())
        self.assertEqual(dialogo.etiqueta_titulo.cget("text"), "¿Descartar grafo?")
        # Escape sigue funcionando como «cancelar»
        dialogo.event_generate("<Escape>")
        self.app.update()
        self.assertIsInstance(self.app.pantalla, PantallaEditor)

    def test_editor_volver_sin_aristas_vuelve_sin_dialogo(self):
        editor = self._abrir_editor()
        self.assertEqual(editor.grafo.cantidad_aristas(), 0)
        editor.boton_volver.invoke()
        self.app.update()

        self.assertIsNone(editor.dialogo_confirmacion)
        self.assertIsInstance(self.app.pantalla, PantallaConfiguracion)

    def test_simulacion_volver_cancelar_permanece_en_simulacion(self):
        self.app.mostrar_configuracion()
        self.app.update()
        self.app.pantalla.entrada_nodos.set("9")
        self.app.pantalla._aleatorio()
        self.app.update()

        simulacion = self.app.pantalla
        simulacion.boton_volver.invoke()
        self.app.update()

        self.assertIsNotNone(simulacion.dialogo_confirmacion)
        simulacion.dialogo_confirmacion.boton_cancelar.invoke()
        self.app.update()
        self.assertIsInstance(self.app.pantalla, PantallaSimulacion)

    def test_editor_escape_y_cancelar_limpian_seleccion_y_preview(self):
        editor = self._abrir_editor()
        editor._al_hacer_clic_en_nodo("A")
        self.assertEqual(editor.origen_arista, "A")
        self.assertEqual(editor.canvas.origen_preview, "A")

        # Pulsar Escape
        editor._al_pulsar_escape()
        self.assertIsNone(editor.origen_arista)
        self.assertIsNone(editor.canvas.origen_preview)

        # Ahora seleccionamos y cancelamos con el botón Cancelar
        editor._al_hacer_clic_en_nodo("B")
        self.assertEqual(editor.origen_arista, "B")
        self.assertEqual(editor.canvas.origen_preview, "B")
        editor._cancelar_seleccion()
        self.assertIsNone(editor.origen_arista)
        self.assertIsNone(editor.canvas.origen_preview)

    def test_editor_flecha_se_mantiene_al_seleccionar_destino_hasta_crear_arista(self):
        editor = self._abrir_editor()
        editor._al_hacer_clic_en_nodo("A")
        self.assertEqual(editor.canvas.origen_preview, "A")
        self.assertIsNone(editor.canvas.destino_preview)

        # Al seleccionar destino, la flecha se mantiene entre A y B
        editor._al_hacer_clic_en_nodo("B")
        self.assertEqual(editor.origen_arista, "A")
        self.assertEqual(editor.destino_arista, "B")
        self.assertEqual(editor.canvas.origen_preview, "A")
        self.assertEqual(editor.canvas.destino_preview, "B")

        # Se introduce el peso y se crea la arista: solo entonces se limpia el preview
        editor.entrada_peso.insert(0, "4")
        editor._crear_arista()
        self.assertIsNone(editor.canvas.origen_preview)
        self.assertIsNone(editor.canvas.destino_preview)
        self.assertTrue(editor.grafo.existe_arista("A", "B"))

    def test_simulacion_navegacion_con_teclas_flecha(self):
        editor = self._editor_con_grafo()
        self._finalizar(editor)
        self.app.update()

        simulacion = self.app.pantalla
        simulacion._ejecutar()
        self.assertEqual(simulacion.simulacion.indice, 0)

        # Flecha derecha avanza al siguiente paso
        simulacion._al_tecla_derecha()
        self.assertEqual(simulacion.simulacion.indice, 1)

        # Flecha izquierda retrocede al paso anterior
        simulacion._al_tecla_izquierda()
        self.assertEqual(simulacion.simulacion.indice, 0)


if __name__ == "__main__":
    unittest.main()


