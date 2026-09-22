# %%
"""Clase práctica de geografía: un hito 2 sobre la ampliación del Metro.

Entre 2017 y 2019 el Metro de Santiago sumó dos líneas. Esta sesión arma un
hito 2 completo alrededor de esa ampliación, con datos abiertos y operaciones
geométricas, y termina con la entrega tal como se presenta.

  Situación. El Metro de Santiago inauguró la Línea 6 en 2017 y la Línea 3 en
  2019: 22 estaciones nuevas. La Encuesta Origen-Destino 2012 registra dónde
  empezaba cada viaje antes de esa ampliación, el GTFS del DTPM entrega la red
  de hoy y el Censo 2024 dice dónde vive la gente.

  Complicación. La ampliación se discute por comuna, y a esa escala no se
  distingue si las líneas pasaron por donde había demanda sin alternativa ni qué
  sectores siguen sin ella. Una comuna de cien kilómetros cuadrados aparece con
  Metro por una estación en un extremo.

  Propuesta. Ordenar los sectores de la ciudad según la brecha entre su demanda
  de transporte público y su acceso al Metro, para orientar dónde conviene que
  la red siga creciendo.

De la propuesta salen tres tareas:

  medir la demanda de transporte público y la población de cada sector
  comparar la cobertura de la red de 2012 con la de hoy sobre los mismos sectores
  identificar los sectores con demanda que siguen fuera del área de servicio

Esta sesión hace esas tres tareas y revisa si los datos las sostienen, que es lo
que pide el hito 2. El orden de prioridad que plantea la propuesta se construye
después, en los hitos siguientes.

El sector es una celda hexagonal de la grilla H3, que mide lo mismo en toda la
ciudad. El script es autocontenido: construye desde cero todo lo que necesita.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from chiricoca.colors import colormap_from_palette
from chiricoca.geo.figures import small_multiples_from_geodataframe
from chiricoca.geo.grid import count_in_grid, h3_grid_from_bounds
from chiricoca.geo.utils import (
    clip_area_geodataframe,
    clip_point_geodataframe,
    to_point_geodataframe,
)
from chiricoca.maps import (
    bivariate_choropleth_map,
    choropleth_map,
    geographical_scale,
)
from adjustText import adjust_text
from matplotlib.collections import PolyCollection
from matplotlib.colors import BoundaryNorm
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

from visutils.estilo import AZUL, DPI, GRIS, MAGENTA, estilo_curso
from visutils.general import descargar_datos

estilo_curso()

# La EOD entrega las coordenadas en UTM 19 Sur, el sistema métrico de Chile
# central. EPSG:4326 son grados y sirve para desplegar.
CRS_METRICO = "EPSG:32719"
CRS_MAPA = "EPSG:4326"

# El área de estudio de la encuesta.
CAJA_URBANA = (-70.85, -33.65, -70.45, -33.30)
LATITUD_SANTIAGO = -33.45

# La grilla: celdas de 0,64 km2, unos 800 metros de lado.
GRILLA_NIVEL = 8
MARGEN = 0.02

# Distancia caminable hasta el transporte público, en metros. La planificación
# de transporte usa un cuarto de milla hasta un paradero y media milla hasta una
# estación, que redondeados son estos dos números.
RADIO_BUS = 400
RADIO_METRO = 800

# Desde esta fracción se considera que la celda está dentro del área de
# servicio. Media celda es el punto donde la mayoría de sus habitantes tiene la
# estación a distancia caminable.
DENTRO = 0.5

# Bajo este umbral la encuesta no alcanza para describir una celda.
MINIMO_VIAJES = 30

# Las líneas que no existían cuando se hizo la encuesta.
LINEAS_NUEVAS = {"L3", "L6"}

MILES = lambda x, _: f"{x:,.0f}".replace(",", ".")

COLOR_ESTADO = {
    "Ya tenía Metro en 2012": AZUL,
    "Ganó Metro con L3 y L6": MAGENTA,
    "Sigue sin Metro": "#C9CBD8",
}


def miles(n):
    """Un número con el separador de miles del castellano."""
    return f"{n:,.0f}".replace(",", ".")


def barra_de_escala(ax, crs=CRS_MAPA, color=AZUL):
    """Barra de distancia sobre el mapa.

    `dx` es cuánto mide en metros una unidad del eje: en un sistema métrico es
    un metro, y en grados depende de la latitud.
    """
    metros_por_unidad = (
        1.0 if crs == CRS_METRICO else 111_320 * np.cos(np.radians(LATITUD_SANTIAGO))
    )
    geographical_scale(
        ax, dx=metros_por_unidad, units="m", location="lower right", frameon=False,
        color=color, font_properties={"size": 6}, scale_loc="top",
        length_fraction=0.25, rotation="horizontal-only",
    )


def barra_de_rangos(ejes, bordes, palette, etiqueta, formato=miles):
    """Barra de color por clases, con un bloque del mismo ancho por clase.

    La barra que trae la coropleta ubica cada corte según su valor, y en una
    distribución sesgada los cortes bajos quedan tan juntos que sus rótulos se
    encabalgan. `spacing="uniform"` reparte los bloques por igual.
    """
    ejes = list(np.atleast_1d(ejes))
    colores = colormap_from_palette(palette, n_colors=len(bordes) - 1)
    barra = ejes[0].get_figure().colorbar(
        plt.cm.ScalarMappable(norm=BoundaryNorm(bordes, colores.N), cmap=colores),
        ax=ejes, orientation="horizontal", ticks=bordes, spacing="uniform",
        fraction=0.045, pad=0.02, shrink=0.6 if len(ejes) > 1 else 0.9,
    )
    barra.set_label(etiqueta, fontsize=7)
    barra.ax.tick_params(labelsize=6)
    barra.ax.set_xticklabels([formato(b) for b in bordes])
    return barra


def raincloud(datos, x, y, order, ax, color=AZUL, ancho=0.8):
    """Media nube de densidad, los puntos debajo y una caja delgada al medio.

    Un boxplot resume cinco números y esconde cuántas observaciones hay detrás.
    En una lámina ancha con varias categorías, la caja además queda tan chata
    que sus bigotes dejan de distinguirse.
    """
    sns.violinplot(data=datos, x=x, y=y, order=order, ax=ax, orient="h", color=color,
                   inner=None, linewidth=0, cut=0, density_norm="width", width=ancho)

    # `violinplot` dibuja la densidad simétrica: recortar la mitad de abajo deja
    # media nube sobre cada categoría.
    nubes = [c for c in ax.collections if isinstance(c, PolyCollection)]
    for posicion, coleccion in enumerate(nubes):
        for camino in coleccion.get_paths():
            camino.vertices[:, 1] = np.clip(camino.vertices[:, 1], -np.inf, posicion)
        coleccion.set_alpha(0.45)

    sns.stripplot(data=datos, x=x, y=y, order=order, ax=ax, orient="h", color=color,
                  size=1.6, alpha=0.5, jitter=0.08)

    # `stripplot` deja una colección por categoría, así que hay que correrlas
    # todas para que la lluvia caiga bajo su nube.
    for coleccion in ax.collections[len(nubes):]:
        puntos = coleccion.get_offsets()
        puntos[:, 1] += 0.16
        coleccion.set_offsets(puntos)

    sns.boxplot(data=datos, x=x, y=y, order=order, ax=ax, orient="h", width=0.12,
                showfliers=False,
                boxprops={"facecolor": "white", "edgecolor": color, "linewidth": 0.7},
                medianprops={"color": MAGENTA, "linewidth": 1.2},
                whiskerprops={"color": color, "linewidth": 0.7},
                capprops={"linewidth": 0})
    ax.set_ylabel("")
    return ax


def mapa_de_celdas(capa, columna, ax, titulo, etiqueta, palette="Blues",
                   bins=None, formato=miles):
    """Coropleta sobre la grilla, con las comunas de fondo y la escala."""
    comunas.plot(ax=ax, facecolor=GRIS, edgecolor="white", linewidth=0.3)
    clasificacion = ({"binning": "custom", "bins": bins} if bins is not None
                     else {"binning": "quantiles", "k": 5})
    _, info = choropleth_map(
        capa, columna, ax=ax, palette=palette, edgecolor="none", linewidth=0,
        legend=None, **clasificacion,
    )
    comunas.boundary.plot(ax=ax, color="white", linewidth=0.3, zorder=3)
    barra_de_rangos(ax, info["bins"], palette, etiqueta, formato=formato)
    barra_de_escala(ax)
    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()


# %%
# PARTE 1: las tres fuentes
#
# Cada una responde una parte de la pregunta: la encuesta dice dónde empezaban
# los viajes antes de la ampliación, el GTFS dónde está la red hoy y con qué
# líneas, y el censo dónde vive la gente ahora.

carpeta_eod = descargar_datos("eod-geografia.tgz")
carpeta_paradas = descargar_datos("paradas.tgz")
carpeta_comunas = descargar_datos("comunas-censo.tgz")
carpeta_censo = descargar_datos("censo2024-asignacion-rm.tgz")

viajes = pd.read_parquet(carpeta_eod / "viajes.parquet")
estaciones = gpd.read_parquet(carpeta_paradas / "estaciones-metro.parquet")
paraderos = gpd.read_parquet(carpeta_paradas / "paraderos-bus.parquet")
comunas_censo = gpd.read_parquet(carpeta_comunas / "comunas-rm.parquet")
censo_h3 = pd.read_parquet(carpeta_censo / "asignaciones-h3-8.parquet")
censo_h3["poblacion"] = censo_h3["n_hombres"] + censo_h3["n_mujeres"]

print(f"EOD 2012: {miles(len(viajes))} viajes")
print(f"GTFS: {len(estaciones)} estaciones de Metro, {miles(len(paraderos))} paraderos")
print(f"Censo 2024: {len(comunas_censo)} comunas, "
      f"{miles(comunas_censo['poblacion'].sum())} habitantes, repartidos en "
      f"{miles(len(censo_h3))} celdas H3")

# %%
# De columnas numéricas a geometría. Sin un sistema de coordenadas, las
# coordenadas de la encuesta son dos números y nada más.

origenes = to_point_geodataframe(viajes, "origen_x", "origen_y", crs=CRS_METRICO)
origenes = origenes.to_crs(CRS_MAPA)

print(f"\nOrígenes: {origenes.crs.to_string()}, estaciones: {estaciones.crs.to_string()}")

# Geopandas no reproyecta por su cuenta: una operación entre capas en sistemas
# distintos falla o entrega cualquier cosa.

# %%
# El recorte al área de estudio, con sus conteos. Los viajes con coordenadas
# válidas no están todos en Santiago y la región llega hasta la cordillera.

origenes = clip_point_geodataframe(origenes, CAJA_URBANA)
estaciones = clip_point_geodataframe(estaciones, CAJA_URBANA).to_crs(CRS_METRICO)
paraderos = clip_point_geodataframe(paraderos, CAJA_URBANA).to_crs(CRS_METRICO)
comunas = clip_area_geodataframe(comunas_censo, CAJA_URBANA)
comunas_m = comunas.to_crs(CRS_METRICO)

origenes_m = origenes.to_crs(CRS_METRICO)

print(f"\nDentro del área de estudio: {miles(len(origenes))} viajes de "
      f"{miles(len(viajes))} ({len(origenes) / len(viajes):.1%})")
print(f"{len(estaciones)} estaciones, {miles(len(paraderos))} paraderos, "
      f"{len(comunas)} comunas")
print(f"Geometrías inválidas: {(~comunas.is_valid).sum()}")

# %%
# PARTE 2: el sector
#
# La comuna es la unidad de la discusión y es demasiado grande: las del área de
# estudio van de 0,7 a 105 km2. La zonificación de la encuesta tampoco sirve
# para comparar, porque sus zonas van de 0,02 a 35,8 km2. Una grilla hexagonal
# da unidades que miden todas lo mismo.

grilla = h3_grid_from_bounds(np.array(CAJA_URBANA), extra_margin=MARGEN,
                             grid_level=GRILLA_NIVEL)
celdas = count_in_grid(origenes, grid_level=GRILLA_NIVEL, column="viajes",
                       grid=grilla).to_crs(CRS_METRICO)

print(f"Comunas del área de estudio: {len(comunas_m)}, de "
      f"{comunas_m.area.min() / 1e6:.1f} a {comunas_m.area.max() / 1e6:.0f} km2")
print(f"Celdas H3 nivel {GRILLA_NIVEL}: {miles(len(grilla))} sobre el área de "
      f"estudio, de {celdas.area.mean() / 1e6:.2f} km2 cada una")
print(f"Celdas con al menos un viaje: {miles(len(celdas))}")

# %%
# PARTE 3: la demanda previa a la ampliación
#
# La encuesta es de 2012, cinco años antes de la primera línea nueva, así que
# describe la demanda que existía antes de la decisión. De los viajes interesa
# el que usa transporte público, que es el que una estación nueva podría captar.

en_celda = gpd.sjoin(
    origenes_m[["modo", "hora_inicio", "geometry"]],
    grilla.to_crs(CRS_METRICO).reset_index()[["h3_cell_id", "geometry"]],
    predicate="within",
)
en_celda["modo"] = en_celda["modo"].astype(str)
es_publico = en_celda["modo"].str.contains("Bus|Metro")

celdas["viajes_publico"] = (
    en_celda[es_publico].groupby("h3_cell_id").size().reindex(celdas.index).fillna(0)
)
celdas["auto"] = (
    en_celda.groupby("h3_cell_id")["modo"].apply(lambda m: (m == "Auto").mean())
)

print(f"Viajes en transporte público: {miles(celdas['viajes_publico'].sum())} "
      f"({celdas['viajes_publico'].sum() / celdas['viajes'].sum():.1%} de los viajes)")
print(f"Por celda: mediana {celdas['viajes_publico'].median():.0f}, "
      f"máximo {miles(celdas['viajes_publico'].max())}")

# %%
# La demanda no es la misma a toda hora. En la mañana los viajes salen de donde
# la gente vive y en la tarde de donde trabaja o estudia, así que el mapa de una
# punta no sirve para leer la otra.

PERIODOS = {"Punta de la mañana (6 a 9)": (6, 9), "Punta de la tarde (17 a 20)": (17, 20)}

for nombre, (desde, hasta) in PERIODOS.items():
    ventana = es_publico & en_celda["hora_inicio"].between(desde, hasta)
    celdas[nombre] = (
        en_celda[ventana].groupby("h3_cell_id").size().reindex(celdas.index).fillna(0)
    )
    print(f"{nombre}: {miles(celdas[nombre].sum())} viajes en transporte público "
          f"({celdas[nombre].sum() / celdas['viajes_publico'].sum():.0%} del total)")

# %%
# La población de cada celda viene del censo, que la publica sobre esta misma
# grilla. Las dos capas se unen por el identificador de celda, sin reproyectar
# ni repartir nada.

celdas = celdas.join(censo_h3.set_index("h3_cell_id")[["poblacion"]])
celdas["poblacion"] = celdas["poblacion"].fillna(0)

print(f"\nPoblación del censo en el área de estudio: "
      f"{miles(celdas['poblacion'].sum())} habitantes")
print(f"Celdas con población y sin viajes en la encuesta: "
      f"{((celdas['poblacion'] > 0) & (celdas['viajes'] < MINIMO_VIAJES)).sum()}")

# %%
# Antes de construir nada más, una mirada a las variables que el proyecto usa.
# El hito 2 pide las distribuciones, y de ahí salen las decisiones que vienen
# después: qué modos entran, qué umbral de viajes por celda, qué hora.

viajes_area = viajes.loc[origenes.index]

print("Modo declarado, los seis más frecuentes:")
print((viajes_area["modo"].value_counts(normalize=True).head(6) * 100).round(1).to_string())
print(f"\nHora de inicio: punta de la mañana en las "
      f"{viajes_area['hora_inicio'].value_counts().idxmax():.0f} horas, "
      f"{viajes_area['hora_inicio'].isna().sum()} viajes sin hora")
print(f"Duración declarada: mediana {viajes_area['minutos'].median():.0f} minutos")
print(f"\nViajes en transporte público por celda: mediana "
      f"{celdas['viajes_publico'].median():.0f}, "
      f"{(celdas['viajes_publico'] < MINIMO_VIAJES).sum()} celdas bajo "
      f"{MINIMO_VIAJES} viajes")
print(f"Población por celda: mediana {celdas['poblacion'].median():,.0f}".replace(",", "."))

# %%
# La exploración va en una fila de cuatro paneles: en una lámina con título, una
# figura ancha se escala hasta el ancho y su texto queda legible al proyectar.

fig, axes = plt.subplots(1, 4, figsize=(7.4, 2.6))

# Cómo se viaja, que decide qué viajes entran en el análisis.
reparto = (
    viajes_area["modo"].astype(str).value_counts(normalize=True).head(6).sort_values()
)
colores = [MAGENTA if "Bus" in modo or "Metro" in modo else GRIS for modo in reparto.index]
axes[0].barh(reparto.index, reparto * 100, color=colores)
axes[0].set_xlabel("% de los viajes", fontsize=7)
axes[0].set_title("Modo declarado", fontsize=8)

# Cuándo empiezan, que muestra las dos puntas del día.
axes[1].hist(viajes_area["hora_inicio"].dropna(), bins=range(0, 25), color=AZUL)
axes[1].set_xlabel("hora de inicio", fontsize=7)
axes[1].set_xticks([0, 6, 12, 18, 24])
axes[1].yaxis.set_major_formatter(MILES)
axes[1].set_title("Hora de inicio del viaje", fontsize=8)

# Cuánta demanda tiene cada celda, que decide el umbral del análisis.
axes[2].hist(celdas["viajes_publico"].clip(upper=200), bins=30, color=MAGENTA)
axes[2].axvline(celdas["viajes_publico"].median(), color="black",
                linestyle="--", linewidth=1)
axes[2].set_xlabel("viajes por celda", fontsize=7)
axes[2].set_xticks([0, 100, 200], labels=["0", "100", "200+"])
axes[2].set_title("Viajes en transporte público", fontsize=8)

# Cuánta gente vive en cada celda, que da el peso de cada una.
axes[3].hist(celdas["poblacion"].clip(upper=20000), bins=30, color=AZUL)
axes[3].axvline(celdas["poblacion"].median(), color="black",
                linestyle="--", linewidth=1)
axes[3].set_xlabel("habitantes por celda", fontsize=7)
axes[3].set_xticks([0, 10000, 20000], labels=["0", "10.000", "20.000+"])
axes[3].set_title("Habitantes", fontsize=8)

for ax in axes:
    ax.tick_params(labelsize=6)

fig.savefig("images/07s-exploracion.png", dpi=DPI, bbox_inches="tight")

# La línea punteada es la mediana. Las dos distribuciones de abajo están
# cortadas en su extremo derecho, así que la última barra acumula la cola.

# %%
# Los dos paneles comparten los cortes de color, porque la comparación entre
# ellos es el punto de la figura.
cortes_demanda = np.unique(
    np.quantile(
        np.concatenate([celdas[nombre] for nombre in PERIODOS]),
        np.linspace(0, 1, 6),
    )
).round(0)

celdas_mapa = celdas.to_crs(CRS_MAPA)

fig, axes = small_multiples_from_geodataframe(comunas, len(PERIODOS), height=3.6,
                                              col_wrap=2)

for ax, nombre in zip(axes, PERIODOS):
    comunas.plot(ax=ax, facecolor=GRIS, edgecolor="white", linewidth=0.3)
    choropleth_map(celdas_mapa, nombre, ax=ax, binning="custom", bins=cortes_demanda,
                   palette="Blues", edgecolor="none", linewidth=0, legend=None)
    comunas.boundary.plot(ax=ax, color="white", linewidth=0.3, zorder=3)
    barra_de_escala(ax)
    ax.set_title(nombre, fontsize=9)
    ax.set_axis_off()

# Una sola barra para los dos paneles: comparten los cortes, y dos barras
# gastarían el alto que necesitan los mapas.
barra_de_rangos(axes, cortes_demanda, "Blues", "viajes en transporte público")

fig.suptitle("Viajes en transporte público por celda, según período del día",
             fontsize=11, y=1.04)
fig.savefig("images/07s-demanda.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 4: la red y su área de servicio
#
# El buffer devuelve todo lo que está a menos de cierta distancia de una
# geometría. Alrededor de una estación es el área desde la que se llega a pie, y
# `union_all` funde los círculos en una sola geometría sin solape.

area_metro = estaciones.buffer(RADIO_METRO)
servicio_metro = area_metro.union_all()
servicio_bus = paraderos.buffer(RADIO_BUS).union_all()

print(f"Un círculo de {RADIO_METRO} m mide {np.pi * RADIO_METRO**2 / 1e6:.2f} km2")
print(f"Los {len(area_metro)} círculos suman {miles(area_metro.area.sum() / 1e6)} km2 "
      f"y fundidos quedan en {miles(servicio_metro.area / 1e6)} km2 "
      f"({servicio_metro.area / comunas_m.area.sum():.1%} del área de estudio)")
print(f"Área de servicio del bus a {RADIO_BUS} m: "
      f"{miles(servicio_bus.area / 1e6)} km2 "
      f"({servicio_bus.area / comunas_m.area.sum():.1%})")

# El bus cubre casi la ciudad entera, así que el acceso al bus no distingue un
# sector de otro. La pregunta se juega en el Metro.

# %%
# La red que existía cuando se hizo la encuesta sale de las líneas: las
# estaciones servidas solo por L3 o L6 no existían en 2012.

# Una estación es nueva cuando todas sus líneas son nuevas: `issubset` pregunta
# justamente eso, si el conjunto de líneas que la sirven cabe dentro de L3 y L6.
nuevas = estaciones["lineas"].str.split(", ").apply(
    lambda lineas: set(lineas).issubset(LINEAS_NUEVAS)
)
servicio_2012 = estaciones[~nuevas].buffer(RADIO_METRO).union_all()

# `difference` deja lo que está en la primera geometría y no en la segunda.
ganado = servicio_metro.difference(servicio_2012)

print(f"\nEstaciones servidas solo por L3 o L6: {nuevas.sum()} de {len(estaciones)}")
print(f"Área de servicio en 2012: {miles(servicio_2012.area / 1e6)} km2")
print(f"Área de servicio hoy:     {miles(servicio_metro.area / 1e6)} km2 "
      f"({ganado.area / servicio_2012.area:.0%} más)")

# La aproximación es a nivel de línea: las estaciones que las otras líneas
# agregaron después de 2012 quedan contadas como si ya existieran.

# %%
fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2))

CENTRO = (-70.72, -33.50, -70.58, -33.40)
centro_m = (
    gpd.GeoSeries(
        gpd.points_from_xy([CENTRO[0], CENTRO[2]], [CENTRO[1], CENTRO[3]]), crs=CRS_MAPA
    )
    .to_crs(CRS_METRICO)
    .total_bounds
)

for ax, geometria, titulo in (
    (axes[0], area_metro, f"{len(estaciones)} círculos, uno por estación"),
    (axes[1], gpd.GeoSeries([servicio_metro], crs=CRS_METRICO),
     "La unión de los círculos"),
):
    comunas_m.plot(ax=ax, facecolor="#F4F4F7", edgecolor="white", linewidth=0.4)
    geometria.plot(ax=ax, facecolor=MAGENTA, edgecolor=MAGENTA, alpha=0.35, linewidth=0.5)
    estaciones.plot(ax=ax, color=AZUL, markersize=3, zorder=3)
    barra_de_escala(ax, crs=CRS_METRICO)
    ax.set_title(titulo, fontsize=9)
    ax.set_xlim(centro_m[0], centro_m[2])
    ax.set_ylim(centro_m[1], centro_m[3])
    ax.set_axis_off()

fig.suptitle("Área a 800 metros de una estación, antes y después de unirla",
             fontsize=11, y=1.06)
fig.savefig("images/07s-buffer.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 5: la cobertura de cada celda
#
# La intersección de dos geometrías es la parte que comparten. Dividida por el
# área de la celda, dice qué fracción de esa celda queda dentro del área de
# servicio, antes y después de la ampliación.

for columna, servicio in (("cobertura_2012", servicio_2012),
                          ("cobertura_hoy", servicio_metro)):
    # La fracción se recorta a uno: cuando la celda queda entera dentro, la
    # división da 1,0000000000000007 y ese sobrante rompe cualquier
    # clasificación en rangos.
    celdas[columna] = (
        celdas.geometry.intersection(servicio).area / celdas.area
    ).clip(0, 1)

print(f"Celdas dentro del área de servicio (al menos {DENTRO:.0%} de su superficie)")
print(f"  en 2012: {(celdas['cobertura_2012'] >= DENTRO).sum()}")
print(f"  hoy:     {(celdas['cobertura_hoy'] >= DENTRO).sum()}")

# %%
# El tamaño de la unidad decide qué mide esta fracción. Una celda de nivel 8
# mide unos 800 metros de lado y el radio del buffer son 800 metros, así que la
# celda entra casi entera o no entra.

for nivel in (7, 8, 9):
    grilla_nivel = h3_grid_from_bounds(np.array(CAJA_URBANA), extra_margin=MARGEN,
                                       grid_level=nivel)
    celdas_nivel = count_in_grid(origenes, grid_level=nivel, column="viajes",
                                 grid=grilla_nivel).to_crs(CRS_METRICO)
    cobertura = (
        celdas_nivel.geometry.intersection(servicio_metro).area / celdas_nivel.area
    ).clip(0, 1)
    extremos = ((cobertura == 0) | (cobertura > 0.99)).mean()
    print(f"H3 nivel {nivel}: celdas de {celdas_nivel.area.mean() / 1e6:.2f} km2, "
          f"cobertura 0 o 1 en el {extremos:.0%} de ellas")

# Con unidades más chicas que el radio, la fracción se vuelve una pertenencia:
# dice si la celda está dentro del área de servicio, no cuánto. Por eso el
# umbral de media celda y no una escala continua.

# %%
RADIOS = (400, 800, 1200)
CORTES = [0, 0.2, 0.4, 0.6, 0.8, 1.0]

celdas_mapa = celdas.to_crs(CRS_MAPA).copy()

fig, axes = small_multiples_from_geodataframe(comunas, len(RADIOS), height=3.0, col_wrap=3)

for ax, radio in zip(axes, RADIOS):
    servicio = estaciones.buffer(radio).union_all()
    cobertura = (celdas.geometry.intersection(servicio).area / celdas.area).clip(0, 1)
    celdas_mapa["cobertura"] = cobertura.to_numpy()

    comunas.plot(ax=ax, facecolor=GRIS, edgecolor="white", linewidth=0.3)
    choropleth_map(celdas_mapa, "cobertura", ax=ax, binning="custom", bins=CORTES,
                   palette="Purples", edgecolor="none", linewidth=0,
                   cbar_args={"orientation": "horizontal", "location": "lower left",
                              "width": "40%", "height": "3%", "label_size": "x-small"})
    comunas.boundary.plot(ax=ax, color="white", linewidth=0.3, zorder=3)
    barra_de_escala(ax)
    ax.set_title(f"radio = {radio} m, dentro {(cobertura >= DENTRO).mean():.0%} "
                 "de las celdas", fontsize=9)
    ax.set_axis_off()

fig.suptitle("Fracción de cada celda dentro del área de servicio del Metro",
             fontsize=11, y=1.04)
fig.savefig("images/07s-cobertura.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 6: qué cambió con la ampliación
#
# Con las dos coberturas, cada celda queda en uno de tres estados.

celdas["estado"] = np.select(
    [celdas["cobertura_2012"] >= DENTRO, celdas["cobertura_hoy"] >= DENTRO],
    ["Ya tenía Metro en 2012", "Ganó Metro con L3 y L6"],
    default="Sigue sin Metro",
)

resumen = celdas.groupby("estado").agg(
    celdas=("viajes", "size"),
    viajes_publico=("viajes_publico", "sum"),
    poblacion=("poblacion", "sum"),
    demanda_mediana=("viajes_publico", "median"),
)

print(resumen.round(1).to_string())

# %%
# Dos paneles, uno por momento: el mapa de la red de 2012 y el de hoy, con las
# celdas que se sumaron destacadas. Dos mapas lado a lado llenan la lámina, que
# uno solo deja a medio ancho.
fig, axes = small_multiples_from_geodataframe(comunas, 2, height=4.2, col_wrap=2)

for ax, momento in zip(axes, ("2012", "hoy")):
    comunas.plot(ax=ax, facecolor="#F4F4F7", edgecolor="white", linewidth=0.3)
    celdas.to_crs(CRS_MAPA).plot(ax=ax, facecolor=COLOR_ESTADO["Sigue sin Metro"],
                                 edgecolor="none")
    dentro = celdas[celdas[f"cobertura_{'2012' if momento == '2012' else 'hoy'}"] >= DENTRO]
    dentro.to_crs(CRS_MAPA).plot(ax=ax, facecolor=AZUL, edgecolor="none")
    if momento == "hoy":
        ganaron = celdas[celdas["estado"] == "Ganó Metro con L3 y L6"].to_crs(CRS_MAPA)
        ganaron.plot(ax=ax, facecolor=MAGENTA, edgecolor="none")
    comunas.boundary.plot(ax=ax, color="white", linewidth=0.4, zorder=3)
    barra_de_escala(ax)
    ax.set_title(f"La red de {momento}, {miles(len(dentro))} celdas dentro", fontsize=9)
    ax.set_axis_off()

axes[0].legend(
    handles=[Patch(facecolor=AZUL, label="dentro del área de servicio"),
             Patch(facecolor=MAGENTA, label="lo que sumaron la L3 y la L6"),
             Patch(facecolor=COLOR_ESTADO["Sigue sin Metro"], label="fuera")],
    fontsize=7, frameon=False, loc="lower left",
)

fig.suptitle("Celdas dentro del área de servicio, red de 2012 y red actual",
             fontsize=11, y=1.03)
fig.savefig("images/07s-estados.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 7: la comparación que responde la propuesta
#
# Entre las celdas que en 2012 no tenían Metro, las que después lo ganaron,
# ¿tenían más demanda que las que siguen sin él?

sin_metro_2012 = celdas[celdas["cobertura_2012"] < DENTRO].copy()
sin_metro_2012["resultado"] = np.where(
    sin_metro_2012["cobertura_hoy"] >= DENTRO, "Ganó Metro con L3 y L6", "Sigue sin Metro"
)

comparacion = sin_metro_2012.groupby("resultado").agg(
    celdas=("viajes_publico", "size"),
    demanda_mediana=("viajes_publico", "median"),
    poblacion_mediana=("poblacion", "median"),
    demanda_total=("viajes_publico", "sum"),
)

print(comparacion.round(1).to_string())

razon = (comparacion.loc["Ganó Metro con L3 y L6", "demanda_mediana"]
         / comparacion.loc["Sigue sin Metro", "demanda_mediana"])
print(f"\nLa celda mediana que ganó Metro tenía {razon:.1f} veces la demanda de "
      "transporte público de la celda mediana que sigue sin él")

# %%
fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0))

for ax, columna, etiqueta in (
    (axes[0], "viajes_publico", "viajes en transporte público, 2012"),
    (axes[1], "poblacion", "habitantes, Censo 2024"),
):
    raincloud(sin_metro_2012, columna, "resultado",
              ["Ganó Metro con L3 y L6", "Sigue sin Metro"], ax)
    ax.set_xlabel(etiqueta, fontsize=8)
    ax.xaxis.set_major_formatter(MILES)
    ax.tick_params(labelsize=8)

axes[0].set_xlim(0, 200)
axes[1].set_xlim(0, 25000)

fig.suptitle("Demanda y población de las celdas sin Metro en 2012, según su\n"
             "cobertura actual", fontsize=11, y=1.06)
fig.savefig("images/07s-comparacion.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 8: los sectores que siguen fuera
#
# La tercera tarea pide identificar. Entre las celdas que siguen sin Metro, las
# que tienen demanda comparable a las que la ganaron son las candidatas.

umbral = comparacion.loc["Ganó Metro con L3 y L6", "demanda_mediana"]
pendientes = celdas[
    (celdas["estado"] == "Sigue sin Metro") & (celdas["viajes_publico"] >= umbral)
]

print(f"Celdas sin Metro con demanda igual o mayor a la mediana de las que lo "
      f"ganaron ({umbral:.0f} viajes): {len(pendientes)}")
print(f"Concentran {miles(pendientes['viajes_publico'].sum())} viajes en transporte "
      f"público y {miles(pendientes['poblacion'].sum())} habitantes")

# Cada celda se ubica en una comuna por su centro, que en un hexágono siempre
# cae adentro.
comuna_de_celda = gpd.sjoin(
    pendientes.assign(geometry=pendientes.geometry.centroid),
    comunas_m[["comuna", "geometry"]], predicate="within",
)
print(comuna_de_celda["comuna"].value_counts().head(8).to_string())

# %%
# El mapa va con las comunas al lado: en una lámina, un mapa solo ocupa el
# ancho que le permite su alto, y la mitad queda vacía.
fig, axes = plt.subplots(1, 2, figsize=(7.4, 4.2),
                         gridspec_kw={"width_ratios": [1.25, 1]})

comunas.plot(ax=axes[0], facecolor="#F4F4F7", edgecolor="white", linewidth=0.3)
celdas[celdas["cobertura_hoy"] >= DENTRO].to_crs(CRS_MAPA).plot(
    ax=axes[0], facecolor=GRIS, edgecolor="none"
)
pendientes.to_crs(CRS_MAPA).plot(ax=axes[0], facecolor=MAGENTA, edgecolor="none")
comunas.boundary.plot(ax=axes[0], color="white", linewidth=0.4, zorder=3)
barra_de_escala(axes[0])
axes[0].legend(
    handles=[Patch(facecolor=GRIS, label="dentro del área de servicio"),
             Patch(facecolor=MAGENTA, label=f"sin Metro y con demanda ({len(pendientes)})")],
    fontsize=7, frameon=False, loc="lower left",
)
# Sin `set_aspect`: geopandas ajusta el aspecto de un CRS geográfico según la
# latitud, y forzar "equal" sobre grados deja el mapa estirado a lo alto.
axes[0].set_axis_off()

conteo_comunal = comuna_de_celda["comuna"].value_counts().head(10).sort_values()
axes[1].barh(conteo_comunal.index, conteo_comunal, color=MAGENTA)
axes[1].xaxis.set_major_locator(MaxNLocator(integer=True))
axes[1].set_xlabel("celdas sin Metro y con demanda", fontsize=8)
axes[1].tick_params(labelsize=8)

fig.suptitle("Celdas sin cobertura y con demanda sobre la mediana", fontsize=11,
             y=1.0)
fig.savefig("images/07s-pendientes.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 9: la lectura comunal
#
# La comuna es la unidad de la conversación pública, así que conviene saber qué
# dice y qué esconde. Con la población del censo se puede medir a cuánta gente
# llega la red.

celdas["poblacion_cubierta"] = celdas["poblacion"] * celdas["cobertura_hoy"]

cubierta = celdas["poblacion_cubierta"].sum()
total = celdas["poblacion"].sum()
print(f"Población a menos de {RADIO_METRO} m de una estación: {miles(cubierta)} "
      f"de {miles(total)} ({cubierta / total:.1%})")

centros = celdas.copy()
centros["geometry"] = centros.geometry.centroid

por_comuna = (
    gpd.sjoin(centros, comunas_m[["comuna", "geometry"]], predicate="within")
    .groupby("comuna")
    .agg(poblacion=("poblacion", "sum"),
         poblacion_cubierta=("poblacion_cubierta", "sum"),
         viajes_publico=("viajes_publico", "sum"))
)
por_comuna["cobertura_poblacion"] = (
    por_comuna["poblacion_cubierta"] / por_comuna["poblacion"]
)

# Las comunas del borde tienen parte de su población fuera del área de estudio,
# así que quedan fuera las que aportan poca.
MINIMO_POBLACION = 20_000
por_comuna = por_comuna[por_comuna["poblacion"] >= MINIMO_POBLACION]

print(f"\nComunas con {miles(MINIMO_POBLACION)} habitantes o más en el área de "
      f"estudio: {len(por_comuna)}")
print(por_comuna["cobertura_poblacion"].nlargest(5).map("{:.0%}".format).to_string())
print(f"Comunas sin nada de población cubierta: "
      f"{(por_comuna['cobertura_poblacion'] == 0).sum()}")

# %%
# El censo también dice en qué se va la gente al trabajo, así que la cobertura
# se contrasta con el uso declarado del transporte público.

uso = comunas_censo.set_index("comuna")[["transporte_publico", "transporte_auto"]]
por_comuna = por_comuna.join(uso)
por_comuna["uso_transporte_publico"] = por_comuna["transporte_publico"] / (
    por_comuna["transporte_publico"] + por_comuna["transporte_auto"]
)

print(f"\nCorrelación entre la cobertura de población y el uso declarado del "
      f"transporte público: "
      f"{por_comuna['cobertura_poblacion'].corr(por_comuna['uso_transporte_publico']):.2f}")

# %%
comunas_mapa = comunas.set_index("comuna")[["geometry"]].join(
    por_comuna[["cobertura_poblacion"]], how="inner"
)

fig, ax = plt.subplots(figsize=(4.8, 5.0))

comunas.plot(ax=ax, facecolor=GRIS, edgecolor="white", linewidth=0.3)
_, info = choropleth_map(
    comunas_mapa, "cobertura_poblacion", ax=ax, k=5, binning="quantiles",
    palette="Purples", edgecolor="white", linewidth=0.4, legend=None,
)
barra_de_rangos(ax, info["bins"], "Purples", "fracción de la población",
                formato=lambda v: f"{v:.0%}")
barra_de_escala(ax)
ax.set_axis_off()
ax.set_title(f"Población a menos de {RADIO_METRO} m de una estación, por comuna",
             fontsize=10)

fig.savefig("images/07s-comunal.png", dpi=DPI, bbox_inches="tight")

# %%
# Lo que la comuna esconde. Cada celda tiene su distancia al Metro, y el
# promedio comunal las resume en un número.

centros_distancia = gpd.GeoDataFrame(geometry=celdas.geometry.centroid, crs=CRS_METRICO)
celdas["distancia_metro"] = gpd.sjoin_nearest(
    centros_distancia, estaciones[["geometry"]], distance_col="d"
).pipe(lambda x: x[~x.index.duplicated()])["d"]

celdas_comuna = gpd.sjoin(
    celdas.assign(geometry=celdas.geometry.centroid)[["distancia_metro", "geometry"]],
    comunas_m[["comuna", "geometry"]], predicate="within",
)

dispersion = celdas_comuna.groupby("comuna")["distancia_metro"].agg(
    ["size", "median", "min", "max"]
)
dispersion = dispersion[dispersion["size"] >= 10]
dispersion["rango"] = dispersion["max"] - dispersion["min"]

print("\nComunas donde la distancia al Metro varía más adentro:")
print(dispersion.nlargest(4, "rango")[["median", "min", "max"]].round(0).to_string())

# %%
# Una fila por comuna no cabe: son 38 y sus nombres dejarían de leerse. El
# resumen que sí cabe es un punto por comuna, con la mediana en un eje y la
# amplitud interna en el otro.

rango = celdas_comuna.groupby("comuna")["distancia_metro"].agg(
    mediana="median",
    p10=lambda d: d.quantile(0.1),
    p90=lambda d: d.quantile(0.9),
    celdas="size",
)
rango["amplitud"] = rango["p90"] - rango["p10"]
rango = rango[rango["celdas"] >= 10].join(por_comuna[["poblacion"]], how="inner")

print(f"\nComunas con diez celdas o más: {len(rango)}")
print(f"Amplitud entre el 10% más cerca y el 10% más lejos de sus celdas: "
      f"mediana {miles(rango['amplitud'].median())} m, "
      f"máxima {miles(rango['amplitud'].max())} m")

# %%
fig, ax = plt.subplots(figsize=(7.4, 4.0))

ax.scatter(rango["mediana"], rango["amplitud"],
           s=rango["poblacion"] / 1500, color=AZUL, alpha=0.45,
           edgecolor=AZUL, linewidth=0.6)

# Se rotulan los dos extremos del argumento: las comunas de mayor amplitud y las
# más compactas. `adjust_text` las separa cuando quedan encima una de otra.
destacadas = list(rango.nlargest(4, "amplitud").index) + list(
    rango.nsmallest(2, "amplitud").index
)
etiquetas = [
    ax.text(rango.loc[comuna, "mediana"], rango.loc[comuna, "amplitud"], comuna,
            fontsize=7, color=AZUL)
    for comuna in destacadas
]
adjust_text(etiquetas, ax=ax, expand=(1.4, 1.6),
            arrowprops={"arrowstyle": "-", "color": GRIS, "linewidth": 0.6})
ax.margins(x=0.1)

ax.set_xlabel("mediana de la distancia al Metro de sus celdas (m)")
ax.set_ylabel("amplitud entre el 10% más cerca\ny el 10% más lejos (m)")
ax.xaxis.set_major_formatter(MILES)
ax.yaxis.set_major_formatter(MILES)
ax.set_title("Distancia al Metro dentro de cada comuna, mediana y amplitud",
             fontsize=10)

# El tamaño codifica población, así que necesita su propia referencia.
for referencia in (100_000, 400_000):
    ax.scatter([], [], s=referencia / 1500, color=AZUL, alpha=0.45,
               edgecolor=AZUL, linewidth=0.6,
               label=f"{miles(referencia)} habitantes")
ax.legend(fontsize=7, frameon=False, loc="upper left", labelspacing=1.2,
          borderpad=0.8)

fig.savefig("images/07s-dispersion-comunal.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 10: hasta dónde llegamos y qué sigue
#
# Las tres tareas de la propuesta se pueden hacer con estos datos:
#
#   1. Medir la demanda y la población de cada sector: la demanda sale de un
#      spatial join entre los viajes y la grilla (parte 3) y la población se une
#      por el identificador de celda, sin repartir nada.
#   2. Comparar la cobertura de 2012 con la de hoy: sale de un buffer, una
#      unión y una intersección sobre las mismas celdas (partes 4 a 6).
#   3. Identificar los sectores que siguen fuera: quedan 119, con su demanda y
#      su población (parte 8).
#
# El proyecto es factible. Lo que falta es el orden de prioridad que pide la
# propuesta, y para construirlo hay que encontrar qué distingue a un sector
# pendiente de otro. Tres lugares donde buscarlo:
#
#   - **Quién vive en los sectores pendientes.** El censo trae el medio de
#     transporte al trabajo, el hacinamiento y la composición etaria de cada
#     celda. Si la población de los sectores pendientes depende más del
#     transporte público que la de los que recibieron Metro, la brecha no es
#     solo de cobertura.
#   - **Si los pendientes forman corredor o están dispersos.** Una línea de
#     Metro necesita demanda alineada; los sectores sueltos piden otra
#     respuesta. El mapa de la parte 8 ya insinúa las dos situaciones y falta
#     medirlas, por ejemplo con la distancia entre celdas pendientes vecinas.
#   - **En qué punta del día se concentra su demanda.** Los sectores cuya
#     demanda sale en la mañana son origen de viajes y los de la tarde son
#     destino, y eso cambia qué infraestructura les sirve.
#
# Los límites que el hito 2 declara:
#
#   - La demanda es de 2012 y la población de 2024. La comparación mide si la
#     ampliación fue hacia donde había demanda antes de construirla, no si hoy
#     esa demanda sigue igual.
#   - La red de 2012 se reconstruye a nivel de línea, así que las estaciones que
#     las otras líneas agregaron después quedan contadas como si ya existieran.
#   - El área de servicio se construye con círculos, es decir, con distancia en
#     línea recta. Caminando la distancia es mayor, porque hay que seguir las
#     calles y cruzar los ríos por los puentes.
#   - La encuesta es una muestra: 360 celdas tienen población y ningún viaje
#     encuestado, así que una celda con pocos viajes describe más a los hogares
#     encuestados que al sector.
