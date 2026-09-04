"""Piezas para dibujar diagramas conceptuales con matplotlib.

Los diagramas del curso (tipos de dataset, tipos de atributo) se construyen
sobre un eje único con `aspect="equal"`, en el que se posicionan formas y
rótulos por coordenadas. Estas funciones son las piezas que se repiten: la
flecha fina que encabeza cada nivel, el rótulo en color del tema y la celda
gris con la que se arman las grillas.
"""

from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

from visutils.estilo import AZUL, GRIS, MAGENTA


def flecha(ax, desde, hasta, lw=0.9, escala=7, color=AZUL):
    """Flecha fina entre dos puntos, en coordenadas de datos."""
    ax.annotate(
        "",
        xy=hasta,
        xytext=desde,
        arrowprops=dict(
            arrowstyle="-|>", color=color, lw=lw, shrinkA=0, shrinkB=0, mutation_scale=escala
        ),
    )


def rotulo(ax, x, y, texto, size=7, ha="center", va="center", color=AZUL, **kwargs):
    """Texto en el color del tema. Retorna el objeto para poder medirlo."""
    return ax.text(x, y, texto, fontsize=size, ha=ha, va=va, color=color, **kwargs)


def celda(ax, x, y, ancho, alto, destacada=False):
    """Celda de una grilla: gris, o magenta si es la que se está señalando."""
    ax.add_patch(
        Rectangle((x, y), ancho, alto, facecolor=MAGENTA if destacada else GRIS, lw=0)
    )


def caja(ax, x, y, ancho, alto, texto, size=8, relleno="white", color=AZUL,
         color_texto=None, redondeo=0.8, **kwargs):
    """Caja redondeada con texto centrado, ubicada por su centro.

    Con `relleno` en un color sólido conviene pasar `color_texto="white"`, que
    es como se marcan el origen y el resultado de un flujo.
    """
    ax.add_patch(
        FancyBboxPatch(
            (x - ancho / 2, y - alto / 2),
            ancho,
            alto,
            boxstyle=f"round,pad=0,rounding_size={redondeo}",
            facecolor=relleno,
            edgecolor=color,
            lw=1.1,
            zorder=2,
        )
    )
    return rotulo(ax, x, y, texto, size=size, color=color_texto or color, zorder=3, **kwargs)


def encabezado(ax, x, y, texto, size=12):
    """Título de primer nivel: flecha dentro de un círculo, más el texto."""
    ax.add_patch(Circle((x, y), 1.35, facecolor="none", edgecolor=AZUL, lw=1.0))
    flecha(ax, (x - 0.7, y), (x + 0.6, y), lw=0.8, escala=6)
    rotulo(ax, x + 2.2, y, texto, size=size, ha="left", weight="bold")


def titulo(ax, fig, x, y, texto, parentesis=None, size=11, italica=False):
    """Título de segundo nivel, con la aclaración entre paréntesis en cuerpo menor.

    El paréntesis se ubica midiendo el ancho real del texto anterior, así queda
    pegado sin depender de un desplazamiento calculado a ojo para cada palabra.
    """
    flecha(ax, (x - 1.8, y), (x - 0.6, y))
    estilo = "italic" if italica else "normal"
    t = rotulo(ax, x, y, texto, size=size, ha="left", style=estilo)
    if parentesis:
        fig.canvas.draw()
        borde = t.get_window_extent().transformed(ax.transData.inverted())
        rotulo(ax, borde.x1 + 0.5, y, parentesis, size=size - 3, ha="left")
    return t


def llave(ax, x_desde, x_hasta, y, alto=1.2, color=AZUL, lw=0.9):
    """Llave horizontal que abarca un rango, con las puntas hacia el contenido.

    El signo de `alto` decide hacia dónde apuntan las puntas: positivo para una
    llave que va debajo de lo que agrupa, negativo para una que va encima.
    """
    ax.plot([x_desde, x_hasta], [y, y], color=color, lw=lw, solid_capstyle="butt")
    for x in (x_desde, x_hasta):
        ax.plot([x, x], [y, y + alto], color=color, lw=lw, solid_capstyle="butt")
