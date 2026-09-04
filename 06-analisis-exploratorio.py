# %%
"""Sexta sesión de código: el análisis exploratorio de un proyecto.

El recorrido tiene la forma de un hito 2: los criterios de limpieza y filtrado
con sus conteos, las propiedades globales, la comparación entre grupos y una
conclusión sobre la factibilidad.

El proyecto viene definido desde el hito 1:

  Situación. Elegir el primer nombre es una decisión cultural que queda
  registrada. El Registro Civil publica los nombres inscritos en Chile cada
  año, entre 1920 y 2021.

  Complicación. La globalización y la influencia de la cultura de masas pueden
  cambiar la distribución de nombres.

  Propuesta. Identificar tendencias en la distribución de nombres, separando la
  concentración del repertorio de su composición.

De la propuesta salen tres tareas:

  comparar la concentración del repertorio entre años
  comparar la composición del repertorio entre períodos
  identificar los años en que el repertorio cambió bruscamente

Esta sesión revisa si los datos sostienen esas tareas. La respuesta puede ser
que no, y en ese caso hay que acotar la propuesta o cambiarla.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from chiricoca.tables import barchart, heatmap, scatterplot

from visutils.estilo import AZUL, DPI, GRIS, MAGENTA, estilo_curso
from visutils.general import descargar_datos

estilo_curso()

# Separador de miles en castellano, porque el de matplotlib es la coma.
MILES = lambda x, _: f"{x:,.0f}".replace(",", ".")

# %%
# PARTE 1: construir
#
# Cada tipo de dataset tiene su estructura. Esta fuente es una tabla, así que va
# a un DataFrame.

carpeta = descargar_datos("guaguas.tgz")
guaguas = pd.read_csv(carpeta / "guaguas.csv.gz")

print(f"{len(guaguas):,} filas, {guaguas['n'].sum():,} inscripciones, "
      f"{guaguas['anio'].min()} a {guaguas['anio'].max()}")
print(guaguas.head())

# %%
# Una fila no es una persona: es la combinación de año, nombre y sexo. Un mismo
# nombre en un mismo año puede ocupar dos filas.

print(guaguas[(guaguas["nombre"] == "Michel") & (guaguas["anio"] == 1997)])

# %%
# PARTE 2: limpiar
#
# Qué cuenta como inválido depende del contexto, así que antes de descartar algo
# hay que mirarlo. El tercer valor de sexo son 318 filas sobre 858.782, y antes
# de decidir qué hacer con ellas conviene ver en qué años aparecen.

print(guaguas.isna().sum().to_dict())
print(
    guaguas.groupby("sexo").agg(
        filas=("n", "size"),
        inscripciones=("n", "sum"),
        desde=("anio", "min"),
        hasta=("anio", "max"),
    )
)

# La categoría no existe antes de 2005: es un cambio en el instrumento y no un
# dato sucio. Se conserva, y las series por sexo usan F y M porque la tercera no
# cubre el período.

# %%
# La columna nombre trae las grafías tal como quedaron inscritas. La tilde
# invertida no existe en castellano, así que esas filas son errores de
# transcripción de la fuente. No se corrigen, porque hacerlo obliga a decidir a
# qué nombre corresponde cada una; se declaran y se mide cuánto pesan.

TILDE_INVERTIDA = r"[àèìòùÀÈÌÒÙ]"

con_tilde_invertida = guaguas["nombre"].str.contains(TILDE_INVERTIDA, regex=True)
peso_errores = guaguas.loc[con_tilde_invertida, "n"].sum() / guaguas["n"].sum()

print(f"{con_tilde_invertida.sum():,} filas con tilde invertida, {peso_errores:.4%} de las "
      f"inscripciones: {list(guaguas.loc[con_tilde_invertida, 'nombre'].unique()[:6])}")

# %%
# La columna proporcion viene calculada en la fuente. Un atributo derivado que
# llega hecho se verifica antes de usarlo: debería sumar 1 cada año.

suma_anual = guaguas.groupby("anio")["proporcion"].sum()
print(f"Suma de proporcion por año: {suma_anual.min():.6f} a {suma_anual.max():.6f}")

# El desvío es de redondeo, pero igual se recalcula desde n para que todas las
# cifras salgan de una sola operación conocida.

totales_anuales = guaguas.groupby("anio")["n"].sum()
guaguas["parte"] = guaguas["n"] / guaguas["anio"].map(totales_anuales)

# %%
# PARTE 3: filtrar
#
# Qué es irrelevante depende de la pregunta. Esta tabla tiene una cola larga y
# hay que decidir qué hacer con ella.

total_por_nombre = guaguas.groupby("nombre")["n"].sum().sort_values(ascending=False)
acumulado = total_por_nombre.cumsum() / total_por_nombre.sum()

print(f"{len(total_por_nombre):,} nombres distintos, "
      f"{(total_por_nombre == 1).sum():,} con una sola inscripción en 102 años")
print(f"{'umbral':>8} {'nombres':>9} {'% inscripciones':>16} {'% filas':>9}")

for umbral in (1, 10, 100, 1_000, 10_000):
    nombres = total_por_nombre[total_por_nombre >= umbral]
    filas = guaguas["nombre"].isin(nombres.index)
    print(f"{umbral:>8,} {len(nombres):>9,} "
          f"{nombres.sum() / total_por_nombre.sum():>15.2%} {filas.mean():>8.1%}")

# Un umbral de diez descarta un tercio de las filas y el 1,4% de las
# inscripciones, lo que parece gratis. Pero esos son los nombres de la cola
# larga, que es lo que la tarea de concentración necesita medir. El análisis usa
# dos criterios, uno por pregunta:
#
#   diversidad del repertorio  ->  la tabla completa, sin umbral
#   trayectoria de cada nombre ->  nombres con 1.000 inscripciones o más
#
# El segundo se aplica en la parte 6, donde se usa.

UMBRAL_TRAYECTORIA = 1_000

# %%
# PARTE 4: propiedades globales, ¿qué?
#
# Qué variables hay y cómo se distribuyen. La única cuantitativa de esta tabla
# es un conteo, y su distribución decide todo lo que viene después.

for etiqueta, umbral in (("la mitad", 0.5), ("el 90%", 0.9)):
    print(f"Nombres para cubrir {etiqueta} de las inscripciones: "
          f"{int((acumulado < umbral).sum() + 1):,}")

fig, axes = plt.subplots(2, 1, figsize=(4.0, 4.6))

np.log10(total_por_nombre).plot(
    kind="hist", bins=60, ax=axes[0], color=AZUL, edgecolor="white", linewidth=0.3
)
axes[0].set_title("Inscripciones por nombre")
axes[0].set_xlabel("Inscripciones totales del nombre")
axes[0].set_ylabel("Nombres")
axes[0].set_xticks([0, 1, 2, 3, 4, 5])
axes[0].set_xticklabels(["1", "10", "100", "mil", "10 mil", "100 mil"])
axes[0].yaxis.set_major_formatter(MILES)

acumulado.reset_index(drop=True).mul(100).plot(ax=axes[1], color=AZUL, logx=True)
axes[1].set_title("Cobertura acumulada")
axes[1].set_xlabel("Nombres, del más al menos inscrito")
axes[1].set_ylabel("% de las inscripciones")
axes[1].set_ylim(0, 100)

for referencia in (50, 90):
    axes[1].axhline(referencia, color=MAGENTA, linestyle="dotted", linewidth=0.8)
    axes[1].annotate(f"{referencia}%", xy=(1, referencia), xytext=(2, 2),
                     textcoords="offset points", color=MAGENTA, fontsize=7)

fig.savefig("images/06-cola-larga.png", dpi=DPI, bbox_inches="tight")

# %%
# PARTE 5: propiedades globales, ¿cuándo?
#
# Antes de la serie del fenómeno conviene mirar la del instrumento, o sea
# cuántas observaciones trae cada año.

nombres_por_anio = guaguas.groupby("anio")["nombre"].nunique()

print(
    pd.DataFrame({"inscripciones": totales_anuales, "nombres": nombres_por_anio})
    .loc[[1920, 1928, 1955, 1990, 2017, 2018, 2021]]
)

# Aparecen dos problemas del registro y ninguno es sobre nombres. El primero es
# que empieza incompleto y su cobertura crece hasta los años cincuenta. El
# segundo es que en 2018 los nombres distintos suben sin que suban las
# inscripciones, así que cambió lo que la fuente registra.

ANIO_INICIO = 1930
ANIO_CAMBIO_FUENTE = 2018

fig, axes = plt.subplots(2, 1, figsize=(4.0, 4.4), sharex=True)

totales_anuales.plot(ax=axes[0], color=AZUL)
axes[0].set_title("Inscripciones por año")
axes[0].set_ylabel("Inscripciones")

nombres_por_anio.plot(ax=axes[1], color=AZUL)
axes[1].set_title("Nombres distintos por año")
axes[1].set_ylabel("Nombres distintos")
axes[1].axvline(ANIO_CAMBIO_FUENTE, color=MAGENTA, linestyle="dotted", linewidth=1)
axes[1].annotate(f"{ANIO_CAMBIO_FUENTE}", xy=(ANIO_CAMBIO_FUENTE - 3, 0.82),
                 xycoords=("data", "axes fraction"), ha="right", va="top",
                 color=MAGENTA, fontsize=7)

for ax in axes:
    ax.set_xlim(1920, 2021)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_formatter(MILES)
    # la franja gris son los años que el análisis descarta
    ax.axvspan(1920, ANIO_INICIO, color=GRIS, alpha=0.6, linewidth=0)
axes[-1].set_xlabel("Año de inscripción")

fig.savefig("images/06-cobertura.png", dpi=DPI, bbox_inches="tight")

# El criterio de recorte sale de esta figura y no de la etapa de limpieza, que
# es un ejemplo de por qué la exploración se itera.

registro = guaguas[guaguas["anio"] >= ANIO_INICIO]
conteo = registro.groupby(["anio", "nombre"])["n"].sum()

# %%
# Recién ahora se puede medir la diversidad del repertorio, que es la primera de
# las tres tareas.


def numero_efectivo(conteos):
    """Nombres efectivos: 2 elevado a la entropía de Shannon de la distribución.

    Vale 1 si todas las inscripciones usan el mismo nombre y crece hasta la
    cantidad de nombres distintos si todos se usan por igual. Se lee en la misma
    unidad que un conteo de nombres, a diferencia de la entropía en bits.
    """
    p = np.asarray(conteos, dtype=float)
    p = p[p > 0]
    p = p / p.sum()
    return 2 ** (-(p * np.log2(p)).sum())


efectivos = conteo.groupby("anio").apply(numero_efectivo)

# La medida depende del tamaño de la muestra: un año con 80 mil inscripciones no
# puede mostrar tantos nombres distintos como uno con 250 mil. Para descartar
# que el alza venga de ahí, se toma de cada año una muestra del mismo porte.

TAMANO_COMUN = int(totales_anuales.loc[ANIO_INICIO:].min())
rng = np.random.default_rng(42)


def igualada(conteos):
    """Nombres efectivos sobre una muestra de TAMANO_COMUN inscripciones."""
    muestra = rng.multivariate_hypergeometric(conteos.values.astype(np.int64), TAMANO_COMUN)
    return numero_efectivo(muestra)


efectivos_igualados = conteo.groupby("anio").apply(igualada)

print(f"Muestra común de {TAMANO_COMUN:,} inscripciones. Correlación entre las dos "
      f"medidas: {efectivos.corr(efectivos_igualados):.3f}")
print(f"  cruda:    {efectivos.min():.0f} en {efectivos.idxmin()} a "
      f"{efectivos.max():.0f} en {efectivos.idxmax()}")
print(f"  igualada: {efectivos_igualados.min():.0f} en {efectivos_igualados.idxmin()} a "
      f"{efectivos_igualados.max():.0f} en {efectivos_igualados.idxmax()}")

fig, ax = plt.subplots(figsize=(5.6, 2.8))

efectivos.plot(ax=ax, color=GRIS, linewidth=2.5, label="Sin corregir")
efectivos_igualados.plot(ax=ax, color=AZUL, label="Con muestra igualada")

ax.set_title("Nombres efectivos por año")
ax.set_xlabel("Año de inscripción")
ax.set_ylabel("Nombres efectivos")
ax.set_xlim(ANIO_INICIO, 2021)
ax.set_ylim(0, None)
ax.legend(fontsize=7)

fig.savefig("images/06-diversidad.png", dpi=DPI, bbox_inches="tight")

# Las dos curvas casi se superponen: el alza no la produce el tamaño del
# registro.

# %%
# PARTE 6: propiedades globales, ¿cómo?
#
# Cómo se relacionan las variables entre sí. Esta tabla tiene tres columnas y
# ninguna relación interesante entre ellas, así que hay que derivar atributos:
# se resume cada nombre en un perfil de su trayectoria.


def concentracion_temporal(serie):
    """Vale 1 si el nombre se inscribió en un solo año, y baja hacia 0 si se
    repartió por igual en todos los años del registro retenido."""
    n_anios = 2021 - ANIO_INICIO + 1
    return 1 - np.log2(numero_efectivo(serie)) / np.log2(n_anios)


por_nombre = conteo.reset_index()

perfil = por_nombre.groupby("nombre").agg(total=("n", "sum"), anios=("anio", "nunique"))
perfil["anio_peak"] = (
    por_nombre.loc[por_nombre.groupby("nombre")["n"].idxmax()].set_index("nombre")["anio"]
)
perfil["concentracion"] = por_nombre.groupby("nombre")["n"].apply(concentracion_temporal)

establecidos = perfil[perfil["total"] >= UMBRAL_TRAYECTORIA]

print(f"{len(establecidos):,} nombres con {UMBRAL_TRAYECTORIA:,} inscripciones o más")
print(establecidos[["total", "anios", "anio_peak", "concentracion"]].corr().round(2))

# %%
# La correlación más fuerte es entre el año del máximo y la concentración. Antes
# de anotarla como hallazgo hay que ver si la medida la permite: un nombre con
# máximo en 2015 no tiene cómo mostrar una trayectoria larga, porque el registro
# se corta en 2021.

ANIO_VENTANA_COMPLETA = 1995

ventana_completa = establecidos[establecidos["anio_peak"] <= ANIO_VENTANA_COMPLETA]

print(f"Año del máximo contra concentración: "
      f"{establecidos['anio_peak'].corr(establecidos['concentracion']):.3f} en todos, "
      f"{ventana_completa['anio_peak'].corr(ventana_completa['concentracion']):.3f} "
      f"con máximo hasta {ANIO_VENTANA_COMPLETA}")

fig, ax = plt.subplots(figsize=(4.6, 3.4))

scatterplot(
    establecidos.reset_index(),
    x="anio_peak",
    y="concentracion",
    ax=ax,
    scatter_args={"color": AZUL, "s": 4, "alpha": 0.35, "linewidth": 0},
)
establecidos.groupby("anio_peak")["concentracion"].mean().rolling(7, center=True).mean().plot(
    ax=ax, color=MAGENTA, linewidth=1.5
)

ax.axvspan(ANIO_VENTANA_COMPLETA, 2021, color=GRIS, alpha=0.6, linewidth=0, zorder=0)
ax.annotate("ventana de observación\nincompleta", xy=(2019, 0.02), ha="right", va="bottom",
            fontsize=6, color="#555555")

ax.set_title("Concentración temporal según el año del máximo")
ax.set_xlabel("Año en que el nombre tuvo su máximo")
ax.set_ylabel("Concentración temporal")
ax.set_xlim(ANIO_INICIO, 2021)

fig.savefig("images/06-como.png", dpi=DPI, bbox_inches="tight")

# La correlación baja al descartar los nombres recientes: parte de la relación
# es un artefacto de la ventana, y lo que queda es lo que se puede reportar.

# %%
# Falta una comprobación más: si la relación se sostiene dentro de los grupos o
# solo entre ellos. Se agrupan los nombres por la década de su máximo y se
# recalcula la correlación dentro de cada una.

# Una correlación sobre cuatro nombres no dice nada, así que las décadas con
# pocos nombres quedan fuera en vez de ensanchar el rango con ruido.
NOMBRES_MINIMOS = 30

por_decada = establecidos.assign(decada=establecidos["anio_peak"] // 10 * 10)
dentro_de_decada = por_decada.groupby("decada").apply(
    lambda d: d["anio_peak"].corr(d["concentracion"]) if len(d) >= NOMBRES_MINIMOS else np.nan,
    include_groups=False,
).dropna()

print(f"Correlación dentro de cada década ({len(dentro_de_decada)} décadas): entre "
      f"{dentro_de_decada.min():.2f} y {dentro_de_decada.max():.2f}, contra "
      f"{establecidos['anio_peak'].corr(establecidos['concentracion']):.2f} en el agregado")

# Dentro de cada década la relación desaparece: la que se ve en el agregado la
# producen las diferencias entre décadas, no las que hay entre nombres de un
# mismo período. Esa distancia entre el agregado y los grupos es el mecanismo de
# la paradoja de Simpson, que en su forma extrema invierte el signo.

# %%
# PARTE 7: propiedades globales, ¿dónde?
#
# No se puede responder. La tabla no trae comuna, región ni coordenadas, y no
# hay forma de derivarlas desde el año, el nombre o el sexo. Harían falta la
# comuna de la inscripción, que la fuente no publica, o el registro individual,
# que no es público por protección de datos.
#
# La consecuencia es un límite de las tareas, y no un vacío que se llene con
# supuestos. Una tarea que compare regiones no es factible con esta fuente.

print(list(guaguas.columns))

# %%
# PARTE 8: propiedades por grupo
#
# Primero, si los grupos están representados de forma comparable, porque de eso
# depende que la comparación signifique algo.

por_sexo = guaguas.groupby(["anio", "sexo"])["n"].sum().unstack(fill_value=0)
parte_sexo = por_sexo.div(por_sexo.sum(axis=1), axis=0) * 100

print(f"Fracción femenina: {parte_sexo.loc[1920, 'F']:.2f}% en 1920, y entre "
      f"{parte_sexo.loc[ANIO_INICIO:, 'F'].min():.2f}% y "
      f"{parte_sexo.loc[ANIO_INICIO:, 'F'].max():.2f}% desde {ANIO_INICIO}")

# El único año que se sale es 1920, que ya quedó descartado por cobertura. En el
# resto el reparto es parejo, así que las dos series se pueden comparar.

# %%
# Segundo, si hay diferencias entre los grupos en la variable que importa, que
# acá es la diversidad del repertorio.

efectivos_sexo = (
    registro[registro["sexo"].isin(["F", "M"])]
    .groupby(["anio", "sexo", "nombre"])["n"]
    .sum()
    .groupby(["anio", "sexo"])
    .apply(numero_efectivo)
    .unstack()
)
razon = efectivos_sexo["F"] / efectivos_sexo["M"]

print(f"Razón entre el repertorio femenino y el masculino: {razon.min():.2f} en "
      f"{razon.idxmin()} a {razon.max():.2f} en {razon.idxmax()}")

COLOR_SEXO = {"F": MAGENTA, "M": AZUL}

fig, axes = plt.subplots(2, 1, figsize=(4.0, 4.4), sharex=True)

parte_sexo.loc[ANIO_INICIO:, ["F", "M"]].plot(ax=axes[0], color=COLOR_SEXO, legend=False)
axes[0].set_title("Reparto de las inscripciones")
axes[0].set_ylabel("% de las inscripciones del año")
axes[0].set_ylim(40, 60)
axes[0].set_yticks([40, 45, 50, 55, 60])
axes[0].axhline(50, color=GRIS, linestyle="dotted", linewidth=0.8)

efectivos_sexo[["F", "M"]].plot(ax=axes[1], color=COLOR_SEXO)
axes[1].set_title("Diversidad del repertorio")
axes[1].set_ylabel("Nombres efectivos")
axes[1].set_ylim(0, None)
axes[1].legend(title="Sexo", fontsize=7)

for ax in axes:
    ax.set_xlim(ANIO_INICIO, 2021)
axes[-1].set_xlabel("Año de inscripción")

fig.savefig("images/06-grupos-sexo.png", dpi=DPI, bbox_inches="tight")

# %%
# La columna sexo permite un segundo corte que no es el obvio: los nombres que
# se inscriben para los dos sexos. Ninguna columna los marca, hay que
# encontrarlos comparando los totales de cada nombre.

UMBRAL_COMPARTIDO = 300
REPARTO_MAXIMO = 0.7

por_nombre_sexo = (
    registro[registro["sexo"].isin(["F", "M"])]
    .pivot_table(index="nombre", columns="sexo", values="n", aggfunc="sum")
    .fillna(0)
    .assign(total=lambda x: x["F"] + x["M"])
    .assign(tendencia=lambda x: (x["F"] - x["M"]) / x["total"])
)

compartidos = por_nombre_sexo[
    (por_nombre_sexo["F"] > 0)
    & (por_nombre_sexo["M"] > 0)
    & (por_nombre_sexo["total"] >= UMBRAL_COMPARTIDO)
    & (por_nombre_sexo["tendencia"].abs() <= REPARTO_MAXIMO)
]

print(f"{((por_nombre_sexo['F'] > 0) & (por_nombre_sexo['M'] > 0)).sum():,} nombres se "
      f"inscribieron para los dos sexos, {len(compartidos):,} con volumen y reparto parejo")
print(compartidos.reindex(compartidos["tendencia"].abs().sort_values().index)
      .head(5)[["F", "M", "tendencia"]].round(3))

# El reparto se lee mejor como barras apiladas que como burbujas: cada nombre
# ocupa el mismo largo y lo que se compara es dónde cae la división.

reparto = compartidos[["F", "M"]].div(compartidos["total"], axis=0).mul(100).sort_values("F")

fig, ax = plt.subplots(figsize=(4.4, 4.0))

barchart(reparto, stacked=True, horizontal=True, palette=[MAGENTA, AZUL], ax=ax)

ax.set_title("Nombres que se inscriben para los dos sexos")
ax.set_xlabel("% de las inscripciones del nombre")
ax.set_ylabel("")
ax.axvline(50, color="white", linestyle="dotted", linewidth=1)

fig.savefig("images/06-compartidos.png", dpi=DPI, bbox_inches="tight")

# %%
# El grupo que las tareas necesitan casi nunca viene como columna. Acá es la
# posición que ocupa cada nombre dentro del repertorio de su año, y hay que
# construirla. El ranking se calcula dentro de cada año, así que la banda de un
# nombre cambia con el tiempo.

BANDAS = [0, 10, 100, 1_000, np.inf]
ETIQUETAS = ["1 a 10", "11 a 100", "101 a 1.000", "más de 1.000"]

ranking = por_nombre.assign(
    rango=por_nombre.groupby("anio")["n"].rank(method="first", ascending=False)
).assign(banda=lambda x: pd.cut(x["rango"], BANDAS, labels=ETIQUETAS))

bandas = ranking.groupby(["anio", "banda"], observed=True)["n"].sum().unstack()
bandas = bandas.div(bandas.sum(axis=1), axis=0) * 100

print(bandas.loc[[ANIO_INICIO, 1970, 2021]].round(1))

fig, ax = plt.subplots(figsize=(5.8, 2.9))

bandas[ETIQUETAS].plot(
    kind="area",
    ax=ax,
    lw=0,
    color=sns.light_palette(AZUL, n_colors=len(ETIQUETAS) + 1)[1:][::-1],
)

ax.set_title("Reparto de las inscripciones según la posición del nombre en su año")
ax.set_xlabel("Año de inscripción")
ax.set_ylabel("% de las inscripciones del año")
ax.set_xlim(ANIO_INICIO, 2021)
ax.set_ylim(0, 100)
ax.legend(title="Posición", fontsize=7, loc="center left", bbox_to_anchor=(1.02, 0.5))

fig.savefig("images/06-estratos.png", dpi=DPI, bbox_inches="tight")

# La figura resuelve la primera tarea: el cambio de concentración existe y se
# puede dibujar. La segunda es el cambio de composición, y se verifica aparte,
# mirando quiénes ocupan las primeras posiciones y qué pasó con los de antes.

fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.6), sharex=True)

for ax, anio in zip(axes, (ANIO_INICIO, 2021)):
    top = (conteo.loc[anio].nlargest(10) / totales_anuales[anio] * 100).to_frame("parte")
    barchart(top, horizontal=True, sort_items=True, sort_items_ascending=True,
             legend=False, palette=[AZUL], ax=ax)
    ax.set_title(str(anio))
    ax.set_ylabel("")
    ax.set_xlabel("% de las inscripciones del año")

fig.savefig("images/06-top10.png", dpi=DPI, bbox_inches="tight")

maria = ranking[ranking["nombre"] == "María"].set_index("anio")
for anio in (ANIO_INICIO, 2021):
    print(f"María en {anio}: posición {int(maria.loc[anio, 'rango'])}, "
          f"{maria.loc[anio, 'n'] / totales_anuales[anio] * 100:.2f}% del año")

# Las dos listas no comparten ningún nombre, pero perder las primeras posiciones
# no es lo mismo que desaparecer.

# %%
# Los cortes anteriores los decidimos nosotros. También se pueden derivar de la
# forma de la serie: se describe cada nombre por cómo repartió sus inscripciones
# entre las décadas y se agrupan los que se parecen.

NOMBRES_EN_MAPA = 30

perfil_decadas = (
    registro.assign(decada=registro["anio"] // 10 * 10)
    .groupby(["nombre", "decada"])["n"]
    .sum()
    .unstack(fill_value=0)
    .loc[total_por_nombre.index[:NOMBRES_EN_MAPA]]
)
# Cada fila se divide por su propio total, así lo que se compara es la forma de
# la trayectoria y no cuántas veces se usó el nombre.
perfil_decadas = perfil_decadas.div(perfil_decadas.sum(axis=1), axis=0)

ax = heatmap(
    perfil_decadas,
    cluster_rows=True,
    fig_args=dict(figsize=(5.4, 5.0)),
    cmap="magma_r",
    cbar_kws={"label": "% de las inscripciones del nombre"},
)
ax.set_xlabel("Década")
ax.set_ylabel("")

ax.get_figure().savefig("images/06-cluster.png", dpi=DPI, bbox_inches="tight")

# El agrupamiento no sabe nada del tiempo y aun así separa generaciones: los
# nombres de mediados de siglo, los que llegan en los ochenta y los recientes.

# %%
# PARTE 9: de la descripción al insight
#
# Todo lo anterior describe. La tercera tarea es identificar los años de cambio
# brusco, así que hay que comprobar que existan y se puedan encontrar. Antes de
# elegir a mano qué nombres mirar, conviene que los datos propongan los
# candidatos.

UMBRAL_MODA = 500

candidatos = total_por_nombre[total_por_nombre >= UMBRAL_MODA].index
partes_anuales = (
    conteo[conteo.index.get_level_values("nombre").isin(candidatos)]
    .unstack(fill_value=0)
    .div(totales_anuales, axis=0)
    * 10_000
)


def salto_del_maximo(serie):
    """Cuántas veces el año más alto de un nombre supera el promedio de los
    cinco anteriores. Un valor alto marca un nombre que subió en un solo año."""
    anio = serie.idxmax()
    previos = serie.loc[max(ANIO_INICIO, anio - 5) : anio - 1]
    if previos.empty or previos.mean() == 0:
        return np.nan
    return serie.max() / previos.mean()


modas = (
    pd.DataFrame({
        "salto": partes_anuales.apply(salto_del_maximo),
        "anio": partes_anuales.idxmax(),
        "por_10mil": partes_anuales.max(),
    })
    .dropna()
    .sort_values("salto", ascending=False)
)

print(modas.head(10).round(1))

# %%
# La señal es más confiable cuando varios nombres saltan el mismo año.

SALTO_MINIMO = 3

anios_con_moda = (
    modas[modas["salto"] >= SALTO_MINIMO].groupby("anio").size().sort_values(ascending=False)
)
encabezan = modas[(modas["salto"] >= SALTO_MINIMO) & (modas["anio"] == 2006)]

print(anios_con_moda.head(5).to_dict())
print(f"Los {len(encabezan)} de 2006: "
      f"{', '.join(encabezan.sort_values('salto', ascending=False).head(10).index)}")

# Son las grafías sin tilde de nombres que sí la llevan. Se comprueba sumando
# las dos: si el total crece parejo, lo que cambió es cómo se escribió el nombre
# y no cuántas veces se eligió.

conteos_grafia = guaguas.groupby(["anio", "nombre"])["n"].sum().unstack(fill_value=0)

par = conteos_grafia[["Sofía", "Sofia"]].loc[1998:2012]
print(par.assign(suma=par.sum(axis=1)).loc[2003:2008])

fig, ax = plt.subplots(figsize=(5.4, 2.8))

par.assign(suma=par.sum(axis=1)).set_axis(
    ["Sofía, con tilde", "Sofia, sin tilde", "Las dos juntas"], axis=1
).plot(ax=ax, color=[AZUL, MAGENTA, GRIS], style=["-", "-", "--"], lw=1.4)

ax.axvspan(2005, 2006, color=GRIS, alpha=0.5, linewidth=0, zorder=0)
ax.set_title("Las dos grafías de Sofía y su suma")
ax.set_xlabel("Año de inscripción")
ax.set_ylabel("Inscripciones")
ax.set_ylim(0, None)
ax.yaxis.set_major_formatter(MILES)
ax.legend(fontsize=7)

fig.savefig("images/06-artefacto.png", dpi=DPI, bbox_inches="tight")

# En 2005 y 2006 parte de los registros perdió sus tildes. Es la misma familia
# de errores de la parte 2, con mil veces más inscripciones involucradas, y
# suficiente para inflar la diversidad de esos dos años.

# %%
# El salto ordena por lo abrupto, así que privilegia una forma de moda sobre las
# otras. Los cuatro paneles están todos en el pool de candidatos, pero solo el
# primero sale arriba en esa lista.

GRUPOS = [
    ("Un año", ["Branco", "Milenka"]),
    ("Un lustro", ["Millaray"]),
    ("Una generación", ["Kevin", "Bryan", "Brian"]),
    ("Todavía subiendo", ["Liam", "Nahuel"]),
]
COLORES_MODA = [AZUL, MAGENTA, "#2E9E8F"]

fig, axes = plt.subplots(2, 2, figsize=(6.6, 4.2), sharex=True)

for ax, (titulo, nombres) in zip(axes.flat, GRUPOS):
    partes_anuales[nombres].plot(ax=ax, color=COLORES_MODA[: len(nombres)], lw=1.2)
    ax.set_title(titulo, fontsize=9)
    ax.set_xlabel("")
    ax.set_xlim(1960, 2021)
    ax.set_ylim(0, None)
    ax.legend(fontsize=6)

for ax in axes[:, 0]:
    ax.set_ylabel("Por cada 10.000\ninscripciones del año")

fig.savefig("images/06-modas.png", dpi=DPI, bbox_inches="tight")

# Cuándo pasó está en la tabla; por qué pasó, no:
#
#   Branco y Milenka        personajes de Romané, telenovela de TVN de 2000
#   Kevin, Bryan y Brian    los Backstreet Boys, en su punto más alto en 1998
#   Liam                    One Direction, banda formada en 2010
#
# Ese salto del patrón al contexto es un insight, y responde el por qué sin
# ajustar ningún modelo.

# %%
# La fuerza de cada atribución depende de cuántas huellas dejó el fenómeno, y
# eso sí se mide con la tabla.

HUELLAS = {
    "Romané": ["Branco", "Milenka", "Salomé", "Jovanka"],
    "Backstreet Boys": ["Kevin", "Brian", "Bryan", "Nick"],
    "One Direction": ["Liam", "Harry", "Niall", "Zayn"],
}

for caso, nombres in HUELLAS.items():
    serie = conteos_grafia[nombres].loc[ANIO_INICIO:]
    print(f"{caso}: " + ", ".join(
        f"{n} {serie[n].sum():,} en {serie[n].idxmax()}" for n in nombres
    ))

# Romané deja cuatro nombres con máximo en 2000 y los Backstreet Boys cuatro en
# 1998 o 1999. De One Direction solo Liam tiene volumen, y además sigue subiendo
# cinco años después de que la banda se separó. Cuatro series que coinciden son
# evidencia; una sola es una coincidencia de fechas.

# %%
# El mismo cruce sobre una serie más conocida, en dos encuadres: el registro
# completo y el tramo donde ocurren los hechos.

CASOS = {"Salvador": AZUL, "Augusto": MAGENTA}

# Salvador Allende fue candidato presidencial cuatro veces antes de ganar.
ELECCIONES = [1952, 1958, 1964, 1970]

# Cada hito lleva su altura y su alineación, porque 1970 y 1973 quedan a tres
# años de distancia y las etiquetas se pisan si van a la misma altura.
HITOS = {
    1970: ("Allende asume\nla presidencia", 0.98, "right"),
    1973: ("Golpe de\nEstado", 0.72, "left"),
    1990: ("Fin de la\ndictadura", 0.98, "left"),
    2006: ("Muere\nPinochet", 0.72, "left"),
}

series = (
    registro[registro["nombre"].isin(CASOS)]
    .groupby(["anio", "nombre"])["parte"]
    .sum()
    .unstack(fill_value=0)
    * 10_000
)

fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.8))

series[list(CASOS)].plot(ax=axes[0], color=CASOS, legend=False)
axes[0].set_title("Todo el registro")
axes[0].set_xlim(ANIO_INICIO, 2021)

VENTANA = (1945, 2010)

series.loc[VENTANA[0] : VENTANA[1], list(CASOS)].plot(ax=axes[1], color=CASOS)
axes[1].scatter(
    ELECCIONES,
    series.loc[ELECCIONES, "Salvador"],
    color="white",
    edgecolor=AZUL,
    linewidth=0.8,
    s=18,
    zorder=5,
    label="Allende candidato",
)
axes[1].set_title(f"Entre {VENTANA[0]} y {VENTANA[1]}")
axes[1].set_xlim(*VENTANA)
axes[1].legend(fontsize=6, loc="lower left")

for anio, (etiqueta, altura, alineacion) in HITOS.items():
    axes[1].axvline(anio, color=GRIS, linestyle="dotted", linewidth=1)
    axes[1].annotate(
        etiqueta,
        xy=(anio + (0.4 if alineacion == "left" else -0.4), altura),
        xycoords=("data", "axes fraction"),
        ha=alineacion,
        va="top",
        fontsize=5.5,
        color="#555555",
    )

for ax in axes:
    ax.set_xlabel("Año de inscripción")
    ax.set_ylabel("Por cada 10.000 inscripciones")
    ax.set_ylim(0, None)

fig.savefig("images/06-contexto.png", dpi=DPI, bbox_inches="tight")

print(series.loc[[1964, 1970, 1973, 1974, 2021]].round(2))

# Los dos paneles son la misma serie y no dicen lo mismo. En el izquierdo domina
# el alza reciente; en el derecho aparecen dos movimientos alineados con fechas
# que no están en los datos.

# %%
# PARTE 10: conclusión sobre la factibilidad
#
# La pregunta de la sesión era si los datos sostienen las tareas, así que la
# respuesta se arma revisándolas una por una:
#
#   comparar la concentración   sí: las bandas de ranking la dibujan y el alza
#                               de diversidad se mantiene al igualar el tamaño
#                               de la muestra (partes 5 y 8)
#   comparar la composición     sí: las diez primeras posiciones se renuevan por
#                               completo entre 1930 y 2021 (parte 8)
#   identificar los años de     sí: la búsqueda los encuentra y separa los
#   cambio brusco               reales del artefacto de la fuente (parte 9)
#
# El proyecto sigue. Si la diversidad no hubiera variado, o si el alza hubiera
# resultado ser el crecimiento del registro, habría que cambiar la propuesta.
#
# Los límites que hay que declarar en la entrega, cada uno con la parte donde
# está medido:
#
#   1930 como año de inicio, por cobertura del registro          parte 5
#   desde 2018 la fuente registra más nombres distintos          parte 5
#   en 2005 y 2006 parte de los registros perdió sus tildes      parte 9
#   el sexo registral I existe solo desde 2005                   parte 2
#   errores de transcripción con tilde invertida                 parte 2
#   la correlación entre año del máximo y concentración vive
#     entre décadas y no dentro de ellas                         parte 6
#
# Y las dos preguntas que esta fuente no responde: dónde, porque no hay columna
# geográfica (parte 7), y por qué, que se aborda conectando los patrones con
# conocimiento del dominio y no con un modelo sobre esta tabla (parte 9).
