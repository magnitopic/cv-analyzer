"""
explainer.py
============
Módulo de generación del texto explicativo de idoneidad.

Nivel 1 — Basado en plantillas (sin LLM, siempre disponible).
Nivel 2 — Generado por Google Gemini (requiere GOOGLE_AI_API_KEY en .env).
"""

from __future__ import annotations

import os
from pathlib import Path


ENV_VAR_NAME = "GOOGLE_AI_API_KEY"
GOOGLE_MODEL = "gemini-flash-latest"


def _cargar_api_key() -> str | None:
    api_key = os.environ.get(ENV_VAR_NAME)
    if api_key:
        return api_key

    # Walk up from this file looking for a .env
    ruta_actual = Path(__file__).resolve()
    for _ in range(5):
        ruta_env = ruta_actual.parent / ".env"
        if ruta_env.exists():
            with open(ruta_env) as f:
                for linea in f:
                    linea = linea.strip()
                    if linea.startswith(f"{ENV_VAR_NAME}="):
                        valor = linea.split("=", 1)[1].strip()
                        return valor.strip('"').strip("'")
        ruta_actual = ruta_actual.parent

    return None


def _explicacion_plantilla(
    score: float,
    score_global: float,
    score_cobertura: float,
    keywords_cubiertas: list[str],
    keywords_gaps: list[str],
    nombre_cv: str = "El candidato",
    nombre_puesto: str = "el puesto",
) -> str:
    porcentaje = f"{score:.0%}"

    if score >= 0.75:
        apertura = (
            f"{nombre_cv} presenta un perfil muy adecuado para {nombre_puesto}, "
            f"con un índice de idoneidad del {porcentaje}. "
            f"La alineación semántica entre el CV y los requisitos del puesto es alta."
        )
    elif score >= 0.55:
        apertura = (
            f"{nombre_cv} muestra una idoneidad moderada para {nombre_puesto} "
            f"({porcentaje}). Existen coincidencias relevantes, aunque también "
            f"algunos requisitos que el CV no cubre explícitamente."
        )
    elif score >= 0.35:
        apertura = (
            f"La adecuación de {nombre_cv} a {nombre_puesto} es limitada "
            f"({porcentaje}). Si bien hay algunos puntos de contacto, el perfil "
            f"del candidato presenta diferencias significativas respecto a lo requerido."
        )
    else:
        apertura = (
            f"{nombre_cv} no parece encajar con el perfil de {nombre_puesto} "
            f"según el análisis automático ({porcentaje}). "
            f"El CV y los requisitos del puesto pertenecen a dominios poco relacionados."
        )

    if keywords_cubiertas:
        n       = len(keywords_cubiertas)
        muestra = keywords_cubiertas[:4]
        lista   = ", ".join(f'"{k}"' for k in muestra)
        sufijo  = " entre otros" if n > 4 else ""
        fortalezas = (
            f"Entre los aspectos que mejor se alinean con el puesto destacan "
            f"{lista}{sufijo}, con una cobertura de requisitos del {score_cobertura:.0%}."
        )
    else:
        fortalezas = (
            "El análisis no ha identificado coincidencias directas entre "
            "las competencias del CV y los requisitos explícitos del puesto."
        )

    if keywords_gaps:
        n_gaps      = len(keywords_gaps)
        muestra_gaps = keywords_gaps[:3]
        lista_gaps  = ", ".join(f'"{k}"' for k in muestra_gaps)
        sufijo_gaps = " entre otros aspectos" if n_gaps > 3 else ""
        gaps_texto  = (
            f"Los principales gaps detectados son {lista_gaps}{sufijo_gaps}. "
            f"Estas áreas podrían ser determinantes en la decisión de selección."
        )
    else:
        gaps_texto = (
            "No se han detectado gaps significativos respecto a los requisitos "
            "explícitos del puesto."
        )

    return f"{apertura} {fortalezas} {gaps_texto}"


def _explicacion_llm(
    score: float,
    score_global: float,
    score_cobertura: float,
    keywords_cv: list[str],
    keywords_cubiertas: list[str],
    keywords_gaps: list[str],
    nombre_cv: str,
    nombre_puesto: str,
    api_key: str,
) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("Ejecuta: pip install google-genai")

    cliente = genai.Client(api_key=api_key)

    cubiertas_str = ", ".join(keywords_cubiertas[:6]) if keywords_cubiertas else "ninguna"
    gaps_str      = ", ".join(keywords_gaps[:5])      if keywords_gaps      else "ninguno"
    kws_cv_str    = ", ".join(keywords_cv[:8])        if keywords_cv        else "no disponibles"

    prompt = f"""Eres un asistente de selección de personal. Tu tarea es escribir UN SOLO PÁRRAFO \
(máximo 5 frases) que explique de forma clara y profesional la adecuación de un candidato a un puesto.

Datos del análisis automático:
- CV analizado: {nombre_cv}
- Puesto: {nombre_puesto}
- Score de idoneidad: {score:.0%}
- Similitud semántica global: {score_global:.0%}
- Cobertura de requisitos: {score_cobertura:.0%}
- Competencias del CV relevantes: {kws_cv_str}
- Requisitos del puesto cubiertos: {cubiertas_str}
- Gaps principales (requisitos no cubiertos): {gaps_str}

Instrucciones:
- Escribe exactamente UN párrafo en español, fluido y profesional.
- Menciona el porcentaje de idoneidad ({score:.0%}) de forma natural.
- Destaca 2-3 puntos fuertes si los hay.
- Menciona los gaps más relevantes si los hay.
- NO inventes información que no esté en los datos proporcionados.
- NO uses listas ni bullets, solo prosa continua.
- Tono: objetivo, profesional, constructivo."""

    respuesta = cliente.models.generate_content(
        model=GOOGLE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=1300,
            temperature=0.4,
        ),
    )
    return respuesta.text.strip()


def generar_explicacion(
    score: float,
    score_global: float,
    score_cobertura: float,
    keywords_cv: list[str],
    keywords_cubiertas: list[str],
    keywords_gaps: list[str],
    nombre_cv: str = "El candidato",
    nombre_puesto: str = "el puesto",
    forzar_plantilla: bool = False,
) -> dict:
    """
    Genera el texto explicativo. Intenta Gemini si hay API key; si no, usa plantillas.
    Retorna dict con 'texto' y 'metodo'.
    """
    api_key = None if forzar_plantilla else _cargar_api_key()

    if api_key:
        try:
            texto = _explicacion_llm(
                score=score,
                score_global=score_global,
                score_cobertura=score_cobertura,
                keywords_cv=keywords_cv,
                keywords_cubiertas=keywords_cubiertas,
                keywords_gaps=keywords_gaps,
                nombre_cv=nombre_cv,
                nombre_puesto=nombre_puesto,
                api_key=api_key,
            )
            return {"texto": texto, "metodo": "gemini"}
        except Exception as e:
            print(f"  [explainer] ⚠️  Gemini no disponible ({e}). Usando plantillas.")

    texto = _explicacion_plantilla(
        score=score,
        score_global=score_global,
        score_cobertura=score_cobertura,
        keywords_cubiertas=keywords_cubiertas,
        keywords_gaps=keywords_gaps,
        nombre_cv=nombre_cv,
        nombre_puesto=nombre_puesto,
    )
    return {"texto": texto, "metodo": "plantilla"}
