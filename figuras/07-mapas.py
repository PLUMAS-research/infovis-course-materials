"""Figuras de la unidad 07: mapas y datos espaciales.

Se ejecuta desde la raíz del repositorio:

    uv run python figuras/07-mapas.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
from chiricoca.base.paths import add_project_root
from shapely.geometry import box

add_project_root(marker="pyproject.toml")

from visutils.estilo import AZUL, DPI, GRIS, MAGENTA, estilo_curso  # noqa: E402
from visutils.general import descargar_datos  # noqa: E402

estilo_curso()

# %%
# La misma geometría en dos proyecciones. Mercator conserva los ángulos y por
# eso sirve para navegar, pero agranda lo que está lejos del ecuador. Equal
# Earth conserva las áreas.
#
# Mercator manda los polos al infinito, así que hay que recortar la latitud
# antes de reproyectar.

LIMITE_MERCATOR = 83
PROYECCIONES = [("Web Mercator", "EPSG:3857"), ("Equal Earth", "EPSG:8857")]
DESTACADOS = {"África": AZUL, "Groenlandia": MAGENTA}

mundo = gpd.read_parquet(descargar_datos("mundo.tgz") / "paises.parquet")
mundo = mundo[~mundo["continente"].isin(["Antarctica", "Seven seas (open ocean)"])]
mundo = gpd.clip(mundo, box(-180, -LIMITE_MERCATOR, 180, LIMITE_MERCATOR))

# La geometría de cada uno de los dos casos que necesita la comparación.
partes = {
    "África": mundo[mundo["continente"] == "Africa"],
    "Groenlandia": mundo[mundo["pais"] == "Groenlandia"],
}


def area_dibujada(geodf, crs):
    """Área que ocupa la geometría en el plano de esa proyección, en km2."""
    return geodf.to_crs(crs).area.sum() / 1e6


fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.8))

for ax, (nombre, crs) in zip(axes, PROYECCIONES):
    mundo.to_crs(crs).plot(ax=ax, color=GRIS, edgecolor="white", linewidth=0.2)
    for parte, color in DESTACADOS.items():
        partes[parte].to_crs(crs).plot(ax=ax, color=color, edgecolor="white", linewidth=0.2)

    razon = area_dibujada(partes["África"], crs) / area_dibujada(partes["Groenlandia"], crs)
    # el separador decimal en castellano es la coma
    ax.set_title(
        f"{nombre}\nÁfrica ocupa {razon:.1f} veces el área de Groenlandia".replace(".", ","),
        fontsize=8,
    )
    ax.set_axis_off()

fig.savefig("images/07-proyecciones.png", dpi=DPI, bbox_inches="tight")

# %%
# Las cifras que resume la figura, para poder citarlas.

equivalente = "EPSG:8857"
for parte in DESTACADOS:
    real = area_dibujada(partes[parte], equivalente)
    dibujada = area_dibujada(partes[parte], "EPSG:3857")
    print(f"{parte:12s} {real:>12,.0f} km2 reales, se dibuja {dibujada / real:>5.1f} veces "
          f"más grande en Web Mercator")

print()
print("Figura escrita en images/:")
print("  07-proyecciones.png")

# %%
# Las mismas cuatro proyecciones sobre Chile y sobre Santiago. Chile abarca casi
# cuarenta grados de latitud, así que la deformación cambia mucho entre el norte
# y el sur; Santiago abarca un tercio de grado y la forma casi no cambia, pero
# el área medida sí.
#
# El área verdadera se calcula sobre el elipsoide con `pyproj.Geod`, no en una
# proyección: así cada proyección se compara contra la superficie real y no
# contra otra proyección.

from pyproj import Geod  # noqa: E402

PROYECCIONES_CHILE = [
    ("Geográficas\n(EPSG:4326)", "EPSG:4326"),
    ("Web Mercator\n(EPSG:3857)", "EPSG:3857"),
    ("UTM 19 Sur\n(EPSG:32719)", "EPSG:32719"),
    ("Equal Earth\n(EPSG:8857)", "EPSG:8857"),
]

geodesico = Geod(ellps="WGS84")


def area_real(geodf):
    """Área sobre el elipsoide, en km2, sin pasar por ninguna proyección."""
    total = sum(abs(geodesico.geometry_area_perimeter(g)[0]) for g in geodf.to_crs(4326).geometry)
    return total / 1e6


def area_plana(geodf, crs):
    """Área que ocupa la geometría en el plano de esa proyección, en km2.

    En EPSG:4326 el resultado está en grados cuadrados, así que no se puede
    comparar con los demás y la función devuelve None.
    """
    if crs == "EPSG:4326":
        return None
    return geodf.to_crs(crs).area.sum() / 1e6


chile = mundo[mundo["pais"] == "Chile"]
comunas = gpd.read_parquet(descargar_datos("eod-geografia.tgz") / "comunas.parquet")
santiago = comunas[comunas["comuna"] == "Santiago"]

# La figura va chica a propósito: en la lámina la limita el alto, así que un
# figsize grande solo achica el texto en proporción.
fig, axes = plt.subplots(2, 4, figsize=(5.4, 3.5))

# Cada panel se encuadra por la altura de la geometría, no por su caja completa.
# Así los cuatro dibujos quedan del mismo alto y lo que se compara es el ancho,
# que es la deformación de la forma. Con el encuadre automático cada proyección
# llenaría su panel y las cuatro se verían iguales.
ancho_fig, alto_fig = fig.get_size_inches()
caja = axes[0][0].get_position()
razon_panel = (caja.width * ancho_fig) / (caja.height * alto_fig)

for fila, (geometria, nombre) in enumerate(((chile, "Chile"), (santiago, "Santiago"))):
    real = area_real(geometria)
    for ax, (titulo, crs) in zip(axes[fila], PROYECCIONES_CHILE):
        proyectada = geometria.to_crs(crs)
        proyectada.plot(ax=ax, color=AZUL, edgecolor="white", linewidth=0.3)

        x0, y0, x1, y1 = proyectada.total_bounds
        alto = (y1 - y0) * 1.05
        centro_x, centro_y = (x0 + x1) / 2, (y0 + y1) / 2
        ax.set_ylim(centro_y - alto / 2, centro_y + alto / 2)
        ax.set_xlim(centro_x - alto * razon_panel / 2, centro_x + alto * razon_panel / 2)
        ax.set_axis_off()

        plana = area_plana(geometria, crs)
        # el separador decimal en castellano es la coma
        desvio = (
            "el área queda en grados cuadrados"
            if plana is None
            else f"{plana / real:.2f} veces el área real".replace(".", ",")
        )
        # El nombre de la proyección va solo en la fila de arriba: repetido en
        # las dos gasta el alto que necesitan las formas.
        ax.set_title(f"{titulo}\n{desvio}" if fila == 0 else desvio, fontsize=8)

    axes[fila][0].text(-0.08, 0.5, nombre, transform=axes[fila][0].transAxes,
                       rotation=90, va="center", ha="center", fontsize=10, color=AZUL)

fig.savefig("images/07-proyecciones-chile.png", dpi=DPI, bbox_inches="tight")

# %%
FUENTES = {
    "Chile": "polígono de Natural Earth a escala 1:110m, simplificado",
    "Comuna de Santiago": "cartografía comunal",
}

for geometria, nombre in ((chile, "Chile"), (santiago, "Comuna de Santiago")):
    real = area_real(geometria)
    print(f"\n{nombre}: {real:,.0f} km2 sobre el elipsoide ({FUENTES[nombre]})")
    for titulo, crs in PROYECCIONES_CHILE:
        plana = area_plana(geometria, crs)
        if plana is not None:
            etiqueta = titulo.split("\n")[0]
            print(f"  {etiqueta:<14} {plana:>12,.0f} km2 ({plana / real:.2f} veces)")
