"""Esquema Pydantic del objeto SCL (Structured Compressed Language).

Un objeto SCL se serializa como una sola linea con el formato:

    ACTION | in:X,Y | out:Z | constraint:A,B | fmt:W

Este modulo define la representacion tipada que un LLM debe llenar
(via structured output) antes de que el serializador (fuera de este
modulo) construya el string final.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Caracteres reservados por la sintaxis SCL: no pueden aparecer dentro
# de un token individual porque delimitan segmentos/listas.
_RESERVED_CHARS = set("|:,+\n")

# Un token "estricto" (action, in, out, fmt): snake_case, empieza con letra.
_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_]*$")

# Un token de constraint es un poco mas laxo: permite espacios y guiones
# para frases cortas legibles (p.ej. "no-external-calls", "max 200 tokens").
_CONSTRAINT_RE = re.compile(r"^[a-z0-9][a-z0-9_ -]*$")


def _split_if_str(value: object, separators: str) -> object:
    """Permite que un campo de lista llegue como string (p.ej. 'dbg+eval')."""
    if isinstance(value, str):
        for sep in separators:
            if sep in value:
                return [part for part in value.split(sep)]
        return [value]
    return value


def _normalize_token(raw: str, *, pattern: re.Pattern[str]) -> str:
    value = raw.strip().lower()
    if not value:
        raise ValueError("el token no puede estar vacio")
    if any(ch in _RESERVED_CHARS for ch in raw):
        raise ValueError(
            f"token invalido {raw!r}: no puede contener ninguno de {sorted(_RESERVED_CHARS)}"
        )
    value = re.sub(r"\s+", "_" if pattern is _TOKEN_RE else " ", value)
    if not pattern.match(value):
        raise ValueError(f"token invalido {raw!r}: no cumple el patron {pattern.pattern}")
    return value


class SCLObject(BaseModel):
    """Representacion tipada de una instruccion SCL."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    action: list[str] = Field(
        ...,
        min_length=1,
        description="Cadena de verbos atomicos en orden de ejecucion, p.ej. ['dbg','eval','fix'].",
    )
    input: list[str] = Field(
        ...,
        min_length=1,
        alias="in",
        description="Entidades de entrada, p.ej. ['fn'].",
    )
    output: list[str] = Field(
        ...,
        min_length=1,
        alias="out",
        description="Entidades de salida esperadas, p.ej. ['bugs', 'patched_fn'].",
    )
    constraints: list[str] = Field(
        default_factory=list,
        alias="constraint",
        description="Restricciones opcionales sobre la ejecucion o el resultado.",
    )
    format: str | None = Field(
        default=None,
        alias="fmt",
        description="Formato de salida esperado, p.ej. 'sections'.",
    )

    @field_validator("action", mode="before")
    @classmethod
    def _split_action(cls, value: object) -> object:
        return _split_if_str(value, "+")

    @field_validator("input", "output", "constraints", mode="before")
    @classmethod
    def _split_list(cls, value: object) -> object:
        return _split_if_str(value, ",")

    @field_validator("action", "input", "output")
    @classmethod
    def _normalize_strict_tokens(cls, values: list[str]) -> list[str]:
        return [_normalize_token(v, pattern=_TOKEN_RE) for v in values]

    @field_validator("constraints")
    @classmethod
    def _normalize_constraint_tokens(cls, values: list[str]) -> list[str]:
        return [_normalize_token(v, pattern=_CONSTRAINT_RE) for v in values]

    @field_validator("format")
    @classmethod
    def _normalize_format(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_token(value, pattern=_TOKEN_RE)
