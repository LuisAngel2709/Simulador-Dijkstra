"""Colores y fuentes compartidos por la interfaz.

Soporta modo claro y modo oscuro. Cada color del módulo (``theme.FONDO``,
``theme.TEXTO``, ...) es un par ``(claro, oscuro)``: CustomTkinter elige el
valor correcto por sí mismo cuando se llama a ``ctk.set_appearance_mode()``, sin
reconstruir ningún widget.

Los componentes que NO son de CustomTkinter (el ``tk.Canvas`` del grafo y las
celdas de la tabla) necesitan un color simple: para ellos se usa
``theme.resolver(color)``, que devuelve el valor del tema activo.
"""

from __future__ import annotations

# -------------------------------------------------------------------- paletas

_PALETA_CLARO = dict(
    FONDO="#f1f5f9",
    FONDO_CANVAS="#ffffff",
    PANEL="#ffffff",
    PANEL_SUAVE="#f8fafc",
    BORDE="#cbd5e1",
    BORDE_SUAVE="#e2e8f0",

    TEXTO="#0f172a",
    TEXTO_SUAVE="#334155",
    TEXTO_TENUE="#64748b",

    ACENTO="#2563eb",
    ACENTO_HOVER="#1d4ed8",
    ACENTO_SUAVE="#eff6ff",
    ACENTO_TEXTO="#ffffff",
    RESALTE="#f59e0b",          # contorno del elemento que explica el tutorial
    DIALOGO_FONDO="#eef2ff",    # ventanas de confirmación: azul-lavanda, distinto del tutorial (crema)
    DIALOGO_BORDE="#6366f1",
    TUTORIAL_FONDO="#fffbeb",   # tarjeta del tutorial: crema, distinta del blanco de la pantalla
    TUTORIAL_CAJA="#fef3c7",
    TUTORIAL_CAJA_BORDE="#fcd34d",

    BOTON_SECUNDARIO="#e2e8f0",
    BOTON_SECUNDARIO_HOVER="#cbd5e1",
    BOTON_SECUNDARIO_TEXTO="#0f172a",

    PELIGRO="#dc2626",
    PELIGRO_HOVER="#b91c1c",
    PELIGRO_TEXTO="#ffffff",

    # Vértices
    NODO="#f8fafc",
    NODO_BORDE="#94a3b8",
    NODO_VISITADO="#bfdbfe",
    NODO_ACTUAL="#fef08a",
    NODO_ORIGEN="#bbf7d0",
    NODO_DESTINO="#fbcfe8",
    NODO_SELECCION_EDITOR="#fed7aa",
    NODO_BORDE_ACTIVO="#1e293b",
    NODO_BORDE_VISITADO="#3b82f6",

    # Aristas
    ARISTA="#94a3b8",
    ARISTA_EVALUADA="#ca8a04",
    ARISTA_EMPATE="#ea580c",
    ARISTA_DESCARTADA="#be123c",
    ARISTA_CAMINO="#16a34a",

    ETIQUETA="#b45309",
    ETIQUETA_DESCARTADA="#94a3b8",

    # Tabla
    CELDA_VIGENTE="#bbf7d0",
    CELDA_EMPATE="#fef08a",
    CELDA_DESCARTADA="#f1f5f9",
    CELDA_VACIA="#ffffff",
    CABECERA="#e2e8f0",
)

_PALETA_OSCURO = dict(
    FONDO="#0f172a",
    FONDO_CANVAS="#1e293b",
    PANEL="#1e293b",
    PANEL_SUAVE="#1a2332",
    BORDE="#334155",
    BORDE_SUAVE="#2d3a4a",

    TEXTO="#e2e8f0",
    TEXTO_SUAVE="#94a3b8",
    TEXTO_TENUE="#64748b",

    ACENTO="#3b82f6",
    ACENTO_HOVER="#2563eb",
    ACENTO_SUAVE="#1e3a5f",
    ACENTO_TEXTO="#ffffff",
    RESALTE="#fbbf24",
    DIALOGO_FONDO="#232640",
    DIALOGO_BORDE="#818cf8",
    TUTORIAL_FONDO="#2b2a24",
    TUTORIAL_CAJA="#3a3524",
    TUTORIAL_CAJA_BORDE="#6b5a22",

    BOTON_SECUNDARIO="#334155",
    BOTON_SECUNDARIO_HOVER="#475569",
    BOTON_SECUNDARIO_TEXTO="#e2e8f0",

    PELIGRO="#ef4444",
    PELIGRO_HOVER="#dc2626",
    PELIGRO_TEXTO="#ffffff",

    # Vértices
    NODO="#334155",
    NODO_BORDE="#64748b",
    NODO_VISITADO="#1e3a5f",
    NODO_ACTUAL="#854d0e",
    NODO_ORIGEN="#166534",
    NODO_DESTINO="#9d174d",
    NODO_SELECCION_EDITOR="#92400e",
    NODO_BORDE_ACTIVO="#e2e8f0",
    NODO_BORDE_VISITADO="#60a5fa",

    # Aristas
    ARISTA="#64748b",
    ARISTA_EVALUADA="#f59e0b",
    ARISTA_EMPATE="#f97316",
    ARISTA_DESCARTADA="#f87171",
    ARISTA_CAMINO="#4ade80",

    ETIQUETA="#fbbf24",
    ETIQUETA_DESCARTADA="#64748b",

    # Tabla
    CELDA_VIGENTE="#166534",
    CELDA_EMPATE="#854d0e",
    CELDA_DESCARTADA="#1e293b",
    CELDA_VACIA="#1a2332",
    CABECERA="#334155",
)

# --------------------------------------------------------- estado del módulo

_modo_actual: str = "claro"

# Cada color es un par (claro, oscuro). Las claves de ambas paletas deben coincidir.
assert _PALETA_CLARO.keys() == _PALETA_OSCURO.keys()
globals().update({nombre: (_PALETA_CLARO[nombre], _PALETA_OSCURO[nombre]) for nombre in _PALETA_CLARO})

FAMILIA = "Segoe UI"

FUENTE_TITULO = (FAMILIA, 22, "bold")
FUENTE_SUBTITULO = (FAMILIA, 15, "bold")
FUENTE_NORMAL = (FAMILIA, 13)
FUENTE_PEQUENA = (FAMILIA, 12)
FUENTE_MONO = ("Consolas", 12)

FUENTE_NODO = (FAMILIA, 13, "bold")
FUENTE_ETIQUETA = (FAMILIA, 11, "bold")
FUENTE_ETIQUETA_TACHADA = (FAMILIA, 10, "overstrike")
FUENTE_PESO = (FAMILIA, 10, "bold")
FUENTE_MARCA = (FAMILIA, 9, "bold")
FUENTE_CELDA = (FAMILIA, 11)
FUENTE_CELDA_TACHADA = (FAMILIA, 11, "overstrike")


def modo_actual() -> str:
    """Devuelve ``'claro'`` u ``'oscuro'``."""
    return _modo_actual


def es_oscuro() -> bool:
    return _modo_actual == "oscuro"


def aplicar_modo(modo: str) -> None:
    """Registra el modo activo (``'claro'`` u ``'oscuro'``).

    No recolorea widgets: eso lo hace ``ctk.set_appearance_mode()`` para los de
    CustomTkinter y ``aplicar_tema()`` de cada componente para los de Tk puro.
    """
    global _modo_actual
    if modo not in ("claro", "oscuro"):
        raise ValueError(f"Modo desconocido: {modo!r}")
    _modo_actual = modo


def alternar_modo() -> str:
    """Cambia entre claro y oscuro y devuelve el nuevo modo."""
    nuevo = "oscuro" if _modo_actual == "claro" else "claro"
    aplicar_modo(nuevo)
    return nuevo


def resolver(color):
    """Devuelve el color simple (``"#rrggbb"``) del tema activo.

    Acepta un par ``(claro, oscuro)`` o un color ya simple (que devuelve igual).
    """
    if isinstance(color, (tuple, list)):
        return color[1] if _modo_actual == "oscuro" else color[0]
    return color
