# CC5208 -- Visualización de Información

El material del curso se ejecuta con `uv`. [Aquí puedes ver sus instrucciones de instalación](https://docs.astral.sh/uv/getting-started/installation/).

Si tienes `uv` instalado, el comando `uv sync` instala todo lo necesario para que ejecutes el código del curso.

Además, en cada clase es recomendable ejecutar `uv lock --upgrade-package chiricoca` y luego `uv sync`. Esto actualizará el código del repositorio `chiricoca` (base de visualización) en caso de que haya cambiado entre una clase y otra (es probable que lo haga).

Los scripts se ejecutan con `uv run python <script>.py`. Están organizados en celdas `# %%`, así que también puedes ejecutarlos paso a paso desde VS Code o desde un notebook.

La carpeta `visutils` contiene funciones utilitarias para trabajar con los datos del curso. La carpeta `data` contiene datos que se descargan de manera automática en cada script.

## Estructura del curso

Cada unidad ocupa dos sesiones: una de teoría y una de código. Acá están las piezas ejecutables de las dos:

- `NN-<nombre>.py`: el script de la sesión de código.
- `figuras/NN-<nombre>.py`: el código que construye las figuras que se muestran en la sesión de teoría. Las demostraciones de esa clase se pueden leer, modificar y volver a ejecutar; sirven además como ejemplos cortos de matplotlib.

Los dos escriben sus figuras en `images/`, que se crea al ejecutarlos. Las slides de la sesión de teoría se entregan aparte y no están en este repositorio.

## Clases

* `01-primer-grafico.py`: de una tabla a un gráfico que se sostiene solo, con los nombres inscritos en el Registro Civil entre 1920 y 2021. Estructura de una tabla (ítems, atributos y sus tipos), construcción de un gráfico completo con título, ejes y fuente, la diferencia entre graficar conteos y proporciones, y una pregunta nueva derivada de lo que muestra el gráfico.

* `02-tipos-de-dataset.py`: los cuatro tipos de dataset con un ejemplo de cada uno (viajes de la EOD, red de músicos de jazz, NDVI de Santiago y comunas de la Región Metropolitana). Qué es un ítem en cada caso, qué tipos de atributo hay, cómo se grafica un atributo cíclico y cómo la misma tabla se puede modelar como red.

* `03-tareas.py`: una pregunta, una tarea, un gráfico, con los siniestros de tránsito de la Región Metropolitana. Nombrar la tarea (acción más objetivo) antes de elegir el gráfico, y distinguir cuándo una respuesta es una descripción de los datos y cuándo llega a ser un insight. La segunda mitad arma un hito 1 completo con el mismo dataset: la propuesta, las variables con sus distribuciones, la cobertura temporal y espacial, y los límites que hay que declarar.

* `04-codificacion-visual.py`: el mismo atributo codificado con posición, largo, área, ángulo y luminosidad, comparados lado a lado, con los siniestros agregados por comuna. Qué falla al aplicar un canal de magnitud a un atributo categórico, cuántos niveles de un canal se distinguen, y un glifo por comuna sobre el mapa del Gran Santiago con los viajes de la EOD.

* `05-tablas.py`: el catálogo de gráficos para tablas, con los nombres del Registro Civil y los viajes de la EOD. Cada técnica se describe con los datos que necesita, la marca, los canales y la tarea que resuelve, y se muestra la operación de datos que la precede (agregar, pivotar, normalizar).

* `06-analisis-exploratorio.py`: un análisis exploratorio completo con la forma de un hito 2, sobre los nombres del Registro Civil. Los criterios de limpieza y filtrado con sus conteos, las propiedades globales respondiendo qué, cuándo y cómo, la comparación entre grupos que vienen en los datos y grupos derivados (incluido un agrupamiento por la forma de la trayectoria), y una conclusión sobre la factibilidad con sus límites declarados.

## Evaluación

El curso se evalúa con un proyecto que avanza durante el semestre a través de cuatro hitos y un examen. Los hitos son la definición del proyecto y la presentación de sus datos (10%), el análisis exploratorio (20%), los insights (30%) y el producto de visualización (40%). El examen es un poster.

Se exime del examen quien tenga nota de hitos igual o superior a 5,5 y asistencia superior al 80% de las sesiones. Quien no se exime obtiene su nota final con 60% de la nota de hitos y 40% de la nota del examen.

Las rúbricas están en `evaluacion/`.

## Referencias por verificar

Datos de fuentes que el material cita y que hay que confirmar antes de dejarlas en las slides:

- La lámina "Lo que la tabla no dice" de la unidad 06 atribuye tres saltos a fenómenos de cultura popular. Los datos confirman las coincidencias de fechas; falta confirmar los hechos externos.
  - *Romané*, telenovela de TVN: Branco, Milenka, Salomé y Jovanka alcanzan su máximo en 2000 (Branco pasa de 22 inscripciones en 1999 a 156 en 2000). La atribución viene del script `08-texto-guaguas.py` de la versión anterior del curso. Falta confirmar el año de emisión y que esos cuatro sean nombres de personajes.
  - Backstreet Boys: Kevin, Bryan y Nick alcanzan su máximo en 1998 y Brian en 1999. Falta confirmar cuáles fueron los años de mayor circulación de la banda en Chile. Kevin ya venía subiendo desde 1990, así que la banda explica el máximo pero no toda la trayectoria.
  - One Direction: Liam despega entre 2012 y 2014, cuando la banda estaba activa, y sigue subiendo hasta 2021. Falta confirmar el período de actividad de la banda. Ninguno de los otros cuatro nombres del grupo tiene volumen en el registro.
- La figura `images/06-tiempo-de-preparacion.png` reparte el tiempo de trabajo de un proyecto de datos en seis tareas (limpiar y organizar 60%, recolectar 19%, buscar patrones 9%, otras 5%, refinar algoritmos 4%, construir datos de entrenamiento 3%). La lámina de la unidad 06 la atribuye a una encuesta de CrowdFlower. Los porcentajes vienen del pptx `06 - Análisis exploratorio` del curso anterior, que citaba a Forbes (2016). Falta confirmar el informe original, su año y la cantidad de personas encuestadas.

## Bibliografía

- Munzner, T. (2014). *Visualization Analysis and Design*. CRC Press. Es la base del contenido teórico del curso.
- Cairo, A. (2012). *The Functional Art*. New Riders.
- Meirelles, I. (2013). *Design for Information*. Rockport.
