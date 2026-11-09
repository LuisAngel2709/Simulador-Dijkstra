"""Enrutado de la rueda del ratón: cada gesto desplaza UN solo componente.

Problema que resuelve: la pantalla de simulación tiene varias zonas con
desplazamiento propio (tabla, cuadros de texto) dentro de una página que a su vez
puede desplazarse. Si cada una escucha la rueda por su cuenta, se pisan entre
sí (o ninguna responde). Aquí hay UN enrutador por aplicación, y la decisión se
toma según el widget que está bajo el puntero (no el que tiene el foco: en
Windows la rueda se entrega al widget con foco):

* si bajo el puntero hay un componente con desplazamiento propio que aún puede
  moverse en esa dirección, se desplaza ese componente;
* en caso contrario, se desplaza la página.
"""

from __future__ import annotations

import time
import tkinter as tk
from typing import Callable

_ENRUTADORES: dict[str, "EnrutadorRueda"] = {}

# Tras desplazar un componente, durante este tiempo (s) no se «encadena» a la
# página cuando llega a su límite, para que un gesto continuo no salte de zona.
RETENCION = 0.35


def _paso_de(evento) -> int:
    """-1 = hacia arriba, +1 = hacia abajo (en cualquier plataforma)."""
    numero = getattr(evento, "num", None)
    if numero == 4:
        return -1
    if numero == 5:
        return 1
    delta = getattr(evento, "delta", 0)
    if delta == 0:
        return 0
    magnitud = max(1, abs(int(delta)) // 120)
    return -magnitud if delta > 0 else magnitud


def enrutador_de(widget: tk.Misc) -> "EnrutadorRueda":
    """Enrutador único de la ventana de ``widget`` (se crea la primera vez)."""
    raiz = widget.winfo_toplevel()
    clave = str(raiz)
    enrutador = _ENRUTADORES.get(clave)
    if enrutador is None or not _existe(enrutador.raiz):
        enrutador = _ENRUTADORES[clave] = EnrutadorRueda(raiz)
    return enrutador


def _existe(widget) -> bool:
    try:
        return bool(widget.winfo_exists())
    except tk.TclError:
        return False


class EnrutadorRueda:
    def __init__(self, raiz: tk.Misc):
        self.raiz = raiz
        self.pagina = None  # PaginaDesplazable activa (o None)
        for secuencia in ("<MouseWheel>", "<Shift-MouseWheel>", "<Button-4>", "<Button-5>",
                          "<Shift-Button-4>", "<Shift-Button-5>"):
            raiz.bind_all(secuencia, self._al_girar, add="+")

    def activar(self, pagina) -> None:
        self.pagina = pagina

    def desactivar(self, pagina) -> None:
        if self.pagina is pagina:
            self.pagina = None

    def _al_girar(self, evento):
        pagina = self.pagina
        if pagina is None or not _existe(pagina):
            return None
        pagina.desplazar_con_rueda(evento)
        return None


class RuedaPagina:
    """Lógica de reparto; la usa ``PaginaDesplazable`` (ver ``pagina_desplazable.py``)."""

    def __init__(self, pagina):
        self.pagina = pagina
        self._propietarios: dict[tk.Misc, Callable[[int, bool], bool]] = {}
        self._ultimo: tuple[tk.Misc, float] | None = None

    def registrar(self, widget: tk.Misc, mover: Callable[[int, bool], bool]) -> None:
        """``mover(pasos, horizontal)`` desplaza el componente y devuelve si pudo."""
        self._propietarios[widget] = mover

    def registrar_texto(self, caja) -> None:
        """Registra un CTkTextbox/tk.Text: su desplazamiento nativo se sustituye por el enrutado."""
        texto = getattr(caja, "_textbox", caja)

        def mover(pasos: int, horizontal: bool) -> bool:
            primero, ultimo = texto.xview() if horizontal else texto.yview()
            if (pasos < 0 and primero <= 0.0) or (pasos > 0 and ultimo >= 1.0):
                return False
            (texto.xview_scroll if horizontal else texto.yview_scroll)(pasos * 2 if not horizontal else pasos, "units")
            return True

        self.registrar(caja, mover)
        self.registrar(texto, mover)

        def al_girar(evento):
            self.repartir(evento)
            return "break"  # evita que Tk lo desplace además por su cuenta

        for secuencia in ("<MouseWheel>", "<Shift-MouseWheel>", "<Button-4>", "<Button-5>"):
            texto.bind(secuencia, al_girar)

    def repartir(self, evento) -> None:
        pasos = _paso_de(evento)
        if pasos == 0:
            return
        horizontal = bool(getattr(evento, "state", 0) & 0x0001)  # Mayús + rueda
        destino = self.pagina.winfo_containing(evento.x_root, evento.y_root)
        if destino is None or not self._es_de_la_pagina(destino):
            return
        widget = destino
        while widget is not None:
            mover = self._propietarios.get(widget)
            if mover is not None:
                if mover(pasos, horizontal):
                    self._ultimo = (widget, time.monotonic())
                    return
                if self._ultimo and self._ultimo[0] is widget and time.monotonic() - self._ultimo[1] < RETENCION:
                    return  # el gesto empezó en este componente: no saltar a la página
                break
            if widget is self.pagina:
                break
            widget = getattr(widget, "master", None)
        if not horizontal:
            self.pagina.desplazar(pasos)

    def _es_de_la_pagina(self, widget) -> bool:
        while widget is not None:
            if widget is self.pagina:
                return True
            widget = getattr(widget, "master", None)
        return False
