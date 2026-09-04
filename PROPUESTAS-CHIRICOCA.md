# Propuestas para chiricoca desde el material del curso

Cada propuesta sale de código que ya existe en este repositorio y que se repite,
o de una trampa con la que tropezamos al preparar las primeras cuatro unidades.
Van ordenadas por cuánto código eliminan frente a cuánto cuestan.

## 1. Publicar `context_boundaries` (resuelto en 0.3.0)

`chiricoca.maps.utils.context_boundaries` ya se puede importar desde la versión
que instala el curso. Queda pendiente el trabajo del lado del material: tres
scripts y dos decks siguen dibujando los bordes a mano y conviene migrarlos.

```python
comunas.boundary.plot(ax=ax, color=AZUL, linewidth=0.3, zorder=5)
```

## 2. Formato numérico en castellano

El separador de miles de matplotlib es la coma, que en castellano es el
separador decimal. Hoy se corrige por eje y a mano:

```python
ax.xaxis.set_major_formatter(lambda x, _: f"{x:,.0f}".replace(",", "."))
```

Un gráfico que muestre 63.627 siniestros como `63,627` no es un detalle de
estilo: dice otro número. La propuesta es que `setup_style` acepte el idioma y
lo aplique a los ejes por omisión.

```python
setup_style(dpi=300, locale="es")            # afecta a todos los ejes
formato_numerico(ax, axis="x", decimales=0)  # para casos puntuales
```

## 3. Registrar fuentes que no están en el sistema

`visutils/estilo.py` existe casi entero por esto: matplotlib no lee `~/.fonts`
por su cuenta, y la tipografía del curso vive dentro del paquete de una
fundición, así que hay que buscarla por patrón antes de nombrarla.

```python
def registrar_fuente():
    for ruta in (Path.home() / ".fonts").glob(PATRON_FUENTES):
        font_manager.fontManager.addfont(ruta)
    return FUENTE in mpl.font_manager.get_font_names()
```

El problema no es del curso sino de cualquier proyecto con tipografía propia, y
la consecuencia de que falle es silenciosa: matplotlib cae a su fuente por
omisión sin avisar.

```python
setup_style(font_family="Beauchef", font_glob="~/.fonts/Latinotype*/**/*.otf")
# devuelve o registra si la familia quedó disponible, en vez de fallar callado
```

## 4. Conteo de puntos sobre una grilla H3

El mapa de la unidad 03 necesita cuatro pasos para algo que se pide siempre:

```python
grilla = h3_grid_from_bounds(siniestros.total_bounds, grid_level=7)
conteo = (gpd.sjoin(siniestros[["geometry"]], grilla.reset_index(), predicate="within")
          .groupby("h3_cell_id").size().rename("siniestros"))
celdas = grilla.join(conteo, how="inner")
```

Tres de esas líneas son plomería, y el nombre de la columna del índice
(`h3_cell_id`) hay que descubrirlo leyendo el código de la biblioteca.

```python
celdas = contar_en_grilla(siniestros, grid_level=7, columna="siniestros")
celdas = agregar_en_grilla(siniestros, grid_level=7, agg={"victimas": "sum"})
```

La unidad 08 (mapas) y la 12 (reducción de complejidad) van a repetir el mismo
patrón, así que conviene resolverlo antes.

## 5. Descarga de datasets publicados

`visutils/general.py` baja un `.tgz` de un servidor, lo extrae en `data/` y
devuelve la carpeta. Se usa catorce veces en el material y es el mismo problema
en CC5216.

```python
carpeta = fetch_dataset("siniestros.tgz", base_url=URL_CURSO)  # cachea en data/
archivo = fetch_file("ndvi-santiago-2023.tif", base_url=URL_CURSO)
```

Con la URL base configurable por variable de entorno, el mismo código sirve a
los dos cursos sin tocar los scripts.

## 6. Piezas para diagramas conceptuales

`visutils/diagramas.py` tiene seis funciones (`flecha`, `rotulo`, `celda`,
`caja`, `encabezado`, `titulo`) que usan los cuatro scripts de `figuras/`. Con
ellas se traducen al castellano las figuras de Munzner: tipos de dataset, tipos
de atributo, taxonomía de tareas y ranking de canales.

No son específicas del curso: son primitivas para dibujar un diagrama sobre un
eje de matplotlib con un estilo consistente. Un módulo `chiricoca.diagrams` las
dejaría disponibles para papers y presentaciones, que es donde vuelven a
aparecer.

La función `titulo` resuelve algo que no es obvio: mide el ancho real del texto
ya dibujado para pegarle una aclaración en cuerpo menor, en vez de estimar el
desplazamiento a ojo.

## 7. Detalles de `barchart` que hoy se corrigen después

Tres líneas aparecen siempre después de llamarlo:

```python
ax.set_ylabel("")            # si no, queda el nombre del índice, "tipo_agrupado"
sort_items_ascending=True    # en horizontal, el primero queda abajo
ax.xaxis.set_major_formatter(...)
```

Propuestas: que el nombre del índice no se use como rótulo de eje cuando es un
identificador técnico; y que `sort_items` acepte el orden visual deseado
(`"mayor_arriba"`) en vez de obligar a razonar sobre el orden interno.

## 8. Anotar valores sobre las barras

La distribución de víctimas del hito 1 anota el porcentaje sobre cada barra con
un bucle:

```python
for x, valor in enumerate(distribucion):
    ax.annotate(f"{valor:.1f}%", (x, valor), ha="center", va="bottom", fontsize=7)
```

`barchart` ya tiene `annotate=True`, pero sin control de formato. Con
`annotate_format="{:.1f}%"` el bucle desaparece, y con él la fuente más común de
inconsistencia entre lo que dice el eje y lo que dice la etiqueta.

## 9. Simulación de daltonismo

La unidad 07 (color) tiene en su programa "verificación de la paleta bajo
simulación de daltonismo". chiricoca ya construyó `BIVARIATE_BLUE_ORANGE` y
`BIVARIATE_PURPLE_TEAL` validándolas contra deuteranopía y protanopía, así que
la herramienta de validación existe en alguna forma.

Exponerla convierte esa clase en algo ejecutable:

```python
simular_cvd(colores, tipo="deuteranopia")   # lista de colores transformada
figura_cvd(fig, tipos=("deuteranopia", "protanopia"))  # la misma figura, tres veces
```

## 10. Un tema con colores nombrados

El curso define `AZUL`, `MAGENTA` y `GRIS` en `visutils/estilo.py` y los importa
en todos los scripts. Cualquier proyecto con identidad visual hace lo mismo.

```python
setup_style(theme={"primary": "#0A0E50", "accent": "#CF3889", "muted": "#D6D6DE"})
from chiricoca.config import theme
theme("accent")
```

Con eso, `barchart(palette="theme")` y las funciones de mapas podrían tomar los
colores del proyecto sin recibirlos en cada llamada.

## Lo que no conviene mover a la biblioteca

- **La comparación de un atributo en cinco canales** (unidad 04) es material
  didáctico: su valor está en que el estudiante lea el código, no en llamarlo.
- **Las traducciones de las figuras de Munzner** son contenido del curso, con
  texto en castellano y decisiones de traducción. Lo reusable son las piezas
  para dibujarlas, que es la propuesta 6.
- **`estilo_curso()`** seguirá existiendo aunque se acepten las propuestas 2, 3
  y 10: su trabajo es fijar los valores del curso, y eso es propio del proyecto.

## 11. Leyenda en `stacked_areas`

`stacked_areas` dibuja cada banda con un `fill_between` que no recibe `label`, así que la figura no tiene con qué armar la leyenda:

```python
stacked_areas(ax, bandas, color_dict=colores)
ax.legend()  # UserWarning: No artists with labels found
```

La unidad 06 necesitaba una leyenda con las cuatro bandas de ranking y terminó usando el `.plot(kind="area")` de pandas, que sí las rotula. La propuesta es que `stacked_areas` pase el nombre de cada columna como `label` de su banda, con lo que `ax.legend()` funciona sin cambiar nada más. Es la misma información que ya está en `df.columns`.

## 12. Color de las etiquetas en `bubble_plot` (baja prioridad)

`bubble_plot` dibuja cada etiqueta con `ax.annotate` sin pasar `color`, así que
toma el color de texto por omisión. Con `dual_left_color` oscuro, las etiquetas
quedan negro sobre azul marino y no se leen. Hoy se corrige después:

```python
bubble_plot(df, "tendencia", "total", label_column="nombre", dual=True,
            dual_left_color=AZUL, dual_right_color=MAGENTA, ax=ax)
for etiqueta in ax.texts:
    etiqueta.set_color("white")
```

Ese bucle toca también cualquier texto que ya estuviera en el eje. La propuesta
es un parámetro `label_color`, o que la función elija blanco o negro según la
luminancia del color de la burbuja, que es la decisión correcta por omisión.

El mismo bucle destapó un segundo problema: el tamaño de la etiqueta sale del
radio de la burbuja sin medir el ancho del texto, así que un nombre largo se
sale de su burbuja y lo recorta el `xlim` que la propia función fija. En la
unidad 06 se resolvió bajando `max_label_size` a 20 hasta que ninguna se pasó.
