"""Pantalla 2 — Editor manual del grafo.

Permite crear aristas dirigidas haciendo clic en los vértices, modificar pesos
y eliminar conexiones. Toda la validación vive en el Core (core.graph).
"""

from __future__ import annotations

import customtkinter as ctk

from core.extremos import analizar, mensaje_advertencia, sugerir_extremos
from core.graph import GrafoError, validar_peso

from . import theme
from .dialogs import DialogoConfirmacion
from .graph_canvas import GrafoCanvas


class PantallaEditor(ctk.CTkFrame):
    def __init__(self, master, grafo, al_finalizar, al_volver, posiciones_iniciales=None, extremos=None):
        super().__init__(master, fg_color=theme.FONDO)
        self.grafo = grafo
        # ``extremos(grafo)`` -> (origen, destino) con el que se revisará el grafo al finalizar
        self.extremos = extremos or sugerir_extremos
        self.al_finalizar = al_finalizar
        self.al_volver = al_volver
        # Si se regresa desde la simulación, los nodos reaparecen donde estaban.
        self.posiciones_iniciales = posiciones_iniciales

        self.origen_arista: str | None = None
        self.destino_arista: str | None = None
        self.arista_seleccionada: tuple[str, str] | None = None
        self.dialogo_confirmacion: DialogoConfirmacion | None = None
        self._aristas_mostradas: list | None = None  # lo que muestra hoy la lista lateral

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_barra_superior()
        self._construir_cuerpo()
        self._configurar_atajos()
        self._refrescar()
        if self.grafo.cantidad_aristas() > 0:
            self._informar("Grafo conservado: puede seguir editándolo.")

    # ---------------------------------------------------------------- construcción

    def _construir_barra_superior(self) -> None:
        barra = ctk.CTkFrame(self, fg_color=theme.PANEL, corner_radius=10, border_width=1, border_color=theme.BORDE)
        barra.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        barra.grid_columnconfigure(1, weight=1)

        self.boton_volver = ctk.CTkButton(
            barra, text="← Volver", width=95, height=32, font=(theme.FAMILIA, 12, "bold"),
            command=self._volver,
            fg_color=theme.BOTON_SECUNDARIO, hover_color=theme.BOTON_SECUNDARIO_HOVER,
            text_color=theme.BOTON_SECUNDARIO_TEXTO, border_width=1, border_color=theme.BORDE,
        )
        self.boton_volver.grid(row=0, column=0, padx=12, pady=10)

        ctk.CTkLabel(
            barra, text="Editor manual del grafo", font=theme.FUENTE_SUBTITULO, text_color=theme.TEXTO,
        ).grid(row=0, column=1, sticky="w", padx=8)

        ctk.CTkLabel(
            barra,
            text="Arrastre nodos para ubicarlos · Clic en origen y destino para conectar",
            font=theme.FUENTE_PEQUENA,
            text_color=theme.TEXTO_SUAVE,
        ).grid(row=0, column=2, padx=8)

        self.boton_restablecer = ctk.CTkButton(
            barra,
            text="↺ Restablecer",
            width=100,
            height=30,
            font=theme.FUENTE_PEQUENA,
            command=self._reorganizar_circulo,
            fg_color=theme.BOTON_SECUNDARIO,
            hover_color=theme.BOTON_SECUNDARIO_HOVER,
            text_color=theme.BOTON_SECUNDARIO_TEXTO,
            border_width=1,
            border_color=theme.BORDE,
        )
        self.boton_restablecer.grid(row=0, column=3, padx=12, pady=10)

    def _construir_cuerpo(self) -> None:
        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        cuerpo.grid_rowconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(0, weight=1)

        self.canvas = GrafoCanvas(
            cuerpo, al_hacer_clic_en_nodo=self._al_hacer_clic_en_nodo,
            al_hacer_clic_en_peso=self._editar_peso_en_linea,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.canvas.establecer_grafo(
            self.grafo,
            posiciones=self.posiciones_iniciales,
            modo_layout="circular",
        )

        panel = ctk.CTkFrame(cuerpo, fg_color=theme.PANEL, corner_radius=10, width=330, border_width=1, border_color=theme.BORDE)
        panel.grid(row=0, column=1, sticky="ns")
        panel.grid_propagate(False)
        panel.grid_rowconfigure(6, weight=1)
        self.panel_lateral = panel

        ctk.CTkLabel(panel, text="Nueva arista", font=theme.FUENTE_SUBTITULO, text_color=theme.TEXTO).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 6)
        )

        self.etiqueta_seleccion = ctk.CTkLabel(
            panel, text="", font=theme.FUENTE_NORMAL, text_color=theme.TEXTO,
            justify="left", anchor="w",
        )
        self.etiqueta_seleccion.grid(row=1, column=0, sticky="ew", padx=16)

        fila_peso = ctk.CTkFrame(panel, fg_color="transparent")
        fila_peso.grid(row=2, column=0, sticky="ew", padx=16, pady=(10, 6))
        self.fila_peso = fila_peso
        ctk.CTkLabel(fila_peso, text="Peso (1-99):", font=theme.FUENTE_NORMAL, text_color=theme.TEXTO_SUAVE).pack(side="left")
        self.entrada_peso = ctk.CTkEntry(fila_peso, width=80, justify="center")
        self.entrada_peso.pack(side="left", padx=8)
        self.entrada_peso.bind("<Return>", lambda _e: self._crear_arista())

        fila_botones = ctk.CTkFrame(panel, fg_color="transparent")
        fila_botones.grid(row=3, column=0, sticky="ew", padx=16)
        self.fila_botones = fila_botones
        ctk.CTkButton(
            fila_botones, text="Crear conexión", command=self._crear_arista, width=150,
            font=(theme.FAMILIA, 12, "bold"),
            fg_color=theme.ACENTO, hover_color=theme.ACENTO_HOVER, text_color=theme.ACENTO_TEXTO,
        ).pack(side="left")
        ctk.CTkButton(
            fila_botones, text="Cancelar", width=90, command=self._cancelar_seleccion,
            font=(theme.FAMILIA, 12, "bold"),
            fg_color=theme.BOTON_SECUNDARIO, hover_color=theme.BOTON_SECUNDARIO_HOVER,
            text_color=theme.BOTON_SECUNDARIO_TEXTO, border_width=1, border_color=theme.BORDE,
        ).pack(side="left", padx=8)

        self.mensaje = ctk.CTkLabel(
            panel, text="", font=theme.FUENTE_PEQUENA, wraplength=290,
            justify="left", anchor="w", text_color=theme.TEXTO_SUAVE,
        )
        self.mensaje.grid(row=4, column=0, sticky="ew", padx=16, pady=(10, 4))

        ctk.CTkLabel(panel, text="Aristas del grafo", font=theme.FUENTE_SUBTITULO, text_color=theme.TEXTO).grid(
            row=5, column=0, sticky="w", padx=16, pady=(8, 4)
        )
        self.lista_aristas = ctk.CTkScrollableFrame(
            panel, fg_color=theme.PANEL_SUAVE, corner_radius=8, width=290,
            border_width=1, border_color=theme.BORDE_SUAVE,
        )
        self.lista_aristas.grid(row=6, column=0, sticky="nsew", padx=16, pady=(0, 10))

        self.boton_finalizar_grafo = ctk.CTkButton(
            panel, text="Finalizar grafo  →", height=40, font=(theme.FAMILIA, 13, "bold"),
            fg_color=theme.ACENTO, hover_color=theme.ACENTO_HOVER, text_color=theme.ACENTO_TEXTO,
            command=self._finalizar,
        )
        self.boton_finalizar_grafo.grid(row=7, column=0, sticky="ew", padx=16, pady=(0, 16))

    # -------------------------------------------------------------------- acciones

    def _configurar_atajos(self) -> None:
        self.bind("<Escape>", self._al_pulsar_escape)
        if hasattr(self, "canvas") and hasattr(self.canvas, "canvas"):
            self.canvas.canvas.bind("<Escape>", self._al_pulsar_escape)
        try:
            self.winfo_toplevel().bind("<Escape>", self._al_pulsar_escape, add="+")
        except Exception:
            pass

    def _al_pulsar_escape(self, _evento=None) -> None:
        if self.origen_arista is not None or self.destino_arista is not None:
            self._cancelar_seleccion()

    def destroy(self) -> None:
        try:
            self.winfo_toplevel().unbind("<Escape>")
        except Exception:
            pass
        super().destroy()

    def aplicar_tema(self) -> None:
        """Repinta solo el canvas (Tk puro), sin tocar el grafo ni la selección."""
        self.canvas.aplicar_tema()

    def _volver(self) -> None:
        if self.grafo.cantidad_aristas() > 0:
            total = self.grafo.cantidad_aristas()
            aristas_str = "1 arista" if total == 1 else f"{total} aristas"
            self.dialogo_confirmacion = DialogoConfirmacion(
                self,
                titulo="¿Descartar grafo?",
                mensaje=(
                    f"El grafo actual tiene {aristas_str}.\n\n"
                    "Si vuelve a la configuración perderá todas las conexiones creadas."
                ),
                texto_confirmar="Descartar y volver",
                texto_cancelar="Continuar editando",
                al_confirmar=self.al_volver,
            )
        else:
            self.al_volver()

    def _al_hacer_clic_en_nodo(self, vertice: str) -> None:
        if self.origen_arista is None:
            self.origen_arista = vertice
        elif self.destino_arista is None:
            if vertice == self.origen_arista:
                self._informar("Un vértice no puede conectarse consigo mismo.", error=True)
                return
            self.destino_arista = vertice
            self._enfocar_peso()
        else:
            self.origen_arista = vertice
            self.destino_arista = None
        self._refrescar()

    def _enfocar_peso(self) -> None:
        """Deja el cursor en el campo del peso para escribir de inmediato.

        Se pide el foco ya y se reafirma al quedar inactivo Tk, por si otro
        widget (o la ventana) lo recupera mientras se redibuja el grafo.
        """
        def poner() -> None:
            try:
                if self.destino_arista is not None and self.focus_get() is not self.entrada_peso._entry:
                    self.entrada_peso._entry.focus_force()
            except Exception:  # pragma: no cover - la pantalla ya no existe
                pass

        self.entrada_peso.focus_set()
        self.after_idle(poner)

    def _cancelar_seleccion(self) -> None:
        self.origen_arista = None
        self.destino_arista = None
        self.canvas.actualizar_estado(origen_preview=None, destino_preview=None)
        self.canvas.limpiar_preview_arista()
        self.entrada_peso.delete(0, "end")
        self._informar("Selección cancelada.")
        self._refrescar()

    def _crear_arista(self) -> None:
        if self.origen_arista is None or self.destino_arista is None:
            self._informar(
                "Seleccione primero el vértice de origen y el de destino.", error=True
            )
            return
        try:
            peso = validar_peso(self.entrada_peso.get())
            self.grafo.agregar_arista(self.origen_arista, self.destino_arista, peso)
        except GrafoError as error:
            self._informar(str(error), error=True)
            return

        self._informar(
            f"Conexión creada: {self.origen_arista} → {self.destino_arista} "
            f"(peso {peso})."
        )
        self.origen_arista = None
        self.destino_arista = None
        self.canvas.actualizar_estado(origen_preview=None, destino_preview=None)
        self.canvas.limpiar_preview_arista()
        self.entrada_peso.delete(0, "end")
        self.canvas.establecer_grafo(self.grafo)
        self._refrescar()

    def _modificar_peso(self, u: str, v: str) -> None:
        dialogo = ctk.CTkInputDialog(
            text=f"Nuevo peso para {u} → {v} (1-99):", title="Modificar peso"
        )
        valor = dialogo.get_input()
        if valor is None:
            return
        try:
            self.grafo.modificar_peso(u, v, valor)
        except GrafoError as error:
            self._informar(str(error), error=True)
            return
        self._informar(f"Peso de {u} → {v} actualizado a {self.grafo.peso(u, v)}.")
        self._refrescar()

    def _eliminar_arista(self, u: str, v: str) -> None:
        try:
            self.grafo.eliminar_arista(u, v)
        except GrafoError as error:
            self._informar(str(error), error=True)
            return
        self._informar(f"Arista {u} → {v} eliminada.")
        self.canvas.establecer_grafo(self.grafo)
        self._refrescar()

    def _editar_peso_en_linea(self, u: str, v: str) -> None:
        """Clic sobre el número de una arista: campo pequeño para cambiar su peso ahí mismo."""
        self.canvas.abrir_editor_peso(u, v, self.grafo.peso(u, v), lambda texto: self._aplicar_peso(u, v, texto))

    def _aplicar_peso(self, u: str, v: str, texto: str) -> bool:
        try:
            self.grafo.modificar_peso(u, v, texto)
        except GrafoError as error:
            self._informar(str(error), error=True)
            return False  # el campo sigue abierto para corregir el valor
        self._informar(f"Peso de {u} → {v} actualizado a {self.grafo.peso(u, v)}.")
        self.canvas.redibujar(actualizar_posiciones_absolutas=False)  # el grafo, al instante
        self._refrescar()                                              # y la lista lateral
        return True

    def _reorganizar_circulo(self) -> None:
        self.canvas.reorganizar_en_circulo()
        self._informar("Posiciones de los nodos restablecidas.")

    def _finalizar(self) -> None:
        if self.grafo.cantidad_aristas() == 0:
            self._informar(
                "El grafo no tiene conexiones. Cree al menos una arista antes de continuar.",
                error=True,
            )
            return
        self.canvas.cerrar_editor_peso()
        origen, destino = self.extremos(self.grafo)
        analisis = analizar(self.grafo, origen, destino)
        if not analisis.hay_advertencias:
            self._continuar_a_simulacion()
            return
        mensaje = mensaje_advertencia(analisis)
        lineas = sum(max(1, -(-len(parte) // 56)) for parte in mensaje.split("\n"))
        self.dialogo_confirmacion = DialogoConfirmacion(
            self,
            titulo="Revisa tu grafo antes de simular",
            mensaje=mensaje,
            texto_confirmar="Continuar de todos modos",
            texto_cancelar="Volver al editor",
            al_confirmar=self._continuar_a_simulacion,
            alto=160 + 19 * lineas,
            peligro=False,
            ancho_confirmar=190,
        )

    def _continuar_a_simulacion(self) -> None:
        posiciones = self.canvas.obtener_posiciones()
        self.al_finalizar(self.grafo, posiciones=posiciones)

    # ----------------------------------------------------------------- presentación

    def _informar(self, texto: str, error: bool = False) -> None:
        self.mensaje.configure(
            text=texto, text_color=theme.PELIGRO if error else theme.ARISTA_CAMINO
        )

    def _refrescar(self) -> None:
        origen = self.origen_arista or "—"
        destino = self.destino_arista or "—"
        self.etiqueta_seleccion.configure(text=f"Origen: {origen}      Destino: {destino}")

        seleccion = [v for v in (self.origen_arista, self.destino_arista) if v]
        self.canvas.actualizar_estado(
            seleccion_editor=seleccion,
            origen_preview=self.origen_arista,
            destino_preview=self.destino_arista,
        )

        aristas = self.grafo.aristas()
        # Reconstruir la lista (decenas de widgets) solo cuando cambian las aristas:
        # seleccionar nodos no las modifica y no debe retrasar el campo del peso.
        if aristas == self._aristas_mostradas:
            return
        self._aristas_mostradas = list(aristas)
        for hijo in self.lista_aristas.winfo_children():
            hijo.destroy()
        if not aristas:
            ctk.CTkLabel(
                self.lista_aristas, text="Todavía no hay aristas.",
                text_color=theme.TEXTO_TENUE, font=theme.FUENTE_PEQUENA,
            ).pack(anchor="w", padx=8, pady=6)
            return
        for u, v, peso in aristas:
            fila = ctk.CTkFrame(self.lista_aristas, fg_color="transparent")
            fila.pack(fill="x", padx=4, pady=2)
            ctk.CTkLabel(
                fila, text=f"{u} → {v}", width=70, font=theme.FUENTE_NORMAL, anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                fila, text=f"peso {peso}", width=80, font=theme.FUENTE_PEQUENA,
                text_color=theme.TEXTO_SUAVE, anchor="w",
            ).pack(side="left")
            ctk.CTkButton(
                fila, text="Peso", width=52, height=26, font=theme.FUENTE_PEQUENA,
                command=lambda a=u, b=v: self._modificar_peso(a, b),
                fg_color=theme.BOTON_SECUNDARIO, hover_color=theme.BOTON_SECUNDARIO_HOVER,
                text_color=theme.BOTON_SECUNDARIO_TEXTO, border_width=1, border_color=theme.BORDE,
            ).pack(side="left", padx=2)
            ctk.CTkButton(
                fila, text="Eliminar", width=66, height=26, font=theme.FUENTE_PEQUENA,
                command=lambda a=u, b=v: self._eliminar_arista(a, b),
                fg_color=theme.PELIGRO, hover_color=theme.PELIGRO_HOVER,
                text_color=theme.PELIGRO_TEXTO,
            ).pack(side="left", padx=2)
