"""Contenedor con desplazamiento vertical para pantallas que pueden no caber.

A diferencia de ``CTkScrollableFrame``, la rueda no se escucha de forma global
por el propio contenedor: la reparte ``ui.rueda`` para que los componentes con
desplazamiento propio (tabla, cuadros de texto) no compitan con la página.

El contenido recibe un alto mínimo: si la ventana es más baja, aparece la barra
y se puede desplazar; si es más alta, el contenido puede ocupar todo el espacio
(``al_cambiar_alto`` informa del alto visible para ajustarlo).
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable

import customtkinter as ctk

from . import theme
from .rueda import RuedaPagina, enrutador_de


TOLERANCIA = 8  # píxeles de desborde que se ignoran


class PaginaDesplazable(ctk.CTkFrame):
    def __init__(self, master, al_cambiar_alto: Callable[[int], None] | None = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._al_cambiar_alto = al_cambiar_alto
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._lienzo = tk.Canvas(
            self, bg=theme.resolver(theme.FONDO), highlightthickness=0, bd=0, yscrollincrement=28
        )
        self._lienzo.grid(row=0, column=0, sticky="nsew")
        self._barra = ctk.CTkScrollbar(self, orientation="vertical", command=self._lienzo.yview)
        self._barra.grid(row=0, column=1, sticky="ns", padx=(4, 8))
        self._lienzo.configure(yscrollcommand=self._al_mover_barra)

        self.contenido = ctk.CTkFrame(self._lienzo, fg_color=theme.FONDO, corner_radius=0)
        self._ventana = self._lienzo.create_window((0, 0), window=self.contenido, anchor="nw")
        self.contenido.bind("<Configure>", lambda _e: self._actualizar_region())
        self._lienzo.bind("<Configure>", self._al_cambiar_tamano)

        self._barra_visible = True
        self._ultimo_alto = -1
        self.rueda = RuedaPagina(self)
        self._enrutador = enrutador_de(self)
        self._enrutador.activar(self)

    # ------------------------------------------------------------------ geometría

    def _al_cambiar_tamano(self, evento) -> None:
        self._lienzo.itemconfigure(self._ventana, width=evento.width)
        if self._al_cambiar_alto is not None and evento.height != self._ultimo_alto:
            self._ultimo_alto = evento.height
            self._al_cambiar_alto(evento.height)
        self._actualizar_region()

    def _actualizar_region(self) -> None:
        # Un desborde de unos pocos píxeles no justifica barra ni desplazamiento.
        alto = self.contenido.winfo_reqheight()
        visible = self._lienzo.winfo_height()
        if visible > 1 and 0 < alto - visible <= TOLERANCIA:
            alto = visible
        self._lienzo.configure(scrollregion=(0, 0, 0, alto))
        self._ajustar_barra()

    def _al_mover_barra(self, primero, ultimo) -> None:
        self._barra.set(primero, ultimo)
        self._ajustar_barra()

    def _ajustar_barra(self) -> None:
        """La barra solo se muestra si el contenido no cabe (no ocupa sitio si no hace falta)."""
        primero, ultimo = self._lienzo.yview()
        necesaria = not (primero <= 0.0 and ultimo >= 1.0)
        if necesaria != self._barra_visible:
            self._barra_visible = necesaria
            if necesaria:
                self._barra.grid()
            else:
                self._barra.grid_remove()

    # ---------------------------------------------------------------- desplazamiento

    @property
    def desbordada(self) -> bool:
        primero, ultimo = self._lienzo.yview()
        return not (primero <= 0.0 and ultimo >= 1.0)

    def desplazar(self, pasos: int) -> bool:
        """Desplaza la página ``pasos`` unidades; devuelve si se movió."""
        primero, ultimo = self._lienzo.yview()
        if (pasos < 0 and primero <= 0.0) or (pasos > 0 and ultimo >= 1.0):
            return False
        self._lienzo.yview_scroll(pasos, "units")
        return True

    def ir_al_principio(self) -> None:
        self._lienzo.yview_moveto(0.0)

    def ir_al_final(self) -> None:
        self._lienzo.yview_moveto(1.0)

    def mostrar_widget(self, widget) -> None:
        """Desplaza lo mínimo para que ``widget`` quede completamente visible."""
        self.update_idletasks()
        alto_visible = self._lienzo.winfo_height()
        total = max(self.contenido.winfo_reqheight(), 1)
        arriba = widget.winfo_rooty() - self.contenido.winfo_rooty()
        abajo = arriba + widget.winfo_height()
        origen = self._lienzo.canvasy(0)
        if arriba < origen:
            self._lienzo.yview_moveto(max(arriba, 0) / total)
        elif abajo > origen + alto_visible:
            self._lienzo.yview_moveto((abajo - alto_visible) / total)

    # --------------------------------------------------------------------- rueda

    def desplazar_con_rueda(self, evento) -> None:
        self.rueda.repartir(evento)

    def registrar_desplazable(self, widget, mover) -> None:
        self.rueda.registrar(widget, mover)

    def registrar_texto(self, caja) -> None:
        self.rueda.registrar_texto(caja)

    # ---------------------------------------------------------------------- tema

    def aplicar_tema(self) -> None:
        self._lienzo.configure(bg=theme.resolver(theme.FONDO))

    def destroy(self) -> None:
        try:
            self._enrutador.desactivar(self)
        except Exception:
            pass
        super().destroy()
