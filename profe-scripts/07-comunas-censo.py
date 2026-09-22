"""Comunas de la Región Metropolitana con los totales del Censo 2024.

Deja `data/comunas-censo/comunas-rm.parquet` con una fila por comuna: la
geometría de la cartografía censal, la población, las viviendas y el medio de
transporte que sus habitantes declaran usar para ir al trabajo. La segunda
clase práctica de geografía lo usa para el análisis a nivel comunal.

Correr desde la raíz del repositorio:

    uv run python profe-scripts/07-comunas-censo.py
"""

# %%
import config
import geopandas as gpd
import pandas as pd

REGION_METROPOLITANA = 13
CRS_MAPA = "EPSG:4326"

# Columnas de las manzanas que se agregan por comuna. El censo publica el medio
# de transporte al trabajo, que es la variable de movilidad comparable con la
# red de transporte público de hoy.
CONTEOS = {
    "n_per": "poblacion",
    "n_vp": "viviendas",
    "n_transporte_auto": "transporte_auto",
    "n_transporte_publico": "transporte_publico",
    "n_transporte_camina": "transporte_camina",
    "n_transporte_bicicleta": "transporte_bicicleta",
}

DIR_SALIDA = config.DIR_DATOS / "comunas-censo"

# %%
dir_carto = config.requerir(
    config.CARTOGRAFIA_DIR, "la cartografía del Censo 2024", "INFOVIS_CARTOGRAFIA_DIR"
)

comunas = gpd.read_parquet(
    dir_carto / "Cartografia_censo2024_Pais_Comunal.parquet",
    columns=["CUT", "COD_REGION", "COMUNA", "PROVINCIA", "SHAPE"],
    filters=[("COD_REGION", "=", REGION_METROPOLITANA)],
)

# Las manzanas se leen sin geometría: de ellas solo hacen falta los conteos.
manzanas = pd.read_parquet(
    dir_carto / "Cartografia_censo2024_Pais_Manzanas.parquet",
    columns=["CUT", *CONTEOS],
    filters=[("COD_REGION", "=", REGION_METROPOLITANA)],
)

print(f"{len(comunas)} comunas y {len(manzanas):,} manzanas en la región")

# %%
# Los totales comunales salen de sumar las manzanas, que es donde el censo
# publica los conteos.

totales = manzanas.groupby("CUT")[list(CONTEOS)].sum().rename(columns=CONTEOS)

comunas = (
    comunas.rename(columns={"CUT": "cut", "COMUNA": "comuna", "PROVINCIA": "provincia",
                            "SHAPE": "geometry"})
    .set_geometry("geometry")
    .drop(columns="COD_REGION")
    .merge(totales, left_on="cut", right_index=True, how="left")
    .to_crs(CRS_MAPA)
)

# Los nombres vienen en mayúsculas y con el resto del material en formato título.
comunas["comuna"] = comunas["comuna"].str.title()
comunas["provincia"] = comunas["provincia"].str.title()

print(f"\nPoblación de la región: {comunas['poblacion'].sum():,}")
print(f"Viviendas: {comunas['viviendas'].sum():,}")
print(comunas.nlargest(5, "poblacion")[["comuna", "poblacion", "viviendas"]].to_string())

# %%
reparto = comunas[[c for c in CONTEOS.values() if c.startswith("transporte")]].sum()
print("\nMedio de transporte al trabajo en la región:")
print((reparto / reparto.sum()).round(3).to_string())

# %%
DIR_SALIDA.mkdir(parents=True, exist_ok=True)
comunas.to_parquet(DIR_SALIDA / "comunas-rm.parquet")
print(f"\nEscrito: {DIR_SALIDA / 'comunas-rm.parquet'}")

config.publicar("comunas-censo")
