# %%
"""Cuarta sesión de código: el mismo dato, distintos canales.

Un atributo se puede codificar de muchas maneras, y la elección cambia qué
tareas se pueden resolver con el gráfico. Acá se codifica el mismo atributo con
cinco canales distintos, se mide cuánto cuesta leer cada uno y se prueba qué
pasa cuando el canal no corresponde al tipo del atributo.

Los datos son los siniestros de tránsito de la Región Metropolitana, agregados
por comuna.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from chiricoca.geo.figures import figure_from_geodataframe

from visutils.estilo import AZUL, DPI, GRIS, MAGENTA, estilo_curso
from visutils.general import descargar_datos

estilo_curso(dpi=DPI)

carpeta = descargar_datos("siniestros.tgz")
siniestros = gpd.read_parquet(carpeta / "siniestros-rm.parquet")

# Diez comunas alcanzan para comparar sin que el gráfico se vuelva un catálogo.
por_comuna = (
    siniestros.groupby("comuna", observed=True)
    .agg(siniestros=("victimas", "size"), victimas=("victimas", "sum"))
    .nlargest(10, "siniestros")
    .sort_values("siniestros")
)
print(por_comuna)

# %%
# PARTE 1: una marca, varios canales
#
# La marca es la primitiva geométrica (punto, línea, área) y el canal es la
# propiedad que controla su apariencia (posición, largo, área, ángulo, color).
# El tipo de marca limita los canales disponibles: un punto no tiene largo.

valores = por_comuna["siniestros"]
etiquetas = valores.index

fig, axes = plt.subplots(1, 5, figsize=(11, 3))

# Posición en escala común: la marca es un punto y lo que varía es dónde está.
axes[0].scatter(valores, range(len(valores)), color=AZUL, s=18)
axes[0].set_yticks(range(len(valores)))
axes[0].set_yticklabels(etiquetas, fontsize=6)
axes[0].set_title("Posición", fontsize=9)

# Largo: la marca es una línea que arranca en una base común.
axes[1].barh(range(len(valores)), valores, color=AZUL, height=0.7)
axes[1].set_yticks([])
axes[1].set_title("Largo", fontsize=9)

# Área: el parámetro s de scatter ya es el área del marcador, así que se le
# pasa el valor normalizado. Pasarle el radio haría el área proporcional al
# cuadrado del dato, que es el error clásico de los gráficos de burbujas.
axes[2].scatter(
    [0] * len(valores), range(len(valores)),
    s=valores / valores.max() * 600, color=AZUL,
)
axes[2].set_xlim(-1, 1)
axes[2].set_yticks([])
axes[2].set_title("Área", fontsize=9)

# Ángulo: el mismo dato como porciones de un círculo. El anchor alinea el
# círculo con el resto de los paneles, que pie() reposiciona por su cuenta.
axes[3].pie(valores, colors=plt.cm.Blues(np.linspace(0.3, 0.9, len(valores))))
axes[3].set_anchor("N")
axes[3].set_title("Ángulo", fontsize=9)

# Luminosidad: la marca no cambia de tamaño ni de lugar, solo de tono.
normalizado = (valores - valores.min()) / (valores.max() - valores.min())
axes[4].scatter(
    [0] * len(valores), range(len(valores)), s=120, marker="s",
    color=plt.cm.Greys(0.25 + 0.7 * normalizado),
)
axes[4].set_xlim(-1, 1)
axes[4].set_yticks([])
axes[4].set_title("Luminosidad", fontsize=9)

for ax in axes[2:]:
    ax.set_xticks([])
for ax in axes:
    ax.grid(False)

# El orden de los cinco paneles no es arbitrario: sigue el ranking de
# efectividad. Para responder "cuántos siniestros más tiene la primera comuna
# que la última", los dos primeros paneles se leen y los tres últimos se
# estiman.
print(f"\nLa comuna con más siniestros tiene {valores.max() / valores.min():.1f} veces "
      f"los de la décima")

# %%
# PARTE 2: expresividad
#
# El canal tiene que corresponder al tipo del atributo. Un canal de magnitud
# sobre un atributo categórico inventa un orden que no existe en los datos.

por_causa = (
    siniestros.groupby("causa_agrupada", observed=True)
    .size()
    .nlargest(6)
    .sort_values()
)
print(por_causa)

fig, axes = plt.subplots(1, 2, figsize=(9, 2.8))

# Correcto: la causa es categórica y se codifica con posición y largo.
por_causa.plot(kind="barh", color=AZUL, ax=axes[0])
axes[0].set_title("Categórico con posición y largo", fontsize=9)
axes[0].set_ylabel("")
axes[0].tick_params(axis="y", labelsize=6)

# Incorrecto: la luminosidad ordena, así que sugiere que una causa es "más"
# que otra cuando el orden solo refleja su frecuencia.
posicion = np.arange(len(por_causa))
axes[1].scatter(
    [0] * len(por_causa), posicion, s=300, marker="s",
    color=plt.cm.Greys(np.linspace(0.2, 0.9, len(por_causa))),
)
axes[1].set_yticks(posicion)
axes[1].set_yticklabels(por_causa.index, fontsize=6)
axes[1].set_xlim(-1, 1)
axes[1].set_xticks([])
axes[1].set_title("Categórico con luminosidad", fontsize=9)
axes[1].grid(False)

# %%
# PARTE 3: estimar antes de medir
#
# Los siniestros cayeron entre 2019 y 2020. La misma caída se muestra con dos
# canales: el largo de una barra y el área de un círculo. Antes de mirar el
# número, estimar de cuánto fue la caída en cada panel.

por_anio = siniestros.groupby("anio").size()
caida = por_anio.loc[[2019, 2020]]

fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.6))

axes[0].bar(["2019", "2020"], caida.values, color=AZUL, width=0.6)
axes[0].set_title("Largo", fontsize=9)
axes[0].set_yticks([])

axes[1].scatter([0, 1], [0, 0], s=caida.values / caida.max() * 1500, color=AZUL)
axes[1].set_xticks([0, 1])
axes[1].set_xticklabels(["2019", "2020"])
axes[1].set_xlim(-0.8, 1.8)
axes[1].set_yticks([])
axes[1].set_title("Área", fontsize=9)
axes[1].grid(False)

print("¿De cuánto fue la caída? Anota una estimación por panel antes de seguir.")

# %%
# La respuesta, calculada desde los datos.

descenso = 1 - caida.loc[2020] / caida.loc[2019]
print(f"{caida.loc[2019]:,} siniestros en 2019 y {caida.loc[2020]:,} en 2020")
print(f"La caída es de {descenso:.1%}")
print(
    "En el panel de área el círculo pequeño no se ve tanto más chico como dice "
    "esa cifra: el radio baja mucho menos que el área."
)

# %%
# PARTE 4: un experimento de precisión
#
# Los rankings de canales salen de experimentos: se muestran pares de valores,
# se pide estimar la razón entre ellos y se mide el error. Acá van cuatro pares
# con la misma razón, cada uno en un canal distinto.

RAZON = 0.55  # la respuesta, que conviene no mirar antes de estimar
PAR = np.array([1.0, RAZON])

fig, axes = plt.subplots(1, 4, figsize=(9, 2.4))

axes[0].bar([0, 1], PAR, color=AZUL, width=0.6)
axes[0].set_title("Largo", fontsize=9)
axes[0].set_ylim(0, 1.15)

axes[1].scatter([0, 1], [0, 0], s=PAR * 1800, color=AZUL)
axes[1].set_title("Área", fontsize=9)
axes[1].set_xlim(-0.8, 1.8)

for i, valor in enumerate(PAR):
    axes[2].pie(
        [valor, 1 - valor], colors=[AZUL, GRIS], radius=0.45,
        center=(i * 1.1, 0), frame=True,
    )
axes[2].set_title("Ángulo", fontsize=9)
axes[2].set_xlim(-0.6, 1.7)
axes[2].set_ylim(-0.6, 0.6)
axes[2].set_anchor("N")

axes[3].scatter([0, 1], [0, 0], s=900, marker="s", color=plt.cm.Greys(0.2 + 0.7 * PAR))
axes[3].set_title("Luminosidad", fontsize=9)
axes[3].set_xlim(-0.8, 1.8)

for ax in axes:
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)

print("En cada panel, ¿qué fracción del primer valor representa el segundo?")
print("Anota las cuatro estimaciones antes de seguir.")

# %%
# PARTE 5: el error de cada estimación
#
# Con las estimaciones del curso se calcula el error de cada canal y se compara
# el orden obtenido con el del ranking teórico.

ESTIMACIONES = {  # reemplazar por las del curso
    "Largo": [],
    "Área": [],
    "Ángulo": [],
    "Luminosidad": [],
}

print(f"Razón real: {RAZON}")
for canal, valores_estimados in ESTIMACIONES.items():
    if not valores_estimados:
        print(f"  {canal}: sin estimaciones")
        continue
    errores = np.abs(np.array(valores_estimados) - RAZON) / RAZON
    print(f"  {canal}: error medio {errores.mean():.1%} sobre {len(errores)} respuestas")

# %%
# PARTE 6: distinguibilidad
#
# Un canal admite pocos niveles separables. Con demasiadas categorías, el color
# deja de identificar y hay que volver a la leyenda para cada marca.

conteo_tipos = siniestros["tipo_agrupado"].value_counts()
print(conteo_tipos)

fig, axes = plt.subplots(1, 2, figsize=(9, 2.8))

for ax, n in zip(axes, [3, len(conteo_tipos)]):
    datos = conteo_tipos.head(n) if n < len(conteo_tipos) else conteo_tipos
    colores = plt.cm.tab10(np.linspace(0, 1, len(datos)))
    ax.pie(datos, colors=colores, labels=None)
    ax.legend(datos.index, fontsize=5, loc="center left", bbox_to_anchor=(0.95, 0.5))
    ax.set_title(f"{len(datos)} categorías", fontsize=9)

print(
    f"\nEl panel de la derecha reparte el color en {len(conteo_tipos)} categorías, "
    "y las más chicas quedan indistinguibles entre sí."
)

# %%
# PARTE 7: un glifo
#
# Un glifo es una visualización completa que funciona como marca dentro de otra:
# cada glifo resume varios atributos de una unidad y se puede ubicar en un mapa.
#
# Este reconstruye el diseño de ModalCell, que resume los viajes que salen de
# una comuna combinando tres atributos: la dirección del viaje en doce sectores,
# la distancia en tres anillos y el modo de transporte en el color.
# Perez-Messina, I. y Graells-Garrido, E. (2019). Visualizing Transportation
# Flows with Mode Split using Glyphs. EuroVis Short Papers.

import colorsys

import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import pandas as pd
from shapely.geometry import box

carpeta_eod = descargar_datos("tipos-de-dataset.tgz")
viajes = pd.read_parquet(carpeta_eod / "eod-viajes.parquet")
comunas = gpd.read_parquet(carpeta_eod / "comunas-rm.parquet")

# La zona urbana del Gran Santiago es el área de estudio de la EOD. Varias
# comunas se extienden mucho más allá: Lo Barnechea llega a la cordillera con
# 1.023 km$^2$, de los cuales 105 están en la ciudad. Recortarlas deja el
# centroide donde vive la gente y no en la montaña.
BBOX_URBANO = (-70.85, -33.65, -70.45, -33.30)

geometria = comunas.set_index("comuna").geometry
urbana = geometria.intersection(box(*BBOX_URBANO))
urbana.loc[urbana.is_empty] = geometria.loc[urbana.is_empty]

# Los centroides van en UTM para que las distancias queden en metros.
centroides = urbana.to_crs(32719).centroid

MODOS = {"Auto": "Auto", "Bus TS": "Bus", "Metro": "Metro", "Bus TS - Metro": "Metro"}
COLOR_MODO = {"Auto": "#E0A32E", "Bus": "#CF3889", "Metro": "#2E9E8F"}
RANGOS = ["corta", "media", "larga"]

# El sector, el rango y el modo se calculan una vez para todos los viajes: cada
# glifo después es una agrupación distinta sobre esta misma tabla.
flujos = viajes[
    viajes["modo"].isin(MODOS)
    & viajes["comuna_origen"].isin(centroides.index)
    & viajes["comuna_destino"].isin(centroides.index)
].copy()
flujos["modo_agrupado"] = flujos["modo"].map(MODOS)
flujos["interno"] = flujos["comuna_origen"] == flujos["comuna_destino"]

origen = centroides.loc[flujos["comuna_origen"]]
destino = centroides.loc[flujos["comuna_destino"]]
dx = destino.x.values - origen.x.values
dy = destino.y.values - origen.y.values

# Doce sectores de 30 grados, contados desde el norte y hacia el este.
flujos["sector"] = (np.degrees(np.arctan2(dx, dy)) % 360 // 30).astype(int)
flujos["rango"] = pd.cut(
    np.hypot(dx, dy) / 1000, [0, 5, 10, np.inf], labels=RANGOS
)


def desaturar(color, factor):
    """Baja la saturación de un color manteniendo su matiz y su luminosidad."""
    h, l, sat = colorsys.rgb_to_hls(*mcolors.to_rgb(color))
    return colorsys.hls_to_rgb(h, l + (1 - l) * (1 - factor) * 0.5, sat * factor)


def datos_del_glifo(comuna):
    """Arma las dos partes del glifo de una comuna.

    Los rayos salen de los viajes que dejan la comuna, agrupados por sector y
    rango de distancia, con el modo predominante de cada celda. El centro sale
    del total por modo, que incluye los viajes internos: esos no tienen
    dirección, así que el radial no los puede mostrar.
    """
    de_la_comuna = flujos[flujos["comuna_origen"] == comuna]
    salidas = de_la_comuna[~de_la_comuna["interno"]]

    conteo = (
        salidas.groupby(["sector", "rango", "modo_agrupado"], observed=True)
        .size()
        .rename("viajes")
        .reset_index()
    )
    por_rango = (
        conteo.groupby(["sector", "rango"], observed=True)["viajes"]
        .sum()
        .unstack(fill_value=0)
        .reindex(columns=RANGOS, fill_value=0)
    )
    predominante = (
        conteo.sort_values("viajes")
        .groupby(["sector", "rango"], observed=True)
        .last()
        .reset_index()
    )
    modo_por_rango = (
        predominante.set_index(["sector", "rango"])["modo_agrupado"]
        .unstack()
        .reindex(columns=RANGOS)
    )
    total_modo = de_la_comuna["modo_agrupado"].value_counts()
    return por_rango, modo_por_rango, total_modo


R_CENTRO = 0.55  # radio del círculo embebido más grande
ANCHO = np.radians(24)


def dibujar_glifo(ax, por_rango, modo_por_rango, total_modo, borde=0.6):
    """Dibuja un glifo ModalCell sobre un eje polar."""
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_yticks([])
    ax.set_ylim(0, 1.55)

    # Centro: cada círculo tiene área proporcional a los viajes de su modo, así
    # que el predominante es el más grande y queda afuera con el color
    # saturado. El segundo va embebido con la saturación a la mitad y el resto
    # en gris, que es como el diseño original mantiene el color preatentivo del
    # modo principal.
    radios = R_CENTRO * np.sqrt(total_modo / total_modo.max())
    for orden, (modo, radio) in enumerate(radios.items()):
        if orden == 0:
            color = COLOR_MODO[modo]
        elif orden == 1:
            color = desaturar(COLOR_MODO[modo], 0.5)
        else:
            color = GRIS
        # El borde va aparte y no como edgecolor de la barra: una barra polar de
        # 2 pi de ancho también dibuja sus dos lados radiales, que se superponen
        # en una línea desde el centro.
        ax.bar(0, radio, width=2 * np.pi, bottom=0, color=color,
               edgecolor="none", zorder=3 + orden)
        ax.plot(np.linspace(0, 2 * np.pi, 180), np.full(180, radio),
                color="white", lw=borde, zorder=3 + orden)

    # Rayos: arrancan en el borde del centro para que no lo tapen. El largo se
    # normaliza dentro de cada glifo, así que compara sectores entre sí y no
    # comunas entre sí.
    angulos = np.radians(por_rango.index.to_numpy() * 30)
    escala = por_rango.sum(axis=1).max()
    base = np.full(len(por_rango), R_CENTRO)
    for rango in RANGOS:
        altura = por_rango[rango].to_numpy() / escala
        colores = [COLOR_MODO.get(m, GRIS) for m in modo_por_rango[rango]]
        ax.bar(angulos, altura, width=ANCHO, bottom=base, color=colores,
               edgecolor="white", linewidth=borde * 0.7)
        base = base + altura


COMUNA = "Santiago"
por_rango, modo_por_rango, total_modo = datos_del_glifo(COMUNA)

print(f"Viajes que salen de {COMUNA}: {int(por_rango.to_numpy().sum()):,}")
print(total_modo)

fig, ax = plt.subplots(figsize=(5.4, 5.4), subplot_kw={"projection": "polar"})
dibujar_glifo(ax, por_rango, modo_por_rango, total_modo)
ax.set_xticks(np.radians(np.arange(0, 360, 90)))
ax.set_xticklabels(["N", "E", "S", "O"], fontsize=8)
ax.grid(alpha=0.25)

for modo, color in COLOR_MODO.items():
    ax.plot([], [], color=color, lw=6, label=modo)
ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.06), fontsize=7, frameon=False)
ax.set_title(f"Viajes de {COMUNA}", fontsize=10)

fig.savefig("images/04-glifo-modalcell.png", dpi=DPI, bbox_inches="tight")

print("\nRangos: corta (hasta 5 km), media (5 a 10), larga (sobre 10)")
print("El orden radial de los rayos es corta, media y larga")

# %%
# PARTE 8: el glifo como marca sobre un mapa
#
# Hasta acá el glifo es un gráfico. Se vuelve marca cuando se repite sobre otra
# visualización: un glifo por comuna, ubicado en su centroide. Ahí el mapa
# aporta un canal más, la posición geográfica, y aparecen patrones que un solo
# glifo no muestra.
#
# El tamaño de cada glifo codifica el total de viajes de la comuna, con el área
# proporcional al volumen. Adentro, los rayos se normalizan por el máximo de esa
# comuna: comparan sectores dentro del glifo, no comunas entre sí.

# Las 34 comunas del Gran Santiago: las 32 de la provincia de Santiago más
# Puente Alto y San Bernardo. Se enumeran en vez de usar un umbral de viajes
# porque el recorte es geográfico y no de tamaño de muestra.
GRAN_SANTIAGO = [
    "Cerrillos", "Cerro Navia", "Conchalí", "El Bosque", "Estación Central",
    "Huechuraba", "Independencia", "La Cisterna", "La Florida", "La Granja",
    "La Pintana", "La Reina", "Las Condes", "Lo Barnechea", "Lo Espejo",
    "Lo Prado", "Macul", "Maipú", "Ñuñoa", "Pedro Aguirre Cerda", "Peñalolén",
    "Providencia", "Pudahuel", "Puente Alto", "Quilicura", "Quinta Normal",
    "Recoleta", "Renca", "San Bernardo", "San Joaquín", "San Miguel",
    "San Ramón", "Santiago", "Vitacura",
]

totales_comuna = flujos["comuna_origen"].value_counts()
con_glifo = [c for c in GRAN_SANTIAGO if totales_comuna.get(c, 0) > 0]
totales_comuna = totales_comuna.loc[con_glifo]
print(f"Comunas con glifo: {len(con_glifo)}")
print(f"Viajes por comuna: de {totales_comuna.min():,} a {totales_comuna.max():,}")

mapa = urbana.loc[con_glifo].to_crs(32719)
centros = centroides.loc[con_glifo]

fig, ax = figure_from_geodataframe(mapa, height=7)
mapa.plot(ax=ax, facecolor="#F0F0F2", edgecolor="white", linewidth=0.8)

# El eje del mapa tiene que quedar quieto antes de calcular las posiciones: un
# dibujo fija el layout y apagarlo evita que agregar ejes lo vuelva a mover.
fig.canvas.draw()
fig.set_layout_engine("none")

# add_axes recibe fracciones de la figura, que no es cuadrada: sin corregir por
# la razón de aspecto el glifo más grande queda achatado.
razon = fig.get_figwidth() / fig.get_figheight()
LADO_MAXIMO = 0.16  # fracción del ancho de la figura para el glifo más grande

# Rotular las treinta comunas satura el centro del mapa, donde los glifos ya se
# tocan entre sí.
destacadas = set(totales_comuna.nlargest(12).index)

for comuna in con_glifo:
    por_rango, modo_por_rango, total_modo = datos_del_glifo(comuna)
    if total_modo.empty or por_rango.empty:
        continue

    # De coordenadas del mapa a coordenadas de la figura, que es lo que espera
    # add_axes para ubicar un eje nuevo.
    punto = centros.loc[comuna]
    en_pantalla = ax.transData.transform((punto.x, punto.y))
    x, y = fig.transFigure.inverted().transform(en_pantalla)

    # El área del glifo es proporcional al total de viajes de la comuna.
    ancho = LADO_MAXIMO * np.sqrt(totales_comuna[comuna] / totales_comuna.max())
    alto = ancho * razon
    glifo = fig.add_axes([x - ancho / 2, y - alto / 2, ancho, alto],
                         projection="polar", label=comuna)
    glifo.patch.set_alpha(0)
    glifo.set_axis_off()
    dibujar_glifo(glifo, por_rango, modo_por_rango, total_modo, borde=0.3)

    if comuna in destacadas:
        etiqueta = fig.text(x, y - alto / 2, comuna, ha="center", va="top",
                            fontsize=6, color=AZUL)
        etiqueta.set_path_effects(
            [pe.withStroke(linewidth=2, foreground="white")]
        )

for modo, color in COLOR_MODO.items():
    ax.plot([], [], color=color, lw=6, label=modo)
ax.legend(loc="upper left", fontsize=8, frameon=False)
ax.set_title("Viajes que salen de cada comuna del Gran Santiago")

fig.savefig("images/04-glifo-mapa.png", dpi=DPI, bbox_inches="tight")

print("Escrito: images/04-glifo-modalcell.png")
print("Escrito: images/04-glifo-mapa.png")
