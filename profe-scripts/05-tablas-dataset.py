"""Prepara la tabla de viajes de la EOD para la unidad 05.

Parte de la tabla de viajes que deja profe-scripts/02-tipos-de-dataset.py y le
agrega dos llaves categóricas que la unidad 05 usa para agrupar y colorear: el
sector de la ciudad donde empieza el viaje y el día de la semana en que se
encuestó al hogar. El resultado se publica como eod-viajes.tgz, aparte de
tipos-de-dataset.tgz: descargar_datos no vuelve a bajar una carpeta que ya
existe, así que cambiar el paquete de la unidad 02 dejaría a quienes ya lo
bajaron con la tabla sin las columnas nuevas.

Uso: uv run python profe-scripts/05-tablas-dataset.py
Requiere haber corrido antes profe-scripts/02-tipos-de-dataset.py.
"""

# %%
import pandas as pd

import config

NOMBRE_DATASET = "eod-viajes"
DIR_SALIDA = config.DIR_DATOS / NOMBRE_DATASET
TABLA_BASE = config.DIR_DATOS / "tipos-de-dataset" / "eod-viajes.parquet"

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

PROCEDENCIA = """\
# eod-viajes

Viajes declarados en la Encuesta Origen Destino de Santiago 2012, con los
códigos traducidos a etiquetas y dos atributos adicionales respecto de la tabla
de `tipos-de-dataset`:

- `sector`: sector de la ciudad donde empieza el viaje, según la zonificación
  de la encuesta (Centro, Norte, Oriente, Poniente, Sur, Sur-Oriente y
  Extensión Sur-Poniente). Cada comuna cae entera en un sector.
- `dia`: día de la semana en que se encuestó al hogar. Cada hogar declara los
  viajes de un solo día, así que los conteos por día reflejan también cuántos
  hogares se encuestaron ese día.

Fuente: SECTRA, Ministerio de Transportes y Telecomunicaciones.
"""

# %%
if not TABLA_BASE.exists():
    raise FileNotFoundError(
        f"No existe {TABLA_BASE}: correr antes profe-scripts/02-tipos-de-dataset.py"
    )

viajes = pd.read_parquet(TABLA_BASE)
print(f"Viajes en la tabla base: {len(viajes):,}")

dir_eod = config.requerir(config.EOD_DIR, "la carpeta de la EOD Santiago 2012", "INFOVIS_EOD_DIR")

# %%
# --- Sector de origen ---
# La encuesta asigna el sector por zona y lo guarda en cada viaje. Un puñado de
# viajes trae sector 0 (sin dato), así que cada comuna recibe el sector de la
# mayoría de sus viajes, que es único porque ninguna comuna cruza sectores.
sectores = pd.read_csv(dir_eod / "Tablas_parametros" / "Sector.csv", sep=";")
nombre_sector = dict(zip(sectores["Sector"], sectores["Nombre"].str.strip()))

crudo = pd.read_csv(dir_eod / "viajes.csv", sep=";", usecols=["Viaje", "SectorOrigen"])
crudo["sector"] = crudo["SectorOrigen"].map(nombre_sector)

viajes = viajes.merge(crudo[["Viaje", "sector"]], left_on="viaje", right_on="Viaje", how="left")
viajes = viajes.drop(columns="Viaje")

sector_comuna = (
    viajes.dropna(subset=["sector"])
    .groupby("comuna_origen", observed=True)["sector"]
    .agg(lambda s: s.value_counts().idxmax())
)
viajes["sector"] = viajes["comuna_origen"].map(sector_comuna).astype("category")
print("Comunas por sector:")
print(sector_comuna.value_counts().to_string())

# %%
# --- Día de la semana ---
hogares = pd.read_csv(dir_eod / "Hogares.csv", sep=";", usecols=["Hogar", "DiaAsig"])
dia_hogar = dict(zip(hogares["Hogar"], hogares["DiaAsig"].str.strip().str.lower()))
viajes["dia"] = pd.Categorical(viajes["hogar"].map(dia_hogar), categories=DIAS, ordered=True)

sin_dia = viajes["dia"].isna().sum()
print(f"Viajes sin día asignado: {sin_dia:,}")
print("Viajes por día:")
print(viajes["dia"].value_counts(sort=False).to_string())

# %%
DIR_SALIDA.mkdir(parents=True, exist_ok=True)
viajes.to_parquet(DIR_SALIDA / "eod-viajes.parquet", index=False)
(DIR_SALIDA / "PROCEDENCIA.md").write_text(PROCEDENCIA)

print(viajes.dtypes)
print("\nArchivos escritos:")
for ruta in sorted(DIR_SALIDA.iterdir()):
    print(f"  {ruta.name}: {ruta.stat().st_size / 1e6:.1f} MB")

# %%
config.publicar(NOMBRE_DATASET)
