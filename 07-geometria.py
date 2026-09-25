# %%
"""Apéndice de geografía: geometría, joins y grillas.

La sesión de mapas dibuja una geometría que ya existe y la clase del hito 2 la
construye a medida que la necesita. Este script recorre esas operaciones
sueltas: medir, derivar una geometría de otra, unir dos capas y cambiar la
unidad sobre la que se agregan los datos.

Los datos son los del proyecto de la clase del hito 2:

  Situación. El Metro de Santiago inauguró la Línea 6 en 2017 y la Línea 3 en
  2019. La Encuesta Origen-Destino 2012 registra dónde empezaba cada viaje
  antes de esa ampliación, y el GTFS del DTPM entrega la ubicación de las
  estaciones de Metro y de los paraderos de bus.

  Complicación. La ampliación se discute por comuna, y a esa escala no se
  distingue si las líneas fueron hacia donde había demanda sin alternativa.

  Propuesta. Ordenar los sectores de la ciudad según la brecha entre su demanda
  de transporte público y su acceso al Metro, para orientar dónde conviene que
  la red siga creciendo.

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
from chiricoca.maps import dot_map
from chiricoca.tables import barchart
from matplotlib.ticker import MaxNLocator
from shapely import get_num_coordinates, make_valid
from shapely.geometry import Polygon

from visutils.estilo import AZUL, DPI, GRIS, MAGENTA, estilo_curso
from visutils.general import descargar_datos
from visutils.graficos import barra_de_escala, coropleta, fondo_de_mapa, miles, porcentaje

estilo_curso()

# La EOD entrega las coordenadas en UTM 19 Sur, el sistema métrico de Chile
# central. EPSG:4326 son grados y sirve para desplegar.
CRS_METRICO = "EPSG:32719"
CRS_MAPA = "EPSG:4326"

# El área de estudio de la encuesta, la misma caja de la sesión de mapas.
CAJA_URBANA = (-70.85, -33.65, -70.45, -33.30)

# El relleno de las comunas cuando el dato va encima en color.
FONDO_CLARO = "#F4F4F7"


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

# %%
# Los viajes traen las coordenadas como columnas numéricas y las paradas ya
# vienen con geometría. `to_point_geodataframe` arma los puntos y `crs` es lo
# que les da sentido: sin ese argumento son dos números y nada más.

origenes = to_point_geodataframe(viajes, "origen_x", "origen_y", crs=CRS_METRICO)

print(f"Orígenes en {origenes.crs.to_string()}, estaciones en {estaciones.crs.to_string()}")

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

print(f"Geometrías vacías: {origenes.geometry.is_empty.sum()}; polígonos válidos: "
      f"zonas {zonas.is_valid.all()}, comunas {comunas.is_valid.all()}")

# %%
# Qué es un polígono inválido. El caso más común es la autointersección: el
# borde se cruza consigo mismo y el interior deja de estar definido, así que el
# área que reporta no significa nada. `make_valid` lo parte en piezas válidas.

mono = Polygon([(0, 0), (2, 2), (2, 0), (0, 2)])
reparado = make_valid(mono)

print(f"Polígono cruzado: válido={mono.is_valid}, área={mono.area}; reparado: "
      f"{reparado.geom_type} de {len(reparado.geoms)} piezas, área={reparado.area}")

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

print(f"Dentro del área de estudio: {miles(len(origenes))} viajes de "
      f"{miles(len(viajes))} ({porcentaje(len(origenes) / len(viajes), 1)}), "
      f"{len(comunas)} comunas y {len(zonas)} zonas")

# %%
# Las dos capas de infraestructura, sobre las comunas del área de estudio.

fig, axes = small_multiples_from_geodataframe(comunas, 2, height=4.0, col_wrap=2)

for ax, capa, color, tamano, titulo in (
    (axes[0], paraderos, AZUL, 0.6, f"{miles(len(paraderos))} paraderos de bus"),
    (axes[1], estaciones, MAGENTA, 6, f"{len(estaciones)} estaciones de Metro"),
):
    fondo_de_mapa(ax, comunas, relleno=FONDO_CLARO)
    dot_map(capa, ax=ax, size=tamano, color=color, alpha=0.6, add_legend=False)
    ax.set_title(titulo, fontsize=9)

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
print(f"Comuna de Santiago: {miles(santiago.area.iloc[0], 6)} grados cuadrados en "
      f"EPSG:4326, {miles(santiago.to_crs(CRS_METRICO).area.iloc[0] / 1e6, 1)} km2 en "
      f"UTM 19 Sur y {miles(santiago.to_crs(CRS_METRICO).length.iloc[0] / 1000, 1)} km "
      "de perímetro")

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

print(f"Baquedano a Universidad de Chile: {miles(baquedano.distance(u_chile))} m")

# %%
# PARTE 4: derivar una geometría de otra
#
# Un polígono se puede resumir en un punto y se puede simplificar. Las dos
# operaciones aparecen todo el tiempo: la primera para ubicar una etiqueta o un
# nodo de un mapa de flujos, la segunda para dibujar más rápido.

centroides = zonas_m.geometry.centroid
representativos = zonas_m.geometry.representative_point()

fuera = ~centroides.within(zonas_m.geometry)
print(f"Zonas con el centroide fuera: {fuera.sum()} de {len(zonas_m)}; con el punto "
      f"representativo fuera: {(~representativos.within(zonas_m.geometry)).sum()}")

# El centroide es el promedio del área y no tiene por qué caer dentro: una zona
# en forma de C lo deja en el hueco. `representative_point` garantiza un punto
# interior, que es lo que hay que usar para etiquetar o para ubicar un glifo.

# %%
# La simplificación reduce los vértices moviendo cada uno hasta una tolerancia
# dada. La tolerancia está en las unidades del sistema de coordenadas, así que
# acá son metros.

vertices_originales = get_num_coordinates(comunas_m.geometry).sum()
print(f"Vértices de las {len(comunas_m)} comunas: {miles(vertices_originales)}")

for tolerancia in (10, 50, 200, 1000):
    simplificadas = comunas_m.geometry.simplify(tolerancia)
    error = ((simplificadas.area - comunas_m.area).abs() / comunas_m.area).max()
    print(f"  tolerancia de {miles(tolerancia)} m: "
          f"{miles(get_num_coordinates(simplificadas).sum())} vértices, "
          f"error de área máximo {porcentaje(error, 2)}")

# %%
# La zona donde el centroide queda más lejos de su propia geometría. Son dos
# polígonos separados y el promedio del área cae en el espacio que los separa.

lejania = centroides.distance(zonas_m.geometry)
zona_ejemplo = zonas_m.loc[[lejania.idxmax()]]

print(f"Zona {zona_ejemplo['zona'].iloc[0]} ({zona_ejemplo['comuna'].iloc[0]}): "
      f"{zona_ejemplo.geom_type.iloc[0]}, el centroide cae a "
      f"{miles(lejania.max())} m de la zona")

fig, ax = plt.subplots(figsize=(4.6, 3.4))

zona_ejemplo.plot(ax=ax, facecolor="#F4F4F7", edgecolor=AZUL, linewidth=0.8)
ax.scatter(*zona_ejemplo.geometry.centroid.iloc[0].coords[0], color=MAGENTA,
           s=40, zorder=3, label="centroide")
ax.scatter(*zona_ejemplo.geometry.representative_point().iloc[0].coords[0],
           color=AZUL, s=40, zorder=3, label="punto representativo")
ax.legend(fontsize=8, frameon=False, loc="lower center")
barra_de_escala(ax, CRS_METRICO)
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
    barra_de_escala(ax, CRS_METRICO)
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

print(f"Zonas sin ningún viaje: {zonas['viajes'].isna().sum()} de {len(zonas)}; "
      f"viajes asignados: {miles(zonas['viajes'].sum())} de {miles(len(origenes))}")

# `how="left"` conserva las zonas sin viajes y las deja en nulo, que es lo que
# corresponde: la zona existe y no aparece en la encuesta. Con `how="inner"`
# desaparecerían del mapa sin dejar rastro.
zonas["viajes"] = zonas["viajes"].fillna(0)
zonas_m["viajes"] = zonas_m["viajes"].fillna(0)

# %%
fig, ax = plt.subplots(figsize=(4.8, 5.0))

coropleta(zonas, "viajes", ax, comunas, "viajes")
ax.set_title("Viajes que salen de cada zona", fontsize=9)

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

print(f"Estaciones sin comuna asignada: {estaciones_comuna['comuna'].isna().sum()}; "
      f"comunas con estación: {len(por_comuna)} de {len(comunas_m)}. Las que no tienen "
      "y generan más viajes:")
print(sin_metro.to_string())

# %%
# El resultado depende de por qué lado de la línea cayó el punto. Las estaciones
# de la Línea 5 corren bajo Vicuña Mackenna, que separa Macul de San Joaquín, y
# el `within` las asigna a una de las dos comunas por unos metros.

borde_comunal = comunas_m.boundary.union_all()
al_borde = estaciones_m.distance(borde_comunal)

print(f"Estaciones a menos de 50 m de un límite comunal: {(al_borde < 50).sum()}; "
      f"a menos de 200 m: {(al_borde < 200).sum()}")

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

print(f"{len(zonas_m)} zonas: {miles(len(zonas_intersects))} filas con 'intersects' y "
      f"{len(zonas_within)} con 'within'; "
      f"{(zonas_intersects.groupby('zona').size() > 1).sum()} tocan más de una comuna")

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

asignada = comuna_de_zona.reindex(zonas_m["zona"]).to_numpy()
print(f"Comuna asignada por mayor superficie a {len(comuna_de_zona)} zonas, desde "
      f"{miles(len(pedazos))} pedazos; coincide con la columna de la capa en el "
      f"{porcentaje((asignada == zonas_m['comuna'].to_numpy()).mean(), 1)}")

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
    print(f"H3 nivel {nivel}: {miles(len(grilla_nivel))} celdas de {miles(area, 2)} km2")

print(f"Zonas de la encuesta: {len(zonas_m)}, de "
      f"{miles(zonas_m.area.min() / 1e6, 2)} a {miles(zonas_m.area.max() / 1e6, 1)} km2")

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
# `count_in_grid` hace el spatial join con los puntos y devuelve la grilla con
# la cuenta. El argumento `grid` recibe una grilla ya construida, que es lo que
# hace falta cuando dos conteos tienen que caer sobre el mismo soporte; sin él,
# la función arma una del nivel `grid_level`.

celdas = count_in_grid(origenes, column="viajes", grid=grilla)

print(f"Celdas con al menos un viaje: {miles(len(celdas))} de {miles(len(grilla))}, "
      f"con {miles(celdas['viajes'].sum())} de {miles(len(origenes))} viajes")

# %%
fig, axes = small_multiples_from_geodataframe(comunas, 3, height=3.0, col_wrap=3)

for ax, nivel in zip(axes, (7, 8, 9)):
    grilla_nivel = h3_grid_from_bounds(np.array(CAJA_URBANA), extra_margin=MARGEN,
                                       grid_level=nivel)
    conteo = count_in_grid(origenes, column="viajes", grid=grilla_nivel)
    area = grilla_nivel.to_crs(CRS_METRICO).area.mean() / 1e6
    coropleta(conteo, "viajes", ax, comunas, "viajes")
    ax.set_title(f"H3 nivel {nivel}, celdas de {miles(area, 2)} km$^2$", fontsize=9)

fig.suptitle("Viajes que empiezan en cada celda", fontsize=11, y=1.08)
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

print(f"Total en las zonas: {miles(zonas_m['viajes'].sum())}; repartido en la "
      f"grilla: {miles(repartido.sum())}")

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

print(f"Sobre {miles(len(comparacion))} celdas, correlación entre el reparto y el "
      f"conteo directo de {miles(comparacion['repartido'].corr(comparacion['directo']), 2)}; "
      f"diferencia por celda con mediana de {miles(diferencia.median(), 1)} viajes y "
      f"máximo de {miles(diferencia.max())}")

# %%
# Los dos paneles de la grilla comparten los cortes, porque muestran la misma
# variable sobre el mismo soporte y la comparación es el punto de la figura.
# El reparto deja decimales, así que los cortes se redondean: la escala muestra
# los mismos números con que el mapa asigna las clases.
cortes_grilla = (
    comparacion[["repartido", "directo"]].stack()
    .quantile(np.linspace(0, 1, 6)).round().unique()
)

fig, axes = small_multiples_from_geodataframe(comunas, 3, height=3.0, col_wrap=3)

capas = (
    (zonas, "viajes", "Zonas de la encuesta", None),
    (comparacion.to_crs(CRS_MAPA), "repartido", "Repartido a la grilla por área",
     cortes_grilla),
    (celdas.to_crs(CRS_MAPA), "viajes", "Contado sobre la grilla", cortes_grilla),
)

for ax, (capa, columna, titulo, bins) in zip(axes, capas):
    coropleta(capa, columna, ax, comunas, "viajes", bins=bins)
    ax.set_title(titulo, fontsize=9)

fig.suptitle("Viajes que empiezan en cada unidad", fontsize=11, y=1.08)
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
# La clase del hito 2 construye el mismo caso y usa estas operaciones donde las
# necesita:
#
#   - `to_point_geodataframe` y `to_crs`, para preparar los viajes.
#   - `clip`, para el área de estudio.
#   - `h3_grid_from_bounds` y `count_in_grid`, para la unidad de análisis y la
#     demanda de cada celda.
#   - `join` por llave, para unir la población del censo a cada celda.
#   - `sjoin`, para ubicar cada celda en su comuna.
#   - `sjoin_nearest`, para la distancia de cada celda a la estación más cercana.
#
# El reparto por área con `overlay` no le hace falta, porque el censo ya viene
# sobre la misma grilla. Haría falta si viniera por manzana.
#
# Las operaciones entre áreas (buffer, unión, intersección y diferencia) están
# en esa clase, que las necesita para construir el área de servicio.
