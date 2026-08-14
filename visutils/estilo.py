"""Estilo visual compartido por los scripts y las figuras de las slides."""

from pathlib import Path

import matplotlib as mpl
from matplotlib import font_manager

from chiricoca.config import setup_style

# Beauchef es la tipografía de las slides. Vive dentro del paquete de Latinotype
# y hay que buscarla por patrón, porque el nombre del directorio incluye el
# número de orden de la licencia.
FUENTE = "Beauchef"
PATRON_FUENTES = "Latinotype*/Fonts/Beauchef/OTF/*.otf"

# Tema de las slides: azul para títulos y texto, magenta para el acento.
AZUL = "#0A0E50"
MAGENTA = "#CF3889"
GRIS = "#D6D6DE"


def registrar_fuente():
    """Registra Beauchef en matplotlib, que no lee ~/.fonts por su cuenta.

    Retorna True si la fuente quedó disponible. Si no está instalada, retorna
    False y matplotlib usa la fuente por omisión de chiricoca.
    """
    for ruta in (Path.home() / ".fonts").glob(PATRON_FUENTES):
        font_manager.fontManager.addfont(ruta)

    return FUENTE in mpl.font_manager.get_font_names()


def estilo_curso(dpi=192, **kwargs):
    """Aplica el estilo de chiricoca con la fuente del curso.

    Para las figuras que van a las slides conviene `dpi=300` junto con un
    `figsize` chico, así el texto queda grande y nítido en la proyección.
    """
    fuente = FUENTE if registrar_fuente() else None
    setup_style(dpi=dpi, font_family=fuente, **kwargs)
