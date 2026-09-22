"""Paradas del transporte público de Santiago, desde el GTFS del DTPM.

Deja `data/paradas/estaciones-metro.parquet` con una fila por estación de Metro
y `data/paradas/paraderos-bus.parquet` con una fila por paradero de bus. El
script de la clase práctica de geografía los usa para las operaciones que
necesitan una capa de puntos de infraestructura: buffer, área de servicio y
distancia a la parada más cercana.

Correr desde la raíz del repositorio:

    uv run python profe-scripts/07-paradas-dataset.py
"""

# %%
import zipfile

import config
import geopandas as gpd
import pandas as pd

# Tipos de servicio del GTFS: 1 es metro y 3 es bus.
METRO = 1
BUS = 3

CRS_MAPA = "EPSG:4326"

DIR_SALIDA = config.DIR_DATOS / "paradas"

# %%
# Las tablas del GTFS se leen directo del zip, sin descomprimirlo.

ruta_gtfs = config.requerir(config.GTFS_ZIP, "el GTFS del DTPM", "INFOVIS_GTFS_ZIP")

with zipfile.ZipFile(ruta_gtfs) as z:
    with z.open("feed_info.txt") as f:
        info = pd.read_csv(f)
    with z.open("stops.txt") as f:
        paradas = pd.read_csv(f)
    with z.open("trips.txt") as f:
        viajes = pd.read_csv(f, usecols=["route_id", "trip_id"])
    with z.open("routes.txt") as f:
        rutas = pd.read_csv(f, usecols=["route_id", "route_short_name", "route_type"])
    with z.open("stop_times.txt") as f:
        detenciones = pd.read_csv(f, usecols=["trip_id", "stop_id"])

print(f"Feed {info['feed_version'].iloc[0]}, vigente entre "
      f"{info['feed_start_date'].iloc[0]} y {info['feed_end_date'].iloc[0]}")
print(f"{len(paradas):,} paradas, {len(rutas):,} servicios, "
      f"{len(detenciones):,} detenciones")

# %%
# Qué servicios pasan por cada parada.
#
# stop_times.txt tiene una fila por detención de cada viaje, así que hay que
# pasar por trips.txt para llegar al servicio.

servicios = (
    detenciones.merge(viajes, on="trip_id")
    .merge(rutas, on="route_id")
    .drop_duplicates(["stop_id", "route_id"])
)

# %%
# Estaciones de Metro.
#
# El GTFS entrega un andén por sentido (`Camino Agrícola Dirección Vicente
# Valdés` y `Camino Agrícola Dirección Plaza de Maipú`), y los dos apuntan a la
# estación con `parent_station`. La estación es la parada padre, que está en la
# misma tabla con `location_type` igual a 1.

andenes = servicios[servicios["route_type"] == METRO]
lineas_por_estacion = (
    paradas[["stop_id", "parent_station"]]
    .merge(andenes[["stop_id", "route_short_name"]], on="stop_id")
    .groupby("parent_station")["route_short_name"]
    .apply(lambda s: ", ".join(sorted(set(s))))
)

estaciones = (
    paradas[paradas["location_type"] == 1]
    .set_index("stop_id")
    .join(lineas_por_estacion.rename("lineas"), how="inner")
    .reset_index()
    .rename(columns={"stop_id": "estacion", "stop_name": "nombre"})
)
estaciones["n_lineas"] = estaciones["lineas"].str.count(",") + 1

estaciones = gpd.GeoDataFrame(
    estaciones[["estacion", "nombre", "lineas", "n_lineas"]],
    geometry=gpd.points_from_xy(estaciones["stop_lon"], estaciones["stop_lat"]),
    crs=CRS_MAPA,
)

print(f"\n{len(estaciones)} estaciones de Metro")
print(estaciones["lineas"].value_counts().head(10))

# %%
# Paraderos de bus.
#
# El nombre viene como `PD1641-Parada 7 / (M) Macul`: el código se repite al
# principio, así que se corta en el primer guion.

paraderos_bus = servicios[servicios["route_type"] == BUS]
cuenta = (
    paraderos_bus.groupby("stop_id")["route_id"]
    .nunique()
    .rename("servicios")
)

paraderos = (
    paradas.set_index("stop_id")
    .join(cuenta, how="inner")
    .reset_index()
    .rename(columns={"stop_id": "paradero"})
)
paraderos["nombre"] = paraderos["stop_name"].str.split("-", n=1).str[1].str.strip()

paraderos = gpd.GeoDataFrame(
    paraderos[["paradero", "nombre", "servicios"]],
    geometry=gpd.points_from_xy(paraderos["stop_lon"], paraderos["stop_lat"]),
    crs=CRS_MAPA,
)

print(f"\n{len(paraderos):,} paraderos de bus")
print(f"Servicios por paradero: mediana {paraderos['servicios'].median():.0f}, "
      f"máximo {paraderos['servicios'].max()}")

# %%
DIR_SALIDA.mkdir(parents=True, exist_ok=True)
estaciones.to_parquet(DIR_SALIDA / "estaciones-metro.parquet")
paraderos.to_parquet(DIR_SALIDA / "paraderos-bus.parquet")
print(f"\nEscrito en {DIR_SALIDA}")

config.publicar("paradas")
