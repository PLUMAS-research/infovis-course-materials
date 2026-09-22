"""Empaqueta la geometría de los países del mundo para la unidad 07.

Fuente: Natural Earth, países a escala 1:110m, dominio público. Se descarga de
https://www.naturalearthdata.com/downloads/110m-cultural-vectors/ y la ruta al
zip se configura en MUNDO_ZIP.

Se corre desde la raíz del repositorio:

    uv run python profe-scripts/07-mundo-dataset.py
"""

import geopandas as gpd

import config

SALIDA = "mundo"
COLUMNAS = {"NAME_ES": "pais", "CONTINENT": "continente", "geometry": "geometry"}

config.requerir(config.MUNDO_ZIP, "el zip de países de Natural Earth", "INFOVIS_MUNDO_ZIP")

mundo = gpd.read_file(f"zip://{config.MUNDO_ZIP}")
print(f"{len(mundo)} países, CRS {mundo.crs.to_string()}")

mundo = mundo[list(COLUMNAS)].rename(columns=COLUMNAS).to_crs("EPSG:4326")

destino = config.Path("data") / SALIDA
destino.mkdir(parents=True, exist_ok=True)
mundo.to_parquet(destino / "paises.parquet")

print(f"{len(mundo)} países escritos en {destino}")
print(mundo["continente"].value_counts().to_dict())

config.publicar(SALIDA)
