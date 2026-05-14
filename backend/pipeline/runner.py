"""
runner.py
=========
Orquestador del pipeline TalentMatch adaptado para el backend FastAPI.

Orden: extractor → keywords → scorer → explainer → dict
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .extractor import extraer_texto
from .keywords import extraer_keywords, MODELO_NOMBRE as MODELO_KEYWORDS
from .scorer import calcular_score
from .explainer import generar_explicacion


N_KEYWORDS = 15


def _nivel_score(score: float) -> str:
    if score >= 0.75:
        return "High match"
    elif score >= 0.55:
        return "Moderate match"
    elif score >= 0.35:
        return "Low match"
    else:
        return "Very low match"


def ejecutar_pipeline(
    ruta_cv: str | Path,
    ruta_puesto: str | Path,
    forzar_plantilla: bool = False,
    verbose: bool = False,
) -> dict:
    """
    Ejecuta el pipeline completo de comparación CV-Puesto.

    Retorna dict con: cv, puesto, score, matching, explicacion, metadatos.
    """
    ruta_cv     = Path(ruta_cv)
    ruta_puesto = Path(ruta_puesto)

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    log("\n[1/4] Extrayendo texto de los PDFs...")
    resultado_cv     = extraer_texto(ruta_cv)
    resultado_puesto = extraer_texto(ruta_puesto)
    texto_cv         = resultado_cv["texto"]
    texto_puesto     = resultado_puesto["texto"]

    log("\n[2/4] Extrayendo keywords...")
    kws_cv     = extraer_keywords(texto_cv,     n_keywords=N_KEYWORDS)
    kws_puesto = extraer_keywords(texto_puesto, n_keywords=N_KEYWORDS)

    log("\n[3/4] Calculando score de idoneidad...")
    resultado_score = calcular_score(texto_cv, texto_puesto, kws_puesto, kws_cv)
    score_final     = resultado_score["score"]
    nivel           = _nivel_score(score_final)

    log("\n[4/4] Generando explicación...")
    explicacion = generar_explicacion(
        score              = resultado_score["score"],
        score_global       = resultado_score["score_global"],
        score_cobertura    = resultado_score["score_cobertura"],
        keywords_cv        = kws_cv,
        keywords_cubiertas = resultado_score["keywords_cubiertas"],
        keywords_gaps      = resultado_score["keywords_gaps"],
        nombre_cv          = ruta_cv.name,
        nombre_puesto      = ruta_puesto.name,
        forzar_plantilla   = forzar_plantilla,
    )

    return {
        "cv": {
            "archivo":  ruta_cv.name,
            "paginas":  resultado_cv["paginas"],
            "keywords": kws_cv,
        },
        "puesto": {
            "archivo":  ruta_puesto.name,
            "paginas":  resultado_puesto["paginas"],
            "keywords": kws_puesto,
        },
        "score": {
            "final":     resultado_score["score"],
            "global":    resultado_score["score_global"],
            "cobertura": resultado_score["score_cobertura"],
            "gaps":      resultado_score["score_gaps"],
            "nivel":     nivel,
            "pesos":     resultado_score["detalle_pesos"],
        },
        "matching": {
            "keywords_cubiertas": resultado_score["keywords_cubiertas"],
            "keywords_gaps":      resultado_score["keywords_gaps"],
        },
        "explicacion": {
            "texto":  explicacion["texto"],
            "metodo": explicacion["metodo"],
        },
        "metadatos": {
            "timestamp":         datetime.now().isoformat(timespec="seconds"),
            "modelo_embeddings": MODELO_KEYWORDS,
            "n_keywords":        N_KEYWORDS,
        },
    }
