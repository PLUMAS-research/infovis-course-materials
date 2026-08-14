# Figuras de las clases

Cada archivo `NN-*.py` construye las figuras que aparecen en las slides de la unidad `NN`. Se ejecutan desde la raíz del repositorio y escriben en `images/`:

```shell
uv run python figuras/01-introduccion.py
```

Estos scripts son parte del material de estudio. Las demostraciones de las clases de teoría (una ilusión perceptual, un cuarteto de datos, una escala mal elegida) no son imágenes traídas de otro lado: están construidas con el mismo código que usaremos en las sesiones prácticas, y se pueden leer, modificar y volver a ejecutar.

Sirven además como ejemplos cortos de matplotlib. Cada uno cabe en una pantalla y muestra una operación básica: componer una grilla de paneles, anotar un punto, controlar los límites de los ejes, elegir marcadores y colores.

El estilo visual (fuente, colores, resolución) viene de `visutils.estilo`, así que las figuras se ven igual en las slides, en los apuntes y en los scripts de clase.
