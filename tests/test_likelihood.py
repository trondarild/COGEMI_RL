# tests/test_likelihood.py

from cogemi.generalize.likelihood import ContextLikelihoodModel

def test_likelihood_model_basic():
    model = ContextLikelihoodModel()

    X = [
        [1, 0, 0],
        [0, 1, 0],
    ]
    y = ["c1", "c2"]

    model.fit(X, y)

    probs = {}
    probs['c1'] = model.predict_proba([1, 0, 0])
    probs['c2'] = model.predict_proba([0, 1, 0])

    assert abs(sum(probs["c1"].values()) - 1.0) < 1e-6
    assert abs(sum(probs["c2"].values()) - 1.0) < 1e-6
    assert probs["c1"]['c1'] == probs["c2"]['c2']
