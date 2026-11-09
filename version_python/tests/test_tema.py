"""Cambio de tema claro/oscuro: no debe reconstruir la pantalla ni alterar la simulación."""

import unittest
from unittest import mock

try:
    import customtkinter as ctk
    from ui import theme
    from ui.app import App
    from ui.simulation import PantallaSimulacion
    from ui.editor import PantallaEditor
    HAY_UI = True
except Exception:  # pragma: no cover - entorno sin Tkinter
    HAY_UI = False


def _hay_pantalla() -> bool:
    if not HAY_UI:
        return False
    try:
        raiz = ctk.CTk()
    except Exception:
        return False
    raiz.destroy()
    return True


def _contar_widgets(raiz) -> int:
    return 1 + sum(_contar_widgets(h) for h in raiz.winfo_children())


class TestParesDeColor(unittest.TestCase):
    @unittest.skipUnless(HAY_UI, "Requiere Tkinter")
    def test_todos_los_colores_son_pares_claro_oscuro(self):
        nombres = [n for n in dir(theme) if n.isupper() and not n.startswith(("FUENTE", "_")) and n != "FAMILIA"]
        self.assertGreater(len(nombres), 30)
        for nombre in nombres:
            valor = getattr(theme, nombre)
            self.assertIsInstance(valor, tuple, nombre)
            self.assertEqual(len(valor), 2, nombre)

    @unittest.skipUnless(HAY_UI, "Requiere Tkinter")
    def test_resolver_devuelve_el_color_del_modo_activo(self):
        try:
            theme.aplicar_modo("claro")
            self.assertEqual(theme.resolver(theme.FONDO), theme.FONDO[0])
            theme.aplicar_modo("oscuro")
            self.assertEqual(theme.resolver(theme.FONDO), theme.FONDO[1])
            self.assertEqual(theme.resolver("#123456"), "#123456")
        finally:
            theme.aplicar_modo("claro")


@unittest.skipUnless(_hay_pantalla(), "Requiere Tkinter y un display disponible")
class TestCambioDeTema(unittest.TestCase):
    def setUp(self):
        self.app = App()
        self.app.geometry("1320x860")
        self.app.update()
        self.app.iniciar_aleatorio(9)
        self.app.update()
        self.sim = self.app.pantalla
        self.assertIsInstance(self.sim, PantallaSimulacion)
        self.sim._ejecutar()
        for _ in range(4):
            self.sim._siguiente()
        self.app.update()

    def tearDown(self):
        theme.aplicar_modo("claro")
        ctk.set_appearance_mode("light")
        self.app.destroy()

    def _estado(self):
        s = self.sim.simulacion
        snap = s.actual
        return {
            "indice": s.indice,
            "snapshot": snap,
            "resultado": self.sim.resultado,
            "posiciones": self.sim.canvas.obtener_posiciones(),
            "tabla": {k: (c.cget("text")) for k, c in self.sim.tabla._celdas.items()},
            "explicacion": self.sim.texto_explicacion.get("1.0", "end"),
            "resultado_texto": self.sim.texto_resultado.get("1.0", "end"),
            "paso": self.sim.etiqueta_paso.cget("text"),
            "origen": self.sim.menu_origen.get(),
            "destino": self.sim.menu_destino.get(),
            "items": len(self.sim.canvas.canvas.find_all()),
        }

    def test_alternar_repetidamente_conserva_pantalla_widgets_y_simulacion(self):
        antes = self._estado()
        widgets = _contar_widgets(self.app)
        ids = (id(self.app.pantalla), id(self.sim.canvas), id(self.sim.tabla), id(self.sim.simulacion))
        geometria = (self.app.winfo_width(), self.app.winfo_height(),
                     self.sim.canvas.winfo_width(), self.sim.canvas.winfo_height())

        with mock.patch("ui.simulation.ejecutar_dijkstra") as recalculo:
            for i in range(10):  # claro → oscuro → claro ... (número par: vuelve al inicio)
                self.app._alternar_tema()
                self.app.update()
                esperado = "oscuro" if i % 2 == 0 else "claro"
                self.assertEqual(theme.modo_actual(), esperado)
                self.assertIs(self.app.pantalla, self.sim)
                self.assertEqual(_contar_widgets(self.app), widgets)
                self.assertEqual(self._estado(), antes)
            recalculo.assert_not_called()

        self.assertEqual(
            ids, (id(self.app.pantalla), id(self.sim.canvas), id(self.sim.tabla), id(self.sim.simulacion))
        )
        self.assertEqual(geometria, (self.app.winfo_width(), self.app.winfo_height(),
                                     self.sim.canvas.winfo_width(), self.sim.canvas.winfo_height()))

    def test_los_colores_del_canvas_y_la_tabla_siguen_al_tema(self):
        canvas = self.sim.canvas.canvas
        for modo in ("oscuro", "claro", "oscuro"):
            self.app._alternar_tema()
            self.app.update()
            self.assertEqual(theme.modo_actual(), modo)
            self.assertEqual(canvas.cget("bg"), theme.resolver(theme.FONDO_CANVAS))
            # todos los nodos usan colores del tema activo
            rellenos = {canvas.itemcget(i, "fill") for i in canvas.find_all() if canvas.type(i) == "oval"}
            permitidos = {
                theme.resolver(c) for c in (
                    theme.NODO, theme.NODO_VISITADO, theme.NODO_ACTUAL, theme.NODO_ORIGEN,
                    theme.NODO_DESTINO, theme.NODO_SELECCION_EDITOR,
                )
            }
            self.assertTrue(rellenos and rellenos <= permitidos, (modo, rellenos))
            # tabla: fondo del contenedor y de las celdas
            self.assertEqual(self.sim.tabla._contenedor.cget("bg"), theme.resolver(theme.PANEL))
            fondos = {c.cget("bg") for c in self.sim.tabla._celdas.values()}
            validos = {theme.resolver(c) for c in (
                theme.CELDA_VACIA, theme.CELDA_VIGENTE, theme.CELDA_EMPATE, theme.CELDA_DESCARTADA)}
            self.assertTrue(fondos <= validos, (modo, fondos))
            # widgets de CustomTkinter: cambian solos con el modo de apariencia
            self.assertEqual(ctk.get_appearance_mode(), "Dark" if modo == "oscuro" else "Light")

    def test_se_puede_seguir_navegando_tras_cambiar_de_tema(self):
        self.app._alternar_tema()
        self.app._alternar_tema()
        self.app._alternar_tema()
        self.app.update()
        indice = self.sim.simulacion.indice
        self.sim._siguiente()
        self.assertEqual(self.sim.simulacion.indice, indice + 1)
        self.sim._anterior()
        self.assertEqual(self.sim.simulacion.indice, indice)
        self.sim._finalizar()
        self.app.update()
        self.assertIn("Fin", self.sim.subtitulo_paso.cget("text"))

    def test_el_boton_esta_en_el_encabezado_y_no_tapa_ningun_control(self):
        self.app.update()
        boton = self.app._boton_tema
        b = (boton.winfo_rootx(), boton.winfo_rooty(),
             boton.winfo_rootx() + boton.winfo_width(), boton.winfo_rooty() + boton.winfo_height())
        encabezado = self.app._encabezado
        # el botón está dentro del encabezado
        self.assertGreaterEqual(b[1], encabezado.winfo_rooty())
        self.assertLessEqual(b[3], encabezado.winfo_rooty() + encabezado.winfo_height())

        def solapa(w):
            x0, y0 = w.winfo_rootx(), w.winfo_rooty()
            x1, y1 = x0 + w.winfo_width(), y0 + w.winfo_height()
            return not (x1 <= b[0] or x0 >= b[2] or y1 <= b[1] or y0 >= b[3])

        pantalla = self.app.pantalla
        self.assertGreaterEqual(pantalla.winfo_rooty(), encabezado.winfo_rooty() + encabezado.winfo_height())

        def todos(w):
            yield w
            for h in w.winfo_children():
                yield from todos(h)

        tapados = [w for w in todos(pantalla) if w.winfo_viewable() and solapa(w)]
        self.assertEqual(tapados, [])
        self.assertFalse(solapa(self.sim.etiqueta_paso))

    def test_el_icono_cambia_pero_el_boton_conserva_tamano_y_posicion(self):
        boton = self.app._boton_tema
        self.app.update()
        geom = (boton.winfo_x(), boton.winfo_y(), boton.winfo_width(), boton.winfo_height())
        imagen_claro = str(boton.cget("image"))
        self.app._alternar_tema()
        self.app.update()
        self.assertNotEqual(str(boton.cget("image")), imagen_claro)
        self.assertEqual(geom, (boton.winfo_x(), boton.winfo_y(), boton.winfo_width(), boton.winfo_height()))

    def test_cambio_de_tema_en_el_editor_conserva_grafo_y_seleccion(self):
        self.app.mostrar_configuracion()
        self.app.update()
        self.app.pantalla.entrada_nodos.set("7")
        self.app.pantalla._manual()
        self.app.update()
        editor = self.app.pantalla
        self.assertIsInstance(editor, PantallaEditor)
        editor._al_hacer_clic_en_nodo("A")
        editor._al_hacer_clic_en_nodo("B")
        editor.entrada_peso.insert(0, "5")
        editor._crear_arista()
        editor._al_hacer_clic_en_nodo("C")
        grafo = editor.grafo
        aristas = list(grafo.aristas())
        for _ in range(4):
            self.app._alternar_tema()
            self.app.update()
        self.assertIs(self.app.pantalla, editor)
        self.assertIs(editor.grafo, grafo)
        self.assertEqual(list(grafo.aristas()), aristas)
        self.assertEqual(editor.origen_arista, "C")

    def test_los_dialogos_siguen_funcionando_en_modo_oscuro(self):
        self.app._alternar_tema()
        self.app.update()
        self.sim.boton_volver.invoke()
        self.app.update()
        self.assertIsNotNone(self.sim.dialogo_confirmacion)
        self.sim.dialogo_confirmacion.boton_cancelar.invoke()
        self.app.update()
        self.assertIs(self.app.pantalla, self.sim)


if __name__ == "__main__":
    unittest.main()
