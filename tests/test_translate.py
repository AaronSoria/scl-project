import json
from unittest.mock import patch

from scl.models import SCLObject
from scl.translate import build_messages, load_fewshot_examples, translate, translate_to_scl


def test_fewshot_examples_are_valid_scl_objects():
    examples = load_fewshot_examples()
    assert len(examples) >= 15
    for example in examples:
        SCLObject.model_validate(example)


def test_fewshot_covers_four_domains():
    examples = load_fewshot_examples()
    domains = {e["domain"] for e in examples}
    assert domains == {
        "code_analysis",
        "info_extraction",
        "structured_reasoning",
        "creative_generation",
    }


def test_build_messages_shape():
    examples = load_fewshot_examples()
    messages = build_messages("traduce esto", examples=examples)

    assert messages[0]["role"] == "system"
    assert messages[-1] == {"role": "user", "content": "traduce esto"}
    assert len(messages) == 1 + 2 * len(examples) + 1

    for i, example in enumerate(examples):
        user_msg = messages[1 + 2 * i]
        assistant_msg = messages[2 + 2 * i]
        assert user_msg == {"role": "user", "content": example["nl"]}
        assert assistant_msg["role"] == "assistant"
        # el turno assistant debe ser JSON valido que reconstruye el mismo SCLObject
        parsed = SCLObject.model_validate_json(assistant_msg["content"])
        assert parsed == SCLObject.model_validate(example)


def test_translate_parses_ollama_response_into_scl_object():
    fake_content = json.dumps({"action": ["dbg", "fix"], "in": ["fn"], "out": ["patched_fn"]})
    fake_response = {"message": {"content": fake_content}}

    with patch("scl.translate.ollama.chat", return_value=fake_response) as mock_chat:
        result = translate("arregla esta funcion")

    assert result == SCLObject(action=["dbg", "fix"], input=["fn"], output=["patched_fn"])
    _, kwargs = mock_chat.call_args
    assert kwargs["model"] == "llama3.1:8b"
    assert kwargs["format"] == SCLObject.model_json_schema()
    assert kwargs["messages"][-1] == {"role": "user", "content": "arregla esta funcion"}


def test_translate_to_scl_serializes_result():
    fake_content = json.dumps({"action": ["dbg", "fix"], "in": ["fn"], "out": ["patched_fn"]})
    fake_response = {"message": {"content": fake_content}}

    with patch("scl.translate.ollama.chat", return_value=fake_response):
        result = translate_to_scl("arregla esta funcion")

    assert result == "dbg+fix | in:fn | out:patched_fn"
