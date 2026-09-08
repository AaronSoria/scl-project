"""Traductor NL -> SCL usando un modelo local via Ollama.

No hay lexer/parser: el LLM nunca escribe el string SCL como texto libre.
En su lugar, Ollama genera un JSON restringido al esquema de SCLObject
(salida estructurada nativa) y el string compacto se produce despues con
el serializador propio (scl.serializer.serialize), no por el modelo.

Few-shot: examples/fewshot.jsonl trae ~20 pares (nl -> campos SCL)
cubriendo 4 dominios (analisis de codigo, extraccion de informacion,
razonamiento estructurado, generacion creativa) que se inyectan como
turnos user/assistant antes de la instruccion real.

Requiere el extra 'translate' (`pip install -e ".[translate]"`) y un
servidor Ollama corriendo localmente con el modelo ya descargado, p.ej.:
    ollama pull llama3.1:8b
"""

from __future__ import annotations

import json
from pathlib import Path

import ollama

from scl.models import SCLObject
from scl.serializer import serialize

DEFAULT_MODEL = "llama3.1:8b"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FEWSHOT_PATH = _REPO_ROOT / "examples" / "fewshot.jsonl"

_SYSTEM_PROMPT = """Eres un traductor de lenguaje natural a SCL (Structured Compressed Language).
SCL descompone una instruccion en: verbos de accion, entidades de entrada,
entidades de salida esperadas, restricciones opcionales y formato opcional.
Responde SIEMPRE con un objeto JSON que cumpla el esquema dado, usando
tokens cortos en snake_case (sin espacios, sin comas, sin '|', ':' ni '+').
No expliques nada, no agregues texto fuera del JSON."""


def load_fewshot_examples(path: Path = _FEWSHOT_PATH) -> list[dict]:
    """Carga los ejemplos canonicos NL->SCL desde un archivo JSONL."""
    if not path.exists():
        return []
    examples = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def _example_to_target_json(example: dict) -> str:
    obj = SCLObject.model_validate(example)
    fields = obj.model_dump(by_alias=True, exclude_none=True, exclude_defaults=True)
    return json.dumps(fields, ensure_ascii=False)


def build_messages(nl_instruction: str, examples: list[dict] | None = None) -> list[dict]:
    """Arma la conversacion few-shot: system + N pares (user, assistant) + instruccion final."""
    if examples is None:
        examples = load_fewshot_examples()

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    for example in examples:
        messages.append({"role": "user", "content": example["nl"]})
        messages.append({"role": "assistant", "content": _example_to_target_json(example)})
    messages.append({"role": "user", "content": nl_instruction})
    return messages


def translate(nl_instruction: str, model: str = DEFAULT_MODEL) -> SCLObject:
    """Traduce una instruccion en lenguaje natural a un SCLObject validado."""
    response = ollama.chat(
        model=model,
        messages=build_messages(nl_instruction),
        format=SCLObject.model_json_schema(),
        options={"temperature": 0},
    )
    return SCLObject.model_validate_json(response["message"]["content"])


def translate_to_scl(nl_instruction: str, model: str = DEFAULT_MODEL) -> str:
    """Traduce y serializa directamente al string SCL compacto."""
    return serialize(translate(nl_instruction, model=model))


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Traduce una instruccion NL a SCL")
    parser.add_argument("instruction", help="Instruccion en lenguaje natural")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Modelo de Ollama a usar")
    args = parser.parse_args()

    print(translate_to_scl(args.instruction, model=args.model))


if __name__ == "__main__":
    _main()
