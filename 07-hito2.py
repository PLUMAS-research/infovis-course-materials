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
ciudad. Los cálculos se hacen en metros y los mapas se dibujan en grados.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from adjustText import adjust_text
from chiricoca.colors import categorical_color_legend
from chiricoca.geo.figures import small_multiples_from_geodataframe
from chiricoca.geo.grid import count_in_grid, h3_grid_from_bounds
from chiricoca.geo.utils import (
    clip_area_geodataframe,
    clip_point_geodataframe,
    to_point_geodataframe,
)
from chiricoca.maps import bivariate_choropleth_map
from chiricoca.tables import barchart
from matplotlib.patches import Rectangle

from visutils.estilo import AZUL, DPI, GRIS, MAGENTA, estilo_curso
from visutils.general import descargar_datos
from visutils.graficos import (
    FORMATO_MILES,
    FORMATO_PORCENTAJE,
    coropleta,
    fondo_de_mapa,
    miles,
    porcentaje,
    raincloud,
)

estilo_curso()

# La EOD entrega las coordenadas en UTM 19 Sur, el sistema métrico de Chile
# central. EPSG:4326 son grados y sirve para desplegar.
CRS_METRICO = "EPSG:32719"
CRS_MAPA = "EPSG:4326"

# %%
# PARTE 1: los viajes y el área de estudio
#
# El proyecto usa tres fuentes: la encuesta dice dónde empezaban los viajes
# antes de la ampliación, el GTFS dónde está la red hoy y con qué líneas, y el
# censo dónde vive la gente ahora. Cada una se lee en la parte que la usa. Acá
# van los viajes y las comunas del censo, que definen el área de estudio.

carpeta_eod = descargar_datos("eod-geografia.tgz")
carpeta_comunas = descargar_datos("comunas-censo.tgz")

viajes = pd.read_parquet(carpeta_eod / "viajes.parquet")
comunas_censo = gpd.read_parquet(carpeta_comunas / "comunas-rm.parquet")

# %%
# De columnas numéricas a geometría. Sin un sistema de coordenadas, las
# coordenadas de la encuesta son dos números y nada más. Geopandas no reproyecta
# por su cuenta: una operación entre capas en sistemas distintos falla o entrega
# cualquier cosa.

origenes = to_point_geodataframe(
    viajes, "origen_x", "origen_y", crs=CRS_METRICO
).to_crs(CRS_MAPA)

# El recorte al área de estudio. Los viajes con coordenadas válidas no están
# todos en Santiago y la región llega hasta la cordillera. La caja está en
# grados, así que el recorte se hace antes de pasar a metros.
CAJA_URBANA = (-70.85, -33.65, -70.45, -33.30)

origenes = clip_point_geodataframe(origenes, CAJA_URBANA)
comunas = clip_area_geodataframe(comunas_censo, CAJA_URBANA)
comunas_m = comunas.to_crs(CRS_METRICO)

print(f"Viajes en el área de estudio: {miles(len(origenes))} de {miles(len(viajes))} "
      f"({porcentaje(len(origenes) / len(viajes), 1)}); comunas con geometría "
      f"inválida: {(~comunas.is_valid).sum()}")

# %%
# PARTE 2: el sector
#
# La comuna es la unidad de la discusión y es demasiado grande. La zonificación
# de la encuesta tampoco sirve para comparar, porque sus zonas van de 0,02 a
# 35,8 km2. Una grilla hexagonal da unidades que miden todas lo mismo.

# El nivel 8 da celdas de 0,64 km2, unos 800 metros de lado. Sin margen, la
# grilla no alcanza a cubrir el borde de la caja y los viajes que caen ahí se
# pierden.
GRILLA_NIVEL = 8
MARGEN = 0.02

grilla = h3_grid_from_bounds(np.array(CAJA_URBANA), extra_margin=MARGEN,
                             grid_level=GRILLA_NIVEL)

print(f"Comunas de {miles(comunas_m.area.min() / 1e6, 1)} a "
      f"{miles(comunas_m.area.max() / 1e6)} km2, contra {miles(len(grilla))} celdas de "
      f"{miles(grilla.to_crs(CRS_METRICO).area.mean() / 1e6, 2)} km2")

# %%
# PARTE 3: la demanda previa a la ampliación
#
# La encuesta es de 2012, cinco años antes de la primera línea nueva, así que
# describe la demanda que existía antes de la decisión. De los viajes interesa
# el que usa transporte público, que es el que una estación nueva podría captar.
#
# La demanda tampoco es la misma a toda hora. En la mañana los viajes salen de
# donde la gente vive y en la tarde de donde trabaja o estudia, así que el mapa
# de una punta no sirve para leer la otra.
PERIODOS = {"mañana": (6, 9), "tarde": (17, 20)}

origenes["publico"] = origenes["modo"].astype(str).str.contains("Bus|Metro")
for periodo, (desde, hasta) in PERIODOS.items():
    origenes[periodo] = origenes["publico"] & origenes["hora_inicio"].between(desde, hasta)

# `count_in_grid` hace el spatial join entre los viajes y la grilla y cuenta los
# viajes de cada celda. Con `agg` suma además otras columnas: la suma de una
# columna de verdadero o falso cuenta los viajes que cumplen la condición.
celdas = count_in_grid(
    origenes, column="viajes", grid=grilla,
    agg={"publico": "sum", "mañana": "sum", "tarde": "sum"},
).to_crs(CRS_METRICO)

print(f"Celdas con al menos un viaje: {miles(len(celdas))}; viajes en transporte "
      f"público: {miles(celdas['publico'].sum())} "
      f"({porcentaje(celdas['publico'].sum() / celdas['viajes'].sum(), 1)})")
for periodo, (desde, hasta) in PERIODOS.items():
    print(f"  entre las {desde} y las {hasta}: {miles(celdas[periodo].sum())}")

# %%
# La población de cada celda viene del censo, que la publica sobre esta misma
# grilla. Las dos capas se unen por el identificador de celda, sin reproyectar
# ni repartir nada.

carpeta_censo = descargar_datos("censo2024-asignacion-rm.tgz")
censo_h3 = pd.read_parquet(carpeta_censo / "asignaciones-h3-8.parquet")
censo_h3["poblacion"] = censo_h3["n_hombres"] + censo_h3["n_mujeres"]

celdas = celdas.join(censo_h3.set_index("h3_cell_id")[["poblacion"]])
celdas["poblacion"] = celdas["poblacion"].fillna(0)

print(f"Por celda: mediana de {miles(celdas['publico'].median())} viajes en "
      f"transporte público y {miles(celdas['poblacion'].median())} habitantes, de "
      f"{miles(celdas['poblacion'].sum())} en total")

# Una limitación que el hito declara: la encuesta es una muestra de hogares, y
# bajo este umbral no alcanza para describir una celda.
MINIMO_VIAJES = 30

print(f"Celdas con población y menos de {MINIMO_VIAJES} viajes encuestados: "
      f"{((celdas['poblacion'] > 0) & (celdas['viajes'] < MINIMO_VIAJES)).sum()}")

# %%
# Antes de construir nada más, una mirada a las variables que el proyecto usa.
# El hito 2 pide las distribuciones, y de ahí salen las decisiones que vienen
# después: qué modos entran, qué umbral de viajes por celda, qué hora.
#
# La exploración va en una fila de cuatro paneles: en una lámina con título, una
# figura ancha se escala hasta el ancho y su texto queda legible al proyectar.
# Los paneles son chicos, así que sus rótulos van más chicos que los del estilo
# del curso.

fig, axes = plt.subplots(1, 4, figsize=(7.4, 2.6))

# Cómo se viaja, que decide qué viajes entran en el análisis.
reparto = origenes["modo"].astype(str).value_counts(normalize=True).head(6) * 100
reparto = reparto.sort_values()
colores = [MAGENTA if publico else GRIS
           for publico in reparto.index.str.contains("Bus|Metro")]
reparto.plot.barh(ax=axes[0], color=colores, width=0.8)
axes[0].set(title="Modo declarado", xlabel="% de los viajes", ylabel="")

# Cuándo empiezan, que muestra las dos puntas del día.
origenes["hora_inicio"].plot.hist(ax=axes[1], bins=range(0, 25), color=AZUL)
axes[1].set(title="Hora de inicio del viaje", xlabel="hora de inicio", ylabel="",
            xticks=[0, 6, 12, 18, 24])
axes[1].yaxis.set_major_formatter(FORMATO_MILES)

# Las dos distribuciones por celda se cortan en su extremo derecho, así que
# la última barra acumula la cola. La línea punteada es la mediana.

# Cuánta demanda tiene cada celda, que decide el umbral del análisis.
celdas["publico"].clip(upper=200).plot.hist(ax=axes[2], bins=30, color=MAGENTA)
axes[2].axvline(celdas["publico"].median(), color="black", linestyle="--",
                linewidth=1)
axes[2].set(title="Viajes en transporte público", xlabel="viajes por celda",
            ylabel="")
axes[2].set_xticks([0, 100, 200], labels=["0", "100", "200+"])

# Cuánta gente vive en cada celda, que da el peso de cada una.
celdas["poblacion"].clip(upper=20_000).plot.hist(ax=axes[3], bins=30, color=AZUL)
axes[3].axvline(celdas["poblacion"].median(), color="black", linestyle="--",
                linewidth=1)
axes[3].set(title="Habitantes", xlabel="habitantes por celda", ylabel="")
axes[3].set_xticks([0, 10_000, 20_000], labels=["0", "10.000", "20.000+"])

for ax in axes:
    ax.title.set_fontsize(8)
    ax.xaxis.label.set_fontsize(7)
    ax.tick_params(labelsize=6)

fig.savefig("images/07s-exploracion.png", dpi=DPI, bbox_inches="tight")

# %%
# Los dos paneles comparten los cortes de color, porque la comparación entre
# ellos es el punto de la figura. Los cortes son los quintiles de las dos
# columnas juntas: `stack` las apila en una sola serie. `unique` descarta los
# cortes repetidos, que aparecen cuando muchas celdas tienen el mismo conteo.

cortes_demanda = (
    celdas[list(PERIODOS)].stack().quantile(np.linspace(0, 1, 6)).unique()
)

mapa = celdas.to_crs(CRS_MAPA)
fig, axes = small_multiples_from_geodataframe(comunas, len(PERIODOS), height=3.6,
                                              col_wrap=2)

for ax, (periodo, (desde, hasta)) in zip(axes, PERIODOS.items()):
    coropleta(mapa, periodo, ax, comunas, "viajes en transporte público",
              bins=cortes_demanda)
    ax.set_title(f"Punta de la {periodo} ({desde} a {hasta})", fontsize=9)

fig.suptitle("Viajes en transporte público por celda, según período del día",
             fontsize=11, y=1.07)
fig.savefig("images/07s-demanda.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 4: la red y su área de servicio
#
# El buffer devuelve todo lo que está a menos de cierta distancia de una
# geometría. Alrededor de una estación es el área desde la que se llega a pie, y
# `union_all` funde los círculos en una sola geometría sin solape.
#
# La red sale del GTFS del DTPM: las estaciones de Metro con las líneas que las
# sirven y los paraderos de bus. Se recortan a la misma caja y pasan a metros,
# porque todo lo que sigue mide distancias y áreas.

carpeta_paradas = descargar_datos("paradas.tgz")
estaciones = gpd.read_parquet(carpeta_paradas / "estaciones-metro.parquet")
paraderos = gpd.read_parquet(carpeta_paradas / "paraderos-bus.parquet")

estaciones = clip_point_geodataframe(estaciones, CAJA_URBANA).to_crs(CRS_METRICO)
paraderos = clip_point_geodataframe(paraderos, CAJA_URBANA).to_crs(CRS_METRICO)

# Distancia caminable hasta el transporte público, en metros. La planificación
# de transporte usa un cuarto de milla hasta un paradero y media milla hasta una
# estación, que redondeados son estos dos números.
RADIO_BUS = 400
RADIO_METRO = 800

area_metro = estaciones.buffer(RADIO_METRO)
servicio_metro = area_metro.union_all()
servicio_bus = paraderos.buffer(RADIO_BUS).union_all()

area_de_estudio = comunas_m.area.sum()
print(f"Los {len(area_metro)} círculos de {RADIO_METRO} m suman "
      f"{miles(area_metro.area.sum() / 1e6)} km2 y fundidos quedan en "
      f"{miles(servicio_metro.area / 1e6)} "
      f"({porcentaje(servicio_metro.area / area_de_estudio, 1)} del área de estudio)")
print(f"Área de servicio del bus a {RADIO_BUS} m: {miles(servicio_bus.area / 1e6)} km2 "
      f"({porcentaje(servicio_bus.area / area_de_estudio, 1)})")

# El bus cubre casi la ciudad entera, así que el acceso al bus no distingue un
# sector de otro. La pregunta se juega en el Metro.

# %%
# La red que existía cuando se hizo la encuesta sale de las líneas: las
# estaciones servidas solo por L3 o L6 no existían en 2012.
LINEAS_NUEVAS = {"L3", "L6"}

# Una estación es nueva cuando todas sus líneas son nuevas: `issubset` pregunta
# eso, si el conjunto de líneas que la sirven cabe dentro de L3 y L6.
nuevas = estaciones["lineas"].str.split(", ").apply(
    lambda lineas: set(lineas).issubset(LINEAS_NUEVAS)
)
servicio_2012 = estaciones[~nuevas].buffer(RADIO_METRO).union_all()

# `difference` deja lo que está en la primera geometría y no en la segunda.
ganado = servicio_metro.difference(servicio_2012)

print(f"Estaciones nuevas: {nuevas.sum()}; área de servicio de "
      f"{miles(servicio_2012.area / 1e6)} km2 en 2012 y {miles(servicio_metro.area / 1e6)} "
      f"hoy ({porcentaje(ganado.area / servicio_2012.area)} más)")

# La aproximación es a nivel de línea: las estaciones que las otras líneas
# agregaron después de 2012 quedan contadas como si ya existieran.

# %%
# El acercamiento es el centro de la ciudad, donde los círculos se solapan. Las
# comunas van en un gris más claro que el de las coropletas, para que se lea lo
# que va encima.
CENTRO = (-70.72, -33.50, -70.58, -33.40)
FONDO_CLARO = "#F4F4F7"

capas = {
    f"{len(estaciones)} círculos, uno por estación": area_metro,
    "La unión de los círculos": gpd.GeoSeries([servicio_metro], crs=CRS_METRICO),
}

fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2))

for ax, (titulo, capa) in zip(axes, capas.items()):
    fondo_de_mapa(ax, comunas, relleno=FONDO_CLARO)
    capa.to_crs(CRS_MAPA).plot(ax=ax, facecolor=MAGENTA, edgecolor=MAGENTA,
                               alpha=0.35, linewidth=0.5)
    estaciones.to_crs(CRS_MAPA).plot(ax=ax, color=AZUL, markersize=3, zorder=4)
    ax.set_xlim(CENTRO[0], CENTRO[2])
    ax.set_ylim(CENTRO[1], CENTRO[3])
    ax.set_title(titulo, fontsize=9)

fig.suptitle(f"Área a {RADIO_METRO} metros de una estación, antes y después de unirla",
             fontsize=11, y=1.06)
fig.savefig("images/07s-buffer.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 5: la cobertura de cada celda


def fraccion_cubierta(celdas, servicio):
    """Fracción de cada celda que queda dentro del área de servicio.

    La intersección es la parte que comparten dos geometrías, así que dividida
    por el área de la celda dice qué fracción de ella queda dentro. El resultado
    se recorta a uno: cuando la celda queda entera dentro, la división da
    1,0000000000000007 y ese sobrante rompe cualquier clasificación en rangos.
    """
    return (celdas.intersection(servicio).area / celdas.area).clip(0, 1)


celdas["cobertura_2012"] = fraccion_cubierta(celdas, servicio_2012)
celdas["cobertura_hoy"] = fraccion_cubierta(celdas, servicio_metro)

# %%
# El tamaño de la unidad decide qué mide esta fracción. Una celda de nivel 8
# mide unos 800 metros de lado y el radio del buffer son 800 metros, así que la
# celda entra casi entera o no entra.

for nivel in (7, 8, 9):
    grilla_nivel = h3_grid_from_bounds(np.array(CAJA_URBANA), extra_margin=MARGEN,
                                       grid_level=nivel)
    celdas_nivel = count_in_grid(origenes, column="viajes",
                                 grid=grilla_nivel).to_crs(CRS_METRICO)
    cobertura = fraccion_cubierta(celdas_nivel, servicio_metro)
    extremos = ((cobertura == 0) | (cobertura > 0.99)).mean()
    print(f"H3 nivel {nivel}: celdas de {miles(celdas_nivel.area.mean() / 1e6, 2)} km2, "
          f"cobertura 0 o 1 en el {porcentaje(extremos)}")

# Con unidades más chicas que el radio, la fracción se vuelve una pertenencia:
# dice si la celda está dentro del área de servicio, no cuánto. Por eso el
# análisis usa un umbral en vez de una escala continua: desde media celda, la
# mayoría de sus habitantes tiene la estación a distancia caminable.
DENTRO = 0.5

# %%
# El radio también decide cuántas celdas quedan dentro.
RADIOS = (400, 800, 1200)
CORTES = [0, 0.2, 0.4, 0.6, 0.8, 1.0]

mapa = celdas.to_crs(CRS_MAPA)
fig, axes = small_multiples_from_geodataframe(comunas, len(RADIOS), height=3.0,
                                              col_wrap=3)

for ax, radio in zip(axes, RADIOS):
    mapa["cobertura"] = fraccion_cubierta(celdas, estaciones.buffer(radio).union_all())
    coropleta(mapa, "cobertura", ax, comunas, "fracción de la celda cubierta",
              palette="Purples", bins=CORTES, formato=porcentaje)
    ax.set_title(f"radio = {miles(radio)} m, "
                 f"{porcentaje((mapa['cobertura'] >= DENTRO).mean())} de las celdas dentro",
                 fontsize=9)

fig.suptitle("Fracción de cada celda dentro del área de servicio del Metro",
             fontsize=11, y=1.08)
fig.savefig("images/07s-cobertura.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 6: qué cambió con la ampliación
#
# Con las dos coberturas, cada celda queda en uno de tres estados.
# `np.select` evalúa las condiciones en orden, así que una celda que ya tenía
# Metro en 2012 no se cuenta como ganada.

celdas["estado"] = np.select(
    [celdas["cobertura_2012"] >= DENTRO, celdas["cobertura_hoy"] >= DENTRO],
    ["Ya tenía Metro en 2012", "Ganó Metro con L3 y L6"],
    default="Sigue sin Metro",
)

# Las filas que responden la propuesta son dos: las celdas que ganaron Metro y
# las que siguen sin él, que son las que en 2012 estaban disponibles para
# recibirlo. La fila de las que ya lo tenían mezclaría el resultado con la red
# vieja.
resumen = celdas.groupby("estado").agg(
    celdas=("viajes", "size"),
    demanda_mediana=("publico", "median"),
    poblacion_mediana=("poblacion", "median"),
)
print(resumen.map(miles).to_string())

# %%
# Dos paneles, uno por momento: el mapa de la red de 2012 y el de hoy, con las
# celdas que se sumaron destacadas. Dos mapas lado a lado llenan la lámina, que
# uno solo deja a medio ancho. Las celdas fuera del área de servicio van en un
# gris intermedio entre el fondo y el azul.
FUERA = "#C9CBD8"

mapa = celdas.to_crs(CRS_MAPA)
fig, axes = small_multiples_from_geodataframe(comunas, 2, height=4.2, col_wrap=2)

for ax, momento in zip(axes, ("2012", "hoy")):
    dentro = mapa[mapa[f"cobertura_{momento}"] >= DENTRO]
    fondo_de_mapa(ax, comunas, relleno=FONDO_CLARO)
    mapa.plot(ax=ax, facecolor=FUERA, edgecolor="none")
    dentro.plot(ax=ax, facecolor=AZUL, edgecolor="none")
    ax.set_title(f"La red de {momento}, {miles(len(dentro))} celdas dentro", fontsize=9)

ganaron = mapa[mapa["estado"] == "Ganó Metro con L3 y L6"]
ganaron.plot(ax=axes[1], facecolor=MAGENTA, edgecolor="none")

leyenda = categorical_color_legend(
    axes[0],
    {"dentro del área de servicio": AZUL, "lo que sumaron la L3 y la L6": MAGENTA,
     "fuera": FUERA},
    loc="lower left", fontsize=7,
)
# La leyenda necesita fondo: el gris de "fuera" es el de las celdas que tiene
# debajo, y sin fondo ese cuadro desaparece.
leyenda.set_frame_on(True)
leyenda.get_frame().set(facecolor="white", edgecolor="none", alpha=0.9)

fig.suptitle("Celdas dentro del área de servicio, red de 2012 y red actual",
             fontsize=11, y=1.03)
fig.savefig("images/07s-estados.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 7: la comparación que responde la propuesta
#
# Entre las celdas que en 2012 no tenían Metro, las que después lo ganaron,
# ¿tenían más demanda que las que siguen sin él?

sin_metro_2012 = celdas[celdas["estado"] != "Ya tenía Metro en 2012"]

fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0))

for ax, columna, etiqueta, tope in (
    (axes[0], "publico", "viajes en transporte público, 2012", 200),
    (axes[1], "poblacion", "habitantes, Censo 2024", 25_000),
):
    raincloud(sin_metro_2012, columna, "estado",
              ["Ganó Metro con L3 y L6", "Sigue sin Metro"], ax)
    ax.set_xlim(0, tope)
    ax.set_xlabel(etiqueta, fontsize=8)
    ax.xaxis.set_major_formatter(FORMATO_MILES)
    ax.tick_params(labelsize=8)

# Los dos paneles tienen las mismas categorías, así que el segundo no repite sus
# nombres y gana ese ancho para los datos.
axes[1].tick_params(labelleft=False)

fig.suptitle("Demanda y población de las celdas sin Metro en 2012, según su cobertura "
             "actual", fontsize=11, y=1.06)
fig.savefig("images/07s-comparacion.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 8: los sectores que siguen fuera
#
# La tercera tarea pide identificar. Entre las celdas que siguen sin Metro, las
# que tienen al menos la demanda de la celda mediana que lo ganó son las
# candidatas.

# Cada celda se ubica en la comuna donde cae su centro, que en un hexágono
# siempre queda adentro. La comuna se usa acá y en la lectura comunal.
centros = gpd.GeoDataFrame(geometry=celdas.centroid, crs=CRS_METRICO)
celdas["comuna"] = gpd.sjoin(centros, comunas_m[["comuna", "geometry"]],
                             predicate="within")["comuna"]

umbral = resumen.loc["Ganó Metro con L3 y L6", "demanda_mediana"]

pendientes = celdas[
    (celdas["estado"] == "Sigue sin Metro") & (celdas["publico"] >= umbral)
]

print(f"Celdas sin Metro con {miles(umbral)} viajes o más: {len(pendientes)}, con "
      f"{miles(pendientes['publico'].sum())} viajes en transporte público y "
      f"{miles(pendientes['poblacion'].sum())} habitantes")

# %%
# El mapa va con las comunas al lado: en una lámina, un mapa solo ocupa el
# ancho que le permite su alto, y la mitad queda vacía. Las dos partes reparten
# las celdas en las mismas tres categorías, con los mismos colores.
COLOR_CATEGORIA = {
    "sin Metro y con demanda": MAGENTA,
    "sin Metro y con menos demanda": FUERA,
    "dentro del área de servicio": AZUL,
}

celdas["categoria"] = np.select(
    [celdas["cobertura_hoy"] >= DENTRO, celdas.index.isin(pendientes.index)],
    ["dentro del área de servicio", "sin Metro y con demanda"],
    default="sin Metro y con menos demanda",
)

mapa = celdas.to_crs(CRS_MAPA)
fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.8))

fondo_de_mapa(axes[0], comunas, relleno=FONDO_CLARO)
for categoria, color in COLOR_CATEGORIA.items():
    mapa[mapa["categoria"] == categoria].plot(ax=axes[0], facecolor=color,
                                              edgecolor="none")
leyenda = categorical_color_legend(axes[0], COLOR_CATEGORIA, loc="lower left",
                                   fontsize=7)
leyenda.set_frame_on(True)
leyenda.get_frame().set(facecolor="white", edgecolor="none", alpha=0.9)

# Las diez comunas con más celdas sin Metro y con demanda, más las que empatan
# con la décima. Cada barra suma el 100% de las celdas de su comuna, así que compara el reparto entre categorías
# y no el tamaño de la comuna; el número entre paréntesis es cuántas celdas
# están sin Metro y con demanda.
por_categoria = pd.crosstab(celdas["comuna"], celdas["categoria"])[list(COLOR_CATEGORIA)]
mas_pendientes = por_categoria.nlargest(10, "sin Metro y con demanda", keep="all")
mas_pendientes.index = [f"{comuna} ({n})"
                        for comuna, n in mas_pendientes["sin Metro y con demanda"].items()]

barchart(mas_pendientes, stacked=True, normalize=True, horizontal=True,
         sort_items="sin Metro y con demanda", sort_items_ascending=True,
         color=list(COLOR_CATEGORIA.values()), legend=False, ax=axes[1])
axes[1].xaxis.set_major_formatter(FORMATO_PORCENTAJE)
axes[1].set_xlabel("celdas de la comuna", fontsize=8)
axes[1].set_ylabel("")
axes[1].tick_params(labelsize=8)

fig.suptitle("Celdas por cobertura y demanda, en la ciudad y por comuna", fontsize=11,
             y=1.05)
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
      f"de {miles(total)} ({porcentaje(cubierta / total, 1)})")

por_comuna = celdas.groupby("comuna").agg(
    poblacion=("poblacion", "sum"),
    poblacion_cubierta=("poblacion_cubierta", "sum"),
)
por_comuna["cobertura_poblacion"] = (
    por_comuna["poblacion_cubierta"] / por_comuna["poblacion"]
)

# Las comunas del borde tienen parte de su población fuera del área de estudio,
# así que quedan fuera las que aportan poca.
MINIMO_POBLACION = 20_000
por_comuna = por_comuna[por_comuna["poblacion"] >= MINIMO_POBLACION]

mayores = por_comuna["cobertura_poblacion"].nlargest(3)
print(f"{len(por_comuna)} comunas con {miles(MINIMO_POBLACION)} habitantes o más, "
      f"{(por_comuna['cobertura_poblacion'] == 0).sum()} sin población cubierta; "
      "las más cubiertas son "
      + ", ".join(f"{comuna} ({porcentaje(valor)})" for comuna, valor in mayores.items()))

# %%
# El censo también dice en qué se va la gente al trabajo, así que la cobertura
# se contrasta con el uso declarado del transporte público: la fracción de
# quienes declaran uno de los cuatro medios que publica el censo y van en
# transporte público.
MODOS = ["transporte_publico", "transporte_auto", "transporte_camina",
         "transporte_bicicleta"]

por_comuna = por_comuna.join(comunas_censo.set_index("comuna")[MODOS])
por_comuna["uso_transporte_publico"] = (
    por_comuna["transporte_publico"] / por_comuna[MODOS].sum(axis=1)
)

correlacion = por_comuna["cobertura_poblacion"].corr(por_comuna["uso_transporte_publico"])
print(f"Correlación entre cobertura y uso declarado del transporte público: "
      f"{miles(correlacion, 2)}")

# %%
comunas_mapa = comunas.set_index("comuna")[["geometry"]].join(
    por_comuna[["cobertura_poblacion", "uso_transporte_publico"]], how="inner"
)

fig, ax = plt.subplots(figsize=(4.8, 5.0))
coropleta(comunas_mapa, "cobertura_poblacion", ax, comunas, "fracción de la población",
          palette="Purples", formato=porcentaje)
ax.set_title(f"Población a menos de {RADIO_METRO} m de una estación, por comuna",
             fontsize=10)

fig.savefig("images/07s-comunal.png", dpi=DPI, bbox_inches="tight")

# %%
# Un mapa bivariado cruza dos variables en un solo color. Cada variable se corta
# en tercios entre las 38 comunas, y la combinación de los dos tercios da uno de
# nueve colores: la esquina que interesa es la de mucho uso del transporte
# público y poco acceso al Metro.
_, cortes_uso = pd.qcut(comunas_mapa["uso_transporte_publico"], 3, retbins=True)
_, cortes_acceso = pd.qcut(comunas_mapa["cobertura_poblacion"], 3, retbins=True)

tercio_uso = pd.cut(comunas_mapa["uso_transporte_publico"], cortes_uso, labels=False,
                    include_lowest=True)
tercio_acceso = pd.cut(comunas_mapa["cobertura_poblacion"], cortes_acceso,
                       labels=False, include_lowest=True)
mucho_uso_poco_acceso = comunas_mapa.index[(tercio_uso == 2) & (tercio_acceso == 0)]
poco_uso_mucho_acceso = comunas_mapa.index[(tercio_uso == 0) & (tercio_acceso == 2)]

print(f"Más uso y menos acceso: {', '.join(mucho_uso_poco_acceso)}; menos uso y más "
      f"acceso: {', '.join(poco_uso_mucho_acceso)}")

# %%
# El diagrama de dispersión es la leyenda del mapa: el plano de las dos
# variables pintado con los mismos nueve colores, con cada comuna como un punto.
fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.8))

# Las comunas fuera del análisis van en blanco: el color de poco uso y poco
# acceso ya es un gris claro, y sobre el fondo gris de los otros mapas se
# confundiría con ellas.
fondo_de_mapa(axes[0], comunas, relleno="white")
_, paleta, _ = bivariate_choropleth_map(
    comunas_mapa, "uso_transporte_publico", "cobertura_poblacion",
    binning="quantiles", k=3, legend=False, edgecolor="white", linewidth=0.4,
    ax=axes[0],
)

# Los rectángulos van de un corte al siguiente; los de los bordes llegan hasta
# el límite del eje. `paleta[j, i]` es el color del tercio i del uso y el tercio
# j del acceso.
LIMITES_USO = (0.1, 0.8)
LIMITES_ACCESO = (-0.05, 0.95)
bordes_uso = [LIMITES_USO[0], *cortes_uso[1:-1], LIMITES_USO[1]]
bordes_acceso = [LIMITES_ACCESO[0], *cortes_acceso[1:-1], LIMITES_ACCESO[1]]
for i in range(3):
    for j in range(3):
        axes[1].add_patch(Rectangle(
            (bordes_uso[i], bordes_acceso[j]), bordes_uso[i + 1] - bordes_uso[i],
            bordes_acceso[j + 1] - bordes_acceso[j], color=paleta[j, i], zorder=0,
        ))

axes[1].scatter(comunas_mapa["uso_transporte_publico"], comunas_mapa["cobertura_poblacion"],
                s=14, color=AZUL, edgecolor="white", linewidth=0.5, zorder=2)

etiquetas = [axes[1].text(comunas_mapa.loc[comuna, "uso_transporte_publico"],
                          comunas_mapa.loc[comuna, "cobertura_poblacion"], comuna,
                          fontsize=7, color=AZUL)
             for comuna in [*mucho_uso_poco_acceso, *poco_uso_mucho_acceso]]
adjust_text(etiquetas, ax=axes[1], expand=(1.3, 1.6),
            arrowprops={"arrowstyle": "-", "color": AZUL, "linewidth": 0.5})

axes[1].set(xlim=LIMITES_USO, ylim=LIMITES_ACCESO)
axes[1].grid(False)
axes[1].xaxis.set_major_formatter(FORMATO_PORCENTAJE)
axes[1].yaxis.set_major_formatter(FORMATO_PORCENTAJE)
axes[1].set_xlabel("va al trabajo en transporte público", fontsize=8)
axes[1].set_ylabel(f"vive a menos de {RADIO_METRO} m de una estación", fontsize=8)
axes[1].tick_params(labelsize=7)

fig.suptitle("Uso del transporte público y acceso al Metro, por comuna", fontsize=11,
             y=1.05)
fig.savefig("images/07s-bivariado.png", dpi=DPI, bbox_inches="tight")

# %%
# Cada celda tiene su distancia al Metro, y la mediana comunal las resume en un
# número que esconde cuánto varían dentro de la comuna.

cercanas = gpd.sjoin_nearest(centros, estaciones[["geometry"]], distance_col="distancia")
# Una celda con dos estaciones a la misma distancia aparece dos veces.
celdas["distancia_metro"] = cercanas.loc[~cercanas.index.duplicated(), "distancia"]

comunas_mapa["distancia_mediana"] = celdas.groupby("comuna")["distancia_metro"].median()

# La comuna donde más varía la distancia entre sus celdas.
distancias = (
    celdas[celdas["comuna"].isin(comunas_mapa.index)]
    .groupby("comuna")["distancia_metro"].agg(["min", "median", "max"])
)
comuna_variable = (distancias["max"] - distancias["min"]).idxmax()
print(f"En {comuna_variable} la mediana es de "
      f"{miles(distancias.loc[comuna_variable, 'median'])} m, y sus celdas van de "
      f"{miles(distancias.loc[comuna_variable, 'min'])} a "
      f"{miles(distancias.loc[comuna_variable, 'max'])} m")

# %%
# Los dos mapas usan los mismos cortes, que se duplican desde la distancia
# caminable: 800 metros, 1,6 km, 3,2 km y 6,4 km. La paleta va invertida para
# que el morado oscuro signifique cerca del Metro, como en el mapa de cobertura.
CORTES_DISTANCIA = [0, 800, 1_600, 3_200, 6_400, celdas["distancia_metro"].max()]

mapa = celdas.to_crs(CRS_MAPA)
fig, axes = small_multiples_from_geodataframe(comunas, 2, height=4.2, col_wrap=2)

for ax, capa, columna, titulo in (
    (axes[0], comunas_mapa, "distancia_mediana", "Mediana de cada comuna"),
    (axes[1], mapa, "distancia_metro", "Cada celda"),
):
    coropleta(capa, columna, ax, comunas, "metros hasta la estación más cercana",
              palette="Purples_r", bins=CORTES_DISTANCIA)
    ax.set_title(titulo, fontsize=9)

fig.suptitle("Distancia a la estación de Metro más cercana, por comuna y por celda",
             fontsize=11, y=1.06)
fig.savefig("images/07s-distancia.png", dpi=DPI, bbox_inches="tight")

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
#   - Quién vive en los sectores pendientes. El censo trae el medio de
#     transporte al trabajo, el hacinamiento y la composición etaria de cada
#     celda. Si la población de los sectores pendientes depende más del
#     transporte público que la de los que recibieron Metro, la brecha no es
#     solo de cobertura.
#   - Si los pendientes forman corredor o están dispersos. Una línea de Metro
#     necesita demanda alineada; los sectores sueltos piden otra respuesta. El
#     mapa de la parte 8 ya muestra las dos situaciones y falta medirlas, por
#     ejemplo con la distancia entre celdas pendientes vecinas.
#   - En qué punta del día se concentra su demanda. Los sectores cuya demanda
#     sale en la mañana son origen de viajes y los de la tarde son destino, y
#     eso cambia qué infraestructura les sirve.
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
#   - La encuesta es una muestra: 360 celdas con población tienen menos de
#     treinta viajes encuestados (parte 3), así que en ellas la demanda describe
#     más a los hogares encuestados que al sector.
