"""Piezas de gráficos que se repiten en los scripts del curso.

Las funciones reciben el eje donde dibujan, igual que las de chiricoca, así que
se combinan con ellas. Las que dibujan mapas leen el sistema de coordenadas de
la capa que reciben, y por eso sirven igual para un mapa en grados que para uno
en metros.
"""

import numpy as np
import pyproj
from chiricoca.colors import colormap_from_palette
from chiricoca.maps import choropleth_map, geographical_scale
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import FuncFormatter
from scipy.stats import gaussian_kde

from visutils.estilo import AZUL, GRIS, MAGENTA


def miles(valor, decimales=0):
    """El número con los separadores del castellano: 1.486 y 4,46."""
    return f"{valor:_.{decimales}f}".replace(".", ",").replace("_", ".")


def porcentaje(fraccion, decimales=0):
    """Una fracción escrita como porcentaje, con la coma decimal del castellano."""
    return f"{miles(fraccion * 100, decimales)}%"


# Para los ejes: matplotlib separa los miles con coma, y 1,486 es otro número.
FORMATO_MILES = FuncFormatter(lambda valor, _: miles(valor))
FORMATO_PORCENTAJE = FuncFormatter(lambda fraccion, _: porcentaje(fraccion))


def barra_de_escala(ax, crs):
    """Barra de distancia para un mapa dibujado en `crs`.

    En un sistema métrico una unidad del eje es un metro. En grados depende de
    la latitud, porque un grado de longitud mide 111,3 km en el ecuador y 92,9
    km en Santiago, así que se calcula en el centro del mapa.
    """
    if pyproj.CRS.from_user_input(crs).is_geographic:
        metros_por_unidad = 111_320 * np.cos(np.radians(np.mean(ax.get_ylim())))
    else:
        metros_por_unidad = 1.0

    # La caja blanca deja leer la escala cuando cae sobre el dato.
    geographical_scale(
        ax, dx=metros_por_unidad, units="m", location="lower right",
        frameon=True, box_color="white", box_alpha=0.8, color=AZUL,
        font_properties={"size": 6}, scale_loc="top", length_fraction=0.25,
        # solo se dibuja la barra horizontal, así que el aviso por el aspecto
        # del eje no aplica
        rotation="horizontal-only",
    )


def fondo_de_mapa(ax, comunas, relleno=GRIS, escala=True):
    """Las comunas debajo del dato, sus límites en blanco encima y la escala.

    Sin el relleno, la forma de la ciudad la da el dato y no la geografía. Sin
    los límites por encima, una nube de celdas sobre Santiago no se distingue de
    una sobre cualquier otra ciudad.
    """
    comunas.plot(ax=ax, facecolor=relleno, edgecolor="none", zorder=0)
    comunas.boundary.plot(ax=ax, color="white", linewidth=0.3, zorder=3)

    # El encuadre es el de las comunas. Sin fijarlo, matplotlib deja un margen
    # alrededor de los datos, y la escala y la leyenda quedan en ese margen,
    # fuera del mapa.
    xmin, ymin, xmax, ymax = comunas.total_bounds
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    if escala:
        barra_de_escala(ax, comunas.crs)
    ax.set_axis_off()


def barra_de_rangos(ax, bordes, palette, etiqueta, formato=miles):
    """Escala de clases debajo del mapa, con un bloque del mismo ancho por clase.

    Si el mapa muestra el dato en rangos, la escala muestra esos mismos rangos.
    Si cada bloque midiera según el valor de sus cortes, en una distribución
    sesgada los cortes bajos quedarían tan juntos que sus rótulos se
    encabalgarían. La barra va en un eje inserto bajo el mapa: una barra que le
    quitara alto al mapa lo achicaría también a lo ancho, porque su aspecto está
    fijo.
    """
    colores = colormap_from_palette(palette, n_colors=len(bordes) - 1)
    barra = ax.get_figure().colorbar(
        ScalarMappable(norm=BoundaryNorm(bordes, colores.N), cmap=colores),
        cax=ax.inset_axes([0.1, -0.06, 0.8, 0.035]), orientation="horizontal",
        ticks=bordes, spacing="uniform",
    )
    barra.set_label(etiqueta, fontsize=7)
    barra.ax.tick_params(labelsize=6)
    barra.ax.set_xticklabels([formato(borde) for borde in bordes])
    return barra


def coropleta(capa, columna, ax, comunas, etiqueta, palette="Blues", bins=None, k=5,
              formato=miles):
    """Coropleta sobre el fondo comunal, con la escala de sus clases debajo.

    Sin `bins` corta por cuantiles, que en una variable de conteos reparte las
    unidades entre las clases. Devuelve los cortes que usó.
    """
    fondo_de_mapa(ax, comunas)
    clases = ({"binning": "custom", "bins": bins} if bins is not None
              else {"binning": "quantiles", "k": k})
    _, info = choropleth_map(capa, columna, ax=ax, palette=palette, edgecolor="none",
                             linewidth=0, legend=None, **clases)
    barra_de_rangos(ax, info["bins"], palette, etiqueta, formato=formato)
    return info["bins"]


def raincloud(datos, x, y, orden, ax, color=AZUL, semilla=0):
    """Media nube de densidad, una caja delgada y las observaciones debajo.

    Un boxplot resume cinco números y esconde cuántas observaciones hay detrás.
    El raincloud muestra las tres cosas, y funciona con pocas categorías: con
    muchas, cada fila queda tan angosta que la nube deja de leerse.

    Cada categoría ocupa una unidad del eje vertical: la nube sube 0,4 desde su
    línea, la caja va justo debajo y la lluvia más abajo. La nube se normaliza
    por su máximo, así que compara la forma de las distribuciones y no su
    tamaño. La dispersión vertical de la lluvia es aleatoria y sale de
    `semilla`, así que la figura es la misma en cada corrida.
    """
    azar = np.random.default_rng(semilla)

    for posicion, categoria in enumerate(orden):
        valores = datos.loc[datos[y] == categoria, x].dropna().to_numpy()

        # La densidad se estima solo entre el mínimo y el máximo observados.
        malla = np.linspace(valores.min(), valores.max(), 300)
        densidad = gaussian_kde(valores)(malla)
        ax.fill_between(malla, posicion, posicion - 0.4 * densidad / densidad.max(),
                        color=color, alpha=0.45, linewidth=0)

        ax.boxplot(valores, positions=[posicion + 0.08], widths=0.08,
                   orientation="horizontal", showfliers=False, patch_artist=True,
                   boxprops={"facecolor": "white", "edgecolor": color, "linewidth": 0.7},
                   medianprops={"color": MAGENTA, "linewidth": 1.2},
                   whiskerprops={"color": color, "linewidth": 0.7},
                   capprops={"linewidth": 0})

        lluvia = posicion + 0.26 + azar.uniform(-0.08, 0.08, len(valores))
        ax.scatter(valores, lluvia, s=2, color=color, alpha=0.5, linewidth=0)

    # La primera categoría arriba, como en una tabla.
    ax.set_yticks(range(len(orden)), orden)
    ax.set_ylim(len(orden) - 0.6, -0.55)
    ax.grid(axis="y", visible=False)
    return ax


def leyenda_de_tamano(ax, referencias, area, rotulo, loc="upper left", fontsize=7,
                      **estilo):
    """Marcadores de referencia para un gráfico donde el área codifica un valor.

    `area` lleva un valor del dato al área del marcador en puntos cuadrados, que
    es lo que recibe el parámetro `s` de `scatter`. Sin esta leyenda el tamaño
    codifica algo que nadie puede leer.
    """
    for valor in referencias:
        ax.scatter([], [], s=area(valor), label=f"{miles(valor)} {rotulo}", **estilo)
    return ax.legend(frameon=False, loc=loc, fontsize=fontsize, labelspacing=1.2,
                     borderpad=0.8)
