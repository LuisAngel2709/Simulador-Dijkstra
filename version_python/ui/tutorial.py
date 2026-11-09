"""Motor del tutorial guiado: resalta un elemento de la interfaz y explica junto a él.

El tutorial se dibuja SOBRE la pantalla activa, sin tocarla:

* el resalte son cuatro filetes (``tk.Frame``) hijos de la ventana raíz que
  forman un contorno alrededor del elemento explicado;
* la explicación es una tarjeta (``CTkFrame``) que se coloca junto al elemento
  sin salirse de la ventana ni taparlo, siempre que haya sitio;
* cambiar de paso solo cambia textos y posiciones: no se destruye ni se crea
  ningún widget, y no se ejecuta nada de la pantalla (ni la simulación ni el
  editor). El usuario puede seguir usando la aplicación mientras el tutorial
  está abierto.

Tk no permite oscurecer parcialmente widgets hijos (no hay transparencia por
widget), por lo que la atención se dirige con el contorno de color y la tarjeta.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Callable, Sequence

import customtkinter as ctk

from . import theme

ANCHO_TARJETA = 390
ANCHO_TEXTO = ANCHO_TARJETA - 52
GROSOR = 3            # grosor del contorno de resalte
SEPARACION = 14       # distancia entre el elemento y la tarjeta
BORDE_VENTANA = 10    # margen mínimo entre la tarjeta y el borde de la ventana
INTERVALO_MS = 120    # cada cuánto se comprueba si el elemento se movió
UMBRAL_SIN_OBJETIVO = 4  # sondeos seguidos sin ver el elemento antes de darlo por oculto
MEDIDA_MINIMA = 300   # una ventana más pequeña que esto es una medida transitoria, no real


@dataclass
class PasoTutorial:
    """Un paso del recorrido.

    ``objetivo``: devuelve un widget, una lista de widgets (se resalta su unión) o None.
    ``preparar``: acción solo visual (p. ej. desplazar la página) previa al resalte.
    ``recorte``: devuelve el widget cuya área limita el resalte (la página con scroll).
    ``ejemplo``: texto dinámico «En tu grafo» calculado a partir del motor.
    """

    titulo: str
    texto: str
    objetivo: Callable[[], object] | None = None
    seccion: str = ""
    ejemplo: Callable[[], str] | None = None
    preparar: Callable[[], None] | None = None
    recorte: Callable[[], object] | None = None


Rect = tuple[int, int, int, int]  # x0, y0, x1, y1


def _solape(a: Rect, b: Rect) -> int:
    ancho = min(a[2], b[2]) - max(a[0], b[0])
    alto = min(a[3], b[3]) - max(a[1], b[1])
    return max(ancho, 0) * max(alto, 0)


def colocar_tarjeta(rect: Rect | None, ancho: int, alto: int, ventana: tuple[int, int],
                    separacion: int = SEPARACION, borde: int = BORDE_VENTANA) -> tuple[int, int]:
    """Esquina superior izquierda de la tarjeta: dentro de la ventana y lo menos solapada con ``rect``.

    Prueba a la derecha, izquierda, debajo y encima del elemento y, si ninguna
    cabe sin taparlo, las esquinas de la ventana; elige la de menor solape.
    """
    W, H = ventana
    x_max = max(W - ancho - borde, borde)
    y_max = max(H - alto - borde, borde)

    def limitar(x, y):
        return min(max(int(x), borde), x_max), min(max(int(y), borde), y_max)

    if rect is None:
        return limitar((W - ancho) / 2, (H - alto) / 2)
    x0, y0, x1, y1 = rect
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    candidatas = [
        limitar(x1 + separacion, cy - alto / 2),
        limitar(x0 - separacion - ancho, cy - alto / 2),
        limitar(cx - ancho / 2, y1 + separacion),
        limitar(cx - ancho / 2, y0 - separacion - alto),
        limitar(x_max, y_max), limitar(borde, y_max), limitar(x_max, borde), limitar(borde, borde),
    ]
    return min(candidatas, key=lambda c: _solape((c[0], c[1], c[0] + ancho, c[1] + alto), rect))


class Tutorial:
    def __init__(self, raiz: ctk.CTk, al_cerrar: Callable[[], None] | None = None):
        self.raiz = raiz
        self.al_cerrar = al_cerrar
        self.pasos: list[PasoTutorial] = []
        self.indice = 0
        self.activo = False
        self._pantalla = None
        self._ultimo = None
        self._after = None
        self._sin_objetivo = 0  # sondeos seguidos en que el elemento no se ve
        self._filetes: list[tk.Frame] = []
        self.tarjeta: ctk.CTkFrame | None = None

    # ------------------------------------------------------------------ ciclo de vida

    def iniciar(self, pasos: Sequence[PasoTutorial], pantalla=None) -> None:
        """Abre el tutorial en el primer paso (si ya estaba abierto, lo reinicia)."""
        if not pasos:
            return
        self.pasos = list(pasos)
        self.indice = 0
        self._pantalla = pantalla
        if not self.activo:
            self._construir()
            self.activo = True
            self._vigilar()
        self.ir_a(0)

    def salir(self) -> None:
        if not self.activo:
            return
        self.activo = False
        if self._after is not None:
            try:
                self.raiz.after_cancel(self._after)
            except Exception:
                pass
            self._after = None
        for filete in self._filetes:
            filete.destroy()
        self._filetes = []
        if self.tarjeta is not None:
            self.tarjeta.destroy()
            self.tarjeta = None
        self._pantalla = None
        if self.al_cerrar is not None:
            self.al_cerrar()

    def siguiente(self) -> None:
        if self.indice + 1 >= len(self.pasos):
            self.salir()
        else:
            self.ir_a(self.indice + 1)

    def anterior(self) -> None:
        if self.indice > 0:
            self.ir_a(self.indice - 1)

    # ------------------------------------------------------------------ construcción

    def _construir(self) -> None:
        self._filetes = [tk.Frame(self.raiz, bd=0, highlightthickness=0, bg=theme.resolver(theme.RESALTE))
                         for _ in range(4)]
        t = ctk.CTkFrame(self.raiz, fg_color=theme.TUTORIAL_FONDO, corner_radius=12,
                         border_width=2, border_color=theme.RESALTE, width=ANCHO_TARJETA)
        self.tarjeta = t
        # ancho constante entre pasos (minsize no se escala solo con el DPI de Windows)
        t.grid_columnconfigure(0, weight=1, minsize=round(ANCHO_TARJETA * self._escala()))

        fila = ctk.CTkFrame(t, fg_color="transparent")
        fila.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 0))
        fila.grid_columnconfigure(0, weight=1)
        self.etiqueta_seccion = ctk.CTkLabel(fila, text="", font=(theme.FAMILIA, 11, "bold"),
                                             text_color=theme.ACENTO, anchor="w")
        self.etiqueta_seccion.grid(row=0, column=0, sticky="w")
        self.etiqueta_progreso = ctk.CTkLabel(fila, text="", font=theme.FUENTE_PEQUENA,
                                              text_color=theme.TEXTO_TENUE)
        self.etiqueta_progreso.grid(row=0, column=1, sticky="e")

        self.barra = ctk.CTkProgressBar(t, height=4, corner_radius=2, fg_color=theme.BORDE_SUAVE,
                                        progress_color=theme.ACENTO)
        self.barra.grid(row=1, column=0, sticky="ew", padx=18, pady=(6, 10))

        self.etiqueta_titulo = ctk.CTkLabel(t, text="", font=theme.FUENTE_SUBTITULO, text_color=theme.TEXTO,
                                            anchor="w", justify="left", wraplength=ANCHO_TEXTO)
        self.etiqueta_titulo.grid(row=2, column=0, sticky="ew", padx=18)
        self.etiqueta_texto = ctk.CTkLabel(t, text="", font=theme.FUENTE_NORMAL, text_color=theme.TEXTO,
                                           anchor="w", justify="left", wraplength=ANCHO_TEXTO)
        self.etiqueta_texto.grid(row=3, column=0, sticky="ew", padx=18, pady=(6, 0))

        self.caja_ejemplo = ctk.CTkFrame(t, fg_color=theme.TUTORIAL_CAJA, corner_radius=8,
                                         border_width=1, border_color=theme.TUTORIAL_CAJA_BORDE)
        self.caja_ejemplo.grid(row=4, column=0, sticky="ew", padx=18, pady=(10, 0))
        ctk.CTkLabel(self.caja_ejemplo, text="EN TU GRAFO", font=(theme.FAMILIA, 10, "bold"),
                     text_color=theme.ACENTO, anchor="w").pack(anchor="w", padx=10, pady=(7, 0))
        self.etiqueta_ejemplo = ctk.CTkLabel(self.caja_ejemplo, text="", font=theme.FUENTE_PEQUENA,
                                             text_color=theme.TEXTO, anchor="w", justify="left",
                                             wraplength=ANCHO_TEXTO - 20)
        self.etiqueta_ejemplo.pack(anchor="w", padx=10, pady=(0, 8))

        self.etiqueta_aviso = ctk.CTkLabel(t, text="", font=theme.FUENTE_PEQUENA, text_color=theme.TEXTO_TENUE,
                                           anchor="w", justify="left", wraplength=ANCHO_TEXTO)
        self.etiqueta_aviso.grid(row=5, column=0, sticky="ew", padx=18, pady=(8, 0))

        botones = ctk.CTkFrame(t, fg_color="transparent")
        botones.grid(row=6, column=0, sticky="ew", padx=18, pady=(12, 16))
        botones.grid_columnconfigure(1, weight=1)
        estilo_sec = dict(fg_color=theme.BOTON_SECUNDARIO, hover_color=theme.BOTON_SECUNDARIO_HOVER,
                          text_color=theme.BOTON_SECUNDARIO_TEXTO, border_width=1, border_color=theme.BORDE)
        self.boton_salir = ctk.CTkButton(botones, text="Salir", width=64, height=32,
                                         font=(theme.FAMILIA, 12, "bold"), command=self.salir, **estilo_sec)
        self.boton_salir.grid(row=0, column=0)
        self.boton_anterior = ctk.CTkButton(botones, text="◀ Anterior", width=96, height=32,
                                            font=(theme.FAMILIA, 12, "bold"), command=self.anterior, **estilo_sec)
        self.boton_anterior.grid(row=0, column=2, padx=(0, 8))
        self.boton_siguiente = ctk.CTkButton(botones, text="Siguiente ▶", width=104, height=32,
                                             font=(theme.FAMILIA, 12, "bold"), command=self.siguiente,
                                             fg_color=theme.ACENTO, hover_color=theme.ACENTO_HOVER,
                                             text_color=theme.ACENTO_TEXTO)
        self.boton_siguiente.grid(row=0, column=3)

    # ------------------------------------------------------------------------ pasos

    def ir_a(self, indice: int) -> None:
        self.indice = indice
        paso = self.pasos[indice]
        if paso.preparar is not None:
            try:
                paso.preparar()
            except Exception:
                pass
        total = len(self.pasos)
        self.etiqueta_seccion.configure(text=paso.seccion.upper())
        self.etiqueta_progreso.configure(text=f"Paso {indice + 1} de {total}")
        self.barra.set((indice + 1) / total)
        self.etiqueta_titulo.configure(text=paso.titulo)
        self.etiqueta_texto.configure(text=paso.texto)
        ejemplo = paso.ejemplo() if paso.ejemplo is not None else ""
        if ejemplo:
            self.etiqueta_ejemplo.configure(text=ejemplo)
            self.caja_ejemplo.grid()
        else:
            self.caja_ejemplo.grid_remove()
        self.boton_anterior.configure(state="normal" if indice > 0 else "disabled")
        self.boton_siguiente.configure(text="Finalizar ✓" if indice == total - 1 else "Siguiente ▶")
        self._ultimo = None
        self._posicionar()

    # ----------------------------------------------------------------- geometría

    def _rect_objetivo(self, paso: PasoTutorial) -> Rect | None:
        """Rectángulo del elemento, en coordenadas de la ventana raíz, recortado a su área visible."""
        if paso.objetivo is None:
            return None
        objetivo = paso.objetivo()
        widgets = objetivo if isinstance(objetivo, (list, tuple)) else [objetivo]
        cajas = []
        for w in widgets:
            if w is None or not w.winfo_exists() or not w.winfo_viewable():
                continue
            cajas.append((w.winfo_rootx(), w.winfo_rooty(),
                          w.winfo_rootx() + w.winfo_width(), w.winfo_rooty() + w.winfo_height()))
        if not cajas:
            return None
        x0, y0 = min(c[0] for c in cajas), min(c[1] for c in cajas)
        x1, y1 = max(c[2] for c in cajas), max(c[3] for c in cajas)
        if paso.recorte is not None:
            r = paso.recorte()
            if r is not None and r.winfo_exists():
                x0, y0 = max(x0, r.winfo_rootx()), max(y0, r.winfo_rooty())
                x1, y1 = min(x1, r.winfo_rootx() + r.winfo_width()), min(y1, r.winfo_rooty() + r.winfo_height())
        if x1 <= x0 or y1 <= y0:
            return None
        rx, ry = self.raiz.winfo_rootx(), self.raiz.winfo_rooty()
        return x0 - rx, y0 - ry, x1 - rx, y1 - ry

    def _ventana_estable(self) -> bool:
        """False mientras la ventana está oculta o a medio redibujar (medidas no fiables)."""
        try:
            r = self.raiz
            return bool(r.winfo_viewable()) and r.winfo_width() >= MEDIDA_MINIMA and r.winfo_height() >= MEDIDA_MINIMA
        except tk.TclError:
            return False

    def _escala(self) -> float:
        """Factor de escala de CustomTkinter (1.0 salvo en pantallas con DPI alto)."""
        try:
            return float(ctk.ScalingTracker.get_widget_scaling(self.raiz))
        except Exception:
            return 1.0

    def rect_resaltado(self) -> Rect | None:
        """Rectángulo que se está resaltando ahora (None si el paso no resalta nada)."""
        return self._rect_objetivo(self.pasos[self.indice]) if self.activo else None

    def _posicionar(self) -> None:
        if not self.activo or self.tarjeta is None or not self._ventana_estable():
            return
        paso = self.pasos[self.indice]
        self.raiz.update_idletasks()
        rect = self._rect_objetivo(paso)
        ventana = (self.raiz.winfo_width(), self.raiz.winfo_height())
        self._ultimo = (rect, ventana)

        if paso.objetivo is not None and rect is None:
            self.etiqueta_aviso.configure(text="Este elemento no está visible ahora mismo.")
            self.etiqueta_aviso.grid()
        else:
            self.etiqueta_aviso.grid_remove()
        self.tarjeta.update_idletasks()
        ancho, alto = self.tarjeta.winfo_reqwidth(), self.tarjeta.winfo_reqheight()
        x, y = colocar_tarjeta(rect, ancho, alto, ventana)
        # CustomTkinter escala x e y de place() con el DPI; aquí x e y ya son píxeles reales.
        esc = self._escala()
        self.tarjeta.place(x=round(x / esc), y=round(y / esc))
        self.tarjeta.lift()

        if rect is None:
            for f in self._filetes:
                f.place_forget()
            return
        m, g = 4, GROSOR
        x0, y0, x1, y1 = rect[0] - m, rect[1] - m, rect[2] + m, rect[3] + m
        ancho_r, alto_r = x1 - x0, y1 - y0
        geometrias = [(x0, y0, ancho_r, g), (x0, y1 - g, ancho_r, g), (x0, y0, g, alto_r), (x1 - g, y0, g, alto_r)]
        for filete, (fx, fy, fw, fh) in zip(self._filetes, geometrias):
            filete.place(x=fx, y=fy, width=fw, height=fh)
            filete.lift()
        self.tarjeta.lift()

    def _vigilar(self) -> None:
        """Reposiciona si el elemento se movió (ventana redimensionada, página desplazada, tema...)."""
        if not self.activo:
            return
        try:
            if self._pantalla is not None and not self._pantalla.winfo_exists():
                self.salir()
                return
            paso = self.pasos[self.indice]
            if not self._ventana_estable():
                # La ventana se está redibujando (p. ej. al cambiar de tema Windows la oculta un
                # instante): se conserva la posición actual en vez de recolocar con medidas falsas.
                self._sin_objetivo = 0
            else:
                actual = (self._rect_objetivo(paso), (self.raiz.winfo_width(), self.raiz.winfo_height()))
                if actual[0] is None and paso.objetivo is not None and self._ultimo and self._ultimo[0] is not None:
                    # Un elemento que desaparece de golpe suele ser transitorio: solo se acepta si persiste.
                    self._sin_objetivo += 1
                    if self._sin_objetivo >= UMBRAL_SIN_OBJETIVO:
                        self._sin_objetivo = 0
                        self._posicionar()
                else:
                    self._sin_objetivo = 0
                    if actual != self._ultimo:
                        self._posicionar()
        except tk.TclError:
            self.salir()
            return
        self._after = self.raiz.after(INTERVALO_MS, self._vigilar)

    # ---------------------------------------------------------------------- tema

    def aplicar_tema(self) -> None:
        """Los widgets de CustomTkinter cambian solos; solo hay que recolorear los filetes (Tk puro)."""
        for filete in self._filetes:
            filete.configure(bg=theme.resolver(theme.RESALTE))
