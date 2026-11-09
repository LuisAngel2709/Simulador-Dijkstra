"""Ventana secundaria «Más detalles»: explicación ampliada del paso actual.

No es modal: se puede dejar abierta mientras se avanza o retrocede en la
simulación (la ventana principal sigue respondiendo) y se actualiza sola.
"""

from __future__ import annotations

import customtkinter as ctk

from . import texto_rico, theme


class VentanaDetalles(ctk.CTkToplevel):
    def __init__(self, master, al_cerrar=None):
        super().__init__(master)
        self._al_cerrar = al_cerrar
        self.title("Más detalles del paso")
        self.configure(fg_color=theme.FONDO)
        self.minsize(460, 380)

        ancho, alto = 560, 680
        try:  # a la derecha de la ventana principal si cabe; si no, centrada sobre ella
            raiz = master.winfo_toplevel()
            raiz.update_idletasks()
            x = raiz.winfo_rootx() + raiz.winfo_width() - ancho - 40
            y = raiz.winfo_rooty() + 70
            x = max(0, min(x, self.winfo_screenwidth() - ancho - 10))
            y = max(0, min(y, self.winfo_screenheight() - alto - 60))
            self.geometry(f"{ancho}x{alto}+{x}+{y}")
        except Exception:
            self.geometry(f"{ancho}x{alto}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        cabecera = ctk.CTkFrame(self, fg_color=theme.PANEL, corner_radius=10, border_width=1, border_color=theme.BORDE)
        cabecera.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        cabecera.grid_columnconfigure(0, weight=1)
        self.etiqueta_titulo = ctk.CTkLabel(
            cabecera, text="", font=theme.FUENTE_SUBTITULO, text_color=theme.TEXTO,
            anchor="w", justify="left", wraplength=480,
        )
        self.etiqueta_titulo.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 0))
        self.etiqueta_subtitulo = ctk.CTkLabel(
            cabecera, text="", font=theme.FUENTE_PEQUENA, text_color=theme.ACENTO, anchor="w",
        )
        self.etiqueta_subtitulo.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
        self.etiqueta_paso = ctk.CTkLabel(
            cabecera, text="", font=theme.FUENTE_PEQUENA, text_color=theme.TEXTO_SUAVE,
        )
        self.etiqueta_paso.grid(row=0, column=1, rowspan=2, padx=14)

        self.texto = ctk.CTkTextbox(
            self, fg_color=theme.PANEL, text_color=theme.TEXTO, font=theme.FUENTE_NORMAL,
            border_width=1, border_color=theme.BORDE, wrap="word", corner_radius=10,
        )
        self.texto.grid(row=1, column=0, sticky="nsew", padx=14)
        texto_rico.preparar(self.texto)
        self.texto.configure(state="disabled")

        pie = ctk.CTkFrame(self, fg_color="transparent")
        pie.grid(row=2, column=0, sticky="ew", padx=14, pady=10)
        pie.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            pie, text="Se actualiza al cambiar de paso.", font=theme.FUENTE_PEQUENA,
            text_color=theme.TEXTO_TENUE,
        ).grid(row=0, column=0, sticky="w")
        self.boton_cerrar = ctk.CTkButton(
            pie, text="Cerrar", width=100, height=32, font=(theme.FAMILIA, 12, "bold"),
            command=self.cerrar,
            fg_color=theme.BOTON_SECUNDARIO, hover_color=theme.BOTON_SECUNDARIO_HOVER,
            text_color=theme.BOTON_SECUNDARIO_TEXTO, border_width=1, border_color=theme.BORDE,
        )
        self.boton_cerrar.grid(row=0, column=1)

        self.bind("<Escape>", lambda _e: self.cerrar())
        self.protocol("WM_DELETE_WINDOW", self.cerrar)

    # ------------------------------------------------------------------- contenido

    def mostrar(self, titulo: str, subtitulo: str, paso: str, bloques) -> None:
        self.etiqueta_titulo.configure(text=titulo)
        self.etiqueta_subtitulo.configure(text=subtitulo)
        self.etiqueta_paso.configure(text=paso)
        texto_rico.escribir(self.texto, bloques)

    def aplicar_tema(self) -> None:
        texto_rico.aplicar_tema(self.texto)

    def cerrar(self) -> None:
        callback, self._al_cerrar = self._al_cerrar, None
        try:
            self.destroy()
        finally:
            if callback:
                callback()
