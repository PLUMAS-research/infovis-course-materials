# %%
"""Segunda sesión de código: cuatro datasets, un solo vocabulario.

Cargamos un ejemplo de cada tipo de dataset (tabla, red, campo y geometría) y
describimos los cuatro con los mismos términos: qué es un ítem, qué atributos
tiene y de qué tipo es cada atributo. Al final derivamos una red desde la
tabla, para mostrar que el tipo no es una propiedad fija de los datos sino una
decisión de quien los modela.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import rasterio
from chiricoca.geo.figures import figure_from_geodataframe
from chiricoca.maps import choropleth_map
from rasterio.plot import plotting_extent

from visutils.estilo import AZUL, MAGENTA, estilo_curso
from visutils.general import descargar_datos

estilo_curso()

carpeta = descargar_datos("tipos-de-dataset.tgz")

# %%
# PARTE 1: la tabla
#
# Viajes declarados en la Encuesta Origen-Destino de Santiago 2012. Un ítem es
# un viaje: una persona que se movió de un lugar a otro con un propósito.

viajes = pd.read_parquet(carpeta / "eod-viajes.parquet")

print(f"Ítems (filas): {len(viajes):,}")
print(f"Atributos (columnas): {len(viajes.columns)}")
print()
print(viajes.head())

# %%
# PARTE 2: los tipos de atributo
#
# El tipo de un atributo no es su tipo de dato en pandas. Es qué operaciones
# tienen sentido sobre él, y eso decide qué codificaciones visuales sirven.
#
#   categórico    solo igualdad. No hay orden ni aritmética.
#   ordinal       hay orden, pero las diferencias no son comparables.
#   cuantitativo  hay orden y aritmética: restar y promediar tiene sentido.
#   cíclico       hay orden, pero después del último valor viene el primero.

print(viajes.dtypes)

# Categórico: el propósito del viaje. Ninguna categoría es mayor que otra.
print("\nPropósito (categórico):")
print(viajes["proposito"].value_counts().head(6))

# Ordinal: el período del día. Hay un orden temporal, pero los períodos no
# duran lo mismo, así que restar dos períodos no da una cantidad de tiempo.
print("\nPeríodo (ordinal):")
print(viajes["periodo"].value_counts())

# Cuantitativo: la duración en minutos. Se puede promediar y restar.
print("\nDuración en minutos (cuantitativo):")
print(viajes["minutos"].describe())

# Cíclico: la hora de inicio. Entre las 23 y la 1 hay dos horas, aunque la
# resta dé 22.
print("\nHora de inicio (cíclico):")
print(viajes["hora_inicio"].value_counts().sort_index().head(5))

# %%
# PARTE 3: un atributo cíclico se grafica en coordenadas polares
#
# En un eje horizontal común, el final del día y el comienzo quedan en
# extremos opuestos, y la continuidad de la madrugada se rompe.

por_hora = viajes["hora_inicio"].value_counts().sort_index()
por_hora = por_hora.reindex(range(24), fill_value=0)

fig = plt.figure(figsize=(7, 2.8))
ax_lineal = fig.add_subplot(1, 2, 1)
ax_polar = fig.add_subplot(1, 2, 2, projection="polar")

por_hora.plot(ax=ax_lineal, color=AZUL)
ax_lineal.set_title("Eje lineal")
ax_lineal.set_xlabel("Hora de inicio")
ax_lineal.set_ylabel("Viajes")

# En el eje polar hay que cerrar la curva a mano: se repite el primer valor al
# final, si no queda un corte entre las 23 y las 0 horas.
angulos = np.linspace(0, 2 * np.pi, 24, endpoint=False)
ax_polar.plot(
    np.append(angulos, angulos[0]),
    np.append(por_hora.values, por_hora.values[0]),
    color=MAGENTA,
)
ax_polar.set_theta_zero_location("N")
ax_polar.set_theta_direction(-1)
ax_polar.set_xticks(angulos[::3])
ax_polar.set_xticklabels([f"{h}h" for h in range(0, 24, 3)])
ax_polar.set_yticklabels([])
ax_polar.set_title("Eje polar")

# En el eje polar la madrugada es continua y las dos puntas del día quedan
# visibles a la vez.
print(f"Hora con más viajes: {por_hora.idxmax()}h ({por_hora.max():,} viajes)")

# %%
# PARTE 4: la red
#
# Colaboraciones entre músicos de jazz: un enlace por cada par que tocó en una
# misma banda. Acá el ítem es doble: hay ítems nodo e ítems enlace, y ambos se
# guardan como tablas.

enlaces = pd.read_csv(carpeta / "jazz-enlaces.csv")
print(f"Enlaces (filas de la tabla de enlaces): {len(enlaces):,}")
print(enlaces.head())

red = nx.from_pandas_edgelist(enlaces, "musico_a", "musico_b")
print(f"\nNodos: {red.number_of_nodes()}")
print(f"Enlaces: {red.number_of_edges()}")
print(f"Densidad: {nx.density(red):.3f}")

# Lo que distingue a una red de una tabla es que los atributos de un nodo
# pueden depender de con quién está conectado. El grado, por ejemplo, no se
# lee en ninguna columna: se calcula recorriendo la estructura.
grados = pd.Series(dict(red.degree())).sort_values(ascending=False)
print("\nMúsicos con más colaboraciones:")
print(grados.head())

fig, ax = plt.subplots(figsize=(4, 2.5))
grados.plot(kind="hist", bins=25, color=AZUL, ax=ax)
ax.set_title("Colaboraciones por músico")
ax.set_xlabel("Grado (cantidad de colaboradores)")
ax.set_ylabel("Músicos")

# %%
# PARTE 5: el campo
#
# NDVI de Santiago en 2023: un valor continuo por celda de una grilla regular.
# El ítem es la celda, y su posición no es un atributo cualquiera, sino lo que
# define el dataset: las celdas vecinas miden lugares vecinos.

with rasterio.open(carpeta / "ndvi-santiago-2023.tif") as raster:
    ndvi = raster.read(1)
    extent = plotting_extent(raster)
    print(f"Grilla: {raster.height} filas por {raster.width} columnas")
    print(f"Celdas: {raster.height * raster.width:,}")
    print(f"Tamaño de celda: {abs(raster.transform.a):.0f} m")
    print(f"Sistema de coordenadas: {raster.crs}")

ndvi = np.where(np.isfinite(ndvi), ndvi, np.nan)
print(f"\nNDVI mínimo: {np.nanmin(ndvi):.2f}, máximo: {np.nanmax(ndvi):.2f}")
print(f"Celdas con vegetación (NDVI > 0,3): {np.nansum(ndvi > 0.3) / np.sum(np.isfinite(ndvi)):.1%}")

# Los extremos del rango los ocupan poquísimas celdas, así que usarlos como
# límites del color deja casi todo el mapa en un mismo tono. Recortar en los
# percentiles 2 y 98 reparte el color donde están los datos.
inferior, superior = np.nanpercentile(ndvi, [2, 98])
print(f"Rango de color usado: {inferior:.2f} a {superior:.2f}")

fig, axes = plt.subplots(1, 2, figsize=(7.5, 3))

imagen = axes[0].imshow(
    ndvi, cmap="BrBG", vmin=inferior, vmax=superior, extent=extent, aspect="auto"
)
axes[0].set_title("NDVI de Santiago, 2023")
axes[0].set_axis_off()
fig.colorbar(imagen, ax=axes[0], shrink=0.8, label="NDVI")

axes[1].hist(ndvi[np.isfinite(ndvi)].ravel(), bins=60, color=AZUL)
axes[1].axvline(0.3, color=MAGENTA, linestyle="--")
axes[1].set_title("Distribución del NDVI")
axes[1].set_xlabel("NDVI")
axes[1].set_ylabel("Celdas")

# La vecindad no hay que declararla en ninguna parte: está en los índices del
# arreglo. La celda [i, j] limita con [i-1, j] y con [i, j+1], y eso alcanza
# para calcular promedios locales, bordes o gradientes.
fila, columna = 600, 700
print(f"\nValor de la celda [{fila}, {columna}]: {ndvi[fila, columna]:.3f}")
vecindad = ndvi[fila - 1 : fila + 2, columna - 1 : columna + 2]
print(f"Promedio de su vecindad de 3 por 3: {np.nanmean(vecindad):.3f}")

# El mismo dato como tabla pierde esa vecindad: cada celda queda como una fila
# suelta y hay que reconstruir a mano quién está al lado de quién.

# %%
# PARTE 5b: un campo vectorial
#
# Un campo no siempre guarda un número por celda. El gradiente del NDVI es un
# campo vectorial sobre la misma grilla: en cada celda dice hacia dónde y con
# qué intensidad crece la vegetación. La grilla no cambia; lo que cambia es que
# el arreglo gana una dimensión.

dy, dx = np.gradient(ndvi)
campo = np.stack([dx, -dy], axis=-1)
magnitud = np.linalg.norm(campo, axis=-1)

print(f"Forma del campo escalar: {ndvi.shape}")
print(f"Forma del campo vectorial: {campo.shape}")
print(f"Magnitud media del gradiente: {np.nanmean(magnitud):.4f}")

# Para dibujar las flechas hay que submuestrear: una por celda son 1,6 millones
# y la figura se vuelve una mancha.
PASO = 40
filas = np.arange(0, ndvi.shape[0], PASO)
columnas = np.arange(0, ndvi.shape[1], PASO)
malla_x, malla_y = np.meshgrid(columnas, filas)

fig, axes = plt.subplots(1, 2, figsize=(7.5, 3))

axes[0].imshow(
    ndvi, cmap="BrBG", vmin=inferior, vmax=superior, aspect="auto", alpha=0.45
)
axes[0].quiver(
    malla_x,
    malla_y,
    campo[::PASO, ::PASO, 0],
    -campo[::PASO, ::PASO, 1],
    color=AZUL,
    scale=4,
    width=0.004,
)
axes[0].set_title("Gradiente del NDVI, una flecha cada 40 celdas")
axes[0].set_axis_off()

imagen = axes[1].imshow(magnitud, cmap="magma_r", vmax=np.nanpercentile(magnitud, 98), aspect="auto")
axes[1].set_title("Magnitud del gradiente")
axes[1].set_axis_off()
fig.colorbar(imagen, ax=axes[1], shrink=0.8)

# La magnitud es alta donde el NDVI cambia rápido de una celda a la siguiente,
# es decir en los bordes entre lo construido y lo vegetado.

# %%
# PARTE 6: la geometría
#
# Comunas de la Región Metropolitana. El ítem es la comuna y su atributo
# principal es la forma misma, que se puede dibujar de manera directa.

comunas = gpd.read_parquet(carpeta / "comunas-rm.parquet")

print(f"Ítems: {len(comunas)} comunas")
print(f"Sistema de coordenadas: EPSG:{comunas.crs.to_epsg()}")
print(comunas.drop(columns="geometry").head())

# Para calcular áreas hay que proyectar: en EPSG:4326 las coordenadas están en
# grados y un grado no mide lo mismo en todas partes. UTM 19S es la proyección
# métrica que corresponde a Chile central.
comunas["area_km2"] = comunas.to_crs(32719).area / 1e6
print("\nComunas más extensas:")
print(comunas.nlargest(5, "area_km2")[["comuna", "provincia", "area_km2"]])

fig, ax = figure_from_geodataframe(comunas, height=4)
choropleth_map(comunas, "area_km2", k=5, binning="quantiles", palette="PuBu", ax=ax)
ax.set_title("Superficie de las comunas de la Región Metropolitana")

# %%
# PARTE 7: los tipos no son fijos
#
# El mismo dataset puede modelarse de más de una manera, y la elección depende
# de la pregunta. Los viajes de la EOD son una tabla, pero si el ítem pasa a
# ser el par de comunas origen-destino, la misma información es una red.

flujos = (
    viajes.groupby(["comuna_origen", "comuna_destino"], observed=True)
    .size()
    .reset_index(name="viajes")
)
flujos = flujos[flujos["viajes"] >= 100]
print(f"Pares de comunas con 100 viajes o más: {len(flujos):,}")

red_comunas = nx.from_pandas_edgelist(
    flujos, "comuna_origen", "comuna_destino", edge_attr="viajes", create_using=nx.DiGraph
)
print(f"Nodos: {red_comunas.number_of_nodes()}")
print(f"Enlaces: {red_comunas.number_of_edges()}")

# Una pregunta que la tabla no responde de manera directa: qué comunas reciben
# viajes desde más orígenes distintos.
recibe_de = pd.Series(dict(red_comunas.in_degree())).sort_values(ascending=False)
print("\nComunas que reciben viajes desde más comunas distintas:")
print(recibe_de.head())

# Y la red se puede volver a unir con la geometría, porque los nodos son
# lugares. Ahí conviven tres tipos de dataset en una sola figura.
#
# El mapa se arma solo con las comunas que aparecen en la red. Si se dibujan
# las 52 de la región, las comunas rurales del sur y de la cordillera ocupan la
# mayor parte de la figura y los flujos quedan apretados en el centro.
con_flujos = comunas[comunas["comuna"].isin(red_comunas.nodes)]
centroides = con_flujos.set_index("comuna").to_crs(32719).geometry.centroid.to_crs(4326)
print(f"\nComunas dibujadas: {len(con_flujos)} de {len(comunas)}")

fig, ax = figure_from_geodataframe(con_flujos, height=5)
con_flujos.plot(color="#EDEDF2", edgecolor="white", linewidth=0.4, ax=ax)

# El grosor codifica la cantidad de viajes. La raíz cuadrada comprime la cola
# larga: sin ella, el par con más viajes se lleva toda la tinta.
maximo = flujos["viajes"].max()
for origen, destino, datos in red_comunas.edges(data=True):
    if origen == destino:
        continue
    a, b = centroides[origen], centroides[destino]
    ax.plot(
        [a.x, b.x],
        [a.y, b.y],
        color=MAGENTA,
        linewidth=3.5 * np.sqrt(datos["viajes"] / maximo),
        alpha=0.5,
        solid_capstyle="round",
    )

ax.set_title("Flujos de viajes entre comunas, EOD Santiago 2012")
ax.set_axis_off()

# %%
# PARTE 8: resumen
#
# Los cuatro datasets se describen con el mismo vocabulario, y lo que cambia
# es qué es un ítem y qué relación hay entre ítems.

resumen = pd.DataFrame(
    [
        ("tabla", "un viaje", "independientes", f"{len(viajes):,}"),
        ("red", "un músico", "explícita, por enlaces", f"{red.number_of_nodes():,}"),
        ("campo", "una celda", "implícita, por vecindad", f"{np.sum(np.isfinite(ndvi)):,}"),
        ("geometría", "una comuna", "implícita, por posición", f"{len(comunas):,}"),
    ],
    columns=["tipo", "un ítem es", "relación entre ítems", "ítems"],
)
print(resumen.to_string(index=False))

print(
    "\nLa pregunta que abre cualquier dataset es la misma: qué representa una "
    "fila, qué atributos tiene y de qué tipo es cada uno."
)
