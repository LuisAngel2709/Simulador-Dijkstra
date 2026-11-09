"""Dibujo del grafo sobre un Canvas de Tkinter.

Layout por capas (izquierda → derecha), determinista y estable: las posiciones
dependen solo de la estructura del grafo, nunca del azar ni del paso de la
simulación.

  1. capa de cada vértice = camino más largo que llega hasta él;
  2. orden dentro de cada capa = heurística de la mediana, con pasadas hacia
     adelante y hacia atrás, quedándose con el orden que produce menos cruces;
  3. las aristas entre capas consecutivas se dibujan rectas y las que saltan
     capas se desvían por fuera de los vértices intermedios;
  4. cada peso se coloca sobre su arista en el primer hueco libre.
"""

from __future__ import annotations

import math
import tkinter as tk
import tkinter.font as tkfont

import customtkinter as ctk

from core.dijkstra_engine import INFINITO, texto_etiqueta

from . import theme

RADIO = 21
MARGEN_BORDE = RADIO + 4     # 25 px: distancia uniforme al borde del canvas
MARGEN_X = MARGEN_BORDE
MARGEN_Y = MARGEN_BORDE
SEPARACION_MAXIMA_Y = 130

PASADAS_DE_ORDENACION = 4
MARGEN_ESQUIVA = 26          # holgura al rodear un vértice intermedio
SEPARACION_ARISTAS = 16      # separación entre aristas largas del mismo tramo


# --------------------------------------------------------------------- layout


def calcular_capas(grafo) -> dict[str, int]:
    """Capa de cada vértice = longitud del camino más largo que llega hasta él."""
    capas = {v: 0 for v in grafo.vertices}
    for v in grafo.orden_topologico():
        for destino, _ in grafo.salientes(v):
            capas[destino] = max(capas[destino], capas[v] + 1)
    return capas


def _mediana(valores: list[float]) -> float | None:
    if not valores:
        return None
    ordenados = sorted(valores)
    mitad = len(ordenados) // 2
    if len(ordenados) % 2:
        return ordenados[mitad]
    return (ordenados[mitad - 1] + ordenados[mitad]) / 2


def _contar_cruces(aristas, capas, posicion) -> int:
    """Cruces aproximados: dos aristas se cruzan si sus tramos horizontales se
    solapan y el orden vertical de sus extremos se invierte."""
    tramos = [
        (capas[u], posicion[u], capas[v], posicion[v]) for u, v in aristas
    ]
    cruces = 0
    for i in range(len(tramos)):
        c1u, p1u, c1v, p1v = tramos[i]
        for j in range(i + 1, len(tramos)):
            c2u, p2u, c2v, p2v = tramos[j]
            if min(c1u, c1v) >= max(c2u, c2v) or min(c2u, c2v) >= max(c1u, c1v):
                continue
            if (p1u - p2u) * (p1v - p2v) < 0:
                cruces += 1
    return cruces


def ordenar_por_capas(grafo, capas: dict[str, int]) -> dict[int, list[str]]:
    """Ordena los vértices de cada capa para reducir los cruces de aristas."""
    por_capa: dict[int, list[str]] = {}
    for v in sorted(grafo.vertices):
        por_capa.setdefault(capas[v], []).append(v)

    aristas = [(u, v) for u, v, _ in grafo.aristas()]
    orden = {capa: list(vs) for capa, vs in por_capa.items()}

    def posiciones(actual) -> dict[str, int]:
        return {v: i for vs in actual.values() for i, v in enumerate(vs)}

    mejor = {capa: list(vs) for capa, vs in orden.items()}
    mejores_cruces = _contar_cruces(aristas, capas, posiciones(orden))

    for pasada in range(PASADAS_DE_ORDENACION):
        hacia_adelante = pasada % 2 == 0
        capas_recorridas = sorted(orden) if hacia_adelante else sorted(orden, reverse=True)
        pos = posiciones(orden)
        for capa in capas_recorridas:
            vecinos_de = grafo.entrantes if hacia_adelante else grafo.salientes
            referencia = {}
            for v in orden[capa]:
                valores = [pos[w] for w, _ in vecinos_de(v) if w in pos]
                referencia[v] = _mediana(valores)
            # Los vértices sin vecinos en esa dirección conservan su sitio.
            for i, v in enumerate(orden[capa]):
                if referencia[v] is None:
                    referencia[v] = i
            orden[capa] = sorted(orden[capa], key=lambda v: (referencia[v], v))
            pos = posiciones(orden)

        cruces = _contar_cruces(aristas, capas, pos)
        if cruces < mejores_cruces:
            mejores_cruces = cruces
            mejor = {capa: list(vs) for capa, vs in orden.items()}

    return mejor


# ---------------------------------------------------------------------- curvas


def _punto_medio(p, q) -> tuple[float, float]:
    return ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)


def _punto_bezier(p0, p1, p2, t: float) -> tuple[float, float]:
    u = 1 - t
    return (
        u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
        u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1],
    )


def _muestrear_bezier(p0, p1, p2, pasos: int = 22) -> list[tuple[float, float]]:
    return [_punto_bezier(p0, p1, p2, i / pasos) for i in range(pasos + 1)]


def _recortar_extremos(puntos, centro_inicio, centro_fin, radio):
    """Deja la polilínea entre los bordes de los dos vértices."""
    def fuera(p, centro):
        return math.dist(p, centro) >= radio

    recortados = [
        p for p in puntos if fuera(p, centro_inicio) and fuera(p, centro_fin)
    ]
    return recortados if len(recortados) >= 2 else [puntos[0], puntos[-1]]


ALTO_MARCA = 18        # alto de la etiqueta «ORIGEN» / «DESTINO»
HUECO_MARCA = 6        # separación entre la marca y el borde del vértice


class GrafoCanvas(ctk.CTkFrame):
    """Canvas del grafo. Solo dibuja y permite interacción visual con los nodos."""

    def __init__(self, master, al_hacer_clic_en_nodo=None, al_hacer_clic_en_peso=None, **kwargs):
        super().__init__(master, fg_color=theme.FONDO_CANVAS, corner_radius=10, **kwargs)
        self.al_hacer_clic_en_nodo = al_hacer_clic_en_nodo
        # Solo el editor lo usa: ``al_hacer_clic_en_peso(u, v)`` al pulsar el número de una arista.
        self.al_hacer_clic_en_peso = al_hacer_clic_en_peso
        self._cajas_peso: dict[tuple[str, str], tuple[float, float, float, float]] = {}
        self._peso_presionado: tuple[str, str] | None = None
        self._editor_peso: tuple[tuple[str, str], tk.Entry, int, object] | None = None

        self.canvas = tk.Canvas(
            self, bg=theme.resolver(theme.FONDO_CANVAS), highlightthickness=0, bd=0
        )
        self.canvas.pack(fill="both", expand=True, padx=6, pady=6)
        self.canvas.bind("<Configure>", lambda _e: self.redibujar())

        # Interacción de arrastrar y soltar (Drag & Drop) y selección
        self.canvas.bind("<ButtonPress-1>", self._al_presionar)
        self.canvas.bind("<B1-Motion>", self._al_arrastrar)
        self.canvas.bind("<ButtonRelease-1>", self._al_soltar)
        self.canvas.bind("<Motion>", self._al_mover_raton)
        self.canvas.bind("<Leave>", self._al_salir_canvas)

        self.grafo = None
        self._capas: dict[str, int] = {}
        self._por_capa: dict[int, list[str]] = {}
        self._posiciones: dict[str, tuple[float, float]] = {}
        self._posiciones_relativas: dict[str, tuple[float, float]] = {}
        self._ocupados: list[tuple[float, float, float, float]] = []

        # Estado del arrastre
        self._vertice_arrastrado: str | None = None
        self._arrastre_inicio: tuple[float, float] = (0.0, 0.0)
        self._ha_arrastrado: bool = False

        self.snapshot = None
        self.origen = None
        self.destino = None
        self.seleccion_editor: list[str] = []
        self.mostrar_etiquetas = True
        self.origen_preview: str | None = None
        self.destino_preview: str | None = None
        self._cursor_x: float = -1.0
        self._cursor_y: float = -1.0

    # ------------------------------------------------------------------- estado

    def establecer_grafo(
        self,
        grafo,
        posiciones: dict[str, tuple[float, float]] | None = None,
        modo_layout: str = "capas",
    ) -> None:
        self.grafo = grafo
        self._capas = calcular_capas(grafo)
        self._por_capa = ordenar_por_capas(grafo, self._capas)

        if posiciones is not None:
            # Posiciones explícitas pasadas
            nuevas_rel: dict[str, tuple[float, float]] = {}
            for v, (x, y) in posiciones.items():
                if x > 1.0 or y > 1.0:
                    nuevas_rel[v] = self._coordenada_relativa(x, y)
                else:
                    nuevas_rel[v] = (max(0.0, min(1.0, x)), max(0.0, min(1.0, y)))
            self._posiciones_relativas = nuevas_rel
        else:
            # Si ya tenemos posiciones relativas para los mismos vértices, se conservan
            mismos_vertices = (
                set(self._posiciones_relativas.keys()) == set(grafo.vertices)
                if self._posiciones_relativas
                else False
            )
            if not mismos_vertices:
                if modo_layout == "circular":
                    self._distribuir_en_circulo()
                else:
                    self._calcular_posiciones_capas()

        self.redibujar()

    def actualizar_estado(self, **cambios) -> None:
        for clave, valor in cambios.items():
            setattr(self, clave, valor)
        if "origen_preview" in cambios and not self.origen_preview:
            self.limpiar_preview_arista()
        self.redibujar()

    def obtener_posiciones(self) -> dict[str, tuple[float, float]]:
        """Devuelve las posiciones relativas normalizadas (0.0 a 1.0) de los vértices."""
        return dict(self._posiciones_relativas)

    def reorganizar_en_circulo(self) -> None:
        """Restablece los nodos en una distribución circular amplia y limpia."""
        self._distribuir_en_circulo()
        self.redibujar()

    # ------------------------------------------------------------------ posiciones

    def _coordenada_absoluta(self, rx: float, ry: float) -> tuple[float, float]:
        ancho = max(self.canvas.winfo_width(), 420)
        alto = max(self.canvas.winfo_height(), 320)
        pad_x = MARGEN_X
        pad_y = MARGEN_Y
        x = pad_x + rx * (ancho - 2 * pad_x)
        y = pad_y + ry * (alto - 2 * pad_y)
        return (x, y)

    def _coordenada_relativa(self, x: float, y: float) -> tuple[float, float]:
        ancho = max(self.canvas.winfo_width(), 420)
        alto = max(self.canvas.winfo_height(), 320)
        pad_x = MARGEN_X
        pad_y = MARGEN_Y
        util_x = max(ancho - 2 * pad_x, 1)
        util_y = max(alto - 2 * pad_y, 1)
        rx = max(0.0, min(1.0, (x - pad_x) / util_x))
        ry = max(0.0, min(1.0, (y - pad_y) / util_y))
        return (rx, ry)

    def _distribuir_en_circulo(self) -> None:
        """Distribuye los vértices en un óvalo amplio y bien espaciado."""
        if not self.grafo or not self.grafo.vertices:
            return
        vertices = list(self.grafo.vertices)
        n = len(vertices)
        self._posiciones_relativas = {}
        for i, v in enumerate(vertices):
            # Empieza arriba (-pi/2) y gira en sentido horario
            angulo = -math.pi / 2 + (2 * math.pi * i) / n
            rx = 0.5 + 0.40 * math.cos(angulo)
            ry = 0.5 + 0.38 * math.sin(angulo)
            self._posiciones_relativas[v] = (rx, ry)

    def _calcular_posiciones_capas(self) -> None:
        """Calcula una distribución inicial basada en capas."""
        if not self.grafo or not self._por_capa:
            return
        total_capas = max(self._por_capa) + 1
        mayor_capa = max(len(vs) for vs in self._por_capa.values())
        self._posiciones_relativas = {}

        for capa, vertices in self._por_capa.items():
            if total_capas > 1:
                rx = 0.08 + 0.84 * (capa / (total_capas - 1))
            else:
                rx = 0.5
            total_v = len(vertices)
            for indice, v in enumerate(vertices):
                if mayor_capa > 1:
                    paso_rel = min(0.76 / (mayor_capa - 1), 0.32)
                else:
                    paso_rel = 0.0
                ry = 0.5 - paso_rel * (total_v - 1) / 2 + indice * paso_rel
                ry = max(0.05, min(0.95, ry))
                self._posiciones_relativas[v] = (rx, ry)

    def _sincronizar_posiciones_absolutas(self) -> None:
        if not self.grafo:
            return
        for v in self.grafo.vertices:
            if v not in self._posiciones_relativas:
                self._posiciones_relativas[v] = (0.5, 0.5)
        self._posiciones = {
            v: self._coordenada_absoluta(*self._posiciones_relativas[v])
            for v in self.grafo.vertices
        }

    def _vertice_en(self, x: float, y: float) -> str | None:
        for v, (vx, vy) in self._posiciones.items():
            if (x - vx) ** 2 + (y - vy) ** 2 <= (RADIO + 5) ** 2:
                return v
        return None

    # ------------------------------------------------------------- drag & drop

    def _al_presionar(self, evento) -> None:
        self.canvas.focus_set()
        vertice = self._vertice_en(evento.x, evento.y)
        if vertice:
            self._vertice_arrastrado = vertice
            self._arrastre_inicio = (float(evento.x), float(evento.y))
            self._ha_arrastrado = False
        else:
            self._vertice_arrastrado = None
            self._ha_arrastrado = False
            # Clic sobre el número de una arista (solo si quien usa el canvas lo pidió)
            self._peso_presionado = self._peso_en(evento.x, evento.y) if self.al_hacer_clic_en_peso else None

    def _peso_en(self, x: float, y: float) -> tuple[str, str] | None:
        """Arista cuyo recuadro de peso contiene el punto (x, y), o ``None``."""
        for clave, (x0, y0, x1, y1) in self._cajas_peso.items():
            if x0 - 2 <= x <= x1 + 2 and y0 - 2 <= y <= y1 + 2:
                return clave
        return None

    def _al_arrastrar(self, evento) -> None:
        if not self._vertice_arrastrado:
            return
        x0, y0 = self._arrastre_inicio
        if not self._ha_arrastrado:
            if math.hypot(evento.x - x0, evento.y - y0) > 4:
                self._ha_arrastrado = True
                self.canvas.configure(cursor="fleur")
        if self._ha_arrastrado:
            w = max(self.canvas.winfo_width(), 420)
            h = max(self.canvas.winfo_height(), 320)
            lim_x = max(MARGEN_X, min(w - MARGEN_X, float(evento.x)))
            lim_y = max(MARGEN_Y, min(h - MARGEN_Y, float(evento.y)))

            self._posiciones[self._vertice_arrastrado] = (lim_x, lim_y)
            rx, ry = self._coordenada_relativa(lim_x, lim_y)
            self._posiciones_relativas[self._vertice_arrastrado] = (rx, ry)
            self.limpiar_preview_arista()
            self.redibujar(actualizar_posiciones_absolutas=False)

    def _al_soltar(self, evento) -> None:
        vertice = self._vertice_arrastrado
        ha_arrastrado = self._ha_arrastrado
        self._vertice_arrastrado = None
        self._ha_arrastrado = False
        self._actualizar_cursor(evento.x, evento.y)
        peso, self._peso_presionado = self._peso_presionado, None
        if peso is not None and self.al_hacer_clic_en_peso and self._peso_en(evento.x, evento.y) == peso:
            self.al_hacer_clic_en_peso(*peso)
            return

        if vertice and not ha_arrastrado:
            if self.al_hacer_clic_en_nodo:
                self.al_hacer_clic_en_nodo(vertice)
        elif ha_arrastrado:
            self.redibujar()

    def _al_mover_raton(self, evento) -> None:
        self._cursor_x = float(evento.x)
        self._cursor_y = float(evento.y)
        if not self._vertice_arrastrado:
            self._actualizar_cursor(evento.x, evento.y)
            if self.origen_preview and not self.destino_preview:
                self._actualizar_preview_arista(evento.x, evento.y)

    def _al_salir_canvas(self, _evento) -> None:
        self._cursor_x = -1.0
        self._cursor_y = -1.0
        self.canvas.configure(cursor="")
        if not self.destino_preview:
            self.limpiar_preview_arista()

    def limpiar_preview_arista(self) -> None:
        """Elimina cualquier flecha provisional dibujada sobre el canvas."""
        self.canvas.delete("preview_arista")

    def _actualizar_preview_arista(self, x: float = -1.0, y: float = -1.0) -> None:
        self.canvas.delete("preview_arista")
        if not self.origen_preview or self.origen_preview not in self._posiciones:
            return

        p0 = self._posiciones[self.origen_preview]

        # Caso 1: Destino fijo ya seleccionado (se mantiene hasta ingresar el peso)
        if self.destino_preview and self.destino_preview in self._posiciones:
            p2 = self._posiciones[self.destino_preview]
            dx = p2[0] - p0[0]
            dy = p2[1] - p0[1]
            dist = math.hypot(dx, dy)
            if dist > 2 * RADIO:
                ux, uy = dx / dist, dy / dist
                x1 = p0[0] + RADIO * ux
                y1 = p0[1] + RADIO * uy
                x2 = p2[0] - RADIO * ux
                y2 = p2[1] - RADIO * uy
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=theme.resolver(theme.ACENTO),
                    width=3,
                    arrow=tk.LAST,
                    arrowshape=(14, 16, 6),
                    tags=("preview_arista",),
                )
            return

        # Caso 2: Solo origen seleccionado, sigue al cursor o se orienta al vértice hover
        if x < 0 or y < 0:
            return

        dest = self._vertice_en(x, y)
        if dest and dest != self.origen_preview and dest in self._posiciones:
            p2 = self._posiciones[dest]
            dx = p2[0] - p0[0]
            dy = p2[1] - p0[1]
            dist = math.hypot(dx, dy)
            if dist > 2 * RADIO:
                ux, uy = dx / dist, dy / dist
                x1 = p0[0] + RADIO * ux
                y1 = p0[1] + RADIO * uy
                x2 = p2[0] - RADIO * ux
                y2 = p2[1] - RADIO * uy
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=theme.resolver(theme.ACENTO),
                    width=3,
                    arrow=tk.LAST,
                    arrowshape=(14, 16, 6),
                    tags=("preview_arista",),
                )
        elif dest != self.origen_preview:
            dx = x - p0[0]
            dy = y - p0[1]
            dist = math.hypot(dx, dy)
            if dist > RADIO + 4:
                ux, uy = dx / dist, dy / dist
                x1 = p0[0] + RADIO * ux
                y1 = p0[1] + RADIO * uy
                self.canvas.create_line(
                    x1, y1, x, y,
                    fill=theme.resolver(theme.ACENTO),
                    width=2,
                    dash=(6, 4),
                    arrow=tk.LAST,
                    arrowshape=(12, 14, 5),
                    tags=("preview_arista",),
                )

    def _actualizar_cursor(self, x: float, y: float) -> None:
        if self._vertice_en(x, y) or (self.al_hacer_clic_en_peso and self._peso_en(x, y)):
            self.canvas.configure(cursor="hand2")
        else:
            self.canvas.configure(cursor="")

    # --------------------------------------------------------------------- dibujo

    def aplicar_tema(self) -> None:
        """Recolorea el canvas con el tema activo sin tocar el estado ni las posiciones.

        El marco (CTkFrame) ya cambia solo con ``set_appearance_mode``; el ``tk.Canvas``
        necesita un color simple y sus elementos se vuelven a dibujar tal cual
        están (mismas posiciones, mismo estado del grafo).
        """
        self.cerrar_editor_peso()
        self.canvas.configure(bg=theme.resolver(theme.FONDO_CANVAS))
        self.redibujar(actualizar_posiciones_absolutas=False)

    def redibujar(self, actualizar_posiciones_absolutas: bool = True) -> None:
        self.canvas.delete("all")
        if not self.grafo:
            return
        if actualizar_posiciones_absolutas:
            self._sincronizar_posiciones_absolutas()
        self._reservar_zonas_de_vertices()
        self._cajas_peso = {}
        self._dibujar_aristas()
        self._dibujar_vertices()
        self._reubicar_editor_peso()
        if self.origen_preview:
            if self.destino_preview:
                self._actualizar_preview_arista()
            elif self._cursor_x >= 0 and self._cursor_y >= 0:
                self._actualizar_preview_arista(self._cursor_x, self._cursor_y)

    @staticmethod
    def _distancia_punto_segmento(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
        px, py = p
        ax, ay = a
        bx, by = b
        dx = bx - ax
        dy = by - ay
        longitud_sq = dx * dx + dy * dy
        if longitud_sq == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / longitud_sq))
        proj_x = ax + t * dx
        proj_y = ay + t * dy
        return math.hypot(px - proj_x, py - proj_y)

    def _posicion_etiqueta_vertice(self, v: str, x: float, y: float) -> str:
        """Determina si la etiqueta debe colocarse 'arriba' o 'abajo' según las aristas incidentes."""
        alto_canvas = self.canvas.winfo_height() or 500
        marca_arriba = self._marca_de_vertice(v) is not None and self._lado_de_marca(y) == "arriba"
        if y < RADIO + 48 + (ALTO_MARCA + 4 if marca_arriba else 0):
            return "abajo"
        if y > alto_canvas - RADIO - 48:
            return "arriba"

        candidato_arriba = (x, y - RADIO - 15)
        candidato_abajo = (x, y + RADIO + 15)

        dist_min_arriba = float("inf")
        dist_min_abajo = float("inf")

        if self.grafo:
            vecinos = set(u for u, _ in self.grafo.entrantes(v)) | set(w for w, _ in self.grafo.salientes(v))
            for vec in vecinos:
                if vec in self._posiciones:
                    pos_vec = self._posiciones[vec]
                    d_arr = self._distancia_punto_segmento(candidato_arriba, pos_vec, (x, y))
                    d_abj = self._distancia_punto_segmento(candidato_abajo, pos_vec, (x, y))
                    dist_min_arriba = min(dist_min_arriba, d_arr)
                    dist_min_abajo = min(dist_min_abajo, d_abj)

        # Si abajo está notablemente más despejado de aristas que arriba, colocar abajo
        if dist_min_abajo > dist_min_arriba + 6:
            return "abajo"
        return "arriba"

    def _reservar_zonas_de_vertices(self) -> None:
        """Zonas que los pesos deben evitar: los vértices y sus etiquetas."""
        self._ocupados = []
        for v, (x, y) in self._posiciones.items():
            self._ocupados.append((x - RADIO - 6, y - RADIO - 6, x + RADIO + 6, y + RADIO + 6))
            if self.snapshot:
                pos = self._posicion_etiqueta_vertice(v, x, y)
                ancho = 65
                extra = self._desvio_por_marca(v, y, pos)
                if pos == "arriba":
                    self._ocupados.append((x - ancho, y - RADIO - 42 - extra, x + ancho, y - RADIO - extra))
                else:
                    self._ocupados.append((x - ancho, y + RADIO + extra, x + ancho, y + RADIO + 42 + extra))
            rect_marca = self._rectangulo_de_marca(v, x, y)
            if rect_marca:
                self._ocupados.append(tuple(c + d for c, d in zip(rect_marca, (-4, -4, 4, 4))))

    def _estilo_de_arista(self, u: str, v: str) -> tuple[str, int]:
        snapshot = self.snapshot
        if snapshot:
            if (u, v) in snapshot.aristas_camino:
                return theme.resolver(theme.ARISTA_CAMINO), 4
            for a, b, tipo in snapshot.aristas_evaluadas:
                if (a, b) == (u, v):
                    if tipo == "mejora":
                        return theme.resolver(theme.ARISTA_EVALUADA), 3
                    if tipo == "empate":
                        return theme.resolver(theme.ARISTA_EMPATE), 3
                    return theme.resolver(theme.ARISTA_DESCARTADA), 2
        return theme.resolver(theme.ARISTA), 2

    def _dibujar_aristas(self) -> None:
        usos_por_tramo: dict[tuple[str, str], int] = {}
        for u, v, peso in self.grafo.aristas():
            if u not in self._posiciones or v not in self._posiciones:
                continue
            tramo = (u, v)
            indice = usos_por_tramo.get(tramo, 0)
            usos_por_tramo[tramo] = indice + 1

            color, grosor = self._estilo_de_arista(u, v)
            p0 = self._posiciones[u]
            p2 = self._posiciones[v]
            control = self._punto_de_control(u, v, p0, p2, indice)

            puntos = _recortar_extremos(_muestrear_bezier(p0, control, p2), p0, p2, RADIO)
            coordenadas = [c for punto in puntos for c in punto]
            self.canvas.create_line(
                *coordenadas, fill=color, width=grosor, smooth=True,
                arrow=tk.LAST, arrowshape=(12, 14, 5),
            )
            self._dibujar_peso(puntos, peso, color, (u, v))

    def _punto_de_control(
        self, u: str, v: str, p0: tuple[float, float], p2: tuple[float, float], indice: int
    ) -> tuple[float, float]:
        """Control de la curva: recta limpia por defecto; si otro vértice está
        en la trayectoria, se desvía suavemente para esquivarlo."""
        dx = p2[0] - p0[0]
        dy = p2[1] - p0[1]
        distancia = math.hypot(dx, dy)
        medio = ((p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2)

        if distancia < 1:
            return medio

        ux = dx / distancia
        uy = dy / distancia
        nx = -uy
        ny = ux

        estorbos: list[float] = []
        for w, pw in self._posiciones.items():
            if w == u or w == v:
                continue
            t = ((pw[0] - p0[0]) * dx + (pw[1] - p0[1]) * dy) / (distancia ** 2)
            if 0.08 < t < 0.92:
                offset_perp = (pw[0] - p0[0]) * nx + (pw[1] - p0[1]) * ny
                if abs(offset_perp) < RADIO + MARGEN_ESQUIVA:
                    estorbos.append(offset_perp)

        if not estorbos:
            if indice == 0:
                return medio
            desvio = SEPARACION_ARISTAS * indice * (1 if indice % 2 else -1)
            return (medio[0] + nx * desvio, medio[1] + ny * desvio)

        promedio_offset = sum(estorbos) / len(estorbos)
        signo = -1.0 if promedio_offset >= 0 else 1.0
        magnitud = (RADIO + MARGEN_ESQUIVA + 12) + (SEPARACION_ARISTAS * indice)
        desvio_total = signo * magnitud
        return (medio[0] + nx * desvio_total * 2, medio[1] + ny * desvio_total * 2)

    def _dibujar_peso(self, puntos, peso, color, arista=None) -> None:
        texto = str(peso)
        ancho = 9 + 5 * len(texto)
        alto = 18
        for posicion in self._candidatos_de_peso(puntos):
            x, y = posicion
            rectangulo = (x - ancho / 2, y - alto / 2, x + ancho / 2, y + alto / 2)
            if not self._colisiona(rectangulo):
                break
        else:  # ningún hueco libre: se usa el centro de la arista
            x, y = puntos[len(puntos) // 2]
            rectangulo = (x - ancho / 2, y - alto / 2, x + ancho / 2, y + alto / 2)

        self._ocupados.append(rectangulo)
        if arista is not None:
            self._cajas_peso[arista] = rectangulo
        self.canvas.create_rectangle(
            *rectangulo, fill=theme.resolver(theme.FONDO_CANVAS), outline=color, width=1
        )
        self.canvas.create_text(x, y, text=texto, fill=theme.resolver(theme.TEXTO), font=theme.FUENTE_PESO)

    # ------------------------------------------------------ edición del peso en línea

    def abrir_editor_peso(self, u: str, v: str, valor_actual, al_confirmar) -> None:
        """Muestra un campo pequeño sobre el número de la arista u → v.

        Enter confirma llamando a ``al_confirmar(texto)``: si devuelve ``False`` (valor
        inválido) el campo sigue abierto para corregirlo; Esc o hacer clic fuera lo cierran.
        """
        self.cerrar_editor_peso()
        if (u, v) not in self._cajas_peso:
            return
        entrada = tk.Entry(
            self.canvas, width=4, justify="center", font=theme.FUENTE_ETIQUETA, relief="flat", bd=0,
            bg=theme.resolver(theme.FONDO_CANVAS), fg=theme.resolver(theme.TEXTO),
            insertbackground=theme.resolver(theme.TEXTO),
            highlightthickness=2, highlightbackground=theme.resolver(theme.ACENTO),
            highlightcolor=theme.resolver(theme.ACENTO),
        )
        entrada.insert(0, str(valor_actual))
        x0, y0, x1, y1 = self._cajas_peso[(u, v)]
        item = self.canvas.create_window((x0 + x1) / 2, (y0 + y1) / 2, window=entrada)
        self._editor_peso = ((u, v), entrada, item, al_confirmar)

        def confirmar(_evento=None):
            if self._editor_peso is None:
                return "break"
            if al_confirmar(entrada.get()) is not False:
                self.cerrar_editor_peso()
            return "break"

        entrada.bind("<Return>", confirmar)
        entrada.bind("<KP_Enter>", confirmar)
        entrada.bind("<Escape>", lambda _e: (self.cerrar_editor_peso(), "break")[1])
        entrada.bind("<FocusOut>", lambda _e: self.cerrar_editor_peso())
        entrada.focus_set()
        entrada.select_range(0, "end")
        entrada.icursor("end")

    def cerrar_editor_peso(self) -> None:
        if self._editor_peso is None:
            return
        _clave, entrada, item, _cb = self._editor_peso
        self._editor_peso = None
        try:
            self.canvas.delete(item)
            entrada.destroy()
        except tk.TclError:
            pass

    def editando_peso(self) -> tuple[str, str] | None:
        return self._editor_peso[0] if self._editor_peso else None

    def _reubicar_editor_peso(self) -> None:
        """Tras redibujar, el campo sigue sobre su arista (o se cierra si ya no existe)."""
        if self._editor_peso is None:
            return
        clave, entrada, _item, cb = self._editor_peso
        caja = self._cajas_peso.get(clave)
        if caja is None:
            self.cerrar_editor_peso()
            return
        item = self.canvas.create_window((caja[0] + caja[2]) / 2, (caja[1] + caja[3]) / 2, window=entrada)
        self._editor_peso = (clave, entrada, item, cb)

    def _candidatos_de_peso(self, puntos):
        """Posiciones a probar: sobre la arista y ligeramente desplazadas."""
        if len(puntos) < 3:
            puntos = [puntos[0], _punto_medio(puntos[0], puntos[-1]), puntos[-1]]
        total = len(puntos) - 1
        for proporcion in (0.5, 0.4, 0.6, 0.32, 0.68):
            indice = max(1, min(total - 1, round(total * proporcion)))
            x, y = puntos[indice]
            anterior, siguiente = puntos[indice - 1], puntos[indice + 1]
            dx, dy = siguiente[0] - anterior[0], siguiente[1] - anterior[1]
            longitud = math.hypot(dx, dy) or 1
            nx, ny = -dy / longitud, dx / longitud
            for desplazamiento in (0, 12, -12):
                yield (x + nx * desplazamiento, y + ny * desplazamiento)

    def _colisiona(self, rectangulo) -> bool:
        x0, y0, x1, y1 = rectangulo
        for a0, b0, a1, b1 in self._ocupados:
            if x0 < a1 and a0 < x1 and y0 < b1 and b0 < y1:
                return True
        return False

    def _colores_del_vertice(self, v: str) -> tuple[str, str]:
        snapshot = self.snapshot
        if v in self.seleccion_editor:
            return theme.resolver(theme.NODO_SELECCION_EDITOR), theme.resolver(theme.NODO_BORDE_ACTIVO)
        if snapshot and snapshot.seleccionado == v and not snapshot.es_final:
            return theme.resolver(theme.NODO_ACTUAL), theme.resolver(theme.NODO_BORDE_ACTIVO)
        if v == self.origen:
            return theme.resolver(theme.NODO_ORIGEN), theme.resolver(theme.NODO_BORDE_ACTIVO)
        if v == self.destino:
            return theme.resolver(theme.NODO_DESTINO), theme.resolver(theme.NODO_BORDE_ACTIVO)
        if snapshot and v in snapshot.visitados:
            return theme.resolver(theme.NODO_VISITADO), theme.resolver(theme.NODO_BORDE_VISITADO)
        return theme.resolver(theme.NODO), theme.resolver(theme.NODO_BORDE)

    def _dibujar_vertices(self) -> None:
        for v, (x, y) in self._posiciones.items():
            relleno, borde = self._colores_del_vertice(v)
            self.canvas.create_oval(
                x - RADIO, y - RADIO, x + RADIO, y + RADIO,
                fill=relleno, outline=borde, width=2,
            )
            self.canvas.create_text(
                x, y, text=v, fill=theme.resolver(theme.TEXTO), font=theme.FUENTE_NODO
            )
            if self.mostrar_etiquetas and self.snapshot:
                self._dibujar_etiqueta(v, x, y)
            self._dibujar_marca(v, x, y)

    # ------------------------------------------------------- marcas ORIGEN / DESTINO

    def _marca_de_vertice(self, v: str) -> str | None:
        """Texto de la marca que lleva el vértice (según los selectores), o ``None``."""
        if self.origen is not None and v == self.origen and v == self.destino:
            return "ORIGEN · DESTINO"
        if self.origen is not None and v == self.origen:
            return "ORIGEN"
        if self.destino is not None and v == self.destino:
            return "DESTINO"
        return None

    @staticmethod
    def _lado_de_marca(y: float) -> str:
        """Encima del vértice; solo pasa debajo si arriba no cabe en el canvas."""
        return "arriba" if y >= RADIO + HUECO_MARCA + ALTO_MARCA + 2 else "abajo"

    def _desvio_por_marca(self, v: str, y: float, lado_etiqueta: str) -> int:
        """Píxeles que debe apartarse la etiqueta [d, V] si comparte lado con la marca."""
        if self._marca_de_vertice(v) is None or self._lado_de_marca(y) != lado_etiqueta:
            return 0
        return ALTO_MARCA + 4

    def _ancho_de_marca(self, texto: str) -> float:
        if not hasattr(self, "_fuente_marca"):
            self._fuente_marca = tkfont.Font(root=self.canvas, font=theme.FUENTE_MARCA)
        return self._fuente_marca.measure(texto) + 14

    def _rectangulo_de_marca(self, v: str, x: float, y: float):
        texto = self._marca_de_vertice(v)
        if texto is None:
            return None
        ancho = self._ancho_de_marca(texto)
        if self._lado_de_marca(y) == "arriba":
            y1 = y - RADIO - HUECO_MARCA
            y0 = y1 - ALTO_MARCA
        else:
            y0 = y + RADIO + HUECO_MARCA
            y1 = y0 + ALTO_MARCA
        return (x - ancho / 2, y0, x + ancho / 2, y1)

    def _dibujar_marca(self, v: str, x: float, y: float) -> None:
        rect = self._rectangulo_de_marca(v, x, y)
        if rect is None:
            return
        x0, y0, x1, y1 = rect
        r = ALTO_MARCA / 2
        relleno = theme.resolver(theme.NODO_ORIGEN if v == self.origen else theme.NODO_DESTINO)
        puntos = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
                  x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
        self.canvas.create_polygon(
            *puntos, smooth=True, fill=relleno, outline=theme.resolver(theme.NODO_BORDE_ACTIVO), width=1,
            tags=("marca",),
        )
        self.canvas.create_text(
            (x0 + x1) / 2, (y0 + y1) / 2, text=self._marca_de_vertice(v),
            fill=theme.resolver(theme.TEXTO), font=theme.FUENTE_MARCA, tags=("marca",),
        )

    def _dibujar_etiqueta(self, v: str, x: float, y: float) -> None:
        snapshot = self.snapshot
        distancia = snapshot.distancias.get(v, INFINITO)
        texto = snapshot.etiqueta(v)

        posicion = self._posicion_etiqueta_vertice(v, x, y)
        descartada = next(
            (t for vertice, t in snapshot.etiquetas_descartadas if vertice == v), None
        )
        color = theme.resolver(theme.ETIQUETA) if distancia != INFINITO else theme.resolver(theme.TEXTO_TENUE)

        extra = self._desvio_por_marca(v, y, posicion)
        if posicion == "arriba":
            y_texto = y - RADIO - 13 - extra
            y_descartada = y - RADIO - 27 - extra
        else:
            y_texto = y + RADIO + 13 + extra
            y_descartada = y + RADIO + 27 + extra

        if descartada:
            self.canvas.create_text(
                x, y_descartada, text=descartada,
                fill=theme.resolver(theme.ETIQUETA_DESCARTADA), font=theme.FUENTE_ETIQUETA_TACHADA,
            )

        self.canvas.create_text(
            x, y_texto, text=texto, fill=color, font=theme.FUENTE_ETIQUETA,
        )
