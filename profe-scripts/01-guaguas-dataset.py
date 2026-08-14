"""Prepara el dataset de nombres de guaguas para la unidad 01.

Fuente: https://github.com/rivaquiroga/guaguas (Riva Quiroga, licencia CC-0),
construido a partir de los registros del Servicio de Registro Civil e
Identificación. Incluye solo los nombres inscritos como primer nombre.

El script lee el CSV crudo, verifica su estructura, escribe la procedencia
junto a los datos y empaqueta todo en data/guaguas.tgz.

Uso: uv run python profe-scripts/01-guaguas-dataset.py
"""

# %%
import shutil

import pandas as pd

import config

NOMBRE_DATASET = "guaguas"
DIR_SALIDA = config.DIR_DATOS / NOMBRE_DATASET

PROCEDENCIA = """\
# guaguas

Nombres inscritos en Chile entre 1920 y 2021, según el Servicio de Registro
Civil e Identificación. Incluye solo los inscritos como primer nombre.

- Fuente: https://github.com/rivaquiroga/guaguas
- Recolección y preparación: Riva Quiroga <riva.quiroga@uc.cl>
- Licencia: CC-0

Columnas:

- `anio`: año de inscripción.
- `nombre`: primer nombre inscrito.
- `sexo`: sexo registral asociado a la inscripción (F, M, I).
- `n`: cantidad de inscripciones de ese nombre ese año.
- `proporcion`: `n` dividido por el total de inscripciones de ese año.
"""

# %%
ruta_csv = config.requerir(
    config.GUAGUAS_CSV,
    "el CSV de nombres del Registro Civil",
    "INFOVIS_GUAGUAS_CSV",
)

print(f"Leyendo {ruta_csv}")
guaguas = pd.read_csv(ruta_csv)

print(f"Filas: {len(guaguas):,}")
print(f"Columnas: {list(guaguas.columns)}")
print(f"Años: {guaguas['anio'].min()} a {guaguas['anio'].max()}")
print(f"Nombres distintos: {guaguas['nombre'].nunique():,}")

# %%
# Verificaciones antes de publicar: las columnas que usan los scripts de clase
# deben existir y no traer nulos.
COLUMNAS = ["anio", "nombre", "sexo", "n", "proporcion"]

faltantes = set(COLUMNAS) - set(guaguas.columns)
if faltantes:
    raise ValueError(f"Faltan columnas en la fuente: {sorted(faltantes)}")

nulos = guaguas[COLUMNAS].isna().sum()
print("\nNulos por columna:")
print(nulos)
if nulos.sum() > 0:
    raise ValueError("La fuente trae nulos en columnas que el curso usa.")

print("\nInscripciones por sexo registral:")
print(guaguas.groupby("sexo")["n"].sum().sort_values(ascending=False))

# %%
DIR_SALIDA.mkdir(parents=True, exist_ok=True)

destino = DIR_SALIDA / "guaguas.csv.gz"
guaguas[COLUMNAS].to_csv(destino, index=False, compression="gzip")
print(f"\nEscrito: {destino} ({destino.stat().st_size / 1e6:.1f} MB)")

(DIR_SALIDA / "PROCEDENCIA.md").write_text(PROCEDENCIA)

# %%
config.publicar(NOMBRE_DATASET)
