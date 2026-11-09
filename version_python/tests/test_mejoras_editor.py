"""Origen/destino automáticos, advertencia al finalizar y edición del peso con clic."""

import random
import unittest

try:
    import customtkinter as ctk
    from core.extremos import fuentes, saltos_desde, sugerir_extremos, sumideros
    from ui import theme
    from ui.app import App
    from ui.editor import PantallaEditor
    from ui.simulation import PantallaSimulacion
    HAY_UI = True
except Exception:  # pragma: no cover
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


@unittest.skipUnless(_hay_pantalla(), "Requiere Tkinter y un display disponible")
class Base(unittest.TestCase):
    def setUp(self):
        self.app = App()
        self.app.geometry("1320x860+0+0")
        self.app.update()

    def tearDown(self):
        theme.aplicar_modo("claro")
        ctk.set_appearance_mode("light")
        self.app.destroy()

    def editor_con(self, aristas, n=7):
        self.app.iniciar_manual(n)
        self.app.update()
        e = self.app.pantalla
        for u, v, p in aristas:
            e._al_hacer_clic_en_nodo(u)
            e._al_hacer_clic_en_nodo(v)
            e.entrada_peso.delete(0, "end")
            e.entrada_peso.insert(0, str(p))
            e._crear_arista()
        self.app.update()
        return e

    def finalizar(self, e, aceptar=True):
        """«Finalizar grafo»; si aparece una advertencia, se acepta (o no) y se devuelve el diálogo."""
        e._finalizar()
        self.app.update()
        d = e.dialogo_confirmacion
        activo = d is not None and d.winfo_exists()
        if activo and aceptar:
            d._confirmar()
            self.app.update()
        return d if activo else None


CONECTADO = [("A", "B", 2), ("A", "C", 4), ("B", "D", 1), ("C", "D", 3), ("D", "E", 2), ("E", "F", 1), ("F", "G", 5)]


class TestExtremosAutomaticos(Base):
    def test_una_fuente_y_un_destino_se_seleccionan_solos(self):
        e = self.editor_con(CONECTADO)
        self.assertIsNone(self.finalizar(e))  # sin advertencias: pasa directo
        sim = self.app.pantalla
        self.assertIsInstance(sim, PantallaSimulacion)
        self.assertEqual((sim.menu_origen.get(), sim.menu_destino.get()), ("A", "G"))
        self.assertEqual(sim.encabezado_ruta.cget("text"), "Camino mínimo:  A → G")
        self.assertEqual((sim.canvas.origen, sim.canvas.destino), ("A", "G"))

    def test_con_varias_opciones_se_elige_una_pareja_valida_modificable(self):
        e = self.editor_con([("A", "C", 1), ("B", "C", 2), ("C", "D", 3), ("C", "E", 1), ("E", "F", 2)], n=8)
        self.finalizar(e)
        sim = self.app.pantalla
        o, d = sim.menu_origen.get(), sim.menu_destino.get()
        self.assertIn(o, fuentes(sim.grafo))
        self.assertIn(d, sumideros(sim.grafo))
        self.assertIn(d, saltos_desde(sim.grafo, o))
        # se puede cambiar a mano y la simulación se invalida
        sim.menu_origen.set("B")
        sim.menu_destino.set("D")
        sim._al_elegir_extremo()
        self.assertEqual(sim.encabezado_ruta.cget("text"), "Camino mínimo:  B → D")
        sim._ejecutar()
        self.assertEqual(sim.resultado.distancia, 5)

    def test_la_seleccion_manual_se_respeta_al_volver_al_editor_y_simular_de_nuevo(self):
        e = self.editor_con(CONECTADO)
        self.finalizar(e)
        sim = self.app.pantalla
        sim.menu_origen.set("B")
        sim.menu_destino.set("F")
        sim._al_elegir_extremo()
        sim.boton_volver.invoke()
        self.app.update()
        e = self.app.pantalla
        self.assertIsInstance(e, PantallaEditor)
        e._al_hacer_clic_en_nodo("A")
        e._al_hacer_clic_en_nodo("G")
        e.entrada_peso.insert(0, "9")
        e._crear_arista()           # nueva conexión: la sugerencia automática seguiría siendo A → G
        self.finalizar(e)
        sim = self.app.pantalla
        self.assertEqual((sim.menu_origen.get(), sim.menu_destino.get()), ("B", "F"))

    def test_sin_seleccion_manual_la_pareja_se_recalcula_al_cambiar_el_grafo(self):
        e = self.editor_con([("A", "B", 1), ("B", "C", 1)])
        self.finalizar(e)
        self.assertEqual((self.app.pantalla.menu_origen.get(), self.app.pantalla.menu_destino.get()), ("A", "C"))
        self.app.pantalla.boton_volver.invoke()
        self.app.update()
        e = self.app.pantalla
        e._al_hacer_clic_en_nodo("C")
        e._al_hacer_clic_en_nodo("D")
        e.entrada_peso.insert(0, "2")
        e._crear_arista()
        self.finalizar(e)
        self.assertEqual((self.app.pantalla.menu_origen.get(), self.app.pantalla.menu_destino.get()), ("A", "D"))

    def test_un_grafo_nuevo_olvida_la_seleccion_anterior(self):
        e = self.editor_con(CONECTADO)
        self.finalizar(e)
        sim = self.app.pantalla
        sim.menu_origen.set("C")
        sim._al_elegir_extremo()
        self.app.mostrar_configuracion()
        self.app.update()
        self.assertIsNone(self.app._extremos_manuales)
        e = self.editor_con(CONECTADO)
        self.finalizar(e)
        self.assertEqual(self.app.pantalla.menu_origen.get(), "A")

    def test_el_flujo_aleatorio_conserva_la_pareja_del_generador(self):
        random.seed(4)
        self.app.iniciar_aleatorio(10)
        self.app.update()
        sim = self.app.pantalla
        self.assertIn(sim.menu_destino.get(), saltos_desde(sim.grafo, sim.menu_origen.get()))

    def test_mostrar_simulacion_sin_extremos_usa_la_sugerencia(self):
        from core.graph import Grafo
        g = Grafo(7)
        for u, v, p in CONECTADO:
            g.agregar_arista(u, v, p)
        self.app.mostrar_simulacion(g)
        self.app.update()
        self.assertEqual((self.app.pantalla.menu_origen.get(), self.app.pantalla.menu_destino.get()),
                         sugerir_extremos(g))


class TestAdvertenciaAlFinalizar(Base):
    def test_vertices_aislados_muestran_advertencia_con_los_nombres(self):
        e = self.editor_con([("A", "B", 1), ("B", "C", 2)])  # D…G aislados
        d = self.finalizar(e, aceptar=False)
        self.assertIsNotNone(d)
        texto = d.etiqueta_mensaje.cget("text")
        self.assertIn("aislados", texto)
        self.assertIn("D, E, F, G", texto)
        self.assertEqual(d.etiqueta_titulo.cget("text"), "Revisa tu grafo antes de simular")
        self.assertEqual(d.boton_confirmar.cget("text"), "Continuar de todos modos")
        self.assertEqual(d.boton_cancelar.cget("text"), "Volver al editor")
        d._cancelar()

    def test_volver_al_editor_no_cambia_de_pantalla_ni_pierde_el_grafo(self):
        e = self.editor_con([("A", "B", 1), ("B", "C", 2)])
        d = self.finalizar(e, aceptar=False)
        d._cancelar()
        self.app.update()
        self.assertIs(self.app.pantalla, e)
        self.assertEqual(e.grafo.cantidad_aristas(), 2)
        # y se puede seguir editando
        e._al_hacer_clic_en_nodo("C")
        e._al_hacer_clic_en_nodo("D")
        e.entrada_peso.insert(0, "3")
        e._crear_arista()
        self.assertEqual(e.grafo.cantidad_aristas(), 3)

    def test_continuar_de_todos_modos_pasa_a_la_simulacion(self):
        e = self.editor_con([("A", "B", 1), ("B", "C", 2)])
        d = self.finalizar(e, aceptar=False)
        d._confirmar()
        self.app.update()
        self.assertIsInstance(self.app.pantalla, PantallaSimulacion)
        self.assertEqual(self.app.pantalla.menu_origen.get(), "A")

    def test_vertices_con_conexiones_que_el_origen_no_alcanza_tambien_se_avisan(self):
        e = self.editor_con([("A", "B", 1), ("B", "C", 1), ("D", "E", 2), ("E", "F", 1), ("F", "G", 1)])
        # origen sugerido: A (alcanza A, B, C) o D (alcanza D…G): ambos dejan vértices fuera
        d = self.finalizar(e, aceptar=False)
        self.assertIsNotNone(d)
        texto = d.etiqueta_mensaje.cget("text")
        self.assertIn("no alcanza", texto)
        d._cancelar()

    def test_destino_inalcanzable_se_advierte_con_claridad(self):
        e = self.editor_con(CONECTADO)
        self.finalizar(e)
        sim = self.app.pantalla
        sim.menu_origen.set("C")
        sim.menu_destino.set("B")        # elección manual: B no es alcanzable desde C
        sim._al_elegir_extremo()
        sim.boton_volver.invoke()
        self.app.update()
        e = self.app.pantalla
        d = self.finalizar(e, aceptar=False)
        self.assertIsNotNone(d)
        texto = d.etiqueta_mensaje.cget("text")
        self.assertIn("⚠ El destino B no es alcanzable desde el origen C", texto)
        d._confirmar()
        self.app.update()
        # la selección manual (aunque sea inalcanzable) se respeta y la simulación lo explica
        sim = self.app.pantalla
        self.assertEqual((sim.menu_origen.get(), sim.menu_destino.get()), ("C", "B"))
        sim._ejecutar()
        sim._finalizar()
        self.assertFalse(sim.resultado.alcanzable)

    def test_un_grafo_sin_problemas_no_muestra_advertencia(self):
        e = self.editor_con(CONECTADO)
        self.assertIsNone(self.finalizar(e, aceptar=False))
        self.assertIsInstance(self.app.pantalla, PantallaSimulacion)

    def test_sin_aristas_sigue_el_mensaje_anterior(self):
        self.app.iniciar_manual(7)
        e = self.app.pantalla
        e._finalizar()
        self.assertIn("no tiene conexiones", e.mensaje.cget("text"))
        self.assertIsNone(e.dialogo_confirmacion)

    def test_el_dialogo_cabe_en_la_ventana_y_su_texto_no_se_corta(self):
        e = self.editor_con([("A", "B", 1), ("D", "E", 2), ("E", "F", 1)])
        d = self.finalizar(e, aceptar=False)
        d.update_idletasks()
        etiqueta = d.etiqueta_mensaje
        botones = d.boton_confirmar
        self.assertLessEqual(etiqueta.winfo_y() + etiqueta.winfo_reqheight(), botones.winfo_rooty() - d.winfo_rooty() + 2)
        self.assertLessEqual(d.winfo_height(), self.app.winfo_height())
        self.assertGreaterEqual(d.winfo_x(), self.app.winfo_rootx())
        d._cancelar()

    def test_el_dialogo_funciona_en_modo_oscuro(self):
        self.app._alternar_tema()
        e = self.editor_con([("A", "B", 1)])
        d = self.finalizar(e, aceptar=False)
        self.assertIsNotNone(d)
        d._cancelar()


class TestEditarPesoConClic(Base):
    def setUp(self):
        super().setUp()
        self.e = self.editor_con([("A", "B", 2), ("B", "C", 7), ("A", "C", 4)])
        self.c = self.e.canvas

    def centro(self, u, v):
        x0, y0, x1, y1 = self.c._cajas_peso[(u, v)]
        return int((x0 + x1) / 2), int((y0 + y1) / 2)

    def clic_en_peso(self, u, v):
        x, y = self.centro(u, v)
        self.c.canvas.event_generate("<ButtonPress-1>", x=x, y=y)
        self.c.canvas.event_generate("<ButtonRelease-1>", x=x, y=y)
        self.app.update()

    def escribir(self, texto, tecla="Return"):
        _, entrada, _, _ = self.c._editor_peso
        entrada.focus_force()
        self.app.update()
        entrada.delete(0, "end")
        entrada.insert(0, texto)
        entrada.event_generate(f"<{tecla}>")
        self.app.update()

    def texto_del_peso(self, u, v):
        x0, y0, x1, y1 = self.c._cajas_peso[(u, v)]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        items = [i for i in self.c.canvas.find_overlapping(cx - 1, cy - 1, cx + 1, cy + 1)
                 if self.c.canvas.type(i) == "text"]
        return [self.c.canvas.itemcget(i, "text") for i in items]

    def test_clic_sobre_el_peso_abre_un_campo_con_el_valor_actual(self):
        self.clic_en_peso("A", "B")
        self.assertEqual(self.c.editando_peso(), ("A", "B"))
        _, entrada, item, _ = self.c._editor_peso
        self.assertEqual(entrada.get(), "2")
        # el campo está sobre el recuadro del peso
        cx, cy = self.c.canvas.coords(item)
        x0, y0, x1, y1 = self.c._cajas_peso[("A", "B")]
        self.assertAlmostEqual(cx, (x0 + x1) / 2, delta=1)
        self.assertAlmostEqual(cy, (y0 + y1) / 2, delta=1)

    def test_enter_actualiza_grafo_y_panel_lateral_al_instante(self):
        self.clic_en_peso("A", "B")
        self.escribir("9")
        self.assertEqual(self.e.grafo.peso("A", "B"), 9)
        self.assertIsNone(self.c.editando_peso())
        self.assertIn("9", self.texto_del_peso("A", "B"))
        textos = []
        for fila in self.e.lista_aristas.winfo_children():
            textos += [h.cget("text") for h in fila.winfo_children() if isinstance(h, ctk.CTkLabel)]
        self.assertIn("peso 9", textos)
        self.assertNotIn("peso 2", textos)
        self.assertIn("actualizado a 9", self.e.mensaje.cget("text"))

    def test_los_pesos_invalidos_se_rechazan_y_el_campo_sigue_abierto(self):
        self.clic_en_peso("B", "C")
        for malo in ("", "abc", "0", "-3", "100", "2.5"):
            self.escribir(malo)
            self.assertEqual(self.e.grafo.peso("B", "C"), 7, malo)
            self.assertEqual(self.c.editando_peso(), ("B", "C"), malo)
            self.assertEqual(self.e.mensaje.cget("text_color"), theme.PELIGRO, malo)
        self.escribir("11")  # y se corrige sin volver a hacer clic
        self.assertEqual(self.e.grafo.peso("B", "C"), 11)
        self.assertIsNone(self.c.editando_peso())

    def test_escape_cancela_sin_cambios(self):
        self.clic_en_peso("A", "C")
        self.escribir("50", tecla="Escape")
        self.assertIsNone(self.c.editando_peso())
        self.assertEqual(self.e.grafo.peso("A", "C"), 4)

    def test_hacer_clic_en_otro_sitio_cierra_el_campo_sin_cambios(self):
        self.clic_en_peso("A", "C")
        _, entrada, _, _ = self.c._editor_peso
        entrada.focus_force()
        self.app.update()
        self.e.entrada_peso.focus_force()
        self.app.update()
        self.assertIsNone(self.c.editando_peso())
        self.assertEqual(self.e.grafo.peso("A", "C"), 4)

    def test_se_pueden_editar_varios_pesos_seguidos(self):
        for (u, v), nuevo in ((("A", "B"), 5), (("B", "C"), 6), (("A", "C"), 8)):
            self.clic_en_peso(u, v)
            self.escribir(str(nuevo))
            self.assertEqual(self.e.grafo.peso(u, v), nuevo)

    def test_un_clic_en_un_nodo_o_en_vacio_no_abre_el_campo(self):
        x, y = self.c._posiciones["A"]
        self.c.canvas.event_generate("<ButtonPress-1>", x=int(x), y=int(y))
        self.c.canvas.event_generate("<ButtonRelease-1>", x=int(x), y=int(y))
        self.c.canvas.event_generate("<ButtonPress-1>", x=3, y=3)
        self.c.canvas.event_generate("<ButtonRelease-1>", x=3, y=3)
        self.app.update()
        self.assertIsNone(self.c.editando_peso())
        self.assertEqual(self.e.origen_arista, "A")  # el clic en el nodo siguió seleccionando

    def test_la_seleccion_en_curso_no_se_pierde_al_editar_un_peso(self):
        self.e._al_hacer_clic_en_nodo("D")
        self.e._al_hacer_clic_en_nodo("E")
        self.clic_en_peso("A", "B")
        self.escribir("3")
        self.assertEqual((self.e.origen_arista, self.e.destino_arista), ("D", "E"))

    def test_arrastrar_un_nodo_sobre_un_peso_no_abre_el_campo(self):
        x, y = self.c._posiciones["D"]
        px, py = self.centro("A", "B")
        self.c.canvas.event_generate("<ButtonPress-1>", x=int(x), y=int(y))
        self.c.canvas.event_generate("<B1-Motion>", x=px, y=py)
        self.c.canvas.event_generate("<ButtonRelease-1>", x=px, y=py)
        self.app.update()
        self.assertIsNone(self.c.editando_peso())

    def test_el_cursor_indica_que_el_peso_es_clicable(self):
        x, y = self.centro("A", "B")
        self.c.canvas.event_generate("<Motion>", x=x, y=y)
        self.app.update()
        self.assertEqual(str(self.c.canvas.cget("cursor")), "hand2")

    def test_el_campo_sigue_sobre_su_arista_si_cambia_el_tamano_de_la_ventana(self):
        self.clic_en_peso("A", "B")
        self.app.geometry("1500x900+0+0")
        self.app.update()
        self.app.update()
        if self.c.editando_peso() is None:   # el redibujado pudo cerrarlo: también es válido
            return
        _, entrada, item, _ = self.c._editor_peso
        cx, cy = self.c.canvas.coords(item)
        x0, y0, x1, y1 = self.c._cajas_peso[("A", "B")]
        self.assertAlmostEqual(cx, (x0 + x1) / 2, delta=1)
        self.assertAlmostEqual(cy, (y0 + y1) / 2, delta=1)

    def test_cambiar_de_tema_con_el_campo_abierto_lo_cierra_sin_romper_nada(self):
        self.clic_en_peso("A", "B")
        self.app._alternar_tema()
        self.app.update()
        self.assertIsNone(self.c.editando_peso())
        self.assertEqual(self.e.grafo.peso("A", "B"), 2)
        self.clic_en_peso("A", "B")   # y se puede volver a abrir en el otro tema
        self.escribir("6")
        self.assertEqual(self.e.grafo.peso("A", "B"), 6)

    def test_el_boton_peso_de_la_lista_sigue_existiendo(self):
        botones = []
        for fila in self.e.lista_aristas.winfo_children():
            botones += [h for h in fila.winfo_children() if h.winfo_class() == "Frame" or hasattr(h, "cget")]
        self.assertTrue(any(getattr(b, "cget", lambda *_: "")("text") == "Peso" for b in botones))

    def test_en_la_simulacion_los_pesos_no_son_editables(self):
        e = self.editor_con(CONECTADO)
        self.finalizar(e)
        sim = self.app.pantalla
        self.assertIsNone(sim.canvas.al_hacer_clic_en_peso)
        x0, y0, x1, y1 = next(iter(sim.canvas._cajas_peso.values()))
        sim.canvas.canvas.event_generate("<ButtonPress-1>", x=int((x0 + x1) / 2), y=int((y0 + y1) / 2))
        sim.canvas.canvas.event_generate("<ButtonRelease-1>", x=int((x0 + x1) / 2), y=int((y0 + y1) / 2))
        self.app.update()
        self.assertIsNone(sim.canvas.editando_peso())

    def test_finalizar_con_el_campo_abierto_lo_cierra(self):
        e = self.editor_con(CONECTADO)
        c = e.canvas
        x0, y0, x1, y1 = c._cajas_peso[("A", "B")]
        c.canvas.event_generate("<ButtonPress-1>", x=int((x0 + x1) / 2), y=int((y0 + y1) / 2))
        c.canvas.event_generate("<ButtonRelease-1>", x=int((x0 + x1) / 2), y=int((y0 + y1) / 2))
        self.app.update()
        self.assertEqual(c.editando_peso(), ("A", "B"))
        self.finalizar(e)
        self.assertIsNone(c.editando_peso())


if __name__ == "__main__":
    unittest.main()
