"""Modo tutorial: recorrido guiado sin alterar la aplicación."""

import random
import time
import unittest

try:
    import customtkinter as ctk
    from core.generator import generar_dag
    from ui import theme
    from ui.app import App, PantallaBienvenida, PantallaConfiguracion
    from ui.editor import PantallaEditor
    from ui.simulation import PantallaSimulacion
    from ui.tutorial import ANCHO_TARJETA, BORDE_VENTANA, GROSOR, colocar_tarjeta
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


class TestColocarTarjeta(unittest.TestCase):
    """La colocación es una función pura: no necesita pantalla."""

    @classmethod
    def setUpClass(cls):
        if not HAY_UI:
            raise unittest.SkipTest("Requiere Tkinter")

    def test_sin_elemento_la_tarjeta_se_centra(self):
        x, y = colocar_tarjeta(None, 300, 200, (1000, 800))
        self.assertEqual((x, y), (350, 300))

    def test_prefiere_la_derecha_sin_tapar_el_elemento(self):
        x, y = colocar_tarjeta((100, 100, 200, 160), 300, 200, (1000, 800))
        self.assertGreaterEqual(x, 200)

    def test_si_no_cabe_a_la_derecha_va_a_la_izquierda_o_debajo(self):
        rect = (700, 300, 980, 360)
        x, y = colocar_tarjeta(rect, 300, 200, (1000, 800))
        self.assertTrue(x + 300 <= rect[0] or y >= rect[3] or y + 200 <= rect[1])

    def test_nunca_se_sale_de_la_ventana_aunque_el_elemento_sea_enorme(self):
        for rect in [(0, 0, 1000, 800), (0, 0, 50, 800), (950, 700, 1000, 800), (400, 300, 600, 500)]:
            x, y = colocar_tarjeta(rect, 390, 420, (1000, 800))
            self.assertGreaterEqual(x, BORDE_VENTANA)
            self.assertGreaterEqual(y, BORDE_VENTANA)
            self.assertLessEqual(x + 390, 1000 - BORDE_VENTANA)
            self.assertLessEqual(y + 420, 800 - BORDE_VENTANA)

    def test_con_un_elemento_enorme_elige_el_menor_solape(self):
        rect = (0, 0, 1000, 600)
        x, y = colocar_tarjeta(rect, 300, 150, (1000, 800))
        self.assertGreaterEqual(y, 600)  # hay franja libre debajo


@unittest.skipUnless(_hay_pantalla(), "Requiere Tkinter y un display disponible")
class Base(unittest.TestCase):
    GEOMETRIA = "1320x860+0+0"

    def setUp(self):
        self.app = App()
        self.app.geometry(self.GEOMETRIA)
        self.app.update()

    def tearDown(self):
        theme.aplicar_modo("claro")
        ctk.set_appearance_mode("light")
        self.app.destroy()

    def abrir_simulacion(self, n=10, semilla=5):
        self.app.mostrar_simulacion(*generar_dag(n, rng=random.Random(semilla)))
        self.app.update()
        self.sim = self.app.pantalla
        return self.sim

    def abrir_tutorial(self):
        self.app.iniciar_tutorial()
        self.app.update()
        return self.app.tutorial

    def caja(self, widget):
        """Caja de ``widget`` en coordenadas de la ventana raíz."""
        r = self.app
        return (widget.winfo_rootx() - r.winfo_rootx(), widget.winfo_rooty() - r.winfo_rooty(),
                widget.winfo_rootx() - r.winfo_rootx() + widget.winfo_width(),
                widget.winfo_rooty() - r.winfo_rooty() + widget.winfo_height())

    def caja_tarjeta(self):
        t = self.app.tutorial.tarjeta
        t.update_idletasks()
        return (t.winfo_x(), t.winfo_y(), t.winfo_x() + t.winfo_reqwidth(), t.winfo_y() + t.winfo_reqheight())

    @staticmethod
    def solape(a, b):
        return max(min(a[2], b[2]) - max(a[0], b[0]), 0) * max(min(a[3], b[3]) - max(a[1], b[1]), 0)


class TestBotonYCiclo(Base):
    def test_el_boton_tutorial_esta_en_el_encabezado_fijo_y_es_visible_en_todas_las_pantallas(self):
        b = self.app._boton_tutorial
        for abrir in (lambda: None, self.app.mostrar_configuracion, lambda: self.app.iniciar_manual(8),
                      lambda: self.abrir_simulacion()):
            abrir()
            self.app.update()
            self.assertTrue(b.winfo_viewable())
            self.assertIn("Tutorial", b.cget("text"))
            self.assertIs(b.master, self.app._encabezado)

    def test_cada_pantalla_tiene_su_recorrido(self):
        esperados = {
            PantallaBienvenida: lambda: None,
            PantallaConfiguracion: self.app.mostrar_configuracion,
            PantallaEditor: lambda: self.app.iniciar_manual(8),
            PantallaSimulacion: lambda: self.abrir_simulacion(),
        }
        for clase, abrir in esperados.items():
            abrir()
            self.app.update()
            self.assertIsInstance(self.app.pantalla, clase)
            t = self.abrir_tutorial()
            self.assertTrue(t.activo)
            self.assertGreaterEqual(len(t.pasos), 3)
            self.assertEqual(t.etiqueta_progreso.cget("text"), f"Paso 1 de {len(t.pasos)}")
            t.salir()
        self.assertEqual(len(__import__("ui.tutorial_pasos", fromlist=["x"]).pasos_simulacion(
            self.abrir_simulacion())), 16)

    def test_avanzar_retroceder_y_salir(self):
        self.abrir_simulacion()
        t = self.abrir_tutorial()
        total = len(t.pasos)
        self.assertEqual(t.boton_anterior.cget("state"), "disabled")
        t.boton_siguiente.invoke()
        t.boton_siguiente.invoke()
        self.assertEqual(t.indice, 2)
        self.assertEqual(t.etiqueta_progreso.cget("text"), f"Paso 3 de {total}")
        t.boton_anterior.invoke()
        self.assertEqual(t.indice, 1)
        self.assertEqual(t.etiqueta_titulo.cget("text"), t.pasos[1].titulo)
        t.boton_salir.invoke()
        self.assertFalse(t.activo)
        self.assertIsNone(t.tarjeta)
        self.assertEqual(t._filetes, [])

    def test_el_ultimo_paso_ofrece_finalizar_y_cierra(self):
        self.abrir_simulacion()
        t = self.abrir_tutorial()
        for _ in range(len(t.pasos) - 1):
            t.boton_siguiente.invoke()
        self.assertIn("Finalizar", t.boton_siguiente.cget("text"))
        t.boton_siguiente.invoke()
        self.assertFalse(t.activo)

    def test_se_puede_repetir_y_pulsar_el_boton_con_el_tutorial_abierto_lo_reinicia(self):
        self.abrir_simulacion()
        for _ in range(3):
            t = self.abrir_tutorial()
            self.assertEqual(t.indice, 0)
            t.siguiente()
            t.siguiente()
            self.app._boton_tutorial.invoke()  # con el tutorial abierto: vuelve al paso 1
            self.app.update()
            self.assertEqual(t.indice, 0)
            self.assertTrue(t.activo)
            t.salir()
            self.assertFalse(t.activo)

    def test_cambiar_de_pantalla_cierra_el_tutorial_sin_dejar_widgets(self):
        self.abrir_simulacion()
        t = self.abrir_tutorial()
        tarjeta = t.tarjeta
        self.app.mostrar_configuracion()
        self.app.update()
        self.assertFalse(t.activo)
        self.assertFalse(tarjeta.winfo_exists())
        self.assertIsNone(t._after)

    def test_cerrar_el_tutorial_no_deja_temporizadores_pendientes(self):
        self.abrir_simulacion()
        t = self.abrir_tutorial()
        self.assertIsNotNone(t._after)
        t.salir()
        self.assertIsNone(t._after)

    def test_la_aplicacion_recupera_su_funcionamiento_normal_al_salir(self):
        sim = self.abrir_simulacion()
        t = self.abrir_tutorial()
        t.salir()
        sim._ejecutar()
        sim._siguiente()
        self.app.update()
        self.assertEqual(sim.simulacion.indice, 1)


class TestSimulacionNoAlterada(Base):
    def estado(self, sim):
        def contar(w):
            return 1 + sum(contar(h) for h in w.winfo_children())
        return dict(
            indice=sim.simulacion.indice if sim.simulacion else None,
            resultado=id(sim.resultado),
            simulacion=id(sim.simulacion),
            explicacion=sim.texto_explicacion.get("1.0", "end"),
            resultado_texto=sim.texto_resultado.get("1.0", "end"),
            encabezado=(sim.encabezado_ruta.cget("text"), sim.encabezado_estado.cget("text")),
            paso=sim.etiqueta_paso.cget("text"),
            origen=sim.menu_origen.get(), destino=sim.menu_destino.get(),
            widgets=contar(sim), pantalla=id(self.app.pantalla),
            nodos=sim.canvas.obtener_posiciones(),
            detalles=sim._ventana_detalles,
        )

    def recorrer_todo(self):
        t = self.abrir_tutorial()
        for _ in range(len(t.pasos) - 1):
            t.siguiente()
            self.app.update()
        for _ in range(len(t.pasos) - 1):
            t.anterior()
            self.app.update()
        t.salir()
        self.app.update()

    def test_una_simulacion_en_curso_no_cambia_de_paso_ni_se_reinicia(self):
        sim = self.abrir_simulacion()
        sim._ejecutar()
        for _ in range(5):
            sim._siguiente()
        self.app.update()
        antes = self.estado(sim)
        self.recorrer_todo()
        self.assertEqual(antes, self.estado(sim))

    def test_una_simulacion_terminada_se_conserva(self):
        sim = self.abrir_simulacion()
        sim._ejecutar()
        sim._finalizar()
        self.app.update()
        antes = self.estado(sim)
        self.recorrer_todo()
        self.assertEqual(antes, self.estado(sim))

    def test_sin_ejecutar_el_tutorial_no_ejecuta_nada(self):
        sim = self.abrir_simulacion()
        antes = self.estado(sim)
        self.recorrer_todo()
        self.assertIsNone(sim.simulacion)
        self.assertIsNone(sim.resultado)
        self.assertEqual(antes, self.estado(sim))
        self.assertEqual(sim.boton_siguiente.cget("state"), "disabled")

    def test_los_ejemplos_usan_el_resultado_de_la_simulacion_en_curso(self):
        sim = self.abrir_simulacion()
        sim._ejecutar()
        t = self.abrir_tutorial()
        t.ir_a(len(t.pasos) - 1)
        texto = t.etiqueta_ejemplo.cget("text")
        self.assertIn(f"{int(sim.resultado.distancia)}", texto)
        for camino in sim.resultado.caminos:
            self.assertIn(" → ".join(camino), texto)

    def test_el_tutorial_no_abre_ni_cierra_la_ventana_mas_detalles(self):
        sim = self.abrir_simulacion()
        sim._ejecutar()
        sim._abrir_detalles()
        ventana = sim._ventana_detalles
        self.recorrer_todo()
        self.assertIs(sim._ventana_detalles, ventana)
        self.assertTrue(ventana.winfo_exists())

    def test_cambiar_origen_o_destino_con_el_tutorial_abierto_funciona_y_sus_ejemplos_se_adaptan(self):
        sim = self.abrir_simulacion()
        t = self.abrir_tutorial()
        t.ir_a(len(t.pasos) - 1)
        antes = t.etiqueta_ejemplo.cget("text")
        sim.menu_destino.set(sim.grafo.vertices[1])
        sim.menu_origen.set(sim.grafo.vertices[0])
        sim._al_cambiar_extremos()
        t.ir_a(len(t.pasos) - 1)
        self.app.update()
        self.assertTrue(t.activo)
        self.assertEqual(sim.encabezado_ruta.cget("text"),
                         f"Camino mínimo:  {sim.grafo.vertices[0]} → {sim.grafo.vertices[1]}")
        self.assertTrue(t.etiqueta_ejemplo.cget("text"))
        self.assertNotEqual(t.etiqueta_ejemplo.cget("text"), antes)


class TestResaltadoCorrecto(Base):
    def _verificar(self, pasos_esperados):
        t = self.app.tutorial
        for titulo, widgets in pasos_esperados.items():
            indice = next(i for i, p in enumerate(t.pasos) if p.titulo == titulo)
            t.ir_a(indice)
            self.app.update()
            rect = t.rect_resaltado()
            self.assertIsNotNone(rect, titulo)
            esperado = [self.caja(w) for w in widgets]
            union = (min(c[0] for c in esperado), min(c[1] for c in esperado),
                     max(c[2] for c in esperado), max(c[3] for c in esperado))
            # el rectángulo resaltado es la unión de los widgets (recortada a la vista)
            self.assertLessEqual(abs(rect[0] - union[0]), 1, titulo)
            self.assertLessEqual(abs(rect[2] - union[2]), 1, titulo)
            self.assertGreaterEqual(rect[3] - rect[1], 1, titulo)
            self.assertLessEqual(rect[1], union[3], titulo)
            self.assertGreaterEqual(rect[3], union[1], titulo)
            # los cuatro filetes rodean exactamente ese rectángulo
            f = t._filetes
            self.assertTrue(all(x.winfo_ismapped() for x in f), titulo)
            self.assertEqual(f[0].winfo_x(), rect[0] - 4)
            self.assertEqual(f[0].winfo_y(), rect[1] - 4)
            self.assertEqual(f[1].winfo_y() + GROSOR, rect[3] + 4)
            self.assertEqual(f[2].winfo_x(), rect[0] - 4)
            self.assertEqual(f[3].winfo_x() + GROSOR, rect[2] + 4)

    def test_los_pasos_de_la_simulacion_resaltan_los_componentes_correctos(self):
        sim = self.abrir_simulacion()
        self.abrir_tutorial()
        self._verificar({
            "Bienvenido a la simulación": [sim.barra_superior],
            "Crear o generar otro grafo": [sim.boton_volver],
            "Origen y destino": [sim.marco_extremos],
            "Iniciar la simulación": [sim.boton_ejecutar],
            "Avanzar y retroceder": [sim.barra_navegacion],
            "Más detalles": [sim.boton_detalles],
        })

    def test_los_pasos_de_pantallas_previas_y_editor(self):
        self.app.mostrar_configuracion()
        self.app.update()
        c = self.app.pantalla
        self.abrir_tutorial()
        self._verificar({"Número de vértices": [c.marco_nodos], "Generar automáticamente": [c.tarjeta_auto],
                         "Crear manualmente": [c.tarjeta_manual]})
        self.app.iniciar_manual(8)
        self.app.update()
        e = self.app.pantalla
        self.abrir_tutorial()
        self._verificar({"El área de construcción": [e.canvas], "Aristas del grafo": [e.lista_aristas],
                         "Restablecer posiciones": [e.boton_restablecer],
                         "Finalizar el grafo": [e.boton_finalizar_grafo]})

    def test_el_resalte_combinado_cubre_todos_sus_componentes(self):
        sim = self.abrir_simulacion()
        t = self.abrir_tutorial()
        i = next(i for i, p in enumerate(t.pasos) if p.titulo == "Explicación de cada paso")
        t.ir_a(i)
        self.app.update()
        rect = t.rect_resaltado()
        for w in (sim.titulo_paso, sim.fila_subpaso, sim.texto_explicacion):
            c = self.caja(w)
            self.assertLessEqual(rect[0], c[0] + 1)
            self.assertGreaterEqual(rect[2], c[2] - 1)
            self.assertLessEqual(rect[1], c[1] + 1)
            self.assertGreaterEqual(rect[3], c[3] - 1)

    def test_el_resalte_es_ancho_de_la_pagina_visible_aunque_haya_que_desplazar(self):
        self.app.geometry("1100x760+0+0")
        self.app.update()
        sim = self.abrir_simulacion()
        t = self.abrir_tutorial()
        i = next(i for i, p in enumerate(t.pasos) if p.titulo == "Tabla del proceso")
        t.ir_a(i)
        self.app.update()
        rect = t.rect_resaltado()
        pag = self.caja(sim.pagina._lienzo)
        self.assertIsNotNone(rect)
        self.assertGreaterEqual(rect[1], pag[1])
        self.assertLessEqual(rect[3], pag[3])

    def test_un_elemento_oculto_no_se_resalta_y_se_avisa(self):
        sim = self.abrir_simulacion()
        sim._alternar_tabla()  # el usuario ocultó la tabla
        self.app.update()
        t = self.abrir_tutorial()
        i = next(i for i, p in enumerate(t.pasos) if p.titulo == "Tabla del proceso")
        t.ir_a(i)
        self.app.update()
        self.assertIsNone(t.rect_resaltado())
        self.assertTrue(all(not f.winfo_ismapped() for f in t._filetes))
        self.assertIn("no está visible", t.etiqueta_aviso.cget("text"))
        self.assertTrue(t.tarjeta.winfo_ismapped())
        self.assertFalse(sim.tabla_visible)


class TestTarjetaCompleta(Base):
    def _revisar_todo(self):
        for clase, abrir in (
            ("bienvenida", lambda: self.app.mostrar_bienvenida()),
            ("configuracion", lambda: self.app.mostrar_configuracion()),
            ("editor", lambda: self.app.iniciar_manual(8)),
            ("simulacion", lambda: self.abrir_simulacion()),
        ):
            abrir()
            self.app.update()
            t = self.abrir_tutorial()
            W, H = self.app.winfo_width(), self.app.winfo_height()
            for i in range(len(t.pasos)):
                t.ir_a(i)
                self.app.update()
                c = self.caja_tarjeta()
                msg = (clase, i, t.pasos[i].titulo, c, (W, H))
                self.assertGreaterEqual(c[0], BORDE_VENTANA - 1, msg)
                self.assertGreaterEqual(c[1], BORDE_VENTANA - 1, msg)
                self.assertLessEqual(c[2], W - BORDE_VENTANA + 1, msg)
                self.assertLessEqual(c[3], H - BORDE_VENTANA + 1, msg)
                self.assertTrue(t.tarjeta.winfo_ismapped(), msg)
                self.assertEqual(t.tarjeta.winfo_reqwidth(), ANCHO_TARJETA, msg)
                # el texto no se corta: cada etiqueta cabe entera en la tarjeta
                for et in (t.etiqueta_titulo, t.etiqueta_texto):
                    self.assertLessEqual(et.winfo_reqheight(), t.tarjeta.winfo_reqheight(), msg)
                # no tapa el elemento resaltado cuando hay sitio de sobra
                rect = t.rect_resaltado()
                if rect is not None and (rect[2] - rect[0]) * (rect[3] - rect[1]) < 0.25 * W * H:
                    self.assertEqual(self.solape(c, rect), 0, msg)
            t.salir()

    def test_la_tarjeta_cabe_en_la_ventana_normal_y_en_la_minima_en_ambos_temas(self):
        for geometria in ("1320x860+0+0", "1100x760+0+0"):
            for oscuro in (False, True):
                self.app.geometry(geometria)
                self.app.update()
                if oscuro != theme.es_oscuro():
                    self.app._alternar_tema()
                    self.app.update()
                self._revisar_todo()


@unittest.skipUnless(_hay_pantalla(), "Requiere Tkinter y un display disponible")
class TestEscalaDeWindows(unittest.TestCase):
    """Con el escalado de pantalla de Windows (125 %, 150 %…) la tarjeta no debe salirse de la ventana."""

    def tearDown(self):
        theme.aplicar_modo("claro")
        ctk.set_appearance_mode("light")
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)

    def _comprobar(self, escala):
        ctk.set_widget_scaling(escala)
        ctk.set_window_scaling(escala)
        app = App()
        try:
            app.geometry("1300x860+0+0")
            app.update()
            for abrir in (lambda: app.mostrar_configuracion(), lambda: app.iniciar_manual(8),
                          lambda: app.mostrar_simulacion(*generar_dag(10, rng=random.Random(5)))):
                abrir()
                app.update()
                app.iniciar_tutorial()
                app.update()
                t = app.tutorial
                W, H = app.winfo_width(), app.winfo_height()
                for i in range(len(t.pasos)):
                    t.ir_a(i)
                    app.update()
                    x, y = t.tarjeta.winfo_x(), t.tarjeta.winfo_y()
                    w, h = t.tarjeta.winfo_width(), t.tarjeta.winfo_height()
                    msg = (escala, type(app.pantalla).__name__, i, (x, y, w, h), (W, H))
                    self.assertTrue(x >= 0 and y >= 0 and x + w <= W and y + h <= H, msg)
                t.salir()
        finally:
            app.destroy()

    def test_la_tarjeta_cabe_con_escalado_125_y_150(self):
        for escala in (1.25, 1.5):
            self._comprobar(escala)


class TestAspectoDeLaTarjeta(Base):
    def test_la_tarjeta_se_distingue_del_blanco_de_la_pantalla_en_ambos_temas(self):
        self.abrir_simulacion()
        t = self.abrir_tutorial()
        for _ in range(2):
            fondo = theme.resolver(theme.TUTORIAL_FONDO)
            self.assertNotEqual(fondo, theme.resolver(theme.PANEL))
            self.assertNotEqual(fondo, theme.resolver(theme.FONDO))
            self.assertNotEqual(theme.resolver(theme.TUTORIAL_CAJA), theme.resolver(theme.PANEL_SUAVE))
            self.assertIn(t.tarjeta.cget("fg_color"), (theme.TUTORIAL_FONDO, list(theme.TUTORIAL_FONDO)))
            self.app._alternar_tema()
            self.app.update()


class TestEstabilidadDeLaTarjeta(Base):
    """La tarjeta no debe saltar mientras la ventana se oculta o se redibuja (p. ej. al cambiar de tema)."""

    def _posicion(self, t):
        return (t.tarjeta.winfo_x(), t.tarjeta.winfo_y(), t.rect_resaltado())

    def _esperar(self, segundos=0.6):
        fin = time.time() + segundos
        while time.time() < fin:
            self.app.update()
            time.sleep(0.02)

    def test_ocultar_y_mostrar_la_ventana_no_recoloca_la_tarjeta(self):
        self.abrir_simulacion()
        t = self.abrir_tutorial()
        for paso in (1, 4, 10):
            t.ir_a(paso)
            self.app.update()
            antes = self._posicion(t)
            self.app.withdraw()
            muestras = set()
            fin = time.time() + 0.5
            while time.time() < fin:
                self.app.update()
                muestras.add((t.tarjeta.winfo_x(), t.tarjeta.winfo_y()))
                time.sleep(0.02)
            self.app.deiconify()
            self._esperar(0.4)
            self.assertEqual(muestras, {antes[:2]}, paso)
            self.assertEqual(self._posicion(t), antes, paso)

    def test_cambiar_de_tema_nunca_mueve_la_tarjeta(self):
        self.abrir_simulacion()
        t = self.abrir_tutorial()
        for paso in range(len(t.pasos)):
            t.ir_a(paso)
            self.app.update()
            antes = self._posicion(t)
            muestras = set()
            self.app._alternar_tema()
            fin = time.time() + 0.35
            while time.time() < fin:
                self.app.update()
                muestras.add((t.tarjeta.winfo_x(), t.tarjeta.winfo_y()))
                time.sleep(0.02)
            self.assertEqual(muestras, {antes[:2]}, paso)
            self.assertEqual(self._posicion(t), antes, paso)

    def test_un_elemento_que_se_oculta_de_verdad_se_acepta_pasado_un_momento(self):
        sim = self.abrir_simulacion()
        t = self.abrir_tutorial()
        t.ir_a(next(i for i, p in enumerate(t.pasos) if p.titulo == "Tabla del proceso"))
        self.app.update()
        self.assertIsNotNone(t.rect_resaltado())
        sim._alternar_tabla()
        self._esperar(1.0)
        self.assertIsNone(t.rect_resaltado())
        self.assertTrue(all(not f.winfo_ismapped() for f in t._filetes))
        self.assertIn("no está visible", t.etiqueta_aviso.cget("text"))


class TestTextosDelTutorial(Base):
    def test_los_colores_citados_existen_en_la_leyenda_o_se_aclara_que_no(self):
        from ui.simulation import _leyenda
        sim = self.abrir_simulacion()
        t = self.abrir_tutorial()
        paso = next(p for p in t.pasos if p.titulo == "Etiquetas, pesos y conexiones")
        texto = paso.texto
        entradas = [e.lower() for _, e in _leyenda()]
        self.assertEqual(entradas, ["origen", "destino", "actual", "visitado", "arista evaluada", "empate", "camino"])
        for palabra in ("origen", "destino", "actual", "visitado", "arista evaluada", "empate"):
            self.assertIn(palabra, texto.lower())
        # el rojo (arista que no mejora) no está en la leyenda y el texto lo dice
        self.assertIn("roja", texto)
        self.assertIn("no aparece en la leyenda", texto)
        # y no se atribuye al rojo un lugar en la leyenda ni se llama «mejora» al ámbar
        self.assertNotIn("ámbar = mejora", texto)
        self.assertNotIn("rojo = no mejora", texto)


class TestTemaYVentana(Base):
    def test_cambiar_de_tema_con_el_tutorial_abierto_conserva_paso_y_estado(self):
        sim = self.abrir_simulacion()
        sim._ejecutar()
        sim._siguiente()
        t = self.abrir_tutorial()
        t.ir_a(4)
        indice_sim = sim.simulacion.indice
        for _ in range(3):
            self.app._alternar_tema()
            self.app.update()
            self.assertTrue(t.activo)
            self.assertEqual(t.indice, 4)
            self.assertEqual(sim.simulacion.indice, indice_sim)
            self.assertEqual(t._filetes[0].cget("bg"), theme.resolver(theme.RESALTE))
        self.assertEqual(t._filetes[0].cget("bg"), theme.resolver(theme.RESALTE))

    def test_los_filetes_cambian_de_color_entre_claro_y_oscuro(self):
        self.abrir_simulacion()
        t = self.abrir_tutorial()
        c1 = t._filetes[0].cget("bg")
        self.app._alternar_tema()
        self.app.update()
        c2 = t._filetes[0].cget("bg")
        self.assertNotEqual(c1, c2)
        self.assertEqual(c2, theme.resolver(theme.RESALTE))

    def test_el_resalte_sigue_al_elemento_si_se_redimensiona_la_ventana(self):
        sim = self.abrir_simulacion()
        t = self.abrir_tutorial()
        i = next(i for i, p in enumerate(t.pasos) if p.titulo == "Iniciar la simulación")
        t.ir_a(i)
        self.app.update()
        antes = t.rect_resaltado()
        self.app.geometry("1500x900+0+0")
        self.app.update()
        time.sleep(0.3)
        self.app.update()
        despues = t.rect_resaltado()
        self.assertNotEqual(antes, despues)
        f = t._filetes[0]
        self.assertEqual((f.winfo_x(), f.winfo_y()), (despues[0] - 4, despues[1] - 4))
        c = self.caja(sim.boton_ejecutar)
        self.assertLessEqual(abs(despues[0] - c[0]), 1)

    def test_el_resalte_sigue_a_la_pagina_cuando_se_desplaza(self):
        self.app.geometry("1100x760+0+0")
        self.app.update()
        sim = self.abrir_simulacion()
        t = self.abrir_tutorial()
        i = next(i for i, p in enumerate(t.pasos) if p.titulo == "Resultado")
        t.ir_a(i)
        self.app.update()
        sim.pagina.ir_al_principio()
        self.app.update()
        time.sleep(0.3)
        self.app.update()
        a = t.rect_resaltado()
        sim.pagina.ir_al_final()
        self.app.update()
        time.sleep(0.3)
        self.app.update()
        b = t.rect_resaltado()
        if sim.pagina.desbordada:
            self.assertNotEqual(a, b)


class TestNoInterfiereConLaEdicion(Base):
    def test_se_puede_editar_el_grafo_con_el_tutorial_abierto(self):
        self.app.iniciar_manual(8)
        self.app.update()
        e = self.app.pantalla
        t = self.abrir_tutorial()
        t.ir_a(1)
        self.assertEqual(e.grafo.cantidad_aristas(), 0)
        v = e.grafo.vertices
        e._al_hacer_clic_en_nodo(v[0])
        e._al_hacer_clic_en_nodo(v[1])
        e.entrada_peso.insert(0, "4")
        e._crear_arista()
        self.app.update()
        self.assertEqual(e.grafo.cantidad_aristas(), 1)
        self.assertEqual(e.grafo.peso(v[0], v[1]), 4)
        self.assertTrue(t.activo)
        # al salir, la edición sigue funcionando y lo creado se conserva
        t.salir()
        e._al_hacer_clic_en_nodo(v[1])
        e._al_hacer_clic_en_nodo(v[2])
        e.entrada_peso.insert(0, "7")
        e._crear_arista()
        self.assertEqual(e.grafo.cantidad_aristas(), 2)

    def test_la_seleccion_en_curso_del_editor_no_se_pierde_al_recorrer_el_tutorial(self):
        self.app.iniciar_manual(8)
        self.app.update()
        e = self.app.pantalla
        v = e.grafo.vertices
        e._al_hacer_clic_en_nodo(v[0])
        e._al_hacer_clic_en_nodo(v[3])
        e.entrada_peso.insert(0, "12")
        t = self.abrir_tutorial()
        for _ in range(len(t.pasos) - 1):
            t.siguiente()
        t.salir()
        self.assertEqual((e.origen_arista, e.destino_arista), (v[0], v[3]))
        self.assertEqual(e.entrada_peso.get(), "12")

    def test_el_editor_responde_a_su_pantalla_finalizar_desde_el_tutorial_cerrado(self):
        self.app.iniciar_manual(8)
        e = self.app.pantalla
        v = e.grafo.vertices
        e._al_hacer_clic_en_nodo(v[0])
        e._al_hacer_clic_en_nodo(v[1])
        e.entrada_peso.insert(0, "2")
        e._crear_arista()
        t = self.abrir_tutorial()
        e._finalizar()  # el usuario pasa a simular con el tutorial abierto
        self.app.update()
        if e.dialogo_confirmacion is not None and e.dialogo_confirmacion.winfo_exists():
            e.dialogo_confirmacion._confirmar()  # grafo con vértices aislados: se acepta el aviso
            self.app.update()
        self.assertFalse(t.activo)
        self.assertIsInstance(self.app.pantalla, PantallaSimulacion)

    def test_la_rueda_sobre_la_tarjeta_no_desplaza_la_pagina(self):
        from types import SimpleNamespace
        self.app.geometry("1100x760+0+0")
        self.app.update()
        sim = self.abrir_simulacion()
        t = self.abrir_tutorial()
        self.app.update()
        t.tarjeta.update_idletasks()
        y = sim.pagina._lienzo.yview()
        ev = SimpleNamespace(x_root=t.tarjeta.winfo_rootx() + 20, y_root=t.tarjeta.winfo_rooty() + 20,
                             delta=-120, num=None, state=0)
        sim.pagina.desplazar_con_rueda(ev)
        self.assertEqual(sim.pagina._lienzo.yview(), y)


class TestEncabezadoYMejorasPrevias(Base):
    def test_las_mejoras_anteriores_siguen_funcionando_con_el_tutorial_abierto(self):
        sim = self.abrir_simulacion()
        self.abrir_tutorial()
        sim._ejecutar()
        sim._siguiente()
        sim._abrir_detalles()
        self.app.update()
        marcas = sorted(sim.canvas.canvas.itemcget(i, "text") for i in sim.canvas.canvas.find_withtag("marca")
                        if sim.canvas.canvas.type(i) == "text")
        self.assertEqual(marcas, ["DESTINO", "ORIGEN"])
        self.assertTrue(sim._ventana_detalles.winfo_exists())
        self.assertIn("Distancia a", sim.encabezado_estado.cget("text"))
        self.app._alternar_tema()
        self.app.update()
        self.assertTrue(self.app.tutorial.activo)


if __name__ == "__main__":
    unittest.main()
