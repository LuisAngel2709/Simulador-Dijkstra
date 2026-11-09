"""Dibuja los bloques de ``core.explicaciones`` en un CTkTextbox (solo lectura).

Los estilos se implementan con etiquetas (tags) del ``tk.Text`` interno. Sus
fuentes se derivan de la fuente ya escalada del propio cuadro, de modo que el
tamaño es coherente con el resto de la interfaz en cualquier escala de pantalla.
Los colores de las etiquetas se resuelven con el tema activo y se actualizan en
``aplicar_tema`` (el resto del cuadro cambia solo con CustomTkinter).
"""

from __future__ import annotations

import tkinter.font as tkfont

from core import explicaciones as ex

from . import theme

# estilo -> (negrita, monoespaciada, color del tema, sangría, espacio antes)
_ESTILOS = {
    ex.TITULO: dict(negrita=True, mono=False, color=theme.ACENTO, antes=8, despues=1),
    ex.TEXTO: dict(negrita=False, mono=False, color=None, antes=0, despues=2),
    ex.CALCULO: dict(negrita=True, mono=True, color=None, antes=2, despues=0),
    ex.TABLA: dict(negrita=False, mono=True, color=None, antes=0, despues=0),
    ex.NOTA: dict(negrita=False, mono=False, color=theme.TEXTO_TENUE, antes=2, despues=2),
    ex.EXITO: dict(negrita=True, mono=False, color=theme.ARISTA_CAMINO, antes=2, despues=2),
    ex.ALERTA: dict(negrita=True, mono=False, color=theme.PELIGRO, antes=2, despues=2),
}


def preparar(caja) -> None:
    """Crea (o recrea) las etiquetas de estilo de ``caja``."""
    texto = caja._textbox
    base = tkfont.Font(root=texto, font=texto.cget("font"))
    caja._fuentes_ricas = {}
    for estilo, cfg in _ESTILOS.items():
        fuente = base.copy()
        if cfg["negrita"]:
            fuente.configure(weight="bold")
        if cfg["mono"]:
            fuente.configure(family=theme.FUENTE_MONO[0])
        caja._fuentes_ricas[estilo] = fuente  # evita que Tk las libere
        sangria = 14 if estilo in (ex.CALCULO, ex.TABLA) else 0
        texto.tag_configure(
            estilo, font=fuente, spacing1=cfg["antes"], spacing3=cfg["despues"],
            lmargin1=sangria, lmargin2=sangria,
        )
    aplicar_tema(caja)


def aplicar_tema(caja) -> None:
    """Recolorea las etiquetas con el tema activo (no toca el contenido)."""
    for estilo, cfg in _ESTILOS.items():
        color = cfg["color"]
        if color is not None:
            caja._textbox.tag_configure(estilo, foreground=theme.resolver(color))
        else:
            caja._textbox.tag_configure(estilo, foreground="")  # hereda el color del cuadro


def escribir(caja, bloques, desplazar_arriba: bool = True) -> None:
    """Sustituye el contenido de ``caja`` por ``bloques``."""
    if not hasattr(caja, "_fuentes_ricas"):
        preparar(caja)
    caja.configure(state="normal")
    caja.delete("1.0", "end")
    texto = caja._textbox
    primero = True
    for bloque in bloques:
        if not primero:
            texto.insert("end", "\n")
        texto.insert("end", bloque.texto, bloque.estilo)
        primero = False
    caja.configure(state="disabled")
    if desplazar_arriba:
        caja.yview_moveto(0.0)
