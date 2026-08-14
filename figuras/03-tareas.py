"""Figuras de la unidad 03.

Reconstruye la taxonomía de tareas de Munzner en castellano, partida en sus dos
mitades: las acciones (qué se quiere hacer) y los objetivos (sobre qué parte de
los datos). Cada hoja de la taxonomía lleva un pictograma que muestra la forma
del resultado, porque el nombre solo no basta para distinguirlas.

Uso: uv run python figuras/03-tareas.py
"""

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from chiricoca.base.paths import add_project_root
from matplotlib.patches import Circle, Polygon, Rectangle

# Este script vive en una subcarpeta, así que hay que agregar la raíz del
# repositorio al path para poder importar visutils.
add_project_root(marker="pyproject.toml")

from visutils.diagramas import encabezado, flecha, rotulo, titulo  # noqa: E402
from visutils.estilo import AZUL, GRIS, MAGENTA, estilo_curso  # noqa: E402

estilo_curso(dpi=300)

DIR_IMAGENES = Path("images")
DIR_IMAGENES.mkdir(exist_ok=True)

ANCHO = 100.0
ANCHO_FIG = 7.6
rng = np.random.default_rng(3)


def lienzo(alto):
    fig, ax = plt.subplots(figsize=(ANCHO_FIG, ANCHO_FIG * alto / ANCHO))
    ax.set_xlim(0, ANCHO)
    ax.set_ylim(0, alto)
    ax.set_aspect("equal")
    ax.set_axis_off()
    return fig, ax


def hoja(ax, fig, x, y, texto):
    """Nombre de una tarea concreta: tercer nivel, en cursiva."""
    titulo(ax, fig, x, y, texto, size=7, italica=True)


# --- Pictogramas. Cada uno se dibuja dentro de una caja de 11 por 7 unidades
# cuya esquina inferior izquierda es (x, y), así se posicionan todos igual.
ANCHO_P, ALTO_P = 11.0, 7.0


def ejes(ax, x, y):
    """Par de ejes tenues, como los del diagrama original."""
    ax.plot([x, x], [y, y + ALTO_P], color=AZUL, lw=0.5)
    ax.plot([x, x + ANCHO_P], [y, y], color=AZUL, lw=0.5)


def pic_tendencia(ax, x, y):
    ejes(ax, x, y)
    t = np.linspace(0, 1, 40)
    ax.plot(x + 1 + t * (ANCHO_P - 2), y + 1.2 + 5 * (t - 0.45) ** 2, color=MAGENTA, lw=1.1)


def pic_atipicos(ax, x, y):
    ejes(ax, x, y)
    xs = x + 1.5 + np.linspace(0, ANCHO_P - 3, 7)
    ax.scatter(xs, y + 1.4 + rng.uniform(0, 0.9, 7), s=3, color=AZUL)
    ax.scatter([x + ANCHO_P * 0.55], [y + ALTO_P * 0.8], s=6, color=MAGENTA)


def pic_rasgos(ax, x, y):
    ejes(ax, x, y)
    t = np.linspace(0, 1, 120)
    ax.plot(
        x + 1 + t * (ANCHO_P - 2),
        y + 3.4 + 2.2 * np.sin(9 * t) * np.exp(-1.5 * (t - 0.5) ** 2),
        color=MAGENTA,
        lw=1.0,
    )


def barras(ax, x, y, alturas, destacar=()):
    ancho = (ANCHO_P - 2) / len(alturas)
    for i, alto in enumerate(alturas):
        color = MAGENTA if i in destacar else AZUL
        ax.add_patch(
            Rectangle(
                (x + 1 + i * ancho, y + 0.6), ancho * 0.72, alto * (ALTO_P - 1.5),
                facecolor=color, lw=0,
            )
        )


DISTRIBUCION = [0.2, 0.45, 0.8, 1.0, 0.75, 0.4, 0.18]


def pic_distribucion(ax, x, y):
    ejes(ax, x, y)
    barras(ax, x, y, DISTRIBUCION)


def pic_extremos(ax, x, y):
    ejes(ax, x, y)
    barras(ax, x, y, DISTRIBUCION, destacar=(0, len(DISTRIBUCION) - 1))


def pic_dependencia(ax, x, y):
    cx, cy = x + ANCHO_P / 2, y + ALTO_P / 2
    ax.plot([cx - 2.6, cx + 2.6], [cy, cy], color=AZUL, lw=0.9)
    ax.scatter([cx - 2.6, cx + 2.6], [cy, cy], s=14, color=[AZUL, MAGENTA])


def pic_correlacion(ax, x, y):
    ejes(ax, x, y)
    t = np.linspace(0.1, 0.9, 9)
    ax.scatter(
        x + 1 + t * (ANCHO_P - 2),
        y + 1 + (t + rng.uniform(-0.12, 0.12, 9)) * (ALTO_P - 2),
        s=3,
        color=AZUL,
    )
    ax.plot([x + 1.5, x + ANCHO_P - 1], [y + 1.2, y + ALTO_P - 1], color=MAGENTA, lw=0.9)


def pic_similitud(ax, x, y):
    ejes(ax, x, y)
    t = np.linspace(0, 1, 40)
    for desfase, color in [(0.0, AZUL), (0.5, MAGENTA)]:
        ax.plot(
            x + 1 + t * (ANCHO_P - 2),
            y + 1.4 + desfase + 4 * (t - 0.55) ** 2,
            color=color,
            lw=0.9,
        )


# Red chica reutilizada por los pictogramas de red.
NODOS = np.array([[0.15, 0.75], [0.45, 0.95], [0.5, 0.45], [0.85, 0.7], [0.3, 0.15], [0.75, 0.2]])
ARISTAS = [(0, 1), (1, 2), (2, 3), (0, 4), (2, 4), (4, 5), (2, 5), (3, 5)]


def _red(ax, x, y, escala=1.0, camino=()):
    puntos = np.column_stack(
        [x + 1 + NODOS[:, 0] * (ANCHO_P - 2) * escala, y + 0.8 + NODOS[:, 1] * (ALTO_P - 1.6)]
    )
    for a, b in ARISTAS:
        destacada = (a, b) in camino or (b, a) in camino
        ax.plot(
            *zip(puntos[a], puntos[b]),
            color=MAGENTA if destacada else AZUL,
            lw=1.2 if destacada else 0.6,
        )
    ax.scatter(puntos[:, 0], puntos[:, 1], s=5, color=AZUL, zorder=3)


def pic_topologia(ax, x, y):
    _red(ax, x, y)


def pic_caminos(ax, x, y):
    _red(ax, x, y, camino=[(0, 4), (4, 5), (5, 3)])


def pic_forma(ax, x, y):
    contorno = np.array(
        [(0.1, 0.4), (0.3, 0.85), (0.65, 0.95), (0.9, 0.6), (0.75, 0.15), (0.35, 0.1)]
    )
    puntos = np.column_stack(
        [x + 1 + contorno[:, 0] * (ANCHO_P - 2), y + 0.8 + contorno[:, 1] * (ALTO_P - 1.6)]
    )
    ax.add_patch(Polygon(puntos, facecolor=GRIS, edgecolor=AZUL, lw=0.8))


def pic_descubrir(ax, x, y):
    barras(ax, x, y, [0.35, 0.7, 0.5, 0.9])
    ax.add_patch(
        Circle((x + ANCHO_P * 0.62, y + ALTO_P * 0.6), 2.0, facecolor="none", edgecolor=MAGENTA, lw=1.0)
    )
    ax.plot(
        [x + ANCHO_P * 0.62 + 1.4, x + ANCHO_P * 0.62 + 3.0],
        [y + ALTO_P * 0.6 - 1.4, y + ALTO_P * 0.6 - 3.0],
        color=MAGENTA,
        lw=1.0,
    )


def pic_presentar(ax, x, y):
    barras(ax, x, y, [0.35, 0.7, 0.5, 0.9], destacar=(3,))
    flecha(ax, (x + 1, y + ALTO_P - 0.5), (x + ANCHO_P * 0.72, y + ALTO_P - 0.5), lw=0.8, escala=6)


def pic_disfrutar(ax, x, y):
    cx, cy = x + ANCHO_P / 2, y + ALTO_P / 2
    ax.add_patch(Circle((cx, cy), 2.4, facecolor="none", edgecolor=AZUL, lw=0.9))
    ax.scatter([cx - 0.9, cx + 0.9], [cy + 0.7, cy + 0.7], s=3, color=AZUL)
    t = np.linspace(np.radians(200), np.radians(340), 30)
    ax.plot(cx + 1.4 * np.cos(t), cy - 0.2 + 1.4 * np.sin(t), color=MAGENTA, lw=0.9)


def pic_anotar(ax, x, y):
    _red(ax, x, y, escala=0.7)
    ax.add_patch(
        Rectangle((x + ANCHO_P * 0.62, y + ALTO_P * 0.55), 3.4, 1.6, facecolor=MAGENTA, lw=0)
    )


def pic_registrar(ax, x, y):
    ejes(ax, x, y)
    t = np.linspace(0, 1, 40)
    ax.plot(x + 1 + t * (ANCHO_P - 2), y + 2 + 2.5 * np.sin(4 * t), color=AZUL, lw=0.8)
    ax.add_patch(Circle((x + ANCHO_P * 0.5, y + ALTO_P * 0.75), 1.3, facecolor=MAGENTA, lw=0))


def pic_derivar(ax, x, y):
    for i in range(3):
        for j in range(3):
            ax.add_patch(
                Rectangle(
                    (x + 0.8 + i * 1.3, y + 1.4 + j * 1.5), 1.0, 1.1,
                    facecolor=MAGENTA if (i, j) == (1, 1) else GRIS, lw=0,
                )
            )
    flecha(ax, (x + 5.2, y + ALTO_P / 2), (x + 6.6, y + ALTO_P / 2), lw=0.8, escala=6)
    _red(ax, x + 5.4, y, escala=0.5)


def pic_identificar(ax, x, y):
    ejes(ax, x, y)
    xs = x + 1.5 + np.linspace(0, ANCHO_P - 3.5, 6)
    ax.scatter(xs, y + 1.4 + rng.uniform(0, 1.2, 6), s=3, color=AZUL)
    ax.scatter([x + ANCHO_P * 0.45], [y + ALTO_P * 0.7], s=8, color=MAGENTA)
    ax.add_patch(
        Circle((x + ANCHO_P * 0.45, y + ALTO_P * 0.7), 1.4, facecolor="none", edgecolor=MAGENTA, lw=0.7)
    )


def pic_comparar(ax, x, y):
    for desplazamiento, color in [(0.0, AZUL), (2.6, MAGENTA)]:
        t = np.linspace(0, 1, 30)
        ax.plot(
            x + 1 + t * (ANCHO_P - 2),
            y + 1.2 + desplazamiento + 2.4 * t**2,
            color=color,
            lw=0.9,
        )


def pic_resumir(ax, x, y):
    for i in range(7):
        for j in range(4):
            ax.add_patch(
                Rectangle(
                    (x + 1 + i * 1.35, y + 1.2 + j * 1.35), 1.05, 1.05,
                    facecolor=MAGENTA if (i + 2 * j) % 3 == 0 else GRIS, lw=0,
                )
            )


# %%
# Acciones: qué se quiere hacer con los datos.
fig, ax = lienzo(52.0)

encabezado(ax, 2.6, 48.5, "Acciones", size=11)

titulo(ax, fig, 5.0, 43.0, "Analizar", size=9)

titulo(ax, fig, 8.0, 38.4, "Consumir", size=8)
for x, nombre, pic in [
    (10.0, "Descubrir", pic_descubrir),
    (24.0, "Presentar", pic_presentar),
    (38.0, "Disfrutar", pic_disfrutar),
]:
    hoja(ax, fig, x, 34.4, nombre)
    pic(ax, x - 0.5, 25.5)

titulo(ax, fig, 8.0, 20.6, "Producir", size=8)
for x, nombre, pic in [
    (10.0, "Anotar", pic_anotar),
    (24.0, "Registrar", pic_registrar),
    (38.0, "Derivar", pic_derivar),
]:
    hoja(ax, fig, x, 16.6, nombre)
    pic(ax, x - 0.5, 7.5)

titulo(ax, fig, 57.0, 43.0, "Buscar", size=9)

# La búsqueda se cruza en dos preguntas: si se sabe qué se busca y si se sabe
# dónde está. Las cuatro combinaciones tienen nombre propio.
X0, Y0, COL, FIL = 57.0, 26.0, 13.5, 4.6
CABECERAS = ["", "Sé qué busco", "No sé qué busco"]
FILAS = [["Sé dónde está", "Recuperar", "Recorrer"], ["No sé dónde está", "Ubicar", "Explorar"]]

for j, texto in enumerate(CABECERAS):
    if texto:
        rotulo(ax, X0 + j * COL + COL / 2, Y0 + 2 * FIL + 1.6, texto, size=6.5)
for i, fila in enumerate(FILAS):
    y = Y0 + (1 - i) * FIL
    rotulo(ax, X0 + COL - 1.0, y + FIL / 2, fila[0], size=6.5, ha="right")
    for j, celda in enumerate(fila[1:], start=1):
        ax.add_patch(
            Rectangle((X0 + j * COL, y), COL, FIL, facecolor=GRIS, edgecolor="white", lw=1.2)
        )
        rotulo(ax, X0 + j * COL + COL / 2, y + FIL / 2, celda, size=7, style="italic")

titulo(ax, fig, 57.0, 20.6, "Consultar", size=9)
for x, nombre, pic in [
    (59.0, "Identificar", pic_identificar),
    (73.0, "Comparar", pic_comparar),
    (87.0, "Resumir", pic_resumir),
]:
    hoja(ax, fig, x, 16.6, nombre)
    pic(ax, x - 0.5, 7.5)

fig.savefig(DIR_IMAGENES / "03-tareas-acciones.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/03-tareas-acciones.png")

# %%
# Objetivos: sobre qué parte de los datos recae la acción.
fig, ax = lienzo(62.0)

encabezado(ax, 2.6, 58.5, "Objetivos", size=11)

titulo(ax, fig, 5.0, 53.0, "Todos los datos", size=9)
for x, nombre, pic in [
    (8.0, "Tendencias", pic_tendencia),
    (30.0, "Valores atípicos", pic_atipicos),
    (58.0, "Rasgos", pic_rasgos),
]:
    hoja(ax, fig, x, 48.6, nombre)
    pic(ax, x - 0.5, 40.0)

titulo(ax, fig, 5.0, 35.4, "Atributos", size=9)
titulo(ax, fig, 8.0, 31.4, "Uno", size=8)
for x, nombre, pic in [(10.0, "Distribución", pic_distribucion), (26.0, "Extremos", pic_extremos)]:
    hoja(ax, fig, x, 27.6, nombre)
    pic(ax, x - 0.5, 19.0)

titulo(ax, fig, 44.0, 31.4, "Muchos", size=8)
for x, nombre, pic in [
    (46.0, "Dependencia", pic_dependencia),
    (64.0, "Correlación", pic_correlacion),
    (81.0, "Similitud", pic_similitud),
]:
    hoja(ax, fig, x, 27.6, nombre)
    pic(ax, x - 0.5, 19.0)

titulo(ax, fig, 5.0, 13.6, "Redes", size=9)
for x, nombre, pic in [(10.0, "Topología", pic_topologia), (30.0, "Caminos", pic_caminos)]:
    hoja(ax, fig, x, 9.6, nombre)
    pic(ax, x - 0.5, 1.0)

titulo(ax, fig, 58.0, 13.6, "Espacio", size=9)
hoja(ax, fig, 63.0, 9.6, "Forma")
pic_forma(ax, 62.5, 1.0)

fig.savefig(DIR_IMAGENES / "03-tareas-objetivos.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/03-tareas-objetivos.png")
