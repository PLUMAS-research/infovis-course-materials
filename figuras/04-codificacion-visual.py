"""Figuras de la unidad 04.

Construye las demostraciones de la clase de codificación visual: el ranking de
canales por efectividad, la diferencia entre comparar con y sin base común, y
qué pasa cuando un canal se divide en más niveles de los que se distinguen.

Uso: uv run python figuras/04-codificacion-visual.py
"""

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from chiricoca.base.paths import add_project_root
from matplotlib.patches import Arc, Circle, Polygon, Rectangle, Wedge

add_project_root(marker="pyproject.toml")

from visutils.diagramas import encabezado, flecha, rotulo  # noqa: E402
from visutils.estilo import AZUL, DPI, GRIS, MAGENTA, estilo_curso  # noqa: E402

estilo_curso(dpi=DPI)

DIR_IMAGENES = Path("images")
DIR_IMAGENES.mkdir(exist_ok=True)

# %%
# El ranking de canales. Los canales se ordenan por su efectividad para las
# tareas que resuelven: los de magnitud sirven a atributos ordenados y los de
# identidad a atributos categóricos.
# Adaptado de Munzner, T. (2014). Visualization Analysis and Design, figura 5.6.

ANCHO = 100.0
ALTO_FILA = 4.0
# Cada pictograma se dibuja dentro de una caja de este tamaño, con la esquina
# inferior izquierda en (x, y), así todos quedan alineados.
ANCHO_P, ALTO_P = 17.0, 2.6

GRISES = ["#F2F2F5", "#C6C6D1", "#8E8EA3", "#4A4A63"]
SATURACIONES = ["#FBEAF3", "#EFB0D2", "#DF6FAE", "#CF3889"]
MATICES = ["#E0A32E", "#CF3889", "#2E9E8F", "#3A6FB5"]


def marco(ax, x, y):
    """Rectángulo tenue que delimita la caja del pictograma (invisible)."""
    return x, y


def pic_posicion_comun(ax, x, y):
    for i, (largo, punto) in enumerate([(0.85, 0.72), (0.85, 0.42)]):
        base = y + 0.6 + i * 1.3
        ax.plot([x, x + ANCHO_P * largo], [base, base], color=AZUL, lw=0.8)
        for extremo in (x, x + ANCHO_P * largo):
            ax.plot([extremo, extremo], [base - 0.25, base + 0.25], color=AZUL, lw=0.8)
        ax.scatter([x + ANCHO_P * punto], [base], s=10, color=AZUL, zorder=3)


def pic_posicion_desalineada(ax, x, y):
    for i, (inicio, largo, punto) in enumerate([(0.0, 0.45, 0.22), (0.35, 0.6, 0.75)]):
        base = y + 0.6 + i * 1.3
        x0, x1 = x + ANCHO_P * inicio, x + ANCHO_P * (inicio + largo)
        ax.plot([x0, x1], [base, base], color=AZUL, lw=0.8)
        for extremo in (x0, x1):
            ax.plot([extremo, extremo], [base - 0.25, base + 0.25], color=AZUL, lw=0.8)
        ax.scatter([x + ANCHO_P * punto], [base], s=10, color=AZUL, zorder=3)


def pic_largo(ax, x, y):
    for i, largo in enumerate([0.15, 0.35, 0.6]):
        base = y + ALTO_P / 2
        x0 = x + i * ANCHO_P * 0.33
        ax.plot([x0, x0 + ANCHO_P * largo * 0.5], [base, base], color=AZUL, lw=1.6)


def pic_angulo(ax, x, y):
    for i, grados in enumerate([90, 55, 20, 0]):
        cx = x + 1.5 + i * 4.0
        rad = np.radians(grados)
        ax.plot(
            [cx, cx + 2.6 * np.cos(rad)],
            [y + 0.5, y + 0.5 + 2.6 * np.sin(rad)],
            color=AZUL,
            lw=1.0,
        )


def pic_area(ax, x, y):
    for i, lado in enumerate([0.5, 1.0, 1.6, 2.3]):
        ax.add_patch(
            Rectangle((x + 1 + i * 4.2, y + 0.2), lado, lado, facecolor=AZUL, lw=0)
        )


def pic_profundidad(ax, x, y):
    for i, largo in enumerate([3.0, 6.0]):
        base = y + 0.8 + i * 1.2
        x0 = x + i * 0.5
        flecha(ax, (x0, base), (x0 + largo, base), lw=0.7, escala=5)
        ax.scatter([x0 + largo + 0.8], [base], s=10, color=AZUL, zorder=3)


def _fila_cuadrados(ax, x, y, colores, borde=None):
    for i, color in enumerate(colores):
        ax.add_patch(
            Rectangle(
                (x + 1 + i * 3.4, y + 0.4),
                2.4,
                1.8,
                facecolor=color,
                edgecolor=borde or "none",
                lw=0.5,
            )
        )


def pic_luminosidad(ax, x, y):
    _fila_cuadrados(ax, x, y, GRISES, borde=AZUL)


def pic_saturacion(ax, x, y):
    _fila_cuadrados(ax, x, y, SATURACIONES, borde=AZUL)


def pic_curvatura(ax, x, y):
    for i, apertura in enumerate([0.1, 60, 110, 170]):
        cx = x + 2 + i * 4.0
        if apertura < 1:
            ax.plot([cx, cx], [y + 0.4, y + 2.2], color=AZUL, lw=1.0)
        else:
            ax.add_patch(
                Arc(
                    (cx, y + 1.3),
                    3.0,
                    3.0,
                    theta1=270 - apertura / 2,
                    theta2=270 + apertura / 2,
                    color=AZUL,
                    lw=1.0,
                )
            )


def pic_volumen(ax, x, y):
    for i, lado in enumerate([0.6, 1.1, 1.7, 2.3]):
        bx, by = x + 1 + i * 4.2, y + 0.2
        prof = lado * 0.4
        ax.add_patch(Rectangle((bx, by), lado, lado, facecolor=GRIS, edgecolor=AZUL, lw=0.4))
        ax.add_patch(
            Polygon(
                [(bx, by + lado), (bx + prof, by + lado + prof),
                 (bx + lado + prof, by + lado + prof), (bx + lado, by + lado)],
                facecolor="white", edgecolor=AZUL, lw=0.4,
            )
        )
        ax.add_patch(
            Polygon(
                [(bx + lado, by), (bx + lado + prof, by + prof),
                 (bx + lado + prof, by + lado + prof), (bx + lado, by + lado)],
                facecolor=AZUL, edgecolor=AZUL, lw=0.4,
            )
        )


def pic_region(ax, x, y):
    for cx, cy, lado in [(1.5, 1.4, 1.4), (5.5, 0.5, 1.8), (10.0, 0.9, 2.2)]:
        ax.add_patch(Rectangle((x + cx, y + cy), lado, lado, facecolor=AZUL, lw=0))


def pic_matiz(ax, x, y):
    _fila_cuadrados(ax, x, y, MATICES)


def pic_movimiento(ax, x, y):
    posiciones = [(2.0, 1.8), (5.0, 0.8), (8.5, 2.0), (12.0, 1.2)]
    for i, (cx, cy) in enumerate(posiciones):
        ax.scatter([x + cx], [y + cy], s=14, color=AZUL, zorder=3)
        if i % 2 == 0:
            ax.add_patch(
                Arc((x + cx, y + cy), 2.2, 2.2, theta1=40, theta2=300, color=AZUL, lw=0.7)
            )


def pic_forma(ax, x, y):
    cy = y + ALTO_P / 2
    ax.plot([x + 1.6, x + 1.6], [cy - 0.9, cy + 0.9], color=AZUL, lw=1.4)
    ax.plot([x + 0.7, x + 2.5], [cy, cy], color=AZUL, lw=1.4)
    ax.add_patch(Circle((x + 6.0, cy), 0.9, facecolor=AZUL, lw=0))
    ax.add_patch(Rectangle((x + 9.6, cy - 0.85), 1.7, 1.7, facecolor=AZUL, lw=0))
    ax.add_patch(
        Polygon([(x + 14.4, cy - 0.85), (x + 15.4, cy + 0.95), (x + 16.4, cy - 0.85)],
                facecolor=AZUL, lw=0)
    )


MAGNITUD = [
    ("Posición en escala común", pic_posicion_comun),
    ("Posición en escala no alineada", pic_posicion_desalineada),
    ("Largo (tamaño 1D)", pic_largo),
    ("Inclinación o ángulo", pic_angulo),
    ("Área (tamaño 2D)", pic_area),
    ("Profundidad (posición 3D)", pic_profundidad),
    ("Luminosidad", pic_luminosidad),
    ("Saturación", pic_saturacion),
    ("Curvatura", pic_curvatura),
    ("Volumen (tamaño 3D)", pic_volumen),
]

IDENTIDAD = [
    ("Región espacial", pic_region),
    ("Matiz", pic_matiz),
    ("Movimiento", pic_movimiento),
    ("Forma", pic_forma),
]

alto = len(MAGNITUD) * ALTO_FILA + 8
fig, ax = plt.subplots(figsize=(7.8, 7.8 * alto / ANCHO))
ax.set_xlim(0, ANCHO)
ax.set_ylim(0, alto)
ax.set_aspect("equal")
ax.set_axis_off()

y_tope = alto - 6.5
encabezado(ax, 2.4, y_tope + 3.0, "Canales de magnitud", size=9)
rotulo(ax, 6.0, y_tope + 1.2, "para atributos ordenados", size=7.5, ha="left", style="italic")
encabezado(ax, 58.0, y_tope + 3.0, "Canales de identidad", size=9)
rotulo(ax, 61.6, y_tope + 1.2, "para atributos categóricos", size=7.5, ha="left", style="italic")

for i, (nombre, pictograma) in enumerate(MAGNITUD):
    y = y_tope - (i + 1) * ALTO_FILA
    rotulo(ax, 2.4, y + ALTO_P / 2, nombre, size=7.5, ha="left")
    pictograma(ax, 30.0, y)

for i, (nombre, pictograma) in enumerate(IDENTIDAD):
    y = y_tope - (i + 1) * ALTO_FILA
    rotulo(ax, 58.0, y + ALTO_P / 2, nombre, size=7.5, ha="left")
    pictograma(ax, 80.0, y)

# La flecha de efectividad ordena la columna de magnitud de arriba hacia abajo.
x_flecha = 53.0
y_arriba, y_abajo = y_tope - ALTO_FILA * 0.4, y_tope - len(MAGNITUD) * ALTO_FILA + 1.0
flecha(ax, (x_flecha, y_abajo), (x_flecha, y_arriba), lw=1.0, escala=8)
rotulo(ax, x_flecha - 1.2, y_arriba, "más efectivo", size=7, rotation=90, va="top", ha="center")
rotulo(ax, x_flecha - 1.2, y_abajo, "menos efectivo", size=7, rotation=90, va="bottom", ha="center")

fig.savefig(DIR_IMAGENES / "04-canales-ranking.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-canales-ranking.png")

# %%
# Razonamiento relativo. La percepción compara, no mide: la misma diferencia se
# estima mejor cuando las marcas comparten una base y peor cuando flotan.
# Basado en Cleveland, W. S. & McGill, R. (1984). Graphical Perception.

VALORES = [7.0, 9.0]

fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.4))

# Sin base común: las dos barras arrancan en alturas distintas.
bases = [2.5, 0.0]
for i, (valor, base) in enumerate(zip(VALORES, bases)):
    axes[0].add_patch(Rectangle((i * 2 + 0.5, base), 1.0, valor, facecolor=AZUL, lw=0))
axes[0].set_title("Sin base común")
axes[0].set_xlim(0, 4)
axes[0].set_ylim(0, 12)

# Con base común y eje: la comparación se vuelve una lectura de largo.
for i, valor in enumerate(VALORES):
    axes[1].add_patch(Rectangle((i * 2 + 0.5, 0), 1.0, valor, facecolor=MAGENTA, lw=0))
axes[1].set_title("Con base común")
axes[1].set_xlim(0, 4)
axes[1].set_ylim(0, 12)
axes[1].axhline(0, color=AZUL, lw=0.8)

for ax in axes:
    ax.set_xticks([])
    ax.grid(False)

axes[0].set_yticks([])
axes[1].set_yticks([0, 5, 10])

fig.savefig(DIR_IMAGENES / "04-base-comun.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-base-comun.png")
print(f"  Las dos barras miden {VALORES[0]:.0f} y {VALORES[1]:.0f}")

# %%
# Distinguibilidad. Un canal admite pocos niveles separables: repartir el mismo
# atributo en más categorías no agrega información, la vuelve ilegible.

fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.2), sharey=True)

for ax, n in zip(axes, [3, 10]):
    grosores = np.linspace(0.6, 4.0, n)
    for i, grosor in enumerate(grosores):
        y = 1 - i / max(n - 1, 1)
        ax.plot([0.05, 0.95], [y, y], color=AZUL, lw=grosor, solid_capstyle="butt")
    ax.set_title(f"{n} niveles de grosor")
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.15, 1.15)
    ax.set_axis_off()

fig.savefig(DIR_IMAGENES / "04-distinguibilidad.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-distinguibilidad.png")

# %%
# Separabilidad. Dos canales sobre la misma marca se pueden leer por separado o
# fundirse en una sola impresión. Tamaño y color se separan; ancho y alto no,
# porque lo que se percibe es el área que forman juntos.

rng = np.random.default_rng(4)
A = np.array([1.0, 2.6, 1.0, 2.6, 1.8, 1.8])
B = np.array([0.2, 0.2, 0.9, 0.9, 0.55, 0.55])

fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8))

xs = np.array([0, 1, 2, 3, 4, 5])
axes[0].scatter(xs, np.zeros_like(xs), s=A * 260, c=B, cmap="cividis", vmin=0, vmax=1)
axes[0].set_title("Separables: tamaño y color", fontsize=9)
axes[0].set_xlim(-0.8, 5.8)
axes[0].set_ylim(-1, 1)

for x, ancho, alto in zip(xs, A * 0.28, B * 1.6):
    axes[1].add_patch(Rectangle((x - ancho / 2, -alto / 2), ancho, alto, facecolor=AZUL, lw=0))
axes[1].set_title("Integrales: ancho y alto", fontsize=9)
axes[1].set_xlim(-0.8, 5.8)
axes[1].set_ylim(-1, 1)

for ax in axes:
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)

fig.savefig(DIR_IMAGENES / "04-separabilidad.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-separabilidad.png")

# %%
# Ley de Stevens. El estímulo percibido crece como una potencia del estímulo
# real, y el exponente depende del canal. Bajo 1 el canal subestima: hay que
# aumentar mucho el dato para que se note el cambio.
# Exponentes aproximados, del orden de los que reporta la literatura.

EXPONENTES = {"Largo": 1.0, "Área": 0.7, "Profundidad": 0.5, "Luminosidad": 0.4}
estimulo = np.linspace(0, 1, 100)

fig, ax = plt.subplots(figsize=(4.4, 2.6))
for (canal, a), color in zip(EXPONENTES.items(), [AZUL, MAGENTA, "#2E9E8F", GRIS]):
    ax.plot(estimulo, estimulo**a, color=color, lw=1.4, label=f"{canal} (a={a})")
ax.plot([0, 1], [0, 1], color="#B0B0BC", lw=0.8, ls=":")
ax.set_title("Estímulo percibido según el canal")
ax.set_xlabel("Magnitud real")
ax.set_ylabel("Magnitud percibida")
ax.legend(fontsize=6)
fig.savefig(DIR_IMAGENES / "04-stevens-ley.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-stevens-ley.png")

# %%
# La misma serie con largo y con área. El largo se lee contra una escala; el
# área se estima, y la estimación se queda corta porque su exponente es menor.

SERIE = np.array([100.0, 200.0, 400.0, 800.0])

fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.4))
axes[0].bar(range(len(SERIE)), SERIE, color=AZUL, width=0.6)
axes[0].set_title("Largo", fontsize=9)
axes[0].set_xticks(range(len(SERIE)))
axes[0].set_xticklabels([f"{v:.0f}" for v in SERIE], fontsize=7)

axes[1].scatter(range(len(SERIE)), np.zeros(len(SERIE)), s=SERIE / SERIE.max() * 900, color=AZUL)
axes[1].set_title("Área", fontsize=9)
axes[1].set_xticks(range(len(SERIE)))
axes[1].set_xticklabels([f"{v:.0f}" for v in SERIE], fontsize=7)
axes[1].set_yticks([])
axes[1].set_ylim(-1, 1)
axes[1].grid(False)

fig.savefig(DIR_IMAGENES / "04-largo-vs-area.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-largo-vs-area.png")
print(f"  La última barra vale {SERIE[-1] / SERIE[0]:.0f} veces la primera")

# %%
# Tres distribuciones distintas en tres gráficos de torta. El ángulo y el área
# no alcanzan para distinguirlas, y hay que leer los números para separarlas.

DISTRIBUCIONES = [
    [26, 25, 25, 24],
    [30, 24, 23, 23],
    [23, 26, 26, 25],
]

fig, axes = plt.subplots(1, 3, figsize=(6.6, 2.4))
for ax, valores in zip(axes, DISTRIBUCIONES):
    ax.pie(valores, colors=[AZUL, MAGENTA, GRIS, "#2E9E8F"], startangle=90)
    ax.set_anchor("N")
fig.savefig(DIR_IMAGENES / "04-tortas-parecidas.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-tortas-parecidas.png")
for i, valores in enumerate(DISTRIBUCIONES, 1):
    print(f"  Torta {i}: {valores}")

# %%
# Marcas: las primitivas geométricas, ordenadas por su dimensión. La dimensión
# decide qué canales admite cada una.

fig, ax = plt.subplots(figsize=(6.6, 1.9))
ax.set_xlim(0, 100)
ax.set_ylim(0, 26)
ax.set_aspect("equal")
ax.set_axis_off()

MARCAS = ["Punto (0D)", "Línea (1D)", "Área (2D)", "Volumen (3D)"]
for i, nombre in enumerate(MARCAS):
    cx = 12 + i * 25
    rotulo(ax, cx, 3, nombre, size=8)
    if i == 0:
        ax.scatter([cx], [14], s=60, color=AZUL)
    elif i == 1:
        ax.plot([cx - 7, cx + 7], [14, 14], color=AZUL, lw=2.2)
    elif i == 2:
        ax.add_patch(Rectangle((cx - 7, 9), 14, 10, facecolor=AZUL, lw=0))
    else:
        ax.add_patch(Rectangle((cx - 7, 9), 12, 9, facecolor=GRIS, edgecolor=AZUL, lw=0.8))
        ax.add_patch(Polygon([(cx - 7, 18), (cx - 3, 22), (cx + 9, 22), (cx + 5, 18)],
                             facecolor="white", edgecolor=AZUL, lw=0.8))
        ax.add_patch(Polygon([(cx + 5, 9), (cx + 9, 13), (cx + 9, 22), (cx + 5, 18)],
                             facecolor=AZUL, edgecolor=AZUL, lw=0.8))

fig.savefig(DIR_IMAGENES / "04-marcas-local.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-marcas-local.png")

# %%
# Canales: la misma marca cambia de apariencia según el canal que se le aplique.

fig, axes = plt.subplots(1, 5, figsize=(8.4, 1.8))
CANALES = ["Posición", "Tamaño", "Matiz", "Forma", "Inclinación"]
xs = np.array([0.2, 0.5, 0.8])

for ax, canal in zip(axes, CANALES):
    if canal == "Posición":
        ax.scatter(xs, [0.3, 0.6, 0.85], s=50, color=AZUL)
    elif canal == "Tamaño":
        ax.scatter(xs, [0.6] * 3, s=[20, 70, 160], color=AZUL)
    elif canal == "Matiz":
        ax.scatter(xs, [0.6] * 3, s=70, color=[AZUL, MAGENTA, "#2E9E8F"])
    elif canal == "Forma":
        for x, marca in zip(xs, ["o", "s", "^"]):
            ax.scatter([x], [0.6], s=70, marker=marca, color=AZUL)
    else:
        for x, grados in zip(xs, [0, 40, 80]):
            rad = np.radians(grados)
            ax.plot([x - 0.07 * np.cos(rad), x + 0.07 * np.cos(rad)],
                    [0.6 - 0.18 * np.sin(rad), 0.6 + 0.18 * np.sin(rad)], color=AZUL, lw=2)
    ax.set_title(canal, fontsize=8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.1)
    ax.set_axis_off()

fig.savefig(DIR_IMAGENES / "04-canales-local.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-canales-local.png")

# %%
# Saliencia. Un canal único se procesa en paralelo y encontrar el objetivo no
# depende de cuántos distractores haya. Con dos canales combinados la búsqueda
# se vuelve serial y el tiempo crece con la cantidad.
# El objetivo va en una posición distinta en cada panel: si estuviera siempre
# en la misma, quien lo encuentra en el primero ya sabe dónde mirar.

rng_sal = np.random.default_rng(11)
OBJETIVOS = {(0, 0): 12, (0, 1): 6, (1, 0): 41, (1, 1): 30}

fig, axes = plt.subplots(2, 2, figsize=(6.2, 5.4))
for fila, n in enumerate([16, 49]):
    lado = int(np.sqrt(n))
    xs_g, ys_g = np.meshgrid(np.arange(lado), np.arange(lado))
    puntos = np.column_stack([xs_g.ravel(), ys_g.ravel()]).astype(float)
    puntos += rng_sal.uniform(-0.22, 0.22, puntos.shape)

    for columna in (0, 1):
        ax = axes[fila, columna]
        objetivo = OBJETIVOS[(fila, columna)]
        resto = np.delete(np.arange(len(puntos)), objetivo)
        if columna == 0:
            ax.scatter(puntos[resto, 0], puntos[resto, 1], s=45, color=AZUL)
        else:
            orden = rng_sal.permutation(resto)
            mitad = len(orden) // 2
            ax.scatter(puntos[orden[:mitad], 0], puntos[orden[:mitad], 1], s=45,
                       color=MAGENTA, marker="o")
            ax.scatter(puntos[orden[mitad:], 0], puntos[orden[mitad:], 1], s=45,
                       color=AZUL, marker="s")
        # En la columna de un canal el objetivo difiere solo en color; en la
        # de dos canales, en la combinación de color y forma.
        ax.scatter(puntos[objetivo, 0], puntos[objetivo, 1], s=45, color=MAGENTA,
                   marker="o" if columna == 0 else "s", zorder=5)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        if fila == 0:
            ax.set_title("Un canal" if columna == 0 else "Dos canales combinados", fontsize=9)
        if columna == 0:
            ax.set_ylabel(f"{n} marcas", fontsize=8)

fig.savefig(DIR_IMAGENES / "04-saliencia-local.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-saliencia-local.png")

# %%
# Ley de Weber. Lo que se discrimina es la razón entre dos magnitudes, no su
# diferencia absoluta: la misma diferencia se nota sobre una base chica y
# desaparece sobre una grande.

PARES = [(10, 12), (100, 102)]

fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.4))
for ax, (a, b) in zip(axes, PARES):
    ax.bar(["A", "B"], [a, b], color=[AZUL, MAGENTA], width=0.55)
    ax.set_title(f"{a} y {b}", fontsize=9)
    ax.set_ylim(0, max(b * 1.2, 14))
    ax.set_yticks([])

fig.savefig(DIR_IMAGENES / "04-weber.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-weber.png")
print(f"  Diferencia absoluta: {PARES[0][1] - PARES[0][0]} en los dos pares")
print(f"  Razón: {PARES[0][1] / PARES[0][0]:.2f} y {PARES[1][1] / PARES[1][0]:.2f}")

# %%
# La estructura de datos del glifo. El espacio angular se parte en doce
# sectores y la distancia en tres rangos, así que cada celda guarda una
# magnitud de flujo por modo de transporte.
# Adaptado de Perez-Messina, I. y Graells-Garrido, E. (2019). Visualizing
# Transportation Flows with Mode Split using Glyphs, figura 2.

MODOS_DIAGRAMA = {"Auto": "#E0A32E", "Bus": "#CF3889", "Metro": "#2E9E8F"}
RANGOS = ["Corta", "Media", "Larga"]
CELDA_SECTOR, CELDA_RANGO = 1, 1  # la celda que se abre para mostrar su contenido
SECTOR_EJEMPLO = 3               # el sector donde se dibuja el rayo resultante

fig, ax = plt.subplots(figsize=(6.2, 4.2), subplot_kw={"projection": "polar"})
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_ylim(0, 3)
ax.set_yticks([1, 2, 3])
ax.set_yticklabels([])
ax.set_xticks(np.radians(np.arange(0, 360, 30)))
ax.set_xticklabels([])
# La grilla queda tenue a propósito: es el espacio donde viven los datos, no
# algo que el glifo dibuje.
ax.grid(color="#D6D6DE", lw=0.5)
ax.spines["polar"].set_color("#D6D6DE")

ax.bar(
    np.radians(CELDA_SECTOR * 30), 1, width=np.radians(30), bottom=CELDA_RANGO,
    color="#F2F2F5", edgecolor=AZUL, linewidth=0.8, align="edge", zorder=2,
)

# La celda guarda tres números, uno por modo. Van como cifras y no como marcas:
# la codificación viene después.
EJEMPLO = {"Auto": 12, "Bus": 30, "Metro": 45}
for i, (modo, valor) in enumerate(EJEMPLO.items()):
    ax.text(np.radians(CELDA_SECTOR * 30 + 15), CELDA_RANGO + 0.78 - i * 0.26,
            str(valor), color=MODOS_DIAGRAMA[modo], fontsize=8, ha="center",
            va="center", zorder=5, fontweight="bold")

ax.annotate(
    "Cada celda guarda una magnitud\npor modo de transporte",
    xy=(np.radians(CELDA_SECTOR * 30 + 30), CELDA_RANGO + 0.85),
    xytext=(46, 24), textcoords="offset points", fontsize=7.5, color=AZUL,
    arrowprops=dict(arrowstyle="->", color=AZUL, lw=0.7),
)

# El glifo no pinta las celdas: convierte el total de cada una en el largo de
# un segmento y su modo predominante en el color. Este rayo lo muestra.
LARGOS = [0.55, 1.0, 0.75]          # totales de las tres celdas de ese sector
PREDOMINANTE = ["Metro", "Bus", "Metro"]
base = 0.0
for largo, modo in zip(LARGOS, PREDOMINANTE):
    ax.bar(np.radians(SECTOR_EJEMPLO * 30 + 15), largo, width=np.radians(22),
           bottom=base, color=MODOS_DIAGRAMA[modo], edgecolor="white",
           linewidth=0.6, zorder=4)
    base += largo

ax.annotate(
    "El glifo no pinta las celdas:\nlas convierte en largo y color",
    xy=(np.radians(SECTOR_EJEMPLO * 30 + 15), base * 0.75),
    xytext=(30, -46), textcoords="offset points", fontsize=7.5, color=AZUL,
    arrowprops=dict(arrowstyle="->", color=AZUL, lw=0.7),
)

arco = np.radians(np.linspace(150, 200, 40))
ax.plot(arco, np.full_like(arco, 3.3), color=AZUL, lw=0.9, clip_on=False)
ax.annotate(
    "", xy=(np.radians(202), 3.3), xytext=(np.radians(198), 3.3),
    arrowprops=dict(arrowstyle="->", color=AZUL, lw=0.9), annotation_clip=False,
)
ax.text(np.radians(175), 4.0, "Dirección del viaje\nen doce sectores",
        fontsize=7.5, color=AZUL, ha="center", va="center")

for i, nombre in enumerate(RANGOS):
    ax.annotate(
        nombre,
        xy=(np.radians(270), i + 0.5),
        xytext=(-40, 26 - i * 22), textcoords="offset points",
        fontsize=7.5, color=AZUL, va="center", ha="right",
        arrowprops=dict(arrowstyle="-", color=AZUL, lw=0.6, shrinkA=2, shrinkB=2),
    )
ax.text(np.radians(270), 4.0, "Distancia", fontsize=7.5, color=AZUL,
        ha="center", va="center", fontweight="bold")

for punto, etiqueta in [(0, "N"), (90, "E"), (180, "S"), (270, "O")]:
    ax.text(np.radians(punto), 3.15, etiqueta, fontsize=7, color="#8E8EA3",
            ha="center", va="center")

for modo, color in MODOS_DIAGRAMA.items():
    ax.plot([], [], color=color, lw=6, label=modo)
ax.legend(loc="center left", bbox_to_anchor=(1.06, 0.12), fontsize=7, frameon=False,
          title="Modo", title_fontsize=7)

fig.savefig(DIR_IMAGENES / "04-glifo-estructura.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-glifo-estructura.png")

# %%
# Por qué la posición encabeza el ranking. Los mismos seis valores en seis
# canales, con la misma tarea: ordenarlos de mayor a menor. Con posición o con
# largo la respuesta se lee; con área, ángulo o luminosidad hay que estimar, y
# el orden deja de ser evidente.

VALORES = np.array([62, 45, 78, 30, 55, 38])
ETIQUETAS = list("ABCDEF")
xs = np.arange(len(VALORES))

fig, axes = plt.subplots(2, 3, figsize=(9, 4.4))
(pos_comun, pos_desalineada, largo), (area, angulo, luminosidad) = axes

pos_comun.scatter(VALORES, xs, color=AZUL, s=26)
pos_comun.set_xlim(0, 100)
pos_comun.set_title("Posición en escala común", fontsize=8.5)

for i, valor in enumerate(VALORES):
    corrimiento = (i % 3) * 18
    pos_desalineada.plot([corrimiento, corrimiento + 60], [i, i], color=GRIS, lw=0.8)
    pos_desalineada.scatter([corrimiento + valor * 0.6], [i], color=AZUL, s=26)
pos_desalineada.set_xlim(0, 100)
pos_desalineada.set_title("Posición en escala no alineada", fontsize=8.5)

largo.barh(xs, VALORES, color=AZUL, height=0.6)
largo.set_xlim(0, 100)
largo.set_title("Largo con base común", fontsize=8.5)

area.scatter(np.zeros(len(VALORES)), xs, s=VALORES / VALORES.max() * 420, color=AZUL)
area.set_xlim(-1, 1)
area.set_title("Área", fontsize=8.5)

# El sector se dibuja con Wedge y el eje va con aspecto igual: sin eso los
# quesitos se estiran con la caja y el ángulo deja de ser el ángulo.
for i, valor in enumerate(VALORES):
    angulo.add_patch(
        Wedge((0, i), 0.42, 90 - 360 * valor / 100, 90, facecolor=AZUL, lw=0)
    )
# El xlim ancho evita que el aspecto igual comprima la caja a una tira.
angulo.set_xlim(-2.8, 2.8)
angulo.set_ylim(-0.7, len(VALORES) - 0.3)
angulo.set_aspect("equal")
angulo.set_title("Ángulo", fontsize=8.5)

luminosidad.scatter(
    np.zeros(len(VALORES)), xs, s=150, marker="s",
    color=plt.cm.Greys(0.2 + 0.7 * VALORES / VALORES.max()),
)
luminosidad.set_xlim(-1, 1)
luminosidad.set_title("Luminosidad", fontsize=8.5)

for ax in axes.flatten():
    ax.set_yticks(xs)
    ax.set_yticklabels(ETIQUETAS, fontsize=7)
    ax.set_xticks([])
    ax.grid(False)

fig.savefig(DIR_IMAGENES / "04-por-que-posicion.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-por-que-posicion.png")
print("  Orden real, de mayor a menor: " + ", ".join(
    ETIQUETAS[i] for i in np.argsort(-VALORES)))

# %%
# El color tiene tres dimensiones y cada una sirve a un tipo de atributo
# distinto: el matiz identifica, la luminosidad y la saturación ordenan. Usar
# la dimensión equivocada inventa un orden o lo borra.

# En un heatmap el color es el único canal: no hay largo ni posición que
# ordenen por su cuenta, así que se ve qué dimensión del color sirve a qué
# atributo. Con barras el efecto se pierde, porque el largo ya ordena y el
# color queda redundante.

rng_color = np.random.default_rng(7)
FILAS, COLUMNAS = 4, 6
magnitud = rng_color.uniform(0, 1, (FILAS, COLUMNAS))
desviacion = rng_color.uniform(-1, 1, (FILAS, COLUMNAS))
categoria = rng_color.integers(0, 5, (FILAS, COLUMNAS))

fig, axes = plt.subplots(2, 2, figsize=(7.4, 4.0))
PANELES = [
    (axes[0, 0], categoria, "tab10", "Matiz para categorías", (0, 9)),
    (axes[0, 1], magnitud, "Blues", "Luminosidad para magnitud", (0, 1)),
    (axes[1, 0], desviacion, "PuOr", "Divergente para desviaciones", (-1, 1)),
    (axes[1, 1], magnitud, "rainbow", "Matiz para magnitud", (0, 1)),
]
for ax, datos, mapa, titulo, (vmin, vmax) in PANELES:
    ax.imshow(datos, cmap=mapa, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_title(titulo, fontsize=8.5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)

# La celda mayor se marca en los dos paneles de magnitud: en uno se encuentra
# sin ayuda y en el otro hay que buscarla contra la leyenda.
fila_max, col_max = np.unravel_index(magnitud.argmax(), magnitud.shape)
for ax in (axes[0, 1], axes[1, 1]):
    ax.add_patch(
        Rectangle((col_max - 0.5, fila_max - 0.5), 1, 1, facecolor="none",
                  edgecolor=AZUL, lw=1.6)
    )

fig.savefig(DIR_IMAGENES / "04-color-usos.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-color-usos.png")
print(f"  La celda marcada es el máximo: fila {fila_max + 1}, columna {col_max + 1}")

# %%
# Dos ejemplos con los siniestros de la Región Metropolitana. Se bajan acá
# porque son los mismos datos de la sesión de código, y así las cifras de las
# slides se pueden verificar.
import geopandas as gpd  # noqa: E402

from visutils.general import descargar_datos  # noqa: E402

siniestros = gpd.read_parquet(
    descargar_datos("siniestros.tgz") / "siniestros-rm.parquet"
)

# %%
# El orden de las categorías. Con una llave categórica el orden en el eje es
# una decisión libre, y cada orden responde una pregunta distinta: alfabético
# para buscar una comuna conocida, por valor para leer el ranking.

por_comuna = siniestros["comuna"].value_counts().nlargest(10)
alfabetico = por_comuna.sort_index(ascending=False)
por_valor = por_comuna.sort_values()

fig, axes = plt.subplots(1, 2, figsize=(8.4, 2.8), sharex=True)
alfabetico.plot(kind="barh", color=GRIS, ax=axes[0])
axes[0].set_title("Orden alfabético", fontsize=9)
por_valor.plot(kind="barh", color=MAGENTA, ax=axes[1])
axes[1].set_title("Orden por valor", fontsize=9)

for ax in axes:
    ax.set_ylabel("")
    ax.set_xlabel("Siniestros, 2019 a 2023")
    ax.tick_params(axis="y", labelsize=7)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:,.0f}".replace(",", "."))

fig.savefig(DIR_IMAGENES / "04-orden-categorias.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-orden-categorias.png")
print(f"  La comuna con más siniestros es {por_valor.index[-1]} con {por_valor.iloc[-1]:,}")

# %%
# Sobreposición. Cuando las marcas se tapan entre sí, el gráfico deja de
# responder: la densidad se satura y una zona con mil casos se ve igual que una
# con diez mil. Hay tres salidas habituales, y todas cambian la codificación.

puntos = siniestros.to_crs(32719)
coords = np.column_stack([puntos.geometry.x, puntos.geometry.y])
muestra_chica = coords[np.random.default_rng(1).choice(len(coords), 200, replace=False)]

fig, axes = plt.subplots(1, 4, figsize=(10, 2.8))
PANELES = [
    ("200 marcas", dict(s=6, alpha=1.0, color=AZUL), muestra_chica),
    ("97.648 marcas", dict(s=6, alpha=1.0, color=AZUL), coords),
    ("Opacidad y tamaño", dict(s=0.4, alpha=0.06, color=AZUL), coords),
]
for ax, (titulo, args, datos) in zip(axes, PANELES):
    ax.scatter(datos[:, 0], datos[:, 1], **args)
    ax.set_title(titulo, fontsize=8.5)

axes[3].hexbin(coords[:, 0], coords[:, 1], gridsize=38, cmap="magma_r", mincnt=1)
axes[3].set_title("Agregadas en celdas", fontsize=8.5)

# Los cuatro paneles comparten encuadre: si cada uno se ajusta a sus datos, la
# comparación deja de ser entre codificaciones y pasa a ser entre escalas.
limites_x = (coords[:, 0].min(), coords[:, 0].max())
limites_y = (coords[:, 1].min(), coords[:, 1].max())
for ax in axes:
    ax.set_xlim(*limites_x)
    ax.set_ylim(*limites_y)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
    ax.grid(False)

fig.savefig(DIR_IMAGENES / "04-sobreposicion.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/04-sobreposicion.png")
