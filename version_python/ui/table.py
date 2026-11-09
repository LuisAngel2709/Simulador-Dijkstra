"""Tabla del proceso de etiquetación, sincronizada con el snapshot actual.

Cada celda corresponde a un vértice y una iteración, igual que la tabla única
que propone el material académico. Las etiquetas descartadas aparecen tachadas
y las etiquetas empatadas se resaltan.
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from core.dijkstra_engine import DESCARTADA, EMPATE

from . import theme

ANCHO_CELDA = 10  # en caracteres


class TablaAlgoritmo(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.PANEL, corner_radius=10, **kwargs)

        self._contenedor = tk.Canvas(
            self, bg=theme.resolver(theme.PANEL), highlightthickness=0, bd=0, height=200
        )
        barra_v = ctk.CTkScrollbar(self, orientation="vertical", command=self._contenedor.yview)
        barra_h = ctk.CTkScrollbar(self, orientation="horizontal", command=self._contenedor.xview)
        self._contenedor.configure(yscrollcommand=barra_v.set, xscrollcommand=barra_h.set)

        self._contenedor.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        barra_v.grid(row=0, column=1, sticky="ns", pady=(8, 0))
        barra_h.grid(row=1, column=0, sticky="ew", padx=(8, 0))
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._interior = tk.Frame(self._contenedor, bg=theme.resolver(theme.PANEL))
        self._contenedor.create_window((0, 0), window=self._interior, anchor="nw")
        self._interior.bind(
            "<Configure>",
            lambda _e: self._contenedor.configure(
                scrollregion=self._contenedor.bbox("all")
            ),
        )

        self._celdas: dict[tuple[str, int], tk.Label] = {}
        self._cabeceras: list[tk.Label] = []
        self._ultimo_snapshot = None  # solo para repintar al cambiar de tema
        self._vertices: list[str] = []
        self._iteraciones: list[int] = []

    # ---------------------------------------------------------------- construcción

    def limpiar(self) -> None:
        """Deja la tabla vacía, como antes de ejecutar (p. ej. si se invalida la simulación)."""
        for hijo in self._interior.winfo_children():
            hijo.destroy()
        self._celdas.clear()
        self._cabeceras.clear()
        self._ultimo_snapshot = None
        self._vertices = []
        self._iteraciones = []
        self._contenedor.xview_moveto(0)
        self._contenedor.yview_moveto(0)

    def construir(self, vertices: list[str], iteraciones: int) -> None:
        self.limpiar()
        self._vertices = list(vertices)
        self._iteraciones = list(range(iteraciones + 1))

        self._crear_cabecera("Vértice", 0, 0)
        for columna, iteracion in enumerate(self._iteraciones, start=1):
            self._crear_cabecera(f"Iteración {iteracion}", 0, columna)

        for fila, vertice in enumerate(self._vertices, start=1):
            self._crear_cabecera(vertice, fila, 0)
            for columna, iteracion in enumerate(self._iteraciones, start=1):
                celda = tk.Label(
                    self._interior,
                    text="",
                    width=ANCHO_CELDA,
                    font=theme.FUENTE_CELDA,
                    bg=theme.resolver(theme.CELDA_VACIA),
                    fg=theme.resolver(theme.TEXTO),
                    padx=4,
                    pady=3,
                )
                celda.grid(row=fila, column=columna, padx=1, pady=1, sticky="nsew")
                self._celdas[(vertice, iteracion)] = celda

    def _crear_cabecera(self, texto: str, fila: int, columna: int) -> None:
        etiqueta = tk.Label(
            self._interior,
            text=texto,
            width=ANCHO_CELDA,
            font=(theme.FAMILIA, 11, "bold"),
            bg=theme.resolver(theme.CABECERA),
            fg=theme.resolver(theme.TEXTO),
            padx=4,
            pady=3,
        )
        etiqueta.grid(row=fila, column=columna, padx=1, pady=1, sticky="nsew")
        self._cabeceras.append(etiqueta)

    # ---------------------------------------------------------------- sincronización

    def mostrar(self, snapshot) -> None:
        """Vuelca el contenido del snapshot; la tabla nunca guarda estado propio."""
        self._ultimo_snapshot = snapshot
        for celda in self._celdas.values():
            celda.configure(
                text="", bg=theme.resolver(theme.CELDA_VACIA), fg=theme.resolver(theme.TEXTO), font=theme.FUENTE_CELDA
            )
        for entrada in snapshot.tabla:
            celda = self._celdas.get((entrada.vertice, entrada.iteracion))
            if celda is None:
                continue
            if entrada.estado == DESCARTADA:
                celda.configure(
                    text=entrada.texto,
                    bg=theme.resolver(theme.CELDA_DESCARTADA),
                    fg=theme.resolver(theme.TEXTO_TENUE),
                    font=theme.FUENTE_CELDA_TACHADA,
                )
            elif entrada.estado == EMPATE:
                celda.configure(
                    text=entrada.texto, bg=theme.resolver(theme.CELDA_EMPATE), fg=theme.resolver(theme.TEXTO)
                )
            else:
                celda.configure(
                    text=entrada.texto, bg=theme.resolver(theme.CELDA_VIGENTE), fg=theme.resolver(theme.TEXTO)
                )

    def aplicar_tema(self) -> None:
        """Recolora la tabla con el tema activo, conservando su contenido."""
        self._contenedor.configure(bg=theme.resolver(theme.PANEL))
        self._interior.configure(bg=theme.resolver(theme.PANEL))
        for cabecera in self._cabeceras:
            cabecera.configure(bg=theme.resolver(theme.CABECERA), fg=theme.resolver(theme.TEXTO))
        if self._ultimo_snapshot is not None:
            self.mostrar(self._ultimo_snapshot)
        else:
            for celda in self._celdas.values():
                celda.configure(bg=theme.resolver(theme.CELDA_VACIA), fg=theme.resolver(theme.TEXTO))

    # ------------------------------------------------------------ scroll ratón

    def desplazar(self, pasos: int, horizontal: bool = False) -> bool:
        """Desplaza la tabla con la rueda; devuelve ``False`` si ya está en el límite.

        Antes la tabla se suscribía a la rueda de toda la aplicación (``bind_all``)
        al entrar el puntero y la desactivaba al salir con ``unbind_all``, lo que
        borraba también las suscripciones de cualquier otro componente. Ahora la
        rueda la reparte ``ui.rueda`` según el widget que está bajo el puntero.
        """
        vista = self._contenedor.xview() if horizontal else self._contenedor.yview()
        if (pasos < 0 and vista[0] <= 0.0) or (pasos > 0 and vista[1] >= 1.0):
            return False
        (self._contenedor.xview_scroll if horizontal else self._contenedor.yview_scroll)(pasos * 2, "units")
        return True
