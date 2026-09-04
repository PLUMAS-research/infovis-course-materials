"""Figuras de la unidad 05.

Tres demostraciones que no salen de los datos del curso sino de casos armados
para mostrar un punto: cuándo una línea afirma algo falso, cómo se lee cada
parte de un boxplot, y qué esconde un boxplot cuando resume una distribución
en cinco números (y que el violín sí muestra).

Uso: uv run python figuras/05-tablas.py
"""

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from chiricoca.base.paths import add_project_root

add_project_root(marker="pyproject.toml")

from visutils.estilo import AZUL, DPI, GRIS, MAGENTA, estilo_curso  # noqa: E402

estilo_curso(dpi=DPI)

DIR_IMAGENES = Path("images")
DIR_IMAGENES.mkdir(exist_ok=True)

# %%
# Barras o líneas. La línea afirma que entre dos puntos hay valores
# intermedios, así que solo corresponde cuando la llave está ordenada. Sobre
# una llave categórica, además, el orden de las categorías es arbitrario: la
# misma tabla produce dos líneas distintas.

CATEGORIAS = ["Bus", "Auto", "Metro", "Caminata", "Taxi"]
VALORES = [38, 27, 19, 12, 4]
otro_orden = [3, 0, 4, 2, 1]

fig, axes = plt.subplots(1, 3, figsize=(9, 2.4), sharey=True)

axes[0].bar(CATEGORIAS, VALORES, color=AZUL, width=0.65)
axes[0].set_title("Barras", fontsize=9)

axes[1].plot(CATEGORIAS, VALORES, color=MAGENTA, marker="o", ms=3)
axes[1].set_title("Líneas", fontsize=9)

axes[2].plot(
    [CATEGORIAS[i] for i in otro_orden],
    [VALORES[i] for i in otro_orden],
    color=MAGENTA, marker="o", ms=3,
)
axes[2].set_title("Líneas, con las categorías en otro orden", fontsize=9)

for ax in axes:
    ax.tick_params(axis="x", labelsize=6, rotation=30)
axes[0].set_ylabel("% de los viajes")

fig.savefig(DIR_IMAGENES / "05-barras-o-lineas.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/05-barras-o-lineas.png")

# %%
# Lo que esconde un boxplot. Tres distribuciones construidas para compartir sus
# cinco números resumen: mínimo, primer cuartil, mediana, tercer cuartil y
# máximo. El boxplot las muestra casi idénticas; las observaciones y el violín,
# que dibuja su densidad, las distinguen.

rng = np.random.default_rng(5)
n = 600

# Simétrica, bimodal y sesgada, todas ajustadas al mismo rango intercuartil.
simetrica = rng.normal(50, 12, n)
bimodal = np.concatenate([rng.normal(32, 5, n // 2), rng.normal(68, 5, n // 2)])
sesgada = 100 - rng.gamma(2.2, 9, n)

DISTRIBUCIONES = {"Simétrica": simetrica, "Bimodal": bimodal, "Sesgada": sesgada}

# El ajuste lleva las tres al mismo primer y tercer cuartil, que es lo que la
# caja dibuja: si no, la comparación no tendría gracia.
objetivo = np.percentile(simetrica, [25, 75])
for nombre, valores in DISTRIBUCIONES.items():
    q1, q3 = np.percentile(valores, [25, 75])
    DISTRIBUCIONES[nombre] = (valores - q1) / (q3 - q1) * (objetivo[1] - objetivo[0]) + objetivo[0]

fig, axes = plt.subplots(1, 3, figsize=(9.6, 2.8), sharey=True)

axes[0].boxplot(
    DISTRIBUCIONES.values(), tick_labels=list(DISTRIBUCIONES), showfliers=False,
    patch_artist=True, boxprops=dict(facecolor=GRIS, color=AZUL),
    medianprops=dict(color=MAGENTA), whiskerprops=dict(color=AZUL), capprops=dict(color=AZUL),
)
axes[0].set_title("Boxplot", fontsize=9)

# Las observaciones, con un poco de ruido horizontal para que no se apilen.
for i, (nombre, valores) in enumerate(DISTRIBUCIONES.items(), start=1):
    x = i + rng.uniform(-0.18, 0.18, len(valores))
    axes[1].scatter(x, valores, s=1.2, color=AZUL, alpha=0.3)
axes[1].set_xticks(range(1, len(DISTRIBUCIONES) + 1))
axes[1].set_xticklabels(list(DISTRIBUCIONES))
axes[1].set_title("Las mismas observaciones", fontsize=9)

observaciones = pd.DataFrame({
    "distribucion": np.repeat(list(DISTRIBUCIONES), [len(v) for v in DISTRIBUCIONES.values()]),
    "valor": np.concatenate(list(DISTRIBUCIONES.values())),
})
sns.violinplot(
    data=observaciones, x="distribucion", y="valor", ax=axes[2], color=GRIS,
    inner="quart", cut=0, linewidth=0.6,
)
axes[2].set_xlabel("")
axes[2].set_ylabel("")
axes[2].set_title("Violín", fontsize=9)

for ax in axes:
    ax.tick_params(axis="x", labelsize=7)

fig.savefig(DIR_IMAGENES / "05-boxplot-esconde.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/05-boxplot-esconde.png")

for nombre, valores in DISTRIBUCIONES.items():
    q1, mediana, q3 = np.percentile(valores, [25, 50, 75])
    print(f"  {nombre:10s} Q1={q1:.1f} mediana={mediana:.1f} Q3={q3:.1f}")

# %%
# Anatomía de un boxplot. Una sola caja sobre una muestra sesgada, con cada
# parte rotulada: la caja va del primer al tercer cuartil, la línea continua es
# la mediana y la discontinua la media, los bigotes llegan hasta el último dato
# que está a menos de 1,5 veces el rango intercuartil de la caja, y lo que
# queda más allá se dibuja como punto atípico. Es la regla por omisión de
# matplotlib y de seaborn.

rng = np.random.default_rng(3)
valores = np.concatenate([rng.gamma(6, 7, 150), [98, 104, 113]])

q1, mediana, q3 = np.percentile(valores, [25, 50, 75])
ric = q3 - q1
dentro = valores[(valores >= q1 - 1.5 * ric) & (valores <= q3 + 1.5 * ric)]
bigote_inferior, bigote_superior = dentro.min(), dentro.max()
atipicos = valores[(valores < bigote_inferior) | (valores > bigote_superior)]

fig, ax = plt.subplots(figsize=(2.6, 3.2))
ax.boxplot(
    valores, positions=[1], widths=0.8, showmeans=True, meanline=True,
    patch_artist=True, boxprops=dict(facecolor=GRIS, color=AZUL),
    medianprops=dict(color=MAGENTA, linewidth=1.5),
    meanprops=dict(color=AZUL, linestyle="--", linewidth=1),
    whiskerprops=dict(color=AZUL), capprops=dict(color=AZUL),
    flierprops=dict(marker="o", markersize=3, markerfacecolor=MAGENTA, markeredgecolor="none"),
)

# Rótulos a la derecha, con una línea guía hasta la parte que nombran. La
# media y la mediana quedan cerca, así que sus textos se separan un poco.
X_CAJA, X_TEXTO = 1.42, 1.6
rotulos = [
    (q3, q3, "Tercer cuartil (Q3)"),
    (mediana, mediana - 2.5, "Mediana"),
    (valores.mean(), valores.mean() + 2.5, "Media"),
    (q1, q1, "Primer cuartil (Q1)"),
    (bigote_superior, bigote_superior, "Último dato dentro de 1,5 RIC"),
    (bigote_inferior, bigote_inferior, "Primer dato dentro de 1,5 RIC"),
    (atipicos.max(), atipicos.max(), "Valores atípicos"),
]
for y, y_texto, texto in rotulos:
    ax.annotate(
        texto, xy=(X_CAJA, y), xytext=(X_TEXTO, y_texto), fontsize=8, va="center", color=AZUL,
        arrowprops=dict(arrowstyle="-", color=GRIS, lw=0.6),
    )

# La llave del rango intercuartil, a la izquierda de la caja.
X_LLAVE = 0.52
ax.plot([X_LLAVE, X_LLAVE], [q1, q3], color=AZUL, lw=0.8)
ax.plot([X_LLAVE, X_LLAVE + 0.05], [q1, q1], color=AZUL, lw=0.8)
ax.plot([X_LLAVE, X_LLAVE + 0.05], [q3, q3], color=AZUL, lw=0.8)
ax.text(X_LLAVE - 0.08, (q1 + q3) / 2, "Rango\nintercuartil\n(RIC)", fontsize=8,
        ha="right", va="center", color=AZUL)

ax.set_xlim(0.4, 3.0)
ax.set_axis_off()

fig.savefig(DIR_IMAGENES / "05-boxplot-anatomia.png", dpi=DPI, bbox_inches="tight")
plt.close(fig)
print("Escrito: images/05-boxplot-anatomia.png")
print(f"  Q1={q1:.1f} mediana={mediana:.1f} media={valores.mean():.1f} Q3={q3:.1f} "
      f"bigotes=[{bigote_inferior:.1f}, {bigote_superior:.1f}] atípicos={len(atipicos)}")
