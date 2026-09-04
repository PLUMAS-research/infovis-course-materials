# %%
"""Primera sesión de código: de una tabla a un gráfico que se sostiene solo.

Trabajamos con los nombres inscritos en el Registro Civil entre 1920 y 2021.
El objetivo no es la técnica (son gráficos de línea), sino el circuito completo:
cargar datos, describir su estructura, graficar, leer lo que aparece y decidir
qué mostrar.
"""

import matplotlib.pyplot as plt
import pandas as pd

from visutils.estilo import DPI, estilo_curso
from visutils.general import descargar_datos

estilo_curso()

# %%
# PARTE 1: los datos
#
# Cada script del curso descarga lo que necesita en la carpeta data/. Si ya
# está descargado, no vuelve a bajarlo.

carpeta = descargar_datos("guaguas.tgz")

guaguas = pd.read_csv(carpeta / "guaguas.csv.gz")

print(f"Filas: {len(guaguas):,}")
print(guaguas.head())

# %%
# PARTE 2: la tabla como dataset
#
# En el vocabulario del curso, una tabla tiene ítems (las filas) y atributos
# (las columnas). Cada atributo tiene un tipo, y el tipo determina qué
# codificaciones visuales son válidas para representarlo.
#
#   anio        cuantitativo, y además ordenado: sirve como eje
#   nombre      categórico, con muchísimas categorías
#   sexo        categórico, tres valores
#   n           cuantitativo, un conteo
#   proporcion  cuantitativo, acotado entre 0 y 1

print(guaguas.dtypes)
print()
print(f"Años: {guaguas['anio'].min()} a {guaguas['anio'].max()}")
print(f"Nombres distintos: {guaguas['nombre'].nunique():,}")
print(f"Valores de sexo: {sorted(guaguas['sexo'].unique())}")

# Un ítem de esta tabla no es una persona: es la combinación año, nombre y
# sexo, con la cantidad de inscripciones que tuvo. Saber qué representa una
# fila es la primera pregunta ante cualquier dataset.
print()
print(guaguas[(guaguas["nombre"] == "Violeta") & (guaguas["anio"] == 1957)])

# %%
# PARTE 3: el primer gráfico
#
# La serie de un nombre a lo largo del tiempo. Empezamos con lo mínimo para
# ver la forma de los datos.

maria = guaguas[guaguas["nombre"] == "María"].groupby("anio")[["n", "proporcion"]].sum()

fig, ax = plt.subplots(figsize=(5, 2.5))
maria["n"].plot(ax=ax)

# El gráfico muestra la forma, pero no se sostiene solo: nadie que lo vea
# fuera de esta pantalla sabe qué mide el eje y, de dónde salen los datos ni
# de qué nombre estamos hablando.

# %%
# PARTE 4: el mismo gráfico, terminado
#
# Título que dice qué se ve, ejes con unidades, fuente citada y el rango
# temporal explícito.

fig, ax = plt.subplots(figsize=(5, 2.5))

maria["n"].plot(ax=ax, color="#0A0E50")

ax.set_title("Inscripciones del nombre María por año")
ax.set_xlabel("Año de inscripción")
ax.set_ylabel("Inscripciones")
ax.set_xlim(1920, 2021)
ax.set_ylim(0, None)

anio_peak = maria["n"].idxmax()
ax.annotate(
    f"{anio_peak}: {maria['n'].max():,.0f}",
    xy=(anio_peak, maria["n"].max()),
    xytext=(anio_peak + 6, maria["n"].max() * 0.92),
    color="#CF3889",
)

fig.text(
    0.0,
    -0.06,
    "Fuente: Registro Civil, procesado en el paquete guaguas de Riva Quiroga.",
    fontsize=6,
)

# %%
# PARTE 5: el conteo y la proporción responden preguntas distintas
#
# El total de inscripciones cambia mucho a lo largo del siglo, así que el
# conteo mezcla dos cosas: cuánta gente nació y cómo se llamó. La proporción
# separa la segunda de la primera.

totales = guaguas.groupby("anio")["n"].sum()
print("Inscripciones totales por año:")
print(totales.loc[[1920, 1955, 1990, 2021]])

fig, axes = plt.subplots(1, 2, figsize=(7, 2.5), sharex=True)

maria["n"].plot(ax=axes[0], color="#0A0E50")
axes[0].set_title("Inscripciones del nombre María")
axes[0].set_ylabel("Inscripciones")

(maria["proporcion"] * 100).plot(ax=axes[1], color="#CF3889")
axes[1].set_title("Porcentaje de inscripciones del año")
axes[1].set_ylabel("% del total del año")

for ax in axes:
    ax.set_xlabel("Año de inscripción")
    ax.set_xlim(1920, 2021)
    ax.set_ylim(0, None)

print()
print(f"Máximo en conteo:    {maria['n'].idxmax()}")
print(f"Máximo en porcentaje: {maria['proporcion'].idxmax()}")

# Las dos curvas vienen de la misma columna de datos y llevan a conclusiones
# distintas sobre cuándo María fue más popular. Elegir entre conteo y
# proporción es una decisión de análisis, no un detalle de formato.

# %%
# PARTE 6: comparar varios nombres
#
# Cuatro nombres con picos en décadas distintas. La comparación entre series
# necesita una escala común, y la proporción la entrega.

NOMBRES = ["María", "Katherine", "Benjamín", "Sofía"]
COLORES = {
    "María": "#0A0E50",
    "Katherine": "#CF3889",
    "Benjamín": "#2E9E8F",
    "Sofía": "#E08D2F",
}

series = (
    guaguas[guaguas["nombre"].isin(NOMBRES)]
    .groupby(["anio", "nombre"])["proporcion"]
    .sum()
    .unstack(fill_value=0)
)

fig, ax = plt.subplots(figsize=(5.5, 2.8))

(series[NOMBRES] * 100).plot(ax=ax, color=COLORES, legend=False)

# La etiqueta va sobre el peak de cada serie, así no hay que ir y volver a una
# leyenda para saber qué línea es cuál.
for nombre in NOMBRES:
    anio_peak = series[nombre].idxmax()
    ax.annotate(
        f"{nombre} ({anio_peak})",
        xy=(anio_peak, series[nombre].max() * 100),
        xytext=(0, 4),
        textcoords="offset points",
        color=COLORES[nombre],
        ha="left" if anio_peak < 1930 else "center",
        va="bottom",
        fontsize=7,
    )

ax.set_title("Los nombres más frecuentes cambian con cada generación")
ax.set_xlabel("Año de inscripción")
ax.set_ylabel("% de inscripciones del año")
ax.set_xlim(1920, 2021)
ax.set_ylim(0, None)

fig.text(
    0.0,
    -0.06,
    "Fuente: Registro Civil, procesado en el paquete guaguas de Riva Quiroga.",
    fontsize=6,
)

fig.savefig("images/01-nombres-generaciones.png", dpi=DPI, bbox_inches="tight")

for nombre in NOMBRES:
    print(f"{nombre:10s} máximo {series[nombre].max() * 100:.2f}% en {series[nombre].idxmax()}")

# %%
# PARTE 7: una pregunta que el gráfico anterior deja abierta
#
# Si el nombre más frecuente de los años veinte concentraba una fracción que
# ningún nombre reciente alcanza, entonces los nombres se repartieron. Se puede
# medir: cuántos nombres distintos se necesitan para cubrir la mitad de las
# inscripciones de cada año.


def nombres_para_la_mitad(anio_df):
    ordenados = anio_df.groupby("nombre")["n"].sum().sort_values(ascending=False)
    acumulado = ordenados.cumsum() / ordenados.sum()
    return int((acumulado < 0.5).sum() + 1)


diversidad = guaguas.groupby("anio", group_keys=False).apply(
    nombres_para_la_mitad, include_groups=False
)

fig, ax = plt.subplots(figsize=(5, 2.5))

diversidad.plot(ax=ax, color="#0A0E50")

ax.set_title("Nombres necesarios para cubrir la mitad de las inscripciones")
ax.set_xlabel("Año de inscripción")
ax.set_ylabel("Cantidad de nombres")
ax.set_xlim(1920, 2021)
ax.set_ylim(0, None)

fig.text(
    0.0,
    -0.06,
    "Fuente: Registro Civil, procesado en el paquete guaguas de Riva Quiroga.",
    fontsize=6,
)

fig.savefig("images/01-diversidad-nombres.png", dpi=DPI, bbox_inches="tight")

print(diversidad.loc[[1920, 1960, 1990, 2021]])

# %%
# PARTE 8: qué quedó hecho
#
# El recorrido fue tabla, estructura, gráfico, lectura y una pregunta nueva
# que salió de la lectura. Ese ciclo es el que repetiremos todo el semestre,
# con datos y técnicas más complejas.
#
# Las dos figuras guardadas en images/ están en el formato que usaremos en el
# resto del curso: fuente citada, ejes con unidades y título que describe lo
# que se ve.

print("Figuras escritas en images/:")
print("  01-nombres-generaciones.png")
print("  01-diversidad-nombres.png")
