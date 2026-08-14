# %%
"""Tercera sesión de código: de la tarea al hito 1.

Dos partes sobre el mismo dataset, los siniestros de tránsito de la Región
Metropolitana. La primera nombra la tarea que resuelve cada pregunta antes de
elegir el gráfico. La segunda arma el hito 1 con ese material: la propuesta,
los datos que la sostienen y los límites que hay que declarar.

Las figuras de la segunda parte quedan en images/, en el mismo formato que se
lleva a la presentación.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from chiricoca.geo.figures import figure_from_geodataframe
from chiricoca.geo.grid import h3_grid_from_bounds
from chiricoca.maps import choropleth_map, dot_map
from chiricoca.tables import barchart

from visutils.estilo import AZUL, GRIS, MAGENTA, estilo_curso
from visutils.general import descargar_datos

estilo_curso()

carpeta = descargar_datos("siniestros.tgz")
siniestros = gpd.read_parquet(carpeta / "siniestros-rm.parquet")

# Las comunas sirven de contorno en los mapas: una nube de puntos sin bordes no
# se distingue de la de cualquier otra ciudad.
comunas = gpd.read_parquet(descargar_datos("tipos-de-dataset.tgz") / "comunas-rm.parquet")

print(f"Ítems: {len(siniestros):,} siniestros")
print(f"Años: {siniestros['anio'].min()} a {siniestros['anio'].max()}")
print(siniestros.head())

# %%
# PARTE 1: qué es una tarea
#
# Una tarea se define como acción más objetivo:
#
#   acción     qué se quiere hacer. Analizar (consumir o producir), buscar
#              (recuperar, ubicar, recorrer, explorar) o consultar (identificar,
#              comparar, resumir).
#   objetivo   sobre qué parte de los datos recae: todos los datos, un atributo,
#              varios atributos, la topología de una red, la forma en el espacio.
#
# La misma tabla admite gráficos distintos según la tarea, y por eso conviene
# nombrarla antes de elegir el gráfico. Si no se puede nombrar, la pregunta
# todavía no está formulada.

print("Atributos disponibles:")
print(siniestros.dtypes)

# %%
# PARTE 2: comparar la gravedad entre tipos de siniestro
#
# Acción: consultar, comparar. Objetivo: dos atributos, el tipo y las víctimas.
#
# Ojo con qué se compara. El total de víctimas mezcla dos cosas: cuán frecuente
# es un tipo de siniestro y cuán grave es cada uno. El promedio por siniestro
# separa la segunda de la primera. Al mirar los dos paneles, comparar el orden:
# el tipo más frecuente no tiene por qué ser el más grave.

por_tipo = (
    siniestros.groupby("tipo_agrupado", observed=True)
    .agg(siniestros=("victimas", "size"), victimas=("victimas", "sum"))
    .assign(victimas_por_siniestro=lambda d: d["victimas"] / d["siniestros"])
    .sort_values("siniestros", ascending=False)
)
print(por_tipo.round(2))

fig, axes = plt.subplots(1, 2, figsize=(7.5, 2.8), sharey=True)

por_tipo["siniestros"].plot(kind="barh", color=GRIS, ax=axes[0])
axes[0].set_title("Cuántos siniestros hay de cada tipo")
axes[0].set_xlabel("Siniestros, 2019 a 2023")
axes[0].set_ylabel("")

por_tipo["victimas_por_siniestro"].plot(kind="barh", color=MAGENTA, ax=axes[1])
axes[1].set_title("Cuántas víctimas deja cada uno")
axes[1].set_xlabel("Víctimas por siniestro")

# La inversión va después de dibujar los dos paneles: con sharey, pandas
# reajusta el eje compartido al graficar el segundo y la deshace.
axes[0].invert_yaxis()
plt.show()

# %%
# PARTE 3: cuándo ocurren
#
# Acción: consultar, comparar. Objetivo: la distribución de un atributo cíclico,
# la hora, en dos subgrupos.
#
# Antes de responder hay que mirar la cobertura del atributo: la fuente entrega
# la hora en tres de los cinco años y en los otros dos la manda corrupta.

cobertura = siniestros.groupby("anio")["hora"].apply(lambda h: h.notna().mean())
print("Proporción de siniestros con hora conocida, por año:")
print(cobertura.round(2))

con_hora = siniestros.dropna(subset=["hora"])
print(f"\nSe responde con {len(con_hora):,} siniestros de {len(siniestros):,}")

TIPOS = ["Colision", "Atropello"]
por_hora = (
    con_hora[con_hora["tipo_agrupado"].isin(TIPOS)]
    .groupby(["tipo_agrupado", "hora"], observed=True)
    .size()
    .unstack(0)
    .reindex(range(24), fill_value=0)
)
# Cada tipo se normaliza por su propio total: la pregunta es a qué hora ocurre
# cada uno, no cuál es más frecuente.
proporcion = por_hora / por_hora.sum()

fig, ax = plt.subplots(figsize=(5, 2.6))
proporcion.plot(ax=ax, color={"Colision": AZUL, "Atropello": MAGENTA})
ax.set_title("Cuándo ocurre cada tipo de siniestro")
ax.set_xlabel("Hora de inicio")
ax.set_ylabel("Proporción del tipo")
ax.set_xlim(0, 23)
plt.show()

for tipo in TIPOS:
    print(f"{tipo}: hora más frecuente {proporcion[tipo].idxmax()}h "
          f"({proporcion[tipo].max():.1%} de los casos)")

# %%
# PARTE 4: dónde ocurren los atropellos
#
# Acción: buscar, explorar. No sabemos qué buscamos ni dónde está, así que el
# gráfico tiene que mostrar todo el territorio a la vez. Objetivo: la forma en
# el espacio.

atropellos = siniestros[siniestros["tipo_agrupado"] == "Atropello"]
print(f"Atropellos: {len(atropellos):,}")
print("\nComunas con más atropellos:")
print(atropellos["comuna"].value_counts().head())

fig, ax = figure_from_geodataframe(atropellos, height=5)
dot_map(
    siniestros.sample(20000, random_state=0),
    size=0.2, color=GRIS, alpha=0.5, add_legend=False, ax=ax, zorder=1
)
dot_map(atropellos, size=0.6, color=MAGENTA, alpha=0.5, add_legend=False, ax=ax, zorder=2)
ax.set_title("Atropellos sobre el resto de los siniestros")
ax.set_axis_off()
plt.show()

# El mapa de puntos responde dónde hay muchos, no dónde son más peligrosos. Para
# lo segundo hay que normalizar por la cantidad de siniestros de cada comuna. El
# umbral deja fuera las comunas rurales, donde una decena de casos produce
# porcentajes que no son comparables con los del área urbana.
por_comuna = (
    siniestros.groupby("comuna", observed=True)
    .agg(total=("victimas", "size"), atropellos=("tipo_agrupado", lambda s: (s == "Atropello").sum()))
    .query("total >= 500")
    .assign(proporcion=lambda d: d["atropellos"] / d["total"])
    .sort_values("proporcion", ascending=False)
)
print("\nComunas donde el atropello pesa más dentro de sus siniestros:")
print(por_comuna.head(8).round(3))

# %%
# PARTE 5: la propuesta del hito 1
#
# Hasta acá hubo preguntas sueltas. El hito 1 las ordena en una propuesta: la
# situación describe el contexto del problema, la complicación dice qué falla
# dentro de ese contexto y la propuesta dice qué se va a construir. Los datos
# todavía no aparecen; eso viene después, al mostrar que la propuesta es
# factible.

PROPUESTA = {
    "Situación": (
        "La seguridad vial en Santiago es importante para toda la población: "
        "todas las personas se desplazan de un lugar a otro, y esos "
        "desplazamientos comparten una misma red vial."
    ),
    "Complicación": (
        "Ocurren decenas de siniestros al día y no se sabe dónde llevar a cabo "
        "intervenciones para reducirlos. Los recursos alcanzan para unas pocas "
        "medidas al año."
    ),
    "Propuesta": (
        "Identificar puntos críticos de la red vial, considerando la frecuencia "
        "de los siniestros y las víctimas que deja cada tipo."
    ),
}

for parte, texto in PROPUESTA.items():
    print(f"\n{parte}:\n  {texto}")

# %%
# PARTE 6: de dónde salen los datos
#
# La rúbrica pide decir cuáles son los datos, dónde están y cómo se obtienen.
# Sin eso no se puede juzgar nada de lo que venga después.

print("Fuente: CONASET, Observatorio de Datos de Seguridad Vial")
print("URL: https://mapas-conaset.opendata.arcgis.com/")
print("Licencia: datos abiertos, un archivo por año")
print(f"\nPeríodo: {siniestros['anio'].min()} a {siniestros['anio'].max()}")
print("Unidad de observación: un siniestro georreferenciado")
print(f"Filas: {len(siniestros):,}")
print(f"Comunas: {siniestros['comuna'].nunique()}")

# %%
# PARTE 7: las variables que la propuesta necesita
#
# La propuesta habla de tipo y de gravedad, así que hay que mostrar que las dos
# existen y que tienen variabilidad. Un tipo que concentrara casi todos los
# casos haría inviable comparar.

gravedad_por_tipo = (
    siniestros.assign(
        gravedad=lambda d: np.where(d["victimas"] > 0, "con víctimas", "sin víctimas")
    )
    .groupby(["tipo_agrupado", "gravedad"], observed=True)
    .size()
    .unstack(fill_value=0)[["sin víctimas", "con víctimas"]]
)
print(gravedad_por_tipo)
print(f"\nProporción de siniestros sin víctimas: {(siniestros['victimas'] == 0).mean():.1%}")

fig, ax = plt.subplots(figsize=(4.4, 2.4))
barchart(
    gravedad_por_tipo,
    stacked=True,
    horizontal=True,
    palette=[GRIS, MAGENTA],
    sort_items="sum",
    sort_items_ascending=True,  # en barras horizontales el primero queda abajo
    ax=ax,
)
ax.set_title("Tipos de siniestro y cuáles dejan víctimas")
ax.set_xlabel("Siniestros, 2019 a 2023")
ax.set_ylabel("")
ax.xaxis.set_major_formatter(lambda x, _: f"{x:,.0f}".replace(",", "."))
fig.savefig("images/03-hito1-tipos.png", dpi=300, bbox_inches="tight")
plt.show()

# %%
# PARTE 8: la variabilidad de la variable central
#
# La rúbrica pide distribuciones, no solo promedios. Las categorías se agrupan
# a partir de cinco víctimas porque más allá los casos son demasiado escasos
# para leerlos por separado, y el porcentaje sobre cada barra evita tener que
# estimar la altura en una escala logarítmica.

CORTE = 5
etiquetas = [str(i) for i in range(CORTE)] + [f"{CORTE} o más"]
distribucion = (
    siniestros["victimas"]
    .clip(upper=CORTE)
    .value_counts(normalize=True)
    .sort_index()
    .set_axis(etiquetas)
    .mul(100)
)
print(distribucion.round(2))
print(f"\nMáximo de víctimas en un siniestro: {siniestros['victimas'].max()}")
print(f"Fallecidos en el período: {siniestros['fallecidos'].sum():,}")

fig, ax = plt.subplots(figsize=(4.6, 2.4))
distribucion.plot(kind="bar", color=AZUL, width=0.85, ax=ax)
for x, valor in enumerate(distribucion):
    ax.annotate(f"{valor:.1f}%", (x, valor), ha="center", va="bottom", fontsize=7)
ax.set_title("Cuántas víctimas deja un siniestro")
ax.set_xlabel("Víctimas en el siniestro")
ax.set_ylabel("% de los siniestros")
ax.set_ylim(0, distribucion.max() * 1.15)
ax.tick_params(axis="x", rotation=0)
fig.savefig("images/03-hito1-victimas.png", dpi=300, bbox_inches="tight")
plt.show()

# %%
# PARTE 9: la cobertura temporal
#
# Hay que mostrar que el período está completo. Un año con menos registros
# puede ser un cambio real o un problema de la fuente, y conviene saber cuál de
# los dos antes de proponer un análisis temporal.

por_mes = siniestros.groupby(siniestros["fecha"].dt.to_period("M")).size()
por_mes.index = por_mes.index.to_timestamp()
print("Siniestros por año:")
print(siniestros.groupby("anio").size())

fig, ax = plt.subplots(figsize=(6, 2.4))
por_mes.plot(ax=ax, color=AZUL, lw=1.2)
# La media móvil de doce meses separa el nivel de la estacionalidad, que en
# esta serie repite un mínimo cada febrero.
por_mes.rolling(12, center=True).mean().plot(ax=ax, color=MAGENTA, lw=1.6)
ax.set_title("Siniestros por mes, con media móvil de 12 meses")
ax.set_ylabel("Siniestros")
ax.set_xlabel("")
ax.set_ylim(0)
fig.savefig("images/03-hito1-cobertura.png", dpi=300, bbox_inches="tight")
plt.show()

# %%
# PARTE 10: la cobertura espacial
#
# La propuesta es sobre lugares, así que hay que mostrar dónde hay datos y
# dónde se concentran. Con 97 mil puntos superpuestos no se puede leer densidad:
# el color de una celda sí, porque cada una resume cuántos casos cayeron en
# ella. La grilla hexagonal evita además el sesgo de comparar comunas de
# tamaños muy distintos.

grilla = h3_grid_from_bounds(siniestros.total_bounds, grid_level=7)
conteo = (
    gpd.sjoin(siniestros[["geometry"]], grilla.reset_index(), predicate="within")
    .groupby("h3_cell_id")
    .size()
    .rename("siniestros")
)
celdas = grilla.join(conteo, how="inner")
print(f"Celdas con al menos un siniestro: {len(celdas):,} de {len(grilla):,}")
print(celdas["siniestros"].describe().round(1))

fig, ax = figure_from_geodataframe(comunas, height=3.6)
choropleth_map(celdas, "siniestros", k=6, binning="fisher_jenks", palette="magma_r", ax=ax)
comunas.boundary.plot(ax=ax, color=AZUL, linewidth=0.3, zorder=5)
ax.set_title("Siniestros por celda hexagonal")
ax.set_axis_off()
fig.savefig("images/03-hito1-mapa.png", dpi=300, bbox_inches="tight")
plt.show()

# %%
# PARTE 11: hasta dónde llegan los datos
#
# Declarar los límites es parte de la factibilidad. Un atributo incompleto no
# bloquea la propuesta: acota sobre qué subconjunto se puede responder. La hora
# alcanza para preguntar a qué hora ocurre cada tipo de siniestro, como en la
# parte 3, pero no para comparar la evolución horaria entre los cinco años.

print("Proporción de siniestros con hora conocida, por año:")
print(cobertura.round(2))

faltantes = siniestros.drop(columns="geometry").isna().mean()
print("\nProporción de valores faltantes por atributo:")
print(faltantes[faltantes > 0].round(3))

# %%
# PARTE 12: las cifras de la lámina de factibilidad
#
# La última lámina del hito responde si con estos datos se puede hacer lo que
# la propuesta dice. El veredicto lo escribe cada grupo; acá quedan las cifras
# que lo sostienen, recalculadas desde los datos.

print(f"Registros: {len(siniestros):,}")
print(f"Período: {siniestros['anio'].min()} a {siniestros['anio'].max()}")
print(f"Meses sin registros: {(por_mes == 0).sum()}")
print(f"Comunas: {siniestros['comuna'].nunique()}")
print(f"Víctimas por siniestro: de {siniestros['victimas'].min()} a {siniestros['victimas'].max()}")
print(f"Atributos sin valores faltantes: {(faltantes == 0).sum()} de {len(faltantes)}")
print(f"Cobertura de la hora: {siniestros['hora'].notna().mean():.0%}")

print("\nFiguras escritas en images/:")
for nombre in ["tipos", "victimas", "cobertura", "mapa"]:
    print(f"  images/03-hito1-{nombre}.png")
