# %%
"""Séptima sesión de código: mapas y datos espaciales.

Los mismos viajes de la Encuesta Origen-Destino de Santiago 2012, dibujados con
las técnicas del catálogo. Cada una responde una pregunta distinta sobre el
mismo dónde, y elegir mal la técnica cambia la respuesta.

El proyecto viene definido desde el hito 1:

  Situación. La EOD registra 89.900 viajes con el origen y el destino
  georreferenciados.

  Complicación. Las decisiones de transporte se toman sobre unidades
  administrativas, y la ciudad no funciona por comuna.

  Propuesta. Comparar dónde empiezan los viajes según la unidad con que se
  agregan, e identificar los pares de comunas que concentran los flujos.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from chiricoca.colors import colormap_from_palette
from chiricoca.geo.figures import small_multiples_from_geodataframe
from chiricoca.geo.grid import count_in_grid
from chiricoca.geo.kde import kde_from_points
from chiricoca.geo.utils import (
    clip_area_geodataframe,
    clip_point_geodataframe,
    projected_centroids,
    to_point_geodataframe,
)
from chiricoca.maps import (
    aggregate_flows,
    bubble_map,
    cartogram_map,
    choropleth_map,
    contour_map,
    dot_map,
    filter_flows,
    flow_map,
    flow_tree,
    geographical_scale,
    heat_map,
    line_heat_map,
    node_composition,
    pie_glyphs,
)
from matplotlib import patheffects
from matplotlib.colors import BoundaryNorm
from matplotlib.lines import Line2D
from scipy.ndimage import gaussian_filter

from visutils.estilo import AZUL, DPI, GRIS, MAGENTA, estilo_curso
from visutils.general import descargar_archivo, descargar_datos

estilo_curso()


# La EOD entrega las coordenadas en UTM 19 Sur, que es el sistema métrico de
# Chile central. Para desplegar se usa EPSG:4326.
CRS_EOD = "EPSG:32719"
CRS_MAPA = "EPSG:4326"

# La latitud del centro del área de estudio, para convertir grados a metros en
# las barras de escala de los mapas dibujados en EPSG:4326.
LATITUD_SANTIAGO = -33.45


def barra_de_color(fig, axes, vmin, vmax, cmap, etiqueta, **kwargs):
    """Barra de color horizontal para toda la figura, rotulada con la variable.

    Un mapa sin barra muestra un patrón y no dice qué codifica el color ni entre
    qué valores se mueve. Va horizontal porque una vertical le quita ancho a los
    mapas y les rompe la razón de aspecto.
    """
    opciones = {"fraction": 0.035, "pad": 0.02, "shrink": 0.5, **kwargs}
    barra = fig.colorbar(
        plt.cm.ScalarMappable(norm=plt.Normalize(vmin, vmax), cmap=cmap),
        ax=list(axes), orientation="horizontal", **opciones,
    )
    barra.set_label(etiqueta, fontsize=8)
    barra.ax.tick_params(labelsize=7)
    return barra


def leyenda_de_tamano(ax, maximo, area_de, etiqueta, n=3):
    """Burbujas de referencia con el valor que representa cada área.

    El tamaño codifica igual que el color y también necesita escala. `area_de`
    lleva un valor del dato al área del marcador en puntos cuadrados, que es lo
    que dibuja `bubble_map`.
    """
    referencias = np.linspace(maximo / n, maximo, n).round(-2)
    manijas = [
        ax.scatter([], [], s=area_de(v), facecolor="none", edgecolor=AZUL,
                   linewidth=0.6, label=f"{int(v):,}".replace(",", "."))
        for v in referencias
    ]
    separacion = 0.4 + np.sqrt(area_de(maximo)) / 12
    leyenda = ax.legend(
        handles=manijas, title=etiqueta, loc="lower left", fontsize=6,
        title_fontsize=6, frameon=False, labelspacing=separacion,
        borderpad=0.8, handletextpad=1.4, labelcolor=AZUL,
    )
    leyenda.get_title().set_color(AZUL)
    return leyenda


def miles_en_castellano(cbar_ax=None, leyenda=None):
    """Cambia la coma de miles por punto en los rótulos de una leyenda.

    Las leyendas de chiricoca formatean con el separador de Python, así que un
    rango que dice 1,153 en realidad vale 1.153.
    """
    if cbar_ax is not None:
        eje = cbar_ax.xaxis if len(cbar_ax.get_xticks()) > 1 else cbar_ax.yaxis
        eje.set_ticks(eje.get_ticklocs())
        eje.set_ticklabels([t.get_text().replace(",", ".") for t in eje.get_ticklabels()])
    if leyenda is not None:
        for texto in leyenda.get_texts():
            texto.set_text(texto.get_text().replace(",", "."))


def leyenda_de_ancho(ax, maximo, max_width, etiqueta, n=3):
    """Tres anchos de referencia con el valor de cada uno.

    `flow_map` la trae con `legend=True`, pero `flow_tree` no, y su ancho
    codifica lo mismo.
    """
    referencias = np.linspace(maximo / n, maximo, n).round(-2)
    manijas = [
        Line2D([], [], color=AZUL, linewidth=v / maximo * max_width, solid_capstyle="butt",
               label=f"{int(v):,}".replace(",", "."))
        for v in referencias
    ]
    leyenda = ax.legend(
        handles=manijas, title=etiqueta, loc="lower left", fontsize=6,
        title_fontsize=6, frameon=False, labelspacing=1.4, borderpad=0.8,
        handletextpad=1.0, labelcolor=AZUL,
    )
    leyenda.get_title().set_color(AZUL)
    return leyenda


def barra_de_rangos(fig, axes, bordes, palette, etiqueta, **kwargs):
    """Barra de color por clases, para los mapas que dibujan el dato en rangos.

    Una barra continua sobre un mapa de siete bandas promete una precisión que
    el mapa no tiene: si el dato se muestra clasificado, la escala tiene que
    mostrar las mismas clases y dónde están sus bordes.
    """
    colores = colormap_from_palette(palette, n_colors=len(bordes) - 1)
    opciones = {"fraction": 0.04, "pad": 0.02, "shrink": 0.85, **kwargs}
    barra = fig.colorbar(
        plt.cm.ScalarMappable(norm=BoundaryNorm(bordes, colores.N), cmap=colores),
        ax=list(axes), orientation="horizontal", ticks=bordes,
        spacing="uniform", **opciones,
    )
    barra.set_label(etiqueta, fontsize=8)
    barra.ax.tick_params(labelsize=6)
    barra.ax.set_xticklabels([f"{int(b):,}".replace(",", ".") for b in bordes])
    return barra


def barra_de_escala(ax, crs=CRS_MAPA, color=AZUL):
    """Barra de distancia sobre el mapa.

    `dx` es cuánto mide en metros una unidad del eje: en un CRS métrico es un
    metro, y en grados depende de la latitud, porque un grado de longitud mide
    111,3 km en el ecuador y 92,9 km en Santiago.
    """
    metros_por_unidad = (
        1.0 if crs == CRS_EOD else 111_320 * np.cos(np.radians(LATITUD_SANTIAGO))
    )
    geographical_scale(
        ax, dx=metros_por_unidad, units="m", location="lower right",
        frameon=False, color=color, font_properties={"size": 6},
        scale_loc="top", length_fraction=0.25,
        # solo se dibuja la barra horizontal, así que el aviso por el aspecto
        # del eje no aplica: la escala en x es la que se está midiendo
        rotation="horizontal-only",
    )

# %%
# PARTE 1: de números a geometría
#
# Las coordenadas llegan como cuatro columnas numéricas. Sin un sistema de
# coordenadas son cuatro números y nada más: no se sabe a qué punto del planeta
# corresponden ni en qué unidad están.

carpeta = descargar_datos("eod-geografia.tgz")

viajes = pd.read_parquet(carpeta / "viajes.parquet")
zonas = gpd.read_parquet(carpeta / "zonas.parquet")
comunas = gpd.read_parquet(carpeta / "comunas.parquet")

print(f"{len(viajes):,} viajes, {len(zonas)} zonas, {len(comunas)} comunas")
print(viajes[["origen_x", "origen_y", "destino_x", "destino_y"]].head(3))

# %%
# `points_from_xy` arma la geometría y `crs` es lo que le da sentido. Sin ese
# argumento geopandas acepta los puntos igual, y cualquier cálculo de distancia
# o cualquier cruce con otra capa queda mal.

origenes = to_point_geodataframe(viajes, "origen_x", "origen_y", crs=CRS_EOD).to_crs(CRS_MAPA)

print(f"CRS de los puntos: {origenes.crs.to_string()}")
print(f"CRS de las zonas:  {zonas.crs.to_string()}")

# %%
# PARTE 2: el encuadre
#
# Los viajes con coordenadas válidas no están todos en Santiago. Un mapa que los
# incluya a todos comprime la ciudad hasta que no se distingue nada.

CAJA_URBANA = (-70.85, -33.65, -70.45, -33.30)

en_caja = clip_point_geodataframe(origenes, CAJA_URBANA)
print(f"Dentro del área de estudio: {len(en_caja):,} de {len(origenes):,} "
      f"({len(en_caja) / len(origenes):.1%})")
print(f"Extensión sin recortar: {[round(v, 2) for v in origenes.total_bounds]}")
print(f"Extensión recortada:    {[round(v, 2) for v in en_caja.total_bounds]}")

fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.2))

for ax, capa, titulo in ((axes[0], origenes, "Todos los viajes"),
                         (axes[1], en_caja, "Recortado al área de estudio")):
    comunas.boundary.plot(ax=ax, color=GRIS, linewidth=0.3)
    capa.plot(ax=ax, color=AZUL, markersize=0.2, alpha=0.3)
    barra_de_escala(ax)
    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()
    x0, y0, x1, y1 = capa.total_bounds
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)

# Cada figura dice qué variable muestra. Un mapa sin eso enseña una forma y deja
# al lector adivinando de qué.
fig.suptitle("Origen de cada viaje declarado en la encuesta", fontsize=11, y=1.02)
fig.savefig("images/07-encuadre.png", dpi=DPI, bbox_inches="tight")

# El recorte no es cosmético: decide qué comparaciones son posibles. Todo lo que
# sigue usa el área de estudio.

origenes = en_caja

# Las comunas se recortan cortando la geometría, y no seleccionando la comuna
# entera si toca la caja. Sin eso Lo Barnechea entra con sus mil kilómetros
# cuadrados de cordillera y la ciudad queda comprimida en una esquina del mapa.
comunas_urbanas = clip_area_geodataframe(comunas, CAJA_URBANA)
zonas_urbanas = clip_area_geodataframe(zonas, CAJA_URBANA)

# %%
# PARTE 3: dot map
#
# Una marca por observación, en su lugar. Responde dónde ocurre cada cosa, y con
# suficientes puntos deja de responderlo: los que están encima tapan a los de
# abajo y la densidad se satura.

# El centro es donde la marca falla, así que el segundo panel lo muestra de cerca.
CENTRO = (-70.70, -33.47, -70.60, -33.41)

# sin `sharex` el zoom del segundo panel se aplicaría también al primero
fig, axes = small_multiples_from_geodataframe(
    comunas_urbanas, 2, height=3.6, col_wrap=2, sharex=False, sharey=False
)

for ax, recorte, titulo in ((axes[0], CAJA_URBANA, f"{len(origenes):,} orígenes"),
                            (axes[1], CENTRO, "El centro, de cerca")):
    comunas_urbanas.plot(ax=ax, facecolor="#F4F4F7", edgecolor="white", linewidth=0.4)
    dot_map(origenes, ax=ax, size=0.4, color=AZUL, alpha=0.25, add_legend=False)
    comunas_urbanas.boundary.plot(ax=ax, color="white", linewidth=0.4, zorder=3)
    barra_de_escala(ax)
    ax.set_xlim(recorte[0], recorte[2])
    ax.set_ylim(recorte[1], recorte[3])
    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()

fig.suptitle("Origen de cada viaje", fontsize=11, y=1.02)
fig.savefig("images/07-dot-map.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 4: mapa de calor
#
# La misma pregunta cuando son demasiados los puntos. En vez de dibujar cada
# observación, estima una densidad continua y la dibuja por niveles.

# El ancho de banda es una distancia, y va en las unidades del sistema de
# coordenadas de los puntos. En grados no es una distancia: acá un grado de
# longitud mide 92,9 km y uno de latitud 111,1 km, así que un kernel circular en
# grados es una elipse en el terreno, más angosta de oriente a poniente. Por eso
# la estimación se hace en UTM, donde el ancho de banda son metros y además se
# puede decir cuántos.
origenes_metricos = origenes.to_crs(CRS_EOD)
comunas_metricas = comunas_urbanas.to_crs(CRS_EOD)

fig, axes = small_multiples_from_geodataframe(comunas_metricas, 3, height=2.8, col_wrap=3)

# La densidad estimada se desborda del área de estudio y cada ancho de banda se
# desborda distinto, así que los tres paneles quedarían de distinto tamaño. Los
# límites se fijan a mano, y las comunas van dibujadas debajo: sin ese fondo, la
# forma de la ciudad depende de la densidad y no de la geografía.
#
# La caja del área de estudio se recortó en grados, y en UTM esa caja queda
# girada casi un grado, así que su contorno deja triángulos blancos en las
# esquinas del panel. Los límites se meten un 2% hacia adentro para taparlos.
x0, y0, x1, y1 = comunas_metricas.total_bounds
margen = (x1 - x0) * 0.02
x0, x1 = x0 + margen, x1 - margen
y0, y1 = y0 + margen, y1 - margen

# `low_threshold` es el valor de densidad desde el que se empieza a pintar, y la
# densidad está en viajes por metro cuadrado: son números minúsculos y cambian
# con el ancho de banda. Así que el piso se calcula como una fracción del máximo
# de cada estimación, en vez de escribirlo a mano.
CELDAS = 2**7

# La densidad de un kernel integra uno, así que multiplicada por la cantidad de
# viajes y por el área de un kilómetro cuadrado queda en viajes por km2, que sí
# se puede leer. El máximo de cada panel es distinto, y ese es el punto de la
# figura, así que cada uno lleva su propia barra.
NIVELES_CALOR = 7

for ax, metros in zip(axes, (400, 800, 2000)):
    _, _, densidad = kde_from_points(origenes_metricos, bandwidth=metros, grid_points=CELDAS)
    piso = densidad.max() * 0.05

    comunas_metricas.plot(ax=ax, facecolor="#E6E6EC", edgecolor="none")
    heat_map(origenes_metricos, ax=ax, n_levels=NIVELES_CALOR, alpha=0.85,
             palette="rocket_r", bandwidth=metros, grid_points=CELDAS,
             low_threshold=piso)
    comunas_metricas.boundary.plot(ax=ax, color="white", linewidth=0.5, zorder=3)

    # `heat_map` rellena entre `n_levels + 1` cortes equiespaciados entre el
    # piso y el máximo, así que esos mismos cortes son los de la barra.
    bordes = np.linspace(piso, densidad.max(), NIVELES_CALOR + 1)
    barra = barra_de_rangos(
        fig, [ax], (bordes * len(origenes_metricos) * 1e6).round(-1),
        "rocket_r", "viajes/km$^2$",
    )
    barra_de_escala(ax, crs=CRS_EOD)
    ax.set_title(f"ancho de banda = {metros} m", fontsize=9)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_axis_off()

fig.suptitle("Densidad de orígenes de viaje", fontsize=11, y=1.08)
fig.savefig("images/07-heat-map.png", dpi=DPI, bbox_inches="tight")

# El ancho de banda decide qué se ve: con 400 metros aparecen los grumos y con
# dos kilómetros queda la mancha urbana. Ninguno de los tres es el correcto, y
# elegir es parte del análisis.

# %%
# PARTE 5: el spatial join
#
# La operación que conecta una capa de puntos con una de áreas: para cada punto,
# en qué polígono cae. Es lo que permite pasar de puntos sueltos a conteos por
# área, y por lo tanto lo que precede a cualquier coropleta.

asignadas = gpd.sjoin(
    origenes[["geometry", "zona_origen"]],
    zonas_urbanas[["zona", "geometry"]],
    predicate="within",
    how="inner",
)

print(f"Puntos con zona asignada: {len(asignadas):,} de {len(origenes):,}")

# La encuesta ya trae la zona de origen en una columna, así que el resultado del
# join se puede comparar con ella. Cuando una operación se puede validar contra
# algo que ya está en los datos, conviene hacerlo antes de seguir.
coincide = (asignadas["zona_origen"] == asignadas["zona"]).mean()
print(f"Coincide con la columna zona_origen: {coincide:.1%}")

# Los que no coinciden caen sobre un borde, donde la geometría de la
# zonificación y la codificación de la encuesta discrepan por unos metros.

# %%
# PARTE 6: mapa de burbujas
#
# Cuando la pregunta pasa de dónde ocurre a cuánto ocurre en cada lugar, hay que
# agregar. El área de la burbuja codifica el conteo y la posición sigue siendo
# el lugar.
#
# La unidad de agregación importa. Sobre 40 comunas, una coropleta responde lo
# mismo con menos tinta; el mapa de burbujas rinde cuando las áreas son muchas y
# de tamaños muy distintos, porque el área de la burbuja no depende del tamaño
# del polígono, y las zonas de la EOD tienen tamaños muy distintos entre sí.

MINIMO_VIAJES = 30

resumen = (
    origenes.groupby("zona_origen", observed=True)
    .agg(
        viajes=("modo", "size"),
        auto=("modo", lambda m: (m == "Auto").mean()),
        caminata=("modo", lambda m: (m == "Caminata").mean()),
    )
    .query("viajes >= @MINIMO_VIAJES")
)

burbujas = zonas_urbanas.merge(resumen, left_on="zona", right_index=True)

# El centroide de un polígono en grados no es el centroide del polígono en el
# terreno, porque un grado de longitud mide menos que uno de latitud. Hay que
# proyectar antes de calcularlo y volver después, que es lo que hace esta
# función.
burbujas["geometry"] = projected_centroids(burbujas.geometry)

print(f"Zonas con {MINIMO_VIAJES} viajes o más: {len(burbujas)} de {len(zonas_urbanas)}")
print(f"Área de zona: de {zonas_urbanas.to_crs(CRS_EOD).area.min() / 1e6:.1f} a "
      f"{zonas_urbanas.to_crs(CRS_EOD).area.max() / 1e6:.0f} km2")
print(burbujas[["auto", "caminata"]].describe().loc[["min", "50%", "max"]].round(2).to_string())

# El tamaño de la burbuja es el mismo en los dos paneles y el color cambia: así
# lo que se compara entre paneles es el color, no el tamaño.
fig, axes = small_multiples_from_geodataframe(zonas_urbanas, 2, height=4.0, col_wrap=2)

for ax, columna, titulo in ((axes[0], "auto", "Viajes en auto"),
                            (axes[1], "caminata", "Viajes a pie")):
    comunas_urbanas.plot(ax=ax, facecolor="#F4F4F7", edgecolor="white", linewidth=0.4)
    bubble_map(burbujas, size="viajes", scale=0.09, column=columna, cmap="magma_r",
               vmin=0, vmax=0.7, alpha=0.85, linewidth=0.2, add_legend=False, ax=ax)
    barra_de_escala(ax)
    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()

# El tamaño también codifica y también necesita escala: tres burbujas de
# referencia dicen cuántos viajes vale cada área.
leyenda_de_tamano(axes[0], burbujas["viajes"].max(), lambda v: v * 0.09,
                  "Viajes que salen de la zona")

# Los dos paneles comparten la escala, así que va una sola barra de color para
# los dos. Horizontal, porque una vertical le quitaría ancho a los mapas y les
# rompería la razón de aspecto.
barra = fig.colorbar(
    plt.cm.ScalarMappable(norm=plt.Normalize(0, 0.7), cmap="magma_r"),
    ax=list(axes), orientation="horizontal", fraction=0.035, pad=0.02, shrink=0.5,
)
barra.set_label("Fracción de los viajes que salen de la zona", fontsize=8)
barra.ax.tick_params(labelsize=7)

fig.suptitle("Viajes que salen de cada zona y con qué modo", fontsize=11, y=1.02)
fig.savefig("images/07-bubble-map.png", dpi=DPI, bbox_inches="tight")

# El auto y la caminata se reparten la ciudad casi en espejo. El tamaño dice
# cuántos viajes salen de cada zona y el color con qué modo, así que una burbuja
# grande y clara es una zona que genera muchos viajes y pocos en ese modo.

# %%
# El área del marcador es lo que codifica el valor, no su radio. `bubble_map`
# recibe el área, así que pasarle el conteo es lo correcto; pasarle su cuadrado
# hace que el radio quede proporcional al conteo y el área crezca con el
# cuadrado.

burbujas["radio_proporcional"] = burbujas["viajes"] ** 2 / burbujas["viajes"].max()

fig, axes = small_multiples_from_geodataframe(zonas_urbanas, 2, height=4.0, col_wrap=2)

for ax, columna, titulo in ((axes[0], "viajes", "Área proporcional a los viajes"),
                            (axes[1], "radio_proporcional", "Radio proporcional")):
    comunas_urbanas.plot(ax=ax, facecolor="#F4F4F7", edgecolor="white", linewidth=0.4)
    escala = 0.09 * burbujas["viajes"].max() / burbujas[columna].max()
    bubble_map(burbujas, size=columna, scale=escala, color=MAGENTA, alpha=0.6,
               linewidth=0.2, ax=ax)
    barra_de_escala(ax)
    # el panel derecho dibuja el cuadrado del valor, así que la leyenda tiene
    # que pasar por la misma transformación para decir la verdad
    maximo = burbujas["viajes"].max()
    area_de = (
        (lambda v, k=escala: v * k)
        if columna == "viajes"
        else (lambda v, k=escala, m=maximo: v**2 / m * k)
    )
    leyenda_de_tamano(ax, burbujas["viajes"].max(), area_de,
                      "Viajes que salen de la zona")
    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()

fig.suptitle("Viajes que salen de cada zona", fontsize=11, y=1.02)
fig.savefig("images/07-bubble-error.png", dpi=DPI, bbox_inches="tight")

# A la derecha las diferencias se exageran, porque el ojo compara el área y el
# área crece con el cuadrado del radio. Es el error clásico de las burbujas.

# %%
# PARTE 7: coropleta y la unidad de área
#
# La coropleta llena cada área con un color según su valor. La trampa es que el
# área la elige quien hace el mapa, y el mismo dato agregado sobre particiones
# distintas produce mapas distintos.
#
# Acá hay tres particiones de los mismos puntos: las comunas, que son
# administrativas; las zonas de la EOD, que se diseñaron para esta encuesta; y
# una grilla hexagonal, que no significa nada y solo divide el espacio parejo.

por_zona = origenes.groupby("zona_origen", observed=True).size().rename("viajes")
zonas_urbanas = zonas_urbanas.join(por_zona, on="zona").fillna({"viajes": 0})

por_comuna = (
    origenes.groupby("comuna_origen", observed=True).size().rename("viajes").reset_index()
)
centroides_mapa = comunas_urbanas.merge(por_comuna, left_on="comuna", right_on="comuna_origen")

# La grilla hace el spatial join por dentro: cada punto cae en un hexágono y se
# cuenta ahí.
celdas = count_in_grid(origenes, grid_level=8, column="viajes")

particiones = [
    (centroides_mapa, f"Comunas ({len(centroides_mapa)})"),
    (zonas_urbanas, f"Zonas de la EOD ({len(zonas_urbanas)})"),
    (celdas, f"Grilla H3 nivel 8 ({len(celdas)})"),
]
for capa, titulo in particiones:
    print(f"{titulo:<30} mediana {capa['viajes'].median():>6.0f} viajes por área")

fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.8))

for ax, (capa, titulo) in zip(axes, particiones):
    # cada partición tiene su propia escala de conteos, así que cada panel
    # lleva su leyenda: son tres mapas de la misma variable y no comparables
    _, datos = choropleth_map(capa, "viajes", k=6, binning="quantiles", palette="Blues",
                              edgecolor="white", linewidth=0.15, ax=ax,
                              cbar_args={"orientation": "horizontal", "location": "lower left"})
    miles_en_castellano(cbar_ax=datos["cbar_axis"])
    comunas_urbanas.boundary.plot(ax=ax, color=GRIS, linewidth=0.2, zorder=3)
    barra_de_escala(ax)
    ax.set_title(titulo, fontsize=8)
    ax.set_axis_off()

fig.suptitle("Viajes que salen de cada polígono", fontsize=11, y=1.10)
fig.savefig("images/07-unidad-de-area.png", dpi=DPI, bbox_inches="tight")

# Los tres mapas salen de la misma tabla de viajes. Lo único que cambia es sobre
# qué polígonos se sumó, y con eso cambia dónde parece estar la concentración.

# %%
# PARTE 8: el conteo y la densidad
#
# Una comuna grande acumula más viajes solo por ser grande. Dividir por el área
# cambia el mapa y cambia la conclusión.

centroides_mapa["km2"] = centroides_mapa.to_crs(CRS_EOD).area / 1e6
centroides_mapa["viajes_km2"] = centroides_mapa["viajes"] / centroides_mapa["km2"]

print(centroides_mapa.nlargest(4, "viajes")[["comuna", "viajes", "km2", "viajes_km2"]]
      .round(1).to_string(index=False))
print(centroides_mapa.nlargest(4, "viajes_km2")[["comuna", "viajes", "km2", "viajes_km2"]]
      .round(1).to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(7, 3.4))

for ax, columna, titulo in ((axes[0], "viajes", "Viajes"),
                            (axes[1], "viajes_km2", "Viajes por km²")):
    _, datos = choropleth_map(centroides_mapa, columna, k=6, binning="quantiles",
                              palette="Blues", edgecolor="white", linewidth=0.3, ax=ax,
                              cbar_args={"orientation": "horizontal", "location": "lower left"})
    miles_en_castellano(cbar_ax=datos["cbar_axis"])
    barra_de_escala(ax)
    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()

fig.suptitle("Viajes que salen de cada comuna", fontsize=11, y=1.06)
fig.savefig("images/07-conteo-densidad.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 9: flujos entre lugares
#
# Hasta acá cada viaje fue un punto de origen. Un viaje es también un par
# origen-destino, y esa es la estructura que dibuja un flow map: una línea entre
# dos lugares con el ancho proporcional a cuántos viajes la recorren.
#
# El problema de la técnica es la cantidad de pares. Con cuarenta comunas hay
# mil quinientas combinaciones posibles, y dibujarlas todas da una maraña donde
# no se lee nada.

pares = (
    origenes.groupby(["comuna_origen", "comuna_destino"], observed=True)
    .size()
    .rename("viajes")
    .reset_index()
)
entre_comunas = pares[pares["comuna_origen"] != pares["comuna_destino"]]

print(f"Pares con al menos un viaje: {len(entre_comunas):,}")
print(f"Viajes entre comunas distintas: {entre_comunas['viajes'].sum():,}")

# Todas las figuras de flujos comparten esta apariencia. El detalle que decide
# si el mapa se lee es la transparencia por tramos: con un solo valor los
# cientos de flujos chicos suman tanta tinta como los pocos grandes y tapan la
# estructura, y con un rango los chicos se desvanecen.
ESTILO_FLUJO = dict(color=AZUL, alpha=(0.2, 0.9), max_width=4.5, node_size=3)

centros = projected_centroids(comunas_urbanas.set_index("comuna").geometry)


def rotular(ax, nombres, desde=None):
    """Escribe el nombre de cada comuna sobre su centroide, con borde blanco.

    Sin nombres, un mapa de flujos es un grafo abstracto que podría ser de
    cualquier ciudad. Con `desde`, cada rótulo se corre hacia afuera en la
    dirección que va de esa comuna a su destino, así ninguno cae sobre el nudo
    de flechas del centro.
    """
    for nombre in dict.fromkeys(nombres):
        punto = centros[nombre]
        if desde is None:
            corrimiento, horizontal, vertical = (0, 7), "center", "bottom"
        else:
            hacia = punto.x - centros[desde].x, punto.y - centros[desde].y
            largo = max(np.hypot(*hacia), 1e-9)
            corrimiento = (12 * hacia[0] / largo, 12 * hacia[1] / largo)
            horizontal = "left" if hacia[0] > 0 else "right"
            vertical = "bottom" if hacia[1] > 0 else "top"
        ax.annotate(
            nombre,
            xy=(punto.x, punto.y),
            xytext=corrimiento,
            textcoords="offset points",
            fontsize=7,
            color=AZUL,
            ha=horizontal,
            va=vertical,
            path_effects=[patheffects.withStroke(linewidth=2.5, foreground="white")],
        )

# %%
# Hay cinco criterios para decidir qué pares dibujar, y cada uno responde una
# pregunta distinta. Los tres primeros son umbrales sobre el peso. El de
# disparidad compara el peso de cada flujo con lo que le tocaría si su origen
# repartiera el total al azar entre sus destinos. El de excedente lo compara con
# lo que se esperaría si origen y destino fueran independientes, que es el mismo
# valor esperado de una tabla de contingencia, así que mide afinidad entre dos
# lugares y no volumen.

CRITERIOS = [
    ("min_weight=100", dict(min_weight=100)),
    ("top_k=2 por origen", dict(top_k=2)),
    ("share=0,5", dict(share=0.5)),
    ("disparity=0,05", dict(disparity=0.05)),
    ("surplus=3", dict(surplus=3)),
]

for nombre, argumentos in CRITERIOS:
    quedan = filter_flows(
        entre_comunas, "comuna_origen", "comuna_destino", "viajes", **argumentos
    )
    fraccion = quedan["viajes"].sum() / entre_comunas["viajes"].sum()
    mayor = quedan.nlargest(1, "viajes").iloc[0]
    print(f"{nombre:20s} {len(quedan):4d} pares, {fraccion:5.1%} del flujo, "
          f"el mayor {mayor['comuna_origen']} a {mayor['comuna_destino']}")

# El umbral de peso conserva lo que sale de las comunas grandes y borra del mapa
# a las chicas. El de destinos principales le deja a cada comuna sus dos flujos
# mayores, tenga mucho o poco, así que la periferia sobrevive. El de disparidad
# deja los flujos que pesan más de lo esperable, que es la columna vertebral de
# la red. El de excedente cambia de pregunta: su flujo mayor une dos comunas
# vecinas en vez de ir al centro.

# %%
# Filtrar es el primero de tres pasos, y cada uno saca una fuente distinta de
# desorden: el filtro saca los pares que no aportan, fundir los dos sentidos
# saca las lentes que forman la ida y la vuelta al curvarse hacia lados
# opuestos, y agrupar acerca los flujos que van al mismo lado hasta que viajan
# juntos por un corredor común, con lo que se van los cruces.

PASOS = [
    (f"Los {len(entre_comunas):,} pares".replace(",", "."), {}),
    ("Filtrar", dict(disparity=0.05)),
    ("Fundir los dos sentidos", dict(disparity=0.05, aggregate="total")),
]

# La figura va en una lámina de ancho completo, donde se escala hasta ocuparla.
# Con varios paneles el `height` chico es lo que deja el texto legible: si la
# figura mide más pulgadas que la lámina, el texto se achica al escalarla.
fig, axes = small_multiples_from_geodataframe(comunas_urbanas, 3, height=2.8, col_wrap=3)

for ax, (titulo, argumentos) in zip(axes, PASOS):
    comunas_urbanas.plot(ax=ax, facecolor="#F0F0F4", edgecolor="white", linewidth=0.4)

    # El ancho también es una escala. La leyenda va en el último panel y vale
    # para los tres, que comparten la misma referencia de ancho.
    es_ultimo = titulo == PASOS[-1][0]
    flow_map(
        entre_comunas,
        comunas_urbanas,
        source="comuna_origen",
        target="comuna_destino",
        weight="viajes",
        node_column="comuna",
        legend=es_ultimo,
        legend_args={"loc": "lower left", "fontsize": 6, "title": "viajes"},
        ax=ax,
        **ESTILO_FLUJO,
        **argumentos,
    )
    if es_ultimo:
        miles_en_castellano(leyenda=ax.get_legend())
    barra_de_escala(ax)
    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()

fig.suptitle("Viajes entre comunas distintas", fontsize=11, y=1.06)
fig.savefig("images/07-flujos-reduccion.png", dpi=DPI, bbox_inches="tight")

# Los tres pasos son independientes entre sí y se pueden usar por separado.

# %%
# El tercer paso necesita verse de cerca. Agrupar mueve cada trazo hacia donde
# la densidad de trazos es mayor, o sea hacia el camino más transitado que tiene
# al lado, y repite ese empujón varias veces con un radio cada vez menor. Los
# flujos que iban al mismo lado terminan pegados en un corredor común, igual que
# muchas calles que desembocan en una avenida.

fig, axes = small_multiples_from_geodataframe(comunas_urbanas, 2, height=3.6, col_wrap=2)

for ax, (titulo, agrupar) in zip(axes, (("Sin agrupar", False), ("Agrupado", True))):
    comunas_urbanas.plot(ax=ax, facecolor="#F0F0F4", edgecolor="white", linewidth=0.4)
    _, dibujados = flow_map(
        entre_comunas,
        comunas_urbanas,
        source="comuna_origen",
        target="comuna_destino",
        weight="viajes",
        node_column="comuna",
        disparity=0.05,
        aggregate="total",
        bundle=agrupar,
        return_flows=True,
        legend=not agrupar,
        legend_args={"loc": "lower left", "fontsize": 6, "title": "viajes"},
        ax=ax,
        **ESTILO_FLUJO,
    )
    miles_en_castellano(leyenda=ax.get_legend())
    rotular(ax, dibujados.nlargest(5, "viajes")["comuna_origen"].tolist()
            + dibujados.nlargest(5, "viajes")["comuna_destino"].tolist())
    barra_de_escala(ax)
    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()

fig.suptitle("Viajes entre comunas distintas", fontsize=11, y=1.02)
fig.savefig("images/07-flujos-corredores.png", dpi=DPI, bbox_inches="tight")

# El agrupamiento es el único de los tres pasos que cambia lo que el mapa
# afirma: un corredor dice entre qué zonas de la ciudad se mueve el flujo y ya
# no por dónde va cada par. A cambio, deja ver cuáles son esas zonas.

# %%
# Un flow map también se lee bien con un origen fijo y varios destinos, porque
# ahí la pregunta queda planteada de una manera: ¿a dónde se viaja desde Puente
# Alto?
#
# La punta de flecha indica la dirección. Se dimensiona con el ancho de la
# línea, pero con un piso: sin él la flecha de un flujo chico no se ve al lado
# de la de uno grande.

ORIGENES = ["Puente Alto", "Providencia"]
UMBRAL_FLUJO = 40


def flujos_desde(comuna):
    """Los destinos de una comuna, sin los viajes que se quedan en ella."""
    return entre_comunas.query("comuna_origen == @comuna and viajes >= @UMBRAL_FLUJO")


for comuna in ORIGENES:
    total = pares.query("comuna_origen == @comuna")["viajes"].sum()
    internos = pares.query("comuna_origen == @comuna and comuna_destino == @comuna")["viajes"].sum()
    salidas = flujos_desde(comuna)
    print(f"{comuna}: {total:,} viajes, {internos / total:.1%} dentro de la comuna, "
          f"{len(salidas)} destinos con {UMBRAL_FLUJO} o más")
    print(salidas.nlargest(3, "viajes")[["comuna_destino", "viajes"]].to_string(index=False))

# Los dos paneles comparten el encuadre. Con extensiones distintas cada mapa
# tendría su propia escala y la comparación entre los dos no se sostendría.
fig, axes = small_multiples_from_geodataframe(comunas_urbanas, 2, height=3.6, col_wrap=2)

for ax, comuna in zip(axes, ORIGENES):
    salidas = flujos_desde(comuna)

    comunas_urbanas.plot(ax=ax, facecolor="#EAEAF0", edgecolor="white", linewidth=0.6)
    comunas_urbanas.query("comuna == @comuna").plot(ax=ax, facecolor=MAGENTA, alpha=0.25)

    flow_map(
        salidas,
        comunas_urbanas,
        source="comuna_origen",
        target="comuna_destino",
        weight="viajes",
        node_column="comuna",
        arrows=True,
        node_color="white",
        node_edgecolor=AZUL,
        legend=comuna == ORIGENES[0],
        legend_args={"loc": "lower left", "fontsize": 6, "title": "viajes"},
        ax=ax,
        **ESTILO_FLUJO,
    )
    miles_en_castellano(leyenda=ax.get_legend())

    # Rotular todos los destinos satura el mapa: van los tres que más reciben.
    rotular(ax, salidas.nlargest(3, "viajes")["comuna_destino"], desde=comuna)

    barra_de_escala(ax)
    ax.set_title(f"Desde {comuna}", fontsize=9)
    ax.set_axis_off()

fig.suptitle("Viajes que salen de una comuna, por destino", fontsize=11, y=1.02)
fig.savefig("images/07-flow-map.png", dpi=DPI, bbox_inches="tight")

# La comuna periférica manda casi todo hacia el centro por un corredor; la
# central reparte en todas las direcciones. La línea es una simplificación
# fuerte: nadie viaja en línea recta, y los dos extremos son centroides de
# comuna, no lugares donde alguien esté. Lo que el flow map afirma es que existe
# un flujo entre dos áreas, con qué volumen y en qué sentido, no por dónde pasa.

# %%
# En el día completo la ida y la vuelta de cada par casi se cancelan, así que
# los pares grandes no dicen hacia dónde se mueve la ciudad. Cortar por hora es
# lo que hace aparecer la conmutación.

VENTANAS = [("Mañana (6 a 9)", 6, 9), ("Tarde (17 a 20)", 17, 20)]


def pares_en(desde, hasta):
    """Los pares entre comunas distintas de los viajes que parten en la ventana."""
    ventana = origenes[origenes["hora_inicio"].between(desde, hasta)]
    p = (
        ventana.groupby(["comuna_origen", "comuna_destino"], observed=True)
        .size()
        .rename("viajes")
        .reset_index()
    )
    return p[p["comuna_origen"] != p["comuna_destino"]]


def desbalance(p):
    """Qué fracción del par se lleva su sentido mayor, en los pares con 100 viajes o más."""
    total = aggregate_flows(p, "comuna_origen", "comuna_destino", "viajes")
    con_ambos = total.merge(
        p, on=["comuna_origen", "comuna_destino"], suffixes=("_par", "_ida")
    ).query("viajes_par >= 100")
    mayor = con_ambos[["viajes_ida"]].assign(
        vuelta=con_ambos["viajes_par"] - con_ambos["viajes_ida"]
    ).max(axis=1)
    return len(con_ambos), (mayor / con_ambos["viajes_par"]).median()


for nombre, p in (
    ("Todo el día", entre_comunas),
    ("Mañana (6 a 9)", pares_en(6, 9)),
    ("Tarde (17 a 20)", pares_en(17, 20)),
):
    cuantos, fraccion = desbalance(p)
    print(f"{nombre:16s} {cuantos:3d} pares con 100 viajes o más; "
          f"el sentido mayor se lleva el {fraccion:.0%}")

# Ese desbalance es lo que el saldo deja a la vista: la resta de los dos
# sentidos, dibujada en el sentido que domina.
fig, axes = small_multiples_from_geodataframe(comunas_urbanas, 2, height=3.6, col_wrap=2)

for ax, (titulo, desde, hasta) in zip(axes, VENTANAS):
    comunas_urbanas.plot(ax=ax, facecolor="#F0F0F4", edgecolor="white", linewidth=0.4)

    # `max_value` fija el ancho de referencia en los dos paneles, si no cada uno
    # escala con su propio máximo y los grosores no se pueden comparar.
    _, dibujados = flow_map(
        pares_en(desde, hasta),
        comunas_urbanas,
        source="comuna_origen",
        target="comuna_destino",
        weight="viajes",
        node_column="comuna",
        aggregate="net",
        min_weight=60,
        arrows=True,
        max_value=400,
        return_flows=True,
        legend=desde == VENTANAS[0][1],
        legend_args={"loc": "lower left", "fontsize": 6, "title": "saldo de viajes"},
        ax=ax,
        **ESTILO_FLUJO,
    )
    miles_en_castellano(leyenda=ax.get_legend())

    # Sin nombres el mapa es un grafo abstracto: van las comunas que reciben o
    # emiten los saldos mayores.
    rotular(ax, dibujados.nlargest(6, "viajes")["comuna_destino"].tolist()
            + dibujados.nlargest(6, "viajes")["comuna_origen"].tolist())

    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()

    barra_de_escala(ax)
    print(f"{titulo}: {len(dibujados)} saldos de 60 viajes o más")
    print(dibujados.nlargest(3, "viajes").to_string(index=False))

fig.suptitle("Saldo de viajes entre cada par de comunas", fontsize=11, y=1.02)
fig.savefig("images/07-flujos-saldo.png", dpi=DPI, bbox_inches="tight")

# En la mañana los saldos apuntan a la comuna de Santiago y en la tarde son los

# mismos pares al revés. Ninguna de las dos cosas se ve en la matriz completa,
# donde cada par lleva la suma de los dos sentidos de todo el día.

# %%
# El punto que marca cada lugar puede reemplazarse por un glifo, o sea por una
# marca compuesta que lleve varios canales dentro. Acá el tamaño sigue siendo el
# total que entra y sale del lugar, y la torta reparte ese total entre
# categorías.
#
# La figura va sobre la punta de la mañana y no sobre el día completo. En el día
# completo cada par se reparte en partes iguales entre sus dos sentidos, así que
# las semiflechas salen simétricas y la dirección no dice nada.

MODOS = {
    "Auto": "Auto",
    "Bus TS": "Bus",
    "Bus TS - Metro": "Bus y Metro",
    "Metro": "Metro",
    "Caminata": "Caminata",
}
PROPOSITOS = {
    "Al trabajo": "Trabajo",
    "Al estudio": "Estudio",
    "De compras": "Compras",
    "Trámites": "Trámites",
    "Recreación": "Recreación",
}

en_punta = origenes[origenes["hora_inicio"].between(6, 9)]
con_categorias = en_punta.assign(
    grupo=en_punta["modo"].astype(str).map(MODOS).fillna("Otros"),
    motivo=en_punta["proposito"].astype(str).map(PROPOSITOS).fillna("Otros"),
)


def pares_por(categoria, tabla):
    """Los pares entre comunas distintas, desagregados por una categoría."""
    p = (
        tabla.groupby(["comuna_origen", "comuna_destino", categoria], observed=True)
        .size()
        .rename("viajes")
        .reset_index()
    )
    return p[p["comuna_origen"] != p["comuna_destino"]]


print(f"Viajes que parten entre las 6 y las 9: {len(en_punta):,} de {len(origenes):,}")
print(con_categorias["motivo"].value_counts(normalize=True).mul(100).round(1).to_string())

COLORES_MODO = {
    "Auto": AZUL, "Bus": MAGENTA, "Bus y Metro": "#E08D2F",
    "Metro": "#7B4EA8", "Caminata": "#2E9E8F", "Otros": GRIS,
}
COLORES_MOTIVO = {
    "Trabajo": AZUL, "Estudio": MAGENTA, "Compras": "#E08D2F",
    "Trámites": "#7B4EA8", "Recreación": "#2E9E8F", "Otros": GRIS,
}

GLIFOS = [
    ("Con qué modo", pares_por("grupo", con_categorias), "grupo", COLORES_MODO),
    ("Para qué", pares_por("motivo", con_categorias), "motivo", COLORES_MOTIVO),
]

fig, axes = small_multiples_from_geodataframe(comunas_urbanas, 2, height=3.6, col_wrap=2)

for ax, (titulo, desagregados, categoria, colores) in zip(axes, GLIFOS):
    # `node_composition` arma la tabla de lugar por categoría y `pie_glyphs`
    # devuelve la función con que `flow_map` dibuja cada nodo.
    # `direction="both"` acumula lo que sale y lo que llega, igual que el tamaño
    # del nodo. Con solo lo que sale, una comuna que en esta ventana únicamente
    # recibe queda sin fila y se dibuja como un círculo gris.
    reparto = node_composition(
        desagregados, "comuna_origen", "comuna_destino", "viajes",
        by=categoria, direction="both",
    )

    comunas_urbanas.plot(ax=ax, facecolor="#F0F0F4", edgecolor="white", linewidth=0.4)
    flow_map(
        pares_en(6, 9),
        comunas_urbanas,
        source="comuna_origen",
        target="comuna_destino",
        weight="viajes",
        node_column="comuna",
        disparity=0.05,
        bundle=True,
        arrows="half",
        color=AZUL,
        alpha=(0.15, 0.55),
        max_width=4.0,
        node_scale=0.09,
        node_glyph=pie_glyphs(
            reparto,
            palette=colores,
            edgecolor="none",
            legend=True,
            legend_args={"loc": "lower left", "fontsize": 6},
        ),
        ax=ax,
    )
    barra_de_escala(ax)
    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()

fig.suptitle("Viajes de la mañana entre comunas, por modo y propósito",
             fontsize=11, y=1.02)
fig.savefig("images/07-flujos-glifos.png", dpi=DPI, bbox_inches="tight")

# Los dos sentidos van por separado y con semiflecha, así cada glifo tiene una
# banda que entra y otra que sale, cada una a un lado del corredor, y en esta
# ventana la banda que va hacia el centro es visiblemente más gruesa que la que
# vuelve. Los flujos van atenuados a propósito: el glifo pasa a ser la marca
# principal y la red queda de contexto.

# %%
# Con un origen y quince destinos las líneas se cruzan igual, porque cada una
# sale por su cuenta. El flow map layout agrupa los destinos por cercanía
# geográfica y manda el flujo por troncos que se van dividiendo, así el ancho de
# cada rama es la suma de lo que va a sus hojas.

ORIGEN_ARBOL = "Puente Alto"

fig, axes = small_multiples_from_geodataframe(
    comunas_urbanas, 2, height=3.6, col_wrap=2, sharex=False, sharey=False
)

for ax, titulo in ((axes[0], "Una línea por destino"), (axes[1], "Agrupado en un árbol")):
    comunas_urbanas.plot(ax=ax, facecolor="#F4F4F7", edgecolor="white", linewidth=0.4)
    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()

desde_origen = flujos_desde(ORIGEN_ARBOL)

flow_map(desde_origen, comunas_urbanas, source="comuna_origen", target="comuna_destino",
         weight="viajes", node_column="comuna", arrows=True, legend=True,
         legend_args={"loc": "lower left", "fontsize": 6, "title": "viajes"},
         ax=axes[0], **ESTILO_FLUJO)
miles_en_castellano(leyenda=axes[0].get_legend())
flow_tree(desde_origen, comunas_urbanas, source="comuna_origen",
          target="comuna_destino", weight="viajes", origin=ORIGEN_ARBOL,
          node_column="comuna", color=AZUL, ax=axes[1])

for ax in axes:
    barra_de_escala(ax)

fig.suptitle(f"Viajes que salen de {ORIGEN_ARBOL}, por destino", fontsize=11, y=1.02)
fig.savefig("images/07-flow-layout.png", dpi=DPI, bbox_inches="tight")

# El árbol no dice por dónde va cada viaje: dice cómo se reparte el flujo que
# sale de un lugar. Se lee desde el origen hacia las hojas, y no par por par.

# %%
# El mismo árbol sirve para la pregunta al revés, si se fija el otro extremo del
# par: de dónde viene lo que llega a un lugar. Acá van todos los destinos, sin
# umbral, que es una cantidad con la que el abanico ya no sirve.

ORIGEN_DOBLE = "Santiago"
DIRECCIONES = [("out", f"Sale de {ORIGEN_DOBLE}"), ("in", f"Llega a {ORIGEN_DOBLE}")]

fig, axes = small_multiples_from_geodataframe(comunas_urbanas, 2, height=3.6, col_wrap=2)

# El mismo `max_value` en los dos paneles hace comparables los grosores, y es el
# número que necesita la leyenda de ancho: sin fijarlo, cada panel escala con su
# propio máximo y la leyenda diría cualquier cosa.
ANCHO_MAXIMO = 6.0
REFERENCIA = max(
    entre_comunas.query("comuna_origen == @ORIGEN_DOBLE")["viajes"].max(),
    entre_comunas.query("comuna_destino == @ORIGEN_DOBLE")["viajes"].max(),
)

for ax, (direccion, titulo) in zip(axes, DIRECCIONES):
    comunas_urbanas.plot(ax=ax, facecolor="#F4F4F7", edgecolor="white", linewidth=0.4)
    flow_tree(
        entre_comunas,
        comunas_urbanas,
        source="comuna_origen",
        target="comuna_destino",
        weight="viajes",
        origin=ORIGEN_DOBLE,
        direction=direccion,
        node_column="comuna",
        color=AZUL,
        max_value=REFERENCIA,
        max_width=ANCHO_MAXIMO,
        ax=ax,
    )
    barra_de_escala(ax)
    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()

leyenda_de_ancho(axes[0], REFERENCIA, ANCHO_MAXIMO, "viajes")

fig.suptitle(f"Viajes entre {ORIGEN_DOBLE} y las demás comunas", fontsize=11, y=1.02)
fig.savefig("images/07-flujos-arbol-direccion.png", dpi=DPI, bbox_inches="tight")

salen = entre_comunas.query("comuna_origen == @ORIGEN_DOBLE")["viajes"].sum()
llegan = entre_comunas.query("comuna_destino == @ORIGEN_DOBLE")["viajes"].sum()
print(f"{ORIGEN_DOBLE}: salen {salen:,} viajes hacia otras comunas, llegan {llegan:,}")
# %%
# PARTE 10: mapa de calor de líneas
#
# Las técnicas anteriores agregan por área o por par de áreas. Un mapa de calor
# de líneas trabaja sobre trazados: acumula el peso de muchas rutas en los
# tramos que comparten, así una avenida por donde pasan cuarenta recorridos se
# distingue de una calle por donde pasa uno.
#
# Los datos son los recorridos del transporte público de Santiago, con su
# frecuencia en la punta de la mañana. Son rutas reales, no líneas rectas entre
# origen y destino: una recta entre dos comunas atraviesa lo que sea que haya en
# medio, y acumular rectas produce corredores que no existen en la calle.

carpeta_recorridos = descargar_datos("recorridos.tgz")
recorridos = gpd.read_parquet(carpeta_recorridos / "recorridos.parquet")
recorridos = clip_area_geodataframe(recorridos, CAJA_URBANA).to_crs(CRS_EOD)

print(f"Recorridos dentro del área de estudio: {len(recorridos)}")
print(f"Buses por hora: mediana {recorridos['buses_hora'].median():.1f}, "
      f"máximo {recorridos['buses_hora'].max():.1f}")
print(f"Largo mediano: {recorridos.length.median() / 1000:.1f} km")

# El acercamiento al centro es parte de la técnica: a escala de ciudad se leen
# los corredores, y de cerca se separan las calles que los componen.
#
# El recorte se deriva del encuadre completo achicándolo por un factor, en vez
# de escribir sus cuatro coordenadas. Así los dos paneles tienen la misma
# proporción y quedan del mismo alto; con proporciones distintas matplotlib
# achica uno de los dos para respetar la escala.
CENTRO = to_point_geodataframe(
    pd.DataFrame({"x": [-70.6506], "y": [-33.4372]}), "x", "y", crs=CRS_MAPA
).to_crs(CRS_EOD).geometry.iloc[0]
ZOOM = 0.22

fondo = comunas_urbanas.to_crs(CRS_EOD)
x0, y0, x1, y1 = fondo.total_bounds
ancho, alto = (x1 - x0) * ZOOM / 2, (y1 - y0) * ZOOM / 2

# Sin sharex/sharey el acercamiento del segundo panel se aplicaría también al
# primero, porque los ejes vienen compartidos por omisión.
fig, axes = small_multiples_from_geodataframe(
    fondo, 2, height=4.0, col_wrap=2, sharex=False, sharey=False
)

for ax, titulo in ((axes[0], "La ciudad"), (axes[1], "El centro")):
    fondo.plot(ax=ax, facecolor="#14142a", edgecolor="none")
    _, coleccion = line_heat_map(recorridos, weight="buses_hora", segment_length=60,
                                 snap=30, palette="magma", max_width=3.5,
                                 return_collection=True, ax=ax)
    barra_de_escala(ax, crs=CRS_EOD)
    ax.set_title(titulo, fontsize=9)
    ax.set_axis_off()

axes[1].set_xlim(CENTRO.x - ancho, CENTRO.x + ancho)
axes[1].set_ylim(CENTRO.y - alto, CENTRO.y + alto)

# El color y el grosor codifican lo mismo, así que una sola barra los explica.
barra = fig.colorbar(coleccion, ax=list(axes), orientation="horizontal",
                     fraction=0.035, pad=0.02, shrink=0.5)
barra.set_label("Buses por hora que pasan por el tramo", fontsize=8)
barra.ax.tick_params(labelsize=7)

fig.suptitle("Frecuencia acumulada del transporte público a las 8 de la mañana",
             fontsize=11, y=1.02)
fig.savefig("images/07-lineas-calor.png", dpi=DPI, bbox_inches="tight")

# Los ejes que aparecen son avenidas: la Alameda, Vicuña Mackenna, Américo
# Vespucio. La técnica sirve para cualquier conjunto de trazados que compartan
# tramos, como trazas GPS o rutas de ciclistas.

# %%
# PARTE 11: cartogramas
#
# La coropleta de la parte 8 tiene un problema que ninguna paleta arregla: el
# ojo suma el color por el área que ocupa, así que una comuna grande pesa más
# aunque su valor sea menor. El cartograma da vuelta el trato y deforma el área
# para que sea ella la que codifique el valor.

fig, axes = plt.subplots(1, 4, figsize=(7.6, 2.3))

_, datos = choropleth_map(centroides_mapa, "viajes", k=6, binning="quantiles",
                          palette="Blues", edgecolor="white", linewidth=0.3, ax=axes[0],
                          cbar_args={"orientation": "horizontal", "location": "lower left"})
miles_en_castellano(cbar_ax=datos["cbar_axis"])
axes[0].set_title("Coropleta", fontsize=8)

for ax, kind, titulo in ((axes[1], "non_contiguous", "No contiguo"),
                         (axes[2], "dorling", "Dorling"),
                         (axes[3], "contiguous", "Contiguo")):
    if kind != "contiguous":
        comunas_urbanas.boundary.plot(ax=ax, color=GRIS, linewidth=0.3)
    _, deformado = cartogram_map(centroides_mapa, "viajes", kind=kind, ax=ax,
                                 color=AZUL, edgecolor="white", linewidth=0.3)
    ax.set_title(titulo, fontsize=8)

# El área de los tres cartogramas codifica la misma variable que el color de la
# coropleta, así que la leyenda de esa primera vale para los cuatro paneles. La
# barra de distancia, en cambio, va solo en la coropleta: en un cartograma la
# geometría está deformada a propósito y una escala de kilómetros mentiría.
barra_de_escala(axes[0])

for ax in axes:
    ax.set_axis_off()

fig.suptitle("Viajes que salen de cada comuna", fontsize=11, y=1.06)
fig.savefig("images/07-cartogramas.png", dpi=DPI, bbox_inches="tight")

peor = deformado.loc[deformado["error_area"].idxmax(), "comuna"]
print(f"Error de área que queda en el contiguo: medio {deformado['error_area'].mean():.1%}, "
      f"máximo {deformado['error_area'].max():.1%} en {peor}")

# Los tres cartogramas pagan algo distinto. El no contiguo conserva la forma de
# cada comuna y pierde que estén pegadas. El de Dorling pierde la forma y gana
# que los tamaños se comparen sin estorbo. El contiguo conserva las dos cosas y
# deforma, y no siempre llega: una comuna que tiene que achicarse al 4% de su
# área no puede colapsar sin invertirse, así que conviene mirar el error.

# %%
# PARTE 12: isolíneas sobre un campo
#
# Los mapas anteriores parten de observaciones sueltas. Un campo escalar es otra
# cosa: un valor por celda de una grilla que cubre todo el territorio. La
# isolínea une los puntos donde el campo vale lo mismo, que es de donde salen
# las curvas de nivel de un mapa topográfico.

with rasterio.open(descargar_archivo("ndvi-santiago-2023.tif")) as fuente:
    ndvi = fuente.read(1).astype(float)
    limites = fuente.bounds

# Las celdas sin dato se rellenan con el promedio, porque el suavizado y las
# curvas no saben qué hacer con un hueco.
ndvi = np.where(np.isfinite(ndvi), ndvi, np.nanmean(ndvi))

print(f"NDVI: grilla de {ndvi.shape[0]} por {ndvi.shape[1]} celdas de 30 m")
print(f"  valores entre {ndvi.min():.2f} y {ndvi.max():.2f}")

# Las isolíneas necesitan un campo suave: a treinta metros cada celda produce su
# propia curva. Cuánto suavizar decide qué dicen las curvas, igual que el ancho
# de banda de un mapa de calor.
NIVELES = [0.1, 0.2, 0.3, 0.4]

fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.6))

for ax, sigma in zip(axes, (2, 8, 20)):
    campo = gaussian_filter(ndvi, sigma=sigma)[::3, ::3]
    ax.imshow(campo, cmap="BrBG", vmin=-0.2, vmax=0.6, aspect="auto",
              extent=(limites.left, limites.right, limites.bottom, limites.top))
    contour_map(campo, (limites.left, limites.bottom, limites.right, limites.top),
                levels=NIVELES, color="black", linewidths=0.5,
                labels=(sigma == 20), label_format="{:.1f}", ax=ax)
    barra_de_escala(ax, crs=CRS_EOD)
    ax.set_title(f"suavizado sigma = {sigma}", fontsize=8)
    ax.set_axis_off()

# El campo se dibuja continuo, así que la barra va continua; las marcas son los
# cuatro niveles donde se trazaron las curvas, para poder leerlas en la barra.
barra = barra_de_color(fig, axes, -0.2, 0.6, "BrBG",
                       "NDVI, de suelo desnudo a vegetación densa")
barra.set_ticks([-0.2, *NIVELES, 0.6])
fig.suptitle("Índice de vegetación de Santiago, 2023", fontsize=11, y=1.06)
fig.savefig("images/07-isolineas.png", dpi=DPI, bbox_inches="tight")

# Con poco suavizado hay una curva por manchón de vegetación y el mapa no se
# lee; con mucho quedan tres o cuatro regiones y se pierde el detalle del
# interior de la ciudad. El nivel intermedio es una decisión, no un valor que
# venga con los datos.

# %%
# PARTE 13: la proyección decide lo que afirma el mapa
#
# Todo lo anterior se dibujó en EPSG:4326. Para medir distancias o áreas hay que
# pasar a un sistema métrico, y para comparar áreas entre latitudes distintas
# hace falta uno que las conserve.

muestra = comunas_urbanas.head(3)[["comuna"]].copy()
for nombre, crs in (("EPSG:4326", 4326), ("UTM 19S", 32719), ("Web Mercator", 3857)):
    muestra[nombre] = comunas_urbanas.head(3).to_crs(crs).area.values

print("Área de tres comunas en tres sistemas de coordenadas:")
print(muestra.to_string(index=False))

# En EPSG:4326 el área sale en grados cuadrados, que no es una unidad de
# superficie. En UTM 19S sale en metros cuadrados y sirve para Santiago. Web
# Mercator también da metros, pero agranda a medida que se aleja del ecuador.
