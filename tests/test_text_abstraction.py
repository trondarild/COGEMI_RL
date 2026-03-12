# tests/test_text_abstraction.py

from cogemi.observe.text_abstraction import TextAbstraction
from cogemi.observe.observation import Observation

def test_text_abstraction_identity():
    obs = Observation(
        id="obs1",
        modalities={"text": "A person interrupts a meeting loudly."},
        metadata={}
    )

    abstraction = TextAbstraction(model="stub")
    scenario = abstraction.abstract(obs)

    assert scenario.id == "obs1"
    assert scenario.representation == obs.modalities["text"]
    assert "action" in scenario.anchors
    assert scenario.origin["observation_id"] == "obs1"
