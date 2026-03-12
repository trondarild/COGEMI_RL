# tests/test_context_learner.py

from cogemi.learning.context_learner import ContextLearner
from cogemi.observe.scenario import Scenario


def test_context_creation_and_merge():
    learner = ContextLearner(
        add_threshold=0.2,
        merge_threshold=0.1,
        metric="js"
    )

    # scenario_id format: id_action_state
    learner.add("ID1_A1_S2", [-1, 0, 1])
    learner.add("ID2_A2_S3", [-1, 0, 1])

    contexts = learner.contexts()

    # contexts is a ContextsDict: {action: {"C1": ContextEntry, ...}}
    assert len(contexts) == 2            # two distinct actions: A1, A2
    assert "A1" in contexts
    assert "A2" in contexts

    # each action starts with one context C1
    assert "C1" in contexts["A1"]
    assert "C1" in contexts["A2"]

    # States entries are [state_str, reward_samples]
    assert contexts["A1"]["C1"]["States"][0][0] == "S2"
    assert contexts["A2"]["C1"]["States"][0][0] == "S3"

    # Distribution has the three ternary keys
    for key in [-1, 0, 1]:
        assert key in contexts["A1"]["C1"]["Distribution"]


def test_fit_returns_context_labels():
    learner = ContextLearner(
        add_threshold=0.5,
        merge_threshold=0.8,
        metric="js"
    )

    scenarios = [
        Scenario(id="ID1_A1_S2", representation="Scenario 1", anchors={"action": "A1"}, origin={}),
        Scenario(id="ID2_A2_S3", representation="Scenario 2", anchors={"action": "A2"}, origin={}),
    ]
    samples = [[0, 1, 0, -1], [0, 0, 1, -1]]

    labels = learner.fit(scenarios, samples)

    # fit() returns one context label per scenario, as "action:Cn" strings
    assert len(labels) == 2
    assert all(isinstance(label, str) for label in labels)
    assert all(":" in label for label in labels)   # format "action:C1"
