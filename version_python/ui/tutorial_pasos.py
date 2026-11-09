"""Contenido del tutorial: los pasos de cada pantalla.

Cada función devuelve la lista de ``PasoTutorial`` de una pantalla y solo
referencia widgets que la pantalla ya tiene. Nada de lo que hay aquí ejecuta
acciones de la pantalla: los pasos únicamente leen, resaltan y, como mucho,
desplazan la página para que el elemento se vea.

La parte «Algoritmo» del recorrido de simulación usa ``core.tutorial_algoritmo``,
que lee el resultado del motor (el de la simulación en curso, sin modificarlo, o
uno calculado aparte con el grafo y los extremos elegidos).
"""

from __future__ import annotations

from core.dijkstra_engine import ejecutar_dijkstra
from core.graph import NODOS_MAXIMO, NODOS_MINIMO
from core.tutorial_algoritmo import ejemplos_algoritmo

from .tutorial import PasoTutorial

INTERFAZ = "Interfaz"
ALGORITMO = "Cómo funciona Dijkstra"
NOTA_EJEMPLO = "\n(Calculado con tu grafo; no modifica tu simulación.)"


def pasos_bienvenida(p) -> list[PasoTutorial]:
    raiz = p.winfo_toplevel()
    return [
        PasoTutorial(
            "Bienvenido al simulador",
            "Esta aplicación te enseña cómo el algoritmo de Dijkstra encuentra el camino más corto "
            "entre dos vértices de un grafo, paso a paso. Primero construyes o generas un grafo y "
            "después lo simulas.",
            lambda: p.tarjeta, seccion="Inicio"),
        PasoTutorial(
            "Empezar",
            "Este botón te lleva a la configuración del grafo.",
            lambda: p.boton_empezar, seccion="Inicio"),
        PasoTutorial(
            "Tutorial y tema",
            "«Tutorial» repite este recorrido en la pantalla donde estés: cada pantalla tiene su propia "
            "guía. El botón de la luna o el sol cambia entre tema claro y oscuro sin perder tu trabajo.",
            lambda: [raiz._boton_tutorial, raiz._boton_tema], seccion="Inicio"),
    ]


def pasos_configuracion(p) -> list[PasoTutorial]:
    return [
        PasoTutorial(
            "Configura tu grafo",
            "Aquí decides cuántos vértices tendrá el grafo y cómo quieres crearlo. "
            "Después podrás simularlo.",
            lambda: p.tarjeta, seccion="Configuración"),
        PasoTutorial(
            "Número de vértices",
            f"Elige cuántos vértices tendrá el grafo, entre {NODOS_MINIMO} y {NODOS_MAXIMO}. "
            "Se nombran con letras: A, B, C…",
            lambda: p.marco_nodos, seccion="Configuración"),
        PasoTutorial(
            "Generar automáticamente",
            "Crea un grafo dirigido sin ciclos con pesos pensados para aprender y pasa directamente a "
            "la simulación, con un origen y un destino sugeridos.",
            lambda: p.tarjeta_auto, seccion="Configuración"),
        PasoTutorial(
            "Crear manualmente",
            "Abre un editor donde tú dibujas las conexiones y eliges sus pesos. Es la mejor opción "
            "para probar tus propios ejemplos.",
            lambda: p.tarjeta_manual, seccion="Configuración"),
    ]


def pasos_editor(p) -> list[PasoTutorial]:
    return [
        PasoTutorial(
            "El área de construcción",
            "Los vértices ya están dibujados. Arrástralos para ubicarlos donde quieras. Para conectar "
            "dos, haz clic en el vértice de origen y luego en el de destino: la flecha irá de uno al otro.",
            lambda: p.canvas, seccion="Editor"),
        PasoTutorial(
            "Peso de la conexión",
            "Con origen y destino elegidos, escribe un peso entero de 1 a 99 y pulsa Enter o "
            "«Crear conexión». «Cancelar» (o Esc) anula la selección. El editor no admite ciclos, "
            "bucles ni conexiones repetidas, y te avisa si lo intentas.",
            lambda: [p.etiqueta_seleccion, p.fila_peso, p.fila_botones], seccion="Editor"),
        PasoTutorial(
            "Aristas del grafo",
            "Aquí aparece cada conexión creada. Con «Peso» cambias su valor y con «Eliminar» la quitas. "
            "También puedes hacer clic sobre el número de una flecha en el grafo y escribir el peso ahí mismo "
            "(Enter confirma, Esc cancela).",
            lambda: p.lista_aristas, seccion="Editor"),
        PasoTutorial(
            "Restablecer posiciones",
            "Si arrastraste los vértices y quedaron enredados, este botón los vuelve a colocar en círculo. "
            "No cambia las conexiones.",
            lambda: p.boton_restablecer, seccion="Editor"),
        PasoTutorial(
            "Finalizar el grafo",
            "Cuando el grafo esté listo (con al menos una conexión), este botón pasa a la simulación. "
            "Si hay vértices aislados o el destino no se puede alcanzar, te avisa antes y puedes continuar "
            "o volver al editor. Desde la simulación podrás volver sin perder lo construido.",
            lambda: p.boton_finalizar_grafo, seccion="Editor"),
    ]


def pasos_simulacion(p) -> list[PasoTutorial]:
    pagina = p.pagina
    recorte = lambda: pagina._lienzo
    ver = lambda *ws: (lambda: pagina.mostrar_widget(ws[0]))

    cache: dict = {}

    def ejemplos():
        """Resultado del motor, de solo lectura: el de la simulación o uno calculado aparte."""
        origen, destino = p.menu_origen.get(), p.menu_destino.get()
        resultado = p.resultado
        if resultado is None:
            clave = (origen, destino)
            if cache.get("clave") != clave:
                cache["clave"] = clave
                cache["resultado"] = ejecutar_dijkstra(p.grafo, origen, destino)
            resultado = cache["resultado"]
        clave = (id(resultado), origen, destino)
        if cache.get("clave_ej") != clave:
            cache["clave_ej"] = clave
            cache["ej"] = ejemplos_algoritmo(p.grafo, resultado)
        return cache["ej"]

    if p.texto_volver == "← Editar grafo":
        volver = ("Vuelve al editor con tu grafo, para añadir, cambiar o quitar conexiones sin perder "
                  "las posiciones de los vértices.")
    else:
        volver = ("Vuelve a la configuración, donde puedes generar otro grafo automáticamente o crearlo "
                  "a mano en el editor. Si el grafo tiene conexiones te pedirá confirmación antes de descartarlo.")

    return [
        PasoTutorial(
            "Bienvenido a la simulación",
            "Aquí verás cómo Dijkstra calcula el camino mínimo, un paso cada vez. Este recorrido explica "
            "cada zona de la pantalla y, al final, los conceptos del algoritmo. No cambia tu grafo ni tu "
            "simulación, y puedes salir cuando quieras.",
            lambda: p.barra_superior, seccion=INTERFAZ),
        PasoTutorial(
            "El grafo",
            "Cada círculo es un vértice y cada flecha una conexión dirigida: solo se puede avanzar en el "
            "sentido de la flecha. Puedes arrastrar los vértices para verlos mejor.",
            lambda: p.canvas, seccion=INTERFAZ, preparar=ver(p.cuerpo), recorte=recorte),
        PasoTutorial(
            "Crear o generar otro grafo",
            volver,
            lambda: p.boton_volver, seccion=INTERFAZ),
        PasoTutorial(
            "Origen y destino",
            "Elige desde qué vértice parte el camino y a cuál quieres llegar (al empezar se propone una pareja "
            "válida, que puedes cambiar). Aparecen marcados como "
            "ORIGEN y DESTINO sobre el grafo y en el encabezado. Si los cambias, hay que volver a ejecutar "
            "la simulación.",
            lambda: p.marco_extremos, seccion=INTERFAZ, preparar=ver(p.cuerpo), recorte=recorte),
        PasoTutorial(
            "Etiquetas, pesos y conexiones",
            "• El número en un recuadro sobre cada flecha es su peso.\n"
            "• [d, V]ₙ es la etiqueta de un vértice: d = distancia acumulada desde el origen, "
            "V = vértice anterior (predecesor), n = iteración en que se asignó. [∞, -] significa que "
            "aún no se llegó a él.\n"
            "• La leyenda explica los colores: en los vértices, verde = origen, rosa = destino, "
            "amarillo = actual y azul = visitado; en las flechas, ámbar = arista evaluada, "
            "naranja = empate y verde = camino mínimo. Una flecha roja es una arista evaluada que "
            "no mejora la distancia (no aparece en la leyenda).",
            lambda: [p.canvas, p.marco_leyenda], seccion=INTERFAZ, preparar=ver(p.cuerpo), recorte=recorte),
        PasoTutorial(
            "Iniciar la simulación",
            "«Ejecutar Dijkstra» calcula el algoritmo y muestra su primer paso. Si ya hay una simulación "
            "en curso, volver a pulsarlo la empieza de nuevo; por eso el tutorial no lo pulsa por ti.",
            lambda: p.boton_ejecutar, seccion=INTERFAZ, preparar=ver(p.cuerpo), recorte=recorte),
        PasoTutorial(
            "Avanzar y retroceder",
            "«Siguiente» y «Anterior» recorren la simulación subpaso a subpaso (también las flechas del "
            "teclado). «Reiniciar» vuelve al primer paso e «Ir al final» salta al resultado. Retroceder no "
            "recalcula nada: revisa pasos ya calculados. El último botón muestra u oculta la tabla.",
            lambda: p.barra_navegacion, seccion=INTERFAZ),
        PasoTutorial(
            "Tabla del proceso",
            "Una fila por vértice y una columna por iteración. Cada celda guarda la etiqueta [d, V] que "
            "el vértice recibió en esa iteración: verde = vigente, amarillo = empate, gris = descartada.",
            lambda: p.tabla, seccion=INTERFAZ, preparar=ver(p.tabla), recorte=recorte),
        PasoTutorial(
            "Explicación de cada paso",
            "Este cuadro cuenta qué hace el algoritmo en el paso actual: qué vértice examina, qué "
            "aristas considera, cómo calcula cada distancia nueva y por qué una etiqueta se actualiza, "
            "se conserva o se descarta. Cambia sola al avanzar o retroceder.",
            lambda: [p.titulo_paso, p.fila_subpaso, p.texto_explicacion],
            seccion=INTERFAZ, preparar=ver(p.cuerpo), recorte=recorte),
        PasoTutorial(
            "Más detalles",
            "Abre una ventana aparte con el razonamiento ampliado, la lectura de la etiqueta y el estado "
            "de todos los vértices. No bloquea la aplicación: se actualiza sola al cambiar de paso y se "
            "cierra con su botón o con Esc. Se activa al ejecutar la simulación.",
            lambda: p.boton_detalles, seccion=INTERFAZ, preparar=ver(p.cuerpo), recorte=recorte),
        PasoTutorial(
            "Resultado",
            "Al terminar muestra la distancia mínima y los caminos mínimos entre origen y destino (varios "
            "si hay empates), o avisa de que el destino no se puede alcanzar. Con «Ir al final» lo ves "
            "al instante.",
            lambda: [p.etiqueta_resultado, p.texto_resultado], seccion=INTERFAZ,
            preparar=ver(p.cuerpo), recorte=recorte),
        PasoTutorial(
            "Distancias provisionales",
            "Dijkstra guarda, para cada vértice, la mejor distancia conocida hasta ahora desde el origen. "
            "Empieza con 0 en el origen y ∞ en los demás. Mientras un vértice no se selecciona, su "
            "distancia es provisional: todavía puede mejorar.",
            lambda: p.canvas, seccion=ALGORITMO, preparar=ver(p.cuerpo), recorte=recorte,
            ejemplo=lambda: ejemplos().provisionales + NOTA_EJEMPLO),
        PasoTutorial(
            "Elegir el vértice de menor distancia",
            "Cada iteración empieza con la Selección: entre los vértices aún no visitados se elige el de "
            "menor distancia provisional. Como los pesos son positivos, esa distancia ya no puede "
            "mejorar: se vuelve definitiva y el vértice pasa a visitado (azul).",
            lambda: [p.titulo_paso, p.fila_subpaso, p.texto_explicacion], seccion=ALGORITMO,
            preparar=ver(p.cuerpo), recorte=recorte,
            ejemplo=lambda: ejemplos().seleccion + NOTA_EJEMPLO),
        PasoTutorial(
            "Actualizar etiquetas y predecesores",
            "Después viene la Actualización: se miran las aristas que salen del vértice elegido y se "
            "calcula distancia nueva = d(elegido) + peso. Si es menor que la etiqueta del vecino, la "
            "reemplaza (la anterior se tacha) y su predecesor pasa a ser el vértice elegido.",
            lambda: p.canvas, seccion=ALGORITMO, preparar=ver(p.cuerpo), recorte=recorte,
            ejemplo=lambda: ejemplos().actualizacion + NOTA_EJEMPLO),
        PasoTutorial(
            "Empates",
            "Si la distancia nueva es igual a la que ya tenía el vecino, hay un empate: se conserva la "
            "distancia y se añade otro predecesor, para no perder ningún camino mínimo. En el grafo la "
            "arista se pinta de naranja y en la tabla la celda de amarillo.",
            lambda: p.tabla, seccion=ALGORITMO, preparar=ver(p.tabla), recorte=recorte,
            ejemplo=lambda: ejemplos().empates + NOTA_EJEMPLO),
        PasoTutorial(
            "Reconstruir el camino mínimo",
            "Cuando no quedan vértices alcanzables por visitar, se parte del destino y se siguen los "
            "predecesores hacia atrás hasta el origen. Si un vértice tiene varios predecesores, cada uno "
            "da un camino mínimo distinto; todos se resaltan en verde.",
            lambda: [p.etiqueta_resultado, p.texto_resultado], seccion=ALGORITMO,
            preparar=ver(p.cuerpo), recorte=recorte,
            ejemplo=lambda: ejemplos().camino + NOTA_EJEMPLO),
    ]
