"""Recorridos del transporte público de Santiago, desde el GTFS del DTPM.

Deja `data/recorridos/recorridos.parquet` con un trazado por recorrido y la
frecuencia de buses por hora en la punta de la mañana de un día laboral. El
script de la unidad 07 lo usa para el mapa de calor de líneas.

Correr desde la raíz del repositorio:

    uv run python profe-scripts/07-recorridos-dataset.py
"""

# %%
import zipfile

import config
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

# Ventana horaria del muestreo. El GTFS declara la frecuencia por tramos, así
# que se toma el tramo que contiene esta hora en el servicio laboral.
HORA_PUNTA = "08:00:00"
SERVICIO_LABORAL = "L"

# Tolerancia de simplificación en metros. Los trazados del GTFS traen un punto
# cada pocos metros y el mapa de calor agrega por tramos de decenas de metros,
# así que bajar la resolución no cambia la figura y sí el tamaño del archivo.
TOLERANCIA_M = 15

CRS_METRICO = "EPSG:32719"
CRS_MAPA = "EPSG:4326"

DIR_SALIDA = config.DIR_DATOS / "recorridos"

# %%
# Las tablas del GTFS se leen directo del zip, sin descomprimirlo.

ruta_gtfs = config.requerir(config.GTFS_ZIP, "el GTFS del DTPM", "INFOVIS_GTFS_ZIP")

with zipfile.ZipFile(ruta_gtfs) as z:
    with z.open("trips.txt") as f:
        viajes = pd.read_csv(f, usecols=["route_id", "service_id", "trip_id", "shape_id"])
    with z.open("frequencies.txt") as f:
        frecuencias = pd.read_csv(f, usecols=["trip_id", "start_time", "end_time", "headway_secs"])
    with z.open("routes.txt") as f:
        rutas = pd.read_csv(f, usecols=["route_id", "route_short_name", "route_long_name"])
    with z.open("shapes.txt") as f:
        puntos = pd.read_csv(f)

print(f"GTFS: {len(viajes):,} viajes, {len(frecuencias):,} tramos de frecuencia")
print(f"       {viajes['shape_id'].nunique():,} trazados, {len(rutas):,} recorridos")

# %%
# Frecuencia en la punta de la mañana.
#
# frequencies.txt entrega el intervalo entre buses (headway) por tramo horario.
# Los buses por hora son 3600 dividido por ese intervalo. Un mismo trazado
# puede tener varios viajes en la ventana (por ejemplo, servicios que comparten
# trazado), así que se suman.

laborales = viajes[viajes["service_id"] == SERVICIO_LABORAL]
tramos = laborales.merge(frecuencias, on="trip_id")

en_punta = tramos[(tramos["start_time"] <= HORA_PUNTA) & (tramos["end_time"] > HORA_PUNTA)].copy()
en_punta["buses_hora"] = 3600 / en_punta["headway_secs"]

por_trazado = (
    en_punta.groupby("shape_id")
    .agg(buses_hora=("buses_hora", "sum"), route_id=("route_id", "first"))
    .reset_index()
)

print(f"\nServicio {SERVICIO_LABORAL} a las {HORA_PUNTA}: {len(en_punta):,} viajes")
print(f"Trazados con servicio: {len(por_trazado):,}")
print(f"Buses por hora: mediana {por_trazado['buses_hora'].median():.1f}, "
      f"máximo {por_trazado['buses_hora'].max():.1f}")

# %%
# De la tabla de puntos a una geometría por trazado.

puntos = puntos.sort_values(["shape_id", "shape_pt_sequence"])
geometrias = (
    puntos.groupby("shape_id")[["shape_pt_lon", "shape_pt_lat"]]
    .apply(lambda g: LineString(g.to_numpy()) if len(g) > 1 else None)
    .rename("geometry")
)

recorridos = (
    gpd.GeoDataFrame(por_trazado.join(geometrias, on="shape_id"), crs=CRS_MAPA)
    .dropna(subset=["geometry"])
    .merge(rutas, on="route_id", how="left")
)

antes = len(recorridos)
recorridos = recorridos.to_crs(CRS_METRICO)
recorridos["geometry"] = recorridos.geometry.simplify(TOLERANCIA_M)
recorridos = recorridos.to_crs(CRS_MAPA)

recorridos = recorridos.rename(
    columns={"route_short_name": "servicio", "route_long_name": "nombre"}
)[["shape_id", "servicio", "nombre", "buses_hora", "geometry"]]

print(f"\nRecorridos con geometría: {antes:,}")
print(f"Largo mediano: {recorridos.to_crs(CRS_METRICO).length.median() / 1000:.1f} km")
print(recorridos.drop(columns="geometry").head())

# %%
DIR_SALIDA.mkdir(parents=True, exist_ok=True)
recorridos.to_parquet(DIR_SALIDA / "recorridos.parquet")
print(f"\nEscrito: {DIR_SALIDA / 'recorridos.parquet'}")

config.publicar("recorridos")
