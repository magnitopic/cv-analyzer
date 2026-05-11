"""
keywords.py
===========
Módulo de extracción de palabras clave (keywords) desde texto de CV o Puesto.

Estrategia:
- KeyBERT como extractor principal: usa embeddings semánticos.
- YAKE como extractor alternativo: algoritmo estadístico ligero.
- Modelo multilingüe: funciona con textos en español, inglés o mezcla de ambos.

Modelo usado por defecto:
    paraphrase-multilingual-MiniLM-L12-v2
"""

from __future__ import annotations

import re

import yake
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer


MODELO_NOMBRE = "paraphrase-multilingual-MiniLM-L12-v2"

_kw_model: KeyBERT | None = None


def _cargar_modelo() -> KeyBERT:
    global _kw_model
    if _kw_model is None:
        print(f"  [keywords] Cargando modelo '{MODELO_NOMBRE}'... (solo la primera vez)")
        _modelo_st = SentenceTransformer(MODELO_NOMBRE)
        _kw_model = KeyBERT(model=_modelo_st)
        print(f"  [keywords] Modelo cargado ✅")
    return _kw_model


STOPWORDS_CV = {
    "perfil", "perfil profesional", "experiencia", "experiencia profesional",
    "formación", "formación académica", "educación", "habilidades",
    "competencias", "idiomas", "contacto", "sobre mí", "resumen",
    "certificaciones", "proyectos", "logros", "referencias", "intereses",
    "voluntariado", "publicaciones", "cursos",
    "profile", "professional profile", "experience", "work experience",
    "education", "skills", "languages", "contact", "about me", "summary",
    "certifications", "projects", "achievements", "references", "interests",
    "volunteering", "publications", "courses", "objective", "career objective",
    "años", "year", "years", "months", "meses", "presente", "present",
    "actual", "current", "empresa", "company", "ciudad", "city",
    "trabajo", "job", "puesto", "position", "rol", "role",
    "mediante", "través", "además", "también", "tanto", "como",
    "para", "con", "por", "que", "una", "uno", "los", "las",
    "del", "entre", "desde", "hasta", "durante",
    "the", "and", "for", "with", "from", "this", "that", "have",
    "has", "been", "will", "also", "both", "more", "our", "their",
    "join", "we", "you", "your", "including",
    "buscamos", "ofrecemos", "requisitos", "responsabilidades",
    "funciones", "incorporación", "inmediata", "vacante",
    "salario", "sueldo", "beneficios", "jornada", "modalidad",
    "híbrido", "remoto", "presencial", "ubicación", "sede",
    "mission", "candidate", "opportunity", "location", "hybrid",
    "remote", "office", "salary", "benefits", "apply", "hiring",
    "vacancy", "vacancies", "site", "join our", "range",
    "fulltime", "full time", "feb", "may", "jan", "jun", "jul", "aug",
    "sep", "oct", "nov", "dec", "enero", "febrero", "marzo", "abril",
    "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
    "noviembre", "diciembre",
    "present", "presente", "horas", "hours", "días", "days",
    "semanas", "weeks",
    "selección", "seleccion", "etalentum", "expansion plan",
    "permanent contract", "contrato indefinido", "contrato",
    "off intensive", "core business",
    "hackathon", "coderdojo", "attended", "club",
    "fulltime", "chief",
    "madrid hub", "hub", "cvs job", "join our team",
}


def _limpiar_para_keywords(texto: str) -> str:
    texto = re.sub(r'\S+@\S+\.\S+', '', texto)
    texto = re.sub(r'http\S+', '', texto)
    texto = re.sub(r'www\.\S+', '', texto)
    texto = re.sub(r'linkedin\.com/\S+', '', texto)
    texto = re.sub(r'github\.com/\S+', '', texto)
    texto = re.sub(r'\+?\d[\d\s\-\.]{7,}\d', '', texto)
    lineas = texto.splitlines()
    lineas_filtradas = [
        linea for linea in lineas
        if len(linea.strip()) >= 3 and not linea.strip().isdigit()
    ]
    return "\n".join(lineas_filtradas)


def _construir_stopwords_keybert() -> list[str]:
    return list(STOPWORDS_CV)


def _es_keyword_valida(kw: str) -> bool:
    kw_lower = kw.lower().strip()
    if len(kw_lower) < 3:
        return False
    if "@" in kw or "://" in kw:
        return False
    if kw_lower.replace(" ", "").isdigit():
        return False
    if kw_lower in STOPWORDS_CV:
        return False
    palabras = kw_lower.split()
    stopwords_basicas = {
        "el", "la", "los", "las", "un", "una", "de", "del", "en", "y",
        "a", "al", "o", "que", "se", "su", "por", "con", "para", "como",
        "the", "an", "of", "in", "to", "or", "on", "at", "by", "is",
        "are", "was", "be", "it", "its",
    }
    if all(p in stopwords_basicas for p in palabras):
        return False
    return True


def extraer_keywords_keybert(
    texto: str,
    n_keywords: int = 15,
    ngram_range: tuple[int, int] = (1, 2),
    diversidad: float = 0.6,
) -> list[tuple[str, float]]:
    if not texto or len(texto.strip()) < 20:
        return []

    texto_limpio = _limpiar_para_keywords(texto)
    modelo = _cargar_modelo()
    stopwords = _construir_stopwords_keybert()

    keywords = modelo.extract_keywords(
        texto_limpio,
        keyphrase_ngram_range=ngram_range,
        stop_words=stopwords,
        use_mmr=True,
        diversity=diversidad,
        top_n=n_keywords,
    )

    return [(kw, score) for kw, score in keywords if _es_keyword_valida(kw)]


def extraer_keywords_yake(
    texto: str,
    n_keywords: int = 15,
    ngram_max: int = 2,
    idioma: str = "es",
) -> list[tuple[str, float]]:
    if not texto or len(texto.strip()) < 20:
        return []

    texto_limpio = _limpiar_para_keywords(texto)
    extractor = yake.KeywordExtractor(
        lan=idioma,
        n=ngram_max,
        dedupLim=0.7,
        dedupFunc="seqm",
        windowsSize=1,
        top=n_keywords,
        features=None,
    )

    raw_keywords = extractor.extract_keywords(texto_limpio)
    if not raw_keywords:
        return []

    scores_raw = [score for _, score in raw_keywords]
    score_max = max(scores_raw)
    score_min = min(scores_raw)
    rango = score_max - score_min if score_max != score_min else 1.0

    keywords_normalizadas = [
        (kw, round(1.0 - (score - score_min) / rango, 4))
        for kw, score in raw_keywords
    ]
    keywords_normalizadas.sort(key=lambda x: x[1], reverse=True)
    return keywords_normalizadas


def extraer_keywords(
    texto: str,
    n_keywords: int = 15,
    metodo: str = "keybert",
) -> list[str]:
    """Interfaz unificada. Devuelve lista de strings (sin scores) para el pipeline."""
    if metodo == "keybert":
        resultados = extraer_keywords_keybert(texto, n_keywords=n_keywords)
    elif metodo == "yake":
        resultados = extraer_keywords_yake(texto, n_keywords=n_keywords)
    else:
        raise ValueError(f"Método desconocido: '{metodo}'. Usa 'keybert' o 'yake'.")
    return [kw for kw, _ in resultados]


def comparar_keywords(
    keywords_cv: list[str],
    keywords_puesto: list[str],
) -> dict:
    set_cv     = {kw.lower().strip() for kw in keywords_cv}
    set_puesto = {kw.lower().strip() for kw in keywords_puesto}
    return {
        "coincidencias":  sorted(set_cv & set_puesto),
        "solo_en_cv":     sorted(set_cv - set_puesto),
        "solo_en_puesto": sorted(set_puesto - set_cv),
    }
