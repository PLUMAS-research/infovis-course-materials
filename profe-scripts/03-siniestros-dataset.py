"""Prepara el dataset de siniestros de tránsito para la unidad 03.

Fuente: CONASET, Portal de Información Geoespacial de Siniestros de Tránsito.
Los archivos crudos son un GeoJSON por año de la Región Metropolitana, de 2019
a 2023.

El esquema cambia de un año a otro: entre 26 y 70 columnas, con nombres
distintos para lo mismo y tres codificaciones de fecha y hora. El script
resuelve esas diferencias, se queda con el núcleo que existe en los cinco
archivos y deja un geoparquet en data/siniestros/.

Uso: uv run python profe-scripts/03-siniestros-dataset.py
"""

# %%
import geopandas as gpd
import pandas as pd

import config

NOMBRE_DATASET = "siniestros"
DIR_SALIDA = config.DIR_DATOS / NOMBRE_DATASET

# Las columnas del GeoJSON traen tildes, mayúsculas y nombres truncados por el
# límite de los shapefiles, y además cambian entre años. Este mapa fija el
# núcleo que existe en los tres archivos; el año se deriva de la fecha, porque
# la columna se llama "Ano" en 2019 y "Año" en los otros dos.
# El nombre de una misma columna cambia entre años: en 2021 la comuna llega como
# COMUNA y Comuna_1, y en los otros dos como Comuna. Por eso cada destino lista
# sus alias posibles, en orden de preferencia. El año se deriva de la fecha,
# porque la columna se llama "Ano" en 2019 y "Año" en los demás.
COLUMNAS = {
    "fecha": ["Fecha"],
    "hora": ["Hora"],
    "comuna": ["Comuna", "Comuna_1", "COMUNA"],
    "tipo": ["Tipo_Accid"],
    "tipo_agrupado": ["Tipo__CONA"],
    "zona": ["Zona"],
    "causa_agrupada": ["Causa__CON"],
    "fallecidos": ["Fallecidos"],
    "graves": ["Graves"],
    "menos_graves": ["Menos_Grav"],
    "leves": ["Leves"],
}

CATEGORICAS = ["comuna", "tipo", "tipo_agrupado", "zona", "causa_agrupada"]

PROCEDENCIA = """\
# siniestros

Siniestros de tránsito georreferenciados de la Región Metropolitana.

- Fuente: CONASET, Comisión Nacional de Seguridad de Tránsito.
- Portal: https://mapas-conaset.opendata.arcgis.com
- Un ítem por siniestro, con su ubicación en EPSG:4326.

Columnas:

- `anio`, `fecha`, `hora`: cuándo ocurrió. `hora` es la hora entera, atributo cíclico.
- `comuna`, `zona`: dónde ocurrió.
- `tipo`, `tipo_agrupado`: qué clase de siniestro fue (colisión, atropello, choque).
- `causa_agrupada`: la causa según la clasificación de CONASET.
- `fallecidos`, `graves`, `menos_graves`, `leves`: personas por gravedad.
- `victimas`: fallecidos más lesionados de cualquier gravedad, derivada acá.

El esquema de la fuente cambia entre años (entre 26 y 70 columnas), así que
este paquete solo conserva las columnas que existen en los cinco archivos.
Quedan fuera las condiciones de la calzada y del clima, disponibles solo en
algunos años. La hora está disponible en 2019, 2020 y 2022; en 2021 y 2023 la
fuente la entrega corrupta y queda nula.
"""

# %%
dir_crudo = config.requerir(
    config.CONASET_DIR, "la carpeta de siniestros de CONASET", "INFOVIS_CONASET_DIR"
)

archivos = sorted(dir_crudo.glob("*-rm-car-accidents.json"))
if not archivos:
    raise FileNotFoundError(f"No hay GeoJSON de CONASET en {dir_crudo}")

def resolver(capa, ruta):
    """Elige, para cada columna del curso, el primer alias presente en la capa."""
    elegidas, faltantes = {}, []
    for destino, alias in COLUMNAS.items():
        presente = next((a for a in alias if a in capa.columns), None)
        if presente is None:
            faltantes.append(destino)
        else:
            elegidas[presente] = destino
    if faltantes:
        raise ValueError(f"{ruta.name} no trae ninguna columna para {faltantes}")
    return capa[list(elegidas) + ["geometry"]].rename(columns=elegidas)


def normalizar_tiempo(parte):
    """Deja `fecha` sin zona horaria y `hora` como entero, o nula si no sirve.

    La fuente cambia de codificación entre años y hay que cubrir los tres casos:

    - `fecha` llega como marca de tiempo en cuatro de los cinco archivos, y en
      2022 como número de serie de planilla, que cuenta días desde el 30 de
      diciembre de 1899.
    - `fecha` nunca trae la hora del día: todas las filas marcan medianoche, así
      que la hora tiene que salir de su propia columna.
    - `hora` llega como hora del día en 2019, 2020 y 2022, y viene corrupta en
      2021 y 2023, donde todas las filas dicen 1899-12-30, el cero de la
      planilla. En esos años queda nula.
    """
    fecha = parte["fecha"]
    if pd.api.types.is_numeric_dtype(fecha):
        fecha = pd.to_datetime(fecha, unit="D", origin="1899-12-30")
    else:
        fecha = pd.to_datetime(fecha)
    if fecha.dt.tz is not None:
        fecha = fecha.dt.tz_localize(None)
    parte["fecha"] = fecha.dt.normalize()

    horas = parte["hora"]
    es_hora_del_dia = horas.map(lambda v: hasattr(v, "hour") and not hasattr(v, "year"))
    if es_hora_del_dia.all():
        parte["hora"] = horas.map(lambda v: v.hour).astype("Int8")
    else:
        parte["hora"] = pd.Series(pd.NA, index=parte.index, dtype="Int8")
    return parte


partes = []
for ruta in archivos:
    capa = gpd.read_file(ruta)
    parte = normalizar_tiempo(resolver(capa, ruta))
    con_hora = parte["hora"].notna().mean()
    print(f"{ruta.name}: {len(capa):,} siniestros, {len(capa.columns)} columnas, "
          f"{con_hora:.0%} con hora utilizable")
    partes.append(parte)

siniestros = pd.concat(partes, ignore_index=True)
siniestros = gpd.GeoDataFrame(siniestros, geometry="geometry", crs=4326)
print(f"\nTotal: {len(siniestros):,} siniestros")

# %%
siniestros["anio"] = siniestros["fecha"].dt.year.astype("int16")

def reparar_texto(serie):
    """Repara el doble encoding del archivo de 2019.

    Ese año llega con el UTF-8 leído como CP1252, así que "PEÑALOLEN" aparece
    como "PEÃ‘ALOLEN". Deshacer el error es volver a codificar en CP1252 y
    decodificar en UTF-8. Tiene que ser CP1252 y no Latin-1: el segundo byte de
    la Ñ en UTF-8 es 0x91, que en CP1252 es la comilla ‘ y en Latin-1 no existe,
    así que con Latin-1 la reparación falla y el nombre queda roto. Sobre un
    texto bien codificado la operación falla y se devuelve el original, así que
    se puede aplicar a todas las filas.
    """

    def arreglar(valor):
        if not isinstance(valor, str):
            return valor
        try:
            return valor.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return valor

    return serie.map(arreglar)


for columna in CATEGORICAS:
    siniestros[columna] = (
        reparar_texto(siniestros[columna]).str.strip().str.title().astype("category")
    )

print(f"\nComunas distintas: {siniestros['comuna'].nunique()}")

heridos = ["fallecidos", "graves", "menos_graves", "leves"]
siniestros[heridos] = siniestros[heridos].fillna(0).astype("int16")
siniestros["victimas"] = siniestros[heridos].sum(axis=1).astype("int16")

print("\nSiniestros por año:")
print(siniestros.groupby("anio").size())
print("\nTipos más frecuentes:")
print(siniestros["tipo_agrupado"].value_counts().head())
print(f"\nFallecidos en total: {siniestros['fallecidos'].sum():,}")
print(f"Siniestros sin víctimas: {(siniestros['victimas'] == 0).mean():.1%}")
print(f"Siniestros con hora conocida: {siniestros['hora'].notna().mean():.1%}")

# %%
# Verificación antes de publicar: sin geometrías vacías ni coordenadas fuera de
# la región, que en versiones anteriores del portal llegaban en cero.
vacias = siniestros.geometry.is_empty | siniestros.geometry.isna()
if vacias.any():
    print(f"Descartando {vacias.sum()} siniestros sin geometría")
    siniestros = siniestros[~vacias]

x, y = siniestros.geometry.x, siniestros.geometry.y
fuera = (x < -71.8) | (x > -69.7) | (y < -34.4) | (y > -32.9)
if fuera.any():
    print(f"Descartando {fuera.sum()} siniestros fuera de la Región Metropolitana")
    siniestros = siniestros[~fuera]

# %%
DIR_SALIDA.mkdir(parents=True, exist_ok=True)
destino = DIR_SALIDA / "siniestros-rm.parquet"
siniestros.reset_index(drop=True).to_parquet(destino, index=False)
print(f"\nEscrito: {destino} ({destino.stat().st_size / 1e6:.1f} MB)")

(DIR_SALIDA / "PROCEDENCIA.md").write_text(PROCEDENCIA)

# %%
config.publicar(NOMBRE_DATASET)
