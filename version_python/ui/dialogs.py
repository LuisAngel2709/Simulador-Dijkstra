"""Diálogos y modales de confirmación para la interfaz."""

from __future__ import annotations

from typing import Callable
import customtkinter as ctk

from . import theme


class DialogoConfirmacion(ctk.CTkToplevel):
    """Diálogo modal moderno para confirmar acciones que descartan cambios."""

    def __init__(
        self,
        master,
        titulo: str = "Confirmar acción",
        mensaje: str = "¿Desea continuar? Se perderán los datos actuales.",
        texto_confirmar: str = "Descartar y volver",
        texto_cancelar: str = "Cancelar",
        al_confirmar: Callable[[], None] | None = None,
        al_cancelar: Callable[[], None] | None = None,
        alto: int = 210,
        peligro: bool = True,
        ancho_confirmar: int = 150,
    ):
        super().__init__(master)
        self.al_confirmar = al_confirmar
        self.al_cancelar = al_cancelar
        self.confirmado = False
        self._ventana_padre = None

        self.title("")
        ancho = 480
        self.geometry(f"{ancho}x{alto}")
        self.resizable(False, False)

        # Sin barra de título nativa (sin botón «X»): el diálogo se cierra solo con
        # sus dos botones o con Esc. El marco propio dibuja el borde y el redondeo.
        self.overrideredirect(True)
        self._color_transparente = "#010101"
        self.configure(fg_color=self._color_transparente)
        try:  # esquinas redondeadas reales: solo disponible en Windows
            self.attributes("-transparentcolor", self._color_transparente)
        except Exception:
            self.configure(fg_color=theme.FONDO)

        try:
            ventana_padre = master.winfo_toplevel() if hasattr(master, "winfo_toplevel") else master
            self._ventana_padre = ventana_padre
            self.transient(ventana_padre)
            self.update_idletasks()
            rx = ventana_padre.winfo_rootx() + (ventana_padre.winfo_width() - ancho) // 2
            ry = ventana_padre.winfo_rooty() + (ventana_padre.winfo_height() - alto) // 2
            self.geometry(f"{ancho}x{alto}+{max(0, rx)}+{max(0, ry)}")
            self.lift()
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

        tarjeta = ctk.CTkFrame(
            self,
            fg_color=theme.DIALOGO_FONDO,
            corner_radius=14,
            border_width=2,
            border_color=theme.DIALOGO_BORDE,
        )
        tarjeta.pack(fill="both", expand=True)

        self.etiqueta_titulo = ctk.CTkLabel(
            tarjeta,
            text=titulo,
            font=theme.FUENTE_SUBTITULO,
            text_color=theme.TEXTO,
            anchor="w",
        )
        self.etiqueta_titulo.pack(fill="x", padx=22, pady=(20, 4))

        self.etiqueta_mensaje = ctk.CTkLabel(
            tarjeta,
            text=mensaje,
            font=theme.FUENTE_NORMAL,
            text_color=theme.TEXTO_SUAVE,
            justify="left",
            anchor="nw",
            wraplength=ancho - 60,
        )
        self.etiqueta_mensaje.pack(fill="x", padx=22, pady=(0, 10))

        fila_botones = ctk.CTkFrame(tarjeta, fg_color="transparent")
        fila_botones.pack(fill="x", padx=22, pady=(0, 18), side="bottom")

        self.boton_cancelar = ctk.CTkButton(
            fila_botones,
            text=texto_cancelar,
            font=theme.FUENTE_NORMAL,
            fg_color=theme.BOTON_SECUNDARIO,
            hover_color=theme.BOTON_SECUNDARIO_HOVER,
            text_color=theme.BOTON_SECUNDARIO_TEXTO,
            border_width=1,
            border_color=theme.DIALOGO_BORDE,
            height=36,
            command=self._cancelar,
        )
        self.boton_cancelar.pack(side="right", padx=(8, 0))

        self.boton_confirmar = ctk.CTkButton(
            fila_botones,
            text=texto_confirmar,
            font=(theme.FAMILIA, 12, "bold"),
            fg_color=theme.PELIGRO if peligro else theme.ACENTO,
            hover_color=theme.PELIGRO_HOVER if peligro else theme.ACENTO_HOVER,
            text_color=theme.PELIGRO_TEXTO if peligro else theme.ACENTO_TEXTO,
            width=ancho_confirmar,
            height=36,
            command=self._confirmar,
        )
        self.boton_confirmar.pack(side="right")

        self.bind("<Escape>", lambda _e: self._cancelar())
        self.protocol("WM_DELETE_WINDOW", self._cancelar)

    def _cerrar(self) -> None:
        """Libera el modal y devuelve el foco de teclado a la ventana principal.

        Sin esto, al destruir una ventana sin marco el sistema puede dejar el foco
        fuera de la aplicación y los campos de texto no reciben teclas.
        """
        try:
            self.grab_release()
        except Exception:
            pass
        padre = self._ventana_padre
        self.destroy()
        try:
            if padre is not None and padre.winfo_exists():
                padre.focus_force()
        except Exception:  # pragma: no cover
            pass

    def _confirmar(self) -> None:
        self.confirmado = True
        self._cerrar()
        if self.al_confirmar:
            self.al_confirmar()

    def _cancelar(self) -> None:
        self.confirmado = False
        self._cerrar()
        if self.al_cancelar:
            self.al_cancelar()
