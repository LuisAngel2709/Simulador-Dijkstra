"""Pantalla 3 — Simulación paso a paso del algoritmo de Dijkstra.

La pantalla solo navega entre snapshots producidos por el Core: nunca recalcula
ni deshace operaciones. `Anterior` se limita a mostrar el snapshot previo.
"""

from __future__ import annotations

import customtkinter as ctk

from core.dijkstra_engine import (
    ACTUALIZACION,
    FINAL,
    INFINITO,
    INICIO,
    SELECCION,
    Simulacion,
    ejecutar_dijkstra,
    formato_distancia,
)
from core import explicaciones
from core.graph import GrafoError

from . import texto_rico, theme
from .detalles import VentanaDetalles
from .dialogs import DialogoConfirmacion
from .graph_canvas import GrafoCanvas
from .pagina_desplazable import PaginaDesplazable
from .table import TablaAlgoritmo

ALTO_CUERPO_MIN = 400    # alto mínimo de grafo + panel antes de que aparezca el desplazamiento
ANCHO_PANEL = 400

NOMBRE_SUBPASO = {
    INICIO: "Etiquetado inicial",
    SELECCION: "Subpaso 1 · Selección",
    ACTUALIZACION: "Subpaso 2 · Actualización",
    FINAL: "Fin de la simulación",
}

def _leyenda():
    """Genera la leyenda con los colores del tema activo."""
    return [
        (theme.NODO_ORIGEN, "Origen"),
        (theme.NODO_DESTINO, "Destino"),
        (theme.NODO_ACTUAL, "Actual"),
        (theme.NODO_VISITADO, "Visitado"),
        (theme.ARISTA_EVALUADA, "Arista evaluada"),
        (theme.ARISTA_EMPATE, "Empate"),
        (theme.ARISTA_CAMINO, "Camino"),
    ]


class PantallaSimulacion(ctk.CTkFrame):
    def __init__(
        self,
        master,
        grafo,
        origen_sugerido,
        destino_sugerido,
        al_volver,
        posiciones_iniciales=None,
        texto_volver="← Volver",
    ):
        """`al_volver` recibe las posiciones actuales de los nodos (normalizadas),
        para que quien reciba el control pueda conservar lo que el usuario movió."""
        super().__init__(master, fg_color=theme.FONDO)
        self.grafo = grafo
        self.al_volver = al_volver
        self.posiciones_iniciales = posiciones_iniciales
        self.texto_volver = texto_volver
        self.simulacion: Simulacion | None = None
        self.resultado = None
        self.dialogo_confirmacion: DialogoConfirmacion | None = None
        self.seleccion_manual: tuple[str, str] | None = None  # lo que el usuario eligió en los menús

        self._ventana_detalles: VentanaDetalles | None = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_barra_superior()
        # Grafo + panel + tabla viven en una página desplazable; la navegación entre
        # pasos queda fija debajo para estar siempre al alcance.
        self.pagina = PaginaDesplazable(self, al_cambiar_alto=self._ajustar_alto_cuerpo)
        self.pagina.grid(row=1, column=0, sticky="nsew")
        self.pagina.contenido.grid_columnconfigure(0, weight=1)
        self._construir_cuerpo()
        self._construir_tabla()
        self._construir_navegacion()
        self.pagina.registrar_texto(self.texto_explicacion)
        self.pagina.registrar_texto(self.texto_resultado)
        self.pagina.registrar_desplazable(self.tabla, self.tabla.desplazar)

        self.menu_origen.set(origen_sugerido)
        self.menu_destino.set(destino_sugerido)
        self.canvas.establecer_grafo(
            grafo,
            posiciones=posiciones_iniciales,
            modo_layout="circular" if posiciones_iniciales else "capas",
        )
        self._al_cambiar_extremos()
        self._configurar_atajos_teclado()

    # ---------------------------------------------------------------- construcción

    def _construir_barra_superior(self) -> None:
        barra = ctk.CTkFrame(self, fg_color=theme.PANEL, corner_radius=10, border_width=1, border_color=theme.BORDE)
        barra.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        barra.grid_columnconfigure(1, weight=1)
        self.barra_superior = barra

        self.boton_volver = ctk.CTkButton(
            barra, text=self.texto_volver, width=130, height=32, font=(theme.FAMILIA, 12, "bold"),
            command=self._volver,
            fg_color=theme.BOTON_SECUNDARIO, hover_color=theme.BOTON_SECUNDARIO_HOVER,
            text_color=theme.BOTON_SECUNDARIO_TEXTO, border_width=1, border_color=theme.BORDE,
        )
        self.boton_volver.grid(row=0, column=0, padx=12, pady=10)

        ctk.CTkLabel(
            barra, text="Simulación del algoritmo de Dijkstra",
            font=theme.FUENTE_SUBTITULO, text_color=theme.TEXTO,
        ).grid(row=0, column=1, sticky="w", padx=8)

        self.etiqueta_paso = ctk.CTkLabel(
            barra, text="", font=theme.FUENTE_NORMAL, text_color=theme.TEXTO_SUAVE
        )
        self.etiqueta_paso.grid(row=0, column=2, padx=14)

    def _construir_cuerpo(self) -> None:
        self.cuerpo = ctk.CTkFrame(self.pagina.contenido, fg_color="transparent", height=ALTO_CUERPO_MIN)
        self.cuerpo.grid(row=0, column=0, sticky="ew", padx=(16, 8))
        self.cuerpo.grid_propagate(False)
        self.cuerpo.grid_rowconfigure(0, weight=1)
        self.cuerpo.grid_columnconfigure(0, weight=1)

        izquierda = ctk.CTkFrame(self.cuerpo, fg_color="transparent")
        izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        izquierda.grid_rowconfigure(1, weight=1)
        izquierda.grid_columnconfigure(0, weight=1)

        self._construir_encabezado_grafo(izquierda)
        self.canvas = GrafoCanvas(izquierda)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self._construir_leyenda(izquierda)

        self._construir_panel_derecho(self.cuerpo)

    def _construir_encabezado_grafo(self, master) -> None:
        """Una sola fila, siempre del mismo alto: ruta a la izquierda, estado a la derecha."""
        encabezado = ctk.CTkFrame(master, fg_color="transparent")
        encabezado.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        encabezado.grid_columnconfigure(1, weight=1)
        self.encabezado_ruta = ctk.CTkLabel(
            encabezado, text="", font=theme.FUENTE_SUBTITULO, text_color=theme.TEXTO, anchor="w",
        )
        self.encabezado_ruta.grid(row=0, column=0, sticky="w", padx=(4, 12))
        self.encabezado_estado = ctk.CTkLabel(
            encabezado, text="", font=theme.FUENTE_PEQUENA, text_color=theme.TEXTO_TENUE, anchor="e",
        )
        self.encabezado_estado.grid(row=0, column=1, sticky="e", padx=(0, 4))
        self.barra_progreso = ctk.CTkProgressBar(
            encabezado, height=4, corner_radius=2, fg_color=theme.BORDE_SUAVE, progress_color=theme.ACENTO,
        )
        self.barra_progreso.grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 0))
        self.barra_progreso.set(0)

    def _construir_leyenda(self, master) -> None:
        leyenda = ctk.CTkFrame(master, fg_color="transparent")
        leyenda.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        self.marco_leyenda = leyenda
        for color, texto in _leyenda():
            item = ctk.CTkFrame(leyenda, fg_color="transparent")
            item.pack(side="left", padx=(0, 8))
            ctk.CTkFrame(item, fg_color=color, width=12, height=12, corner_radius=3, border_width=1, border_color=theme.BORDE_SUAVE).pack(
                side="left", pady=2
            )
            ctk.CTkLabel(
                item, text=texto, font=theme.FUENTE_PEQUENA, text_color=theme.TEXTO_SUAVE
            ).pack(side="left", padx=(4, 0))

    def _construir_panel_derecho(self, master) -> None:
        panel = ctk.CTkFrame(master, fg_color=theme.PANEL, corner_radius=10, width=ANCHO_PANEL, border_width=1, border_color=theme.BORDE)
        panel.grid(row=0, column=1, sticky="ns")
        panel.grid_propagate(False)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(5, weight=3, minsize=110)   # explicación
        panel.grid_rowconfigure(7, weight=2, minsize=84)    # resultado
        self.panel = panel

        extremos = ctk.CTkFrame(panel, fg_color="transparent")
        extremos.grid(row=1, column=0, sticky="ew", padx=16, pady=(14, 0))
        self.marco_extremos = extremos
        ctk.CTkLabel(extremos, text="Origen:", font=theme.FUENTE_NORMAL, text_color=theme.TEXTO_SUAVE).pack(side="left")
        self.menu_origen = ctk.CTkOptionMenu(
            extremos, values=self.grafo.vertices, width=70,
            command=lambda _v: self._al_elegir_extremo(),
            fg_color=theme.ACENTO, button_color=theme.ACENTO_HOVER,
            text_color=theme.ACENTO_TEXTO,
            dropdown_text_color=theme.TEXTO, dropdown_fg_color=theme.PANEL,
        )
        self.menu_origen.pack(side="left", padx=(6, 14))
        ctk.CTkLabel(extremos, text="Destino:", font=theme.FUENTE_NORMAL, text_color=theme.TEXTO_SUAVE).pack(side="left")
        self.menu_destino = ctk.CTkOptionMenu(
            extremos, values=self.grafo.vertices, width=70,
            command=lambda _v: self._al_elegir_extremo(),
            fg_color=theme.ACENTO, button_color=theme.ACENTO_HOVER,
            text_color=theme.ACENTO_TEXTO,
            dropdown_text_color=theme.TEXTO, dropdown_fg_color=theme.PANEL,
        )
        self.menu_destino.pack(side="left", padx=6)

        self.boton_ejecutar = ctk.CTkButton(
            panel, text="Ejecutar Dijkstra  ▶", height=36, font=(theme.FAMILIA, 13, "bold"),
            fg_color=theme.ACENTO, hover_color=theme.ACENTO_HOVER, text_color=theme.ACENTO_TEXTO,
            command=self._ejecutar,
        )
        self.boton_ejecutar.grid(row=2, column=0, sticky="ew", padx=16, pady=(10, 8))

        self.titulo_paso = ctk.CTkLabel(
            panel, text="", font=theme.FUENTE_SUBTITULO, text_color=theme.TEXTO, anchor="w",
            justify="left", wraplength=ANCHO_PANEL - 44,
        )
        self.titulo_paso.grid(row=3, column=0, sticky="ew", padx=16)

        fila_subpaso = ctk.CTkFrame(panel, fg_color="transparent")
        fila_subpaso.grid(row=4, column=0, sticky="ew", padx=16, pady=(2, 6))
        self.fila_subpaso = fila_subpaso
        fila_subpaso.grid_columnconfigure(0, weight=1)
        self.subtitulo_paso = ctk.CTkLabel(
            fila_subpaso, text="", font=theme.FUENTE_PEQUENA, text_color=theme.ACENTO,
            anchor="w", justify="left",
        )
        self.subtitulo_paso.grid(row=0, column=0, sticky="w")
        self.boton_detalles = ctk.CTkButton(
            fila_subpaso, text="Más detalles", width=104, height=26, font=(theme.FAMILIA, 12, "bold"),
            command=self._abrir_detalles,
            fg_color="transparent", hover_color=theme.ACENTO_SUAVE, text_color=theme.ACENTO,
            border_width=1, border_color=theme.ACENTO,
        )
        self.boton_detalles.grid(row=0, column=1, sticky="e")

        self.texto_explicacion = ctk.CTkTextbox(
            panel, fg_color=theme.PANEL_SUAVE, text_color=theme.TEXTO, font=theme.FUENTE_NORMAL,
            border_width=1, border_color=theme.BORDE_SUAVE,
            wrap="word", activate_scrollbars=True, height=110,
        )
        self.texto_explicacion.grid(row=5, column=0, sticky="nsew", padx=16)
        texto_rico.preparar(self.texto_explicacion)
        self.texto_explicacion.configure(state="disabled")

        self.etiqueta_resultado = ctk.CTkLabel(
            panel, text="Resultado", font=theme.FUENTE_SUBTITULO, text_color=theme.TEXTO)
        self.etiqueta_resultado.grid(row=6, column=0, sticky="w", padx=16, pady=(10, 4))
        self.texto_resultado = ctk.CTkTextbox(
            panel, fg_color=theme.PANEL_SUAVE, text_color=theme.TEXTO, font=theme.FUENTE_MONO,
            border_width=1, border_color=theme.BORDE_SUAVE,
            wrap="word", height=84,
        )
        self.texto_resultado.grid(row=7, column=0, sticky="nsew", padx=16, pady=(0, 12))
        self.texto_resultado.configure(state="disabled")

    def _construir_navegacion(self) -> None:
        barra = ctk.CTkFrame(self, fg_color=theme.PANEL, corner_radius=10, border_width=1, border_color=theme.BORDE)
        barra.grid(row=2, column=0, sticky="ew", padx=16, pady=8)
        barra.grid_columnconfigure(4, weight=1)
        self.barra_navegacion = barra

        self.boton_anterior = ctk.CTkButton(
            barra, text="◀ Anterior", width=120, height=36, font=(theme.FAMILIA, 12, "bold"),
            fg_color=theme.ACENTO, hover_color=theme.ACENTO_HOVER, text_color=theme.ACENTO_TEXTO,
            command=self._anterior,
        )
        self.boton_anterior.grid(row=0, column=0, padx=(12, 6), pady=10)

        self.boton_siguiente = ctk.CTkButton(
            barra, text="Siguiente ▶", width=120, height=36, font=(theme.FAMILIA, 12, "bold"),
            fg_color=theme.ACENTO, hover_color=theme.ACENTO_HOVER, text_color=theme.ACENTO_TEXTO,
            command=self._siguiente,
        )
        self.boton_siguiente.grid(row=0, column=1, padx=6)

        self.boton_reiniciar = ctk.CTkButton(
            barra, text="🔄 Reiniciar", width=110, height=36, font=(theme.FAMILIA, 12, "bold"),
            command=self._reiniciar,
            fg_color=theme.BOTON_SECUNDARIO, hover_color=theme.BOTON_SECUNDARIO_HOVER,
            text_color=theme.BOTON_SECUNDARIO_TEXTO, border_width=1, border_color=theme.BORDE,
        )
        self.boton_reiniciar.grid(row=0, column=2, padx=6)

        self.boton_finalizar = ctk.CTkButton(
            barra, text="⏭ Ir al final", width=110, height=36, font=(theme.FAMILIA, 12, "bold"),
            command=self._finalizar,
            fg_color=theme.BOTON_SECUNDARIO, hover_color=theme.BOTON_SECUNDARIO_HOVER,
            text_color=theme.BOTON_SECUNDARIO_TEXTO, border_width=1, border_color=theme.BORDE,
        )
        self.boton_finalizar.grid(row=0, column=3, padx=6)

        self.boton_tabla = ctk.CTkButton(
            barra, text="Ocultar tabla del proceso", width=200, height=36, font=(theme.FAMILIA, 12, "bold"),
            command=self._alternar_tabla,
            fg_color=theme.BOTON_SECUNDARIO, hover_color=theme.BOTON_SECUNDARIO_HOVER,
            text_color=theme.BOTON_SECUNDARIO_TEXTO, border_width=1, border_color=theme.BORDE,
        )
        self.boton_tabla.grid(row=0, column=5, padx=12)

    def _construir_tabla(self) -> None:
        self.tabla = TablaAlgoritmo(self.pagina.contenido, height=200)
        self.tabla.grid(row=1, column=0, sticky="ew", padx=(16, 8), pady=(8, 16))
        self.tabla_visible = True

    def _ajustar_alto_cuerpo(self, alto_visible: int) -> None:
        """Grafo + panel ocupan lo que sobra de la ventana, sin bajar de ``ALTO_CUERPO_MIN``.

        Si no cabe todo, la página se desplaza (en vez de recortar el panel o el resultado).
        """
        if not hasattr(self, "cuerpo") or not hasattr(self, "tabla"):
            return
        alto_tabla = (self.tabla.winfo_reqheight() + 24) if self.tabla_visible else 0
        self.cuerpo.configure(height=max(ALTO_CUERPO_MIN, alto_visible - alto_tabla))

    # -------------------------------------------------------------------- acciones

    def _configurar_atajos_teclado(self) -> None:
        # Un único enlace, en la ventana principal: llega la tecla venga de donde venga el foco.
        # (Enlazarla además en el canvas o en este marco hacía avanzar dos pasos por pulsación.)
        try:
            raiz = self.winfo_toplevel()
            raiz.bind("<Left>", self._al_tecla_izquierda, add="+")
            raiz.bind("<Right>", self._al_tecla_derecha, add="+")
            raiz.bind("<Up>", self._al_tecla_izquierda, add="+")
            raiz.bind("<Down>", self._al_tecla_derecha, add="+")
        except Exception:
            pass

    def _al_tecla_izquierda(self, _evento=None) -> None:
        if self.simulacion and self.simulacion.puede_retroceder:
            self._anterior()

    def _al_tecla_derecha(self, _evento=None) -> None:
        if self.simulacion and self.simulacion.puede_avanzar:
            self._siguiente()

    def destroy(self) -> None:
        if self._ventana_detalles is not None:
            try:
                self._ventana_detalles.cerrar()
            except Exception:
                pass
        try:
            raiz = self.winfo_toplevel()
            raiz.unbind("<Left>")
            raiz.unbind("<Right>")
            raiz.unbind("<Up>")
            raiz.unbind("<Down>")
        except Exception:
            pass
        super().destroy()

    def aplicar_tema(self) -> None:
        """Repinta solo lo que no es de CustomTkinter, sin tocar el estado."""
        self.canvas.aplicar_tema()
        self.tabla.aplicar_tema()
        self.pagina.aplicar_tema()
        texto_rico.aplicar_tema(self.texto_explicacion)
        if self._ventana_detalles is not None and self._ventana_detalles.winfo_exists():
            self._ventana_detalles.aplicar_tema()

    def _volver(self) -> None:
        if self.texto_volver == "← Configuración" and self.grafo.cantidad_aristas() > 0:
            total = self.grafo.cantidad_aristas()
            aristas_str = "1 arista" if total == 1 else f"{total} aristas"
            self.dialogo_confirmacion = DialogoConfirmacion(
                self,
                titulo="¿Descartar grafo?",
                mensaje=(
                    f"El grafo actual tiene {aristas_str}.\n\n"
                    "Si vuelve a la configuración perderá el grafo y la simulación actual."
                ),
                texto_confirmar="Descartar y volver",
                texto_cancelar="Permanecer en la simulación",
                al_confirmar=lambda: self.al_volver(self.canvas.obtener_posiciones()),
            )
        else:
            self.al_volver(self.canvas.obtener_posiciones())

    def _al_elegir_extremo(self) -> None:
        """El usuario cambió origen o destino en los menús: su elección se recuerda y se respeta."""
        self.seleccion_manual = (self.menu_origen.get(), self.menu_destino.get())
        self._al_cambiar_extremos()

    def _al_cambiar_extremos(self) -> None:
        """Cambiar origen o destino invalida la simulación anterior."""
        self.simulacion = None
        self.resultado = None
        self.tabla.limpiar()  # la tabla no debe conservar datos de la corrida anterior
        self.canvas.actualizar_estado(
            snapshot=None,
            origen=self.menu_origen.get(),
            destino=self.menu_destino.get(),
        )
        texto_rico.escribir(self.texto_explicacion, (
            explicaciones.Bloque(explicaciones.TITULO, "Cómo empezar"),
            explicaciones.Bloque(
                explicaciones.TEXTO,
                "Elija el origen y el destino y pulse «Ejecutar Dijkstra». Cada iteración se muestra en dos "
                "subpasos: primero se SELECCIONA el vértice no visitado con menor distancia y después se "
                "ACTUALIZAN las etiquetas de sus vecinos.",
            ),
        ))
        self._escribir(
            self.texto_resultado,
            "Elija origen y destino y pulse «Ejecutar Dijkstra».",
        )
        self.titulo_paso.configure(text="Simulación no iniciada")
        self.subtitulo_paso.configure(text="")
        self.etiqueta_paso.configure(text="")
        self.panel.grid_rowconfigure(5, weight=3)
        self.panel.grid_rowconfigure(7, weight=2)
        self._actualizar_encabezado()
        self._actualizar_detalles()
        self._actualizar_botones()

    def _ejecutar(self) -> None:
        origen, destino = self.menu_origen.get(), self.menu_destino.get()
        try:
            self.resultado = ejecutar_dijkstra(self.grafo, origen, destino)
        except GrafoError as error:  # pragma: no cover - los menús ya validan
            self._escribir(self.texto_resultado, str(error))
            return
        self.simulacion = Simulacion(self.resultado)
        # Origen = destino: no hay iteraciones de selección, solo la columna de la iteración 0.
        iteraciones = 0 if self.resultado.origen == self.resultado.destino else self.grafo.n
        self.tabla.construir(self.grafo.vertices, iteraciones)
        self._refrescar()

    def _siguiente(self) -> None:
        if self.simulacion:
            self.simulacion.siguiente()
            self._refrescar()

    def _anterior(self) -> None:
        if self.simulacion:
            self.simulacion.anterior()
            self._refrescar()

    def _reiniciar(self) -> None:
        if self.simulacion:
            self.simulacion.reiniciar()
            self._refrescar()

    def _finalizar(self) -> None:
        if self.simulacion:
            self.simulacion.finalizar()
            self._refrescar()

    def _alternar_tabla(self) -> None:
        if self.tabla_visible:
            self.tabla.grid_remove()
            self.boton_tabla.configure(text="Mostrar tabla del proceso")
        else:
            self.tabla.grid()
            self.boton_tabla.configure(text="Ocultar tabla del proceso")
        self.tabla_visible = not self.tabla_visible
        self._ajustar_alto_cuerpo(self.pagina.winfo_height())

    # ----------------------------------------------------------------- presentación

    def _refrescar(self) -> None:
        if not self.simulacion:
            return
        snapshot = self.simulacion.actual

        self.canvas.actualizar_estado(
            snapshot=snapshot,
            origen=self.resultado.origen,
            destino=self.resultado.destino,
        )
        self.tabla.mostrar(snapshot)

        self.titulo_paso.configure(text=snapshot.titulo)
        self.subtitulo_paso.configure(text=NOMBRE_SUBPASO.get(snapshot.subpaso, ""))
        explicacion = explicaciones.explicar(self.grafo, self.resultado, self.simulacion.indice)
        texto_rico.escribir(self.texto_explicacion, explicacion.breve)
        self.etiqueta_paso.configure(
            text=f"Paso {self.simulacion.indice + 1} de {self.simulacion.total}"
        )
        self._escribir(self.texto_resultado, self._texto_resultado(snapshot))
        self._actualizar_encabezado()
        self._actualizar_detalles(explicacion)
        self._actualizar_botones()
        # En el resultado final el cuadro «Resultado» pasa a tener más espacio que la explicación.
        self.panel.grid_rowconfigure(5, weight=2 if snapshot.es_final else 3)
        self.panel.grid_rowconfigure(7, weight=3 if snapshot.es_final else 2)
        if snapshot.es_final:
            self.pagina.mostrar_widget(self.panel)  # el resultado nunca queda fuera de vista

    # ------------------------------------------------------- encabezado del grafo

    def _actualizar_encabezado(self) -> None:
        """Ruta seleccionada + estado (antes / durante / después). Solo cambia textos y colores."""
        origen, destino = self.menu_origen.get(), self.menu_destino.get()
        self.encabezado_ruta.configure(text=f"Camino mínimo:  {origen} → {destino}")
        if not self.simulacion:
            self.encabezado_estado.configure(
                text="Pulsa Ejecutar Dijkstra para comenzar", text_color=theme.TEXTO_TENUE
            )
            self.barra_progreso.configure(progress_color=theme.BORDE_SUAVE)  # sin avance: pista vacía
            self.barra_progreso.set(0)
            return

        snapshot, resultado = self.simulacion.actual, self.resultado
        total = max(self.simulacion.total - 1, 1)
        self.barra_progreso.set(self.simulacion.indice / total)
        if not snapshot.es_final:
            d = snapshot.distancias[destino]
            if destino in snapshot.visitados or (destino == origen):
                texto = f"Distancia a {destino}: {formato_distancia(d)} · definitiva"
            elif d != INFINITO:
                texto = f"Distancia a {destino}: {formato_distancia(d)} · provisional"
            else:
                texto = f"Distancia a {destino}: ∞ · aún sin alcanzar"
            self.encabezado_estado.configure(text=texto, text_color=theme.TEXTO_SUAVE)
            self.barra_progreso.configure(progress_color=theme.ACENTO)
        elif resultado.alcanzable:
            n = resultado.cantidad_caminos
            self.encabezado_estado.configure(
                text=f"✓ Completada · distancia mínima {formato_distancia(resultado.distancia)} · "
                     f"{n} camino{'s' if n != 1 else ''} mínimo{'s' if n != 1 else ''}",
                text_color=theme.ARISTA_CAMINO,
            )
            self.barra_progreso.configure(progress_color=theme.ARISTA_CAMINO)
        else:
            self.encabezado_estado.configure(
                text=f"✗ Completada · no existe camino de {origen} a {destino}", text_color=theme.PELIGRO
            )
            self.barra_progreso.configure(progress_color=theme.PELIGRO)

    # -------------------------------------------------------------- más detalles

    def _abrir_detalles(self) -> None:
        if not self.simulacion:
            return
        if self._ventana_detalles is not None and self._ventana_detalles.winfo_exists():
            self._ventana_detalles.deiconify()
            self._ventana_detalles.lift()
            self._ventana_detalles.focus()
        else:
            self._ventana_detalles = VentanaDetalles(self, al_cerrar=self._al_cerrar_detalles)
            self._ventana_detalles.after(150, self._ventana_detalles.lift)
        self._actualizar_detalles()

    def _al_cerrar_detalles(self) -> None:
        self._ventana_detalles = None

    def _actualizar_detalles(self, explicacion=None) -> None:
        ventana = self._ventana_detalles
        if ventana is None or not ventana.winfo_exists():
            return
        if not self.simulacion:
            ventana.mostrar(
                "Simulación no iniciada", "", "",
                (explicaciones.Bloque(explicaciones.TEXTO, "Cambió el origen o el destino. Pulse «Ejecutar Dijkstra» "
                                      "para generar de nuevo la simulación; esta ventana mostrará el detalle de cada paso."),),
            )
            return
        if explicacion is None:
            explicacion = explicaciones.explicar(self.grafo, self.resultado, self.simulacion.indice)
        ventana.mostrar(
            explicacion.titulo, explicacion.subtitulo,
            f"Paso {self.simulacion.indice + 1} de {self.simulacion.total}", explicacion.detalle,
        )

    def _texto_resultado(self, snapshot) -> str:
        if not snapshot.es_final:
            return (
                "La simulación está en curso.\n"
                "Avance con «Siguiente» o pulse «Ir al final» para ver el resultado."
            )
        resultado = self.resultado
        if not resultado.alcanzable:
            return (
                f"No existe un camino desde {resultado.origen} hasta "
                f"{resultado.destino}.\nDistancia: ∞"
            )
        lineas = [
            f"Distancia mínima: {formato_distancia(resultado.distancia)}",
            f"Caminos mínimos encontrados: {resultado.cantidad_caminos}",
            "",
        ]
        if resultado.origen == resultado.destino:
            lineas.append(resultado.origen)
            lineas.append("")
            lineas.append(
                f"{resultado.origen} es a la vez origen y destino: la distancia es 0 "
                "y no se recorre ninguna arista."
            )
        else:
            lineas.extend(" → ".join(camino) for camino in resultado.caminos)
        if resultado.truncado:
            lineas.append("(lista truncada por la elevada cantidad de caminos)")
        return "\n".join(lineas)

    def _actualizar_botones(self) -> None:
        activa = self.simulacion is not None
        estados = {
            self.boton_anterior: activa and self.simulacion.puede_retroceder,
            self.boton_siguiente: activa and self.simulacion.puede_avanzar,
            self.boton_reiniciar: activa,
            self.boton_finalizar: activa,
            self.boton_detalles: activa,
        }
        for boton, habilitado in estados.items():
            boton.configure(state="normal" if habilitado else "disabled")

    @staticmethod
    def _escribir(caja: ctk.CTkTextbox, texto: str) -> None:
        caja.configure(state="normal")
        caja.delete("1.0", "end")
        caja.insert("1.0", texto)
        caja.configure(state="disabled")
