"""
extractor.py
============
Módulo de extracción de texto desde archivos PDF.

Estrategia:
- Se usa PyMuPDF (fitz) como extractor principal por su velocidad y robustez.
- Para PDFs con columnas (layout complejo), se usa pdfplumber como fallback,
  ya que respeta mejor el orden de lectura en layouts multi-columna.
- El texto resultante se limpia de ruido típico (saltos de línea excesivos,
  caracteres extraños, espacios múltiples, texto pegado sin espacios).

Dependencias:
    pip install pymupdf pdfplumber
"""

import re
import fitz          # PyMuPDF
import pdfplumber
from pathlib import Path


def extraer_texto(ruta_pdf: str | Path, metodo: str = "auto") -> dict:
    """
    Extrae el texto de un archivo PDF y devuelve un diccionario con:
        - 'texto'   : str  — texto limpio y concatenado de todas las páginas
        - 'paginas' : int  — número de páginas del documento
        - 'metodo'  : str  — método usado ('pymupdf' o 'pdfplumber')
        - 'ruta'    : str  — ruta del archivo procesado
    """
    ruta_pdf = Path(ruta_pdf)
    if not ruta_pdf.exists():
        raise FileNotFoundError(f"No se encuentra el archivo: {ruta_pdf}")

    if metodo == "pymupdf":
        texto, n_paginas = _extraer_pymupdf(ruta_pdf)
        metodo_usado = "pymupdf"
    elif metodo == "pdfplumber":
        texto, n_paginas = _extraer_pdfplumber(ruta_pdf)
        metodo_usado = "pdfplumber"
    elif metodo == "auto":
        texto, n_paginas = _extraer_pymupdf(ruta_pdf)
        metodo_usado = "pymupdf"
        if n_paginas > 0 and len(texto) / n_paginas < 100:
            texto_alt, _ = _extraer_pdfplumber(ruta_pdf)
            if len(texto_alt) > len(texto):
                texto = texto_alt
                metodo_usado = "pdfplumber (fallback)"
    else:
        raise ValueError(
            f"Método desconocido: '{metodo}'. Usa 'auto', 'pymupdf' o 'pdfplumber'."
        )

    texto_limpio = _limpiar_texto(texto)

    return {
        "texto":   texto_limpio,
        "paginas": n_paginas,
        "metodo":  metodo_usado,
        "ruta":    str(ruta_pdf),
    }


def _extraer_pymupdf(ruta_pdf: Path) -> tuple[str, int]:
    doc = fitz.open(str(ruta_pdf))
    paginas_texto = []
    for pagina in doc:
        texto_pagina = pagina.get_text("text", sort=True)
        paginas_texto.append(texto_pagina)
    doc.close()
    return "\n".join(paginas_texto), len(paginas_texto)


def _extraer_pdfplumber(ruta_pdf: Path) -> tuple[str, int]:
    paginas_texto = []
    with pdfplumber.open(str(ruta_pdf)) as pdf:
        for pagina in pdf.pages:
            texto_pagina = pagina.extract_text()
            if texto_pagina:
                paginas_texto.append(texto_pagina)
    return "\n".join(paginas_texto), len(paginas_texto)


def _separar_texto_pegado(texto: str) -> str:
    texto = re.sub(r'-\n([a-záéíóúüñ])', r'\1', texto)
    texto = re.sub(r'(\d)([a-záéíóúüñ])', r'\1 \2', texto)
    texto = re.sub(r'([a-záéíóúüñ])([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ])', r'\1 \2', texto)
    return texto


def _limpiar_texto(texto: str) -> str:
    texto = _separar_texto_pegado(texto)
    texto = re.sub(r'[^\x09\x0A\x20-\x7E\x80-\xFF]', ' ', texto)
    texto = re.sub(r'[ \t]+', ' ', texto)
    lineas = [linea.strip() for linea in texto.splitlines()]
    lineas_limpias = []
    lineas_vacias_consecutivas = 0
    for linea in lineas:
        if linea == '':
            lineas_vacias_consecutivas += 1
            if lineas_vacias_consecutivas <= 2:
                lineas_limpias.append(linea)
        else:
            lineas_vacias_consecutivas = 0
            lineas_limpias.append(linea)
    return "\n".join(lineas_limpias).strip()
