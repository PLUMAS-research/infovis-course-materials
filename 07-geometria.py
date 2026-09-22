# %%
"""Apéndice de geografía: geometría, joins y grillas.

La sesión de mapas dibuja una geometría que ya existe y la clase del hito 2 la
construye a medida que la necesita. Este script recorre esas operaciones
sueltas: medir, derivar una geometría de otra, unir dos capas y cambiar la
unidad sobre la que se agregan los datos.

Los datos son los del proyecto de la clase del hito 2:

  Situación. La Encuesta Origen-Destino 2012 registra dónde empieza cada viaje
  en Santiago y en qué modo. El GTFS del DTPM entrega la ubicación de las
  estaciones de Metro y de los paraderos de bus.

  Complicación. El acceso al Metro se describe por comuna, y la comuna es una
  unidad demasiado grande: dentro de una misma comuna hay zonas a 300 metros de
  una estación y otras a tres kilómetros.

  Propuesta. Comparar el acceso al Metro entre zonas de la ciudad, e
  identificar las zonas donde la demanda ocurre lejos de la red.

Acá cada operación se muestra por separado, con lo que hay que revisar al
usarla.
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from chiricoca.geo.figures import small_multiples_from_geodataframe
from chiricoca.geo.grid import count_in_grid, h3_grid_from_bounds
from chiricoca.geo.utils import (
    clip_area_geodataframe,
    clip_point_geodataframe,
    to_point_geodataframe,
)
from chiricoca.colors import colormap_from_palette
from chiricoca.maps import choropleth_map, dot_map, geographical_scale
from chiricoca.tables import barchart
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
from shapely import get_num_coordinates, make_valid
from shapely.geometry import Polygon

from visutils.estilo import AZUL, DPI, GRIS, MAGENTA, estilo_curso
from visutils.general import descargar_datos

estilo_curso()

# La EOD entrega las coordenadas en UTM 19 Sur, el sistema métrico de Chile
# central. EPSG:4326 son grados y sirve para desplegar.
CRS_METRICO = "EPSG:32719"
CRS_MAPA = "EPSG:4326"

# El área de estudio de la encuesta, la misma caja de la sesión de mapas.
CAJA_URBANA = (-70.85, -33.65, -70.45, -33.30)

# La latitud del centro de la ciudad, para pasar grados a metros en las barras
# de escala de los mapas dibujados en EPSG:4326.
LATITUD_SANTIAGO = -33.45


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


def barra_de_rangos(ax, bordes, palette, etiqueta):
    """Barra de color por clases, con un bloque del mismo ancho por clase.

    La barra que trae la coropleta ubica cada corte según su valor, y en una
    distribución sesgada los cortes bajos quedan tan juntos que sus rótulos se
    encabalgan. `spacing="uniform"` reparte los bloques por igual.
    """
    colores = colormap_from_palette(palette, n_colors=len(bordes) - 1)
    barra = ax.get_figure().colorbar(
        plt.cm.ScalarMappable(norm=BoundaryNorm(bordes, colores.N), cmap=colores),
        ax=[ax], orientation="horizontal", ticks=bordes, spacing="uniform",
        fraction=0.045, pad=0.02, shrink=0.9,
    )
    barra.set_label(etiqueta, fontsize=7)
    barra.ax.tick_params(labelsize=6)
    barra.ax.set_xticklabels([miles(b) for b in bordes])
    return barra


def mapa_de_conteo(capa, columna, ax, titulo, etiqueta="viajes", bins=None):
    """Coropleta con las comunas de fondo, la escala y la leyenda de clases.

    Con `bins` los cortes vienen de afuera, que es lo que hace falta cuando dos
    paneles muestran la misma variable sobre el mismo soporte.
    """
    comunas.plot(ax=ax, facecolor=GRIS, edgecolor="white", linewidth=0.3)
    # Los cuantiles reparten las unidades entre las clases, que en una variable
    # de conteos deja más contraste que los cortes naturales.
    clasificacion = ({"binning": "custom", "bins": bins} if bins is not None
                     else {"binning": "quantiles", "k": 5})
    _, info = choropleth_map(
        capa, columna, ax=ax, palette="Blues", edgecolor="none", linewidth=0,
        legend=None, **clasificacion,
    )
    comunas.boundary.plot(ax=ax, color="white", linewidth=0.3, zorder=3)
    barra_de_rangos(ax, info["bins"], "Blues", etiqueta)
    barra_de_escala(ax)
    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()


# %%
# PARTE 1: las capas y su sistema de coordenadas
#
# El análisis cruza dos fuentes: los viajes de la encuesta y la infraestructura
# del transporte público. Cada una llega en su propio formato y en su propio
# sistema de coordenadas, y nada se puede cruzar hasta que los dos coincidan.

carpeta_eod = descargar_datos("eod-geografia.tgz")
carpeta_paradas = descargar_datos("paradas.tgz")

viajes = pd.read_parquet(carpeta_eod / "viajes.parquet")
zonas = gpd.read_parquet(carpeta_eod / "zonas.parquet")
comunas = gpd.read_parquet(carpeta_eod / "comunas.parquet")
estaciones = gpd.read_parquet(carpeta_paradas / "estaciones-metro.parquet")
paraderos = gpd.read_parquet(carpeta_paradas / "paraderos-bus.parquet")

print(f"{len(viajes):,} viajes, {len(zonas)} zonas, {len(comunas)} comunas")
print(f"{len(estaciones)} estaciones de Metro, {len(paraderos):,} paraderos de bus")

# %%
# Los viajes traen las coordenadas como columnas numéricas y las paradas ya
# vienen con geometría. `to_point_geodataframe` arma los puntos y `crs` es lo
# que les da sentido: sin ese argumento son dos números y nada más.

origenes = to_point_geodataframe(viajes, "origen_x", "origen_y", crs=CRS_METRICO)

print(f"Orígenes: {origenes.crs.to_string()}")
print(f"Estaciones: {estaciones.crs.to_string()}")

# Las dos capas viven en sistemas distintos, así que una de las dos tiene que
# moverse antes de cualquier operación. Geopandas no reproyecta por su cuenta y
# una operación entre capas en sistemas distintos falla o entrega cualquier cosa.
origenes = origenes.to_crs(CRS_MAPA)

# %%
# PARTE 2: limpiar y filtrar
#
# Antes de medir hay que revisar que las geometrías existan, sean válidas y
# estén donde corresponde. Cada criterio deja un conteo, que es lo que el hito 2
# pide reportar.

print(f"Geometrías vacías: {origenes.geometry.is_empty.sum()}")
print(f"Polígonos válidos: zonas {zonas.is_valid.all()}, comunas {comunas.is_valid.all()}")

# %%
# Qué es un polígono inválido. El caso más común es la autointersección: el
# borde se cruza consigo mismo y el interior deja de estar definido, así que el
# área que reporta no significa nada. `make_valid` lo parte en piezas válidas.

mono = Polygon([(0, 0), (2, 2), (2, 0), (0, 2)])
reparado = make_valid(mono)

print(f"\nPolígono cruzado: válido={mono.is_valid}, área={mono.area}")
print(f"Reparado: tipo={reparado.geom_type}, piezas={len(reparado.geoms)}, "
      f"área={reparado.area}")

# Cualquier operación sobre una geometría inválida falla con TopologyException o,
# peor, entrega un resultado sin avisar.

# %%
# El recorte al área de estudio. Los viajes con coordenadas válidas no están
# todos en Santiago, y las comunas de la Región Metropolitana llegan hasta la
# cordillera.

origenes = clip_point_geodataframe(origenes, CAJA_URBANA)
estaciones = clip_point_geodataframe(estaciones, CAJA_URBANA)
paraderos = clip_point_geodataframe(paraderos, CAJA_URBANA)

# Para los polígonos hay que cortar la geometría, y no quedarse con la comuna
# entera si toca la caja.
comunas = clip_area_geodataframe(comunas, CAJA_URBANA)
zonas = clip_area_geodataframe(zonas, CAJA_URBANA)

print(f"\nDentro del área de estudio: {len(origenes):,} viajes de {len(viajes):,} "
      f"({len(origenes) / len(viajes):.1%})")
print(f"{len(estaciones)} estaciones, {len(paraderos):,} paraderos")
print(f"{len(comunas)} comunas, {len(zonas)} zonas")

# %%
# Las dos capas de infraestructura, sobre las comunas del área de estudio.

fig, axes = small_multiples_from_geodataframe(comunas, 2, height=4.0, col_wrap=2)

for ax, capa, color, tamano, titulo in (
    (axes[0], paraderos, AZUL, 0.6, f"{miles(len(paraderos))} paraderos de bus"),
    (axes[1], estaciones, MAGENTA, 6, f"{len(estaciones)} estaciones de Metro"),
):
    comunas.plot(ax=ax, facecolor="#F4F4F7", edgecolor="white", linewidth=0.4)
    dot_map(capa, ax=ax, size=tamano, color=color, alpha=0.6, add_legend=False)
    comunas.boundary.plot(ax=ax, color="white", linewidth=0.4, zorder=3)
    barra_de_escala(ax)
    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()

fig.suptitle("Paradas del transporte público de Santiago", fontsize=11, y=1.04)
fig.savefig("images/07g-paradas.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 3: medir
#
# Área, largo y distancia salen de la geometría, y las tres dependen del sistema
# de coordenadas. En grados el resultado no es una superficie ni una distancia.

santiago = comunas[comunas["comuna"] == "Santiago"]

# La primera línea emite un aviso de geopandas: el área de un polígono en un
# sistema de coordenadas geográficas sale en grados cuadrados, que no es una
# unidad de superficie y no se puede comparar entre latitudes.
print("Comuna de Santiago")
print(f"  área en EPSG:4326  = {santiago.area.iloc[0]:.6f} grados cuadrados")
print(f"  área en UTM 19 Sur = {santiago.to_crs(CRS_METRICO).area.iloc[0] / 1e6:.1f} km2")
print(f"  perímetro en UTM   = {santiago.to_crs(CRS_METRICO).length.iloc[0] / 1000:.1f} km")

# `length` sobre un polígono es el perímetro, y sobre una línea es su largo.

# %%
# Todo lo que sigue mide distancias y áreas, así que las capas pasan a UTM. Las
# versiones en grados quedan para dibujar.

origenes_m = origenes.to_crs(CRS_METRICO)
estaciones_m = estaciones.to_crs(CRS_METRICO)
paraderos_m = paraderos.to_crs(CRS_METRICO)
zonas_m = zonas.to_crs(CRS_METRICO)
comunas_m = comunas.to_crs(CRS_METRICO)

# La distancia entre dos geometrías es la distancia entre sus puntos más
# cercanos. Entre dos estaciones da el tramo que las separa.
baquedano = estaciones_m[estaciones_m["nombre"] == "Baquedano"].geometry.iloc[0]
u_chile = estaciones_m[estaciones_m["nombre"] == "Universidad de Chile"].geometry.iloc[0]

print(f"\nBaquedano a Universidad de Chile: {baquedano.distance(u_chile):,.0f} m")
print(f"La misma distancia en grados: "
      f"{estaciones.geometry.iloc[0].distance(estaciones.geometry.iloc[1]):.4f}")

# %%
# PARTE 4: derivar una geometría de otra
#
# Un polígono se puede resumir en un punto y se puede simplificar. Las dos
# operaciones aparecen todo el tiempo: la primera para ubicar una etiqueta o un
# nodo de un mapa de flujos, la segunda para dibujar más rápido.

centroides = zonas_m.geometry.centroid
representativos = zonas_m.geometry.representative_point()

fuera = ~centroides.within(zonas_m.geometry)
print(f"Zonas cuyo centroide cae fuera de la zona: {fuera.sum()} de {len(zonas_m)}")
print(f"Puntos representativos fuera: {(~representativos.within(zonas_m.geometry)).sum()}")

# El centroide es el promedio del área y no tiene por qué caer dentro: una zona
# en forma de C lo deja en el hueco. `representative_point` garantiza un punto
# interior, que es lo que hay que usar para etiquetar o para ubicar un glifo.

# %%
# La simplificación reduce los vértices moviendo cada uno hasta una tolerancia
# dada. La tolerancia está en las unidades del sistema de coordenadas, así que
# acá son metros.

vertices_originales = get_num_coordinates(comunas_m.geometry).sum()
print(f"\nVértices de las {len(comunas_m)} comunas: {vertices_originales:,}")

for tolerancia in (10, 50, 200, 1000):
    simplificadas = comunas_m.geometry.simplify(tolerancia)
    error = ((simplificadas.area - comunas_m.area).abs() / comunas_m.area).max()
    print(f"  tolerancia {tolerancia:>5} m: "
          f"{get_num_coordinates(simplificadas).sum():>7,} vértices, "
          f"error de área máximo {error:.2%}")

# %%
# La zona donde el centroide queda más lejos de su propia geometría. Son dos
# polígonos separados y el promedio del área cae en el espacio que los separa.

lejania = centroides.distance(zonas_m.geometry)
zona_ejemplo = zonas_m.loc[[lejania.idxmax()]]

print(f"\nZona {zona_ejemplo['zona'].iloc[0]} ({zona_ejemplo['comuna'].iloc[0]}): "
      f"{zona_ejemplo.geom_type.iloc[0]}, el centroide cae a "
      f"{lejania.max():.0f} m de la zona")

fig, ax = plt.subplots(figsize=(4.6, 3.4))

zona_ejemplo.plot(ax=ax, facecolor="#F4F4F7", edgecolor=AZUL, linewidth=0.8)
ax.scatter(*zona_ejemplo.geometry.centroid.iloc[0].coords[0], color=MAGENTA,
           s=40, zorder=3, label="centroide")
ax.scatter(*zona_ejemplo.geometry.representative_point().iloc[0].coords[0],
           color=AZUL, s=40, zorder=3, label="punto representativo")
ax.legend(fontsize=8, frameon=False, loc="lower center")
barra_de_escala(ax, crs=CRS_METRICO)
ax.set_axis_off()
ax.set_title(f"El centroide de la zona {zona_ejemplo['zona'].iloc[0]} cae fuera "
             "de la zona", fontsize=10)

fig.savefig("images/07g-centroide.png", dpi=DPI, bbox_inches="tight")

# %%
comuna_ejemplo = comunas_m[comunas_m["comuna"] == "Santiago"]

fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.9))

for ax, tolerancia in zip(axes, (0, 200, 1000)):
    borde = (comuna_ejemplo.geometry if tolerancia == 0
             else comuna_ejemplo.geometry.simplify(tolerancia))
    comuna_ejemplo.boundary.plot(ax=ax, color=GRIS, linewidth=2.5)
    borde.boundary.plot(ax=ax, color=MAGENTA, linewidth=0.8)
    barra_de_escala(ax, crs=CRS_METRICO)
    ax.set_axis_off()
    ax.set_aspect("equal")
    etiqueta = ("sin simplificar" if tolerancia == 0
                else f"tolerancia = {miles(tolerancia)} m")
    ax.set_title(f"{etiqueta}, {miles(get_num_coordinates(borde).sum())} vértices",
                 fontsize=9)

fig.suptitle("Borde de la comuna de Santiago", fontsize=11, y=1.04)
fig.savefig("images/07g-simplificacion.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 5: unir una tabla a una capa
#
# El join más frecuente no es espacial. La geometría vive en una capa y el dato
# en una tabla, y las dos comparten una columna: el código de la zona, el de la
# comuna, el rol de la propiedad.

viajes_por_zona = (
    origenes.groupby("zona_origen", observed=True).size().rename("viajes")
)

print(f"Zonas con viajes en la tabla: {len(viajes_por_zona)}")
print(f"Tipo de la llave: la capa trae {zonas['zona'].dtype} y la tabla "
      f"{viajes_por_zona.index.dtype}")

# Las dos llaves tienen que ser del mismo tipo. Si una es número y la otra
# texto, pandas rechaza el merge y el error se lee.
llave_texto = viajes_por_zona.rename_axis("zona_texto").reset_index()
llave_texto["zona_texto"] = llave_texto["zona_texto"].astype(str)

try:
    zonas.merge(llave_texto, left_on="zona", right_on="zona_texto", how="left")
except ValueError as problema:
    print(f"Merge rechazado: {problema}")

# El caso peligroso es el que no da error. Un código que viajó por un archivo
# donde quedó como decimal llega escrito "103.0", y contra "103" no calza
# ninguna fila: el merge corre, devuelve todo nulo y no avisa nada.
llave_decimal = llave_texto.assign(
    zona_texto=lambda x: x["zona_texto"].astype(float).astype(str)
)
prueba = zonas.assign(zona_texto=lambda x: x["zona"].astype(str)).merge(
    llave_decimal, on="zona_texto", how="left"
)

print(f"Filas que calzan entre '103' y '103.0': {prueba['viajes'].notna().sum()}")

# %%
zonas = zonas.merge(viajes_por_zona, left_on="zona", right_index=True, how="left")
zonas_m = zonas_m.merge(viajes_por_zona, left_on="zona", right_index=True, how="left")

print(f"\nZonas sin ningún viaje: {zonas['viajes'].isna().sum()} de {len(zonas)}")
print(f"Viajes que quedaron asignados: {miles(zonas['viajes'].sum())} "
      f"de {miles(len(origenes))}")

# `how="left"` conserva las zonas sin viajes y las deja en nulo, que es lo que
# corresponde: la zona existe y no aparece en la encuesta. Con `how="inner"`
# desaparecerían del mapa sin dejar rastro.
zonas["viajes"] = zonas["viajes"].fillna(0)
zonas_m["viajes"] = zonas_m["viajes"].fillna(0)

# %%
fig, ax = plt.subplots(figsize=(4.8, 5.0))

mapa_de_conteo(zonas, "viajes", ax, "Viajes que salen de cada zona")

fig.savefig("images/07g-join-zonas.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 6: unir dos capas por su ubicación
#
# Cuando no hay columna en común, la relación la da la geometría. El spatial
# join busca, para cada geometría de una capa, las de la otra que cumplen una
# relación: `within` para lo que está adentro, `intersects` para lo que se toca,
# `contains` al revés.

estaciones_comuna = gpd.sjoin(
    estaciones_m[["nombre", "lineas", "geometry"]],
    comunas_m[["comuna", "geometry"]],
    predicate="within",
    how="left",
)

por_comuna = estaciones_comuna["comuna"].value_counts()
viajes_comuna = origenes["comuna_origen"].value_counts()
sin_metro = viajes_comuna[
    viajes_comuna.index.isin(set(comunas_m["comuna"]) - set(por_comuna.index))
].head(6)

print(f"Estaciones sin comuna asignada: {estaciones_comuna['comuna'].isna().sum()}")
print(f"Comunas con estación: {len(por_comuna)} de {len(comunas_m)}")
print("Comunas sin estación con más viajes que salen de ellas:")
print(sin_metro.to_string())

# %%
# El resultado depende de por qué lado de la línea cayó el punto. Las estaciones
# de la Línea 5 corren bajo Vicuña Mackenna, que separa Macul de San Joaquín, y
# el `within` las asigna a una de las dos comunas por unos metros.

borde_comunal = comunas_m.boundary.union_all()
al_borde = estaciones_m.distance(borde_comunal)

print(f"\nEstaciones a menos de 50 m de un límite comunal: {(al_borde < 50).sum()}")
print(f"Estaciones a menos de 200 m: {(al_borde < 200).sum()}")

# %%
fig, ax = plt.subplots(figsize=(3.8, 3.2))

barchart(por_comuna.head(10).rename("estaciones").to_frame(), horizontal=True,
         sort_items=True, legend=False, ax=ax, color=AZUL)
ax.xaxis.set_major_locator(MaxNLocator(integer=True))
ax.set_xlabel("estaciones de Metro en la comuna")
ax.set_ylabel("")
ax.set_title("Las diez comunas con más estaciones", fontsize=10)

fig.savefig("images/07g-estaciones-comuna.png", dpi=DPI, bbox_inches="tight")

# El conteo por comuna es el dato con que se discute el acceso al Metro, y es
# justo el que la propuesta cuestiona: una comuna grande con dos estaciones en
# un extremo aparece con Metro.

# %%
# PARTE 7: el join que duplica filas
#
# Un punto cae en un solo polígono, pero un polígono toca varios. Entre dos
# capas de áreas el spatial join es de uno a muchos, así que el resultado trae
# más filas que la capa con que se empezó.

zonas_intersects = gpd.sjoin(
    zonas_m[["zona", "geometry"]], comunas_m[["comuna", "geometry"]],
    predicate="intersects",
)
zonas_within = gpd.sjoin(
    zonas_m[["zona", "geometry"]], comunas_m[["comuna", "geometry"]],
    predicate="within",
)

print(f"Zonas: {len(zonas_m)}")
print(f"Filas con predicate='intersects': {miles(len(zonas_intersects))}")
print(f"Filas con predicate='within':     {len(zonas_within)}")
print(f"Zonas que tocan más de una comuna: "
      f"{(zonas_intersects.groupby('zona').size() > 1).sum()}")

# `intersects` cuenta el roce de un borde, así que casi toda zona toca a sus
# vecinas. `within` pide que la zona quede entera adentro y deja fuera a las que
# cruzan un límite. Ninguno de los dos responde a qué comuna pertenece una zona.

# %%
# La respuesta necesita medir cuánto comparten. `overlay` corta las dos capas
# entre sí y devuelve un pedazo por cada par que se solapa, con la geometría de
# lo que comparten.

pedazos = gpd.overlay(
    zonas_m[["zona", "geometry"]], comunas_m[["comuna", "geometry"]],
    how="intersection", keep_geom_type=True,
)
pedazos["area"] = pedazos.area

comuna_de_zona = pedazos.sort_values("area").groupby("zona")["comuna"].last()

print(f"\nPedazos que deja el overlay: {miles(len(pedazos))}")
print(f"Zonas con comuna asignada por mayor superficie: {len(comuna_de_zona)}")
asignada = comuna_de_zona.reindex(zonas_m["zona"]).to_numpy()
print(f"Coincide con la columna comuna de la capa: "
      f"{(asignada == zonas_m['comuna'].to_numpy()).mean():.1%}")

# Un join sirve cuando se puede revisar: cuántas filas entraron, cuántas
# salieron, cuántas quedaron sin pareja y cuántas se duplicaron.

# %%
# PARTE 8: el join por cercanía
#
# `sjoin_nearest` busca para cada geometría la más cercana de otra capa y deja
# la distancia en la columna que se le pida. No necesita que las capas se toquen.

cercania = gpd.sjoin_nearest(
    origenes_m[["modo", "zona_origen", "geometry"]],
    estaciones_m[["nombre", "geometry"]].rename(columns={"nombre": "estacion"}),
    distance_col="distancia_metro",
)

print(f"Filas del resultado: {miles(len(cercania))} para {miles(len(origenes_m))} viajes")

# Un viaje equidistante de dos estaciones aparece en dos filas. Acá no ocurrió,
# y el filtro queda igual porque el join no garantiza una fila por viaje.
cercania = cercania[~cercania.index.duplicated()]

print(f"Distancia a la estación más cercana: "
      f"mediana {miles(cercania['distancia_metro'].median())} m, "
      f"máxima {miles(cercania['distancia_metro'].max())} m")
print(f"La estación más veces más cercana: "
      f"{cercania['estacion'].value_counts().index[0]} "
      f"({miles(cercania['estacion'].value_counts().iloc[0])} viajes)")

# %%
# PARTE 9: construir una grilla
#
# La zona y la comuna son unidades heredadas: alguien las dibujó con un criterio
# administrativo y sus tamaños son muy distintos entre sí. Una grilla es una
# unidad que no trae criterio propio, y donde cada celda mide lo mismo que las
# demás.

# `extra_margin` agranda la caja antes de teselarla. Sin ese margen, las
# observaciones que caen sobre el borde quedan fuera de la grilla.
MARGEN = 0.02

for nivel in (7, 8, 9):
    grilla_nivel = h3_grid_from_bounds(np.array(CAJA_URBANA), extra_margin=MARGEN,
                                       grid_level=nivel)
    area = grilla_nivel.to_crs(CRS_METRICO).area.mean() / 1e6
    print(f"H3 nivel {nivel}: {miles(len(grilla_nivel))} celdas de {area:.2f} km2")

print(f"Zonas de la encuesta: {len(zonas_m)}, de "
      f"{zonas_m.area.min() / 1e6:.2f} a {zonas_m.area.max() / 1e6:.1f} km2")

# H3 es una grilla hexagonal jerárquica: cada celda de un nivel se reparte en
# siete del nivel siguiente y todas las celdas de un nivel tienen casi la misma
# superficie. El hexágono tiene seis vecinos a la misma distancia; el cuadrado
# tiene cuatro por el lado y cuatro por la esquina, que quedan más lejos.

GRILLA_NIVEL = 8
grilla = h3_grid_from_bounds(np.array(CAJA_URBANA), extra_margin=MARGEN,
                             grid_level=GRILLA_NIVEL)
grilla_m = grilla.to_crs(CRS_METRICO)

# %%
# PARTE 10: contar sobre la grilla
#
# `count_in_grid` arma la grilla, hace el spatial join con los puntos y devuelve
# la grilla con la cuenta. El argumento `grid` recibe una grilla ya construida,
# que es lo que hace falta cuando dos conteos tienen que caer sobre el mismo
# soporte.

celdas = count_in_grid(origenes, grid_level=GRILLA_NIVEL, column="viajes", grid=grilla)

print(f"Celdas con al menos un viaje: {miles(len(celdas))} de {miles(len(grilla))}")
print(f"Viajes contados: {miles(celdas['viajes'].sum())} de {miles(len(origenes))}")
print(f"Viajes por celda: mediana {celdas['viajes'].median():.0f}, "
      f"máximo {miles(celdas['viajes'].max())}")

# %%
fig, axes = small_multiples_from_geodataframe(comunas, 3, height=3.0, col_wrap=3)

for ax, nivel in zip(axes, (7, 8, 9)):
    grilla_nivel = h3_grid_from_bounds(np.array(CAJA_URBANA), extra_margin=MARGEN,
                                       grid_level=nivel)
    conteo = count_in_grid(origenes, grid_level=nivel, column="viajes", grid=grilla_nivel)
    area = grilla_nivel.to_crs(CRS_METRICO).area.mean() / 1e6
    mapa_de_conteo(conteo, "viajes", ax,
                   f"H3 nivel {nivel}, celdas de {area:.2f} km$^2$")

fig.suptitle("Viajes que empiezan en cada celda", fontsize=11, y=1.04)
fig.savefig("images/07g-grilla.png", dpi=DPI, bbox_inches="tight")

# El nivel de la grilla decide el conteo igual que el ancho de banda decide un
# mapa de calor. Con celdas grandes el mapa se parece a la zonificación y con
# celdas chicas queda casi vacío, porque la encuesta es una muestra y no un
# censo de viajes.

# %%
# PARTE 11: cambiar de soporte
#
# Contar sobre la grilla necesita los puntos. Lo habitual es recibir el dato ya
# agregado en un soporte que no sirve: población por manzana, votos por local,
# viajes por zona. Pasarlo a otro soporte es repartirlo, y la forma más simple
# es repartirlo en proporción al área que comparten los dos.

pedazos = gpd.overlay(
    zonas_m[["zona", "viajes", "geometry"]], grilla_m.reset_index(),
    how="intersection", keep_geom_type=True,
)
pedazos["area"] = pedazos.area

# El peso es la fracción del área de la zona que cae en cada celda, así que los
# pesos de una misma zona suman uno y el total se conserva.
pedazos["peso"] = pedazos["area"] / pedazos.groupby("zona")["area"].transform("sum")

repartido = (
    pedazos.assign(viajes=lambda x: x["viajes"] * x["peso"])
    .groupby("h3_cell_id")["viajes"]
    .sum()
)

print(f"Total en las zonas: {miles(zonas_m['viajes'].sum())}")
print(f"Total repartido en la grilla: {miles(repartido.sum())}")

# %%
# El reparto supone que el dato se distribuye parejo dentro de la zona, y acá
# ese supuesto se puede revisar: los puntos existen, así que el conteo directo
# sobre la misma grilla dice lo que el reparto debería haber dado.

comparacion = (
    grilla_m.join(repartido.rename("repartido"))
    .join(celdas["viajes"].rename("directo"))
    .fillna({"repartido": 0, "directo": 0})
)
comparacion = comparacion[(comparacion["repartido"] > 0) | (comparacion["directo"] > 0)]

diferencia = (comparacion["repartido"] - comparacion["directo"]).abs()

print(f"\nCeldas comparables: {miles(len(comparacion))}")
print(f"Correlación entre el reparto y el conteo directo: "
      f"{comparacion['repartido'].corr(comparacion['directo']):.2f}")
print(f"Diferencia por celda: mediana {diferencia.median():.1f} viajes, "
      f"máxima {diferencia.max():.0f}")

# %%
# Los dos paneles de la grilla comparten los cortes, porque muestran la misma
# variable sobre el mismo soporte y la comparación es el punto de la figura.
cortes_grilla = np.unique(
    np.quantile(
        np.concatenate([comparacion["repartido"], comparacion["directo"]]),
        np.linspace(0, 1, 6),
    )
).round(0)

fig, axes = small_multiples_from_geodataframe(comunas, 3, height=3.0, col_wrap=3)

capas = (
    (zonas, "viajes", "Zonas de la encuesta", None),
    (comparacion.to_crs(CRS_MAPA), "repartido", "Repartido a la grilla por área",
     cortes_grilla),
    (celdas.to_crs(CRS_MAPA), "viajes", "Contado sobre la grilla", cortes_grilla),
)

for ax, (capa, columna, titulo, bins) in zip(axes, capas):
    mapa_de_conteo(capa, columna, ax, titulo, bins=bins)

fig.suptitle("Viajes que empiezan en cada unidad", fontsize=11, y=1.04)
fig.savefig("images/07g-interpolacion.png", dpi=DPI, bbox_inches="tight")

# El reparto por área inventa detalle donde la zona es grande, porque distribuye
# los viajes por toda su superficie aunque la gente viva en un borde. Donde las
# zonas son chicas, que es el centro de la ciudad, las dos versiones coinciden.

# %%
# PARTE 12: guardar lo construido
#
# Una capa se guarda con `to_file` o con `to_parquet`, y el formato decide qué
# se conserva. El curso usa parquet, que guarda la geometría en binario, escribe
# el CRS junto a los datos y conserva el tipo de cada columna.

SALIDA = Path("data") / "07-geometria"
SALIDA.mkdir(parents=True, exist_ok=True)

zonas.to_parquet(SALIDA / "zonas-con-viajes.parquet")
celdas.to_parquet(SALIDA / "celdas-h3.parquet")

print(f"Escrito en {SALIDA}")
print(f"  zonas-con-viajes.parquet: {len(zonas)} filas, "
      f"{(SALIDA / 'zonas-con-viajes.parquet').stat().st_size / 1e6:.1f} MB")

# Los otros formatos que aparecen en un proyecto:
#
#   - **GeoJSON** (`to_file`, extensión .geojson): texto plano, se abre en
#     cualquier editor y lo lee el navegador. Siempre en EPSG:4326.
#   - **Shapefile** (.shp): son varios archivos que viajan juntos, los nombres
#     de columna se cortan a diez caracteres y el CRS va en un archivo aparte
#     que a veces falta.
#   - **GeoPackage** (.gpkg): un archivo con varias capas adentro.
#
# `gpd.read_file` lee los tres y `gpd.read_parquet` el del curso.

# %%
# PARTE 13: dónde se usa cada operación
#
# La clase del hito 2 (`07-hito2.py`) construye el mismo caso y usa estas
# operaciones donde las necesita:
#
#   - `to_point_geodataframe` y `to_crs`, para preparar los viajes.
#   - `clip`, para el área de estudio.
#   - `merge` por llave, para unir una tabla de conteos a una capa.
#   - `sjoin`, para asignar cada viaje a su celda.
#   - `sjoin_nearest`, para la distancia a la estación más cercana.
#   - `h3_grid_from_bounds` y `count_in_grid`, para la unidad de análisis.
#   - `overlay` con reparto por área, cuando el dato viene en otro soporte.
#
# Las operaciones entre áreas (buffer, unión, intersección y diferencia) están
# en esa clase, que las necesita para construir el área de servicio.
