"""Configuración compartida de los profe-scripts (preparación de datasets).

Centraliza el destino de publicación, la URL pública del curso, las rutas a
fuentes crudas y los helpers para empaquetar y subir artefactos, así los
scripts de preparación no repiten el hostname ni la URL.

Override
--------
- Publicación (`DESTINO_SCP`, `URL_BASE`, `SUBIR_AL_SERVIDOR`): variables de
  entorno `INFOVIS_DESTINO_SCP`, `INFOVIS_URL_BASE`, `INFOVIS_SUBIR` (0 para
  empaquetar sin subir; la subida ocurre por omisión).
- Fuentes crudas privadas (microdatos sin publicar, repos hermanos): no se
  versionan. Copiar `config_local.example.py` a `config_local.py` (gitignored)
  y completar las rutas, o exportar las variables `INFOVIS_*` correspondientes.
  Sin configurar, los scripts que las usan fallan con un mensaje claro.
"""

import os
import subprocess
import tarfile
from pathlib import Path

DIR_DATOS = Path("data")

# Override local opcional (gitignored): config_local.py define constantes en
# MAYÚSCULAS. Precedencia: variable de entorno > config_local > default.
_local = {}
try:
    import config_local as _cl

    _local = {k: getattr(_cl, k) for k in dir(_cl) if k.isupper()}
except ImportError:
    pass


def _conf(const, env, default=None, ruta=False):
    valor = os.environ.get(env)
    if valor is None:
        valor = _local.get(const, default)
    if ruta and valor is not None:
        valor = Path(valor).expanduser()
    return valor


# --- Publicación ---
DESTINO_SCP = _conf("DESTINO_SCP", "INFOVIS_DESTINO_SCP")
URL_BASE = _conf("URL_BASE", "INFOVIS_URL_BASE")
# La subida ocurre por omisión. Para una corrida que solo empaquete, exportar
# INFOVIS_SUBIR=0 o poner SUBIR_AL_SERVIDOR = False en config_local.py.
_subir = os.environ.get("INFOVIS_SUBIR")
SUBIR_AL_SERVIDOR = (
    _subir != "0" if _subir is not None else bool(_local.get("SUBIR_AL_SERVIDOR", True))
)

# --- Fuentes crudas ---
EOD_DIR = _conf("EOD_DIR", "INFOVIS_EOD_DIR", ruta=True)
CENSO_DIR = _conf("CENSO_DIR", "INFOVIS_CENSO_DIR", ruta=True)
CARTOGRAFIA_DIR = _conf("CARTOGRAFIA_DIR", "INFOVIS_CARTOGRAFIA_DIR", ruta=True)
CLNEWS_DIR = _conf("CLNEWS_DIR", "INFOVIS_CLNEWS_DIR", ruta=True)
CONASET_DIR = _conf("CONASET_DIR", "INFOVIS_CONASET_DIR", ruta=True)
GUAGUAS_CSV = _conf("GUAGUAS_CSV", "INFOVIS_GUAGUAS_CSV", ruta=True)
JAZZ_DIR = _conf("JAZZ_DIR", "INFOVIS_JAZZ_DIR", ruta=True)
NDVI_TIF = _conf("NDVI_TIF", "INFOVIS_NDVI_TIF", ruta=True)


def requerir(ruta, descripcion, env_var):
    """Valida que una ruta de fuente cruda exista; si no, falla con guía."""
    if ruta is None or not Path(ruta).exists():
        raise FileNotFoundError(
            f"No se encontró {descripcion}: {ruta!s}.\n"
            f"Configurar la ruta en profe-scripts/config_local.py o exportar "
            f"{env_var} antes de correr el script."
        )
    return Path(ruta)


def empaquetar_tgz(nombre_dataset, dir_salida=None):
    """Empaqueta `dir_salida` (o data/<nombre>) en data/<nombre>.tgz."""
    dir_salida = Path(dir_salida) if dir_salida else DIR_DATOS / nombre_dataset
    ruta_tgz = DIR_DATOS / f"{nombre_dataset}.tgz"
    with tarfile.open(ruta_tgz, "w:gz") as tar:
        tar.add(dir_salida, arcname=nombre_dataset)
    print(f"Empaquetado: {ruta_tgz} ({ruta_tgz.stat().st_size / 1e6:.1f} MB)")
    return ruta_tgz


def subir_scp(ruta, destino=None):
    """Sube un archivo por scp e imprime la URL pública resultante."""
    ruta = Path(ruta)
    destino = destino or DESTINO_SCP
    if not destino:
        raise ValueError(
            "DESTINO_SCP no configurado. Definirlo en profe-scripts/config_local.py "
            "o exportar INFOVIS_DESTINO_SCP."
        )
    print(f"Subiendo {ruta.name} ({ruta.stat().st_size / 1e6:.1f} MB) a {destino}")
    r = subprocess.run(["scp", str(ruta), destino], capture_output=True, text=True)
    if r.returncode == 0:
        url = f"{URL_BASE}/{ruta.name}" if URL_BASE else ruta.name
        print(f"  OK: {url}")
    else:
        print(f"  scp falló (returncode={r.returncode}): {r.stderr.strip()}")
        print(f"  Subir manualmente: scp {ruta} {destino}")
    return r.returncode == 0


def publicar(nombre_dataset, dir_salida=None, extras=()):
    """Empaqueta el dataset y, si SUBIR_AL_SERVIDOR, lo sube con `extras`.

    `extras`: rasters u otros archivos sueltos a subir junto al .tgz.
    """
    ruta_tgz = empaquetar_tgz(nombre_dataset, dir_salida)
    if SUBIR_AL_SERVIDOR:
        subir_scp(ruta_tgz)
        for extra in extras:
            extra = Path(extra)
            if extra.exists():
                subir_scp(extra)
            else:
                print(f"  Skip (no existe): {extra}")
    else:
        destino = DESTINO_SCP or "<DESTINO_SCP no configurado>"
        print("SUBIR_AL_SERVIDOR=False (INFOVIS_SUBIR=0 en el entorno). Subir manualmente:")
        print(f"  scp {ruta_tgz} {destino}")
        for extra in extras:
            print(f"  scp {extra} {destino}")
    return ruta_tgz
