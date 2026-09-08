# SCL — Structured Compressed Language

SCL es un lenguaje de prompts compacto y ontológico, pensado para reducir
tokens y ambigüedad en instrucciones a LLMs. En vez de una instrucción en
prosa, representa la intención como una sola línea con campos explícitos:

```
ACTION | in:X | out:Y | constraint:Z | fmt:W
```

Ejemplo:

```
dbg+eval+fix | in:fn | out:bugs,patched_fn | fmt:sections
```

que equivale a: *"depura, evalúa y arregla esta función; dame los bugs
encontrados y la función parchada; preséntalo en secciones"*.

## Motivación

Un prompt en lenguaje natural es ineficiente en dos ejes:

- **Redundancia léxica** — conectores, cortesías y repeticiones que no
  aportan información nueva al modelo.
- **Ambigüedad semántica** — entidades, relaciones o restricciones que
  quedan implícitas y que el modelo debe inferir (o adivinar).

SCL fuerza a hacer explícitos los cinco campos que casi siempre importan
en una instrucción — acción, entrada, salida, restricciones y formato —
y descarta el resto. Esto es un prototipo para explorar si esa
compresión reduce tokens sin perder fidelidad semántica.

## Cómo está construido

Este proyecto **no usa un lexer/parser formal** para SCL: la sintaxis es
plana y de una sola línea, así que no hace falta. En cambio:

1. Un LLM local (vía [Ollama](https://ollama.com)) llena un objeto
   **tipado** (`SCLObject`, definido con Pydantic) usando salida
   estructurada nativa restringida a un JSON Schema — el modelo nunca
   escribe el string SCL como texto libre.
2. Un **serializador** propio (código, no el LLM) convierte ese objeto
   validado al string SCL compacto.

```
NL (texto libre) → [LLM + few-shot + JSON Schema] → SCLObject (Pydantic) → [serializer] → string SCL
```

## Estructura del repo

```
scl-project/
├── src/scl/
│   ├── models.py      # esquema Pydantic de SCLObject (action, in, out, constraint, fmt)
│   ├── serializer.py  # SCLObject -> string SCL compacto
│   └── translate.py   # traductor NL -> SCL vía Ollama (few-shot + salida estructurada)
├── examples/
│   └── fewshot.jsonl  # ~20 ejemplos canónicos NL->SCL (4 dominios)
├── schemas/           # (reservado para JSON Schema exportado / datasets de eval)
├── tests/             # pytest: modelo, serializador, traductor
└── docs/              # (reservado para notas de diseño y métricas)
```

## Instalación

Requiere Python 3.10+.

```bash
python -m venv .venv
.venv/Scripts/activate   # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -e ".[dev,translate]"
```

- `dev` instala `pytest` para correr la suite de tests.
- `translate` instala el cliente `ollama` (necesario solo para el
  traductor NL→SCL, no para usar el esquema o el serializador).

Para el traductor además necesitas [Ollama](https://ollama.com) corriendo
localmente con un modelo descargado, por ejemplo:

```bash
ollama pull llama3.1:8b
```

## Uso básico

### Construir y serializar un objeto SCL a mano

```python
from scl import SCLObject, serialize

obj = SCLObject(
    action=["dbg", "eval", "fix"],
    input=["fn"],
    output=["bugs", "patched_fn"],
    format="sections",
)
print(serialize(obj))
# dbg+eval+fix | in:fn | out:bugs,patched_fn | fmt:sections
```

`SCLObject` valida cada token (no permite `|`, `:`, `,`, `+` dentro de un
campo, ya que son separadores reservados de la sintaxis) y normaliza
mayúsculas/espacios. También acepta la forma abreviada de la sintaxis
SCL directamente:

```python
SCLObject(action="dbg+eval+fix", input="fn", output="bugs,patched_fn")
```

### Traducir lenguaje natural a SCL con un modelo local

```python
from scl.translate import translate_to_scl

print(translate_to_scl("Encuentra los bugs de esta función y corrígelos"))
# dbg+eval+fix | in:fn | out:bugs,patched_fn
```

O desde la línea de comandos:

```bash
python -m scl.translate "Encuentra los bugs de esta función y corrígelos"
python -m scl.translate "..." --model qwen2.5:7b
```

## Tests

```bash
pytest
```

## Estado del proyecto

Prototipo en desarrollo activo. Pendiente (no implementado todavía):

- Métricas de tasa de éxito sintáctico y fidelidad semántica (round-trip
  NL→SCL→NL' comparado por similitud).
- Medición de ahorro neto de tokens frente al prompt original.

## Licencia

[MIT](LICENSE)
