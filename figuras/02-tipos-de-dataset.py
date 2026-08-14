"""Figuras de la unidad 02.

Construye el diagrama de los tipos de atributo, que es el vocabulario con el
que se describe cualquier columna de una tabla, y una demostración de las tres
direcciones de orden con datos concretos.

Uso: uv run python figuras/02-tipos-de-dataset.py
"""

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from chiricoca.base.paths import add_project_root
from matplotlib.patches import FancyArrowPatch, Polygon

# Este script vive en una subcarpeta, así que hay que agregar la raíz del
# repositorio al path para poder importar visutils.
add_project_root(marker="pyproject.toml")

from visutils.diagramas import encabezado, flecha, rotulo, titulo  # noqa: E402
from visutils.estilo import AZUL, MAGENTA, estilo_curso  # noqa: E402

# dpi alto con figuras chicas: el texto queda grande y nítido al proyectar.
estilo_curso(dpi=300)

DIR_IMAGENES = Path("images")
DIR_IMAGENES.mkdir(exist_ok=True)

# %%
# Tipos de atributo. Un atributo es categórico cuando solo admite comparar por
# igualdad, y ordenado cuando además admite comparar por magnitud. Dentro de
# los ordenados, el ordinal no admite aritmética y el cuantitativo sí. La
# dirección del orden es una propiedad aparte: dice hacia dónde crece.
# Adaptado de Munzner, T. (2014). Visualization Analysis and Design, figura 2.4.

ANCHO = 100.0
ABAJO, ARRIBA = 6.4, 48.0
ANCHO_FIG = 7.2

fig, ax = plt.subplots(figsize=(ANCHO_FIG, ANCHO_FIG * (ARRIBA - ABAJO) / ANCHO))
ax.set_xlim(0, ANCHO)
ax.set_ylim(ABAJO, ARRIBA)
ax.set_aspect("equal")
ax.set_axis_off()

rotulo(ax, ANCHO / 2, 45.6, "Atributos", size=13, weight="bold")
ax.plot([4, ANCHO - 4], [43.4, 43.4], color=MAGENTA, lw=1.2)

# --- Tipos de atributo ---
encabezado(ax, 3.4, 40.0, "Tipos de atributo", size=11)

titulo(ax, fig, 10.0, 35.6, "Categórico", size=10)
# Cuatro marcas distintas entre sí, sin ninguna relación de orden.
for x, marca in zip([12.0, 17.5, 23.0, 28.5], ["P", "o", "s", "^"]):
    if marca == "P":
        ax.plot(x, 31.0, marker="P", color=AZUL, markersize=9)
    else:
        ax.plot(x, 31.0, marker=marca, color=AZUL, markersize=8)

titulo(ax, fig, 48.0, 35.6, "Ordenado", size=10)

titulo(ax, fig, 52.0, 31.4, "Ordinal", size=8, italica=True)


def polera(ax, x, y, escala):
    """Polera de talla creciente: hay orden, pero no aritmética entre tallas."""
    cuerpo = np.array(
        [
            (-1.0, 1.0), (-1.8, 0.6), (-1.8, -0.1), (-1.1, -0.1),
            (-1.1, -1.4), (1.1, -1.4), (1.1, -0.1), (1.8, -0.1),
            (1.8, 0.6), (1.0, 1.0), (0.5, 1.0), (-0.5, 1.0),
        ]
    )
    ax.add_patch(Polygon(cuerpo * escala + np.array([x, y]), facecolor=AZUL, lw=0))


for x, escala in zip([54.0, 58.5, 64.0], [0.9, 1.2, 1.6]):
    polera(ax, x, 27.4, escala)

titulo(ax, fig, 76.0, 31.4, "Cuantitativo", size=8, italica=True)
# Barras con topes: lo que importa es que las longitudes se pueden restar.
for i, largo in enumerate([5.0, 9.5, 14.5]):
    y = 28.8 - i * 2.0
    ax.plot([78.0, 78.0 + largo], [y, y], color=AZUL, lw=1.0)
    for extremo in [78.0, 78.0 + largo]:
        ax.plot([extremo, extremo], [y - 0.5, y + 0.5], color=AZUL, lw=1.0)

# --- Dirección del orden ---
encabezado(ax, 3.4, 19.0, "Dirección del orden", size=11)

titulo(ax, fig, 10.0, 14.6, "Secuencial", size=10)
ax.plot([12.0, 12.0], [9.4, 11.0], color=AZUL, lw=1.2)
flecha(ax, (12.0, 10.2), (26.0, 10.2), lw=1.2, escala=12)

titulo(ax, fig, 42.0, 14.6, "Divergente", size=10)
flecha(ax, (51.0, 10.2), (44.0, 10.2), lw=1.2, escala=12)
flecha(ax, (51.0, 10.2), (58.0, 10.2), lw=1.2, escala=12)
ax.plot([51.0, 51.0], [9.2, 11.2], color=AZUL, lw=2.2)

titulo(ax, fig, 74.0, 14.6, "Cíclico", size=10)
# Arco casi cerrado con punta: el orden avanza y vuelve al punto de partida.
t = np.linspace(np.radians(105), np.radians(400), 60)
ax.plot(78.0 + 2.6 * np.cos(t), 10.2 + 2.6 * np.sin(t), color=AZUL, lw=1.2)
ax.add_patch(
    FancyArrowPatch(
        (78.0 + 2.6 * np.cos(t[2]), 10.2 + 2.6 * np.sin(t[2])),
        (78.0 + 2.6 * np.cos(t[0]), 10.2 + 2.6 * np.sin(t[0])),
        arrowstyle="-|>",
        color=AZUL,
        lw=1.2,
        mutation_scale=12,
        shrinkA=0,
        shrinkB=0,
    )
)

fig.savefig(DIR_IMAGENES / "02-tipos-atributo.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/02-tipos-atributo.png")

# %%
# Las tres direcciones de orden con datos. La dirección no está en los números:
# está en cómo se interpretan, y decide qué eje y qué paleta corresponden.

# Población de Chile en los censos del siglo XX y XXI, en millones (INE).
CENSOS = {
    1907: 3.2, 1920: 3.7, 1930: 4.3, 1940: 5.0, 1952: 5.9, 1960: 7.4,
    1970: 8.9, 1982: 11.3, 1992: 13.3, 2002: 15.1, 2017: 17.6, 2024: 18.5,
}

# Anomalía de temperatura media global respecto del promedio 1961-1990, en
# grados Celsius (HadCRUT5).
ANOMALIAS = {
    1900: -0.31, 1920: -0.29, 1940: 0.00, 1960: -0.06, 1980: 0.11,
    2000: 0.32, 2020: 0.92,
}

# Precipitación media mensual en Santiago, en milímetros (Dirección
# Meteorológica de Chile).
LLUVIA = [17.2, 13.1, 8.6, 15.6, 55.6, 74.6, 77.0, 53.5, 30.5, 12.2, 8.0, 8.1]
MESES = ["E", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]

fig = plt.figure(figsize=(7.6, 2.3))
ax_sec = fig.add_subplot(1, 3, 1)
ax_div = fig.add_subplot(1, 3, 2)
ax_cic = fig.add_subplot(1, 3, 3, projection="polar")

ax_sec.plot(list(CENSOS), list(CENSOS.values()), color=AZUL, marker="o", markersize=2.5)
ax_sec.set_title("Secuencial", fontsize=9)
ax_sec.set_xlabel("Año del censo", fontsize=7)
ax_sec.set_ylabel("Población (millones)", fontsize=7)
ax_sec.tick_params(labelsize=6)

anios = list(ANOMALIAS)
valores = np.array(list(ANOMALIAS.values()))
ax_div.bar(
    anios,
    valores,
    width=12,
    color=[MAGENTA if v > 0 else AZUL for v in valores],
)
ax_div.axhline(0, color=AZUL, lw=0.8)
ax_div.set_title("Divergente", fontsize=9)
ax_div.set_xlabel("Año", fontsize=7)
ax_div.set_ylabel(r"Anomalía ($^\circ$C)", fontsize=7)
ax_div.tick_params(labelsize=6)

# La curva se cierra repitiendo el primer valor al final: en un eje cíclico
# diciembre y enero son vecinos.
angulos = np.linspace(0, 2 * np.pi, 12, endpoint=False)
ax_cic.plot(
    np.append(angulos, angulos[0]),
    np.append(LLUVIA, LLUVIA[0]),
    color=MAGENTA,
)
ax_cic.set_theta_zero_location("N")
ax_cic.set_theta_direction(-1)
ax_cic.set_xticks(angulos)
ax_cic.set_xticklabels(MESES, fontsize=6)
ax_cic.set_yticklabels([])
ax_cic.set_title("Cíclico", fontsize=9)

fig.savefig(DIR_IMAGENES / "02-direcciones-orden.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/02-direcciones-orden.png")

print(f"Población entre 1907 y 2024: de {CENSOS[1907]} a {CENSOS[2024]} millones")
print(f"Mes más lluvioso en Santiago: {MESES[int(np.argmax(LLUVIA))]} ({max(LLUVIA)} mm)")
