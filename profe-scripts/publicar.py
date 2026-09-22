"""Sincroniza los artefactos del curso con el servidor.

Los datasets viven en data/ como .tgz, y los rasters como archivos sueltos. Este
comando los manda al servidor con rsync, que transfiere solo lo que cambió.

    uv run python profe-scripts/publicar.py                 # qué falta por subir
    uv run python profe-scripts/publicar.py --subir         # sincroniza todo
    uv run python profe-scripts/publicar.py --subir mundo.tgz
    uv run python profe-scripts/publicar.py --empaquetar    # arma los .tgz que falten
    uv run python profe-scripts/publicar.py --listar        # qué hay en el servidor

Sin --subir no transfiere nada: hace el recorrido en seco y muestra qué haría.
Nunca borra archivos del servidor.

El barrido toma los .tgz y los rasters de data/. El curso publica su propia copia
de cada artefacto que usa, aunque otro curso tenga la suya: son cursos distintos
y ninguno depende del servidor del otro.
"""

import argparse
import subprocess
import sys

import config

PATRONES = ("*.tgz", "*.tif")


def artefactos(nombres=()):
    """Los archivos publicables de data/, o los que se pidan por nombre."""
    if nombres:
        rutas = [config.DIR_DATOS / n for n in nombres]
        faltan = [r for r in rutas if not r.exists()]
        if faltan:
            sys.exit("No existen: " + ", ".join(str(r) for r in faltan))
        return sorted(rutas)
    return sorted(r for p in PATRONES for r in config.DIR_DATOS.glob(p))


def empaquetar_pendientes():
    """Arma el .tgz de cada carpeta de data/ que todavía no lo tenga.

    Sirve para los datasets que llegaron descargados y extraídos, sin que su
    tarball haya quedado en data/.
    """
    carpetas = sorted(d for d in config.DIR_DATOS.iterdir() if d.is_dir())
    faltan = [d for d in carpetas if not (config.DIR_DATOS / f"{d.name}.tgz").exists()]
    if not faltan:
        print("Todas las carpetas de data/ ya tienen su .tgz.")
        return
    for carpeta in faltan:
        config.empaquetar_tgz(carpeta.name)


def listar_servidor():
    """Muestra lo que hay publicado, con su tamaño."""
    host, _, ruta = config.DESTINO_SCP.partition(":")
    r = subprocess.run(["ssh", host, f"ls -lh {ruta}"], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    return r.returncode


def sincronizar(rutas, subir):
    """Llama a rsync, en seco si `subir` es False."""
    orden = ["rsync", "--times", "--human-readable", "--itemize-changes", "--progress"]
    if not subir:
        orden.append("--dry-run")
    orden += [str(r) for r in rutas] + [config.DESTINO_SCP]

    print(" ".join(orden), "\n", flush=True)
    r = subprocess.run(orden)

    if r.returncode != 0:
        print(f"\nrsync falló (returncode={r.returncode}).")
    elif not subir:
        print("\nRecorrido en seco. Para transferir de verdad, repetir con --subir.")
    elif config.URL_BASE:
        print("\nPublicados en:")
        for ruta in rutas:
            print(f"  {config.URL_BASE}/{ruta.name}")
    return r.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("nombres", nargs="*", help="archivos de data/ a sincronizar")
    parser.add_argument("--subir", action="store_true", help="transferir de verdad")
    parser.add_argument("--listar", action="store_true", help="listar el servidor y salir")
    parser.add_argument("--empaquetar", action="store_true",
                        help="armar el .tgz de las carpetas de data/ que no lo tengan")
    args = parser.parse_args()

    if not config.DESTINO_SCP:
        sys.exit(
            "DESTINO_SCP no configurado. Definirlo en profe-scripts/config_local.py "
            "o exportar INFOVIS_DESTINO_SCP."
        )

    if args.listar:
        sys.exit(listar_servidor())

    if args.empaquetar:
        empaquetar_pendientes()

    rutas = artefactos(args.nombres)
    total = sum(r.stat().st_size for r in rutas) / 1e6
    print(f"{len(rutas)} archivos, {total:.1f} MB en total, hacia {config.DESTINO_SCP}\n",
          flush=True)
    sys.exit(sincronizar(rutas, args.subir))
