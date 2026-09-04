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

# Resolución de las figuras que van a las slides. A 300 el texto chico se ve
# pixelado cuando la lámina se mira con zoom en el PDF.
DPI = 400

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


def estilo_curso(dpi=DPI, **kwargs):
    """Aplica el estilo de chiricoca con la fuente del curso.

    Las figuras van a las slides, así que conviene un `figsize` chico junto con
    el `DPI` del curso: el texto queda grande y nítido en la proyección.
    """
    fuente = FUENTE if registrar_fuente() else None
    setup_style(dpi=dpi, font_family=fuente, **kwargs)
