"""Pantalla de simulación: desplazamiento, encabezado, marcas ORIGEN/DESTINO y «Más detalles»."""

import random
import unittest
from types import SimpleNamespace

try:
    import customtkinter as ctk
    from core import explicaciones
    from core.generator import generar_dag, generar_dag_didactico
    from core.graph import Grafo
    from ui import rueda, theme
    from ui.app import App
    from ui.simulation import PantallaSimulacion
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


def rueda_en(widget, delta=-120, shift=False):
    """Evento de rueda con el puntero sobre el centro de ``widget``."""
    widget.update_idletasks()
    return SimpleNamespace(
        x_root=widget.winfo_rootx() + min(30, max(widget.winfo_width() // 2, 1)),
        y_root=widget.winfo_rooty() + min(30, max(widget.winfo_height() // 2, 1)),
        delta=delta, num=None, state=0x0001 if shift else 0,
    )


@unittest.skipUnless(_hay_pantalla(), "Requiere Tkinter y un display disponible")
class Base(unittest.TestCase):
    GEOMETRIA = "1320x860+0+0"

    def setUp(self):
        self.app = App()
        self.app.geometry(self.GEOMETRIA)
        self.app.update()
        self.app.iniciar_aleatorio(10)
        self.app.update()
        self.sim = self.app.pantalla
        self.assertIsInstance(self.sim, PantallaSimulacion)

    def tearDown(self):
        theme.aplicar_modo("claro")
        ctk.set_appearance_mode("light")
        self.app.destroy()

    def ejecutar(self, pasos=0):
        self.sim._ejecutar()
        for _ in range(pasos):
            self.sim._siguiente()
        self.app.update()

    def girar(self, widget, **kw):
        self.sim.pagina.rueda._ultimo = None  # sin «retención» entre gestos de la prueba
        self.sim.pagina.desplazar_con_rueda(rueda_en(widget, **kw))
        self.app.update()


class TestDesplazamiento(Base):
    GEOMETRIA = "1100x760+0+0"  # el mínimo permitido: el contenido no cabe entero

    def test_la_pagina_se_desplaza_con_la_rueda_sobre_el_grafo(self):
        self.ejecutar(3)
        pagina = self.sim.pagina
        self.assertTrue(pagina.desbordada, "a 1100×760 el contenido debe exceder la ventana")
        self.assertEqual(pagina._lienzo.yview()[0], 0.0)
        self.girar(self.sim.canvas.canvas, delta=-120)  # rueda hacia abajo
        self.assertGreater(pagina._lienzo.yview()[0], 0.0)
        antes = pagina._lienzo.yview()[0]
        self.girar(self.sim.canvas.canvas, delta=120)   # y hacia arriba
        self.assertLess(pagina._lienzo.yview()[0], antes)

    def test_la_rueda_llega_hasta_el_final_de_la_pagina(self):
        self.ejecutar(3)
        for _ in range(60):
            self.girar(self.sim.canvas.canvas, delta=-120)
        self.assertGreaterEqual(self.sim.pagina._lienzo.yview()[1], 0.999)

    def test_la_rueda_sobre_la_tabla_mueve_la_tabla_y_no_la_pagina(self):
        self.ejecutar(0)
        self.sim._finalizar()
        self.app.update()
        tabla, pagina = self.sim.tabla, self.sim.pagina
        self.assertLess(tabla._contenedor.yview()[1], 1.0, "la tabla debe tener filas ocultas")
        y_pagina = pagina._lienzo.yview()
        celda = next(iter(tabla._celdas.values()))
        self.girar(celda, delta=-120)
        self.assertGreater(tabla._contenedor.yview()[0], 0.0)
        self.assertEqual(pagina._lienzo.yview(), y_pagina)

    def test_mayus_mas_rueda_desplaza_la_tabla_en_horizontal(self):
        self.ejecutar(0)
        self.sim._finalizar()
        self.app.update()
        tabla = self.sim.tabla
        antes = tabla._contenedor.xview()
        puede = antes[1] < 1.0
        self.girar(tabla._contenedor, delta=-120, shift=True)
        if puede:
            self.assertGreater(tabla._contenedor.xview()[0], antes[0])

    def test_una_tabla_en_su_limite_deja_pasar_la_rueda_a_la_pagina(self):
        self.ejecutar(0)
        self.sim._finalizar()
        self.app.update()
        tabla, pagina = self.sim.tabla, self.sim.pagina
        tabla._contenedor.yview_moveto(0.0)
        self.girar(tabla._contenedor, delta=120)  # hacia arriba: la tabla ya está arriba
        self.assertEqual(tabla._contenedor.yview()[0], 0.0)
        pagina._lienzo.yview_moveto(0.0)
        self.girar(tabla._contenedor, delta=-120)  # hacia abajo: la tabla puede bajar
        self.assertGreater(tabla._contenedor.yview()[0], 0.0)
        self.assertEqual(pagina._lienzo.yview()[0], 0.0)

    def test_un_cuadro_de_texto_con_desbordamiento_se_desplaza_solo(self):
        self.ejecutar(0)
        caja = self.sim.texto_explicacion
        caja.configure(state="normal")
        caja.insert("end", "\n".join(f"línea {i}" for i in range(80)))
        caja.configure(state="disabled")
        self.app.update()
        pagina = self.sim.pagina
        y_pagina = pagina._lienzo.yview()
        self.girar(caja._textbox, delta=-120)
        self.assertGreater(caja.yview()[0], 0.0)
        self.assertEqual(pagina._lienzo.yview(), y_pagina)

    def test_un_cuadro_sin_desbordamiento_deja_desplazar_la_pagina(self):
        self.ejecutar(0)
        self.sim._al_cambiar_extremos()  # el resultado vuelve a ser un texto corto
        self.app.update()
        caja = self.sim.texto_resultado
        self.assertEqual(caja.yview(), (0.0, 1.0))
        self.girar(caja._textbox, delta=-120)
        self.assertGreater(self.sim.pagina._lienzo.yview()[0], 0.0)

    def test_la_rueda_fuera_de_la_pagina_no_hace_nada(self):
        self.ejecutar(0)
        y = self.sim.pagina._lienzo.yview()
        self.girar(self.sim.boton_siguiente, delta=-120)  # barra de navegación (fija)
        self.assertEqual(self.sim.pagina._lienzo.yview(), y)

    def test_el_enrutador_sobrevive_a_entrar_y_salir_de_la_tabla(self):
        """Antes la tabla hacía bind_all/unbind_all de la rueda al entrar/salir el puntero."""
        self.ejecutar(0)
        tabla = self.sim.tabla
        tabla._contenedor.event_generate("<Enter>")
        tabla._contenedor.event_generate("<Leave>")
        self.app.update()
        self.assertTrue(self.app.bind_all("<MouseWheel>"))
        y = self.sim.pagina._lienzo.yview()
        self.girar(self.sim.canvas.canvas, delta=-120)
        self.assertNotEqual(self.sim.pagina._lienzo.yview(), y)

    def test_la_rueda_llega_por_los_eventos_reales_de_tk(self):
        self.ejecutar(0)
        c = self.sim.canvas.canvas
        self.app.update()
        try:
            c.event_generate("<MouseWheel>", delta=-120, x=40, y=40,
                             rootx=c.winfo_rootx() + 40, rooty=c.winfo_rooty() + 40)
        except Exception:
            self.skipTest("este Tk no permite generar <MouseWheel>")
        self.app.update()
        if self.sim.pagina._lienzo.yview()[0] == 0.0:
            c.event_generate("<Button-5>", x=40, y=40,
                             rootx=c.winfo_rootx() + 40, rooty=c.winfo_rooty() + 40)
            self.app.update()
        self.assertGreater(self.sim.pagina._lienzo.yview()[0], 0.0)

    def test_el_resultado_es_accesible_con_la_ventana_minima(self):
        self.ejecutar(0)
        self.sim._finalizar()
        for _ in range(60):
            self.girar(self.sim.canvas.canvas, delta=-120)
        pagina, caja = self.sim.pagina, self.sim.texto_resultado
        base = pagina._lienzo.winfo_rooty()
        self.assertGreaterEqual(caja.winfo_rooty(), base)
        self.assertLessEqual(caja.winfo_rooty() + caja.winfo_height(), base + pagina._lienzo.winfo_height() + 2)
        self.assertIn("Distancia mínima", caja.get("1.0", "end"))

    def test_al_llegar_al_final_el_resultado_queda_a_la_vista_sin_girar_la_rueda(self):
        self.ejecutar(0)
        self.sim._finalizar()
        self.app.update()
        pagina, caja = self.sim.pagina, self.sim.texto_resultado
        base = pagina._lienzo.winfo_rooty()
        self.assertLessEqual(caja.winfo_rooty() + caja.winfo_height(), base + pagina._lienzo.winfo_height() + 2)

    def test_con_la_ventana_grande_no_hace_falta_desplazar(self):
        self.app.geometry("1500x1000+0+0")
        self.app.update()
        self.ejecutar(2)
        self.assertFalse(self.sim.pagina.desbordada)
        self.assertFalse(self.sim.pagina._barra_visible)

    def test_la_navegacion_siempre_esta_visible(self):
        self.ejecutar(0)
        for _ in range(60):
            self.girar(self.sim.canvas.canvas, delta=-120)
        b = self.sim.boton_siguiente
        self.assertTrue(b.winfo_viewable())
        self.assertLessEqual(b.winfo_rooty() + b.winfo_height(), self.app.winfo_rooty() + self.app.winfo_height())


class TestEncabezadoYMarcas(Base):
    def _textos_de_marca(self):
        c = self.sim.canvas.canvas
        return sorted(c.itemcget(i, "text") for i in c.find_withtag("marca") if c.type(i) == "text")

    def test_antes_de_ejecutar_muestra_la_ruta_y_la_indicacion(self):
        o, d = self.sim.menu_origen.get(), self.sim.menu_destino.get()
        self.assertEqual(self.sim.encabezado_ruta.cget("text"), f"Camino mínimo:  {o} → {d}")
        self.assertEqual(self.sim.encabezado_estado.cget("text"), "Pulsa Ejecutar Dijkstra para comenzar")
        self.assertEqual(self.sim.barra_progreso.get(), 0)

    def test_la_ruta_y_las_marcas_siguen_a_los_selectores(self):
        v = self.sim.grafo.vertices
        self.sim.menu_origen.set(v[1])
        self.sim.menu_destino.set(v[3])
        self.sim._al_cambiar_extremos()
        self.app.update()
        self.assertEqual(self.sim.encabezado_ruta.cget("text"), f"Camino mínimo:  {v[1]} → {v[3]}")
        self.assertEqual(self._textos_de_marca(), ["DESTINO", "ORIGEN"])
        self.assertEqual((self.sim.canvas.origen, self.sim.canvas.destino), (v[1], v[3]))
        # las marcas están sobre los vértices elegidos
        c = self.sim.canvas
        for nombre, vertice in (("ORIGEN", v[1]), ("DESTINO", v[3])):
            item = next(i for i in c.canvas.find_withtag("marca")
                        if c.canvas.type(i) == "text" and c.canvas.itemcget(i, "text") == nombre)
            x0, y0, x1, y1 = c.canvas.bbox(item)
            vx, vy = c._posiciones[vertice]
            self.assertLess(abs((x0 + x1) / 2 - vx), 2)
            self.assertLess(y1, vy - 21 + 1)  # encima del círculo

    def test_origen_igual_a_destino_muestra_una_sola_marca_combinada(self):
        v = self.sim.grafo.vertices
        self.sim.menu_origen.set(v[2])
        self.sim.menu_destino.set(v[2])
        self.sim._al_cambiar_extremos()
        self.app.update()
        self.assertEqual(self._textos_de_marca(), ["ORIGEN · DESTINO"])

    def test_las_marcas_se_mantienen_durante_toda_la_simulacion_y_en_ambos_temas(self):
        self.ejecutar(0)
        for i in range(self.sim.simulacion.total):
            self.sim.simulacion.indice = i
            self.sim._refrescar()
            self.assertEqual(self._textos_de_marca(), ["DESTINO", "ORIGEN"], i)
        self.app._alternar_tema()
        self.app.update()
        self.assertEqual(self._textos_de_marca(), ["DESTINO", "ORIGEN"])

    def test_el_encabezado_durante_y_al_final(self):
        self.ejecutar(2)
        d = self.sim.menu_destino.get()
        self.assertIn(f"Distancia a {d}:", self.sim.encabezado_estado.cget("text"))
        self.assertTrue(any(p in self.sim.encabezado_estado.cget("text") for p in ("provisional", "aún sin alcanzar", "definitiva")))
        self.assertGreater(self.sim.barra_progreso.get(), 0)
        self.sim._finalizar()
        r = self.sim.resultado
        texto = self.sim.encabezado_estado.cget("text")
        self.assertIn("Completada", texto)
        self.assertIn(f"distancia mínima {int(r.distancia)}", texto)
        self.assertEqual(self.sim.barra_progreso.get(), 1.0)

    def test_el_encabezado_al_finalizar_sin_camino(self):
        g = Grafo(7)
        for u, v, p in [("A", "B", 1), ("C", "D", 2), ("D", "E", 1)]:
            g.agregar_arista(u, v, p)
        self.app.mostrar_simulacion(g, "A", "E")
        self.app.update()
        sim = self.app.pantalla
        sim._ejecutar()
        sim._finalizar()
        self.assertIn("no existe camino de A a E", sim.encabezado_estado.cget("text"))

    def test_cambiar_el_selector_reinicia_el_encabezado(self):
        self.ejecutar(3)
        v = self.sim.grafo.vertices
        self.sim.menu_destino.set(v[-1])
        self.sim._al_cambiar_extremos()
        self.assertEqual(self.sim.encabezado_estado.cget("text"), "Pulsa Ejecutar Dijkstra para comenzar")
        self.assertEqual(self.sim.barra_progreso.get(), 0)

    def test_el_encabezado_no_cambia_de_alto_ni_mueve_el_grafo(self):
        c = self.sim.canvas
        antes = (self.sim.encabezado_ruta.winfo_height(), c.winfo_rooty(), c.winfo_height())
        self.ejecutar(3)
        self.sim._finalizar()
        self.app.update()
        self.assertEqual(antes, (self.sim.encabezado_ruta.winfo_height(), c.winfo_rooty(), c.winfo_height()))

    def test_las_marcas_no_se_solapan_con_vertices_ni_con_pesos_ni_con_etiquetas(self):
        azar = random.Random(11)
        problemas = []
        for n in (7, 9, 12, 14, 16):
            for intento in range(3):
                g, o, d = generar_dag(n, rng=azar)
                self.app.mostrar_simulacion(g, o, d)
                self.app.update()
                sim = self.app.pantalla
                sim._ejecutar()
                for paso in (0, 2, sim.simulacion.total // 2, sim.simulacion.total - 1):
                    sim.simulacion.indice = paso
                    sim._refrescar()
                    self.app.update()
                    problemas += self._solapes(sim.canvas, n, intento, paso)
        self.assertEqual(problemas, [])

    @staticmethod
    def _solapes(gcanvas, n, intento, paso):
        c = gcanvas.canvas
        marcas = [c.bbox(i) for i in c.find_withtag("marca") if c.type(i) == "polygon"]
        encontrados = []

        def cruza(a, b, margen=2):
            # bbox de Tk incluye ~1-2 px de relleno: dos cajas que solo se tocan no cuentan
            return (a[0] + margen < b[2] and b[0] + margen < a[2]
                    and a[1] + margen < b[3] and b[1] + margen < a[3])

        for caja in marcas:
            for item in c.find_all():
                if "marca" in c.gettags(item):
                    continue
                tipo = c.type(item)
                bb = c.bbox(item)
                if tipo == "rectangle" or (tipo == "text" and not c.itemcget(item, "text") in gcanvas.grafo.vertices):
                    if cruza(caja, bb):
                        encontrados.append((n, intento, paso, tipo, c.itemcget(item, "text") if tipo == "text" else ""))
                elif tipo == "oval":
                    if cruza(caja, bb):
                        encontrados.append((n, intento, paso, "vertice"))
        return encontrados


class TestMasDetalles(Base):
    def test_el_boton_esta_desactivado_hasta_ejecutar(self):
        self.assertEqual(self.sim.boton_detalles.cget("state"), "disabled")
        self.ejecutar(0)
        self.assertEqual(self.sim.boton_detalles.cget("state"), "normal")

    def test_abre_una_ventana_secundaria_no_modal_con_el_detalle_del_paso(self):
        self.ejecutar(3)
        self.sim._abrir_detalles()
        self.app.update()
        v = self.sim._ventana_detalles
        self.assertIsNotNone(v)
        esperado = explicaciones.explicar(self.sim.grafo, self.sim.resultado, self.sim.simulacion.indice)
        contenido = v.texto.get("1.0", "end")
        self.assertIn("Cómo leer una etiqueta", contenido)
        self.assertIn("Estado de todos los vértices", contenido)
        self.assertEqual(contenido.strip(), explicaciones.Explicacion.texto_plano(esperado.detalle).strip())
        self.assertEqual(v.etiqueta_titulo.cget("text"), esperado.titulo)
        self.assertEqual(v.etiqueta_paso.cget("text"), f"Paso {self.sim.simulacion.indice + 1} de {self.sim.simulacion.total}")
        # no modal: la ventana principal sigue respondiendo
        self.assertEqual(self.app.grab_current(), None)
        indice = self.sim.simulacion.indice
        self.sim.boton_siguiente.invoke()
        self.app.update()
        self.assertEqual(self.sim.simulacion.indice, indice + 1)

    def test_se_actualiza_al_avanzar_retroceder_reiniciar_y_finalizar(self):
        self.ejecutar(0)
        self.sim._abrir_detalles()
        self.app.update()
        v = self.sim._ventana_detalles
        vistos = set()
        for accion in (self.sim._siguiente, self.sim._siguiente, self.sim._siguiente, self.sim._anterior,
                       self.sim._reiniciar, self.sim._finalizar):
            accion()
            self.app.update()
            esperado = explicaciones.explicar(self.sim.grafo, self.sim.resultado, self.sim.simulacion.indice)
            self.assertEqual(v.texto.get("1.0", "end").strip(),
                             explicaciones.Explicacion.texto_plano(esperado.detalle).strip())
            self.assertEqual(v.etiqueta_titulo.cget("text"), esperado.titulo)
            vistos.add(esperado.titulo)
        self.assertGreater(len(vistos), 3)

    def test_abrirla_dos_veces_no_duplica_la_ventana(self):
        self.ejecutar(1)
        self.sim._abrir_detalles()
        primera = self.sim._ventana_detalles
        self.sim._abrir_detalles()
        self.app.update()
        self.assertIs(self.sim._ventana_detalles, primera)

    def test_se_cierra_con_el_boton_con_escape_y_al_salir_de_la_pantalla(self):
        self.ejecutar(1)
        self.sim._abrir_detalles()
        self.app.update()
        self.sim._ventana_detalles.boton_cerrar.invoke()
        self.app.update()
        self.assertIsNone(self.sim._ventana_detalles)
        self.sim._abrir_detalles()
        self.app.update()
        ventana = self.sim._ventana_detalles
        ventana.event_generate("<Escape>")
        self.app.update()
        self.assertIsNone(self.sim._ventana_detalles)
        self.assertFalse(ventana.winfo_exists())
        self.sim._abrir_detalles()
        ventana = self.sim._ventana_detalles
        self.app.mostrar_configuracion()
        self.app.update()
        self.assertFalse(ventana.winfo_exists())

    def test_avisa_si_cambia_el_origen_o_el_destino_con_la_ventana_abierta(self):
        self.ejecutar(2)
        self.sim._abrir_detalles()
        self.app.update()
        self.sim.menu_destino.set(self.sim.grafo.vertices[-1])
        self.sim._al_cambiar_extremos()
        self.app.update()
        self.assertEqual(self.sim._ventana_detalles.etiqueta_titulo.cget("text"), "Simulación no iniciada")
        self.assertIn("Ejecutar Dijkstra", self.sim._ventana_detalles.texto.get("1.0", "end"))
        self.sim._ejecutar()
        self.app.update()
        self.assertNotEqual(self.sim._ventana_detalles.etiqueta_titulo.cget("text"), "Simulación no iniciada")

    def test_funciona_en_modo_oscuro_y_se_recolorea_al_cambiar_de_tema(self):
        self.ejecutar(3)
        self.sim._abrir_detalles()
        self.app.update()
        texto = self.sim._ventana_detalles.texto._textbox
        claro = texto.tag_cget("titulo", "foreground")
        self.app._alternar_tema()
        self.app.update()
        self.assertNotEqual(texto.tag_cget("titulo", "foreground"), claro)
        self.assertEqual(texto.tag_cget("titulo", "foreground"), theme.resolver(theme.ACENTO))
        self.app._alternar_tema()
        self.app.update()
        self.assertEqual(texto.tag_cget("titulo", "foreground"), claro)


class TestNavegacionYEstado(Base):
    def test_avanzar_y_retroceder_muestra_siempre_la_explicacion_de_ese_paso(self):
        self.ejecutar(0)
        sim = self.sim
        total = sim.simulacion.total

        def fotografia():
            i = sim.simulacion.indice
            esperado = explicaciones.explicar(sim.grafo, sim.resultado, i)
            self.assertEqual(sim.texto_explicacion.get("1.0", "end").strip(),
                             explicaciones.Explicacion.texto_plano(esperado.breve).strip(), i)
            self.assertEqual(sim.titulo_paso.cget("text"), esperado.titulo)
            self.assertEqual(sim.etiqueta_paso.cget("text"), f"Paso {i + 1} de {total}")
            return sim.texto_explicacion.get("1.0", "end"), sim.encabezado_estado.cget("text")

        ida = [fotografia()]
        for _ in range(total - 1):
            sim._siguiente()
            ida.append(fotografia())
        vuelta = []
        for _ in range(total - 1):
            sim._anterior()
            vuelta.append(fotografia())
        self.assertEqual(vuelta, list(reversed(ida[:-1])))  # mismo contenido al volver por el mismo paso

    def test_actualizar_el_texto_de_un_paso_no_reconstruye_widgets(self):
        self.ejecutar(0)
        def contar(w):
            return 1 + sum(contar(h) for h in w.winfo_children())
        widgets = contar(self.sim)
        ids = [id(w) for w in (self.sim.canvas, self.sim.tabla, self.sim.texto_explicacion, self.sim.texto_resultado,
                               self.sim.encabezado_ruta, self.sim.encabezado_estado, self.sim.panel)]
        for _ in range(8):
            self.sim._siguiente()
            self.app.update()
        for _ in range(8):
            self.sim._anterior()
            self.app.update()
        self.assertEqual(widgets, contar(self.sim))
        self.assertEqual(ids, [id(w) for w in (self.sim.canvas, self.sim.tabla, self.sim.texto_explicacion,
                                               self.sim.texto_resultado, self.sim.encabezado_ruta,
                                               self.sim.encabezado_estado, self.sim.panel)])

    def test_el_resultado_del_algoritmo_no_cambia_con_la_nueva_interfaz(self):
        from core.dijkstra_engine import ejecutar_dijkstra
        self.ejecutar(0)
        r = ejecutar_dijkstra(self.sim.grafo, self.sim.menu_origen.get(), self.sim.menu_destino.get())
        self.assertEqual(self.sim.resultado.caminos, r.caminos)
        self.assertEqual(self.sim.resultado.distancia, r.distancia)
        self.assertEqual(self.sim.resultado.snapshots, r.snapshots)

    def test_el_cuadro_de_resultado_del_panel_conserva_su_contenido(self):
        self.ejecutar(0)
        self.assertIn("La simulación está en curso", self.sim.texto_resultado.get("1.0", "end"))
        self.sim._finalizar()
        t = self.sim.texto_resultado.get("1.0", "end")
        self.assertIn(f"Distancia mínima: {int(self.sim.resultado.distancia)}", t)
        for camino in self.sim.resultado.caminos:
            self.assertIn(" → ".join(camino), t)


class TestTecladoYTabla(Base):
    def _tecla(self, widget, tecla):
        widget.focus_force()
        self.app.update()
        widget.event_generate(f"<{tecla}>")
        self.app.update()

    def test_una_pulsacion_avanza_un_solo_paso_con_el_foco_en_el_canvas(self):
        self.ejecutar(0)
        for foco in (self.sim.canvas.canvas, self.app):
            self.sim.simulacion.indice = 3
            self.sim._refrescar()
            self._tecla(foco, "Right")
            self.assertEqual(self.sim.simulacion.indice, 4, foco)
            self._tecla(foco, "Left")
            self.assertEqual(self.sim.simulacion.indice, 3, foco)
            self._tecla(foco, "Down")
            self.assertEqual(self.sim.simulacion.indice, 4, foco)
            self._tecla(foco, "Up")
            self.assertEqual(self.sim.simulacion.indice, 3, foco)

    def test_tras_arrastrar_un_nodo_las_flechas_siguen_moviendo_un_paso(self):
        self.ejecutar(0)
        c = self.sim.canvas
        v = self.sim.grafo.vertices[0]
        x, y = c._posiciones[v]
        for tipo, dx in (("<ButtonPress-1>", 0), ("<B1-Motion>", 15), ("<ButtonRelease-1>", 15)):
            c.canvas.event_generate(tipo, x=int(x + dx), y=int(y))
        self.sim.simulacion.indice = 2
        self.sim._refrescar()
        self._tecla(c.canvas, "Right")
        self.assertEqual(self.sim.simulacion.indice, 3)

    def test_las_flechas_no_hacen_nada_sin_simulacion_ni_en_los_extremos(self):
        self._tecla(self.sim.canvas.canvas, "Right")
        self.assertIsNone(self.sim.simulacion)
        self.ejecutar(0)
        self._tecla(self.sim.canvas.canvas, "Left")
        self.assertEqual(self.sim.simulacion.indice, 0)
        self.sim._finalizar()
        ultimo = self.sim.simulacion.indice
        self._tecla(self.sim.canvas.canvas, "Right")
        self.assertEqual(self.sim.simulacion.indice, ultimo)

    def test_la_tabla_se_vacia_al_cambiar_origen_o_destino(self):
        for cambiar in ("origen", "destino"):
            self.ejecutar(0)
            self.sim._finalizar()
            llenas = [c for c in self.sim.tabla._celdas.values() if c.cget("text")]
            self.assertGreater(len(llenas), 0)
            vertices = self.sim.grafo.vertices
            menu = self.sim.menu_origen if cambiar == "origen" else self.sim.menu_destino
            menu.set(vertices[1] if menu.get() != vertices[1] else vertices[2])
            self.sim._al_cambiar_extremos()
            self.app.update()
            self.assertEqual(self.sim.tabla._celdas, {}, cambiar)
            self.assertEqual(self.sim.tabla._cabeceras, [], cambiar)
            self.assertIsNone(self.sim.tabla._ultimo_snapshot)
            self.assertEqual(self.sim.tabla._interior.winfo_children(), [])

    def test_tras_limpiar_se_puede_ejecutar_de_nuevo_con_una_tabla_nueva(self):
        self.ejecutar(0)
        self.sim._finalizar()
        self.sim._al_cambiar_extremos()
        self.ejecutar(2)
        self.assertEqual(len(self.sim.tabla._celdas), self.sim.grafo.n * (self.sim.grafo.n + 1))
        self.assertTrue(any(c.cget("text") for c in self.sim.tabla._celdas.values()))

    def test_cambiar_de_tema_con_la_tabla_vacia_no_falla(self):
        self.ejecutar(0)
        self.sim._al_cambiar_extremos()
        self.app._alternar_tema()
        self.app._alternar_tema()
        self.app.update()


class TestDialogoDeConfirmacion(Base):
    def _abrir_dialogo(self):
        self.sim._volver()  # grafo con aristas: pide confirmación
        self.app.update()
        return self.sim.dialogo_confirmacion

    def test_el_dialogo_tiene_borde_visible_y_color_propio_en_ambos_temas(self):
        for _ in range(2):
            d = self._abrir_dialogo()
            tarjeta = d.etiqueta_titulo.master
            self.assertEqual(int(tarjeta.cget("border_width")), 2)
            borde, fondo = theme.resolver(theme.DIALOGO_BORDE), theme.resolver(theme.DIALOGO_FONDO)
            # distinto del fondo de pantalla, de los paneles y de la tarjeta del tutorial
            for otro in (theme.FONDO, theme.PANEL, theme.PANEL_SUAVE, theme.TUTORIAL_FONDO, theme.TUTORIAL_CAJA):
                self.assertNotEqual(fondo, theme.resolver(otro))
            self.assertNotEqual(borde, theme.resolver(theme.BORDE))
            self.assertNotEqual(borde, theme.resolver(theme.RESALTE))
            self.assertIn(tarjeta.cget("border_color"), (theme.DIALOGO_BORDE, list(theme.DIALOGO_BORDE)))
            d._cancelar()
            self.app.update()
            self.app._alternar_tema()
            self.app.update()

    def test_el_dialogo_del_editor_manual_usa_el_mismo_estilo(self):
        self.app.iniciar_manual(8)
        self.app.update()
        e = self.app.pantalla
        v = e.grafo.vertices
        e._al_hacer_clic_en_nodo(v[0])
        e._al_hacer_clic_en_nodo(v[1])
        e.entrada_peso.insert(0, "3")
        e._crear_arista()
        e._volver()
        self.app.update()
        tarjeta = e.dialogo_confirmacion.etiqueta_titulo.master
        self.assertEqual(int(tarjeta.cget("border_width")), 2)
        self.assertIn(tarjeta.cget("fg_color"), (theme.DIALOGO_FONDO, list(theme.DIALOGO_FONDO)))
        e.dialogo_confirmacion._cancelar()


if __name__ == "__main__":
    unittest.main()
