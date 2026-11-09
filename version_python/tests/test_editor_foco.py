"""Editor manual: el campo del peso debe quedar listo al instante tras elegir el destino."""

import time
import unittest

try:
    import customtkinter as ctk
    from ui.app import App
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


PARES = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("D", "E"), ("E", "F"),
         ("F", "G"), ("G", "H"), ("A", "H"), ("B", "H")]


@unittest.skipUnless(_hay_pantalla(), "Requiere Tkinter y un display disponible")
class TestFocoDelPeso(unittest.TestCase):
    def setUp(self):
        self.app = App()
        self.app.geometry("1320x860+0+0")
        self.app.update()
        self.app.iniciar_manual(8)
        self.app.update()
        self.ed = self.app.pantalla
        self.assertIsInstance(self.ed, PantallaEditor)
        self.app.focus_force()
        self.app.update()

    def tearDown(self):
        self.app.destroy()

    def _clic(self, vertice):
        """Clic real sobre el canvas (presionar y soltar), como lo hace el usuario."""
        cv = self.ed.canvas
        x, y = cv._posiciones[vertice]
        cv.canvas.event_generate("<Motion>", x=x, y=y)
        cv.canvas.event_generate("<ButtonPress-1>", x=x, y=y)
        cv.canvas.event_generate("<ButtonRelease-1>", x=x, y=y)
        self.app.update()

    def test_tras_elegir_destino_el_peso_tiene_el_foco_y_acepta_teclas(self):
        for u, v in PARES:
            self.ed._cancelar_seleccion()
            self.app.update()
            self._clic(u)
            self._clic(v)
            self.assertEqual((self.ed.origen_arista, self.ed.destino_arista), (u, v))
            self.assertIs(self.app.focus_get(), self.ed.entrada_peso._entry, (u, v))

    def test_se_puede_escribir_el_peso_y_crear_la_arista_sin_tocar_nada_mas(self):
        self._clic("B")
        self._clic("A")
        entrada = self.ed.entrada_peso._entry
        for tecla in "7":
            entrada.event_generate("<KeyPress>", keysym=tecla)
            entrada.event_generate("<KeyRelease>", keysym=tecla)
        self.app.update()
        self.assertEqual(self.ed.entrada_peso.get(), "7")
        entrada.event_generate("<Return>")
        self.app.update()
        self.assertTrue(self.ed.grafo.existe_arista("B", "A"))
        self.assertEqual(self.ed.grafo.peso("B", "A"), 7)

    def test_seleccionar_nodos_no_reconstruye_la_lista_de_aristas(self):
        for u, v in PARES[:4]:
            self._clic(u)
            self._clic(v)
            self.ed.entrada_peso.delete(0, "end")
            self.ed.entrada_peso.insert(0, "3")
            self.ed._crear_arista()
            self.app.update()
        filas = list(self.ed.lista_aristas.winfo_children())
        self.assertEqual(len(filas), 4)

        self._clic("E")
        self._clic("F")
        self.ed._cancelar_seleccion()
        self.app.update()
        self.assertEqual(list(self.ed.lista_aristas.winfo_children()), filas)  # mismos widgets

        # ...pero sí se actualiza cuando cambian las aristas
        self.ed._eliminar_arista("A", "B")
        self.app.update()
        self.assertEqual(len(self.ed.lista_aristas.winfo_children()), 3)
        self.ed.grafo.modificar_peso("A", "C", 9)
        self.ed._refrescar()
        textos = []
        for fila in self.ed.lista_aristas.winfo_children():
            textos += [h.cget("text") for h in fila.winfo_children() if isinstance(h, ctk.CTkLabel)]
        self.assertIn("peso 9", textos)

    def test_elegir_nodos_es_rapido_aun_con_muchas_aristas(self):
        for u, v in PARES:
            self._clic(u)
            self._clic(v)
            self.ed.entrada_peso.delete(0, "end")
            self.ed.entrada_peso.insert(0, "3")
            self.ed._crear_arista()
            self.app.update()
        t0 = time.perf_counter()
        for _ in range(5):
            self._clic("A")
            self.ed._cancelar_seleccion()
            self.app.update()
        promedio = (time.perf_counter() - t0) / 5
        self.assertLess(promedio, 0.25, f"{promedio * 1000:.0f} ms por selección")

    def test_el_foco_vuelve_a_la_ventana_al_cerrar_el_dialogo(self):
        self._clic("A")
        self._clic("B")
        self.ed.entrada_peso.insert(0, "4")
        self.ed._crear_arista()
        self.app.update()
        self.ed.boton_volver.invoke()
        self.app.update()
        self.assertIsNotNone(self.ed.dialogo_confirmacion)
        self.ed.dialogo_confirmacion.boton_cancelar.invoke()
        self.app.update()
        self._clic("C")
        self._clic("D")
        self.assertIs(self.app.focus_get(), self.ed.entrada_peso._entry)


if __name__ == "__main__":
    unittest.main()
