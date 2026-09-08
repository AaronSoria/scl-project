import pytest
from pydantic import ValidationError

from scl.models import SCLObject


def test_builds_from_python_names():
    obj = SCLObject(
        action=["dbg", "eval", "fix"],
        input=["fn"],
        output=["bugs", "patched_fn"],
        constraints=["no-side-effects"],
        format="sections",
    )
    assert obj.action == ["dbg", "eval", "fix"]
    assert obj.constraints == ["no-side-effects"]
    assert obj.format == "sections"


def test_builds_from_scl_aliases():
    obj = SCLObject.model_validate(
        {
            "action": ["dbg", "eval", "fix"],
            "in": ["fn"],
            "out": ["bugs", "patched_fn"],
            "constraint": [],
            "fmt": "sections",
        }
    )
    assert obj.input == ["fn"]
    assert obj.output == ["bugs", "patched_fn"]
    assert obj.format == "sections"


def test_accepts_compact_string_shorthand():
    obj = SCLObject(action="dbg+eval+fix", input="fn", output="bugs,patched_fn")
    assert obj.action == ["dbg", "eval", "fix"]
    assert obj.output == ["bugs", "patched_fn"]
    assert obj.constraints == []
    assert obj.format is None


def test_normalizes_case_and_whitespace():
    obj = SCLObject(action=["  DBG "], input=["Fn"], output=["Bugs"])
    assert obj.action == ["dbg"]
    assert obj.input == ["fn"]
    assert obj.output == ["bugs"]


@pytest.mark.parametrize("bad_token", ["in:fn", "a,b", "a|b", "a+b"])
def test_rejects_reserved_characters(bad_token):
    with pytest.raises(ValidationError):
        SCLObject(action=[bad_token], input=["fn"], output=["bugs"])


def test_requires_at_least_one_action_input_output():
    with pytest.raises(ValidationError):
        SCLObject(action=[], input=["fn"], output=["bugs"])
    with pytest.raises(ValidationError):
        SCLObject(action=["dbg"], input=[], output=["bugs"])
    with pytest.raises(ValidationError):
        SCLObject(action=["dbg"], input=["fn"], output=[])


def test_constraints_allow_short_phrases():
    obj = SCLObject(
        action=["gen"],
        input=["prompt"],
        output=["text"],
        constraints=["max 200 tokens", "no-external-links"],
    )
    assert obj.constraints == ["max 200 tokens", "no-external-links"]
