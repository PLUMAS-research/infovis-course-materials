"""Figuras de la unidad 06: análisis exploratorio.

Dos figuras. La primera mapea las cuatro preguntas del análisis exploratorio a
las columnas de una tabla, que es la forma de decidir cuáles se pueden
responder con un dataset dado. La segunda muestra en qué se gasta el tiempo de
un proyecto de datos.

Se ejecuta desde la raíz del repositorio:

    uv run python figuras/06-analisis-exploratorio.py
"""

import matplotlib.pyplot as plt
import numpy as np
from chiricoca.base.paths import add_project_root
from matplotlib.patches import Rectangle

add_project_root(marker="pyproject.toml")

from visutils.diagramas import flecha, llave, rotulo  # noqa: E402
from visutils.estilo import AZUL, DPI, GRIS, MAGENTA, estilo_curso  # noqa: E402

estilo_curso()

# %%
# Las cuatro preguntas sobre las columnas de una tabla.

COLUMNAS = ["fecha", "comuna", "categoría", "valor 1", "valor 2"]
FILAS = 5

ANCHO_COL = 14.0
SEPARACION_COL = 1.4
ALTO_FILA = 3.4
SEPARACION_FILA = 0.7
X_TABLA = 3.0
Y_TABLA = 15.0

centros = [
    X_TABLA + i * (ANCHO_COL + SEPARACION_COL) + ANCHO_COL / 2 for i in range(len(COLUMNAS))
]
bordes = [
    (X_TABLA + i * (ANCHO_COL + SEPARACION_COL),
     X_TABLA + i * (ANCHO_COL + SEPARACION_COL) + ANCHO_COL)
    for i in range(len(COLUMNAS))
]
alto_tabla = FILAS * ALTO_FILA + (FILAS - 1) * SEPARACION_FILA
y_arriba = Y_TABLA + alto_tabla

fig, ax = plt.subplots(figsize=(7, 3.9))

for i, columna in enumerate(COLUMNAS):
    for j in range(FILAS):
        ax.add_patch(
            Rectangle(
                (bordes[i][0], Y_TABLA + j * (ALTO_FILA + SEPARACION_FILA)),
                ANCHO_COL,
                ALTO_FILA,
                facecolor=GRIS,
                lw=0,
            )
        )
    rotulo(ax, centros[i], y_arriba + 2.2, columna, size=8)

# Arriba de la tabla: las dos preguntas que dependen de que exista la columna.
llave(ax, *bordes[0], y_arriba + 6.0, alto=-1.4)
rotulo(ax, centros[0], y_arriba + 8.0, "¿Cuándo?", size=9, weight="bold")

llave(ax, *bordes[1], y_arriba + 6.0, alto=-1.4, color=MAGENTA)
rotulo(ax, centros[1], y_arriba + 8.0, "¿Dónde?", size=9, weight="bold", color=MAGENTA)
rotulo(
    ax, centros[1], y_arriba + 11.0, "datos geográficos", size=6, color=MAGENTA, style="italic"
)

# Abajo: la pregunta que se le hace a cada columna por separado, y la que
# necesita dos columnas a la vez.
llave(ax, bordes[0][0], bordes[-1][1], Y_TABLA - 4.0, alto=1.4)
rotulo(ax, (bordes[0][0] + bordes[-1][1]) / 2, Y_TABLA - 6.2, "¿Qué?", size=9, weight="bold")
rotulo(
    ax,
    (bordes[0][0] + bordes[-1][1]) / 2,
    Y_TABLA - 9.0,
    "la distribución de cada variable, una por una",
    size=7,
)

llave(ax, bordes[-2][0], bordes[-1][1], Y_TABLA - 14.0, alto=1.4)
rotulo(ax, (bordes[-2][0] + bordes[-1][1]) / 2, Y_TABLA - 16.2, "¿Cómo?", size=9, weight="bold")
rotulo(
    ax,
    (bordes[-2][0] + bordes[-1][1]) / 2,
    Y_TABLA - 19.0,
    "la relación entre dos variables",
    size=7,
)

# A la derecha: la pregunta cuya respuesta no está en ninguna columna.
x_fuera = bordes[-1][1] + 4.0
flecha(ax, (bordes[-1][1] + 1.0, Y_TABLA + alto_tabla / 2), (x_fuera + 3.0, Y_TABLA + alto_tabla / 2))
rotulo(ax, x_fuera + 5.0, Y_TABLA + alto_tabla / 2 + 3.0, "¿Por qué?", size=9,
       weight="bold", ha="left")
rotulo(ax, x_fuera + 5.0, Y_TABLA + alto_tabla / 2 - 1.0, "la respuesta viene\nde fuera de la tabla",
       size=7, ha="left", va="top")

ax.set_xlim(0, 118)
ax.set_ylim(Y_TABLA - 22, y_arriba + 14)
ax.set_aspect("equal")
ax.set_axis_off()

fig.savefig("images/06-preguntas-tabla.png", dpi=DPI, bbox_inches="tight")

# %%
# En qué se gasta el tiempo de un proyecto de datos.

TAREAS = {
    "Limpiar y organizar datos": 60,
    "Recolectar los datos": 19,
    "Buscar patrones": 9,
    "Otras tareas": 5,
    "Refinar algoritmos": 4,
    "Construir datos de entrenamiento": 3,
}

fig, ax = plt.subplots(figsize=(6.4, 1.4))

colores = plt.get_cmap("viridis")(
    [0.15 + 0.75 * i / (len(TAREAS) - 1) for i in range(len(TAREAS))]
)

# Los cuatro segmentos angostos no admiten rótulo adentro ni encima, así que
# los seis van a la leyenda con su porcentaje.
izquierda = 0
for (tarea, valor), color in zip(TAREAS.items(), colores):
    ax.barh(0, valor, left=izquierda, color=color, edgecolor="white", linewidth=0.8,
            label=f"{tarea}, {valor}%")
    if valor >= 15:
        ax.text(izquierda + valor / 2, 0, f"{valor}%", ha="center", va="center",
                fontsize=8, color="white")
    izquierda += valor

ax.set_xlim(0, 100)
ax.set_ylim(-0.45, 0.45)
ax.set_yticks([])
ax.set_xlabel("% del tiempo de trabajo")
ax.spines[["left", "right", "top"]].set_visible(False)
ax.legend(fontsize=6, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)

fig.savefig("images/06-tiempo-de-preparacion.png", dpi=DPI, bbox_inches="tight")

# %%
print("Figuras escritas en images/:")
print("  06-preguntas-tabla.png")
print("  06-tiempo-de-preparacion.png")

# %%
# La paradoja de Simpson: la relación global entre dos variables se invierte al
# mirar dentro de cada grupo. Los datos son construidos, para que el mecanismo
# quede a la vista.

GRUPOS_SIMPSON = 3
POR_GRUPO = 40
CENTROS_X = [2.0, 5.0, 8.0]
CENTROS_Y = [3.0, 6.0, 9.0]
PENDIENTE_INTERNA = -0.8
COLORES_GRUPO = [AZUL, "#2E9E8F", "#E08D2F"]

rng = np.random.default_rng(7)

x = np.concatenate([rng.normal(c, 0.8, POR_GRUPO) for c in CENTROS_X])
grupo = np.repeat(np.arange(GRUPOS_SIMPSON), POR_GRUPO)
y = np.concatenate([
    CENTROS_Y[k] + PENDIENTE_INTERNA * (x[grupo == k] - CENTROS_X[k])
    + rng.normal(0, 0.5, POR_GRUPO)
    for k in range(GRUPOS_SIMPSON)
])


def recta(ax, xs, ys, color, estilo="-", ancho=1.4):
    """Ajusta una recta por mínimos cuadrados y la dibuja sobre su propio rango."""
    pendiente, corte = np.polyfit(xs, ys, 1)
    borde = np.array([xs.min(), xs.max()])
    ax.plot(borde, pendiente * borde + corte, color=color, linestyle=estilo, linewidth=ancho)
    return pendiente


fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.9), sharex=True, sharey=True)

axes[0].scatter(x, y, s=8, color="#9A9AA8", linewidth=0)
pendiente_global = recta(axes[0], x, y, MAGENTA, ancho=1.8)
# el separador decimal en castellano es la coma
axes[0].set_title(
    f"Sin agrupar, pendiente {pendiente_global:+.2f}".replace(".", ","), fontsize=9
)

for k in range(GRUPOS_SIMPSON):
    dentro = grupo == k
    axes[1].scatter(x[dentro], y[dentro], s=8, color=COLORES_GRUPO[k], linewidth=0,
                    label=f"Grupo {k + 1}")
    recta(axes[1], x[dentro], y[dentro], COLORES_GRUPO[k])

recta(axes[1], x, y, MAGENTA, estilo="dotted", ancho=1.2)
axes[1].set_title("Por grupo, las tres pendientes son negativas", fontsize=9)
axes[1].legend(fontsize=6, loc="upper left")

for ax in axes:
    ax.set_xlabel("Variable x")
axes[0].set_ylabel("Variable y")

fig.savefig("images/06-simpson.png", dpi=DPI, bbox_inches="tight")

print("  06-simpson.png")
