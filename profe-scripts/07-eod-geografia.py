"""Prepara los datos geográficos de la EOD para la unidad 07.

La tabla de viajes que publica la unidad 02 trae códigos de comuna y de zona,
pero no coordenadas, así que no sirve para una sesión de mapas. Este script arma
un paquete con las tres capas que necesita la clase:

- viajes con las coordenadas de origen y destino, para los mapas de puntos.
- zonas de la EOD, para agregar y hacer coropletas.
- comunas de la Región Metropolitana, como capa de contexto.

Las coordenadas quedan como columnas numéricas y no como geometría: darles un
sistema de coordenadas es lo primero que hace el script de clase.

Uso: uv run python profe-scripts/07-eod-geografia.py
"""

# %%
import geopandas as gpd
import pandas as pd

import config

NOMBRE_DATASET = "eod-geografia"
DIR_SALIDA = config.DIR_DATOS / NOMBRE_DATASET

# La EOD entrega las coordenadas en UTM 19 Sur, que es el sistema métrico que
# corresponde a Chile central.
CRS_EOD = "EPSG:32719"

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
    "OrigenCoordX": "origen_x",
    "OrigenCoordY": "origen_y",
    "DestinoCoordX": "destino_x",
    "DestinoCoordY": "destino_y",
}

COORDENADAS = ["origen_x", "origen_y", "destino_x", "destino_y"]

PROCEDENCIA = """\
# eod-geografia

Las tres capas geográficas de la Encuesta Origen-Destino de Santiago 2012, para
la unidad de mapas y datos espaciales.

## `viajes.parquet`

Viajes declarados, con las coordenadas de origen y destino.

- Fuente: SECTRA, Encuesta Origen-Destino de Viajes de Santiago 2012.
- Coordenadas en EPSG:32719 (UTM 19 Sur), como columnas numéricas.
- Se descartan los viajes sin las cuatro coordenadas y los que traen un cero en
  alguna de ellas, que es el valor con que marca la fuente lo que no se pudo
  georreferenciar.

## `zonas.parquet`

Zonificación de la EOD, que es la unidad de análisis con que se diseñó la
encuesta.

- Fuente: SECTRA, Zonificacion_EOD2012.
- Proyección EPSG:4326 para desplegar.
- Cinco zonas venían con autointersecciones y se repararon con `make_valid`.

## `comunas.parquet`

Comunas de la Región Metropolitana, como capa de contexto de los mapas.

- Fuente: cartografía del Censo 2024, Instituto Nacional de Estadísticas.
- Proyección EPSG:4326 para desplegar.
"""

# %%
# --- Viajes con coordenadas ---
dir_eod = config.requerir(config.EOD_DIR, "la carpeta de la EOD Santiago 2012", "INFOVIS_EOD_DIR")

viajes = pd.read_csv(dir_eod / "viajes.csv", sep=";", decimal=",", low_memory=False)
print(f"Viajes crudos: {len(viajes):,}")

faltantes = set(COLUMNAS_VIAJES) - set(viajes.columns)
if faltantes:
    raise ValueError(f"Faltan columnas en viajes.csv: {sorted(faltantes)}")

viajes = viajes[list(COLUMNAS_VIAJES)].rename(columns=COLUMNAS_VIAJES)

for columna, (archivo, id_col, etiqueta_col) in PARAMETROS.items():
    tabla = pd.read_csv(dir_eod / "Tablas_parametros" / archivo, sep=";")
    mapa = dict(zip(tabla[id_col], tabla[etiqueta_col].str.strip()))
    destino = COLUMNAS_VIAJES[columna]
    viajes[destino] = viajes[destino].map(mapa).astype("category")

# Comunas.csv trae los nombres en formato título y separados por coma, a
# diferencia del resto de las tablas de parámetros.
comunas_eod = pd.read_csv(dir_eod / "Tablas_parametros" / "Comunas.csv", sep=",")
mapa_comunas = dict(zip(comunas_eod["Id"], comunas_eod["Comuna"].str.strip()))
for columna in ["comuna_origen", "comuna_destino"]:
    viajes[columna] = viajes[columna].map(mapa_comunas).astype("category")

# La hora de inicio llega como texto, con la hora en uno o dos dígitos ("9:00"
# y "22:30"), así que hay que cortar por el separador y no por posición.
viajes["hora_inicio"] = pd.to_numeric(
    viajes["hora_inicio"].astype(str).str.split(":").str[0], errors="coerce"
)

# %%
# Las coordenadas son la razón de ser de este paquete, así que el descarte se
# reporta paso a paso.
completos = viajes[COORDENADAS].notna().all(axis=1)
print(f"  con las cuatro coordenadas: {completos.sum():,} ({completos.mean():.1%})")

viajes = viajes[completos]

# Un cero en una coordenada UTM cae en el golfo de Guinea, así que la fuente lo
# usa para marcar lo que no se pudo georreferenciar.
sin_cero = (viajes[COORDENADAS] != 0).all(axis=1)
print(f"  sin ceros en las coordenadas: {sin_cero.sum():,}")

viajes = viajes[sin_cero].reset_index(drop=True)
print(f"Viajes publicados: {len(viajes):,}")

# %%
# --- Zonas de la EOD ---
zonas = gpd.read_file(dir_eod / "Zonificacion_EOD2012" / "Zonificacion_EOD2012.shp")
zonas = zonas[["Zona", "Comuna", zonas.geometry.name]]
zonas.columns = ["zona", "comuna", "geometry"]
zonas["zona"] = zonas["zona"].astype(int)
zonas = zonas.set_geometry("geometry").to_crs(4326)

# Cinco zonas traen autointersecciones, y con una geometría inválida cualquier
# operación de recorte o de cruce falla con un TopologyException.
invalidas = ~zonas.is_valid
print(f"Zonas: {len(zonas):,} en {zonas['comuna'].nunique()} comunas, "
      f"{invalidas.sum()} con geometría inválida")
zonas.loc[invalidas, "geometry"] = zonas.loc[invalidas, "geometry"].make_valid()

# %%
# --- Comunas de contexto ---
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
print(f"Comunas: {len(comunas)}")

# %%
DIR_SALIDA.mkdir(parents=True, exist_ok=True)

viajes.to_parquet(DIR_SALIDA / "viajes.parquet", index=False)
zonas.to_parquet(DIR_SALIDA / "zonas.parquet", index=False)
comunas.to_parquet(DIR_SALIDA / "comunas.parquet", index=False)
(DIR_SALIDA / "PROCEDENCIA.md").write_text(PROCEDENCIA, encoding="utf-8")

config.publicar(NOMBRE_DATASET)
