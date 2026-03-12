# tests/test_feature_extractor.py

from cogemi.features.extractor_llm import LLMFeatureExtractor
from cogemi.observe.scenario import Scenario
def test_feature_extraction_stub():
    extractor = LLMFeatureExtractor(model="stub")
    # Example feature vector:
    # feature_cols = [
    # 'Comfort-driven', 'Low-stakes consequences', 'Preserves emotional well-being',
    # 'Strategic deception', 'Role-based justification', 'Protective intent',
    # 'Avoidance of emotional burden', 'Personal relationship context',
    # 'Soothing narrative for loss', 'Protective fabrication',
    # 'Professional authority used', 'Ethical tension', 'Truth withheld to maintain hope'
    # ]
    scenarios = [
        #{"id": "c1", "description": "Polite correction"},
        #{"id": "c2", "description": "Public shaming"},
        Scenario(id="c1", representation="Someone politely corrects another person.", anchors={"action": "polite_correction"}, origin={"observation_id": "o1"}),
        Scenario(id="c2", representation="Someone publicly shames another person.", anchors={"action": "public_shaming"}, origin={"observation_id": "o2"})
    ]

    features = extractor.extract_from_scenarios(scenarios)

    for f in features:
        print(f)  # This will print the dummy features for each scenario
    assert len(features) == 2
    assert all(len(f) > 0 for f in features) # just checks that there is something in the list
