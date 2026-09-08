"""Serializador de SCLObject al string SCL compacto.

    ACTION | in:X,Y | out:Z | constraint:A,B | fmt:W

Los segmentos 'constraint' y 'fmt' se omiten cuando estan vacios/ausentes.
La validacion de tokens (caracteres reservados, normalizacion) ya ocurre
en SCLObject, asi que este modulo solo se encarga del formato de union.
"""

from __future__ import annotations

from scl.models import SCLObject

_SEGMENT_SEP = " | "
_LIST_SEP = ","
_ACTION_SEP = "+"


def serialize(obj: SCLObject) -> str:
    """Convierte un SCLObject validado en su representacion SCL de una linea."""
    segments = [
        _ACTION_SEP.join(obj.action),
        "in:" + _LIST_SEP.join(obj.input),
        "out:" + _LIST_SEP.join(obj.output),
    ]
    if obj.constraints:
        segments.append("constraint:" + _LIST_SEP.join(obj.constraints))
    if obj.format:
        segments.append("fmt:" + obj.format)
    return _SEGMENT_SEP.join(segments)
