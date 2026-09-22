# Plan para implementar las técnicas de mapas del catálogo

El deck de mapas cataloga técnicas que muestra como imagen y no puede
ejecutar. Este documento dice cómo cerrar esa brecha: qué datos necesita cada
una, cómo se implementa, cuánto cuesta y dónde debería vivir.

Lo que chiricoca 0.3.0 ya resuelve, para tener la línea de base: `dot_map`,
`bubble_map`, `choropleth_map`, `heat_map` (KDE), `bivariate_choropleth_map` y
`lisa_map`, más `add_basemap`, `context_boundaries`, `geographical_labels`,
`geographical_scale` y `north_arrow`.

## Orden propuesto

El orden sale de dividir lo que aporta al curso por lo que cuesta. Las cuatro
primeras se pueden hacer con datos que ya publica el curso.

| # | Técnica | Datos | Costo | Dónde vive | Estado |
|---:|:---|:---|:---|:---|:---|
| 1 | Flow map de líneas | matriz OD de la EOD | bajo | chiricoca | **hecha** |
| 1b | Mapa de calor de líneas | recorridos del GTFS | bajo | chiricoca | **hecha** |
| 2 | Cartograma no contiguo | comunas más una variable | bajo | chiricoca | **hecha** |
| 3 | Cartograma de Dorling | comunas más una variable | bajo | chiricoca | **hecha** |
| 4 | Isolíneas sobre un campo | NDVI o luminosidad | bajo | chiricoca | **hecha** |
| 5 | Cubo espacio-tiempo | viajes con hora y coordenadas | medio | script del curso | |
| 6 | Isócronas | red de calles o GTFS | medio | script del curso | |
| 7 | Flowstrates | OD con dimensión temporal (DTPM) | medio | chiricoca | |
| 8 | MapTrix | matriz OD | medio-alto | chiricoca | |
| 9 | Voronoi treemap | cualquier jerarquía | alto | chiricoca | |
| 10 | Flow map layout | matriz OD desde un origen | alto | chiricoca | **hecha** |
| 11 | Cartograma contiguo | comunas más una variable | alto | chiricoca | **hecha** |

## Lo hecho

Están implementadas en `chiricoca.maps`: `flow_map` (con filtros, agregación de
sentidos, agrupamiento en corredores, semiflechas y nodos por volumen),
`filter_flows`,
`aggregate_flows`, `bundle_flows`, `flow_tree`, `line_heat_map`,
`cartogram_map` con sus tres variantes y `contour_map`. La unidad 07 las usa
todas. Lo que sigue es la nota de diseño de cada una, más el plan de las que
faltan.

Lo que apareció al implementarlas:

- **La matriz completa se dibuja reduciéndola primero, y el flow map también
  sirve con un origen fijo.** Los 1.486 pares entre las 40 comunas del área de
  estudio dan una maraña. `filter_flows` ofrece cinco criterios que responden
  preguntas distintas: umbral de peso, destinos principales por origen,
  fracción acumulada del total, disparidad (Serrano, Boguñá y Vespignani, 2009)
  y excedente sobre el esperado de una tabla de contingencia. Los cuatro
  primeros dejan como flujo mayor a Las Condes con Providencia; el de excedente
  lo cambia por La Florida con Puente Alto, porque mide afinidad y no volumen.
  Con un origen fijo la pregunta queda planteada de otra manera ("¿a dónde se
  viaja desde Puente Alto?"), y la unidad 07 compara dos orígenes en el mismo
  encuadre, uno periférico y uno central.
- **El saldo neto necesita un corte temporal.** En el día completo la ida y la
  vuelta de cada par casi se cancelan, así que `aggregate="net"` sobre toda la
  encuesta no dice nada. Cortando por hora de inicio aparece la conmutación:
  entre las 6 y las 9 el saldo mayor es Maipú hacia Santiago con 354 viajes, y
  entre las 17 y las 20 el mismo par se da vuelta con 259.
- **El agrupamiento no se llama "haces".** `bundle=True` es el método por
  densidad de Hurter, Ersoy y Telea (2012), *edge bundling* en la literatura.
  En castellano el material dice **corredor** para el resultado y **agrupar**
  para la acción: "haces" no se entiende. Gana legibilidad a cambio de perder
  por dónde va cada par.
- **La semiflecha no tiene figura propia.** `arrows="half"` pone cada sentido
  como una banda a un lado de la línea. La figura que la comparaba contra el
  trazo fundido salió vacía, porque en el día completo los pares son simétricos
  (el sentido mayor se lleva el 51%). Queda como nota en la lámina del saldo
  (restar pierde la magnitud de cada lado) y como forma de dibujar los sentidos
  en la figura de glifos. El término que usa el profesor es "semiflecha".
- **El nodo acepta un glifo en vez del punto.** `node_composition` más
  `pie_glyphs` ponen una torta en cada lugar, con el área proporcional a su
  total y los sectores repartiendo ese total entre categorías. Es la marca
  compuesta sobre un mapa, y la unidad 07 la usa con el modo y el propósito de
  los viajes. `edge_triangles` queda disponible y sin usar: cuenta en cuántos
  triángulos participa cada flujo, que es análisis de redes más que cartografía.
- **La transparencia por tramos decide si el mapa se ve bien.** Con un `alpha`
  único los cientos de flujos chicos suman tanta tinta como los pocos grandes y
  tapan la estructura; con `alpha=(0.2, 0.9)` se desvanecen. Junto con fundir
  los sentidos (que saca las lentes que forman la ida y la vuelta al curvarse
  hacia lados opuestos) es lo que separa un mapa de flujos legible de una
  maraña oscura.
- **La dirección se marca con punta de flecha** (`arrows=True`), dimensionada
  con el ancho de la línea pero con un piso del 45% del ancho mayor. Sin ese
  piso la flecha de un flujo chico no se ve al lado de la de uno grande, y la
  punta dice la dirección, no la magnitud, que ya la lleva el ancho. La línea se
  corta en la base del triángulo, porque si sigue por debajo la superposición se
  nota con transparencia.
- **La curva sirve cuando hay muchos pares.** Con líneas rectas las que comparten
  tramo quedan una encima de la otra. El punto de control de la Bézier se
  desplaza perpendicular a la recta, idea tomada de `line_with_curve_smooth`
  del repositorio Viajes_Encadenados. Con un solo origen no hace falta, así que
  las figuras de un origen fijo de la unidad 07 usan líneas rectas y las de la
  matriz completa, curva.
- **El mapa de calor de líneas necesita trazados reales, no pares.** Acumular
  rectas origen-destino produce corredores que no existen en la calle, porque
  la recta atraviesa lo que haya en medio. La unidad 07 lo hace sobre los
  recorridos del GTFS del DTPM, con la frecuencia en buses por hora como peso, y
  los ejes que aparecen son avenidas.
- **El ancho de las ramas del árbol de flujo es proporcional al valor desde
  cero, no reescalado entre el mínimo y el máximo.** Reescalado, el tronco deja
  de medir lo que suman sus ramas, que es justamente la propiedad que hace
  legible el árbol. Los nodos internos tampoco van en el centroide de su grupo:
  puestos ahí el tronco parte hacia el centro de la nube y las ramas tienen que
  devolverse. Se ubican recorriendo desde el origen hacia afuera, a una fracción
  (`branch_ratio`) del camino entre el padre y el centro del grupo.
- **Los centroides hay que calcularlos en un CRS proyectado.** En grados
  geopandas avisa y el resultado está corrido. Las tres funciones proyectan a la
  zona UTM que corresponda, calculan ahí y vuelven.
- **El cartograma de Dorling usa pymunk, que chiricoca ya trae para
  `bubble_plot`.** El relajador de colisiones a mano funcionaba, pero el motor
  hace lo mismo mejor y sin un bucle cuadrático en Python. El detalle que
  decide todo es `collision_slop`: la simulación trabaja en unidades del radio
  mayor, y con el valor por omisión de pymunk (0,1) cada contacto admite un
  décimo de ese radio de penetración. Sobre las comunas de Santiago eso deja
  11,4 km de solape total; con 1e-4 baja a 0,02 km, con el mismo desplazamiento
  respecto del centroide original y en dos centésimas de segundo.
- **Las isolíneas necesitan un campo suave.** Sobre el NDVI a treinta metros
  cada píxel produce su propia curva y el mapa queda ilegible. Hay que suavizar
  antes, y cuánto suavizar decide qué dicen las curvas: es el mismo parámetro de
  decisión que el ancho de banda de un mapa de calor.

## 1. Flow map de líneas

Dibuja cada flujo origen-destino como una línea entre los centroides, con el
ancho proporcional al volumen. Es la que más rinde: la matriz OD de la EOD la
habilita sin datos nuevos, y el repositorio anterior ya la hizo a mano en
`ejemplo-hito-2.py` con `nx.draw_networkx_edges` sobre posiciones geográficas.

Implementación: un `LineCollection` con el ancho mapeado desde el flujo, un
umbral para descartar la cola de flujos chicos y curvas de Bézier para separar
la ida del regreso, que en líneas rectas se superponen. La dirección se puede
marcar con un degradado de color a lo largo de la línea en vez de una flecha,
que a este tamaño no se ve.

```python
flow_map(salidas, comunas, source="comuna_origen",
         target="comuna_destino", weight="viajes",
         node_column="comuna", arrows=True, ax=ax)
```

## 2 y 3. Cartogramas no contiguo y de Dorling

Los dos responden el argumento de Cairo que ya cita el deck: el territorio no
vota. El no contiguo escala cada polígono en torno a su centroide según la
variable, con `shapely.affinity.scale`, y se resuelve en unas diez líneas. El de
Dorling reemplaza cada comuna por un círculo de área proporcional y separa los
círculos con un relajador de colisiones iterativo, que es un bucle corto sobre
las distancias entre centros.

Los dos son baratos y conviene hacerlos juntos, porque la comparación entre el
mapa normal, el no contiguo y el de Dorling es lo que enseña el problema.

```python
cartogram_map(geodf, "poblacion", kind="no_contiguo", ax=ax)
cartogram_map(geodf, "poblacion", kind="dorling", ax=ax)
```

## 4. Isolíneas sobre un campo

El `contour` de matplotlib sobre el arreglo del raster, con la georreferencia
puesta en `extent`. Los datos ya están publicados (NDVI y luminosidad de
Santiago). Lo que hay que resolver es la parte aburrida: leer la
georreferencia del raster, elegir los niveles y rotularlos.

La isosuperficie en tres dimensiones es otra cosa y necesita un campo 3D, que el
curso no tiene. Esa se queda como imagen de catálogo.

## 5. Cubo espacio-tiempo

Las coordenadas geográficas en el plano y la hora en el eje vertical, con una
línea por viaje. La EOD lo permite directo, porque cada viaje trae origen,
destino y hora de inicio. Se hace con `Axes3D` y `plot`, y el trabajo está en el
encuadre y en no dibujar 113.454 líneas.

Va en el script del curso y no en chiricoca, porque la lectura depende del
ángulo de cámara y eso se ajusta caso a caso.

## 6. Isócronas

Se necesita una red. El curso hermano ya tiene la versión por saltos sobre el
grafo de paraderos del DTPM, en `09-redes-urbanas.py` de `gds-course-materials`,
y la red de calles está en `redes-santiago/calles.parquet`.

Con distancia en vez de saltos: grafo en networkx con peso igual al largo del
arco dividido por la velocidad, `single_source_dijkstra_path_length` desde el
punto de origen, y el resultado agregado a una grilla H3 y dibujado como
coropleta. La versión con el contorno del área alcanzable necesita además un
alpha shape sobre los nodos alcanzados.

El costo está en el dataset, no en el algoritmo. Hay que publicar la red.

## 7. Flowstrates

Tres columnas: los orígenes en un mapa a la izquierda, los destinos en un mapa a
la derecha, y en el medio una banda por flujo donde el color muestra su
evolución en el tiempo. No es un algoritmo difícil, es composición de ejes con
`gridspec` más el ordenamiento de las filas y las líneas guía que unen cada
banda con su lugar en los dos mapas.

Necesita OD con dimensión temporal. El DTPM tiene viajes de 2014 a 2025, así que
los datos existen pero hay que prepararlos.

## 8. MapTrix

La matriz OD en el centro y dos mapas a los lados, unidos por líneas guía. La
matriz y los mapas son fáciles; lo caro es rutear las líneas guía para que no se
crucen, que es un problema de ordenamiento y de trazado por canales.

Conviene hacerla después de flowstrates, porque comparten la composición de tres
columnas y las líneas guía.

## 9. Voronoi treemap

Un treemap cuyas celdas son polígonos de Voronoi ajustados a una forma. El
algoritmo es el Voronoi centroidal ponderado de Balzer y Deussen: se itera
moviendo los sitios a los centroides y ajustando los pesos hasta que el área de
cada celda se acerca a su valor objetivo. Con `scipy.spatial.Voronoi` más el
bucle de ajuste.

Es autocontenido y no necesita datos nuevos, pero converger bien pide cuidado.
La referencia hay que verificarla antes de citarla en las slides.

## 10. Flow map layout (hecho)

`flow_tree` sigue la idea de Phan y otros sin implementar el paper
completo: agrupamiento jerárquico de los destinos con `scipy.cluster.hierarchy`,
cada nodo interno ubicado en el centroide de sus hijos ponderado por el flujo, y
el ancho de cada rama igual a la suma de sus hojas. Lo que no hace es el ruteo
que evita cruces entre ramas, que es la parte cara del paper; con treinta y seis
destinos no hace falta.

Puestos al lado, el abanico de líneas desde un mismo origen y el árbol muestran
para qué sirve: en el primero no se lee nada y en el segundo el mismo total se
reparte por troncos.

## 12. Heatmap de líneas (hecho)

No estaba en la lista original y salió del paper de física del repositorio
Viajes_Encadenados, donde acumula los abordajes del transporte público sobre los
segmentos de calle que recorren las rutas.

`line_heat_map` hace esa agregación aditiva en vectorial: densifica cada trazado
en segmentos cortos, redondea los vértices a una grilla para que dos trazados
paralelos digitalizados distinto caigan en el mismo segmento, y suma el peso de
todo lo que pasa por cada uno. Sin eso, dibujar los trazados uno sobre otro tapa
los de abajo y un eje por donde pasan cientos se ve igual que una calle por
donde pasa uno.

El exponente de la escala importa: con logarítmica la mediana cae al 63% de la
rampa y casi toda la red rinde el mismo color; con raíz cuadrada cae al 10% y
solo las troncales se oscurecen. Por eso `gamma` viene en 0,5.

## 11. Cartograma contiguo (hecho)

Quedó implementado con el método de hoja de goma de Dougenik, Chrisman y
Niemeyer (1985) y no con el de difusión de Gastner y Newman. Dougenik es
iterativo y geométrico: cada área ejerce sobre todos los vértices del mapa una
fuerza que decae con la distancia, hacia afuera si necesita crecer y hacia
adentro si necesita achicarse. Sale en cincuenta líneas de numpy, contra la
transformada del coseno y la integración del campo de velocidades que pide el
de difusión.

Dos límites que conviene tener presentes y que la función reporta:

- **No siempre converge.** Sobre las comunas de Santiago, donde la central tiene
  que crecer siete veces y las periféricas encogerse al cuatro por ciento, treinta
  iteraciones dejan un error medio del 2% y uno máximo del 38%, siempre en las
  que más tienen que achicarse: un polígono no puede colapsar sin invertirse. La
  función devuelve una columna `error_area` para poder mirarlo.
- **El costo crece con el producto de iteraciones, vértices y áreas.** Cuarenta
  comunas de mil ochocientos vértices y treinta iteraciones toman unos seis
  segundos.

## Lo que se queda como catálogo

- **Isosuperficies**: necesitan un campo escalar en tres dimensiones y el curso
  trabaja con campos en dos.
- **Voronoi treemap y flow map layout** hasta que las anteriores estén hechas.

## Referencias por verificar antes de citarlas

- Phan, D., Xiao, L., Yeh, R., Hanrahan, P. y Winograd, T. (2005). Flow Map
  Layout. *IEEE InfoVis*.
- Balzer, M. y Deussen, O. (2005). Voronoi Treemaps. *IEEE InfoVis*.
- Gastner, M. y Newman, M. (2004). Diffusion-based method for producing
  density-equalizing maps. *PNAS*, 101(20).
- Boyandin, I., Bertini, E., Bak, P. y Lalanne, D. (2011). Flowstrates.
  *Computer Graphics Forum*, 30(3).
- Yang, Y., Dwyer, T., Goodwin, S. y Marriott, K. (2017). Many-to-Many
  Geographically-Embedded Flow Visualisation (MapTrix). *IEEE TVCG*, 23(1).
