"""Descarga de los datasets del curso."""

import tarfile
import urllib.request
from pathlib import Path

URL_BASE = "https://dcc.uchile.cl/~egraells/infovis-data"

DIR_DATOS = Path("data")


def descargar_datos(url):
    """Baja un .tgz del servidor del curso y lo extrae en data/.

    El nombre de la carpeta destino se deriva del nombre del archivo. Si la
    carpeta ya existe, no vuelve a descargar. Acepta una URL completa o el
    nombre del archivo, en cuyo caso se resuelve contra el servidor del curso.
    """
    if not url.startswith("http"):
        url = f"{URL_BASE}/{url}"

    nombre_archivo = url.split("/")[-1]
    carpeta = DIR_DATOS / nombre_archivo.split(".")[0]

    if carpeta.exists():
        print(f"La carpeta '{carpeta}' ya existe, no se descarga de nuevo.")
        return carpeta

    DIR_DATOS.mkdir(parents=True, exist_ok=True)
    print(f"Descargando {url}")

    try:
        archivo_temporal, _ = urllib.request.urlretrieve(url)
        with tarfile.open(archivo_temporal, "r:gz") as tar:
            tar.extractall(path=DIR_DATOS)
        print(f"Datos disponibles en '{carpeta}'.")
    finally:
        urllib.request.urlcleanup()

    return carpeta


def descargar_archivo(url, nombre=None):
    """Baja un archivo suelto (raster, parquet) a data/ sin extraerlo."""
    if not url.startswith("http"):
        url = f"{URL_BASE}/{url}"

    destino = DIR_DATOS / (nombre or url.split("/")[-1])

    if destino.exists():
        print(f"El archivo '{destino}' ya existe, no se descarga de nuevo.")
        return destino

    DIR_DATOS.mkdir(parents=True, exist_ok=True)
    print(f"Descargando {url}")
    urllib.request.urlretrieve(url, destino)
    print(f"Datos disponibles en '{destino}'.")

    return destino
