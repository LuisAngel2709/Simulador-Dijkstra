"""Botón del selector de tema (luna / sol) para el encabezado de la aplicación.

Se dibuja como una imagen propia con suavizado (sin depender de Pillow ni de
emojis), de modo que la luna y el sol tienen exactamente el mismo tamaño y el
mismo peso visual. Solo cambia la imagen al alternar el tema: el widget no se
destruye ni se reposiciona.
"""

from __future__ import annotations

import math
import tkinter as tk
from typing import Callable

from . import theme

TAMANO = 32          # píxeles del botón (círculo con borde)
_SUBMUESTRAS = 4     # 4×4 muestras por píxel para el suavizado

ICONO_LUNA = "#0f172a"   # visible en modo claro: invita a pasar a oscuro
ICONO_SOL = "#fbbf24"    # visible en modo oscuro: invita a pasar a claro


def _hex_a_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _dentro_luna(x: float, y: float) -> bool:
    """Creciente: disco grande menos un disco desplazado hacia arriba-derecha."""
    en_disco = math.hypot(x - 0.0, y - 0.0) <= 7.0
    en_hueco = math.hypot(x - 3.6, y + 3.0) <= 6.0
    return en_disco and not en_hueco


def _dentro_sol(x: float, y: float) -> bool:
    """Disco central con ocho rayos."""
    r = math.hypot(x, y)
    if r <= 3.8:
        return True
    if 5.6 <= r <= 8.0:
        angulo = math.atan2(y, x)
        paso = math.pi / 4
        # distancia angular al rayo más cercano, convertida a distancia lineal
        desviacion = abs((angulo + paso / 2) % paso - paso / 2)
        return r * math.sin(min(desviacion, math.pi / 2)) <= 0.8
    return False


def _renderizar(modo: str, fondo: str, relleno: str, borde: str) -> tk.PhotoImage:
    icono = ICONO_SOL if modo == "oscuro" else ICONO_LUNA
    dentro_icono = _dentro_sol if modo == "oscuro" else _dentro_luna
    c_fondo, c_relleno, c_borde, c_icono = map(_hex_a_rgb, (fondo, relleno, borde, icono))
    centro = TAMANO / 2
    radio = TAMANO / 2 - 0.5
    n = _SUBMUESTRAS
    filas = []
    for py in range(TAMANO):
        fila = []
        for px in range(TAMANO):
            r = g = b = 0
            for sy in range(n):
                for sx in range(n):
                    x = px + (sx + 0.5) / n - centro
                    y = py + (sy + 0.5) / n - centro
                    distancia = math.hypot(x, y)
                    if distancia > radio:
                        c = c_fondo
                    elif distancia > radio - 1.2:
                        c = c_borde
                    elif dentro_icono(x, y):
                        c = c_icono
                    else:
                        c = c_relleno
                    r += c[0]; g += c[1]; b += c[2]
            total = n * n
            fila.append("#%02x%02x%02x" % (r // total, g // total, b // total))
        filas.append("{" + " ".join(fila) + "}")
    imagen = tk.PhotoImage(width=TAMANO, height=TAMANO)
    imagen.put(" ".join(filas))
    return imagen


class BotonTema(tk.Label):
    """Botón circular luna/sol. ``actualizar()`` lo repinta con el tema activo."""

    def __init__(self, master, comando: Callable[[], None]):
        super().__init__(master, bd=0, highlightthickness=0, cursor="hand2", takefocus=0)
        self._comando = comando
        self._encima = False
        self._cache: dict[tuple, tk.PhotoImage] = {}
        self.bind("<Button-1>", lambda _e: self._comando())
        self.bind("<Enter>", lambda _e: self._poner_hover(True))
        self.bind("<Leave>", lambda _e: self._poner_hover(False))
        self.actualizar()

    def _poner_hover(self, valor: bool) -> None:
        self._encima = valor
        self.actualizar()

    def actualizar(self) -> None:
        """Muestra el icono que invita al otro tema, con los colores del tema activo."""
        modo = theme.modo_actual()
        fondo = theme.resolver(theme.FONDO)
        relleno = theme.resolver(
            theme.BOTON_SECUNDARIO_HOVER if self._encima else theme.BOTON_SECUNDARIO
        )
        borde = theme.resolver(theme.BORDE)
        clave = (modo, fondo, relleno, borde)
        imagen = self._cache.get(clave)
        if imagen is None:
            imagen = self._cache[clave] = _renderizar(modo, fondo, relleno, borde)
        self.configure(image=imagen, bg=fondo)
        self.image = imagen  # evita que Tk libere la imagen
