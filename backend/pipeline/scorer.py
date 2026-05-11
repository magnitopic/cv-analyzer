"""
scorer.py
=========
Módulo de cálculo de idoneidad entre un CV y un puesto de trabajo.

Score híbrido en tres capas:
  Capa 1 — Similitud semántica global        (peso: 50%)
  Capa 2 — Cobertura de keywords del puesto  (peso: 35%)
  Capa 3 — Penalización por gaps críticos    (peso: 15%)
"""

from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


PESO_SIMILITUD_GLOBAL   = 0.50
PESO_COBERTURA_KEYWORDS = 0.35
PESO_PENALIZACION_GAPS  = 0.15

assert abs(PESO_SIMILITUD_GLOBAL + PESO_COBERTURA_KEYWORDS + PESO_PENALIZACION_GAPS - 1.0) < 1e-9

UMBRAL_SIMILITUD_KEYWORD = 0.35
N_KEYWORDS_CRITICAS = 5
MODELO_NOMBRE = "paraphrase-multilingual-MiniLM-L12-v2"

_modelo: SentenceTransformer | None = None


def _cargar_modelo() -> SentenceTransformer:
    global _modelo
    if _modelo is None:
        print(f"  [scorer] Cargando modelo '{MODELO_NOMBRE}'... (solo la primera vez)")
        _modelo = SentenceTransformer(MODELO_NOMBRE)
        print(f"  [scorer] Modelo cargado ✅")
    return _modelo


def _similitud_global(texto_cv: str, texto_puesto: str) -> float:
    modelo = _cargar_modelo()
    embeddings = modelo.encode(
        [texto_cv, texto_puesto],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    sim = float(cosine_similarity(
        embeddings[0].reshape(1, -1),
        embeddings[1].reshape(1, -1),
    )[0][0])
    return max(0.0, min(1.0, sim))


def _cobertura_keywords(
    keywords_puesto: list[str],
    keywords_cv: list[str],
) -> tuple[float, list[str], list[str]]:
    if not keywords_puesto or not keywords_cv:
        return 0.0, [], list(keywords_puesto)

    modelo = _cargar_modelo()
    emb_puesto = modelo.encode(keywords_puesto, convert_to_numpy=True, normalize_embeddings=True)
    emb_cv     = modelo.encode(keywords_cv,     convert_to_numpy=True, normalize_embeddings=True)

    sim_matrix = cosine_similarity(emb_puesto, emb_cv)
    max_sims   = sim_matrix.max(axis=1)

    cubiertas, no_cubiertas = [], []
    for kw, sim in zip(keywords_puesto, max_sims):
        (cubiertas if sim >= UMBRAL_SIMILITUD_KEYWORD else no_cubiertas).append(kw)

    return float(len(cubiertas) / len(keywords_puesto)), cubiertas, no_cubiertas


def _penalizacion_gaps(
    keywords_no_cubiertas: list[str],
    keywords_puesto: list[str],
) -> float:
    if not keywords_puesto:
        return 1.0
    criticas          = {kw.lower() for kw in keywords_puesto[:N_KEYWORDS_CRITICAS]}
    ausentes          = {kw.lower() for kw in keywords_no_cubiertas}
    ausentes_criticas = criticas & ausentes
    return float(1.0 - len(ausentes_criticas) / len(criticas))


def calcular_score(
    texto_cv: str,
    texto_puesto: str,
    keywords_puesto: list[str],
    keywords_cv: list[str] | None = None,
) -> dict:
    if not texto_cv or not texto_puesto:
        raise ValueError("Los textos del CV y del puesto no pueden estar vacíos.")

    if keywords_cv is None:
        from .keywords import extraer_keywords
        keywords_cv = extraer_keywords(texto_cv, n_keywords=15)

    score_global = _similitud_global(texto_cv, texto_puesto)
    score_cobertura, kws_cubiertas, kws_gaps = _cobertura_keywords(keywords_puesto, keywords_cv)
    score_gaps  = _penalizacion_gaps(kws_gaps, keywords_puesto)
    score_final = max(0.0, min(1.0,
        PESO_SIMILITUD_GLOBAL   * score_global    +
        PESO_COBERTURA_KEYWORDS * score_cobertura +
        PESO_PENALIZACION_GAPS  * score_gaps
    ))

    return {
        "score":              round(score_final, 4),
        "score_global":       round(score_global, 4),
        "score_cobertura":    round(score_cobertura, 4),
        "score_gaps":         round(score_gaps, 4),
        "keywords_cubiertas": kws_cubiertas,
        "keywords_gaps":      kws_gaps,
        "detalle_pesos": {
            "similitud_global":   PESO_SIMILITUD_GLOBAL,
            "cobertura_keywords": PESO_COBERTURA_KEYWORDS,
            "penalizacion_gaps":  PESO_PENALIZACION_GAPS,
        },
    }
