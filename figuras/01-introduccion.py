"""Figuras de la unidad 01.

Construye las demostraciones de la clase de introducción: el cuarteto de
Anscombe, donde cuatro conjuntos con los mismos descriptivos se ven distintos;
una búsqueda visual que compara un canal preatentivo con la combinación de dos
canales; el diagrama de los cuatro tipos de dataset; y el plano que decide
cuándo conviene diseñar una visualización y cuándo automatizar.

Uso: uv run python figuras/01-introduccion.py
"""

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from chiricoca.base.paths import add_project_root
from matplotlib.patches import Circle, Ellipse, Polygon, Rectangle

# Este script vive en una subcarpeta, así que hay que agregar la raíz del
# repositorio al path para poder importar visutils.
add_project_root(marker="pyproject.toml")

from visutils.diagramas import caja, celda, encabezado, flecha, rotulo, titulo  # noqa: E402
from visutils.estilo import AZUL, GRIS, MAGENTA, estilo_curso  # noqa: E402

# dpi alto con figuras chicas: el texto queda grande y nítido al proyectar.
estilo_curso(dpi=300)

DIR_IMAGENES = Path("images")
DIR_IMAGENES.mkdir(exist_ok=True)

# %%
# Cuarteto de Anscombe (1973). Cuatro conjuntos con la misma media, varianza,
# correlación y recta de regresión.
X_COMUN = [10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5]

ANSCOMBE = {
    "I": (X_COMUN, [8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68]),
    "II": (X_COMUN, [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74]),
    "III": (X_COMUN, [7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39, 8.15, 6.42, 5.73]),
    "IV": (
        [8, 8, 8, 8, 8, 8, 8, 19, 8, 8, 8],
        [6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.50, 5.56, 7.91, 6.89],
    ),
}

print("Descriptivos de los cuatro conjuntos:")
for etiqueta, (x, y) in ANSCOMBE.items():
    x, y = np.array(x), np.array(y)
    print(
        f"  {etiqueta:4s} media x={x.mean():.2f} media y={y.mean():.2f} "
        f"desv y={y.std(ddof=1):.2f} correlacion={np.corrcoef(x, y)[0, 1]:.2f}"
    )

fig, axes = plt.subplots(1, 4, figsize=(7.5, 2.1), sharex=True, sharey=True)

for ax, (etiqueta, (x, y)) in zip(axes, ANSCOMBE.items()):
    ax.scatter(x, y, color=AZUL, s=18, zorder=3)
    pendiente, intercepto = np.polyfit(x, y, 1)
    linea_x = np.array([3, 20])
    ax.plot(linea_x, pendiente * linea_x + intercepto, color=MAGENTA, linewidth=1)
    ax.set_title(f"Conjunto {etiqueta}", fontsize=9)
    ax.set_xlim(2, 21)
    ax.set_ylim(2, 14)

axes[0].set_ylabel("y")
for ax in axes:
    ax.set_xlabel("x")

fig.savefig(DIR_IMAGENES / "01-anscombe.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("\nEscrito: images/01-anscombe.png")

# %%
# Búsqueda visual. El objetivo es siempre el mismo, un círculo magenta, y lo
# que cambia es qué lo separa de los distractores. En los dos primeros paneles
# lo separa un solo canal (color, y después forma), y ambos se procesan en
# paralelo. En el tercero cada distractor comparte uno de los dos canales con
# el objetivo y ninguno comparte los dos, así que hay que revisarlos de a uno.
rng = np.random.default_rng(20)

FILAS, COLUMNAS = 9, 9
xs, ys = np.meshgrid(np.arange(COLUMNAS), np.arange(FILAS))
puntos = pd.DataFrame({"x": xs.ravel(), "y": ys.ravel()}).astype(float)
# El jitter rompe la regularidad de la grilla sin que los elementos se tapen.
puntos += rng.uniform(-0.3, 0.3, puntos.shape)

# El objetivo ocupa una posición distinta en cada panel: si estuviera en la
# misma, quien lo encuentra en el primero ya sabe dónde mirar en los otros.
OBJETIVOS = [70, 30, 48]

fig, axes = plt.subplots(1, 3, figsize=(7.6, 2.4))

# Panel 1: los distractores solo se diferencian del objetivo en el color.
distractores = puntos.drop(index=OBJETIVOS[0])
axes[0].scatter(distractores["x"], distractores["y"], marker="o", color=AZUL, s=32)
axes[0].set_title("Difiere en color", fontsize=9)

# Panel 2: los distractores solo se diferencian del objetivo en la forma.
distractores = puntos.drop(index=OBJETIVOS[1])
axes[1].scatter(distractores["x"], distractores["y"], marker="s", color=MAGENTA, s=32)
axes[1].set_title("Difiere en forma", fontsize=9)

# Panel 3: mitad círculos azules, mitad cuadrados magenta, repartidos al azar
# por la grilla. Cada distractor comparte un canal con el objetivo.
distractores = puntos.drop(index=OBJETIVOS[2])
orden = rng.permutation(len(distractores))
mitad = len(distractores) // 2
circulos = distractores.iloc[orden[:mitad]]
cuadrados = distractores.iloc[orden[mitad:]]

axes[2].scatter(circulos["x"], circulos["y"], marker="o", color=AZUL, s=32)
axes[2].scatter(cuadrados["x"], cuadrados["y"], marker="s", color=MAGENTA, s=32)
axes[2].set_title("Difiere en la combinación de ambos", fontsize=9)

for ax, objetivo in zip(axes, OBJETIVOS):
    ax.scatter(
        puntos.loc[objetivo, "x"],
        puntos.loc[objetivo, "y"],
        marker="o",
        color=MAGENTA,
        s=32,
        zorder=5,
    )
    ax.set_xlim(-1, COLUMNAS)
    ax.set_ylim(-1, FILAS)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)

fig.savefig(DIR_IMAGENES / "01-preatentivo.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/01-preatentivo.png")

for etiqueta, objetivo in zip(["color", "forma", "combinación"], OBJETIVOS):
    x, y = puntos.loc[objetivo, "x"], puntos.loc[objetivo, "y"]
    print(f"Objetivo del panel '{etiqueta}': fila {y:.1f}, columna {x:.1f} de la grilla")

# %%
# Los cuatro tipos de dataset: tablas, redes, campos y geometría. Cada tipo se
# dibuja con su vocabulario propio (ítem, atributo, celda, nodo, enlace,
# posición), que es el que usamos durante el resto del curso.
# Adaptado de Munzner, T. (2014). Visualization Analysis and Design, figura 2.1.

ANCHO = 100.0
# Los límites verticales encierran el contenido, sin margen muerto arriba ni
# abajo, y el figsize sigue esa proporción para que el aspect equal no acolche.
ABAJO, ARRIBA = 5.0, 45.4
COLUMNAS = {"tablas": 6.0, "redes": 30.0, "campos": 52.0, "geometria": 76.5}
ANCHO_FIG = 7.6  # figura chica: al escalarla en la lámina el texto queda grande

fig, ax = plt.subplots(figsize=(ANCHO_FIG, ANCHO_FIG * (ARRIBA - ABAJO) / ANCHO))
ax.set_xlim(0, ANCHO)
ax.set_ylim(ABAJO, ARRIBA)
ax.set_aspect("equal")
ax.set_axis_off()

encabezado(ax, 2.4, 43.2, "Tipos de dataset")

for clave, texto, parentesis in [
    ("tablas", "Tablas", None),
    ("redes", "Redes", None),
    ("campos", "Campos", "(continuos)"),
    ("geometria", "Geometría", "(espacial)"),
]:
    titulo(ax, fig, COLUMNAS[clave], 39.0, texto, parentesis)

# --- Tablas: una grilla de celdas, con ítems en las filas y atributos en las
# columnas. La celda destacada es el valor de un atributo para un ítem.
X0, Y0, ANCHO_C, ALTO_C, HUECO = 6.0, 33.6, 2.3, 1.9, 0.35
N_COLS, N_FILAS = 5, 4
for i in range(N_COLS):
    for j in range(N_FILAS):
        celda(
            ax,
            X0 + i * (ANCHO_C + HUECO),
            Y0 - (j + 1) * ALTO_C - j * HUECO,
            ANCHO_C,
            ALTO_C,
            destacada=(i, j) == (2, 1),
        )

x_fin = X0 + N_COLS * ANCHO_C + (N_COLS - 1) * HUECO
y_fin = Y0 - N_FILAS * ALTO_C - (N_FILAS - 1) * HUECO
flecha(ax, (X0, Y0 + 1.3), (x_fin, Y0 + 1.3))
rotulo(ax, (X0 + x_fin) / 2, Y0 + 2.3, "Atributos (columnas)")
flecha(ax, (X0 - 1.3, Y0), (X0 - 1.3, y_fin))
rotulo(ax, X0 - 2.2, (Y0 + y_fin) / 2, "Ítems\n(filas)", ha="right")

x_destacada = X0 + 2 * (ANCHO_C + HUECO) + ANCHO_C / 2
y_destacada = Y0 - 2 * ALTO_C - HUECO
ax.plot([x_destacada, x_destacada], [y_destacada, y_fin - 1.6], color=AZUL, lw=0.7)
rotulo(ax, x_destacada, y_fin - 2.5, "Celda con un valor", va="top")

# --- Tabla multidimensional: el mismo contenido indexado por más de una llave.
titulo(ax, fig, COLUMNAS["tablas"] + 1.6, 17.2, "Tabla multidimensional", size=8, italica=True)

CX, CY, LADO, N_CUBO = 8.4, 8.2, 1.35, 4
PROF = np.array([0.62, 0.42])  # dirección de la profundidad en la proyección


def cara(ax, origen, paso_u, paso_v, destacada=None):
    for u in range(N_CUBO):
        for v in range(N_CUBO):
            esquina = origen + u * paso_u + v * paso_v
            puntos = [esquina, esquina + paso_u, esquina + paso_u + paso_v, esquina + paso_v]
            ax.add_patch(
                Polygon(
                    puntos,
                    facecolor=MAGENTA if (u, v) == destacada else GRIS,
                    edgecolor="white",
                    lw=0.8,
                )
            )


base = np.array([CX, CY])
paso_x = np.array([LADO, 0.0])
paso_y = np.array([0.0, LADO])
paso_z = PROF * LADO
cara(ax, base, paso_x, paso_y, destacada=(1, 1))  # frente
cara(ax, base + N_CUBO * paso_y, paso_x, paso_z)  # tapa
cara(ax, base + N_CUBO * paso_x, paso_z, paso_y)  # costado

alto_cubo = N_CUBO * LADO
flecha(ax, (CX - 0.6, CY + alto_cubo + 0.6), (CX - 0.6 + 3 * paso_z[0], CY + alto_cubo + 0.6 + 3 * paso_z[1]))
rotulo(ax, CX - 1.0, CY + alto_cubo + 1.6, "Llave 1", ha="right")
flecha(ax, (CX - 0.9, CY + alto_cubo), (CX - 0.9, CY))
rotulo(ax, CX - 1.6, CY + alto_cubo / 2, "Llave 2", ha="right")
flecha(ax, (CX, CY - 0.9), (CX + alto_cubo, CY - 0.9))
rotulo(ax, CX + alto_cubo / 2, CY - 1.9, "Atributos")

x_valor, y_valor = CX + 1.5 * LADO, CY + 1.5 * LADO
ax.plot([x_valor, CX + alto_cubo + 2.4], [y_valor, y_valor - 1.4], color=AZUL, lw=0.7)
rotulo(ax, CX + alto_cubo + 2.8, y_valor - 1.4, "Valor en la celda", ha="left")

# --- Redes: ítems que son nodos, más los enlaces que los relacionan.
NODOS = np.array([
    [1.4, 8.4], [3.7, 9.6], [4.8, 7.5], [2.3, 6.1], [0.5, 4.5], [5.7, 5.2],
    [7.7, 6.5], [4.4, 3.1], [6.3, 1.9], [2.9, 1.2], [8.6, 3.8],
]) + np.array([29.8, 24.2])
ENLACES = [(0, 1), (1, 2), (2, 3), (3, 0), (2, 5), (5, 6), (3, 4), (5, 7),
           (7, 8), (7, 9), (6, 10), (8, 10), (2, 6)]
for a, b in ENLACES:
    ax.plot(*zip(NODOS[a], NODOS[b]), color=AZUL, lw=0.8, zorder=1)
ax.scatter(NODOS[:, 0], NODOS[:, 1], s=42, color=MAGENTA, zorder=2)

# Los rótulos apuntan al medio de un enlace largo y a un nodo del borde, para
# que la punta de la flecha no quede ambigua entre los dos elementos.
medio = (NODOS[2] + NODOS[6]) / 2
flecha(ax, (43.0, medio[1] + 3.2), medio + np.array([0.4, 0.2]))
rotulo(ax, 43.4, medio[1] + 3.4, "Enlace", ha="left")
flecha(ax, (43.0, NODOS[10][1] - 0.8), NODOS[10] + np.array([0.7, 0.0]))
rotulo(ax, 43.4, NODOS[10][1] - 1.0, "Nodo\n(ítem)", ha="left", va="top")

# --- Árboles: una red con jerarquía, un caso particular de red.
titulo(ax, fig, COLUMNAS["redes"] + 1.6, 17.2, "Árboles", size=8, italica=True)

RAIZ = np.array([35.0, 14.6])
HIJOS = np.array([[32.3, 12.1], [35.0, 12.1], [37.9, 12.1]])
HOJAS = np.array([[31.1, 9.6], [33.4, 9.6], [35.0, 9.6], [36.9, 9.6], [38.9, 9.6]])
RAMAS = [(RAIZ, h) for h in HIJOS] + [
    (HIJOS[0], HOJAS[0]), (HIJOS[0], HOJAS[1]), (HIJOS[1], HOJAS[2]),
    (HIJOS[2], HOJAS[3]), (HIJOS[2], HOJAS[4]),
]
for a, b in RAMAS:
    ax.plot(*zip(a, b), color=AZUL, lw=0.8, zorder=1)
puntos = np.vstack([RAIZ, HIJOS, HOJAS])
ax.scatter(puntos[:, 0], puntos[:, 1], s=42, color=MAGENTA, zorder=2)

# --- Campos continuos: las celdas están en una grilla de posiciones, y cada
# celda guarda los atributos medidos en ese punto del espacio.
rotulo(ax, 61.0, 35.6, "Grilla de posiciones", size=7.5)

ARCO_C = np.array([61.0, 23.8])
R0, R1, NR, NA = 5.4, 8.9, 3, 9
A0, A1 = np.radians(25), np.radians(155)
for i in range(NR):
    for j in range(NA):
        ri = R0 + i * (R1 - R0) / NR
        ro = R0 + (i + 1) * (R1 - R0) / NR
        t = np.linspace(A0 + j * (A1 - A0) / NA, A0 + (j + 1) * (A1 - A0) / NA, 10)
        contorno = np.vstack([
            ARCO_C + ro * np.column_stack([np.cos(t), np.sin(t)]),
            ARCO_C + ri * np.column_stack([np.cos(t[::-1]), np.sin(t[::-1])]),
        ])
        ax.add_patch(
            Polygon(
                contorno,
                facecolor=MAGENTA if (i, j) == (NR - 1, NA - 1) else GRIS,
                edgecolor="white",
                lw=0.9,
            )
        )

angulo_celda = (A1 - (A1 - A0) / NA / 2)
centro_celda = ARCO_C + (R1 - (R1 - R0) / NR / 2) * np.array(
    [np.cos(angulo_celda), np.sin(angulo_celda)]
)
flecha(ax, (49.6, centro_celda[1] + 1.0), centro_celda + np.array([-1.0, 0.4]))
rotulo(ax, 49.2, centro_celda[1] + 1.2, "Celda", ha="right")

TIRA_X, TIRA_Y, TIRA_W, TIRA_H, TIRA_N = 55.0, 19.4, 1.9, 1.6, 8
flecha(ax, (TIRA_X - 1.2, 26.0), (TIRA_X - 1.2, TIRA_Y + 3.6), lw=1.0)
for i in range(TIRA_N):
    celda(ax, TIRA_X + i * (TIRA_W + 0.28), TIRA_Y, TIRA_W, TIRA_H, destacada=i == 4)

tira_fin = TIRA_X + TIRA_N * TIRA_W + (TIRA_N - 1) * 0.28
flecha(ax, (TIRA_X, TIRA_Y + 2.2), (tira_fin, TIRA_Y + 2.2))
rotulo(ax, (TIRA_X + tira_fin) / 2, TIRA_Y + 3.1, "Atributos (columnas)")

x_tira = TIRA_X + 4 * (TIRA_W + 0.28) + TIRA_W / 2
ax.plot([x_tira, x_tira], [TIRA_Y, TIRA_Y - 1.2], color=AZUL, lw=0.7)
rotulo(ax, x_tira, TIRA_Y - 2.0, "Valor en la celda", va="top")

# --- Geometría: la forma misma es el dato. El contorno se genera con ruido de
# baja frecuencia sobre un círculo, así queda una costa irregular reproducible.
rng_costa = np.random.default_rng(7)
theta = np.linspace(0, 2 * np.pi, 240)
radio = np.ones_like(theta)
for k in range(2, 8):
    radio += (0.16 / (k - 1)) * np.sin(k * theta + rng_costa.uniform(0, 2 * np.pi))
COSTA_C, COSTA_R = np.array([85.0, 27.0]), 6.4
costa = COSTA_C + COSTA_R * np.column_stack([radio * np.cos(theta), radio * np.sin(theta)])
ax.add_patch(Polygon(costa, facecolor="white", edgecolor=AZUL, lw=1.1, closed=True))

PUNTOS_GEO = COSTA_C + np.array([[-2.6, 2.4], [1.8, 3.2], [-3.4, -1.8],
                                 [0.6, -0.4], [2.6, -2.8], [-0.8, -3.6]])
ax.scatter(PUNTOS_GEO[:, 0], PUNTOS_GEO[:, 1], s=42, color=MAGENTA, zorder=3)
flecha(ax, (95.5, PUNTOS_GEO[1][1] + 0.2), PUNTOS_GEO[1] + np.array([0.7, 0.0]))
rotulo(ax, 95.9, PUNTOS_GEO[1][1] + 0.2, "Posición", ha="left")

fig.savefig(DIR_IMAGENES / "01-tipos-dataset.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/01-tipos-dataset.png")

# %%
# Cuándo conviene diseñar una visualización y cuándo automatizar. Los ejes son
# la claridad de la tarea y dónde está la información necesaria para resolverla.
# Si la tarea es precisa y todo lo que hace falta está en el computador, se
# escribe un algoritmo; si algo vive en la cabeza de las personas o la tarea es
# difusa, no hay especificación que automatizar.
# Adaptado de Sedlmair, M., Meyer, M. y Munzner, T. (2012). Design Study
# Methodology: Reflections from the Trenches and the Stacks. IEEE TVCG, 18(12),
# figura 1.

# Versiones claras de los colores del tema, para rellenar regiones sin que el
# texto encima pierda contraste.
AZUL_CLARO = "#E7E8F0"
MAGENTA_CLARO = "#F6DCEA"

ANCHO_P, ALTO_P = 100.0, 72.0
# Extremos de la caja de regiones, en coordenadas del plano.
IZQ, DER, ABAJO_P, ARRIBA_P = 21.0, 99.0, 5.0, 68.0
# La diagonal que separa la automatización nace arriba, al 38% del ancho de la
# caja, y llega al borde derecho a media altura.
DIAG_ARRIBA = IZQ + 0.38 * (DER - IZQ)
DIAG_DERECHA = ABAJO_P + 0.50 * (ARRIBA_P - ABAJO_P)
HUECO_DIAG = 1.4  # separación entre las dos regiones, medida en horizontal


def plano_decision(ax):
    """Ejes rotulados del plano, sin las regiones."""
    ax.set_xlim(-7, 103)
    ax.set_ylim(-9, 74)
    ax.set_aspect("equal")
    ax.set_axis_off()

    flecha(ax, (2.0, 1.0), (2.0, ARRIBA_P + 4.0), lw=1.4, escala=11)
    flecha(ax, (1.0, 2.0), (DER + 3.0, 2.0), lw=1.4, escala=11)

    rotulo(ax, -5.0, (ABAJO_P + ARRIBA_P) / 2, "Claridad de la tarea", size=10,
           weight="bold", rotation=90)
    rotulo(ax, 0.0, ARRIBA_P + 1.0, "precisa", size=9, rotation=90, va="top")
    rotulo(ax, 0.0, ABAJO_P + 1.0, "difusa", size=9, rotation=90, va="bottom")

    rotulo(ax, (IZQ + DER) / 2, -6.5, "Ubicación de la información", size=10, weight="bold")
    rotulo(ax, 4.0, -2.0, "cabeza", size=9, ha="left", va="top")
    rotulo(ax, DER, -2.0, "computador", size=9, ha="right", va="top")


def region(ax, vertices, color, borde=AZUL):
    ax.add_patch(Polygon(vertices, facecolor=color, edgecolor=borde, lw=1.1, zorder=1))


def regiones_decision(ax, diag_arriba, diag_derecha, centro_texto):
    """Las tres regiones del plano, según dónde caiga la diagonal.

    `diag_arriba` es el x en que la diagonal toca el borde superior y
    `diag_derecha` el y en que toca el borde derecho. Bajar cualquiera de los
    dos agranda la región automatizable.
    """
    # Franja izquierda: la información está en la cabeza de las personas, así
    # que todavía no hay datos que mirar.
    ax.add_patch(
        Rectangle((6.0, ABAJO_P), 11.0, ARRIBA_P - ABAJO_P, facecolor=GRIS, edgecolor=AZUL, lw=1.1)
    )
    rotulo(ax, 11.5, (ABAJO_P + ARRIBA_P) / 2, "No hay datos suficientes", size=8.5,
           rotation=90, style="italic")

    # Región central: hay datos y la tarea admite exploración, así que el
    # diseño de una visualización es la vía.
    region(ax, [
        (IZQ, ABAJO_P), (DER, ABAJO_P), (DER, diag_derecha - HUECO_DIAG),
        (diag_arriba - HUECO_DIAG, ARRIBA_P), (IZQ, ARRIBA_P),
    ], AZUL_CLARO)
    rotulo(ax, *centro_texto, "Conviene diseñar\nuna visualización", size=13, weight="bold")

    # Esquina superior derecha: tarea precisa y datos completos en el computador.
    region(ax, [
        (diag_arriba + HUECO_DIAG, ARRIBA_P), (DER, ARRIBA_P), (DER, diag_derecha + HUECO_DIAG),
    ], MAGENTA_CLARO)
    rotulo(ax, DER - 2.5, ARRIBA_P - 4.0, "Automatización\nposible", size=9.5,
           ha="right", va="top", style="italic")


FIGSIZE_P = (5.2, 5.2 * (74 + 9) / 110)

fig, ax = plt.subplots(figsize=FIGSIZE_P)
plano_decision(ax)
regiones_decision(ax, DIAG_ARRIBA, DIAG_DERECHA, (46.0, 34.0))

fig.savefig(DIR_IMAGENES / "01-cuando-visualizar.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/01-cuando-visualizar.png")

# %%
# La misma decisión con modelos de lenguaje de por medio. Un LLM acepta la
# especificación de la tarea en lenguaje natural, así que hay tareas difusas
# que antes no se podían automatizar y ahora sí. La frontera baja y se corre a
# la izquierda, y la región donde el diseño de una visualización es la vía se
# achica por arriba.
DIAG_ARRIBA_LLM = IZQ + 0.18 * (DER - IZQ)
DIAG_DERECHA_LLM = ABAJO_P + 0.22 * (ARRIBA_P - ABAJO_P)

fig, ax = plt.subplots(figsize=FIGSIZE_P)
plano_decision(ax)
regiones_decision(ax, DIAG_ARRIBA_LLM, DIAG_DERECHA_LLM, (44.0, 24.0))

# La frontera anterior queda punteada encima, para que se vea qué se movió.
ax.plot([DIAG_ARRIBA, DER], [ARRIBA_P, DIAG_DERECHA], color=AZUL, lw=1.1,
        linestyle=(0, (4, 3)), zorder=3)

pendiente = (DIAG_DERECHA - ARRIBA_P) / (DER - DIAG_ARRIBA)
angulo = np.degrees(np.arctan(pendiente))
rotulo(ax, 58.0, ARRIBA_P + pendiente * (58.0 - DIAG_ARRIBA) + 1.6, "frontera en 2012",
       size=8, rotation=angulo, rotation_mode="anchor", style="italic")

# Flecha vertical entre las dos fronteras: para una misma ubicación de la
# información, la tarea puede ser bastante más difusa y aun así automatizarse.
X_FLECHA = 66.0
y_antes = ARRIBA_P + pendiente * (X_FLECHA - DIAG_ARRIBA)
y_ahora = ARRIBA_P + (DIAG_DERECHA_LLM - ARRIBA_P) / (DER - DIAG_ARRIBA_LLM) * (
    X_FLECHA - DIAG_ARRIBA_LLM
)
flecha(ax, (X_FLECHA, y_antes - 1.5), (X_FLECHA, y_ahora + 1.5), lw=1.3, escala=10, color=MAGENTA)

fig.savefig(DIR_IMAGENES / "01-cuando-visualizar-llm.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/01-cuando-visualizar-llm.png")
print(
    f"Frontera 2012: toca arriba en x={DIAG_ARRIBA:.1f} y la derecha en y={DIAG_DERECHA:.1f}. "
    f"Frontera con LLM: x={DIAG_ARRIBA_LLM:.1f}, y={DIAG_DERECHA_LLM:.1f}"
)

# %%
# Las disciplinas que se cruzan en la ciencia de datos. El núcleo son tres
# componentes que ninguna disciplina aporta completa: los datos, el dominio del
# problema y la manera de pensarlo. Alrededor, las disciplinas que prestan
# métodos, cada una cubriendo parte del núcleo.
# Adaptado de Cao, L. (2017). Data science: challenges and directions.
# Communications of the ACM, 60(8).

# Ángulo en que se ubica cada disciplina, partiendo de arriba y girando en
# sentido horario, con el patrón de línea que la distingue de sus vecinas.
DISCIPLINAS = [
    ("Comunicación", 90, AZUL, (0, (6, 3))),
    ("Sociología", 30, MAGENTA, (0, (1, 2))),
    ("Computación", -30, AZUL, (0, (4, 2, 1, 2))),
    ("Estadística", -90, MAGENTA, (0, (6, 3))),
    ("Informática", -150, AZUL, (0, (1, 2))),
    ("Gestión", 150, MAGENTA, (0, (4, 2, 1, 2))),
]
SEMI_MAYOR, SEMI_MENOR = 1.30, 0.80
DESPLAZAMIENTO = 0.52  # cuánto se aleja del centro la elipse de cada disciplina

fig, ax = plt.subplots(figsize=(3.4, 3.1))
ax.set_xlim(-2.15, 2.15)
ax.set_ylim(-1.95, 1.95)
ax.set_aspect("equal")
ax.set_axis_off()

for nombre, grados, color, guion in DISCIPLINAS:
    rad = np.radians(grados)
    direccion = np.array([np.cos(rad), np.sin(rad)])
    ax.add_patch(
        Ellipse(
            DESPLAZAMIENTO * SEMI_MAYOR * direccion,
            2 * SEMI_MAYOR,
            2 * SEMI_MENOR,
            angle=grados,
            facecolor="none",
            edgecolor=color,
            lw=1.1,
            linestyle=guion,
        )
    )
    borde = (DESPLAZAMIENTO * SEMI_MAYOR + SEMI_MAYOR + 0.16) * direccion
    rotulo(ax, borde[0], borde[1], nombre, size=9, color=color)

# El núcleo: tres círculos que se solapan, con el nombre del campo encima.
NUCLEO = [("Datos", (-0.40, 0.28)), ("Dominio", (0.40, 0.28)), ("Pensamiento", (0.0, -0.44))]
for nombre, centro in NUCLEO:
    ax.add_patch(Circle(centro, 0.50, facecolor="white", edgecolor=AZUL, lw=1.2, zorder=2))
    rotulo(ax, *centro, nombre, size=8, zorder=4)

rotulo(ax, 0.0, -1.20, "Ciencia de datos", size=11, weight="bold", color=MAGENTA, zorder=5,
       bbox=dict(facecolor="white", edgecolor="none", pad=2.0))

fig.savefig(DIR_IMAGENES / "01-venn-ciencia-de-datos.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/01-venn-ciencia-de-datos.png")

# %%
# El camino de los datos hasta que alguien los entiende. Quien diseña decide el
# filtrado y la codificación; quien mira interpreta con su propio esquema
# notacional, que depende de su contexto. Por eso dos personas distintas no
# leen lo mismo en la misma representación.
# Adaptado de Dürsteler y Engelhardt, <http://infovis.net>.

fig, ax = plt.subplots(figsize=(7.0, 3.5))
ax.set_xlim(0, 100)
ax.set_ylim(0, 50)
ax.set_aspect("equal")
ax.set_axis_off()

Y_FLUJO = 20.0

# La cadena de transformaciones, de los datos a la comprensión.
caja(ax, 9, Y_FLUJO, 15, 8, "Datos", size=9, relleno=AZUL, color=AZUL, color_texto="white")
caja(ax, 35, Y_FLUJO, 17, 8, "Información", size=9)
caja(ax, 63, Y_FLUJO, 21, 8, "Representación\ngráfica", size=9)
caja(ax, 90, Y_FLUJO, 15, 8, "Comprensión", size=9, relleno=MAGENTA, color=MAGENTA,
     color_texto="white")

for x0, x1, texto in [
    (17, 26, "filtrado y\nprocesado"),
    (44, 52, "transformación\nvisual"),
    (74, 82, "percepción e\ninterpretación"),
]:
    flecha(ax, (x0, Y_FLUJO), (x1, Y_FLUJO), lw=1.2, escala=9)
    rotulo(ax, (x0 + x1) / 2, Y_FLUJO + 3.4, texto, size=7, va="bottom")

# Quien diseña interviene en las dos primeras transformaciones, y lo hace con
# un esquema notacional: el repertorio de convenciones gráficas que maneja.
caja(ax, 16, 40, 20, 8, "Quien diseña", size=9)
flecha(ax, (26, 40), (38, 40), lw=1.0, escala=8)
flecha(ax, (14, 36), (32, 24.5), lw=1.0, escala=8)

# El contexto y la cultura contienen los dos esquemas notacionales, el de quien
# diseña y el de quien mira: ninguno de los dos elige el repertorio de
# convenciones gráficas con el que trabaja.
ax.add_patch(
    Rectangle((36, 31), 63, 17, facecolor="none", edgecolor=MAGENTA, lw=1.1,
              linestyle=(0, (5, 3)))
)
rotulo(ax, 67.5, 45.4, "Contexto y cultura", size=8.5, color=MAGENTA)
caja(ax, 52, 37.6, 26, 7, "Esquema notacional\nde quien diseña", size=7.5)
caja(ax, 85, 37.6, 24, 7, "Esquema notacional\nde quien mira", size=7.5, color=MAGENTA)
flecha(ax, (54, 34), (60, 24.8), lw=1.0, escala=8)
flecha(ax, (86, 34), (90, 26), lw=1.0, escala=8, color=MAGENTA)

# La interacción devuelve el control sobre las dos etapas intermedias.
Y_RETORNO = 8.0
ax.plot([90, 90, 35], [16, Y_RETORNO, Y_RETORNO], color=GRIS, lw=1.4, zorder=1)
for x in (35, 63):
    flecha(ax, (x, Y_RETORNO), (x, 16), lw=1.4, escala=9, color=GRIS)
rotulo(ax, 62, Y_RETORNO - 2.4, "interacción y manipulación", size=7.5, va="top")

fig.savefig(DIR_IMAGENES / "01-pipeline-dursteler.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/01-pipeline-dursteler.png")
