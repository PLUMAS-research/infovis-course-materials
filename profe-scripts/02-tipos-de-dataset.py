"""Prepara los cuatro datasets de la unidad 02, uno por tipo.

La unidad necesita un ejemplo de cada tipo de dataset, y los cuatro tienen que
caber en una sesión de clases. Este script reduce cada fuente cruda a un
archivo manejable y los empaqueta juntos en data/tipos-de-dataset.tgz:

- tabla: viajes de la Encuesta Origen-Destino de Santiago 2012, con los códigos
  ya traducidos a etiquetas legibles.
- red: colaboraciones entre músicos de jazz.
- campo: NDVI de Santiago, compuesto anual de Sentinel-2.
- geometría: comunas de la Región Metropolitana según el Censo 2024.

Uso: uv run python profe-scripts/02-tipos-de-dataset.py
"""

# %%
import shutil

import geopandas as gpd
import pandas as pd

import config

NOMBRE_DATASET = "tipos-de-dataset"
DIR_SALIDA = config.DIR_DATOS / NOMBRE_DATASET

# La EOD codifica casi todo con enteros y guarda el diccionario en
# Tablas_parametros. Traducirlos acá deja el script de clase libre para hablar
# de tipos de atributo en vez de pelear con códigos.
PARAMETROS = {
    "Proposito": ("Proposito.csv", "Id", "Proposito"),
    "ModoAgregado": ("ModoAgregado.csv", "ID", "Modo"),
    "Periodo": ("Periodo.csv", "Id", "Periodos"),
}

COLUMNAS_VIAJES = {
    "Hogar": "hogar",
    "Persona": "persona",
    "Viaje": "viaje",
    "ComunaOrigen": "comuna_origen",
    "ComunaDestino": "comuna_destino",
    "ZonaOrigen": "zona_origen",
    "ZonaDestino": "zona_destino",
    "Proposito": "proposito",
    "ModoAgregado": "modo",
    "Periodo": "periodo",
    "HoraIni": "hora_inicio",
    "TiempoViaje": "minutos",
}

PROCEDENCIA = """\
# tipos-de-dataset

Cuatro datasets, uno por cada tipo que estructura el curso. Se usan en la
unidad 02 para describir la misma estructura con el mismo vocabulario.

## `eod-viajes.parquet` (tabla)

Viajes declarados en la Encuesta Origen-Destino de Santiago 2012.

- Fuente: SECTRA, Ministerio de Transportes y Telecomunicaciones.
- Un ítem por viaje. Los códigos de propósito, modo y período vienen
  traducidos a etiquetas desde `Tablas_parametros` de la fuente original.

## `jazz-enlaces.csv` (red)

Red de colaboración entre músicos de jazz: un enlace por cada par de músicos
que tocó en una misma banda.

- Fuente: KONECT, `arenas-jazz`, recolectada en 2003.
- Referencia: Gleiser, P. & Danon, L. (2003). Community structure in jazz.
  Advances in Complex Systems, 6(4), 565-573.

## `ndvi-santiago-2023.tif` (campo)

Índice de vegetación de diferencia normalizada (NDVI) para Santiago, compuesto
anual de Sentinel-2 para 2023. Un valor continuo por celda de la grilla, entre
-1 y 1: sobre 0,3 hay vegetación, bajo 0 hay agua o superficie construida.

## `comunas-rm.parquet` (geometría)

Polígonos de las comunas de la Región Metropolitana.

- Fuente: cartografía del Censo 2024, Instituto Nacional de Estadísticas.
- Proyección EPSG:4326 para desplegar.
"""

# %%
# --- Tabla: viajes de la EOD ---
dir_eod = config.requerir(config.EOD_DIR, "la carpeta de la EOD Santiago 2012", "INFOVIS_EOD_DIR")

print(f"Leyendo {dir_eod / 'viajes.csv'}")
viajes = pd.read_csv(dir_eod / "viajes.csv", sep=";", decimal=",", low_memory=False)
print(f"  Viajes crudos: {len(viajes):,}")

faltantes = set(COLUMNAS_VIAJES) - set(viajes.columns)
if faltantes:
    raise ValueError(f"Faltan columnas en viajes.csv: {sorted(faltantes)}")

viajes = viajes[list(COLUMNAS_VIAJES)].rename(columns=COLUMNAS_VIAJES)

for columna, (archivo, id_col, etiqueta_col) in PARAMETROS.items():
    tabla = pd.read_csv(dir_eod / "Tablas_parametros" / archivo, sep=";")
    mapa = dict(zip(tabla[id_col], tabla[etiqueta_col].str.strip()))
    destino = COLUMNAS_VIAJES[columna]
    viajes[destino] = viajes[destino].map(mapa).astype("category")
    print(f"  {destino}: {viajes[destino].nunique()} categorías")

# Comunas.csv trae los nombres en formato título y separados por coma, a
# diferencia del resto de las tablas de parámetros.
comunas_eod = pd.read_csv(dir_eod / "Tablas_parametros" / "Comunas.csv", sep=",")
mapa_comunas = dict(zip(comunas_eod["Id"], comunas_eod["Comuna"].str.strip()))
for columna in ["comuna_origen", "comuna_destino"]:
    viajes[columna] = viajes[columna].map(mapa_comunas).astype("category")

# La hora de inicio llega como texto, con la hora en uno o dos dígitos ("9:00"
# y "22:30"), así que hay que cortar por el separador y no por posición. Se
# guarda como hora entera, que es el atributo cíclico que se usa en clases.
viajes["hora_inicio"] = pd.to_numeric(
    viajes["hora_inicio"].astype(str).str.split(":").str[0], errors="coerce"
)
viajes = viajes.dropna(subset=["proposito", "modo", "hora_inicio"])
viajes["hora_inicio"] = viajes["hora_inicio"].astype("int8")

print(f"  Viajes con propósito, modo y hora: {len(viajes):,}")
print(viajes.dtypes)

# %%
# --- Red: colaboraciones entre músicos de jazz ---
dir_jazz = config.requerir(config.JAZZ_DIR, "la carpeta de la red arenas-jazz", "INFOVIS_JAZZ_DIR")

enlaces = pd.read_csv(
    dir_jazz / "out.arenas-jazz",
    sep=r"\s+",
    comment="%",
    header=None,
    names=["musico_a", "musico_b"],
)
# La fuente es una red no dirigida: cada par aparece una sola vez, pero se
# normaliza el orden por si acaso y se eliminan bucles y duplicados.
enlaces = enlaces[enlaces["musico_a"] != enlaces["musico_b"]]
enlaces[["musico_a", "musico_b"]] = pd.DataFrame(
    {
        "musico_a": enlaces.min(axis=1),
        "musico_b": enlaces.max(axis=1),
    }
)
enlaces = enlaces.drop_duplicates().sort_values(["musico_a", "musico_b"]).reset_index(drop=True)

musicos = pd.unique(enlaces[["musico_a", "musico_b"]].values.ravel())
print(f"Red de jazz: {len(musicos):,} músicos y {len(enlaces):,} enlaces")

# %%
# --- Geometría: comunas de la Región Metropolitana ---
dir_carto = config.requerir(
    config.CARTOGRAFIA_DIR, "la cartografía del Censo 2024", "INFOVIS_CARTOGRAFIA_DIR"
)

comunas = gpd.read_parquet(dir_carto / "Cartografia_censo2024_Pais_Comunal.parquet")
comunas = comunas[comunas["COD_REGION"].astype(str) == "13"]
comunas = comunas[["CUT", "COMUNA", "PROVINCIA", comunas.geometry.name]]
comunas.columns = ["cut", "comuna", "provincia", "geometry"]
comunas = comunas.set_geometry("geometry").set_crs(4674, allow_override=True).to_crs(4326)

def formato_titulo(serie):
    """Título castellano: `str.title()` capitaliza también los conectores."""
    conectores = {"De", "Del", "La", "Las", "Los", "El", "Y"}
    return serie.str.strip().str.title().apply(
        lambda nombre: " ".join(
            palabra.lower() if i and palabra in conectores else palabra
            for i, palabra in enumerate(nombre.split())
        )
    )


comunas["comuna"] = formato_titulo(comunas["comuna"])
comunas["provincia"] = formato_titulo(comunas["provincia"])
comunas = comunas.sort_values("comuna").reset_index(drop=True)
print(f"Comunas de la Región Metropolitana: {len(comunas)}")
print(f"  Provincias: {sorted(comunas['provincia'].unique())}")

# %%
# --- Campo: NDVI de Santiago ---
ruta_ndvi = config.requerir(config.NDVI_TIF, "el raster de NDVI de Santiago", "INFOVIS_NDVI_TIF")

# %%
DIR_SALIDA.mkdir(parents=True, exist_ok=True)

viajes.to_parquet(DIR_SALIDA / "eod-viajes.parquet", index=False)
enlaces.to_csv(DIR_SALIDA / "jazz-enlaces.csv", index=False)
comunas.to_parquet(DIR_SALIDA / "comunas-rm.parquet", index=False)
shutil.copy(ruta_ndvi, DIR_SALIDA / "ndvi-santiago-2023.tif")
(DIR_SALIDA / "PROCEDENCIA.md").write_text(PROCEDENCIA)

print("\nArchivos escritos:")
for ruta in sorted(DIR_SALIDA.iterdir()):
    print(f"  {ruta.name}: {ruta.stat().st_size / 1e6:.1f} MB")

# %%
config.publicar(NOMBRE_DATASET)
