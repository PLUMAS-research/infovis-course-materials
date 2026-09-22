# %%
"""Quinta sesión de código: el catálogo de gráficos para tablas.

Cada gráfico de este recorrido se describe con el vocabulario de la unidad
anterior: qué datos necesita, qué marca usa, qué canales aplica y qué tarea
resuelve. La pregunta que ordena la elección no es cuál se ve mejor, sino qué
llaves y qué atributos tiene la tabla.

Las figuras quedan en images/, que es de donde las toman las slides.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from chiricoca.tables import (
    barchart,
    heatmap,
    marimekko,
    parallel_coordinates,
    scatterplot,
    streamgraph,
    ternary_scatter,
)

from visutils.estilo import AZUL, DPI, GRIS, MAGENTA, estilo_curso
from visutils.general import descargar_datos

estilo_curso()

guaguas = pd.read_csv(descargar_datos("guaguas.tgz") / "guaguas.csv.gz")
viajes = pd.read_parquet(descargar_datos("eod-viajes.tgz") / "eod-viajes.parquet")

print(f"Nombres inscritos: {len(guaguas):,} filas, {guaguas['anio'].min()} a {guaguas['anio'].max()}")
print(f"Viajes de la EOD: {len(viajes):,}")

# El sector de la ciudad aparece como color en varias figuras. Fijar la paleta
# una sola vez asegura que cada sector tenga el mismo color en todas.
SECTORES = list(viajes["sector"].cat.categories)
PALETA_SECTOR = dict(zip(SECTORES, sns.color_palette("tab10", len(SECTORES))))

# %%
# PARTE 1: qué tiene una tabla
#
# Una tabla tiene observaciones. Cada una lleva atributos que la caracterizan y
# una llave que la identifica. La llave decide qué gráficos son posibles: si es
# categórica, barras; si es ordinal o cuantitativa, líneas.

print("Llaves y atributos de guaguas:")
print("  llaves    : anio (ordinal), nombre (categórica), sexo (categórica)")
print("  atributos : n (cuantitativo), proporcion (cuantitativo)")
print(guaguas.head())

print("\nLlaves y atributos de viajes:")
print("  llaves    : hogar, persona y viaje (identificadores), comuna_origen, sector")
print("              y dia (categóricas)")
print("  atributos : proposito, modo y periodo (categóricos), hora_inicio (cíclico),")
print("              minutos (cuantitativo)")
print(viajes.head())

# %%
# PARTE 2: scatterplot
#
# Datos: dos atributos cuantitativos, sin llave. Marca: puntos. Canales:
# posición horizontal y vertical. Tarea: encontrar correlación y valores
# atípicos.
#
# Operación: agrupar por nombre y resumir cada grupo en dos números, de modo que
# cada nombre pase de ser muchas filas a ser una sola observación.

por_nombre = (
    guaguas.groupby("nombre")
    .agg(total=("n", "sum"), anios=("anio", "nunique"), peak=("n", "max"))
    .query("total >= 2000")
    .reset_index()
)
print(f"Nombres con 2.000 inscripciones o más: {len(por_nombre):,}")

fig, ax = plt.subplots(figsize=(4.6, 3.4))
scatterplot(por_nombre, x="anios", y="peak", ax=ax, scatter_args={"color": AZUL, "s": 10})
ax.set_yscale("log")
ax.set_title("Duración y máximo de cada nombre")
ax.set_xlabel("Años en que aparece")
ax.set_ylabel("Máximo de inscripciones en un año")
fig.savefig("images/05-scatterplot.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 3: líneas y áreas
#
# Datos: una llave ordinal, una categórica y un valor. Marca: puntos conectados
# por líneas, o áreas si se apilan. Canales: posición horizontal para el año,
# posición vertical para la proporción, color para el nombre. Tarea: seguir la
# tendencia de cada serie.
#
# La línea afirma que entre dos puntos hay continuidad, así que la llave tiene
# que estar ordenada.
#
# Operación: agrupar por las dos llaves, sumar el valor y pasar la llave
# categórica a columnas con unstack, que es la forma que espera plot.

NOMBRES = ["María", "Katherine", "Benjamín", "Sofía"]
series = (
    guaguas[guaguas["nombre"].isin(NOMBRES)]
    .groupby(["anio", "nombre"])["proporcion"]
    .sum()
    .unstack(fill_value=0)
    * 100
)

fig, ax = plt.subplots(figsize=(4.6, 3.4))
series.plot(ax=ax, lw=1.2)
ax.set_title("Líneas")
ax.set_xlabel("Año de inscripción")
ax.set_ylabel("% de inscripciones del año")
ax.legend(fontsize=6)
fig.savefig("images/05-lineas.png", dpi=DPI, bbox_inches="tight")

fig, ax = plt.subplots(figsize=(7.4, 3.8))
series.plot(kind="area", ax=ax, lw=0, alpha=0.85)
ax.set_title("Áreas apiladas")
ax.set_xlabel("Año de inscripción")
ax.set_ylabel("% de inscripciones del año")
ax.legend(fontsize=6)
fig.savefig("images/05-areas.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 4: barras apiladas y normalizadas
#
# Datos: dos llaves categóricas y un valor. Marca: líneas con largo. Canales:
# largo para el valor, posición sobre un eje común para la primera llave, color
# para la segunda. Tarea: comparar totales y, dentro de cada total, comparar la
# composición.
#
# Al apilar, solo el primer segmento tiene base común: los demás flotan y su
# largo se vuelve difícil de comparar entre barras. Al normalizar se pierde el
# total y se gana la comparación de proporciones.
#
# Operación: contar por las dos llaves con size, pasar la segunda a columnas y
# quedarse con las cinco categorías más frecuentes.

modo_periodo = (
    # El período viene como categórica y trae el rango horario entre paréntesis.
    # Hay que pasarlo a texto antes de cortarlo, si no el split no rinde.
    viajes.assign(
        periodo_corto=lambda d: d["periodo"].astype(str).str.split(" (", regex=False).str[0]
    )
    .groupby(["periodo_corto", "modo"], observed=True)
    .size()
    .unstack(fill_value=0)
)
principales = modo_periodo.sum().nlargest(5).index
modo_periodo = modo_periodo[principales]
print(modo_periodo)

fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.8))
barchart(modo_periodo, stacked=True, horizontal=True, palette="viridis", ax=axes[0])
axes[0].set_title("Apiladas: total y composición")
axes[0].set_ylabel("")

barchart(modo_periodo, stacked=True, normalize=True, horizontal=True, palette="viridis", ax=axes[1])
axes[1].set_title("Normalizadas: solo composición")
axes[1].set_ylabel("")
fig.savefig("images/05-barras.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 5: histograma
#
# Datos: un atributo cuantitativo, sin llave. Marca: líneas con largo. Canales:
# posición horizontal para el intervalo, largo para el conteo. Tarea: ver la
# forma de una distribución.
#
# Un histograma es un gráfico de barras cuya llave es ordinal y la construye el
# propio gráfico: cada categoría cubre un rango de valores. El ancho del rango
# es una decisión de quien grafica y cambia la forma que se ve.
#
# Operación: dividir el rango del atributo en intervalos y contar cuántas
# observaciones caen en cada uno.

hora = viajes["hora_inicio"].dropna()

fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.8), sharey=True)
for ax, bins in zip(axes, [6, 12, 24]):
    hora.plot(kind="hist", bins=bins, color=AZUL, ax=ax, edgecolor="white", linewidth=0.4)
    ax.set_title(f"{bins} intervalos")
    ax.set_xlabel("Hora de inicio")
    ax.set_ylabel("")
axes[0].set_ylabel("Viajes")
fig.savefig("images/05-histograma.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 6: boxplot
#
# Datos: una llave categórica y un atributo cuantitativo. Marca: un glifo de
# líneas y un área por categoría. Canales: posición para los cinco números
# resumen (mínimo, cuartiles y máximo), región del espacio para la categoría.
# Tarea: comparar distribuciones entre categorías.
#
# Operación: ninguna agregación previa. El gráfico calcula los cuartiles sobre
# las observaciones de cada categoría.

MODOS = ["Caminata", "Bicicleta", "Auto", "Bus TS", "Metro", "Bus TS - Metro"]

# modo es una categórica con los dieciocho modos de la encuesta. Filtrar filas
# no elimina las categorías vacías, y seaborn dibujaría dieciocho cajas, doce
# de ellas vacías: hay que pasar la columna a texto.
duraciones = viajes[viajes["modo"].isin(MODOS)].assign(modo=lambda d: d["modo"].astype(str))

largos = duraciones["minutos"] > 150
print(f"Viajes de más de 150 minutos que quedan fuera: {largos.sum():,} ({largos.mean():.1%})")
duraciones = duraciones[~largos]

# Las categorías van ordenadas por su mediana, así el gráfico se lee de arriba
# hacia abajo.
ORDEN = duraciones.groupby("modo")["minutos"].median().sort_values().index

fig, ax = plt.subplots(figsize=(4.6, 3.4))
sns.boxplot(
    data=duraciones, x="minutos", y="modo", order=ORDEN, ax=ax, color=GRIS,
    width=0.55, fliersize=1, medianprops={"color": MAGENTA, "linewidth": 1.2},
)
ax.set_title("Duración del viaje según modo")
ax.set_xlabel("Minutos")
ax.set_ylabel("")
fig.savefig("images/05-boxplot.png", dpi=DPI, bbox_inches="tight")

print("Cuartiles de la duración por modo:")
print(duraciones.groupby("modo")["minutos"].quantile([0.25, 0.5, 0.75]).unstack().loc[ORDEN].round(0))

# %%
# PARTE 6b: violín
#
# Datos: los mismos del boxplot. Marca: un área por categoría. Canales: grosor
# para la densidad, posición para el valor, región del espacio para la
# categoría. Tarea: comparar la forma de las distribuciones.
#
# El violín reemplaza los cinco números por la densidad completa, estimada con
# un kernel. El ancho del kernel es una decisión, como el número de intervalos
# del histograma: uno angosto muestra cada ondulación de los datos y uno ancho
# las borra.
#
# Operación: ninguna. El gráfico estima la densidad sobre las observaciones.

fig, ax = plt.subplots(figsize=(4.6, 3.4))
sns.violinplot(
    data=duraciones, x="minutos", y="modo", order=ORDEN, ax=ax, color=GRIS,
    inner="quart", cut=0, linewidth=0.6, density_norm="width",
)
ax.set_title("Duración del viaje según modo")
ax.set_xlabel("Minutos")
ax.set_ylabel("")
fig.savefig("images/05-violin.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 6c: boxplot y violín lado a lado
#
# Los dos resumen la misma columna. El boxplot dice dónde está la mitad central
# de cada modo y cuánto se extiende; el violín dice cuántos viajes hay en cada
# duración, que es lo que la caja no puede decir.

fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.8), sharey=True)
sns.boxplot(
    data=duraciones, x="minutos", y="modo", order=ORDEN, ax=axes[0], color=GRIS,
    width=0.55, fliersize=1, medianprops={"color": MAGENTA, "linewidth": 1.2},
)
axes[0].set_title("Boxplot")

sns.violinplot(
    data=duraciones, x="minutos", y="modo", order=ORDEN, ax=axes[1], color=GRIS,
    inner="quart", cut=0, linewidth=0.6, density_norm="width",
)
axes[1].set_title("Violín")

for ax in axes:
    ax.set_xlabel("Minutos")
    ax.set_ylabel("")
fig.savefig("images/05-boxplot-violin.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 6d: raincloud
#
# Datos: los mismos del boxplot. Marca: un glifo de tres capas por categoría.
# Canales: posición horizontal para el valor en las tres capas, grosor de la
# nube para la densidad. Tarea: comparar distribuciones sin perder la forma ni
# las observaciones.
#
# El nombre viene de la figura: la nube arriba es la densidad, la caja al medio
# son los cinco números y la lluvia abajo son las observaciones. Es un caso de
# marca compuesta: tres gráficos superpuestos en un mismo eje.
#
# Operación: ninguna. Las tres capas se dibujan sobre las mismas observaciones.

fig, ax = plt.subplots(figsize=(4.8, 3.6))

# La nube: violín completo, recortado después a su mitad superior.
sns.violinplot(
    data=duraciones, x="minutos", y="modo", order=ORDEN, ax=ax, color=GRIS,
    inner=None, cut=0, linewidth=0, density_norm="width",
)
for posicion, coleccion in enumerate(ax.collections):
    vertices = coleccion.get_paths()[0].vertices
    vertices[:, 1] = np.clip(vertices[:, 1], -np.inf, posicion)

# La lluvia: las observaciones, corridas hacia abajo para que no tapen la nube.
# stripplot deja una colección por categoría, así que hay que correrlas todas.
dibujadas = len(ax.collections)
sns.stripplot(
    data=duraciones.sample(1500, random_state=0), x="minutos", y="modo", order=ORDEN,
    ax=ax, color=MAGENTA, size=2, alpha=0.5, jitter=0.06,
)
for coleccion in ax.collections[dibujadas:]:
    coleccion.set_offsets(coleccion.get_offsets() + [0, 0.25])

# La caja: los cinco números, al medio.
sns.boxplot(
    data=duraciones, x="minutos", y="modo", order=ORDEN, ax=ax, width=0.12,
    showfliers=False, boxprops={"facecolor": "white"}, medianprops={"color": MAGENTA},
)

ax.set_title("Duración del viaje según modo")
ax.set_xlabel("Minutos")
ax.set_ylabel("")
fig.savefig("images/05-raincloud-eod.png", dpi=DPI, bbox_inches="tight")

# La lluvia deja ver algo que la nube borra: casi todas las duraciones son
# múltiplos de cinco, porque son respuestas a una encuesta y no mediciones.
redondos = (duraciones["minutos"] % 5 == 0).mean()
print(f"Duraciones que son múltiplo de cinco minutos: {redondos:.1%}")

# %%
# PARTE 7: streamgraph
#
# Datos: una llave ordinal, una categórica y un valor. Marca: bandas. Canales:
# grosor para el valor, posición horizontal para el tiempo, color para la
# categoría. Tarea: seguir la trayectoria de muchas categorías a la vez.
#
# Generaliza las áreas apiladas: la línea base deja de ser el eje y las bandas
# se acomodan alrededor. Enfatiza la continuidad de cada banda en el tiempo, a
# costa de que ningún valor se pueda leer contra una escala.
#
# Operación: la misma tabla año por nombre de la parte 3, ahora con doce
# categorías en vez de cuatro.

TOP = (
    guaguas.groupby("nombre")["n"].sum().nlargest(12).index
)
corrientes = (
    guaguas[guaguas["nombre"].isin(TOP)]
    .groupby(["anio", "nombre"])["n"]
    .sum()
    .unstack(fill_value=0)
)

fig, ax = plt.subplots(figsize=(7.4, 3.8))
streamgraph(corrientes, palette="husl", ax=ax)
ax.set_title("Los doce nombres más inscritos del siglo")
ax.set_xlabel("Año de inscripción")
fig.savefig("images/05-streamgraph.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 8: heatmap
#
# Datos: dos llaves categóricas y un valor. Marca: áreas alineadas en una
# matriz. Canales: posición horizontal y vertical para las dos llaves,
# luminosidad para el valor. Tarea: ver el patrón general de una tabla completa.
#
# La luminosidad es un canal de magnitud poco preciso, así que el heatmap sirve
# para encontrar dónde mirar, no para comparar valores.
#
# Operación: contar por las dos llaves, pasar la segunda a columnas y quedarse
# con las seis filas de mayor total.

matriz = (
    viajes.groupby(["proposito", "hora_inicio"], observed=True)
    .size()
    .unstack(fill_value=0)
)
matriz = matriz.loc[matriz.sum(axis=1).nlargest(6).index]

fig, ax = plt.subplots(figsize=(7.4, 3.8))
heatmap(matriz, cmap="magma_r", ax=ax, cbar_kws={"label": "viajes"})
ax.set_title("Propósito del viaje por hora de inicio")
ax.set_xlabel("Hora de inicio")
ax.set_ylabel("")
ax.tick_params(axis="y", labelsize=7)
fig.savefig("images/05-heatmap.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 8b: cluster heatmap
#
# Datos: los mismos del heatmap. Marca: las mismas áreas, más un árbol. Canales:
# los mismos, y el largo de las ramas para la distancia entre grupos. Tarea:
# encontrar filas parecidas entre sí.
#
# Con los conteos crudos, la fila de mayor volumen se lleva toda la escala de
# color y las demás quedan pálidas. Al dividir cada fila por su total, la fila
# deja de decir cuántos viajes son y pasa a decir a qué hora ocurren: el perfil
# horario del propósito. Recién ahí tiene sentido agrupar filas parecidas.
#
# Operación: la misma matriz completa, dividida fila a fila por su total, y
# clustering jerárquico solo sobre las filas. Las columnas no se reordenan
# porque la hora tiene un orden propio.

perfiles = (
    viajes.groupby(["proposito", "hora_inicio"], observed=True)
    .size()
    .unstack(fill_value=0)
)
perfiles = perfiles.div(perfiles.sum(axis=1), axis=0) * 100

ax = heatmap(
    perfiles, cluster_rows=True, cmap="magma_r", robust=True, linewidths=0.3,
    fig_args={"figsize": (7.4, 3.8)}, cbar_kws={"label": "% de los viajes"},
)
ax.set_title("Perfil horario de cada propósito")
ax.set_xlabel("Hora de inicio")
ax.set_ylabel("")
ax.tick_params(labelsize=6)
ax.get_figure().savefig("images/05-cluster-heatmap.png", dpi=DPI, bbox_inches="tight")

print("Hora de mayor actividad de cada propósito:")
for proposito, fila in perfiles.iterrows():
    print(f"  {proposito:30s} {fila.idxmax():2d}h ({fila.max():.1f}%)")

# %%
# PARTE 8c: la misma técnica sobre el día de la semana
#
# Cada hogar de la encuesta declara los viajes de un solo día, y se encuestaron
# más hogares un viernes que un lunes: los conteos por día mezclan lo que hace
# la gente con cuántos hogares cayeron en cada día. Por eso hay dos
# normalizaciones. La primera divide cada columna por su total y deja la
# composición de los viajes de cada día, que ya no depende de la muestra. La
# segunda divide cada fila por su total y deja el perfil semanal del propósito,
# que es lo que se quiere agrupar.
#
# Volver a casa queda fuera: es la mitad de los viajes de cualquier día y no
# distingue ninguno.

semana = (
    viajes[viajes["proposito"] != "volver a casa"]
    .groupby(["proposito", "dia"], observed=True)
    .size()
    .unstack(fill_value=0)
)
semana = semana.div(semana.sum(axis=0), axis=1)
semana = semana.div(semana.sum(axis=1), axis=0) * 100

ax = heatmap(
    semana, cluster_rows=True, cmap="magma_r", annot=True, fmt=".0f", linewidths=0.3,
    annot_kws={"fontsize": 6}, cbar=False, fig_args={"figsize": (7.4, 3.8)},
)
ax.set_title("Perfil semanal de cada propósito (% de sus viajes)")
ax.set_xlabel("")
ax.set_ylabel("")
ax.tick_params(labelsize=6)
ax.get_figure().savefig("images/05-rutinas-dia.png", dpi=DPI, bbox_inches="tight")

fin_de_semana = semana[["sábado", "domingo"]].sum(axis=1).sort_values()
print("Propósitos según el peso del fin de semana:")
print(fin_de_semana.round(1).to_string())

# %%
# PARTE 9: marimekko
#
# Datos: dos llaves categóricas y un valor. Marca: áreas. Canales: alto para la
# proporción dentro del grupo, ancho para el tamaño del grupo, color para la
# segunda llave. Tarea: comparar composiciones sin perder de vista cuánto pesa
# cada grupo.
#
# Agrega un canal a las barras apiladas normalizadas, y el precio es que ninguna
# de las dos dimensiones del área tiene base común.
#
# Operación: la misma tabla período por modo de la parte 4.

fig, ax = plt.subplots(figsize=(7.4, 3.8))
marimekko(modo_periodo, palette="viridis", ax=ax)
ax.set_title("Composición modal por período, con el ancho según el total")
fig.savefig("images/05-marimekko.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 10: varias dimensiones a la vez
#
# Con más de dos atributos cuantitativos hay dos salidas clásicas, y las dos
# parten de la misma tabla: una fila por comuna con cuatro atributos, más el
# sector de la ciudad como categoría para el color.
#
# Operación: agrupar por comuna y resumir cada una en cuatro números. Tres son
# porcentajes de los viajes de la comuna y el cuarto es una media.


def porcentaje(serie, patron):
    """Porcentaje de los valores de la serie que contienen el patrón."""
    return serie.astype(str).str.contains(patron).mean() * 100


comunas = (
    viajes.groupby("comuna_origen", observed=True)
    .agg(**{
        "viajes": ("viaje", "size"),
        "% auto": ("modo", lambda s: porcentaje(s, "Auto|Taxi")),
        "% caminata": ("modo", lambda s: porcentaje(s, "Caminata|Bicicleta")),
        "% compras": ("proposito", lambda s: porcentaje(s, "compras")),
        "minutos": ("minutos", "mean"),
        "sector": ("sector", "first"),
    })
    .query("viajes >= 500")
)
ATRIBUTOS = ["% auto", "% caminata", "% compras", "minutos"]
print(f"Comunas con 500 viajes o más: {len(comunas)}")
print(comunas[ATRIBUTOS].describe().round(1))
print("Correlación entre atributos:")
print(comunas[ATRIBUTOS].corr().round(2))

# Matriz de scatterplots. Marca: puntos. Canales: posición horizontal y
# vertical, distintos en cada panel, y color para el sector. Tarea: buscar en
# qué par de atributos hay relación. El número de paneles crece al cuadrado con
# los atributos, así que solo sirve con pocos.

splom = sns.pairplot(
    comunas, vars=ATRIBUTOS, hue="sector", palette=PALETA_SECTOR, corner=True,
    height=1.25, plot_kws={"s": 16, "alpha": 0.9, "edgecolor": "none"},
    diag_kind="hist", diag_kws={"multiple": "stack", "bins": 10, "linewidth": 0},
)
for ax in splom.axes.flat:
    if ax is not None:
        ax.tick_params(labelsize=6)
        ax.xaxis.label.set_size(7)
        ax.yaxis.label.set_size(7)
splom.legend.set_title("")
splom.figure.suptitle(f"Cuatro atributos de {len(comunas)} comunas", fontsize=9)
splom.figure.savefig("images/05-splom.png", dpi=DPI, bbox_inches="tight")

# Coordenadas paralelas. Marca: una línea quebrada por comuna. Canales:
# posición vertical en cada eje para el valor del atributo, color para el
# sector. Tarea: encontrar grupos de observaciones con el mismo perfil.
#
# Cada eje tiene su propia escala, de su mínimo a su máximo. El orden de los
# ejes es una decisión: dos atributos vecinos con relación inversa se ven como
# líneas que se cruzan, y con relación directa como líneas paralelas. Acá cada
# eje va al lado del atributo con el que más se relaciona.

fig, ax = plt.subplots(figsize=(7.4, 3.8))
parallel_coordinates(
    comunas, columns=ATRIBUTOS, hue="sector", palette=PALETA_SECTOR, ax=ax,
    labels=["Vitacura", "Las Condes", "Santiago", "La Pintana", "Providencia"],
)
ax.set_title(f"Las mismas {len(comunas)} comunas, una línea por comuna")
fig.savefig("images/05-paralelas.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 11: áreas apiladas normalizadas
#
# Datos: una llave ordinal, una categórica y un valor. Marca: áreas. Canales:
# grosor para la proporción, posición horizontal para el tiempo, color para la
# categoría. Tarea: seguir cómo cambia la composición, no el total.
#
# Operación: dividir cada fila de la tabla por su propia suma, o sea cada año
# por el total de ese año.

TOP_SIGLO = guaguas.groupby("nombre")["n"].sum().nlargest(6).index
conteos = (
    guaguas[guaguas["nombre"].isin(TOP_SIGLO)]
    .groupby(["anio", "nombre"])["n"]
    .sum()
    .unstack(fill_value=0)
)
composicion = conteos.div(conteos.sum(axis=1), axis=0) * 100

fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.8), sharex=True)
conteos.plot(kind="area", ax=axes[0], lw=0, legend=False)
axes[0].set_title("Áreas apiladas: total y composición", fontsize=9)
axes[0].set_ylabel("Inscripciones")

composicion.plot(kind="area", ax=axes[1], lw=0)
axes[1].set_title("Normalizadas: solo composición", fontsize=9)
axes[1].set_ylabel("% de los seis nombres")
axes[1].legend(fontsize=5, ncol=2)
axes[1].set_ylim(0, 100)

for ax in axes:
    ax.set_xlabel("Año de inscripción")
fig.savefig("images/05-areas-normalizadas.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 12: barras polares
#
# Datos: una llave cíclica y un valor. Marca: líneas en coordenadas polares.
# Canales: ángulo para la llave, largo del radio para el valor. Tarea:
# comparar valores sobre un ciclo, sin que el final quede lejos del comienzo.
#
# Operación: contar por la llave cíclica y reindexar para que no falte ningún
# valor del ciclo.

por_hora = (
    viajes["hora_inicio"].value_counts().reindex(range(24), fill_value=0).sort_index()
)

fig, ax = plt.subplots(figsize=(4.4, 3.3), subplot_kw={"projection": "polar"})
grados = por_hora.index * 15
ax.bar(np.radians(grados), por_hora.values, width=np.radians(15),
       color=AZUL, edgecolor="white", linewidth=0.4)
ax.set_title("Viajes por hora de inicio", fontsize=9)
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_xticks(np.radians(np.arange(0, 360, 45)))
ax.set_xticklabels([f"{h}h" for h in range(0, 24, 3)], fontsize=6)
ax.set_yticklabels([])

fig.savefig("images/05-barras-polares.png", dpi=DPI, bbox_inches="tight")

print(f"Hora con más viajes: {por_hora.idxmax()}h ({por_hora.max():,} viajes)")

# %%
# PARTE 13: partes de un todo
#
# Datos: una llave categórica y un valor que suma un total. Marca: sectores en
# la torta, segmentos en la barra apilada. Canales: ángulo y área en la torta,
# largo en la barra. Tarea: comparar la parte con el todo.
#
# La barra usa un canal más preciso que la torta, y por eso mismo pierde la
# lectura inmediata de "esto es la mitad" que da el círculo.
#
# Operación: contar por la llave y dividir por el total.

partes = viajes["modo"].value_counts().head(6)
partes = (partes / partes.sum() * 100).sort_values(ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.8), width_ratios=[1, 1.6])
colores = plt.get_cmap("viridis")(np.linspace(0.15, 0.9, len(partes)))

axes[0].pie(partes.values, labels=partes.index, colors=colores, startangle=90,
            counterclock=False, textprops={"fontsize": 6},
            wedgeprops={"edgecolor": "white", "linewidth": 0.6})
# pie() reubica su eje al dibujar: sin este anclaje el círculo queda descentrado
# respecto del panel de al lado.
axes[0].set_anchor("N")
axes[0].set_title("Torta", fontsize=9)

izquierda = 0
for (modo, valor), color in zip(partes.items(), colores):
    axes[1].barh(0, valor, left=izquierda, color=color, edgecolor="white", linewidth=0.6)
    etiqueta = f"{modo}\n{valor:.0f}%" if valor > 12 else f"{valor:.0f}%"
    axes[1].text(izquierda + valor / 2, 0, etiqueta, ha="center", va="center",
                 fontsize=6, color="white")
    izquierda += valor
axes[1].set_title("Una sola barra apilada", fontsize=9)
axes[1].set_yticks([])
axes[1].set_xlabel("% de los viajes")

fig.savefig("images/05-partes.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 14: ternario
#
# Datos: tres atributos cuantitativos que suman un total. Marca: puntos.
# Canales: posición en coordenadas baricéntricas, más color para el sector y
# área para el total de viajes. Tarea: comparar la mezcla de tres partes entre
# observaciones.
#
# Los tres ejes no están alineados entre sí, y esa es la diferencia con un
# scatterplot: un punto se lee contra los tres a la vez y su posición ya contiene
# la restricción de que las tres partes suman 1.
#
# Operación: reducir los dieciocho modos de la EOD a tres grupos y contar por
# comuna. La normalización de cada fila la hace el gráfico.

GRUPOS_MODO = {"Activo": ("Caminata", "Bicicleta"),
               "Público": ("Bus", "Metro"),
               "Auto": ("Auto", "Taxi")}


def grupo_modal(modo):
    for grupo, patrones in GRUPOS_MODO.items():
        if any(patron in str(modo) for patron in patrones):
            return grupo
    return None


particion = (
    viajes.assign(grupo=lambda d: d["modo"].map(grupo_modal))
    .dropna(subset=["grupo"])
    .groupby(["comuna_origen", "grupo"], observed=True)
    .size()
    .unstack(fill_value=0)
)
particion = particion[particion.sum(axis=1) >= 800]
particion["viajes"] = particion.sum(axis=1)
particion["sector"] = particion.index.map(comunas["sector"])
print(f"Comunas en el ternario: {len(particion)}")

# Con cuarenta comunas no caben todos los nombres: se rotulan las de los
# extremos y las más pobladas.
DESTACADAS = ["Vitacura", "Las Condes", "Santiago", "Puente Alto", "La Pintana",
              "Estación Central", "Maipú", "Providencia"]

tax = ternary_scatter(
    particion, ["Auto", "Público", "Activo"], hue="sector", size="viajes",
    labels=DESTACADAS, palette=PALETA_SECTOR, fig_args={"figsize": (5.0, 3.7)},
)
ax = tax.get_axes()
ax.set_title("Partición modal de cada comuna", y=1.09)
ax.get_figure().savefig("images/05-ternario-eod.png", dpi=DPI, bbox_inches="tight")

print("\nFiguras escritas en images/:")
for nombre in ["scatterplot", "lineas", "areas", "barras", "histograma", "boxplot",
               "violin", "boxplot-violin", "raincloud-eod", "streamgraph", "heatmap",
               "cluster-heatmap", "rutinas-dia", "marimekko", "splom", "paralelas",
               "areas-normalizadas", "barras-polares", "partes", "ternario-eod"]:
    print(f"  images/05-{nombre}.png")
