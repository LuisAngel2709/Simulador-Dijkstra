"""Ventana principal y navegación entre pantallas."""

from __future__ import annotations

import customtkinter as ctk

from core.extremos import sugerir_extremos
from core.generator import generar_dag_didactico
from core.graph import NODOS_MAXIMO, NODOS_MINIMO, Grafo, GrafoError, validar_numero_nodos

from . import theme
from .boton_tema import BotonTema
from .editor import PantallaEditor
from .simulation import PantallaSimulacion
from .tutorial import Tutorial
from . import tutorial_pasos


ALTO_ENCABEZADO = 40


class PantallaBienvenida(ctk.CTkFrame):
    """Pantalla 0 — Bienvenida con estética moderna, tarjetas y jerarquía clara."""

    def __init__(self, master, al_continuar):
        super().__init__(master, fg_color=theme.FONDO)
        self.al_continuar = al_continuar

        tarjeta = ctk.CTkFrame(
            self,
            fg_color=theme.PANEL,
            corner_radius=16,
            border_width=1,
            border_color=theme.BORDE,
        )
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")
        self.tarjeta = tarjeta

        # Badge superior
        badge = ctk.CTkFrame(
            tarjeta,
            fg_color=theme.ACENTO_SUAVE,
            corner_radius=20,
            border_width=1,
            border_color=theme.BORDE_SUAVE,
        )
        badge.pack(pady=(36, 12), padx=40)
        ctk.CTkLabel(
            badge,
            text="🎓  SIMULADOR EDUCATIVO INTERACTIVO",
            font=(theme.FAMILIA, 11, "bold"),
            text_color=theme.ACENTO,
        ).pack(padx=16, pady=4)

        # Título y subtítulos
        ctk.CTkLabel(
            tarjeta,
            text="ENCUENTRA EL CAMINO MÍNIMO",
            font=(theme.FAMILIA, 28, "bold"),
            text_color=theme.TEXTO,
        ).pack(pady=(0, 6), padx=40)

        ctk.CTkLabel(
            tarjeta,
            text="Descubre paso a paso cómo funciona el algoritmo de Dijkstra",
            font=(theme.FAMILIA, 15, "bold"),
            text_color=theme.TEXTO_SUAVE,
        ).pack(pady=(0, 8), padx=40)

        ctk.CTkLabel(
            tarjeta,
            text="Construye un grafo, elige un punto de partida y descubre cómo encontrar el camino más corto.",
            font=theme.FUENTE_NORMAL,
            text_color=theme.TEXTO_TENUE,
        ).pack(pady=(0, 26), padx=40)

        # Fila de 3 minitarjetas informativas
        fila_caracteristicas = ctk.CTkFrame(tarjeta, fg_color="transparent")
        fila_caracteristicas.pack(pady=(0, 30), padx=36)

        caracteristicas = [
            ("🌐 Grafo Visual", "Estructura por capas y conexiones claras."),
            ("🔍 Paso a Paso", "Etiquetado y relajación en cada iteración."),
            ("🎯 Rutas Óptimas", "Cálculo de distancias y detección de empates."),
        ]

        for titulo, desc in caracteristicas:
            caja = ctk.CTkFrame(
                fila_caracteristicas,
                fg_color=theme.PANEL_SUAVE,
                corner_radius=10,
                border_width=1,
                border_color=theme.BORDE_SUAVE,
                width=190,
            )
            caja.pack(side="left", padx=8, fill="both", expand=True)
            ctk.CTkLabel(
                caja,
                text=titulo,
                font=(theme.FAMILIA, 13, "bold"),
                text_color=theme.TEXTO,
            ).pack(anchor="w", padx=14, pady=(12, 3))
            ctk.CTkLabel(
                caja,
                text=desc,
                font=theme.FUENTE_PEQUENA,
                text_color=theme.TEXTO_SUAVE,
                justify="left",
                wraplength=170,
            ).pack(anchor="w", padx=14, pady=(0, 12))

        # Botón principal de acción
        self.boton_empezar = ctk.CTkButton(
            tarjeta,
            text="EMPEZAR SIMULACIÓN  →",
            width=300,
            height=50,
            font=(theme.FAMILIA, 15, "bold"),
            fg_color=theme.ACENTO,
            hover_color=theme.ACENTO_HOVER,
            text_color=theme.ACENTO_TEXTO,
            corner_radius=10,
            command=self.al_continuar,
        )
        self.boton_empezar.pack(pady=(0, 14))

        # Pie discreto
        ctk.CTkLabel(
            tarjeta,
            text="Simulación interactiva del algoritmo de Dijkstra",
            font=theme.FUENTE_PEQUENA,
            text_color=theme.TEXTO_TENUE,
        ).pack(pady=(0, 28))


class PantallaConfiguracion(ctk.CTkFrame):
    """Pantalla 1 — Configuración guiada con tarjetas interactivas."""

    def __init__(self, master, al_elegir_manual, al_elegir_aleatorio, al_volver_bienvenida):
        super().__init__(master, fg_color=theme.FONDO)
        self.al_elegir_manual = al_elegir_manual
        self.al_elegir_aleatorio = al_elegir_aleatorio
        self.al_volver_bienvenida = al_volver_bienvenida

        tarjeta = ctk.CTkFrame(
            self,
            fg_color=theme.PANEL,
            corner_radius=16,
            border_width=1,
            border_color=theme.BORDE,
        )
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")
        self.tarjeta = tarjeta

        # Badge superior
        badge = ctk.CTkFrame(
            tarjeta,
            fg_color=theme.ACENTO_SUAVE,
            corner_radius=20,
            border_width=1,
            border_color=theme.BORDE_SUAVE,
        )
        badge.pack(pady=(32, 10), padx=48)
        ctk.CTkLabel(
            badge,
            text="PASO 1 · CONFIGURACIÓN DEL GRAFO",
            font=(theme.FAMILIA, 11, "bold"),
            text_color=theme.ACENTO,
        ).pack(padx=16, pady=4)

        ctk.CTkLabel(
            tarjeta,
            text="Primero, configuremos tu grafo",
            font=(theme.FAMILIA, 24, "bold"),
            text_color=theme.TEXTO,
        ).pack(pady=(0, 4), padx=48)

        ctk.CTkLabel(
            tarjeta,
            text="Elige cuántos nodos tendrá y cómo quieres construirlo.",
            font=theme.FUENTE_NORMAL,
            text_color=theme.TEXTO_SUAVE,
        ).pack(pady=(0, 24), padx=48)

        # Sección 1: Selección de Nodos
        marco_nodos = ctk.CTkFrame(
            tarjeta,
            fg_color=theme.PANEL_SUAVE,
            corner_radius=10,
            border_width=1,
            border_color=theme.BORDE_SUAVE,
        )
        marco_nodos.pack(fill="x", padx=48, pady=(0, 20))
        self.marco_nodos = marco_nodos

        ctk.CTkLabel(
            marco_nodos,
            text="¿Cuántos nodos quieres?",
            font=(theme.FAMILIA, 14, "bold"),
            text_color=theme.TEXTO,
        ).pack(side="left", padx=(18, 12), pady=12)

        ctk.CTkLabel(
            marco_nodos,
            text=f"(entre {NODOS_MINIMO} y {NODOS_MAXIMO}):",
            font=theme.FUENTE_PEQUENA,
            text_color=theme.TEXTO_SUAVE,
        ).pack(side="left", pady=12)

        self.entrada_nodos = ctk.CTkOptionMenu(
            marco_nodos,
            values=[str(i) for i in range(NODOS_MINIMO, NODOS_MAXIMO + 1)],
            width=90,
            fg_color=theme.ACENTO,
            button_color=theme.ACENTO_HOVER,
            button_hover_color=theme.ACENTO,
            text_color=theme.ACENTO_TEXTO,
            dropdown_text_color=theme.TEXTO,
            dropdown_fg_color=theme.PANEL,
            dropdown_hover_color=theme.BORDE_SUAVE,
        )
        self.entrada_nodos.set("8")
        self.entrada_nodos.pack(side="right", padx=18, pady=12)

        self.mensaje = ctk.CTkLabel(
            tarjeta, text="", font=theme.FUENTE_PEQUENA, text_color=theme.PELIGRO
        )
        self.mensaje.pack(pady=(0, 6))

        # Sección 2: Modo de Construcción (Tarjetas interactivas)
        ctk.CTkLabel(
            tarjeta,
            text="¿Cómo quieres crear el grafo?",
            font=(theme.FAMILIA, 15, "bold"),
            text_color=theme.TEXTO,
        ).pack(anchor="w", padx=48, pady=(4, 10))

        fila_opciones = ctk.CTkFrame(tarjeta, fg_color="transparent")
        fila_opciones.pack(padx=48, pady=(0, 24))

        # Tarjeta 1: Automático
        tarjeta_auto = ctk.CTkFrame(
            fila_opciones,
            fg_color=theme.PANEL_SUAVE,
            corner_radius=12,
            border_width=1,
            border_color=theme.BORDE,
            width=270,
            height=160,
        )
        tarjeta_auto.pack(side="left", padx=(0, 10), fill="both", expand=True)
        tarjeta_auto.pack_propagate(False)
        self.tarjeta_auto = tarjeta_auto

        ctk.CTkLabel(
            tarjeta_auto,
            text="⚡ Generar automáticamente",
            font=(theme.FAMILIA, 14, "bold"),
            text_color=theme.TEXTO,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            tarjeta_auto,
            text="Deja que el sistema cree un grafo dirigido sin ciclos con pesos didácticos y camino óptimo garantizado.",
            font=theme.FUENTE_PEQUENA,
            text_color=theme.TEXTO_SUAVE,
            justify="left",
            wraplength=235,
        ).pack(anchor="w", padx=16, pady=(0, 14))

        ctk.CTkButton(
            tarjeta_auto,
            text="Generar y Continuar  →",
            height=36,
            font=(theme.FAMILIA, 13, "bold"),
            fg_color=theme.ACENTO,
            hover_color=theme.ACENTO_HOVER,
            text_color=theme.ACENTO_TEXTO,
            corner_radius=8,
            command=self._aleatorio,
        ).pack(fill="x", padx=16, pady=(0, 16), side="bottom")

        # Tarjeta 2: Manual
        tarjeta_manual = ctk.CTkFrame(
            fila_opciones,
            fg_color=theme.PANEL_SUAVE,
            corner_radius=12,
            border_width=1,
            border_color=theme.BORDE,
            width=270,
            height=160,
        )
        tarjeta_manual.pack(side="left", padx=(10, 0), fill="both", expand=True)
        tarjeta_manual.pack_propagate(False)
        self.tarjeta_manual = tarjeta_manual

        ctk.CTkLabel(
            tarjeta_manual,
            text="✏️ Crear manualmente",
            font=(theme.FAMILIA, 14, "bold"),
            text_color=theme.TEXTO,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            tarjeta_manual,
            text="Define las conexiones y los pesos tú mismo en un editor visual interactivo nodo por nodo.",
            font=theme.FUENTE_PEQUENA,
            text_color=theme.TEXTO_SUAVE,
            justify="left",
            wraplength=235,
        ).pack(anchor="w", padx=16, pady=(0, 14))

        ctk.CTkButton(
            tarjeta_manual,
            text="Abrir Editor Manual  →",
            height=36,
            font=(theme.FAMILIA, 13, "bold"),
            fg_color=theme.BOTON_SECUNDARIO,
            hover_color=theme.BOTON_SECUNDARIO_HOVER,
            text_color=theme.BOTON_SECUNDARIO_TEXTO,
            border_width=1,
            border_color=theme.BORDE,
            corner_radius=8,
            command=self._manual,
        ).pack(fill="x", padx=16, pady=(0, 16), side="bottom")

        # Botón volver inferior
        ctk.CTkButton(
            tarjeta,
            text="← Volver al inicio",
            width=140,
            height=32,
            font=theme.FUENTE_PEQUENA,
            fg_color=theme.BOTON_SECUNDARIO,
            hover_color=theme.BOTON_SECUNDARIO_HOVER,
            text_color=theme.BOTON_SECUNDARIO_TEXTO,
            border_width=1,
            border_color=theme.BORDE,
            corner_radius=8,
            command=self.al_volver_bienvenida,
        ).pack(pady=(0, 24))

    def _leer_nodos(self) -> int | None:
        try:
            return validar_numero_nodos(self.entrada_nodos.get())
        except GrafoError as error:
            self.mensaje.configure(text=str(error))
            return None

    def _manual(self) -> None:
        n = self._leer_nodos()
        if n:
            self.al_elegir_manual(n)

    def _aleatorio(self) -> None:
        n = self._leer_nodos()
        if n:
            self.al_elegir_aleatorio(n)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("Simulador del algoritmo de Dijkstra")
        self.geometry("1320x860")
        self.minsize(1100, 760)
        self.configure(fg_color=theme.FONDO)

        self.pantalla: ctk.CTkFrame | None = None
        # Origen y destino que el usuario eligió a mano en la simulación: se respetan si vuelve
        # al editor y simula de nuevo el mismo grafo. Se olvidan al empezar un grafo distinto.
        self._extremos_manuales: tuple[str, str] | None = None

        # Encabezado fijo (se crea una sola vez): el selector de tema vive aquí, por
        # encima de todas las pantallas, así que no puede tapar sus controles.
        self._encabezado = ctk.CTkFrame(self, fg_color="transparent", height=ALTO_ENCABEZADO)
        self._encabezado.pack(side="top", fill="x")
        self._encabezado.pack_propagate(False)
        self._boton_tema = BotonTema(self._encabezado, self._alternar_tema)
        self._boton_tema.pack(side="right", padx=(0, 18), pady=(6, 0))
        self._boton_tutorial = ctk.CTkButton(
            self._encabezado, text="?  Tutorial", width=104, height=30,
            font=(theme.FAMILIA, 12, "bold"), corner_radius=15, command=self.iniciar_tutorial,
            fg_color=theme.ACENTO, hover_color=theme.ACENTO_HOVER, text_color=theme.ACENTO_TEXTO,
        )
        self._boton_tutorial.pack(side="right", padx=(0, 10), pady=(5, 0))
        self.tutorial = Tutorial(self)

        self.mostrar_bienvenida()

    # ------------------------------------------------------------- tema

    def _alternar_tema(self) -> None:
        """Alterna claro/oscuro sin destruir ni reconstruir ninguna pantalla.

        Los widgets de CustomTkinter usan pares (claro, oscuro) y cambian solos con
        ``set_appearance_mode``. Solo se repintan los componentes de Tk puro (el
        canvas del grafo y la tabla), conservando su estado.
        """
        nuevo_modo = theme.alternar_modo()
        # Primero los componentes de Tk puro: los widgets transparentes de CustomTkinter
        # toman el color de su contenedor al recolorearse, así que este ya debe estar al día.
        if self.pantalla is not None and hasattr(self.pantalla, "aplicar_tema"):
            self.pantalla.aplicar_tema()
        ctk.set_appearance_mode("dark" if nuevo_modo == "oscuro" else "light")
        self._boton_tema.actualizar()
        self.tutorial.aplicar_tema()

    # ---------------------------------------------------------------- tutorial

    def iniciar_tutorial(self) -> None:
        """Abre (o reinicia) el recorrido guiado de la pantalla actual, sin modificarla."""
        pantalla = self.pantalla
        for clase, pasos in (
            (PantallaBienvenida, tutorial_pasos.pasos_bienvenida),
            (PantallaConfiguracion, tutorial_pasos.pasos_configuracion),
            (PantallaEditor, tutorial_pasos.pasos_editor),
            (PantallaSimulacion, tutorial_pasos.pasos_simulacion),
        ):
            if isinstance(pantalla, clase):
                self.tutorial.iniciar(pasos(pantalla), pantalla)
                return

    # ------------------------------------------------------------------ navegación

    def _cambiar_pantalla(self, pantalla: ctk.CTkFrame) -> None:
        self.tutorial.salir()
        if self.pantalla is not None:
            self.pantalla.destroy()
        self.pantalla = pantalla
        self.pantalla.pack(fill="both", expand=True)

    def _extremos_para(self, grafo) -> tuple[str, str]:
        """Selección manual del usuario si la hay; si no, la pareja sugerida para el grafo."""
        manuales = self._extremos_manuales
        if manuales and all(grafo.existe_vertice(v) for v in manuales):
            return manuales
        return sugerir_extremos(grafo)

    def mostrar_bienvenida(self) -> None:
        self._extremos_manuales = None
        self._cambiar_pantalla(PantallaBienvenida(self, self.mostrar_configuracion))

    def mostrar_configuracion(self) -> None:
        self._extremos_manuales = None
        self._cambiar_pantalla(
            PantallaConfiguracion(
                self,
                self.iniciar_manual,
                self.iniciar_aleatorio,
                al_volver_bienvenida=self.mostrar_bienvenida,
            )
        )

    def iniciar_manual(self, n: int) -> None:
        self._extremos_manuales = None
        self.mostrar_editor(Grafo(n))

    def mostrar_editor(self, grafo, posiciones=None) -> None:
        """Abre el editor con un grafo nuevo o con uno ya construido."""
        self._cambiar_pantalla(
            PantallaEditor(
                self,
                grafo,
                al_finalizar=self._simular_desde_editor,
                al_volver=self.mostrar_configuracion,
                posiciones_iniciales=posiciones,
                extremos=self._extremos_para,
            )
        )

    def _simular_desde_editor(self, grafo, posiciones) -> None:
        self.mostrar_simulacion(grafo, posiciones=posiciones, desde_editor=True)

    def iniciar_aleatorio(self, n: int) -> None:
        self._extremos_manuales = None
        grafo, origen, destino = generar_dag_didactico(n)
        self.mostrar_simulacion(grafo, origen, destino)

    def mostrar_simulacion(
        self, grafo, origen=None, destino=None, posiciones=None, desde_editor=False
    ) -> None:
        """Muestra la simulación. Con `desde_editor`, "volver" regresa al editor
        conservando el grafo y la posición de los nodos; si el grafo era aleatorio
        no hay nada que editar y se vuelve a la configuración."""
        if origen is None or destino is None:
            sugerido = self._extremos_para(grafo)  # selección manual previa o pareja sugerida
            origen, destino = origen or sugerido[0], destino or sugerido[1]
        if desde_editor:
            al_volver = lambda pos: self._volver_al_editor(grafo, pos)
            texto_volver = "← Editar grafo"
        else:
            al_volver = lambda _pos: self.mostrar_configuracion()
            texto_volver = "← Configuración"

        self._cambiar_pantalla(
            PantallaSimulacion(
                self,
                grafo,
                origen_sugerido=origen,
                destino_sugerido=destino,
                al_volver=al_volver,
                posiciones_iniciales=posiciones,
                texto_volver=texto_volver,
            )
        )

    def _volver_al_editor(self, grafo, posiciones) -> None:
        """Vuelve al editor recordando el origen/destino que el usuario eligió a mano."""
        self._extremos_manuales = getattr(self.pantalla, "seleccion_manual", None) or self._extremos_manuales
        self.mostrar_editor(grafo, posiciones)
