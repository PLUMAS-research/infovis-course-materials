"""Previsualizaciones de las fuentes de datos de la unidad 02.

Cada fuente que se presenta en clases lleva una imagen de lo que contiene. Las
que vienen de un sitio web se muestran con una captura; las que son datasets
descargables se muestran con un gráfico hecho desde los datos, que es lo que
construye este script.

Todos los mapas dibujan encima los bordes comunales. Sin ese contorno, una nube
de puntos sobre Santiago no se distingue de una nube de puntos sobre cualquier
otra ciudad.

Uso: uv run python figuras/02-fuentes.py
"""

# %%
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from chiricoca.base.paths import add_project_root
from chiricoca.geo.grid import h3_grid_from_ids
from rasterio.plot import plotting_extent

# Este script vive en una subcarpeta, así que hay que agregar la raíz del
# repositorio al path para poder importar visutils.
add_project_root(marker="pyproject.toml")

from visutils.estilo import AZUL, MAGENTA, estilo_curso  # noqa: E402
from visutils.general import descargar_archivo, descargar_datos  # noqa: E402

estilo_curso(dpi=300)

DIR_IMAGENES = Path("images")
DIR_IMAGENES.mkdir(exist_ok=True)

# Estos datasets se comparten con el curso de datos geográficos, así que se
# bajan de su servidor con la URL completa.
GDS = "https://dcc.uchile.cl/~egraells/gds-data"

FIGSIZE = (3.4, 3.4)

# %%
# Las comunas de la Región Metropolitana son la capa de contexto de todos los
# mapas. Las de la periferia rural son enormes y comprimen el resto, así que
# los mapas se recortan al área donde efectivamente hay datos.
comunas = gpd.read_parquet(descargar_datos("tipos-de-dataset.tgz") / "comunas-rm.parquet")
print(f"Comunas de contexto: {len(comunas)}")


def contexto(ax, capa, margen=0.02):
    """Dibuja los bordes comunales y encuadra el mapa en la capa de datos."""
    # zorder alto: los bordes van encima de los datos, si no quedan tapados por
    # las celdas rellenas y dejan de servir para orientarse.
    comunas.to_crs(capa.crs).boundary.plot(ax=ax, color=AZUL, linewidth=0.25, zorder=3)
    x0, y0, x1, y1 = capa.total_bounds
    ancho, alto = x1 - x0, y1 - y0
    ax.set_xlim(x0 - margen * ancho, x1 + margen * ancho)
    ax.set_ylim(y0 - margen * alto, y1 + margen * alto)
    ax.set_axis_off()


def guardar(fig, nombre):
    fig.savefig(DIR_IMAGENES / nombre, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Escrito: images/{nombre}")


# %%
# Censo 2024: población por celda hexagonal de la Región Metropolitana.
censo = descargar_datos(f"{GDS}/censo2024-asignacion-rm.tgz")
celdas = pd.read_parquet(censo / "asignaciones-h3-8.parquet")
celdas["personas"] = celdas["n_hombres"] + celdas["n_mujeres"]
print(f"Censo 2024: {len(celdas):,} celdas, {celdas['personas'].sum():,.0f} personas")

grilla = h3_grid_from_ids(celdas["h3_cell_id"].tolist()).merge(
    celdas[["h3_cell_id", "personas"]], on="h3_cell_id"
)

fig, ax = plt.subplots(figsize=FIGSIZE)
grilla.plot(column="personas", cmap="PuBu", scheme="quantiles", k=6, linewidth=0, ax=ax, zorder=2)
contexto(ax, grilla)
ax.set_title("Población por celda H3", fontsize=8)
guardar(fig, "02-fuente-censo.png")

# %%
# SOSAFE: reportes ciudadanos de una quincena, con su categoría.
sosafe = descargar_datos(f"{GDS}/sosafe-clustering.tgz")
reportes = gpd.read_parquet(sosafe / "reportes-quincena.parquet")
print(f"SOSAFE: {len(reportes):,} reportes, {reportes['grupo'].nunique()} grupos")

fig, ax = plt.subplots(figsize=FIGSIZE)
reportes.plot(ax=ax, markersize=0.4, color=MAGENTA, alpha=0.35, zorder=2)
contexto(ax, reportes)
ax.set_title("Reportes de una quincena", fontsize=8)
guardar(fig, "02-fuente-sosafe.png")

# %%
# eBird: cada observación de ave en su punto, sin agregar a celdas. Así se ve
# que la cobertura sigue a los observadores y no al territorio.
ebird = descargar_datos(f"{GDS}/ebird-santiago-2024.tgz")
observaciones = pd.read_parquet(ebird / "observaciones.parquet")
aves = gpd.GeoDataFrame(
    observaciones,
    geometry=gpd.points_from_xy(observaciones["lon"], observaciones["lat"]),
    crs=4326,
)
print(f"eBird: {len(aves):,} observaciones, {aves['nombre_cientifico'].nunique()} especies")

fig, ax = plt.subplots(figsize=FIGSIZE)
aves.plot(ax=ax, markersize=0.3, color="#2E7D32", alpha=0.2, zorder=2)
contexto(ax, aves)
ax.set_title("Observaciones de aves, 2024", fontsize=8)
guardar(fig, "02-fuente-ebird.png")

# %%
# SINCA: material particulado fino diario en las estaciones de Santiago.
sinca = descargar_datos(f"{GDS}/sinca-santiago-2024.tgz")
pm25 = pd.read_parquet(sinca / "pm25-diario.parquet")
print(f"SINCA: {pm25['codigo'].nunique()} estaciones, {len(pm25):,} mediciones diarias")

fig, ax = plt.subplots(figsize=(3.8, 2.6))
for codigo, serie in pm25.groupby("codigo"):
    ax.plot(serie["fecha"], serie["pm25"], color=AZUL, alpha=0.4, linewidth=0.7)
ax.set_title("PM2.5 diario por estación", fontsize=8)
ax.set_ylabel(r"PM2.5 ($\mu$g/m$^3$)", fontsize=7)
ax.tick_params(labelsize=6)
for etiqueta in ax.get_xticklabels():
    etiqueta.set_rotation(30)
    etiqueta.set_ha("right")
guardar(fig, "02-fuente-sinca.png")

# %%
# Rasters de Sentinel-2 y VIIRS: dos campos sobre la misma ciudad.
ndvi_tif = descargar_archivo(f"{GDS}/ndvi-santiago-2023.tif")
luz_tif = descargar_archivo(f"{GDS}/luminosidad-santiago-2023.tif")

fig, axes = plt.subplots(1, 2, figsize=(5.2, 2.6))
for ax, ruta, cmap, borde, titulo in [
    (axes[0], ndvi_tif, "BrBG", AZUL, "NDVI, 30 m"),
    (axes[1], luz_tif, "inferno", "white", "Luminosidad, 500 m"),
]:
    with rasterio.open(ruta) as raster:
        capa = raster.read(1).astype(float)
        extent = plotting_extent(raster)
        limites = comunas.to_crs(raster.crs)
    capa = np.where(np.isfinite(capa), capa, np.nan)
    inferior, superior = np.nanpercentile(capa, [2, 98])
    ax.imshow(capa, cmap=cmap, vmin=inferior, vmax=superior, extent=extent, aspect="auto")
    # Sobre el mapa oscuro de luminosidad el borde azul no se ve: va en blanco.
    limites.boundary.plot(ax=ax, color=borde, linewidth=0.25, alpha=0.7)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_title(titulo, fontsize=8)
    ax.set_axis_off()

guardar(fig, "02-fuente-rasters.png")
