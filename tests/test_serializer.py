from scl.models import SCLObject
from scl.serializer import serialize


def test_serializes_canonical_example():
    obj = SCLObject(
        action=["dbg", "eval", "fix"],
        input=["fn"],
        output=["bugs", "patched_fn"],
        format="sections",
    )
    assert serialize(obj) == "dbg+eval+fix | in:fn | out:bugs,patched_fn | fmt:sections"


def test_omits_empty_constraint_and_format():
    obj = SCLObject(action=["gen"], input=["prompt"], output=["text"])
    assert serialize(obj) == "gen | in:prompt | out:text"


def test_includes_constraints_when_present():
    obj = SCLObject(
        action=["gen"],
        input=["prompt"],
        output=["text"],
        constraints=["max 200 tokens", "no-external-links"],
    )
    assert serialize(obj) == (
        "gen | in:prompt | out:text | constraint:max 200 tokens,no-external-links"
    )


def test_joins_multiple_inputs_and_outputs():
    obj = SCLObject(action=["extract"], input=["doc", "schema"], output=["fields"])
    assert serialize(obj) == "extract | in:doc,schema | out:fields"
