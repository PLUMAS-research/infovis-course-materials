"""Copiar a config_local.py (gitignored) y completar las rutas de esta máquina.

Precedencia: variable de entorno INFOVIS_* > config_local.py > default.
"""

# --- Publicación de los artefactos del curso ---
DESTINO_SCP = "dichato.dcc.uchile.cl:~/public_www/infovis-data/"
URL_BASE = "https://dcc.uchile.cl/~egraells/infovis-data"

# La subida no ocurre por defecto: activarla con INFOVIS_SUBIR=1 o con esta
# constante en True.
SUBIR_AL_SERVIDOR = False

# --- Fuentes crudas ---
# Encuesta Origen-Destino Santiago 2012 (SECTRA), carpeta EOD_STGO.
EOD_DIR = "~/datos/EOD_STGO"

# Microdatos y cartografía del Censo 2024.
CENSO_DIR = "~/datos/censo2024"

# Corpus de noticias chilenas (CLNews).
CLNEWS_DIR = "~/datos/CLNews"

# CSV de nombres del Registro Civil (paquete guaguas de Riva Quiroga).
GUAGUAS_CSV = "~/datos/guaguas/1920-2021.csv.gz"

# Cartografía del Censo 2024 (parquets por nivel: comunal, zonal, manzanas).
CARTOGRAFIA_DIR = "~/datos/censo2024-cartografia"

# Red de colaboración entre músicos de jazz (KONECT, arenas-jazz).
JAZZ_DIR = "~/datos/arenas-jazz"

# Raster de NDVI de Santiago, compuesto anual de Sentinel-2.
NDVI_TIF = "~/datos/ndvi-santiago-2023.tif"

# Siniestros de tránsito georreferenciados de CONASET (un GeoJSON por año).
CONASET_DIR = "~/datos/conaset"
